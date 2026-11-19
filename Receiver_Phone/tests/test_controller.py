"""Synthetic protocol/failure tests. These are NOT research recordings."""
import copy
import hashlib
import http.client
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controller as c

def archive(plan, device='test-device', extra=None, bad_hash=False):
    header='sensor_elapsed_ns,received_elapsed_ns,device_time_est_ns,controller_time_est_ns,clock_sample_id,x,y,z,accuracy\n'
    rows=''.join(f'{i*20000000},{i*20000000+100},1,1,test,1.0,2.0,3.0,3\n' for i in range(101))
    files={'accelerometer.csv':(header+rows).encode(),'gyroscope.csv':(header+rows).encode(),
           'labels.csv':b'phase_index,trial,kind,label,state\n',
           'clock_sync.csv':b'sample_id,controller_id,phone_sample_ns,offset_ns,rtt_ns\n',
           'metadata.json':json.dumps(dict(session_id=plan['session_id'],pid=plan['pid'],device_id=device,status='complete')).encode()}
    manifest={n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in files.items()}
    if bad_hash:manifest['accelerometer.csv']['sha256']='0'*64
    files['manifest.json']=json.dumps(manifest).encode()
    if extra:files.update(extra)
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        for n,data in files.items():z.writestr(n,data)
    return b.getvalue()

class PlanTests(unittest.TestCase):
    def test_complete_modern_dictionary(self):
        self.assertEqual(len(c.ACTIONS),12);self.assertEqual(len(c.SIGNS),14)
        for label in ['COOK','TOILET','HUNGRY','chop_food','stir_pot']:self.assertIn(label,c.ACTIONS+c.SIGNS)
    def test_reproducible_randomization_and_no_gap_truth(self):
        req=dict(pid='P04',session='S01',mode='isolated',classes=['walk','COOK'],reps=3,seed=17)
        a=c.make_plan(req,100);b=c.make_plan(req,100)
        self.assertEqual(a['phases'],b['phases'])
        self.assertEqual(sum(p['kind']=='perform' for p in a['phases']),6)
        self.assertTrue(all(p['state']=='' for p in a['phases'] if p['kind'] in ('ready','rest','sync')))
        for x,y in zip(a['phases'],a['phases'][1:]):self.assertEqual(x['end_ns'],y['start_ns'])
    def test_validation(self):
        for req in [dict(pid='../escape'),dict(pid='P04',session='../x'),dict(pid='P04',mode='isolated',classes=['invented']),dict(pid='P04',mode='isolated',classes=['fall'],reps=5)]:
            with self.assertRaises(ValueError):c.make_plan(req,0)
    def test_mixed_sequences_really_alternate(self):
        p=c.make_plan(dict(pid='P05',mode='meal'),0)
        states=[p['state'] for p in p['phases'] if p['kind']=='perform']
        self.assertGreater(sum(x!=y for x,y in zip(states,states[1:])),4)
    def test_event_stop_and_next_start_have_unscored_buffer(self):
        kinds={'perform','baseline','ordinary','sync'}
        for mode in ['pilot','meal','tv','cleaning','baseline','ordinary','isolated']:
            p=c.make_plan(dict(pid='P00',mode=mode,classes=['walk','WATER'],reps=1),0)
            for a,b in zip(p['phases'],p['phases'][1:]):
                self.assertFalse(a['kind'] in kinds and b['kind'] in kinds,mode)
            for phase in p['phases']:
                if phase['kind'] in ('ready','rest'):self.assertEqual(phase['state'],'')

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=c.Store(self.tmp.name)
        self.server=c.ThreadingHTTPServer(('127.0.0.1',0),c.Handler);self.server.store=self.store
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.db.close();self.tmp.cleanup()
    def call(self,path,data=None,headers=None,auth=True):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        h={'X-Token':self.store.token} if auth else {}
        if headers:h.update(headers)
        if isinstance(data,dict):data=json.dumps(data).encode();h['Content-Type']='application/json'
        conn.request('POST' if data is not None else 'GET',path,body=data,headers=h)
        r=conn.getresponse();status=r.status;raw=r.read();conn.close();return status,json.loads(raw)
    def phone(self,**kw):
        info=dict(device_id='test-device',model='SYNTHETIC TEST',accelerometer=True,gyroscope=True,active_session='',clock_controller_id=self.store.controller_id,clock_age_ms=0,clock_rtt_ms=5)
        info.update(kw);return self.call('/api/heartbeat',info)
    def start(self):
        self.phone();code,result=self.call('/api/session',dict(device_id='test-device',pid='P04',session='S01',mode='pilot'))
        self.assertEqual(code,200,result);return result['session_id']
    def plan(self,sid):return json.loads((self.store.path(sid)/'plan.json').read_text())
    def upload(self,sid,b,sha=None):return self.call('/api/upload',b,{'X-Session-ID':sid,'X-SHA256':sha or hashlib.sha256(b).hexdigest(),'Content-Type':'application/zip'})
    def test_auth_and_clock(self):
        self.assertEqual(self.call('/api/state',auth=False)[0],401)
        code,t=self.call('/api/clock');self.assertEqual(code,200);self.assertGreaterEqual(t['send_ns'],t['receive_ns'])
    def test_browser_can_load_cue_audio_module(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        conn.request('GET','/cues.js');response=conn.getresponse();body=response.read();conn.close()
        self.assertEqual(response.status,200);self.assertIn('javascript',response.getheader('Content-Type'))
        self.assertIn(b'CueSound',body)
    def test_rejects_foreign_origin(self):
        self.assertEqual(self.call('/api/session',{'pid':'P04'},headers={'Origin':'http://evil.invalid'})[0],403)
    def test_requires_sensors_and_clock(self):
        for kw in [dict(gyroscope=False),dict(clock_controller_id='stale-controller'),dict(clock_age_ms=999999),dict(clock_rtt_ms=500)]:
            self.phone(**kw);self.assertEqual(self.call('/api/session',dict(device_id='test-device',pid='P04'))[0],400)
    def test_only_one_active_session(self):
        self.start();self.assertEqual(self.call('/api/session',dict(device_id='test-device',pid='P05'))[0],400)
    def test_verified_upload_and_idempotent_retry(self):
        sid=self.start();b=archive(self.plan(sid));code,result=self.upload(sid,b)
        self.assertEqual(code,200,result);dest=self.store.path(sid)
        self.assertTrue((dest/'transfer_receipt.json').exists());self.assertTrue((dest/'phone_original.zip').exists())
        q=json.loads((dest/'phone/quality.json').read_text());self.assertEqual(q['accelerometer']['median_hz'],50);self.assertTrue(q['review_required'])
        self.assertEqual(self.upload(sid,b)[1]['already_received'],True)
        self.assertEqual(self.store.snapshot()['sessions'][0]['status'],'received_complete')
    def test_hash_mismatch_and_zip_traversal(self):
        sid=self.start();p=self.plan(sid)
        for b,h in [(archive(p),'0'*64),(archive(p,bad_hash=True),None),(archive(p,extra={'../escape':b'no'}),None)]:
            self.assertEqual(self.upload(sid,b,h)[0],400)
            self.assertFalse((self.store.path(sid)/'phone').exists())
        self.assertFalse(list(self.store.path(sid).glob('*.part')))
    def test_never_overwrites_a_different_recording(self):
        sid=self.start();p=self.plan(sid);b=archive(p);self.assertEqual(self.upload(sid,b)[0],200)
        # A byte-distinct but otherwise valid archive must not replace the first.
        p2=dict(p);b2=archive(p2)+b'changed ZIP comment bytes'
        self.assertEqual(self.upload(sid,b2)[0],400)
        self.assertEqual(c.digest(self.store.path(sid)/'phone_original.zip'),hashlib.sha256(b).hexdigest())
    def test_stop_before_start_cancels_pending_start(self):
        sid=self.start();self.call('/api/stop',dict(session_id=sid))
        cmd=self.call('/api/command?device=test-device')[1]['command'];self.assertEqual(cmd['kind'],'STOP')
        self.call('/api/ack',dict(device_id='test-device',id=cmd['id'],ok=True,result={'not_started':True}))
        self.assertEqual(self.store.snapshot()['sessions'][0]['status'],'cancelled')
    def test_metadata_wrong_person_rejected(self):
        sid=self.start();p=self.plan(sid);p['pid']='P05';self.assertEqual(self.upload(sid,archive(p))[0],400)
    def test_retry_after_file_commit_but_before_database_commit(self):
        sid=self.start();b=archive(self.plan(sid));self.assertEqual(self.upload(sid,b)[0],200)
        self.store.db.execute("UPDATE sessions SET archive_sha=NULL,status='recording' WHERE id=?",(sid,));self.store.db.commit()
        (self.store.path(sid)/'transfer_receipt.json').unlink()
        self.assertEqual(self.upload(sid,b)[0],200)
        self.assertEqual(self.store.snapshot()['sessions'][0]['status'],'received_complete')
    def test_retry_after_extraction_before_archive_commit(self):
        sid=self.start();b=archive(self.plan(sid));dest=self.store.path(sid)
        phone=dest/'phone';phone.mkdir()
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            for name in c.REQUIRED|{'manifest.json'}:(phone/name).write_bytes(z.read(name))
        self.assertEqual(self.upload(sid,b)[0],200)
        self.assertEqual(c.digest(dest/'phone_original.zip'),hashlib.sha256(b).hexdigest())

if __name__=='__main__':unittest.main(verbosity=2)
