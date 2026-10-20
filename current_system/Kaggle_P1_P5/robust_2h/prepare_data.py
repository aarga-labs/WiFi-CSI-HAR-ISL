from pathlib import Path
import sys,json,time,joblib,hashlib
import fyp_common as fyp

KNOWN_ROOT=Path('/kaggle/input/datasets/adhikkeshsk/fyp-dataset/phase1')

def resolve_input(cfg,input_base=Path('/kaggle/input')):
    input_base=Path(input_base)
    if cfg.get('root'):
        root=Path(cfg['root'])
        if not (root/'session_log.csv').is_file() and (root/'phase1/session_log.csv').is_file():root=root/'phase1'
        if not (root/'manifest.json').is_file() or not (root/'session_log.csv').is_file():
            raise FileNotFoundError(f'DATA_ROOT={root} is not a mounted verified CSI dataset. Attach fyp-dataset using Add Input, then copy its phase1 folder path.')
        return root,None
    if cfg.get('zip'):
        archive=Path(cfg['zip'])
        if not archive.is_file():raise FileNotFoundError(f'ZIP_PATH does not exist: {archive}. Attach the verified data ZIP as Input first.')
        return None,archive
    candidates=sorted({p.parent.resolve() for p in input_base.rglob('manifest.json') if (p.parent/'session_log.csv').is_file()})
    if len(candidates)==1:return candidates[0],None
    if KNOWN_ROOT in candidates:return KNOWN_ROOT,None
    if len(candidates)>1:
        hashes={hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest() for p in candidates}
        if len(hashes)==1:return candidates[0],None
        raise ValueError('Multiple different CSI datasets are attached. Set DATA_ROOT to one phase1 folder: '+', '.join(map(str,candidates)))
    archives=list(input_base.rglob('FYP_Phase1_P01_P05_verified.zip'))
    if len(archives)==1:return None,archives[0]
    if len(archives)>1:raise ValueError('Multiple data ZIPs are attached. Set ZIP_PATH: '+', '.join(map(str,archives)))
    mounts=sorted(str(p) for p in input_base.iterdir()) if input_base.exists() else []
    raise FileNotFoundError('No P1-P5 CSI dataset was found in this notebook. Add Input -> Your Datasets -> fyp-dataset -> Add. '
        'The previous successful path was '+str(KNOWN_ROOT)+'. Current input mounts: '+str(mounts))


def main(spec_path):
    spec=json.loads(Path(spec_path).read_text());cfg=spec['data'];work=Path(spec['work']);work.mkdir(parents=True,exist_ok=True)
    fyp.atomic_json(dict(time=time.time(),phase='finding attached dataset'),spec['progress'])
    root,archive=resolve_input(cfg)
    if archive is not None:root=fyp.extract_verified(archive,Path('/kaggle/temp/fyp_robust_data'),cfg['sha'])
    print('[DATASET]',root,flush=True)
    fyp.atomic_json(dict(time=time.time(),phase='validating and preprocessing real recordings'),spec['progress'])
    streams,fingerprint=fyp.prepare(root,work)
    cache=work/'cache';cache.mkdir(exist_ok=True)
    joblib.dump(streams,cache/'prepared_streams.joblib',compress=0)
    fyp.atomic_json(dict(fingerprint=fingerprint,streams=len(streams),participants=sorted({s['pid'] for s in streams}),dataset_root=str(root)),work/'prepared.json')
    fyp.atomic_json(dict(time=time.time(),phase='preprocessing complete'),spec['progress'])
    print('[DATA READY]',fingerprint,len(streams),'recordings',flush=True)


if __name__=='__main__':main(sys.argv[2])
