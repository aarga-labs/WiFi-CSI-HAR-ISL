"""Package real kept recordings; does not alter recordings or train any model."""
from pathlib import Path
import hashlib
import json
import zipfile
import pandas as pd

SOURCE = Path('/home/adhikkesh/usrp-projects/data/phase1')
DEST = Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5')
AUDITS = Path('/home/adhikkesh/.codex/.chatgpt-projects/g-p-6abe30abf790819195241e261aa9757d/output/recording_checks')

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    log = pd.read_csv(SOURCE/'session_log.csv')
    kept = log[log.status.eq('kept')].sort_values(['date','time'])
    people = kept[kept.pid.isin(['P01','P02','P03','P04','P05'])].drop_duplicates(['pid','part'], keep='last')
    # Keep each day's empty reference, rather than silently assigning one to every participant.
    empty = kept[kept.pid.eq('DAY') & kept.part.eq('empty')]
    selected = pd.concat([people, empty]).sort_values(['date','time']).copy()
    files = {}
    for r in selected.itertuples():
        raw = SOURCE/Path(r.csi_file).name
        if not raw.exists(): raw = Path(str(raw)+'.gz')
        assert raw.exists(), raw
        files[raw.name] = raw
        if isinstance(r.label_file, str) and r.label_file != '-':
            f = SOURCE/'labels'/Path(r.label_file).name
            assert f.exists(), f
            files['labels/'+f.name] = f
        rx = SOURCE/'logs'/(Path(r.csi_file).stem+'.rx.log')
        if rx.exists(): files['logs/'+rx.name] = rx
    generated = {'session_log.csv': selected.to_csv(index=False).encode()}
    manifest = {'schema_version':1, 'participants':sorted(people.pid.unique().tolist()),
                'selection':'latest kept participant part; all kept empty references',
                'files':{}, 'notes':[
                    'P02 actions is truncated; unrecorded label intervals must be excluded.',
                    'P04/P05 alone have isolated seated and cooking additions.',
                    'P04 baseline is Oct 15; main blocks Oct 16.',
                    'Videos are not included. Labels are cue/operator annotations.',
                    'Discarded takes, fabricated DATA_COMBINED and duplicate gzip copies are excluded.']}
    for p in ['P04','P05']:
        for ext in ['json','md']:
            f = AUDITS/f'{p}_capture_audit.{ext}'
            if f.exists(): files['audits/'+f.name] = f
    for name, path in files.items():
        manifest['files'][name] = {'bytes':path.stat().st_size, 'sha256':sha256(path)}
    for name,b in generated.items():
        manifest['files'][name] = {'bytes':len(b), 'sha256':hashlib.sha256(b).hexdigest()}
    archive = DEST/'FYP_Phase1_P01_P05_verified.zip'
    tmp = archive.with_suffix('.zip.part')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=4, allowZip64=True) as z:
        for name,path in files.items():
            print('Packing', name, flush=True)
            z.write(path, 'phase1/'+name)
        for name,b in generated.items(): z.writestr('phase1/'+name,b)
        z.writestr('phase1/manifest.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(tmp) as z:
        assert z.testzip() is None, 'ZIP CRC verification failed'
        for name,info in manifest['files'].items():
            h=hashlib.sha256()
            with z.open('phase1/'+name) as f:
                for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
            assert h.hexdigest()==info['sha256'], name
    tmp.replace(archive)
    digest=sha256(archive)
    (DEST/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n')
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2))
    report={'archive':str(archive),'sha256':digest,'bytes':archive.stat().st_size,
            'csi_files':len(selected),'participant_takes':len(people),
            'counts':people.groupby('pid').size().to_dict(),'crc_and_all_file_hashes_verified':True}
    (DEST/'upload_verification.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
