"""Build a self-contained notebook. Does not execute notebook or training."""
from pathlib import Path
import ast
import hashlib
import json
import shutil

HERE=Path(__file__).resolve().parent
DEST=Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5')
DEST.mkdir(parents=True,exist_ok=True)
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):
    ast.parse(s)
    cells.append(dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=s.splitlines(True)))

md('''# P1–P5: shape + spectrum cross-fit ensemble

**One fixed workflow. Attach `fyp-dataset`, enable GPU T4 ×2, then Save Version → Save & Run All.** No previous results ZIP, model upload, Google Drive access, pip installation or mode selection is required. The verified data ZIP can also be attached as input and is extracted after integrity checks.

The current balanced baseline reached 50.2% isolated action macro F1 and 33.2% sign macro F1. Story identity, seated recognition and false commands remain weak. This experiment targets those issues; it does not promise an improved score.

The main workload is **20 × 9-minute optimization jobs on two GPUs**, approximately 90 minutes plus setup, validation inference and export. Two final all-five models follow, within the remaining time. Target wall time: roughly **100–115 minutes** on two T4 GPUs. There are no artificial waits or early-stopping shortcuts. Kaggle queuing/publishing is outside this runtime. A worker/global safety limit can interrupt abnormal runs; incomplete results are explicitly marked.

### What changes

1. A single four-second CNN learns temporal movement shape and four signal-frequency bands, retaining energy features for weak movements. Group normalization and attention pooling reduce dependence on a batch’s people and motion timing.
2. Action and sign identities have separate heads and losses. Class/person/source/posture/event balancing prevents long standing recordings from dominating shorter seated and story examples. Cue/key-press labels remain unverified by video.
3. A small supervised contrastive loss uses matching labels from different **training people** as positives. This is an experimental application of the [supervised contrastive learning objective](https://arxiv.org/abs/2004.11362); the paper does not establish performance on this dataset.
4. Moving-average model weights and validation checkpoints are used. For each outer test person, four models each train on three other people and validate on the remaining person. Average their probabilities. All four non-test people contribute across the ensemble; no member trains on the outer test person.
5. Sign detection and confidence rejection are selected from those four out-of-fold validation people, emphasizing correct-command precision. Test scores never choose weights or thresholds.

The preprocessing, quality masks, covered event IDs, class order and story overlap matching are retained for comparison. No test-person calibration is used. All-five deployment weights have no new independent score. This revision is informed by earlier test results; a fresh session/person is still needed for a final independent claim.
''')
code('''import time
RUN_STARTED=time.time()
DATA_ROOT=""  # auto-discover the attached fyp-dataset/phase1 folder
ZIP_PATH=""   # optional alternative: attached FYP_Phase1_P01_P05_verified.zip
EXPECTED_ZIP_SHA256="74259c5718d512ffa9cd3bdf63f150badcd6887e0cd2b35f780602e6e13a165c"
EVALUATION_DEADLINE=RUN_STARTED+103*60
TRAINING_DEADLINE=RUN_STARTED+112*60
FINISH_DEADLINE=RUN_STARTED+118*60
''')
md('''## GPU and workspace checks

The intended schedule requires two GPUs. This cell stops before training if two GPUs are unavailable. The notebook keeps the installed Kaggle PyTorch environment and uses [automatic mixed precision](https://docs.pytorch.org/docs/stable/notes/amp_examples.html). Training is blocked on a laptop.
''')
code('''from pathlib import Path
import os,sys,json,shutil,importlib,importlib.util
assert Path('/kaggle/working').is_dir(), 'Run this notebook on Kaggle. Laptop training is disabled.'
for module in ['torch','numpy','pandas','scipy','sklearn','joblib','matplotlib']:
    assert importlib.util.find_spec(module), f'Missing required Kaggle package: {module}'
import torch
assert torch.cuda.is_available() and torch.cuda.device_count()>=2, 'Enable GPU T4 x2 in Kaggle Settings, then start a fresh run.'
for i in range(2):
    free,total=torch.cuda.mem_get_info(i)
    print(f'GPU {i}: {torch.cuda.get_device_name(i)}; free {free/2**30:.1f} GiB',flush=True)
    assert free>7*2**30, 'GPU memory is occupied. Stop other work and start a fresh session.'
WORK=Path('/kaggle/working')/('FYP_IMPROVED_2H_'+time.strftime('%Y%m%d_%H%M%S',time.gmtime(RUN_STARTED)))
OUT=WORK/'results';OUT.mkdir(parents=True,exist_ok=True)
SOURCE_DIR=WORK/'source';SOURCE_DIR.mkdir(exist_ok=True)
from IPython.display import display,FileLink,Image
import pandas as pd
''')
names=['fyp_common.py','fyp_robust.py','run_jobs.py','prepare_data.py','assemble_evaluation.py','finish_results.py','baseline_reference.json']
sources={name:(HERE/name).read_text() for name in names}
code('SOURCES = '+repr(sources)+'''
for filename,source in SOURCES.items():(SOURCE_DIR/filename).write_text(source)
sys.path.insert(0,str(SOURCE_DIR))
import fyp_robust as R
import run_jobs
print('Experiment:',R.VERSION,'fixed model:',R.ARCH,flush=True)
''')
md('''## Verify and prepare the real P1–P5 recordings

The manifest checks every dataset file. This uses the same input resolver as the successful balanced run. Partial P2 labels are excluded; unavailable covered events count as misses. Only P4/P5 contain the new seated/cooking recordings. Empty-room recordings are quality references. No normalization is fitted on the test person.
''')
code('''prep=dict(pid='PREPARE',spec_path=str(WORK/'prepare.json'),progress=str(WORK/'prepare.progress.json'),
          deadline=min(RUN_STARTED+7*60,EVALUATION_DEADLINE),work=str(WORK),
          data=dict(root=DATA_ROOT,zip=ZIP_PATH,sha=EXPECTED_ZIP_SHA256))
prepared_status=run_jobs.run_jobs([prep],SOURCE_DIR/'prepare_data.py',max_parallel=1,stall_seconds=300)
assert prepared_status[0]['status']=='complete', 'Preparation failed. Read prepare.log; no training started.'
prepared=json.loads((WORK/'prepared.json').read_text())
assert prepared['participants']==R.PIDS and prepared['streams']==22
for name in ['recording_audit.csv','event_coverage.csv','dataset_info.json']:
    shutil.copy2(WORK/name,OUT/name)
for name in SOURCES:shutil.copy2(SOURCE_DIR/name,OUT/name)
versions={m:importlib.import_module(m).__version__ for m in ['torch','numpy','pandas','scipy','sklearn']}
R.C.atomic_json(versions,OUT/'environment.json')
display(pd.read_csv(OUT/'recording_audit.csv'))
coverage=pd.read_csv(OUT/'event_coverage.csv')
display(coverage.groupby(['pid','part','covered']).size().rename('events').reset_index())
cfg=dict(R.CFG)
R.C.atomic_json(cfg,OUT/'training_config.json')
common=dict(out=str(OUT),streams=str(WORK/'cache/prepared_streams.joblib'),fingerprint=prepared['fingerprint'],
            cfg=cfg,started=RUN_STARTED)
''')
md('''## Train twenty cross-fit members — approximately 90 minutes

One GPU runs one independent job. Each job has nine minutes for real optimization, validation and atomic checkpoint updates. The loop continues for its assigned budget, with a fixed cosine-restart learning-rate schedule; it keeps the highest validation-scoring moving-average checkpoint, even if later epochs overfit. Training time itself is not evidence of quality.

Every outer test person is excluded from four member fits. Each member uses a different validation person. The validation score gives extra weight to story sign identity, using a fixed formula recorded in the code. Sampling is with replacement; a dataset-sized draw count does not mean every unique window was visited.

Logs print epochs, loss, validation score and update counts. Status appears at least every minute. `best.pt`, recoverable `last.pt`, histories and participant metadata are saved during fitting. No DataLoader workers or DataParallel are used.
''')
code('''jobs=R.inner_plan(OUT,WORK,common['streams'],common['fingerprint'],cfg,EVALUATION_DEADLINE)
assert len(jobs)==20
display(pd.DataFrame([dict(test=j['test'],validation=j['val'],seed=j['seed'],
    train=','.join(p for p in R.PIDS if p not in [j['test'],j['val']])) for j in jobs]))
member_status=run_jobs.run_jobs(jobs,SOURCE_DIR/'fyp_robust.py',max_parallel=2,stall_seconds=300)
R.C.atomic_json(member_status,OUT/'member_status.json')
display(pd.DataFrame(member_status))
''')
md('''## Assemble five untouched outer test scores

Each threshold/confidence pair is chosen from four validation people whose predictions came from models that excluded them. The operating-point objective favors correctly identified signs and precision (F0.5). The four test predictions are averaged, then scored once. Confidence rejection leaves the measured routine-time denominator unchanged.

These ensemble members each fit three people, unlike the previous run’s four-person refit. The comparison measures the complete methods, not architecture alone. Incomplete four-member ensembles are not reported as completed folds.
''')
code('''assembly_spec=dict(common,pid='ASSEMBLE',spec_path=str(WORK/'assemble.json'),progress=str(WORK/'assemble.progress.json'),
                   deadline=min(TRAINING_DEADLINE,time.time()+5*60))
assembly_status=run_jobs.run_jobs([assembly_spec],SOURCE_DIR/'assemble_evaluation.py',max_parallel=1,stall_seconds=300)
R.C.atomic_json(assembly_status,OUT/'assembly_status.json')
completed=[pid for pid in R.PIDS if (OUT/pid/'complete.json').exists()]
print('Completed untouched participant tests:',completed,flush=True)
''')
md('''## Train and save the all-five deployment models

Two new seeds train on all five people. Their epoch target is the median best epoch from the twenty inner validation fits; they use the same learning-rate schedule and dataset-scaled batches. The remaining time caps these refits. A budget-shortened target is recorded explicitly in `model_card.json`, rather than hidden.

The deployment package contains both selected weights, class order, normalization scales, model code and an inference example. This all-five refit has no separate independent test score; the reported results above belong to the four-member outer ensembles. Centered windows make this an offline prototype.
''')
code('''final_status=[]
if len(completed)==5:
    import numpy as np
    infos=[json.loads((Path(j['folder'])/'fit_info.json').read_text()) for j in jobs]
    final_epochs=max(1,int(np.median([info['best_epoch'] for info in infos])))
    remaining=TRAINING_DEADLINE-time.time()-90
    if remaining>60:
        final_seconds=min(8*60,remaining)
        final_jobs=[]
        for seed in cfg['final_seeds']:
            name='FINAL_'+str(seed)
            final_jobs.append(dict(common,pid=name,job='final',seed=seed,epochs=final_epochs,final_seconds=final_seconds,
                folder=str(OUT/'deployment_all5/models'/('seed_'+str(seed))),
                deadline=TRAINING_DEADLINE,spec_path=str(WORK/(name+'.json')),progress=str(WORK/(name+'.progress.json'))))
        print('All-five target:',final_epochs,'epochs; cap per seed:',round(final_seconds/60,1),'minutes',flush=True)
        final_status=run_jobs.run_jobs(final_jobs,SOURCE_DIR/'fyp_robust.py',max_parallel=2,stall_seconds=300)
        if all(s['status']=='complete' for s in final_status):
            card=R.package_deployment(OUT,prepared['fingerprint'],cfg)
            display(card)
        else:print('A final seed failed; checkpoints remain, but no ready deployment package is declared.',flush=True)
    else:print('Insufficient final-training budget. Evaluation and checkpoint files are preserved.',flush=True)
else:print('Final refit withheld because all five four-member tests did not complete.',flush=True)
R.C.atomic_json(final_status,OUT/'final_status.json')
''')
md('''## Class graphs, baseline comparison and download

Outputs include action/sign class F1, confusion matrices, participant and posture results, continuous detection, correct identity, full intent and false commands. The automatic comparison to the previous balanced run is allowed only when the dataset fingerprint and all event IDs match. Negative changes are kept.

Download `FYP_Improved_All5_Model.zip` for the inference model, and `FYP_all_checkpoints_and_results.zip` for models, histories and results. Output files are also saved individually. Keep the original dataset and the completed Kaggle notebook version.
''')
code('''report_spec=dict(common,pid='REPORT',spec_path=str(WORK/'report.json'),progress=str(WORK/'report.progress.json'),
                 deadline=FINISH_DEADLINE)
report_status=run_jobs.run_jobs([report_spec],SOURCE_DIR/'finish_results.py',max_parallel=1,stall_seconds=300)
R.C.atomic_json(report_status,OUT/'report_status.json')
if (OUT/'run_completion.json').exists():
    status=json.loads((OUT/'run_completion.json').read_text());display(status)
else:status=dict(evaluation_complete=False,all_five_model_ready=False,error='Report did not complete; inspect report.log.')
for name in ['FYP_all_checkpoints_and_results.zip','FYP_Improved_All5_Model.zip']:
    path=WORK/name
    if path.exists():display(FileLink(str(path)))
for name in ['summary.csv','comparison_with_balanced.csv','story_metrics.csv']:
    if (OUT/name).exists():print(name);display(pd.read_csv(OUT/name))
for figure in sorted((OUT/'figures').glob('*.png')):display(Image(filename=str(figure)))
print('Total elapsed:',round((time.time()-RUN_STARTED)/60,1),'minutes. Saved under:',WORK,flush=True)
assert status['evaluation_complete'] and status['all_five_model_ready'], 'INCOMPLETE RUN: saved outputs remain available; read member/assembly/final/report status logs.'
''')
md('''## Validation limits

Before delivery, local checks cover notebook syntax/schema, embedded source consistency, model forward passes, finite conditional losses, cross-person contrastive masking, source/event balancing, split plans, saved-model inference and orchestration using synthetic fixtures. No model is fitted on the laptop. GPU speed, convergence and result quality require this Kaggle run.

Small participant coverage, protocol-driven recordings and unverified video alignment remain limitations. Seated/cooking classes have only two-person coverage. An extended training run cannot create missing diversity.
''')
for i,c in enumerate(cells):c['id']=hashlib.sha256(f'robust-{i}'.encode()).hexdigest()[:8]
nb=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata=dict(
    kernelspec=dict(display_name='Python 3',language='python',name='python3'),
    language_info=dict(name='python',version='3.11'),
    kaggle=dict(accelerator='gpu',isInternetEnabled=False,language='python',sourceType='notebook')))
p=HERE/'FYP_P1_P5_Kaggle_IMPROVED_2_Hours.ipynb'
p.write_text(json.dumps(nb,indent=1));shutil.copy2(p,DEST/p.name)
print(p,p.stat().st_size,'bytes; cells',len(cells))
