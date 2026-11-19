"""Create a portable, checksummed two-modality dataset from the reviewed windows."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capture_paths import saved_capture_path
import csv,json,hashlib,shutil,zipfile
from collections import Counter
root = Path(__file__).resolve().parents[1]
recovery = (root/'recovery').resolve()
review = recovery/'P04_standing_after_makeup'
dest = recovery.parent/'P04_Standing_Activities_Rebuilt'
dest.mkdir()
summary=json.loads((review/'summary.json').read_text())
with (review/'trial_manifest.csv').open() as f:trials=list(csv.DictReader(f))
with (review/'clean_2s_windows.csv').open() as f:windows=list(csv.DictReader(f))
source_paths={}
for row in trials:
 sid=row['source_run']
 if sid not in source_paths:source_paths[sid]=(saved_capture_path(row['phone_folder']),saved_capture_path(row['csi_file']))
rebase={};hashes={}
for sid,(phone,csi) in source_paths.items():
 tag='makeup' if 'makeup' in sid else 'original';target=dest/'source_runs'/tag;target.mkdir(parents=True,exist_ok=True);(target/'phone').mkdir(exist_ok=True);rebase[sid]=str(target.relative_to(dest))
 files=[(csi,target/'csi.csv'),(phone/'plan.json',target/'plan.json')]
 for name in ['accelerometer.csv','gyroscope.csv','clock_sync.csv','metadata.json','labels.csv','quality.json']:
  files.append((phone/'phone'/name,target/'phone'/name))
 for src,out in files:
  shutil.copy2(src,out);a=hashlib.sha256(src.read_bytes()).hexdigest();b=hashlib.sha256(out.read_bytes()).hexdigest();assert a==b;hashes[str(out.relative_to(dest))]=b
for name,rows in [('trial_manifest.csv',trials),('windows.csv',windows)]:
 for row in rows:
  tag=rebase[row['source_run']];row['phone_folder']=tag;row['csi_file']=tag+'/csi.csv'
 with (dest/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
counts=Counter(row['label'] for row in trials);wcounts=Counter(row['label'] for row in windows)
assert len(trials)==115 and len(windows)==901 and len({r['original_trial'] for r in windows})==115
with (dest/'class_counts.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['label','original_trials_represented','overlapping_2s_windows'])
 for label,n in counts.items():w.writerow([label,n,wcounts[label]])
summary.update(dataset='P04 standing activities, reviewed two-second paired windows',participant='P04',session='S01',window_duration_s=2,stride_s=.5,raw_source_file_sha256=hashes,portable_paths=True)
(dest/'dataset_manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Portable dataset created:',dest,'| trials:',len(trials),'| windows:',len(windows),'| raw copies independently SHA256 verified.')
