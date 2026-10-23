import os
import tempfile
import unittest
from pathlib import Path
import app

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        app.DATA = Path(self.tmp.name)
        app.initialize()
    def tearDown(self):self.tmp.cleanup()
    def test_seeded(self):
        s=app.state();self.assertEqual(s['stats']['open_tasks'],6);self.assertEqual(s['stats']['blockers'],2)
    def test_plan(self):
        x=app.execute('Alexa, plan my day');self.assertEqual(x['intent'],'day_plan');self.assertTrue(x['result']['items'])
        self.assertEqual(len(x['agents']),4);self.assertEqual(app.state()['stats']['runs'],1)
    def test_launch(self):
        x=app.execute('Alexa, check launch readiness');self.assertEqual(x['result']['ready'],False)
        self.assertEqual(x['result']['next_action'],'Finish launch demonstration')
    def test_customer(self):
        x=app.execute('Alexa, draft customer follow-up');self.assertIn('no email was sent',x['result']['summary'])
        self.assertIn('Subject:',x['result']['draft'])
    def test_brief(self):
        x=app.execute('Alexa, portfolio brief');self.assertGreater(len(x['result']['items']),1)
    def test_unknown_refuses(self):
        with self.assertRaises(ValueError):app.execute('Alexa, unlock my front door')
    def test_sqlite_receipt(self):
        x=app.execute('schedule my day')
        with app.connect() as db:
            n=db.execute('SELECT COUNT(*) FROM events WHERE receipt_id=?',(x['receipt_id'],)).fetchone()[0]
        self.assertEqual(n,4)
    def test_no_duplicate_seed(self):
        app.initialize();self.assertEqual(app.state()['stats']['open_tasks'],6)
    def test_ui_assets(self):
        for x in ('index.html','assets/app.js','assets/style.css'):
            self.assertTrue((app.ROOT/x).is_file())

if __name__=='__main__':unittest.main(verbosity=2)

# HTTP proof suite is discoverable separately even though the CLI also supports unittest.
class TestHttp(unittest.TestCase):
    def setUp(self):
        import threading
        from http.server import ThreadingHTTPServer
        self.tmp=tempfile.TemporaryDirectory();app.DATA=Path(self.tmp.name);app.initialize()
        self.srv=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.thread=threading.Thread(target=self.srv.serve_forever,daemon=True);self.thread.start()
        self.base='http://127.0.0.1:'+str(self.srv.server_port)
    def tearDown(self):
        self.srv.shutdown();self.srv.server_close();self.thread.join(timeout=2);self.tmp.cleanup()
    def call(self,path,payload=None):
        from urllib.request import urlopen,Request
        import json
        if payload is None: r=urlopen(self.base+path,timeout=3)
        else:r=urlopen(Request(self.base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST'),timeout=3)
        with r:return json.load(r)
    def test_full_lifecycle(self):
        self.assertEqual(self.call('/health')['status'],'ok')
        first=self.call('/api/state');self.assertEqual(first['stats']['open_tasks'],6)
        new=self.call('/api/tasks',{'title':'Review verification evidence','priority':'high','minutes':15,'project':'Launch','blocker':True})['task']
        run=self.call('/api/command',{'command':'Alexa, plan my day'})
        self.assertTrue(any(x['title']==new['title'] for x in run['result']['items']))
        self.assertEqual(self.call('/api/receipt/'+run['receipt_id'])['receipt']['intent'],'day_plan')
        self.call('/api/tasks/'+new['id'],{'status':'done'})
        self.assertEqual(self.call('/api/state')['stats']['open_tasks'],6)