"""Paired-command protocol tests; every file and device here is synthetic."""
import contextlib
import csv
import io
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controller as c
import run_block as runner
from collection_blocks import BLOCKS, SEATED_ACTIONS

class BlockTests(unittest.TestCase):
    def test_receiver_identity_accepts_both_entrypoints_but_not_names_in_arguments(self):
        for argv,expected in [
            (['/usr/bin/python3','/collector/capture_receiver.py'],True),
            (['/usr/bin/python3','/preserved/wifi_rx.py'],True),
            (['/usr/bin/python3','-u','/collector/capture_receiver.py'],True),
            (['/usr/bin/python3','-W','ignore','/collector/capture_receiver.py'],True),
            (['/usr/bin/python3','-c','print("wifi_rx.py")'],False),
            (['/usr/bin/python3','other.py','capture_receiver.py'],False),
            (['echo','capture_receiver.py'],False),
        ]:
            with self.subTest(argv=argv),mock.patch('pathlib.Path.read_bytes',return_value=b'\0'.join(x.encode() for x in argv)+b'\0'):
                self.assertIs(runner.process_alive(123),expected)

    def test_real_wrapper_process_hands_shared_mixed_plan_to_simulated_phone(self):
        # No SDR or physical phone: actual process detection, growing CSV,
        # HTTP controller and run_block handoff are exercised together.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'data/csi/P04/S01/synthetic';folder.mkdir(parents=True)
            raw=folder/'csi.csv';script=root/'capture_receiver.py'
            script.write_text("import sys,time\nfrom pathlib import Path\np=Path(sys.argv[1]);p.write_text('Packet,Timestamp_us,Channel\\n'+'0,1,1\\n'*30)\ni=1\nwhile True:\n with p.open('a') as f:f.write(f'{i},{time.time_ns()//1000},1\\n')\n i+=1;time.sleep(.02)\n")
            proc=subprocess.Popen([sys.executable,'-u',str(script),str(raw)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            store=c.Store(root/'data');server=c.ThreadingHTTPServer(('127.0.0.1',0),c.Handler);server.store=store
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                deadline=time.monotonic()+5
                while (not raw.exists() or raw.stat().st_size<100) and time.monotonic()<deadline:time.sleep(.02)
                self.assertIsNone(proc.poll());self.assertTrue(runner.process_alive(proc.pid))
                meta=dict(recording_id='synthetic-csi',block='mixed_activity',status='running',receiver_pid=proc.pid,csi_csv=str(raw))
                (folder/'metadata.json').write_text(json.dumps(meta))
                runner.api(server.server_port,store.token,'/api/heartbeat',dict(device_id='synthetic-phone',accelerometer=True,gyroscope=True,clock_controller_id=store.controller_id,clock_age_ms=0,clock_rtt_ms=1,active_session=''))
                argv=['run_block.py','mixed_activity','--pid','P04','--port',str(server.server_port),'--managed-csi']
                with mock.patch.object(runner,'ROOT',root),mock.patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.main(),0)
                saved=store.snapshot()['sessions'];self.assertEqual(len(saved),1)
                plan=saved[0]['plan'];self.assertEqual(plan['block'],'mixed_activity');self.assertEqual(plan['paired_csi_csv'],str(raw))
                link=json.loads(next(folder.glob('phone_plan_*.json')).read_text());self.assertEqual(link['plan'],plan)
                with next(folder.glob('planned_labels_*.csv')).open() as f:labels=list(csv.DictReader(f))
                self.assertEqual([x['label'] for x in labels],[x['label'] for x in plan['phases']])
                self.assertIsNone(proc.poll())
            finally:
                proc.terminate();proc.wait(timeout=5);proc.stderr.close()
                server.shutdown();server.server_close();thread.join();store.db.close()

    def test_all_named_runs_have_no_extra_calibration_or_pilot_events(self):
        for block in BLOCKS:
            plan=c.make_plan(dict(pid='P04',block=block),0)
            self.assertFalse(any(p['kind']=='sync' for p in plan['phases']))
            if block not in ('stand_still','sit_still'):
                self.assertFalse(any(p['kind']=='baseline' for p in plan['phases']))
            else:
                self.assertEqual([p['kind'] for p in plan['phases']],['ready','baseline'])
                self.assertEqual(plan['phases'][1]['end_ns']-plan['phases'][1]['start_ns'],120_000_000_000)
    def test_activity_sign_and_mixed_order_match_actual_previous_recordings(self):
        collector=Path(__file__).resolve().parents[1]
        root=collector.parents[1]
        profiles=json.loads((collector/'previous_collection_protocol.json').read_text())
        for pid,blocks in profiles.items():
            for block,source in blocks.items():
                with (root/source['source']).open() as f:
                    original=[r for r in csv.DictReader(f) if r['type'] in ('activity','sign')]
                plan=c.make_plan(dict(pid=pid,block=block),0)
                events=[p for p in plan['phases'] if p['kind']=='perform']
                self.assertEqual([p['label'] for p in events],[r['label'] for r in original])
                self.assertEqual([p['posture'] for p in events],[r['posture'] for r in original])
    def test_class_coverage_and_posture(self):
        for block,classes in [('activities_standing',c.ACTIONS),
                              ('activities_seated',SEATED_ACTIONS),
                              ('signs_standing',c.SIGNS),('signs_seated',c.SIGNS)]:
            plan=c.make_plan(dict(pid='P04',block=block,reps=5,seed=401),0)
            events=[p['label'] for p in plan['phases'] if p['kind']=='perform']
            expected={label:(5 if label=='fall' or block.startswith('signs_') else 10) for label in classes}
            self.assertEqual(len(events),sum(expected.values()))
            for label,count in expected.items():self.assertEqual(events.count(label),count)
            self.assertEqual(plan['posture'],'seated' if block.endswith('seated') else 'standing')
    def test_stillness_is_separate_and_seated_never_prompts_standing(self):
        for block,label in [('stand_still','stand_still'),('sit_still','sit_still')]:
            plan=c.make_plan(dict(pid='P05',block=block),0)
            scored=[p for p in plan['phases'] if p['kind']=='baseline' and p['duration_s']==120]
            self.assertEqual(len(scored),1);self.assertEqual(scored[0]['label'],label)
            self.assertEqual({p['label'] for p in plan['phases'] if p['kind']=='baseline'},{label})
    def test_named_blocks_reproducible_with_buffers_and_link_identity(self):
        for block in BLOCKS:
            req=dict(pid='P04',block=block,seed=401,reps=2,paired_csi_id='test-csi',paired_csi_csv='/synthetic/csi.csv')
            a=c.make_plan(req,100);b=c.make_plan(req,100)
            self.assertEqual(a['phases'],b['phases'])
            self.assertEqual(a['paired_csi_id'],'test-csi')
            kinds={'perform','baseline','ordinary','sync'}
            self.assertFalse(any(x['kind'] in kinds and y['kind'] in kinds for x,y in zip(a['phases'],a['phases'][1:])))
    def test_rejects_unknown_profile_and_invented_still_posture(self):
        for req in [dict(pid='P04',block='imaginary'),dict(pid='P04',mode='still'),dict(pid='P04',posture='flying')]:
            with self.assertRaises(ValueError):c.make_plan(req,0)
    def test_csi_must_be_alive_growing_and_match_block(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);folder=root/'data/csi/P04/S01/test';folder.mkdir(parents=True)
            raw=folder/'csi.csv';raw.write_text('x'*200)
            meta=dict(block='signs_seated',status='running',receiver_pid=123,csi_csv=str(raw))
            (folder/'metadata.json').write_text(json.dumps(meta))
            with mock.patch.object(runner,'process_alive',return_value=False):
                with self.assertRaises(ValueError):runner.find_csi(root,'P04','S01','signs_seated')
            with mock.patch.object(runner,'process_alive',return_value=True),mock.patch.object(runner.time,'sleep'):
                with self.assertRaises(ValueError):runner.find_csi(root,'P04','S01','signs_seated')
            def append(_):
                with raw.open('a') as f:f.write('new row\n')
            with mock.patch.object(runner,'process_alive',return_value=True),mock.patch.object(runner.time,'sleep',side_effect=append):
                self.assertEqual(runner.find_csi(root,'P04','S01','signs_seated')[0],folder)
                with self.assertRaises(ValueError):runner.find_csi(root,'P04','S01','signs_standing')
    def test_command_uses_server_plan_for_csi_labels_without_second_shuffle(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);store=c.Store(root/'data')
            server=c.ThreadingHTTPServer(('127.0.0.1',0),c.Handler);server.store=store
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            folder=root/'synthetic-csi';folder.mkdir()
            meta=dict(recording_id='synthetic-csi-id',csi_csv=str(folder/'csi.csv'))
            try:
                runner.api(server.server_port,store.token,'/api/heartbeat',dict(device_id='test-device',
                    accelerometer=True,gyroscope=True,clock_controller_id=store.controller_id,
                    clock_age_ms=0,clock_rtt_ms=1,active_session=''))
                argv=['run_block.py','signs_seated','--pid','P04','--port',str(server.server_port)]
                with mock.patch.object(runner,'ROOT',root),mock.patch.object(runner,'find_csi',return_value=(folder,meta)),mock.patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.main(),0)
                saved=store.snapshot()['sessions'][0]['plan']
                linked=json.loads(next(folder.glob('phone_plan_*.json')).read_text())['plan']
                self.assertEqual(saved,linked)
                self.assertEqual(saved['paired_csi_id'],'synthetic-csi-id')
                with next(folder.glob('planned_labels_*.csv')).open() as f:rows=list(csv.DictReader(f))
                self.assertEqual([r['label'] for r in rows],[p['label'] for p in saved['phases']])
                self.assertEqual([int(r['t_start_us']) for r in rows],[p['start_ns']//1000 for p in saved['phases']])
            finally:
                server.shutdown();server.server_close();thread.join();store.db.close()

if __name__=='__main__':unittest.main()
