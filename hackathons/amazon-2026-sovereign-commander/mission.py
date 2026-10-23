"""Public, standalone mission orchestration reference. No private TitanU internals.

Bounded local tools only. A mission autonomously plans, fans out to three
specialist workers, adapts to evidence, produces files, and audits every stage.
No outbound connections, code execution, or implicit external side effects.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import re
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MAX_GOAL=500
EVENT_LOCK=threading.RLock()
PRIORITY={'high':3,'medium':2,'low':1}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds')


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(buf):
    return hashlib.sha256(buf).hexdigest()


def schema(db_factory):
    with db_factory() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS missions(
                id TEXT PRIMARY KEY,goal TEXT NOT NULL,status TEXT NOT NULL,
                allow_writes INTEGER NOT NULL,created_at TEXT NOT NULL,
                finished_at TEXT,summary TEXT NOT NULL DEFAULT '',error TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS mission_steps(
                id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL,
                agent TEXT NOT NULL,status TEXT NOT NULL,started_at TEXT NOT NULL,
                finished_at TEXT, result TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (mission_id) REFERENCES missions(id)
            );
            CREATE TABLE IF NOT EXISTS mission_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, mission_id TEXT NOT NULL,
                seq INTEGER NOT NULL,agent TEXT NOT NULL,kind TEXT NOT NULL,
                payload TEXT NOT NULL,previous_hash TEXT NOT NULL,hash TEXT NOT NULL,
                time TEXT NOT NULL,UNIQUE(mission_id,seq)
            );
            CREATE TABLE IF NOT EXISTS mission_artifacts(
                mission_id TEXT NOT NULL, name TEXT NOT NULL,
                sha256 TEXT NOT NULL,bytes INTEGER NOT NULL,
                PRIMARY KEY(mission_id,name)
            );
        ''')


class MissionEngine:
    def __init__(self, db_factory, root_factory, task_reader):
        self.db_factory=db_factory
        self.root_factory=root_factory
        self.task_reader=task_reader
        schema(db_factory)

    def emit(self, mission_id, agent, kind, payload):
        # Single append-only serialization point even across worker threads.
        with EVENT_LOCK:
            with self.db_factory() as db:
                prev=db.execute('SELECT seq,hash FROM mission_events WHERE mission_id=? ORDER BY seq DESC LIMIT 1',(mission_id,)).fetchone()
                seq=(prev['seq']+1) if prev else 1
                prev_hash=prev['hash'] if prev else '0'*64
                p=canonical(payload)
                event={'mission_id':mission_id,'seq':seq,'agent':agent,'kind':kind,'payload':p,'previous_hash':prev_hash}
                h=digest(canonical(event).encode('utf-8'))
                db.execute('INSERT INTO mission_events(mission_id,seq,agent,kind,payload,previous_hash,hash,time) VALUES(?,?,?,?,?,?,?,?)',
                           (mission_id,seq,agent,kind,p,prev_hash,h,now()))
                return h

    def start(self, goal, allow_local_writes=False):
        if not isinstance(goal,str) or not (8<=len(goal.strip())<=MAX_GOAL):
            raise ValueError('Mission objective must be 8–500 characters')
        if type(allow_local_writes) is not bool:
            raise ValueError('allow_local_writes must be boolean')
        mid=uuid.uuid4().hex
        with self.db_factory() as db:
            db.execute('INSERT INTO missions(id,goal,status,allow_writes,created_at) VALUES(?,?,?,?,?)',
                       (mid,goal.strip(),'queued',int(allow_local_writes),now()))
        self.emit(mid,'Mission Control','MISSION_ACCEPTED',{'goal':goal.strip(),'scope':'local-only','allow_local_writes':allow_local_writes})
        th=threading.Thread(target=self.execute,args=(mid,),daemon=True,name='mission-'+mid[:8])
        th.start()
        return {'id':mid,'status':'queued','detail_url':'/api/missions/'+mid}

    def assert_active(self,mid):
        with self.db_factory() as db:
            r=db.execute('SELECT status FROM missions WHERE id=?',(mid,)).fetchone()
        if not r or r['status']=='cancelled':
            raise RuntimeError('Mission cancelled')

    def step(self,mid,agent,fn):
        self.assert_active(mid)
        with self.db_factory() as db:
            cur=db.execute('INSERT INTO mission_steps(mission_id,agent,status,started_at) VALUES(?,?,?,?)',
                           (mid,agent,'running',now()))
            sid=cur.lastrowid
        self.emit(mid,agent,'AGENT_STARTED',{'step_id':sid})
        try:
            result=fn()
            with self.db_factory() as db:
                db.execute('UPDATE mission_steps SET status=?,result=?,finished_at=? WHERE id=?',
                           ('passed',canonical(result),now(),sid))
            self.emit(mid,agent,'AGENT_COMPLETED',{'step_id':sid,'summary':result.get('summary','completed')})
            return result
        except Exception as err:
            with self.db_factory() as db:
                db.execute('UPDATE mission_steps SET status=?,result=?,finished_at=? WHERE id=?',
                           ('failed',canonical({'error':type(err).__name__}),now(),sid))
            self.emit(mid,agent,'AGENT_FAILED',{'step_id':sid,'reason':str(err)[:200]})
            raise

    def snapshot(self):
        with self.db_factory() as db:
            return [dict(x) for x in db.execute('SELECT * FROM tasks ORDER BY created_at,id')]

    @staticmethod
    def scout(goal, items):
        keys=set(re.findall(r'[a-z0-9]+',goal.lower()))-{'the','and','that','with','from','please','about','for','build','create','make','this'}
        matched=[]
        for task in items:
            hay=(task['title']+' '+task['project']).lower()
            if any(k in hay for k in keys) or any(k in goal.lower() for k in ('all','company','business','portfolio')):
                matched.append(task)
        if not matched: matched=items
        active=[x for x in matched if x['status']=='open']
        return {'summary':f'Scoped {len(active)} open tasks from {len(items)} local records',
                'scope':active, 'available_projects':sorted({t['project'] for t in active}),
                'snapshot_hash':digest(canonical(items).encode())}

    @staticmethod
    def risk(context):
        issues=[]
        for item in context['scope']:
            if item['blocker']:
                issues.append({'task_id':item['id'],'title':item['title'],'severity':'critical' if item['priority']=='high' else 'elevated','project':item['project']})
        return {'summary':f'{len(issues)} unresolved blockers detected','blockers':issues,'has_blockers':bool(issues)}

    @staticmethod
    def schedule(context):
        agenda=[]; cursor=9*60
        for t in sorted(context['scope'],key=lambda x:(-int(x['blocker']),-PRIORITY[x['priority']],x['minutes'],x['title'])):
            if cursor<12*60 and cursor+t['minutes']>12*60:cursor=13*60
            if cursor+t['minutes']>17*60: break
            start=cursor;cursor+=t['minutes']
            agenda.append({'task_id':t['id'],'task':t['title'],'project':t['project'],
                           'window':f'{start//60:02d}:{start%60:02d}-{cursor//60:02d}:{cursor%60:02d}'})
        return {'summary':f'Planned {len(agenda)} tasks with blocker-first priorities','timeline':agenda}

    @staticmethod
    def outreach(context):
        customers=[t for t in context['scope'] if 'customer' in t['project'].lower() or 'customer' in t['title'].lower()]
        bullets='\n'.join('- '+t['title'] for t in customers[:12])
        draft='Subject: Verified project progress\n\nHello,\n\nHere is our current work queue:\n'+(bullets or '- No customer-specific tasks on record.')+'\n\nWe will confirm progress against completed milestones before making commitments.\n\nTitanU'
        return {'summary':f'Generated an UNSENT draft referencing {len(customers)} customer items',
                'draft':draft,'sent':False}

    def remediate(self,mid,risk,allow_writes,project='Launch'):
        suggestions=[];created=[]
        for issue in risk['blockers'][:3]:
            task_title='Resolve blocker: '+issue['title']
            suggestions.append(task_title)
            if allow_writes:
                with self.db_factory() as db:
                    exists=db.execute('SELECT id FROM tasks WHERE title=? AND status=?',(task_title,'open')).fetchone()
                    if not exists:
                        task_id=str(uuid.uuid4())
                        db.execute('INSERT INTO tasks(id,title,priority,minutes,project,blocker,status,created_at) VALUES(?,?,?,?,?,?,?,?)',
                                   (task_id,task_title,'high',30,issue['project'] or project,0,'open',now()))
                        created.append(task_id)
        return {'summary':f'Proposed {len(suggestions)} resolution tasks, created {len(created)} after authorization',
                'proposed_actions':suggestions,'created_task_ids':created,
                'local_changes_authorized':allow_writes}

    def write_artifact(self,mid,name,content):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,80}',name):raise ValueError('invalid artifact name')
        folder=self.root_factory()/'missions'/mid
        folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        out=folder/name
        if out.exists():raise ValueError('artifact already exists')
        buf=content.encode('utf-8')
        if len(buf)>512*1024:raise ValueError('artifact exceeds limit')
        with open(out,'xb') as f:f.write(buf)
        out.chmod(0o600)
        hash_=digest(buf)
        with self.db_factory() as db:
            db.execute('INSERT INTO mission_artifacts(mission_id,name,sha256,bytes) VALUES(?,?,?,?)',(mid,name,hash_,len(buf)))
        self.emit(mid,'Artifact Builder','ARTIFACT_WRITTEN',{'name':name,'sha256':hash_,'bytes':len(buf)})
        return {'name':name,'sha256':hash_,'bytes':len(buf)}

    def deliver(self,mid,goal,context,risk,timeline,outreach,remedy):
        lines=['# TitanU mission execution report','',f'Objective: {goal}','',
               '## Local evidence',f'Open matching tasks: {len(context["scope"])}',
               f'Active blockers: {len(risk["blockers"])}','',
               '## Risk agent findings']
        lines.extend(f'- [{v["severity"]}] {v["title"]}' for v in risk['blockers'])
        if not risk['blockers']:lines.append('- No blockers marked in the available task records')
        lines.extend(['','## Coordinator response'])
        lines.extend('- '+x for x in remedy['proposed_actions'])
        lines.append(f'Local action tasks created: {len(remedy["created_task_ids"])}')
        lines.extend(['','## Timeline'])
        lines.extend(f'- {x["window"]}: {x["task"]}' for x in timeline['timeline'])
        lines.extend(['','## Evidence limits','No external deployments, emails, purchases, or cloud actions were performed.',
                      'Tasks are user-maintained local records; absence of marked blockers is not independent production verification.',''])
        report=self.write_artifact(mid,'mission-brief.md','\n'.join(lines))
        draft=self.write_artifact(mid,'customer-draft.txt',outreach['draft'])
        raw=io.StringIO();w=csv.writer(raw);w.writerow(['time','project','task'])
        for x in timeline['timeline']:w.writerow([x['window'],x['project'],x['task']])
        csv_artifact=self.write_artifact(mid,'schedule.csv',raw.getvalue())
        return {'summary':'Produced 3 persistent, content-hashed output artifacts',
                'artifacts':[report,draft,csv_artifact]}

    def verify(self,mid):
        with self.db_factory() as db:
            ev=[dict(x) for x in db.execute('SELECT seq,agent,kind,payload,previous_hash,hash FROM mission_events WHERE mission_id=? ORDER BY seq',(mid,))]
            artifacts=[dict(x) for x in db.execute('SELECT name,sha256,bytes FROM mission_artifacts WHERE mission_id=? ORDER BY name',(mid,))]
            steps=[dict(x) for x in db.execute('SELECT agent,status FROM mission_steps WHERE mission_id=? ORDER BY id',(mid,))]
        expected='0'*64;problems=[]
        for idx,e in enumerate(ev,1):
            payload={'mission_id':mid,'seq':e['seq'],'agent':e['agent'],'kind':e['kind'],'payload':e['payload'],'previous_hash':e['previous_hash']}
            if e['seq']!=idx or e['previous_hash']!=expected or digest(canonical(payload).encode())!=e['hash']:
                problems.append('Event integrity failure at sequence '+str(idx))
            expected=e['hash']
        for a in artifacts:
            f=self.root_factory()/'missions'/mid/a['name']
            if not f.is_file() or f.stat().st_size!=a['bytes'] or digest(f.read_bytes())!=a['sha256']:
                problems.append('Artifact integrity failure: '+a['name'])
        if any(s['status']!='passed' for s in steps):problems.append('Unfinished or failed agent step')
        if not artifacts:problems.append('No materialized artifacts')
        return {'verified':not problems,'problems':problems,'steps_passed':sum(s['status']=='passed' for s in steps),
                'event_count':len(ev),'artifacts':len(artifacts),
                'event_chain_head':expected, 'verification_scope':'local event-hash chain and artifact SHA-256; not a third-party notarization'}

    def execute(self,mid):
        with self.db_factory() as db:
            r=db.execute('SELECT * FROM missions WHERE id=?',(mid,)).fetchone()
            if not r:return
            if r['status']!='queued':return
            cur=db.execute("UPDATE missions SET status='running' WHERE id=? AND status='queued'",(mid,))
            if not cur.rowcount:return
            goal=r['goal'];allow=bool(r['allow_writes'])
        try:
            context=self.step(mid,'Scope Scout',lambda:self.scout(goal,self.snapshot()))
            self.emit(mid,'Mission Control','FAN_OUT',{'workers':['Risk Analyst','Timeline Planner','Customer Comms']})
            with ThreadPoolExecutor(max_workers=3,thread_name_prefix='titanu-worker') as pool:
                futures={name:pool.submit(self.step,mid,name,lambda f=fn:f(context)) for name,fn in [
                    ('Risk Analyst',self.risk),('Timeline Planner',self.schedule),('Customer Comms',self.outreach)]}
                results={name:future.result() for name,future in futures.items()}
            risk=results['Risk Analyst'];timeline=results['Timeline Planner'];outreach=results['Customer Comms']
            self.emit(mid,'Mission Control','FAN_IN',{'results':list(results),'blockers':len(risk['blockers'])})
            if risk['has_blockers']:
                remedy=self.step(mid,'Remediation Agent',lambda:self.remediate(mid,risk,allow))
                if remedy['created_task_ids']:
                    # Adaptive replanning uses a new live snapshot after authorized writes.
                    new_context=self.scout(goal,self.snapshot())
                    timeline=self.step(mid,'Adaptive Planner',lambda:self.schedule(new_context))
                    context=new_context
                    self.emit(mid,'Mission Control','REPLAN',{'reason':'authorized remediation tasks added','new_tasks':len(remedy['created_task_ids'])})
            else:
                remedy={'summary':'No blockers: no remediation necessary','proposed_actions':[],'created_task_ids':[]}
            artifacts=self.step(mid,'Artifact Builder',lambda:self.deliver(mid,goal,context,risk,timeline,outreach,remedy))
            self.emit(mid,'Mission Control','HANDOFF_TO_AUDITOR',{'artifact_count':len(artifacts['artifacts'])})
            proof=self.step(mid,'Independent Auditor',lambda:self.verify_before_audit(mid))
            if not proof['verified']:raise RuntimeError('Audit rejected mission output: '+','.join(proof['problems']))
            summary=f"{len(artifacts['artifacts'])} artifacts generated; {len(risk['blockers'])} blockers analyzed; {len(remedy['created_task_ids'])} authorized tasks created"
            with self.db_factory() as db:
                db.execute("UPDATE missions SET status='completed',summary=?,finished_at=? WHERE id=?",(summary,now(),mid))
            self.emit(mid,'Mission Control','MISSION_COMPLETED',{'summary':summary})
        except Exception as err:
            with self.db_factory() as db:
                db.execute("UPDATE missions SET status=CASE WHEN status='cancelled' THEN status ELSE 'failed' END,error=?,finished_at=? WHERE id=?",(str(err)[:250],now(),mid))
            self.emit(mid,'Mission Control','MISSION_STOPPED',{'type':type(err).__name__,'reason':str(err)[:250]})

    def verify_before_audit(self,mid):
        # During the auditor step, the auditor itself is still 'running'.
        proof=self.verify(mid)
        with self.db_factory() as db:
            running=db.execute('SELECT COUNT(*) FROM mission_steps WHERE mission_id=? AND status=?',(mid,'running')).fetchone()[0]
        if running==1 and proof['problems']==['Unfinished or failed agent step']:
            proof['problems']=[];proof['verified']=True
        return proof

    def detail(self,mid):
        if not re.fullmatch(r'[0-9a-f]{32}',mid):raise ValueError('invalid mission id')
        with self.db_factory() as db:
            m=db.execute('SELECT * FROM missions WHERE id=?',(mid,)).fetchone()
            if not m:return None
            steps=[dict(x) for x in db.execute('SELECT id,agent,status,started_at,finished_at,result FROM mission_steps WHERE mission_id=? ORDER BY id',(mid,))]
            events=[dict(x) for x in db.execute('SELECT seq,agent,kind,payload,hash,time FROM mission_events WHERE mission_id=? ORDER BY seq',(mid,))]
            files=[dict(x) for x in db.execute('SELECT * FROM mission_artifacts WHERE mission_id=? ORDER BY name',(mid,))]
        return {'mission':dict(m),'steps':[{**s,'result':json.loads(s['result'])} for s in steps],
                'events':[{**e,'payload':json.loads(e['payload'])} for e in events],
                'artifacts':[{**a,'url':'/api/missions/'+mid+'/artifacts/'+a['name']} for a in files],
                'proof':self.verify(mid) if m['status']=='completed' else None}

    def list(self):
        with self.db_factory() as db:
            return [dict(x) for x in db.execute('SELECT * FROM missions ORDER BY created_at DESC LIMIT 12')]

    def artifact(self,mid,name):
        if not re.fullmatch(r'[0-9a-f]{32}',mid) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,80}',name):return None
        with self.db_factory() as db:
            a=db.execute('SELECT sha256 FROM mission_artifacts WHERE mission_id=? AND name=?',(mid,name)).fetchone()
        if not a:return None
        f=self.root_factory()/'missions'/mid/name
        if not f.is_file():return None
        b=f.read_bytes()
        if digest(b)!=a['sha256']:return None
        return b

    def cancel(self,mid):
        with self.db_factory() as db:
            cur=db.execute("UPDATE missions SET status='cancelled',finished_at=? WHERE id=? AND status IN ('running','queued')",(now(),mid))
        if cur.rowcount:self.emit(mid,'Mission Control','USER_CANCELLED',{})
        return bool(cur.rowcount)