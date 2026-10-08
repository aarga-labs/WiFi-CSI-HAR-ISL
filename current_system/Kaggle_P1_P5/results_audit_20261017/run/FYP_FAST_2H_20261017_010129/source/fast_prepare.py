from pathlib import Path
import sys,json,time,joblib
import fyp_fast as fyp
spec=json.loads(Path(sys.argv[2]).read_text());cfg=spec['data'];work=Path(spec['work']);work.mkdir(parents=True,exist_ok=True)
fyp.atomic_json(dict(time=time.time(),phase='validating and preprocessing real recordings'),spec['progress'])
if cfg.get('root'):
    root=Path(cfg['root'])
else:
    candidates=[p.parent for p in Path('/kaggle/input').rglob('manifest.json') if (p.parent/'session_log.csv').is_file()]
    if len(candidates)==1 and not cfg.get('zip'):
        root=candidates[0]
    else:
        archives=[Path(cfg['zip'])] if cfg.get('zip') else list(Path('/kaggle/input').rglob('FYP_Phase1_P01_P05_verified.zip'))
        assert len(archives)==1,'Set DATA_ROOT or ZIP_PATH to the attached private dataset.'
        root=fyp.extract_verified(archives[0],Path('/kaggle/temp/fyp_fast_data'),cfg['sha'])
streams,fingerprint=fyp.prepare(root,work)
cache=work/'cache';cache.mkdir(exist_ok=True)
joblib.dump(streams,cache/'prepared_streams.joblib',compress=0)
fyp.atomic_json(dict(fingerprint=fingerprint,streams=len(streams),participants=sorted({s['pid'] for s in streams}),dataset_root=str(root)),work/'prepared.json')
fyp.atomic_json(dict(time=time.time(),phase='preprocessing complete'),spec['progress'])
print('[DATA READY]',fingerprint,len(streams),'recordings',flush=True)
