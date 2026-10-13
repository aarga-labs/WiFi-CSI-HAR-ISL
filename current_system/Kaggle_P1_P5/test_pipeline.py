"""Read-only data validation, synthetic forward passes and invariants. NO training."""
import json, tempfile, zipfile, sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import fyp_pipeline as p

HERE=Path(__file__).parent
ARCHIVE=Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/FYP_Phase1_P01_P05_verified.zip')
report={}
for arch in p.CANDIDATES:
    model=p.CSIModel(arch).eval()
    with torch.inference_mode():
        state,fine=model(torch.zeros(2,52,arch['seconds']*p.FS))
    assert state.shape==(2,3) and fine.shape==(2,26)
    assert torch.isfinite(state).all() and torch.isfinite(fine).all()
report['cpu_forward_shapes']='passed; no gradients or training'
try:
    p.require_kaggle_gpu()
    raise AssertionError('Local training guard failed')
except AssertionError as e:
    assert 'Kaggle' in str(e)
report['local_training_guard']='passed'
with tempfile.TemporaryDirectory(prefix='fyp_checks_') as folder:
    folder=Path(folder)
    for val in [1,2]: p.checkpoint_save({'value':val},folder/'last.pt')
    assert p.trusted_load(folder/'last.pt')['value']==2
    (folder/'last.pt').write_bytes(b'interrupted write')
    assert p.trusted_load(folder/'last.pt')['value']==1
    bad=folder/'unsafe.zip'
    with zipfile.ZipFile(bad,'w') as z:z.writestr('../escape.txt','bad')
    try:
        p.extract_verified(bad,folder/'unsafe')
        raise RuntimeError('Unsafe ZIP accepted')
    except AssertionError as e: assert 'Unsafe' in str(e)
    report['atomic_checkpoint_recovery_and_zip_path_guard']='passed'
    print('Extracting and verifying full real-data archive',flush=True)
    root=p.extract_verified(ARCHIVE,folder/'extracted',ARCHIVE.with_suffix('.zip.sha256').read_text().split()[0])
    print('Preprocessing all 22 participant recordings without training',flush=True)
    streams,fingerprint=p.prepare(root,HERE/'validation')
    report['dataset_fingerprint']=fingerprint
    report['participants']=sorted({s['pid'] for s in streams})
    assert report['participants']==p.PIDS and len(streams)==22
    report['streams']=len(streams)
    report['events']={pid:sum(e['type']!='idle' for s in streams if s['pid']==pid for e in s['events']) for pid in p.PIDS}
    report['windows']={}
    for pid in p.PIDS:
        subset=[s for s in streams if s['pid']==pid]; rows=p.examples(subset)
        weights=p.sampling_weights(subset,rows)
        assert torch.isfinite(weights).all() and (weights>0).all()
        report['windows'][pid]=len(rows)
        for arch in p.CANDIDATES:
            ds=p.WindowDataset(subset,rows,p.fit_scale(subset),arch['seconds'])
            x,ys,yf=ds[len(ds)//2]
            assert x.shape==(52,arch['seconds']*p.FS) and torch.isfinite(x).all()
    coverage=pd.read_csv(HERE/'validation/event_coverage.csv')
    missing=coverage[~coverage.covered]
    report['uncovered_labels_excluded']=missing.groupby(['pid','part']).size().to_dict().__str__()
    assert len(missing)>0 and set(missing.pid)=={'P02'}
    assert report['events']['P04']==425 and report['events']['P05']==425
    for test in p.PIDS:
        outer=[s for s in streams if s['pid']!=test]
        for val in p.PIDS:
            if val==test: continue
            tr=[s for s in outer if s['pid']!=val]
            assert not {test,val}&{s['pid'] for s in tr}
    report['all_20_nested_participant_splits']='disjoint'
    # Deterministic perfect synthetic story predictions, no model fit.
    s=next(s for s in streams if s['pid']=='P05' and s['part']=='scripts')
    centers=np.arange(150,len(s['x'])-150+1,10)
    ps=np.zeros((len(centers),3),np.float32); pf=np.zeros((len(centers),26),np.float32)
    for k,c in enumerate(centers):
        st=s['state'][c]; fi=s['fine'][c]
        ps[k,max(st,0)]=1
        if fi>=0:pf[k,fi]=1
    pred=[dict(stream=s,centers=centers,ps=ps,pf=pf,valid=np.ones(len(centers),bool))]
    table=p.segment_table(pred); em,commands=p.event_metrics(pred,0.5)
    assert (table.pred==table.label).all()
    assert em['detected']<=em['n_true'] and em['identified']<=em['detected']
    assert em['identity_recall']>0.8,em
    report['synthetic_perfect_story_identity_recall']=em['identity_recall']
    p.report_fold(table,pred,0.5,folder/'synthetic_report')
    report['metrics_export']='passed'
    # Handcrafted feature extraction and class mapping; no ExtraTrees fitting.
    x,ids,y=p.action_features([s for s in streams if s['pid']=='P05'],p.fit_scale([s for s in streams if s['pid']=='P01']))
    assert len(x)==len(ids)==len(y) and np.isfinite(x).all()
    report['action_feature_shape']=list(x.shape)
report['training_executed']=False
report['gpu_execution']='not run; requires Kaggle'
(HERE/'validation/verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
