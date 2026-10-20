"""CPU-only structural/logic checks. Never fits a model or runs an optimizer."""
from pathlib import Path
import tempfile,time,json,ast,hashlib,sys
import numpy as np
import pandas as pd
import torch
import fyp_fast as f
import fast_runner as runner

HERE=Path(__file__).parent
report={'training_executed':False,'gpu_execution':'not tested; run on Kaggle'}
for test,val in f.VALIDATION_PID.items():
 tr=set(f.PIDS)-{test,val}
 assert test!=val and len(tr)==3 and not tr&{test,val}
 assert tr&{'P04','P05'},'Every training split must include a cooking participant'
report['five_fixed_participant_splits']='passed'
for arch in f.CANDIDATES:
 model=f.CSIModel(arch).eval()
 with torch.inference_mode():state,fine=model(torch.zeros(2,52,arch['seconds']*50))
 assert state.shape==(2,3) and fine.shape==(2,26) and torch.isfinite(fine).all()
report['cpu_forward_shapes']='passed; no fitting/backpropagation'
# Compare GPU-bank indexing math on CPU against the original Dataset slice.
rng=np.random.default_rng(17)
streams=[dict(x=rng.normal(size=(700,52)).astype(np.float32)),dict(x=rng.normal(size=(900,52)).astype(np.float32))]
scale=np.ones(52,np.float32)
rows=np.array([[0,200,1,0],[1,400,2,15]])
flat=torch.tensor(np.concatenate([s['x'] for s in streams]).T.copy())
offsets=np.array([0,700]);centers=torch.tensor(rows[:,1]+offsets[rows[:,0]])
for width in [200,300]:
 idx=centers[:,None]+torch.arange(width)[None,:]-width//2
 batch=flat[:,idx].permute(1,0,2).contiguous()
 ds=f.WindowDataset(streams,rows,scale,width/50)
 for i in range(2):assert torch.equal(batch[i],ds[i][0])
report['gpu_bank_indexing_equivalence_on_cpu']='passed'
try:f.require_kaggle_gpu();raise RuntimeError('Guard failed')
except AssertionError as e:assert 'Kaggle' in str(e)
report['local_training_guard']='passed'
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp)
 fake=tmp/'fake_worker.py'
 fake.write_text('''import sys,json,time\nfrom pathlib import Path\ns=json.loads(Path(sys.argv[2]).read_text())\nprint('fake started',flush=True)\nif s['pid']=='OK':\n Path(s['progress']).write_text(json.dumps(dict(time=time.time(),phase='done')))\nelse:time.sleep(30)\n''')
 common=dict(deadline=time.time()+20,max_job_seconds=10)
 specs=[dict(common,pid=pid,spec_path=str(tmp/(pid+'.json')),progress=str(tmp/(pid+'.progress.json'))) for pid in ['OK','HANG']]
 start=time.time();rs=runner.run_jobs(specs,fake,max_parallel=2,stall_seconds=0.5,poll_seconds=0.05)
 assert next(r for r in rs if r['pid']=='OK')['status']=='complete'
 assert next(r for r in rs if r['pid']=='HANG')['status']=='stalled_no_progress'
 assert time.time()-start<10
 report['external_watchdog_stops_fake_hang']='passed'
 expired=dict(common,pid='EXPIRED',spec_path=str(tmp/'expired.json'),progress=str(tmp/'expired.progress'),deadline=time.time()-1)
 rs=runner.run_jobs([expired],fake,max_parallel=1,poll_seconds=0.05)
 assert rs[0]['status']=='not_started_time_budget'
 report['deadline_prevents_new_work']='passed'
 # Real previously audited labels; data parsing and filtering are unchanged.
 old=HERE.parent/'validation/event_coverage.csv'
 d=pd.read_csv(old);assert set(d.pid)==set(f.PIDS)
 assert (d[(d.pid=='P05')&d.covered].type.isin(['activity','sign'])).sum()==425
 report['real_data_coverage_reference']='22 recordings already validated; preprocessing functions unchanged'
 # Metric and plot exports from synthetic held-out predictions, never model outputs.
 out=tmp/'results'
 for pid in f.PIDS:
  fold=out/pid;fold.mkdir(parents=True)
  row=dict(pid=pid,part='actions',label='walk',pred='walk',cnn_pred='walk',hier_pred='walk',type='activity',posture='standing',scored_windows=1,p_sign=0.)
  pd.DataFrame([row]).to_csv(fold/'segments.csv',index=False)
  pd.DataFrame([dict(split='isolated',type='activity',n=1,supported_classes=1,macro_f1=1.,accuracy=1.,cnn_macro_f1=1.,unavailable=0)]).to_csv(fold/'metrics.csv',index=False)
  (fold/'story_events.json').write_text(json.dumps(dict(n_true=1,detection_f1=1.,identity_f1=1.,intent_e2e=1.,false_commands_per_routine_hour=0.,detection_recall=1.,identity_recall=1.)))
  (fold/'complete.json').write_text('{}')
 import matplotlib;matplotlib.use('Agg')
 f.summarize(out)
 assert (out/'summary.csv').exists() and len(list((out/'figures').glob('*.png')))>=5
 f.archive_outputs(out)
 report['synthetic_metric_plot_zip_export']='passed'
nb=json.loads((HERE/'FYP_P1_P5_Kaggle_FAST_2_Hours.ipynb').read_text())
for c in nb['cells']:
 if c['cell_type']=='code':ast.parse(''.join(c['source']))
embedded=ast.literal_eval(ast.parse(''.join(nb['cells'][4]['source'])).body[0].value)
for filename,source in embedded.items():assert source==(HERE/filename).read_text()
report['notebook_ast_and_embedded_sources']='passed'
report['evaluation_fits']=5*(2+1);report['deployment_fits']=1
report['budgets_minutes']=dict(evaluation=85,all_training=105,finish_target=115)
report['source_sha256']=hashlib.sha256((HERE/'fyp_fast.py').read_bytes()).hexdigest()
(HERE/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
