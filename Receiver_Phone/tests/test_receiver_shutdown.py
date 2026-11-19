"""Exercise a pipe-full shutdown without radio hardware."""
import tempfile,subprocess,sys,signal,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from start_csi_rx import drain_shutdown_output

class ShutdownCheck(unittest.TestCase):
    def test_shutdown_output_cannot_block_receiver_exit(self):
        code='''import signal,time,sys
def finish(*args):
 sys.stdout.write('x'*1048576+'\\nFINAL_RECEIVER_OUTPUT\\n');sys.stdout.flush();sys.exit(0)
signal.signal(signal.SIGINT,finish)
print('READY',flush=True)
while True:time.sleep(.1)
'''
        with tempfile.TemporaryDirectory() as t:
            p=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,text=True)
            try:
                self.assertEqual(p.stdout.readline().strip(),'READY')
                log=Path(t)/'log.txt';drain=drain_shutdown_output(p,log)
                p.send_signal(signal.SIGINT);self.assertEqual(p.wait(timeout=5),0);drain.join(timeout=2)
                self.assertTrue(log.read_text().endswith('FINAL_RECEIVER_OUTPUT\n'))
            finally:
                if p.poll() is None:p.kill();p.wait()
                p.stdout.close()
