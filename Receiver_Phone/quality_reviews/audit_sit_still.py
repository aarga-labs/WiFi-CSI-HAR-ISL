import csv,json,hashlib,zipfile,re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_paths import saved_capture_path
import numpy as np
root=Path(__file__).resolve().parents[1]
folder=max((root/'data/recordings/P04/S01').glob('*sit_still*'),key=lambda p:p.stat().st_mtime)
plan=json.loads((folder/'plan.json').read_text());phase=next(p for p in plan['phases'] if p['kind']=='baseline')
a,b=phase['start_ns'],phase['end_ns'];duration=(b-a)/1e9
csi=saved_capture_path(plan['paired_csi_csv'])
def rows(path):
 with path.open() as f:return list(csv.DictReader(f))
def summary(ts,scale):
 d=np.diff(ts)/scale
 return dict(rows=len(ts),span_s=float((ts[-1]-ts[0])/scale),mean_rows_per_s=float((len(ts)-1)/((ts[-1]-ts[0])/scale)),non_increasing=int(np.sum(d<=0)),median_gap_ms=float(np.median(d)*1000),p95_gap_ms=float(np.percentile(d,95)*1000),max_gap_ms=float(np.max(d)*1000),gaps_over_100ms=int(np.sum(d>.1)),gaps_over_50ms=int(np.sum(d>.05)))
r=rows(csi);times=np.array([int(x['Timestamp_us']) for x in r],dtype=np.int64);v=np.array([[float(x[k]) for k in r[0] if k.startswith('SC')] for x in r]);sel=(times>=a//1000)&(times<b//1000)
t=times[sel];z=v[sel];counts=np.histogram((t-a//1000)/1e6,bins=np.arange(121))[0]
amp=np.hypot(z[:,0::2],z[:,1::2]);rms=np.sqrt(np.mean(amp**2,axis=1))
report=dict(phone_folder=str(folder),csi_file=str(csi),scored_interval_s=duration,csi_full=summary(times,1e6),csi_scored=summary(t,1e6))
report['csi_scored'].update(rows_per_scored_s=len(t)/duration,per_second_min=int(counts.min()),per_second_median=float(np.median(counts)),per_second_max=int(counts.max()),seconds_below_50=int(np.sum(counts<50)),seconds_below_20=int(np.sum(counts<20)),empty_seconds=int(np.sum(counts==0)),channels=sorted(set(x['Channel'] for x in r)),nonfinite=int(np.sum(~np.isfinite(z))),all_zero_rows=int(np.sum(np.all(z==0,axis=1))),repeated_adjacent_vectors=int(np.sum(np.all(np.diff(z,axis=0)==0,axis=1))),amplitude_rms_p05_p50_p95=[float(x) for x in np.percentile(rms,[5,50,95])],first_row_delay_ms=float((t[0]-a//1000)/1000),last_row_margin_ms=float((b//1000-t[-1])/1000))
labels=rows(folder/'phone/labels.csv');event=next(x for x in labels if x['kind']=='baseline');sensor_a=int(event['actual_start_phone_ns']);sensor_b=int(event['actual_end_phone_ns'])
report['actual_phone_event_s']=(sensor_b-sensor_a)/1e9
report['sensors']={};gyro_values=None;acc_values=None
for name in ['accelerometer','gyroscope']:
 r=rows(folder/f'phone/{name}.csv');ts=np.array([int(x['sensor_elapsed_ns']) for x in r],dtype=np.int64);vals=np.array([[float(x[k]) for k in ['x','y','z']] for x in r]);m=(ts>=sensor_a)&(ts<sensor_b);x=vals[m];tt=ts[m];norm=np.linalg.norm(x,axis=1)
 out=dict(full=summary(ts,1e9),scored=summary(tt,1e9));out['scored'].update(nonfinite=int(np.sum(~np.isfinite(x))),norm_p05_p50_p95_p99_max=[float(q) for q in np.percentile(norm,[5,50,95,99,100])],axis_mean=[float(q) for q in x.mean(axis=0)],axis_std=[float(q) for q in x.std(axis=0)],first_sample_delay_ms=float((tt[0]-sensor_a)/1e6),last_sample_margin_ms=float((sensor_b-tt[-1])/1e6))
 binidx=((tt-sensor_a)//1_000_000_000).astype(int)
 if name=='gyroscope':
  out['scored']['seconds_with_gyro_rms_over_0_1_rad_s']=[int(i) for i in range(120) if np.any(binidx==i) and np.sqrt(np.mean(norm[binidx==i]**2))>.1]
  gyro_values=x
 else:
  out['scored']['acc_norm_std']=float(norm.std());acc_values=x
  out['scored']['gravity_vector_first10_last10_angle_deg']=float(np.degrees(np.arccos(np.clip(np.dot(x[binidx<10].mean(0),x[binidx>=110].mean(0))/(np.linalg.norm(x[binidx<10].mean(0))*np.linalg.norm(x[binidx>=110].mean(0))),-1,1))))
 report['sensors'][name]=out
sync=rows(folder/'phone/clock_sync.csv');off=np.array([int(x['offset_ns']) for x in sync],dtype=np.int64);rtt=np.array([int(x['rtt_ns']) for x in sync])/1e6
report['clock']=dict(samples=len(sync),controllers=len(set(x['controller_id'] for x in sync)),rtt_ms_min_median_max=[float(x) for x in [rtt.min(),np.median(rtt),rtt.max()]],offset_span_ms=float((off.max()-off.min())/1e6),cue_start_est_error_ms=(int(event['start_controller_est_ns'])-a)/1e6,cue_end_est_error_ms=(int(event['end_controller_est_ns'])-b)/1e6)
receipt=json.loads((folder/'transfer_receipt.json').read_text());archive=folder/'phone_original.zip'
report['transfer']=dict(phone_status=receipt['phone_status'],archive_sha256_matches=hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256'])
with zipfile.ZipFile(archive) as arc:
 manifest=json.loads(arc.read('manifest.json'));report['transfer']['all_archived_and_extracted_member_hashes_match']=all(hashlib.sha256(arc.read(n)).hexdigest()==e['sha256']==hashlib.sha256((folder/'phone'/n).read_bytes()).hexdigest() for n,e in manifest.items())
logs=list((root/'data/run_logs').glob('P04_sit_still_*.log'));log=max(logs,key=lambda p:p.stat().st_mtime);text=log.read_text(errors='replace')
report['receiver_log']=dict(file=str(log),bytes=log.stat().st_size,overflow_mentions=len(re.findall('overflow',text,re.I)),underflow_mentions=len(re.findall('underflow',text,re.I)),overflow_character_runs=len(re.findall(r'(?m)^O+$',text)),warnings=list(dict.fromkeys(line for line in text.splitlines() if 'WARNING' in line))[:12])
path=root/'quality_reviews'/f"{plan['session_id']}_quality.json";path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));print('REPORT:',path)
