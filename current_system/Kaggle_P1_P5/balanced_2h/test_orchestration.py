"""Run orchestration with fake fits only. No neural/classifier training."""
from pathlib import Path
import tempfile,json,numpy as np,pandas as pd
import fyp_fast as f
calls=[]
class FakeNet:
 def __init__(self,arch):self.arch=arch
 def cpu(self):return self

def fake_fit(tr,va,arch,cfg,folder,fingerprint,epochs=None,deadline=None):
 assert not {s['pid'] for s in tr}&{s['pid'] for s in va}
 calls.append(dict(train={s['pid'] for s in tr},val={s['pid'] for s in va},arch=arch['name'],seed=cfg['seed']))
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);(folder/'best.pt').write_text('fake fixture, not weights')
 return FakeNet(arch),np.ones(52),{'residual4':8,'residual6':12,'normalized4':16}[arch['name']],[]
def fake_predict(net,ss,scale,arch,*args,**kwargs):
 out=[]
 for s in ss:
  ps=np.zeros((2,3),np.float32);ps[:,2]=1;pf=np.zeros((2,26),np.float32);pf[:,0]=0.5;pf[:,12]=0.5
  out.append(dict(stream=s,centers=np.array([150,160]),ps=ps,pf=pf,valid=np.ones(2,bool),arch=arch['name']))
 return out

def fake_table(pred):
 rows=[]
 for p in pred:
  s=p['stream']
  for typ,label in [('activity','walk'),('sign','HELLO')]:
   rows.append(dict(id=s['pid']+typ,pid=s['pid'],type=typ,label=label,pred=label,part='actions',action_prob=np.eye(12)[0],scored_windows=1))
 return pd.DataFrame(rows)
def fake_tree(ss,scale,path):Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text('fixture');return None
f.require_kaggle_gpu=lambda:None
f.fit_fast=fake_fit;f.predict=fake_predict;f.release=lambda net:None
f.fit_scale=lambda s:np.ones(52)
f.role_scores=lambda p:{'action':{'residual4':.3,'residual6':.6,'normalized4':.4}[p[0]['arch']],
 'sign':{'residual4':.4,'residual6':.2,'normalized4':.6}[p[0]['arch']],
 'detector':{'residual4':.5,'residual6':.7,'normalized4':.4}[p[0]['arch']]}
f.segment_table=fake_table;f.choose_tau=lambda ps:(.6,[])
f.train_tree=fake_tree;f.tree_predictions=lambda tree,ss,scale:{s['pid']+'activity':np.eye(12)[0] for s in ss}
f.save_predictions=lambda *args:None
f.report_fold=lambda *args:None
ss=[dict(pid=p,file=p,part='actions') for p in f.PIDS]
with tempfile.TemporaryDirectory() as tmp:
 out=Path(tmp)
 for pid in f.PIDS:
  begin=len(calls);f.fast_fold(ss,pid,dict(f.DEFAULTS),out,'fixture',9999999999)
  assert all(pid not in c['train'] and pid not in c['val'] for c in calls[begin:])
  choice=json.loads((out/pid/'selection.json').read_text())
  assert choice['roles']==dict(detector='residual6',action='residual6',sign='normalized4')
  assert (out/pid/'complete.json').exists()
 f.fast_final(ss,dict(f.DEFAULTS),out,'fixture',9999999999)
 card=json.loads((out/'deployment_all5/model_card.json').read_text())
 assert card['training_participants']==f.PIDS and card['evaluation_status']=='complete'
 assert card['roles']==dict(detector='residual6',action='residual6',sign='normalized4')
 assert len(card['models'])==2 and all(len(paths)==2 for paths in card['models'].values())
 assert all((out/'deployment_all5'/p).exists() for paths in card['models'].values() for p in paths)
 assert len(calls)==39
print('PASS: five test folds + all-five refit, two seeds, role choices, class alignment and output model paths. 39 fake fits; zero real fits.')
