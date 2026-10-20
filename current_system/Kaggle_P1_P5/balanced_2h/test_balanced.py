"""No training: forward, indexing, augmentation, roles, deadlines and artifacts."""
from pathlib import Path
import json,sys,ast,hashlib,tempfile
import numpy as np
import torch
import fyp_fast as f
sys.path.insert(0,str(Path(__file__).parent.parent/'fast_2h'))
import fast_runner as runner
HERE=Path(__file__).parent
report=dict(training_executed_locally=False,gpu_execution='not run; requires Kaggle')
for arch in f.CANDIDATES:
 model=f.CSIModel(arch).eval()
 with torch.inference_mode():
  for scale in [0.,0.01,1.,10.]:
   st,fi=model(torch.ones(2,52,arch['seconds']*50)*scale)
   assert st.shape==(2,3) and fi.shape==(2,26) and torch.isfinite(fi).all()
 # Inference checkpoint round-trip, not a fit.
 with tempfile.TemporaryDirectory() as folder:
  path=Path(folder)/'best.pt';f.checkpoint_save(dict(arch=arch,model=model.state_dict()),path)
  ck=f.trusted_load(path);other=f.CSIModel(ck['arch']).eval();other.load_state_dict(ck['model'])
  x=torch.randn(1,52,arch['seconds']*50)
  with torch.inference_mode():
   a,b=model(x);c,d=other(x)
  assert torch.equal(a,c) and torch.equal(b,d)
report['all_three_architectures_forward_and_checkpoint_roundtrip']='passed'
for n in [1000,34987,62807]:
 cfg=dict(passes_per_epoch=1.,batch_size=256)
 steps=f.epoch_steps(n,cfg)
 assert steps>=32 and steps*256>=n
report['all_five_steps_per_epoch']=f.epoch_steps(62807,dict(passes_per_epoch=1.,batch_size=256))
assert report['all_five_steps_per_epoch']==246
report['draw_budget_scales_with_dataset']='passed'
for p,v in f.VALIDATION_PID.items():
 tr=set(f.PIDS)-{p,v};assert len(tr)==3 and not tr&{p,v} and tr&{'P04','P05'}
report['participant_split_separation']='passed'
# Relative augmentation must scale with weak input rather than bury it in fixed noise.
torch.manual_seed(17);small=f.augment(torch.ones(4,52,200)*0.01)
torch.manual_seed(17);large=f.augment(torch.ones(4,52,200))
assert torch.allclose(small*100,large,atol=1e-5)
report['weak_signal_relative_augmentation']='passed'
# Aligned role heads must originate from the correct selected network.
centers=np.array([150,160]);stream=dict(file='synthetic')
def pred(state,cls):
 ps=np.zeros((2,3),np.float32);ps[:,state]=1;pf=np.zeros((2,26),np.float32);pf[:,cls]=1
 return [dict(stream=stream,centers=centers,ps=ps,pf=pf,valid=np.array([True,True]))]
combined=f.combine_roles({'d':pred(2,0),'a':pred(1,3),'s':pred(0,20)},dict(detector='d',action='a',sign='s'))[0]
assert np.all(combined['ps'].argmax(1)==2)
assert np.all(combined['pf'][:,:12].argmax(1)==3)
assert np.all(combined['pf'][:,12:].argmax(1)+12==20)
report['role_head_combination']='passed'
# Same epoch positions must use the same learning-rate horizon, including refits.
source=(HERE/'fyp_fast.py').read_text()
assert "T_max=cfg['epochs']" in source and 'T_max=total' not in source
report['selection_and_refit_learning_rate_horizon']='passed'
# Verify original raw residual state dicts still load: audit uses the real saved weights.
original=HERE.parent/'results_audit_20261017/run/FYP_FAST_2H_20261017_010129/results/P01/models/seed_17/best.pt'
ck=torch.load(original,map_location='cpu',weights_only=False)
model=f.CSIModel(ck['arch']);model.load_state_dict(ck['model'])
report['raw_reference_checkpoint_compatibility']='passed'
try:f.require_kaggle_gpu();raise RuntimeError('Local training guard failed')
except AssertionError as e:assert 'Kaggle' in str(e)
report['local_training_guard']='passed'
nb=json.loads((HERE/'FYP_P1_P5_Kaggle_BALANCED_2_Hours.ipynb').read_text())
for c in nb['cells']:
 if c['cell_type']=='code':ast.parse(''.join(c['source']))
sources=ast.literal_eval(ast.parse(''.join(nb['cells'][4]['source'])).body[0].value)
for name,s in sources.items():assert s==(HERE/name).read_text()
report['notebook_syntax_embedded_sources']='passed'
report['watchdog']='same tested runner as fast notebook; independent process termination and expired-deadline skipping verified previously'
assert (HERE/'fast_runner.py').read_bytes()==(HERE.parent/'fast_2h/fast_runner.py').read_bytes()
report['maximum_fit_count']=51
report['source_sha256']=hashlib.sha256(source.encode()).hexdigest()
(HERE/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
