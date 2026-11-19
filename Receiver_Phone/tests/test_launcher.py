"""Launcher regressions: reuse a live collector without replacing it or the app."""
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import controller
import start_collector as launcher

class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.store=controller.Store(self.root/'data')
        self.server=controller.ThreadingHTTPServer(('127.0.0.1',0),controller.Handler)
        self.server.store=self.store;self.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.store.db.close();self.temp.cleanup()
    def test_recognizes_only_matching_authenticated_collector(self):
        state,link=launcher.controller_state(self.port,self.root/'data')
        self.assertEqual(state,'collector');self.assertIn(f':{self.port}/',link)
        (self.root/'data/pairing.json').write_text(json.dumps({'token':'wrong-key'}))
        self.assertEqual(launcher.controller_state(self.port,self.root/'data')[0],'other')
    def test_free_port(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        self.assertEqual(launcher.controller_state(port,self.root/'data'),('free',None))
    def test_second_launch_reuses_process_and_skips_reinstall(self):
        installed=subprocess.CompletedProcess([],0,stdout='package:/data/app/example/base.apk\n',stderr='')
        with mock.patch.object(launcher,'ROOT',self.root),mock.patch.object(sys,'argv',['launcher','--install','--port',str(self.port)]),mock.patch('shutil.which',return_value='adb'),mock.patch.object(launcher.subprocess,'check_output',return_value='List of devices attached\nTEST device\n'),mock.patch.object(launcher.subprocess,'run',return_value=installed) as run,mock.patch.object(launcher.subprocess,'Popen') as popen,mock.patch.object(launcher.webbrowser,'open') as browser:
            self.assertEqual(launcher.main(),0)
            popen.assert_not_called();browser.assert_called_once()
            self.assertFalse(any('install' in call.args[0] for call in run.call_args_list))
        self.assertEqual(launcher.controller_state(self.port,self.root/'data')[0],'collector')
    def test_unrelated_service_not_stopped_or_replaced(self):
        (self.root/'data/pairing.json').write_text(json.dumps({'token':'wrong-key'}))
        with mock.patch.object(launcher,'ROOT',self.root),mock.patch.object(sys,'argv',['launcher','--wifi','--port',str(self.port)]),mock.patch.object(launcher.subprocess,'Popen') as popen:
            self.assertEqual(launcher.main(),1);popen.assert_not_called()
        self.assertTrue(self.thread.is_alive())

if __name__=='__main__':unittest.main()
