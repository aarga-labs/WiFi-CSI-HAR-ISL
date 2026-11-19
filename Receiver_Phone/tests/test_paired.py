"""One-command orchestration checks, with simulated processes and no hardware."""
import contextlib
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_paired as paired

class PairedTests(unittest.TestCase):
    def test_existing_receiver_is_left_alone(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);folder=root/'data/csi/P04/S01/existing';folder.mkdir(parents=True)
            (root/'data/pairing.json').write_text('{"token":"synthetic"}')
            (folder/'metadata.json').write_text(json.dumps(dict(status='running',receiver_pid=123)))
            state=dict(paired_commands_version=2,sessions=[],devices=[dict(seen_s_ago=0,app_version='1.1',screen_visible=True)])
            with mock.patch.object(paired,'ROOT',root),mock.patch.object(paired,'api',return_value=state),mock.patch.object(paired,'ensure_receive_buffer'),mock.patch.object(paired,'process_alive',return_value=True),mock.patch.object(paired.subprocess,'Popen') as popen,mock.patch.object(sys,'argv',['run_paired.py','--pid','P04','--block','stand_still']),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(paired.main(),1);popen.assert_not_called()
    def simulate_run(self,status):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'data').mkdir();(root/'data/pairing.json').write_text('{"token":"synthetic"}')
            folder=root/'data/csi/P04/S01/test';raw=folder/'csi.csv'
            proc=mock.Mock(pid=222);proc.poll.return_value=None;proc.wait.return_value=0
            def spawn(*args,**kw):
                folder.mkdir(parents=True)
                (folder/'metadata.json').write_text(json.dumps(dict(helper_pid=222,csi_csv=str(raw))))
                raw.write_text('x'*200)
                return proc
            def sleep(_):
                with raw.open('a') as f:f.write('new synthetic row\n')
            def start_phone(*args,**kw):
                (folder/'phone_plan_test.json').write_text('{"phone_session_id":"test-phone-session"}')
                return mock.Mock(returncode=0)
            preflight=dict(paired_commands_version=2,sessions=[],devices=[dict(seen_s_ago=0,app_version='1.1',screen_visible=True)])
            completed=dict(sessions=[dict(id='test-phone-session',status=status)])
            with mock.patch.object(paired,'ROOT',root),mock.patch.object(paired,'api',side_effect=[preflight,completed]),mock.patch.object(paired,'ensure_receive_buffer'),mock.patch.object(paired,'inspect_csi_tail',return_value=dict(ready=True,rows_per_s=100,max_gap_ms=10,observed_s=21)),mock.patch.object(paired,'inspect_receiver_health',return_value=dict(ready=True)),mock.patch.object(paired,'assess_saved_run',return_value=dict(status='passed_window_checks',events=1,events_with_clean_2s_windows=1,strict_full_trials=1)),mock.patch.object(paired.subprocess,'Popen',side_effect=spawn),mock.patch.object(paired.subprocess,'run',side_effect=start_phone),mock.patch.object(paired.time,'sleep',side_effect=sleep),mock.patch.object(sys,'argv',['run_paired.py','--pid','P04','--block','stand_still']),contextlib.redirect_stdout(io.StringIO()):
                code=paired.main()
            proc.send_signal.assert_called_once_with(signal.SIGINT)
            self.assertTrue(raw.exists())
            return code
    def test_completion_stops_only_its_own_receiver(self):
        self.assertEqual(self.simulate_run('received_complete'),0)
    def test_partial_transfer_is_not_reported_as_complete(self):
        self.assertEqual(self.simulate_run('received_stopped'),1)

if __name__=='__main__':unittest.main()
