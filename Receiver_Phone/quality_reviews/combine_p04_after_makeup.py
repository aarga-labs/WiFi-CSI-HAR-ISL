"""Build explicit recovery manifests; no interpolation, overwriting, or fabricated samples."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_paths import saved_capture_path
import csv,json,hashlib
import numpy as np
root=Path(__file__).resolve().parents[1]
base=root/'recovery/P04_activities_standing_20261113_124340';m=json.loads((base/'recovery_manifest.json').read_text());oldp=saved_capture_path(m['source_phone_run']);newp=root/'data/recordings/P04/S01/P04_S01_activities_standing_makeup_20261113_133827_e5a2cd'
old=json.loads((oldp/'plan.json').read_text());new=json.loads((newp/'plan.json').read_text());audit=json.loads((root/'quality_reviews'/f"{new['session_id']}_quality.json").read_text());strict_new={e['original_trial'] for e in audit['trial_decisions'] if e['pass']};old_keep=set(m['retained_trials']);oldlookup={e['trial']:e for e in old['phases'] if e['kind']=='perform'};newlookup={e['source_trial']:e for e in new['phases'] if e['kind']=='perform'}
def times(p,key):
 with p.open() as f:return np.array([int(r[key]) for r in csv.DictReader(f)],dtype=np.int64)
def streams(p,plan):return {'csi':times(saved_capture_path(plan['paired_csi_csv']),'Timestamp_us')*1000,'accelerometer':times(p/'phone/accelerometer.csv','controller_time_est_ns'),'gyroscope':times(p/'phone/gyroscope.csv','controller_time_est_ns')}
sets={'original':streams(oldp,old),'makeup':streams(newp,new)}
full=[];windows=[]
for trial in range(1,116):
 src='original' if trial in old_keep else 'makeup';p,plan=(oldp,old) if src=='original' else (newp,new);event=oldlookup[trial] if src=='original' else newlookup[trial]
 allpass=trial in old_keep or trial in strict_new
 entry={'recovery_note':'','original_trial':trial,'label':oldlookup[trial]['label'],'source_run':plan['session_id'],'phone_folder':str(p),'csi_file':plan['paired_csi_csv'],'event_start_ns':event['start_ns'],'event_end_ns':event['end_ns'],'full_trial_strict_pass':allpass}
 n=0
 for start in range(event['start_ns'],event['end_ns']-2_000_000_000+1,500_000_000):
  end=start+2_000_000_000;valid=True;stats={}
  for name,t in sets[src].items():
   a,b=np.searchsorted(t,[start,end]);near=t[max(0,a-1):min(len(t),b+1)];mx=float(np.diff(near).max()/1e6) if len(near)>1 else 1e9
   enough=(b-a)>= (40 if name=='csi' else 90)
   if not (t[0]<=start and t[-1]>=end and mx<=100 and enough):valid=False
   stats[name]={'rows':int(b-a),'max_gap_ms':mx}
  if valid:
   n+=1;windows.append(dict(original_trial=trial,label=entry['label'],source_run=plan['session_id'],start_controller_ns=start,end_controller_ns=end,phone_folder=str(p),csi_file=plan['paired_csi_csv'],csi_rows=stats['csi']['rows'],accelerometer_rows=stats['accelerometer']['rows'],gyroscope_rows=stats['gyroscope']['rows']))
 # If the makeup has no clean window, inspect the matching original trial.
 # Select windows from one attempt per original trial, never duplicate a trial.
 if not n and src=='makeup':
  event=oldlookup[trial]
  for start in range(event['start_ns'],event['end_ns']-2_000_000_000+1,500_000_000):
   end=start+2_000_000_000;valid=True;counts={}
   for name,t in sets['original'].items():
    a,b=np.searchsorted(t,[start,end]);near=t[max(0,a-1):min(len(t),b+1)]
    mx=float(np.diff(near).max()/1e6) if len(near)>1 else 1e9
    if not (t[0]<=start and t[-1]>=end and mx<=100 and b-a >= (40 if name=='csi' else 90)):valid=False
    counts[name]=int(b-a)
   if valid:
    n+=1;windows.append(dict(original_trial=trial,label=entry['label'],source_run=old['session_id'],start_controller_ns=start,end_controller_ns=end,phone_folder=str(oldp),csi_file=old['paired_csi_csv'],csi_rows=counts['csi'],accelerometer_rows=counts['accelerometer'],gyroscope_rows=counts['gyroscope']))
  if n:entry.update(source_run=old['session_id'],phone_folder=str(oldp),csi_file=old['paired_csi_csv'],event_start_ns=event['start_ns'],event_end_ns=event['end_ns'],recovery_note='Clean windows from original attempt used because makeup had no passing 2-second window')
 entry['clean_2s_windows']=n;full.append(entry)
out=root/'recovery/P04_standing_after_makeup';out.mkdir(exist_ok=True)
for name,values in [('trial_manifest.csv',full),('clean_2s_windows.csv',windows)]:
 with (out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(values[0]));w.writeheader();w.writerows(values)
summary={'original_retained_full_trials':len(old_keep),'makeup_recorded_trials':len(newlookup),'makeup_strict_full_trials':len(strict_new),'combined_strict_full_trials':len(old_keep)+len(strict_new),'trials_requiring_gap_filtered_windows':[e['original_trial'] for e in full if not e['full_trial_strict_pass']],'trials_with_at_least_one_clean_2s_window':sum(e['clean_2s_windows']>0 for e in full),'total_clean_2s_windows':len(windows),'trials_with_no_clean_2s_window':[e['original_trial'] for e in full if not e['clean_2s_windows']],'label_provenance':'scheduled laptop cues, operator confirmed following these cues throughout the original run','criteria':'Every exported 2-second window lies wholly within its event; both phone sensors >=45Hz and CSI >=20 rows/s; no gap >100ms overlapping window including boundary brackets. Missing samples not filled.','evaluation_note':'Overlapping windows are correlated. Group participant/session/trial before splitting; never split overlapping windows randomly across train/test.','limitations':'Full 115-trial timing-complete dataset is not claimed. 97 pass strict whole-trial coverage; other trial windows are separately filtered. Sensor latency and movement execution not independently verified.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));print('MANIFEST FOLDER',out)
