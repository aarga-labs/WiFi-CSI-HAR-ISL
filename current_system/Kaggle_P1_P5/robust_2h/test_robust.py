"""Synthetic CPU forward/loss/inference and fake orchestration. Zero model fits."""
from pathlib import Path
import ast
import hashlib
import json
import tempfile
import time

import numpy as np
import pandas as pd
import torch
import fyp_robust as R

torch.set_num_threads(2)
checks=[]
def passed(name):checks.append(name);print('PASS:',name)

# 1. Fixed split plan covers every ordered test/validation pair once.
jobs=R.inner_plan('/out','/work','/streams','fixture',R.CFG,9999999999)
assert len(jobs)==20 and len({(j['test'],j['val']) for j in jobs})==20
for j in jobs:
    assert j['test']!=j['val']
    assert len(set(R.PIDS)-{j['test'],j['val']})==3
    assert j['cfg']['fit_seconds']==540
assert len({j['seed'] for j in jobs})==20
passed('20 fixed cross-fit splits; outer test excluded; distinct seeds; nine-minute training allocations')

# 2. Synthetic forward and loss-gradient sanity. No optimizer is constructed.
net=R.ShapeSpectrumCNN().eval();x=torch.randn(8,52,200)
with torch.no_grad():
    st,fi,z=net(x,with_embedding=True)
assert st.shape==(8,3) and fi.shape==(8,26) and z.shape==(8,64)
assert torch.isfinite(st).all() and torch.isfinite(fi).all()
assert torch.allclose(fi[:,:12].exp().sum(1),torch.ones(8),atol=1e-6)
assert torch.allclose(fi[:,12:].exp().sum(1),torch.ones(8),atol=1e-6)
state=torch.tensor([0,1,1,1,2,2,2,2]);fine=torch.tensor([-1,0,0,1,12,12,13,13]);people=torch.tensor([0,0,1,2,0,1,1,2])
sf=st.detach().requires_grad_();ff=fi.detach().requires_grad_();zz=z.detach().requires_grad_()
loss=R.objective(sf,ff,zz,state,fine,people);loss.backward()
assert torch.isfinite(loss) and all(torch.isfinite(t.grad).all() for t in [sf,ff,zz])
assert sf.grad.abs().sum()>0 and ff.grad.abs().sum()>0 and zz.grad.abs().sum()>0
assert R.cross_person_contrastive(z,torch.full((8,),-1),people).item()==0
assert R.cross_person_contrastive(z,torch.zeros(8,dtype=torch.long),torch.zeros(8,dtype=torch.long)).item()==0
passed('finite CPU forward, two conditional distributions and synthetic loss gradients; zero optimizer updates')

# 3. Relative augmentation and EMA mechanics.
y=R.augment(torch.ones(12,52,200)*1e-3)
assert torch.isfinite(y).all() and y.square().mean().sqrt()<.003
ema=R.ShapeSpectrumCNN().eval();before=next(ema.parameters()).detach().clone()
R.update_ema(ema,net,.5)
assert torch.allclose(next(ema.parameters()),before*.5+next(net.parameters())*.5,atol=1e-7)
passed('augmentation preserves weak-signal scale and moving-average weights update correctly')

# 4. Hierarchical weights keep person/source/event masses balanced even when
#    different events have different numbers of overlapping windows.
ss=[dict(pid='P01',part='signs_standing',event=np.array([0,0,1]),events=[dict(posture='standing'),dict(posture='standing')]),
    dict(pid='P01',part='scripts',event=np.array([0,0,0]),events=[dict(posture='seated')]),
    dict(pid='P02',part='signs_standing',event=np.array([0,0,0]),events=[dict(posture='standing')])]
rows=np.array([[0,0,2,12],[0,1,2,12],[0,2,2,12],[1,0,2,12],[1,1,2,12],[1,2,2,12],
               [2,0,2,12],[2,1,2,12],[2,2,2,12]])
w=R.balanced_weights(ss,rows).numpy()
assert np.isclose(w[:6].sum(),.5) and np.isclose(w[6:].sum(),.5)
assert np.isclose(w[:3].sum(),w[3:6].sum())
assert np.isclose(w[:2].sum(),w[2])
passed('equal person, source and event mass despite different window counts')

# 5. GPU-bank indexing equals ordinary dataset extraction (CPU only).
streams=[dict(pid='P01',part='actions',x=np.arange(52*650,dtype=np.float32).reshape(650,52)/10000,
              valid=np.ones(650,bool),severe=np.zeros(650,bool),state=np.ones(650,dtype=np.int64),
              fine=np.zeros(650,dtype=np.int64),event=np.zeros(650,dtype=np.int64),events=[dict(posture='standing')])]
bank,centers,targets,people,weights,scale=R.make_bank(streams,'cpu')
rows=R.C.examples(streams);dataset=R.C.WindowDataset(streams,rows,scale,4)
actual=bank[:,centers[0]+torch.arange(200)-100]
assert torch.allclose(actual,dataset[0][0])
passed('resident-bank windows match ordinary extraction without fitting or using a GPU')

# 6. Save/reload actual randomly initialized weights and run finite CPU inference.
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);(folder/'model_card.json').write_text(json.dumps(dict(classes=R.FINE,models=['model.pt'])))
    R.C.checkpoint_save(dict(classes=R.FINE,model=net.state_dict(),scale=np.ones(52,dtype=np.float32)),folder/'model.pt')
    loaded,card=R.load_deployment(folder,'cpu')
    with torch.no_grad():s,f=loaded[0][0](x)
    assert torch.allclose(s,st) and torch.allclose(f,fi)
passed('deployment checkpoint round-trip preserves model outputs and class order')

# 7. Rejection does not change valid-frame coverage or state predictions.
s=dict(pid='P01',part='scripts',file='synthetic.csv',state=np.ones(1000,dtype=np.int64),
       events=[dict(i0=300,i1=600,type='sign',label='HELLO',intent='I0',home_action='none')])
centers=np.arange(150,850,10);ps=np.zeros((len(centers),3),np.float32);ps[:,2]=1
pf=np.zeros((len(centers),26),np.float32);pf[:,0]=.5;pf[:,12:]=.5/14
p=dict(stream=s,centers=centers,ps=ps,pf=pf,valid=np.ones(len(centers),bool),sign_confidence=0)
a,_=R.C.event_metrics([p],.5);p['sign_confidence']=.35;b,_=R.C.event_metrics([p],.5)
assert a['n_pred']>0 and b['n_pred']==0 and a['routine_seconds']==b['routine_seconds']
passed('confidence rejection removes ambiguous commands without shrinking measured routine time')

# 8. Inner-worker orchestration uses only training+validation for selection.
#    Fake fit/predict functions return fixtures, not trained weights.
original_fit,original_predict,original_release=R.fit,R.C.predict,R.C.release
calls=[]
def fake_fit(tr,va,cfg,folder,fingerprint,deadline,epochs=None):
    calls.append(dict(train={s['pid'] for s in tr},val={s['pid'] for s in va}))
    Path(folder).mkdir(parents=True,exist_ok=True)
    return object(),np.ones(52),dict(best_epoch=2,best_updates=6,epochs_completed=3,updates=9,
        train_participants=sorted({s['pid'] for s in tr}),validation_participants=sorted({s['pid'] for s in va}))
def fake_predict(model,streams,*args,**kwargs):
    return [dict(stream=s,centers=np.array([150,160]),ps=np.ones((2,3),np.float32)/3,
                 pf=np.ones((2,26),np.float32)/26,valid=np.ones(2,bool)) for s in streams]
R.fit=fake_fit;R.C.predict=fake_predict;R.C.release=lambda model:None
try:
    with tempfile.TemporaryDirectory() as tmp:
        fixtures=[dict(pid=p,file=p+'.csv') for p in R.PIDS]
        for j in R.inner_plan(tmp,tmp,'unused','fixture',R.CFG,time.time()+10000):
            R.inner_worker(fixtures,j)
            assert j['test'] not in calls[-1]['train']|calls[-1]['val']
            assert len(calls[-1]['train'])==3 and calls[-1]['val']=={j['val']}
            assert (Path(j['folder'])/'complete.json').exists()
            restored=R.restore_predictions(Path(j['folder'])/'test_frames.npz',fixtures)
            assert restored[0]['stream']['pid']==j['test']
finally:R.fit=original_fit;R.C.predict=original_predict;R.C.release=original_release
passed('all 20 inner workers preserve split separation and save matching outer predictions using fake fits')

# 9. Missing members cannot produce a completed outer result.
with tempfile.TemporaryDirectory() as tmp:
    try:R.score_outer(dict(out=tmp,test='P01'),[])
    except AssertionError:pass
    else:raise AssertionError('Missing members were accepted')
passed('incomplete ensembles cannot silently receive completed test scores')

# 10. Notebook code and embedded sources are exactly the files just checked.
here=Path(__file__).parent;nb=json.loads((here/'FYP_P1_P5_Kaggle_IMPROVED_2_Hours.ipynb').read_text())
for cell in nb['cells']:
    if cell['cell_type']=='code':ast.parse(''.join(cell['source']))
source_cell=next(''.join(c['source']) for c in nb['cells'] if ''.join(c['source']).startswith('SOURCES = '))
embedded=ast.literal_eval(ast.parse(source_cell).body[0].value)
assert all(source==(here/name).read_text() for name,source in embedded.items())
try:
    import nbformat
    nbformat.validate(nb)
except ImportError:raise AssertionError('nbformat is required for delivery schema verification')
passed('notebook schema, code syntax and all embedded sources match checked files')

result=dict(checks=checks,count=len(checks),local_training=False,optimizer_updates=0,
            gpu_run_verified=False,notebook_sha256=hashlib.sha256((here/'FYP_P1_P5_Kaggle_IMPROVED_2_Hours.ipynb').read_bytes()).hexdigest())
(here/'verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
