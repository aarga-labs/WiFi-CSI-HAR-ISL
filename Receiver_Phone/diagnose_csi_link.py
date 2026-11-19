"""Unlabeled P00 receiver-only link check; no phone or training data changed."""
import os,sys,time,json,subprocess,signal,csv,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
if len(sys.argv)>1 and sys.argv[1]=='--child':
 folder=Path(sys.argv[2]);from PyQt5 import Qt
 from capture_paths import RECEIVER_EXAMPLES
 receiver=RECEIVER_EXAMPLES
 sys.path.insert(0,str(receiver));from wifi_rx import wifi_rx
 app=Qt.QApplication([]);tb=wifi_rx();tb.ieee802_11_extract_csi_0.set_channel(1);tb.start();tb.flowgraph_started.set();tb.show()
 gains=[int(x) for x in os.environ.get('FYP_DIAGNOSTIC_GAINS','12,18,24,12').split(',')];index=[0]
 def mark(gain):
  with (folder/'segments.jsonl').open('a') as f:f.write(json.dumps({'gain_db':gain,'time_us':time.time_ns()//1000})+'\n')
 def step():
  i=index[0]
  if i==len(gains):
   mark(None);tb.stop();tb.wait();app.quit();return
  gain=gains[i];tb.uhd_usrp_source_0.set_gain(gain,0);mark(gain);index[0]+=1
  Qt.QTimer.singleShot(12000,step)
 Qt.QTimer.singleShot(0,step);sys.exit(app.exec_())
from start_csi_rx import clean_environment
folder=ROOT/'diagnostics'/('csi_link_'+time.strftime('%Y%m%d_%H%M%S'));folder.mkdir(parents=True,exist_ok=False)
env=clean_environment();env.update(RX_ADDR='192.168.10.7',RX_GAIN='12',CSI_CHANNEL='1',CSI_TA='02:00:00:00:00:01',CSI_RA='02:00:00:00:00:02',CSI_OUT=str(folder/'csi.csv'))
def udp():
 lines=Path('/proc/net/snmp').read_text().splitlines();idx=next(i for i,line in enumerate(lines) if line.startswith('Udp:'))
 return dict(zip(lines[idx].split()[1:],map(int,lines[idx+1].split()[1:])))
def snapshot(pid):
 try:
  x=Path(f'/proc/{pid}/stat').read_text().split();ticks=int(x[13])+int(x[14])
 except OSError:ticks=0
 return {'time_us':time.time_ns()//1000,'cpu_ticks':ticks,'udp':udp()}
with (folder/'receiver.log').open('w') as log:
 child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child',str(folder)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 print('Receiver-only check started:',folder,flush=True);snapshots=[];deadline=time.monotonic()+80
 while child.poll() is None and time.monotonic()<deadline:
  snapshots.append(snapshot(child.pid));time.sleep(.25)
 if child.poll() is None:
  child.send_signal(signal.SIGINT)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:child.terminate()
 code=child.wait(timeout=10)
(folder/'host_samples.json').write_text(json.dumps(snapshots,indent=2)+'\n');(folder/'exit.json').write_text(json.dumps({'code':code,'kind':'P00 diagnostic only, not participant data'})+'\n')
print('Receiver diagnostic capture ended, code:',code,flush=True)
import numpy as np
with (folder/'segments.jsonl').open() as f:segments=[json.loads(line) for line in f]
with (folder/'csi.csv').open() as f:ts=np.array([int(row['Timestamp_us']) for row in csv.DictReader(f)],dtype=np.int64)
results=[]
for first,last in zip(segments,segments[1:]):
 lo=first['time_us']+2_000_000;hi=last['time_us'];v=ts[(ts>=lo)&(ts<hi)];delta=np.diff(v)/1000
 near=[s for s in snapshots if lo<=s['time_us']<=hi]
 loss=near[-1]['udp']['RcvbufErrors']-near[0]['udp']['RcvbufErrors'] if len(near)>1 else None
 cpu=100*(near[-1]['cpu_ticks']-near[0]['cpu_ticks'])/os.sysconf('SC_CLK_TCK')/((near[-1]['time_us']-near[0]['time_us'])/1e6) if len(near)>1 else None
 results.append({'gain_db':first['gain_db'],'measured_seconds':(hi-lo)/1e6,'rows':len(v),'rows_per_s':len(v)/((hi-lo)/1e6),'max_gap_ms':float(delta.max()) if len(delta) else None,'gaps_over_100ms':int(np.sum(delta>100)),'udp_receive_buffer_errors_delta':loss,'process_cpu_percent':cpu})
text=(folder/'receiver.log').read_text(errors='replace');results_out={'folder':str(folder),'diagnostic_not_research':True,'method':os.environ.get('FYP_DIAGNOSTIC_GAINS','12,18,24,12')+' dB; 2 second settling excluded in each 12 second phase; fixed channel 1 and existing TX settings','segments':results,'overflow_mentions':len(re.findall('overflow',text,re.I))}
(folder/'summary.json').write_text(json.dumps(results_out,indent=2)+'\n');print(json.dumps(results_out,indent=2),flush=True)
