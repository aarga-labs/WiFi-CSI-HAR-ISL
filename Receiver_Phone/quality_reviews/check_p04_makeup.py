import csv,json,hashlib,zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_paths import saved_capture_path
import numpy as np
root=Path(__file__).resolve().parents[1];p=root/'data/recordings/P04/S01/P04_S01_activities_standing_makeup_20261113_133827_e5a2cd';plan=json.loads((p/'plan.json').read_text())
def rows(path):
 with path.open() as f:return list(csv.DictReader(f))
def stamps(path,key,scale=1):
 with path.open() as f:return np.array([int(r[key])*scale for r in csv.DictReader(f)],dtype=np.int64)
ct=stamps(saved_capture_path(plan['paired_csi_csv']),'Timestamp_us',1000);streams={'csi':ct,'accelerometer':stamps(p/'phone/accelerometer.csv','controller_time_est_ns'),'gyroscope':stamps(p/'phone/gyroscope.csv','controller_time_est_ns')}
labels=rows(p/'phone/labels.csv');actual=[e for e in labels if e['kind']=='perform'];events=[e for e in plan['phases'] if e['kind']=='perform'];decisions=[]
for e in events:
 reasons=[];stats={}
 for name,t in streams.items():
  a,b=np.searchsorted(t,[e['start_ns'],e['end_ns']]);v=t[a:b];near=t[max(0,a-1):min(len(t),b+1)];g=np.diff(near);mx=float(max(g)/1e6) if len(g) else 1e9
  valid=len(v)>0 and t[0]<=e['start_ns'] and t[-1]>=e['end_ns'] and mx<=100 and len(v)/e['duration_s']>=(20 if name=='csi' else 45)
  stats[name]={'rows':len(v),'max_gap_ms_including_edges':mx,'pass':bool(valid)}
  if not valid:reasons.append(name)
 decisions.append({'makeup_trial':e['trial'],'original_trial':e['source_trial'],'label':e['label'],'pass':not reasons,'failed_streams':reasons,'stats':stats})
d=np.diff(ct)/1e9;whole=(ct[-1]-ct[0])/1e9
receipt=json.loads((p/'transfer_receipt.json').read_text());archive=p/'phone_original.zip'
report={'source_run':str(p),'phone_version':json.loads((p/'phone/metadata.json').read_text())['app_version'],'phone_status':receipt['phone_status'],'planned_events':len(events),'completed_events':sum(e['phase_complete']=='true' for e in actual),'cue_delay_ms_min_max':[float(min((int(e['start_controller_est_ns'])-int(e['scheduled_start_controller_ns']))/1e6 for e in actual)),float(max((int(e['start_controller_est_ns'])-int(e['scheduled_start_controller_ns']))/1e6 for e in actual))],'phone_quality':json.loads((p/'phone/quality.json').read_text()),'csi':{'rows':len(ct),'span_s':float(whole),'mean_rows_per_s':float((len(ct)-1)/whole),'max_gap_ms':float(max(d)*1000),'gaps_above_100ms':int(sum(d>.1))},'strict_passing_events':sum(e['pass'] for e in decisions),'strict_rejected_events':[e for e in decisions if not e['pass']],'trial_decisions':decisions,'archive_hash_matches':hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256']}
with zipfile.ZipFile(archive) as z:
 manifest=json.loads(z.read('manifest.json'));report['member_hashes_match']=all(hashlib.sha256(z.read(n)).hexdigest()==e['sha256']==hashlib.sha256((p/'phone'/n).read_bytes()).hexdigest() for n,e in manifest.items())
q=root/'quality_reviews'/f"{plan['session_id']}_quality.json";q.write_text(json.dumps(report,indent=2)+'\n');small={k:v for k,v in report.items() if k not in ['trial_decisions','strict_rejected_events']};small['rejected']=[(e['makeup_trial'],e['original_trial'],e['label'],e['failed_streams'],e['stats']['csi']['max_gap_ms_including_edges']) for e in report['strict_rejected_events']];print(json.dumps(small,indent=2));print('Report',q)
