import json
import tempfile
import time
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import app

class TestMissionEngine(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        app.DATA=Path(self.temp.name)
        app.initialize()
        self.engine=app.mission_engine()
    def tearDown(self):self.temp.cleanup()
    def complete(self,objective='Prepare launch and customer outreach with verified evidence',writes=False):
        mid=self.engine.start(objective,writes)['id']
        for _ in range(200):
            x=self.engine.detail(mid)
            if x['mission']['status'] in ('completed','failed','cancelled'):return x
            time.sleep(0.02)
        self.fail('mission timeout')
    def test_autonomous_mission_completes(self):
        x=self.complete()
        self.assertEqual(x['mission']['status'],'completed',x['mission']['error'])
        self.assertGreaterEqual(len(x['steps']),7)
        self.assertTrue(all(s['status']=='passed' for s in x['steps']))
        self.assertTrue(x['proof']['verified'])
        self.assertEqual(x['proof']['artifacts'],3)
    def test_does_not_write_without_authorization(self):
        before=app.state()['stats']['open_tasks']
        x=self.complete(writes=False)
        self.assertEqual(x['mission']['status'],'completed',x['mission']['error'])
        self.assertEqual(app.state()['stats']['open_tasks'],before)
    def test_authorized_local_write_and_replan(self):
        before=app.state()['stats']['open_tasks']
        x=self.complete(writes=True)
        self.assertEqual(x['mission']['status'],'completed',x['mission']['error'])
        self.assertGreater(app.state()['stats']['open_tasks'],before)
        self.assertLessEqual(app.state()['stats']['open_tasks']-before,3)
        self.assertTrue(any(e['kind']=='REPLAN' for e in x['events']))
        self.assertTrue(any(s['agent']=='Adaptive Planner' for s in x['steps']))
        self.assertTrue(x['proof']['verified'])
    def test_evidence_changes_with_goal(self):
        a=self.complete('Prepare launch blockers and execution timeline')
        b=self.complete('Prepare research strategy and portfolio plan')
        self.assertNotEqual(a['mission']['goal'],b['mission']['goal'])
        self.assertNotEqual(a['steps'][0]['result']['snapshot_hash'],'')
        self.assertEqual(b['mission']['status'],'completed',b['mission']['error'])
    def test_output_files_download_and_integrity(self):
        x=self.complete()
        for item in x['artifacts']:
            blob=self.engine.artifact(x['mission']['id'],item['name'])
            self.assertIsNotNone(blob)
            self.assertEqual(len(blob),item['bytes'])
        self.assertIn(b'TitanU mission',self.engine.artifact(x['mission']['id'],'mission-brief.md'))
    def test_artifact_tamper_detection(self):
        x=self.complete()
        f=app.DATA/'missions'/x['mission']['id']/'mission-brief.md'
        f.write_text(f.read_text()+'\nMALICIOUS UPDATE\n')
        proof=self.engine.verify(x['mission']['id'])
        self.assertFalse(proof['verified'])
        self.assertIn('Artifact integrity failure: mission-brief.md',proof['problems'])
        self.assertIsNone(self.engine.artifact(x['mission']['id'],'mission-brief.md'))
    def test_event_chain_tamper_detection(self):
        x=self.complete()
        with app.connect() as db:
            db.execute('UPDATE mission_events SET payload=? WHERE mission_id=? AND seq=2',('{"tampered":true}',x['mission']['id']))
        self.assertFalse(self.engine.verify(x['mission']['id'])['verified'])
    def test_path_guard(self):
        x=self.complete()
        self.assertIsNone(self.engine.artifact(x['mission']['id'],'../app.py'))
        self.assertIsNone(self.engine.artifact('invalid-id','mission-brief.md'))
    def test_bad_input_rejected(self):
        for goal in ('', 'abcd', 'z'*501,42):
            with self.assertRaises(ValueError):self.engine.start(goal)
        with self.assertRaises(ValueError):self.engine.start('Assess launch readiness',allow_local_writes='yes')
    def test_mcp_contract(self):
        init=app.mcp_call({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'probe','version':'1'}}})
        self.assertEqual(init['result']['protocolVersion'],'2025-11-25')
        tools=app.mcp_call({'jsonrpc':'2.0','id':2,'method':'tools/list'})['result']['tools']
        self.assertEqual(len(tools),4)
        self.assertTrue(all('inputSchema' in x for x in tools))
    def test_mcp_launch_to_verify(self):
        mid=None
        call=app.mcp_call({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'titanu_mission_launch','arguments':{'goal':'Coordinate release readiness and customer communication'}}})
        self.assertFalse(call['result']['isError'])
        mid=json.loads(call['result']['content'][0]['text'])['id']
        for _ in range(200):
            x=self.engine.detail(mid)
            if x['mission']['status']=='completed':break
            if x['mission']['status']=='failed':self.fail(x['mission']['error'])
            time.sleep(0.02)
        proof=app.mcp_call({'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'titanu_mission_verify','arguments':{'mission_id':mid}}})
        self.assertTrue(json.loads(proof['result']['content'][0]['text'])['verified'])
    def test_concurrent_agents_present(self):
        x=self.complete()
        names={s['agent'] for s in x['steps']}
        self.assertTrue({'Scope Scout','Risk Analyst','Timeline Planner','Customer Comms','Artifact Builder','Independent Auditor'}<=names)
        self.assertTrue(any(e['kind']=='FAN_OUT' for e in x['events']))
        self.assertTrue(any(e['kind']=='FAN_IN' for e in x['events']))

class TestMissionHTTP(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();app.DATA=Path(self.tmp.name);app.initialize()
        self.server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2);self.tmp.cleanup()
    def request(self,path,payload=None,headers=None):
        if payload is None:req=Request(self.base+path)
        else:req=Request(self.base+path,method='POST',headers={'Content-Type':'application/json',**(headers or {})},data=json.dumps(payload).encode())
        with urlopen(req,timeout=5) as f:
            if f.status==202 and not f.headers.get('Content-Length'):return None
            return json.load(f)
    def test_http_mission_lifecycle(self):
        x=self.request('/api/missions',{'goal':'Launch work and verify each agent artifact','allow_local_writes':False})
        mid=x['id']
        for _ in range(200):
            result=self.request('/api/missions/'+mid)
            if result['mission']['status'] in ('completed','failed'):break
            time.sleep(.02)
        self.assertEqual(result['mission']['status'],'completed',result['mission']['error'])
        self.assertTrue(self.request('/api/missions/'+mid+'/verify')['verified'])
        self.assertEqual(len(self.request('/api/missions')['missions']),1)
        with urlopen(self.base+'/api/missions/'+mid+'/artifacts/mission-brief.md') as f:
            self.assertIn('TitanU mission execution report',f.read().decode())
    def test_streamable_http_mcp(self):
        init=self.request('/mcp',{'jsonrpc':'2.0','id':'one','method':'initialize','params':{'protocolVersion':'2025-11-25'}},headers={'Accept':'application/json, text/event-stream'})
        self.assertEqual(init['result']['protocolVersion'],'2025-11-25')
        self.assertEqual(len(self.request('/mcp',{'jsonrpc':'2.0','id':'two','method':'tools/list'})['result']['tools']),4)
    def test_mcp_origin_protection(self):
        req=Request(self.base+'/mcp',method='POST',data=b'{"jsonrpc":"2.0","id":1,"method":"initialize"}',headers={'Content-Type':'application/json','Origin':'https://attacker.example'})
        with self.assertRaises(HTTPError) as e:urlopen(req,timeout=3)
        self.assertEqual(e.exception.code,403)

if __name__=='__main__':unittest.main(verbosity=2)