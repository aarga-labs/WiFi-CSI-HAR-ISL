import csv,json,hashlib,zipfile,re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_paths import saved_capture_path
from collections import Counter
import numpy as np
root=Path(__file__).resolve().parents[1]
p=max((root/'data/recordings/P04/S01').glob('*activities_standing*'),key=lambda f:f.stat().st_mtime)
plan=json.loads((p/'plan.json').read_text());events=[x for x in plan['phases'] if x['kind']=='perform']
def read(path):
 with path.open() as f:return list(csv.DictReader(f))
labels=read(p/'phone/labels.csv');actual=[x for x in labels if x['kind']=='perform'];complete=[x for x in actual if x['phase_complete']=='true'];seen={int(x['phase_index']) for x in complete}
report={'phone_folder':str(p),'phone_status':json.loads((p/'phone/metadata.json').read_text())['status'],'expected_events':len(events),'complete_events':len(complete),'incomplete_or_missing':[{'trial':x['trial'],'label':x['label']} for x in events if x['index'] not in seen],'planned_class_counts':dict(Counter(x['label'] for x in events)),'complete_class_counts':dict(Counter(x['label'] for x in complete))}
errors=[(int(x['start_controller_est_ns'])-int(x['scheduled_start_controller_ns']))/1e9 for x in actual]
report['cue_timing']={'max_start_delay_s':max(errors),'first_trial_delayed_over_200ms':next((int(x['trial']) for x,e in zip(actual,errors) if e>.2),None),'delayed_trials':[{ 'trial':int(x['trial']),'label':x['label'],'start_delay_s':e} for x,e in zip(actual,errors) if e>.2]}
sensors={}
for name in ['accelerometer','gyroscope']:
 r=read(p/f'phone/{name}.csv');ts=np.array([int(x['sensor_elapsed_ns']) for x in r],dtype=np.int64);host=np.array([int(x['controller_time_est_ns']) for x in r],dtype=np.int64);xyz=np.array([[float(x[k]) for k in ['x','y','z']] for x in r]);d=np.diff(ts)/1e9
 gaps=[]
 for ix in np.flatnonzero(d>.1):
  involved=[int(x['trial']) for x in labels if x['kind']=='perform' and int(x['actual_start_phone_ns'])<ts[ix+1] and int(x['actual_end_phone_ns'])>ts[ix]]
  gaps.append({'from_s':float((ts[ix]-ts[0])/1e9),'duration_s':float(d[ix]),'overlapping_actual_trials':involved,'from_host_ns':int(host[ix]),'to_host_ns':int(host[ix+1])})
 sensors[name]={'rows':len(ts),'span_s':float((ts[-1]-ts[0])/1e9),'overall_mean_hz':float((len(ts)-1)/((ts[-1]-ts[0])/1e9)),'median_hz':float(1/np.median(d)),'max_gap_s':float(max(d)),'gaps_over_100ms':gaps,'non_increasing':int(np.sum(d<=0)),'nonfinite':int(np.sum(~np.isfinite(xyz))),'axis_max_abs':np.max(np.abs(xyz),axis=0).tolist()}
report['sensors']=sensors
# Stream CSI to avoid a large row-dictionary allocation.
csi=saved_capture_path(plan['paired_csi_csv']);ts=[];invalid=0;zero=0;channels=Counter();badwidth=0
with csi.open() as f:
 reader=csv.reader(f);header=next(reader)
 for row in reader:
  if len(row)!=len(header):badwidth+=1;continue
  try:
   t=int(row[1]);v=np.asarray(row[3:],dtype=float)
   ts.append(t);invalid+=int(np.sum(~np.isfinite(v)));zero+=int(np.all(v==0));channels[row[2]]+=1
  except ValueError:badwidth+=1
ct=np.asarray(ts,dtype=np.int64);d=np.diff(ct)/1e6
lo=int(plan['phases'][0]['start_ns'])//1000;hi=min(int(plan['end_ns'])//1000,int(labels[-1]['end_controller_est_ns'])//1000)
sel=ct[(ct>=lo)&(ct<hi)];seconds=int((hi-lo)//1e6);hist=np.histogram((sel-lo)/1e6,bins=np.arange(seconds+1))[0]
report['csi']={'file':str(csi),'rows':len(ct),'span_s':float((ct[-1]-ct[0])/1e6),'overall_rows_per_s':float((len(ct)-1)/((ct[-1]-ct[0])/1e6)),'max_gap_ms':float(d.max()*1000),'gaps_over_100ms':int(np.sum(d>.1)),'per_second_min':int(hist.min()),'per_second_max':int(hist.max()),'empty_seconds':int(np.sum(hist==0)),'seconds_below_50':int(np.sum(hist<50)),'bad_width_or_parse_rows':badwidth,'nonfinite_values':invalid,'all_zero_rows':zero,'channels':dict(channels)}
# Compare complete CSI coverage for the early phone events that still match the shared plan.
early=[]
for x,e in zip(actual,errors):
 if e>.2:break
 t0=int(x['scheduled_start_controller_ns'])//1000;t1=int(x['scheduled_end_controller_ns'])//1000
 early.append({'trial':int(x['trial']),'label':x['label'],'csi_rows':int(np.sum((ct>=t0)&(ct<t1)))})
report['early_timing_matched_event_count']=len(early);report['early_event_csi_min_rows']=min(x['csi_rows'] for x in early)
receipt=json.loads((p/'transfer_receipt.json').read_text());archive=p/'phone_original.zip'
report['transfer']={'sha256_matches':hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256']}
with zipfile.ZipFile(archive) as z:
 manifest=json.loads(z.read('manifest.json'));report['transfer']['all_member_hashes_match']=all(hashlib.sha256(z.read(n)).hexdigest()==e['sha256']==hashlib.sha256((p/'phone'/n).read_bytes()).hexdigest() for n,e in manifest.items())
report['assessment']='Incomplete run. Long phone sensor gaps and cue schedule divergence after trial 84 mean later data must not be naively paired using planned labels. Early trials require gap overlap filtering and movement review before salvage. Preserve raw data.'
q=root/'quality_reviews'/f"{plan['session_id']}_quality.json";q.write_text(json.dumps(report,indent=2)+'\n')
summary=dict(report);summary['cue_timing']={k:v for k,v in report['cue_timing'].items() if k!='delayed_trials'}
for name,v in summary['sensors'].items():v['gaps_over_100ms']=[{k:x[k] for k in ['from_s','duration_s','overlapping_actual_trials']} for x in v['gaps_over_100ms']]
print(json.dumps(summary,indent=2));print('REPORT',q)
