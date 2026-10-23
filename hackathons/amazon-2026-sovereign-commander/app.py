#!/usr/bin/env python3
"""TitanU Sovereign Agent Commander - local Alexa+-style agent experience.
Uses deterministic, inspectable tools; no external API dependency or fabricated outcomes.
"""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('TITANU_DATA_DIR', str(ROOT / 'data'))).resolve()
STARTED = time.monotonic()
MAX_BYTES = 32768
PRIORITY = {'high': 3, 'medium': 2, 'low': 1}
SAMPLE = [
    ('Finish launch demonstration', 'high', 50, 'Launch', 1),
    ('Verify production deployment', 'high', 35, 'Launch', 1),
    ('Reply to customer product inquiry', 'high', 20, 'Customers', 0),
    ('Review release documentation', 'medium', 35, 'Launch', 0),
    ('Organize customer feedback', 'medium', 25, 'Customers', 0),
    ('Refine next product concept', 'low', 40, 'Research', 0),
]

class AutoClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()

def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def connect():
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
    db = sqlite3.connect(str(DATA / 'commander.sqlite'), timeout=10, factory=AutoClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=10000')
    db.execute('PRAGMA journal_mode=WAL')
    return db

def initialize():
    with connect() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS tasks(
               id TEXT PRIMARY KEY, title TEXT NOT NULL, priority TEXT NOT NULL,
               minutes INTEGER NOT NULL, project TEXT NOT NULL, blocker INTEGER NOT NULL,
               status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS receipts(
               id TEXT PRIMARY KEY, command TEXT NOT NULL, intent TEXT NOT NULL,
               outcome TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events(
               id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_id TEXT NOT NULL,
               agent TEXT NOT NULL, detail TEXT NOT NULL, occurred_at TEXT NOT NULL
            );
        ''')
        c = db.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
        if c == 0 and not (DATA / 'initialized').exists():
            db.executemany('''INSERT INTO tasks(id,title,priority,minutes,project,blocker,status,created_at)
                             VALUES(?,?,?,?,?,?,'open',?)''',
                           [(str(uuid.uuid4()), *t, utcnow()) for t in SAMPLE])
            (DATA / 'initialized').write_text(utcnow())
            os.chmod(DATA / 'initialized', 0o600)

def tasks(db):
    return [dict(x) for x in db.execute('SELECT * FROM tasks ORDER BY created_at DESC')]

def receipts(db):
    out = []
    for r in db.execute('SELECT * FROM receipts ORDER BY created_at DESC LIMIT 30'):
        d = dict(r); d['outcome'] = json.loads(d['outcome']); out.append(d)
    return out

def state():
    with connect() as db:
        t = tasks(db)
        r = receipts(db)
    return {'tasks': t, 'receipts': r, 'stats': {
        'open_tasks': sum(v['status']=='open' for v in t),
        'blockers': sum(v['status']=='open' and bool(v['blocker']) for v in t),
        'completed': sum(v['status']=='done' for v in t),
        'runs': len(r)
    }}

def detect_intent(command):
    s = command.lower().strip()
    if any(w in s for w in ('plan my day','schedule my day','organize my day','prioritize','timeblock','time block')):
        return 'day_plan'
    if any(w in s for w in ('launch','release','ship','readiness','blockers')):
        return 'launch_audit'
    if any(w in s for w in ('follow up','follow-up','email','customer update','draft')):
        return 'follow_up'
    if any(w in s for w in ('portfolio','executive brief','project brief','status report','status brief')):
        return 'executive_brief'
    return 'unknown'

def workday(open_tasks):
    ordered = sorted(open_tasks, key=lambda t: (-PRIORITY[t['priority']], -int(t['blocker']), t['minutes'], t['title']))
    cursor = 9 * 60
    agenda=[]; overflow=[]
    for t in ordered:
        if cursor < 12*60 and cursor+t['minutes'] > 12*60:
            cursor=13*60
        if cursor+t['minutes']>17*60:
            overflow.append(t['title']); continue
        h1,m1=divmod(cursor,60); cursor += t['minutes']; h2,m2=divmod(cursor,60)
        agenda.append({'time': f'{h1:02d}:{m1:02d}–{h2:02d}:{m2:02d}', 'title':t['title'],'priority':t['priority'],'project':t['project']})
    return {'title':'Prioritized workday', 'summary':f'{len(agenda)} scheduled tasks; {len(overflow)} overflow tasks. Local timeblocks start at 09:00.',
            'items':agenda,'overflow':overflow}

def launch_audit(open_tasks):
    related=[t for t in open_tasks if t['project'].lower()=='launch' or any(k in t['title'].lower() for k in ('launch','release','deploy','demo','test'))]
    blockers=[t for t in related if t['blocker']]
    return {'title':'Launch readiness inspection', 'summary':f'{len(related)} relevant open tasks; {len(blockers)} marked blockers. No deployment or hardware checks were performed.',
            'items':[{'task':t['title'],'status':'BLOCKER' if t['blocker'] else 'OPEN','priority':t['priority']} for t in related],
            'ready':not bool(blockers), 'next_action':blockers[0]['title'] if blockers else ('Review remaining open tasks' if related else 'Add launch tasks')}

def follow_up(open_tasks):
    customers=[t for t in open_tasks if 'customer' in t['project'].lower()]
    lines=[f"- {x['title']}" for x in customers]
    body='Subject: Project update and next steps\n\nHello,\n\nHere is an update on the items we are working through:\n'+('\n'.join(lines) if lines else '- We are preparing the next update.')+'\n\nI will share the next concrete milestone when it is verified.\n\nBest,\nTitanU'
    return {'title':'Customer follow-up draft', 'summary':f'Drafted from {len(customers)} open customer tasks; no email was sent.', 'draft':body,'items':lines}

def executive_brief(open_tasks):
    projects={}
    for t in open_tasks:
        projects.setdefault(t['project'],[]).append(t)
    rows=[]
    for k,v in sorted(projects.items()):
        rows.append({'project':k,'open':len(v),'blockers':sum(t['blocker'] for t in v),'next':sorted(v,key=lambda x:-PRIORITY[x['priority']])[0]['title']})
    return {'title':'Portfolio command brief','summary':f'{len(rows)} active workstreams. Derived only from tasks stored locally.','items':rows}

def execute(command):
    command=command.strip()
    if not command or len(command)>800:
        raise ValueError('Command must be 1–800 characters')
    intent=detect_intent(command)
    if intent=='unknown':
        raise ValueError('Supported commands: plan my day; check launch readiness; draft customer follow-up; portfolio brief.')
    receipt_id=uuid.uuid4().hex[:16]
    now=utcnow()
    with connect() as db:
        open_tasks=[x for x in tasks(db) if x['status']=='open']
        events=[('Intent Router',f'Classified request as {intent}'),('Task Reader',f'Read {len(open_tasks)} open local tasks')]
        fn={'day_plan':workday,'launch_audit':launch_audit,'follow_up':follow_up,'executive_brief':executive_brief}[intent]
        result=fn(open_tasks)
        events.extend([('Specialist Agent',f'Executed {intent} deterministic tool'),('Evidence Verifier','Recorded outcome; no external system was contacted')])
        db.execute('INSERT INTO receipts VALUES(?,?,?,?,?)',(receipt_id,command,intent,json.dumps(result,sort_keys=True),now))
        db.executemany('INSERT INTO events(receipt_id,agent,detail,occurred_at) VALUES(?,?,?,?)',[(receipt_id,*event,utcnow()) for event in events])
    return {'receipt_id':receipt_id,'intent':intent,'result':result,'agents':[{'name':a,'action':b} for a,b in events],'created_at':now}

class Handler(BaseHTTPRequestHandler):
    server_version='TitanUCommander/1.0'
    def log_message(self, fmt, *args):
        sys.stderr.write(f'{self.address_string()} {fmt % args}\n')
    def send_common_headers(self, status,ctype, length):
        self.send_response(status)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(length))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; base-uri 'none'; object-src 'none'; form-action 'self'")
        self.end_headers()
    def output(self, code, value):
        b=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        self.send_common_headers(code,'application/json; charset=utf-8',len(b));self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path); route=p.path
        if route=='/health':
            return self.output(200,{'status':'ok','product':'TitanU Sovereign Agent Commander','simulated_alexa':True,'uptime_sec':int(time.monotonic()-STARTED)})
        if route=='/api/state': return self.output(200,state())
        if route.startswith('/api/receipt/'):
            id=route.rsplit('/',1)[-1]
            if not re.fullmatch(r'[0-9a-f]{16}',id): return self.output(400,{'error':'Invalid receipt ID'})
            with connect() as db:
                x=db.execute('SELECT * FROM receipts WHERE id=?',(id,)).fetchone()
                ev=[dict(z) for z in db.execute('SELECT agent,detail,occurred_at FROM events WHERE receipt_id=? ORDER BY id',(id,))]
            if not x:return self.output(404,{'error':'Not found'})
            return self.output(200,{'receipt':dict(x)|{'outcome':json.loads(x['outcome'])},'events':ev})
        if route in ('/','/index.html','/assets/app.js','/assets/style.css'):
            f={'/':'index.html','/index.html':'index.html','/assets/app.js':'assets/app.js','/assets/style.css':'assets/style.css'}[route]
            b=(ROOT/f).read_bytes()
            typ='text/html; charset=utf-8' if f.endswith('.html') else ('application/javascript; charset=utf-8' if f.endswith('.js') else 'text/css; charset=utf-8')
            self.send_common_headers(200,typ,len(b));self.wfile.write(b);return
        self.output(404,{'error':'Not found'})
    def body(self):
        size=int(self.headers.get('Content-Length','0'))
        if size<=0 or size>MAX_BYTES:raise ValueError('Request must be 1–32768 bytes')
        obj=json.loads(self.rfile.read(size))
        if not isinstance(obj,dict):raise ValueError('Expected JSON object')
        return obj
    def do_POST(self):
        try:
            path=urlparse(self.path).path; data=self.body()
            if path=='/api/command':
                if not isinstance(data.get('command'),str):raise ValueError('Command string is required')
                return self.output(200,execute(data['command']))
            if path=='/api/tasks':
                title=data.get('title','');priority=data.get('priority','medium');minutes=data.get('minutes',30);project=data.get('project','General')
                if not isinstance(title,str) or not 1<=len(title.strip())<=180: raise ValueError('Task title must be 1–180 characters')
                if priority not in PRIORITY:raise ValueError('Priority must be high, medium, or low')
                if type(minutes) is not int or not 5<=minutes<=480: raise ValueError('Duration must be 5–480 minutes')
                if not isinstance(project,str) or not 1<=len(project.strip())<=70:raise ValueError('Project must be 1–70 characters')
                blocker=data.get('blocker',False)
                if type(blocker) is not bool:raise ValueError('blocker must be boolean')
                item={'id':str(uuid.uuid4()),'title':title.strip(),'priority':priority,'minutes':minutes,'project':project.strip(),'blocker':int(blocker),'status':'open','created_at':utcnow()}
                with connect() as db:db.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?)',tuple(item.values()))
                return self.output(201,{'task':item})
            if path.startswith('/api/tasks/'):
                id=path.rsplit('/',1)[-1]
                if not re.fullmatch(r'[0-9a-f-]{36}',id):raise ValueError('Invalid task ID')
                status=data.get('status')
                if status not in ('open','done'):raise ValueError('Status must be open or done')
                with connect() as db:
                    cur=db.execute('UPDATE tasks SET status=? WHERE id=?',(status,id))
                    if not cur.rowcount: return self.output(404,{'error':'Task not found'})
                return self.output(200,{'id':id,'status':status})
            self.output(404,{'error':'Not found'})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as err:
            self.output(400,{'error':str(err)[:240]})
        except Exception:
            self.output(500,{'error':'Unexpected server error'})

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default=os.getenv('TITANU_HOST','127.0.0.1'))
    parser.add_argument('--port',default=int(os.getenv('PORT','8787')),type=int)
    args=parser.parse_args()
    initialize()
    srv=ThreadingHTTPServer((args.host,args.port),Handler)
    print(f'TitanU Commander READY http://{args.host}:{srv.server_port}',flush=True)
    try:srv.serve_forever()
    except KeyboardInterrupt:pass
    finally:srv.server_close()

if __name__=='__main__':main()