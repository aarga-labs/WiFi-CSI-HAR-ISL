"""Recover operator-confirmed laptop-cued trials; never alter raw recordings."""
import csv,json,hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_paths import saved_capture_path
from collections import Counter
root=Path(__file__).resolve().parents[1]
audit=json.loads((root/'quality_reviews/P04_standing_recovery_draft.json').read_text())
p=root/audit['source_run'];plan=json.loads((p/'plan.json').read_text())
out=root/'recovery/P04_activities_standing_20261113_124340';out.mkdir(parents=True,exist_ok=True)
keep={x['trial'] for x in audit['trials'] if x['keep']};events=[x for x in plan['phases'] if x['kind']=='perform'];accepted=[x for x in events if x['trial'] in keep];retry=[x for x in events if x['trial'] not in keep]
profile={'source':str((out/'recovery_manifest.json').relative_to(root)),'source_sha256':hashlib.sha256((p/'plan.json').read_bytes()).hexdigest(),'source_run_id':plan['session_id'],'label_basis':'operator explicitly confirms following laptop prompts throughout','events':[dict(label=e['label'],type=e['state'],duration_s=e['duration_s'],trial=e['trial'],**{k:e[k] for k in ['posture','script_id','run','context','intent','home_action']}) for e in retry]}
(root/'p04_standing_makeup.json').write_text(json.dumps(profile,indent=2)+'\n')
counts={}
for name,src,timefield,mult in [('csi',saved_capture_path(plan['paired_csi_csv']),'Timestamp_us',1000),('accelerometer',p/'phone/accelerometer.csv','controller_time_est_ns',1),('gyroscope',p/'phone/gyroscope.csv','controller_time_est_ns',1)]:
 count=0;index=0
 with src.open() as inp,(out/f'{name}_recovered.csv').open('w',newline='') as target:
  reader=csv.DictReader(inp);w=csv.DictWriter(target,fieldnames=['source_run','original_trial','label','posture','label_source']+reader.fieldnames);w.writeheader()
  for row in reader:
   t=int(row[timefield])*mult
   while index<len(accepted) and t>=accepted[index]['end_ns']:index+=1
   if index==len(accepted):break
   e=accepted[index]
   if t<e['start_ns']:continue
   w.writerow(dict(source_run=plan['session_id'],original_trial=e['trial'],label=e['label'],posture=e['posture'],label_source='laptop_scheduled_cue_operator_confirmed',**row));count+=1
 counts[name]=count
with (out/'trial_decisions.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['original_trial','label','decision','reason']);w.writeheader()
 for e in audit['trials']:w.writerow(dict(original_trial=e['trial'],label=e['label'],decision='retain' if e['keep'] else 'makeup',reason=','.join(e['failed_streams'])))
manifest={'source_phone_run':str(p),'source_csi':plan['paired_csi_csv'],'operator_confirmation':'Followed laptop website prompts throughout; confirmed in chat','label_source':'Original laptop plan, not delayed phone cue callbacks','quality_criteria':audit['criteria'],'retained_trials':sorted(keep),'makeup_trials':[e['trial'] for e in retry],'retained_count':len(keep),'makeup_count':len(retry),'retained_class_counts':dict(Counter(e['label'] for e in accepted)),'makeup_class_counts':dict(Counter(e['label'] for e in retry)),'rows_written':counts,'source_hashes':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p/'plan.json',p/'phone/accelerometer.csv',p/'phone/gyroscope.csv',saved_capture_path(plan['paired_csi_csv'])]},'limitations':['Scheduled movement labels confirmed by operator; execution is not independently verified.','Clock mapping retains original estimates; not an independent physical synchronization calibration.','Makeup data must be collected and audited before declaring all 115 trials restored.']}
(out/'recovery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
from controller import make_plan
mp=make_plan(dict(pid='P04',block='activities_standing_makeup'),0);seconds=(mp['end_ns']-mp['start_ns'])/1e9
manifest['makeup_duration_s']=seconds;(out/'recovery_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
profile['source_plan_sha256']=profile['source_sha256']
profile['source_sha256']=hashlib.sha256((out/'recovery_manifest.json').read_bytes()).hexdigest()
(root/'p04_standing_makeup.json').write_text(json.dumps(profile,indent=2)+'\n')
print('Retained',len(keep),'trials; makeup',len(retry),'trials; makeup seconds',seconds,'rows',counts)
print('Makeup class counts:',manifest['makeup_class_counts']);print('Output:',out)
