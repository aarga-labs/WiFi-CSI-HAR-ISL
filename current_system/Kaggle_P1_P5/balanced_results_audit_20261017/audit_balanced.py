"""Audit saved models/results. CPU inference only, no fitting or optimizer steps."""
from pathlib import Path
import sys,json,hashlib,zipfile,shutil
import numpy as np,pandas as pd,torch
from sklearn.metrics import f1_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).parent
RUN=BASE/'run/FYP_BALANCED_2H_20261017_015419';OUT=RUN/'results'
OLD=BASE.parent/'results_audit_20261017/run/FYP_FAST_2H_20261017_010129/results'
sys.path.insert(0,str(BASE.parent/'balanced_2h'))
import fyp_fast as f
assert hashlib.sha256((RUN/'source/fyp_fast.py').read_bytes()).digest()==hashlib.sha256((BASE.parent/'balanced_2h/fyp_fast.py').read_bytes()).digest()
torch.set_num_threads(2)
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as inp:
  for b in iter(lambda:inp.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
report=dict(archive_crc='passed',archive_sha256=digest('/home/adhikkesh/Downloads/results_1.zip'),
 local_training_executed=False,checkpoint_checks=[],metrics_recomputed=True)
new=pd.read_csv(OUT/'all_out_of_fold_predictions.csv');old=pd.read_csv(OLD/'all_out_of_fold_predictions.csv')
assert set(new.id)==set(old.id) and len(new)==len(old)==1534
report['identical_evaluation_event_ids']=True
report['unavailable_event_predictions']=int(new.scored_windows.eq(0).sum())
for pid in f.PIDS:
 assert (OUT/pid/'complete.json').exists()
 for path in sorted((OUT/pid).rglob('last.pt')):
  ck=torch.load(path,map_location='cpu',weights_only=False)
  tr=ck['train_participants'];va=ck['validation_participants']
  assert pid not in tr and pid not in va and not set(tr)&set(va)
  assert len(tr)==(3 if va else 4)
  assert ck['classes']==f.FINE
  assert ck['scheduler']['T_max']==100
  steps=ck['config']['steps_per_epoch'];history=pd.DataFrame(ck['history'])
  assert (history.steps==steps).all() and steps>=32
  report['checkpoint_checks'].append(dict(pid=pid,path=str(path.relative_to(OUT)),train=tr,val=va,
   epoch=int(ck['epoch']),steps=steps,updates=int(history.steps.sum()),cosine_horizon=100))
metrics=pd.read_csv(OUT/'fold_metrics.csv')
for r in metrics.itertuples():
 if r.split=='isolated':mask=new.pid.eq(r.pid)&new.part.ne('scripts')
 elif r.split=='stories_oracle_boundaries':mask=new.pid.eq(r.pid)&new.part.eq('scripts')
 elif r.split=='isolated_seated':mask=new.pid.eq(r.pid)&new.part.isin(['actions_seated','signs_seated'])
 elif r.split=='isolated_original_parts':mask=new.pid.eq(r.pid)&new.part.isin(['actions','signs_standing'])
 else:raise AssertionError(r.split)
 g=new[mask&new.type.eq(r.type)]
 names=f.ACTIONS if r.type=='activity' else f.SIGNS
 calc=f.macro(g,names)
 assert np.isclose(calc,r.macro_f1),str(r)
report['metrics_recomputed_rows']=len(metrics)
card=json.loads((OUT/'deployment_all5/model_card.json').read_text())
assert card['training_participants']==f.PIDS and card['evaluation_status']=='complete' and card['seeds']==[17,29]
assert card['dataset']==json.loads((OLD/'dataset_info.json').read_text())['dataset']
report['deployment_model_card']=card
models,loaded=f.load_deployment(OUT/'deployment_all5',device='cpu')
for name,ensemble in models.items():
 for net,scale in ensemble:
  with torch.inference_mode():ps,pf=net(torch.zeros(2,52,card['architectures'][name]['seconds']*f.FS))
  assert ps.shape==(2,3) and pf.shape==(2,26) and torch.isfinite(pf).all()
  assert np.isfinite(scale).all() and (scale>0).all()
report['deployment_cpu_load_and_forward']='passed, both seeds; no training'
for path in (OUT/'deployment_all5').rglob('last.pt'):
 ck=torch.load(path,map_location='cpu',weights_only=False)
 assert ck['train_participants']==f.PIDS and not ck['validation_participants'] and ck['config']['steps_per_epoch']==246
 assert ck['scheduler']['T_max']==100
 report.setdefault('deployment_updates',[]).append(dict(seed=path.parent.name,epochs=ck['epoch'],steps=246,updates=ck['epoch']*246))
summary=pd.read_csv(OUT/'summary.csv').merge(pd.read_csv(OLD/'summary.csv'),on=['split','type'],suffixes=('_new','_old'))
summary['change_percentage_points']=100*(summary.mean_f1_new-summary.mean_f1_old)
summary.to_csv(BASE/'run_comparison.csv',index=False)
report['summary_comparison']=summary.to_dict('records')
classrows=[]
for typ in ['activity','sign']:
 a=pd.read_csv(OUT/f'isolated_{typ}_per_class.csv');b=pd.read_csv(OLD/f'isolated_{typ}_per_class.csv')
 d=a.merge(b,on='label',suffixes=('_new','_old'));d['type']=typ
 d['change_percentage_points']=100*(d['f1-score_new']-d['f1-score_old'])
 classrows.append(d)
allclasses=pd.concat(classrows,ignore_index=True);allclasses.to_csv(BASE/'class_comparison.csv',index=False)
report['class_comparison']=allclasses[['label','type','f1-score_new','f1-score_old','change_percentage_points','support_new']].to_dict('records')
story=pd.read_csv(OUT/'story_metrics.csv');prior=pd.read_csv(OLD/'story_metrics.csv')
counts=story[['n_true','n_pred','detected','identified','intent_correct','false_on_routine','routine_seconds']].sum()
report['story_totals']=counts.to_dict();report['story_identity_recall']=float(counts.identified/counts.n_true)
report['story_intent_success']=float(counts.intent_correct/counts.n_true)
report['measured_routine_minutes']=float(counts.routine_seconds/60)
report['routine_false_command_rate']=float(counts.false_on_routine/counts.routine_seconds*3600)
report['previous_story_totals']=prior[['n_true','n_pred','detected','identified','intent_correct','false_on_routine','routine_seconds']].sum().to_dict()
# Matched counts, never interpret F1 as accuracy.
fig,axes=plt.subplots(2,1,figsize=(13,10),layout='constrained')
for ax,typ,title in zip(axes,['activity','sign'],['Actions','Signs']):
 d=allclasses[allclasses.type.eq(typ)].sort_values('f1-score_new',ascending=False);x=np.arange(len(d))
 ax.bar(x-.18,d['f1-score_old'],.36,label='Previous',color='#bec8d4');ax.bar(x+.18,d['f1-score_new'],.36,label='Balanced',color='#187b62')
 ax.set_xticks(x,d.label,rotation=40,ha='right');ax.set_ylim(0,1.08);ax.set_ylabel('Pooled class F1')
 ax.set_title(title+' — same held-out event IDs; pooled per-class results')
 for i,v in enumerate(d['f1-score_new']):ax.text(i+.18,v+.015,f'{v:.2f}',ha='center',fontsize=8)
 ax.legend(loc='upper right');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
fig.savefig(BASE/'classwise_comparison.png',dpi=170);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.6),layout='constrained')
x=np.arange(4);vals=[208,int(counts.detected),int(counts.identified),int(counts.intent_correct)]
ax.bar(x,vals,color=['#66788d','#5989b5','#cf9c36','#ae5d53']);ax.set_xticks(x,['True story signs','Detected','Correct sign','Correct full intent'])
ax.set_ylabel('Events');ax.set_ylim(0,235);ax.set_title('Continuous stories — detection is only the first step')
for i,v in enumerate(vals):ax.text(i,v+4,str(v),ha='center')
fig.savefig(BASE/'story_pipeline_counts.png',dpi=170);plt.close(fig)
# Create an inference-only package, preserving model-card-relative paths.
package=BASE/'Balanced_All5_Inference_Model.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=4) as z:
 for rel in ['model_card.json','fyp_fast.py','action_tree.joblib']:
  z.write(OUT/'deployment_all5'/rel,'Balanced_All5_Model/'+rel)
 for paths in card['models'].values():
  for rel in paths:z.write(OUT/'deployment_all5'/rel,'Balanced_All5_Model/'+rel)
 z.writestr('Balanced_All5_Model/README.md',
  '# P1–P5 saved inference model\n\nTwo normalized4 networks (seeds 17/29), 12 actions and 14 signs. Both were trained on all five participants. This package is for inference; the final refit has no separate independent score.\n\nRequirements: numpy, pandas, scipy, scikit-learn, joblib, torch. Place fyp_fast.py on your Python import path.\n\n```python\nfrom fyp_fast import predict_unlabelled_csv\nframes, commands = predict_unlabelled_csv("new_capture.csv", "Balanced_All5_Model", device="cpu")\n```\n\nUse device="cuda" on a compatible GPU. Inference uses offline centered windows and the same amplitude-only CSI CSV schema. The two-hour training notebook is not needed for inference. Tree fusion is isolated-event only; continuous inference uses CNNs.\n\nHeld-out benchmark mean macro F1: actions 0.5023, signs 0.3323. Seated and continuous end-to-end results remain weak. See the audit before making performance claims.\n')
with zipfile.ZipFile(package) as z:assert z.testzip() is None
report['inference_package']=dict(path=str(package),bytes=package.stat().st_size,sha256=digest(package))
(BASE/'audit.json').write_text(json.dumps(report,indent=2))
print('CHECKPOINTS',len(report['checkpoint_checks']),'METRIC_ROWS',report['metrics_recomputed_rows'])
print('STORY',json.dumps(report['story_totals']))
print('MODEL',report['inference_package'])
print(summary[['split','type','mean_f1_old','mean_f1_new','change_percentage_points']].to_string(index=False))
