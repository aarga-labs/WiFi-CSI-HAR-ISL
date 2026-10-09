from pathlib import Path
import json,ast,hashlib,shutil
HERE=Path(__file__).parent
OLD=HERE.parent/'fast_2h/FYP_P1_P5_Kaggle_FAST_2_Hours.ipynb'
nb=json.loads(OLD.read_text());cells=nb['cells']
def setsrc(i,s):cells[i]['source']=s.splitlines(True)
setsrc(0,'''# P1–P5: corrected training within a two-hour compute budget

This notebook replaces the six-minute fast run. It starts fresh on Kaggle and uses the same verified private P1–P5 dataset. **Attach that dataset, select T4 ×2, then Save Version → Save & Run All once.** No old checkpoint or results upload is required.

The previous run completed, but its action macro F1 was 0.355 and sign macro F1 0.181. Its final model received only 384 optimizer updates. The saved histories also show a substantial gap between training-person and unseen-person recognition. More epochs alone are not assumed to solve that gap.

Corrections in this version:
- An epoch scales with the number of available training windows instead of a fixed 32 batches. Sampling is balanced and with replacement; a draw budget equal to dataset size does not mean every unique window was seen once.
- Up to 100 epochs, validation every four epochs, early stopping, and a consistent learning-rate horizon across selection and refit.
- Separate validation-selected networks for activity/sign detection, action identity and sign identity. Compare the existing residual CNN at 4 and 6 seconds and a window-normalized 4-second alternative.
- The normalized candidate keeps local waveform shape and energy, uses group normalization, and is chosen only if validation supports it. Augmentation noise is relative to each window's signal rather than a fixed amplitude that can swamp weak movements.
- Two training seeds per selected network; two GPUs run independent participant tests. No DataLoader workers or DataParallel.
- Training diagnostic probes and real update/draw counts appear in saved histories.

Maximum workload is 51 fits, usually fewer because roles can share networks. The time cap is maintained: evaluation ends by minute 75; all training ends by minute 105; export ends by minute 115. A supervisor stops stalled workers. Incomplete evaluation or a missing final model is reported explicitly. Queue/publishing time is outside notebook control.

This protocol is a practical model revision informed by the previous benchmark. For a final independent claim, validate on a fresh recording session or new person after fixing the design. No improved accuracy or actual runtime is claimed before this Kaggle run.''')
setsrc(1,'''import time
RUN_STARTED=time.time()
EVALUATION_DEADLINE=RUN_STARTED+75*60
TRAINING_DEADLINE=RUN_STARTED+105*60
FINISH_DEADLINE=RUN_STARTED+115*60
DATA_ROOT=""  # optional explicit private dataset folder
ZIP_PATH=""   # optional explicit verified ZIP path
EXPECTED_ZIP_SHA256="74259c5718d512ffa9cd3bdf63f150badcd6887e0cd2b35f780602e6e13a165c"
STALL_SECONDS=300
MAX_FOLD_MINUTES=24
MAX_FINAL_MINUTES=29
''')
setup=''.join(cells[3]['source']).replace('FYP_FAST_2H_','FYP_BALANCED_2H_')
setsrc(3,setup)
files=['fyp_fast.py','fast_runner.py','fast_prepare.py','fast_report.py']
setsrc(4,'SOURCES = '+repr({n:(HERE/n).read_text() for n in files})+'''
for filename,source in SOURCES.items():(SOURCE_DIR/filename).write_text(source)
sys.path.insert(0,str(SOURCE_DIR))
import fast_runner
print("Sources written:",SOURCE_DIR)
''')
setsrc(7,'''## Participant-separated evaluation and role selection

The outer test participant is excluded from all fitting and model selection. The same fixed validation mapping as the prior fast benchmark is retained:

| Test | Validation | Initial training |
|---|---|---|
| P1 | P4 | P2, P3, P5 |
| P2 | P5 | P1, P3, P4 |
| P3 | P1 | P2, P4, P5 |
| P4 | P2 | P1, P3, P5 |
| P5 | P3 | P1, P2, P4 |

Fit three candidates using training data only: residual 4 s, residual 6 s, and normalized residual 4 s. Use the validation person to choose a candidate separately for the detector, action identity and sign identity. The new normalized candidate is an experiment; it is not assumed superior.

Refit each unique selected network on the four training participants with two seeds. Average its seed predictions and combine the role heads. Select the story threshold and isolated-action ExtraTrees fusion weight using validation only. Finally score the unseen participant.

At each validation check, histories also record a fixed training-window diagnostic probe. This is not a held-out event accuracy. A large train/validation gap calls for stronger generalization or better data, not merely extra epochs. No test-participant score controls stopping or model choice.''')
train=''.join(cells[8]['source'])
a=train.index('cfg=dict(');b=train.index('(OUT/"training_config.json")',a)
train=train[:a]+'''cfg=dict(epochs=100,patience=8,min_epochs=24,passes_per_epoch=1.0,batch_size=256,
         lr=0.001,weight_decay=0.01,seed=17,seeds=[17,29],val_every=4,tree_estimators=300)
'''+train[b:]
setsrc(8,train)
setsrc(9,'''## Train the all-five deployment ensemble

Use validation-selection votes to pick the final network for each role. Train those networks using **all P1+P2+P3+P4+P5**, with two seeds and matching dataset-scaled update budgets. The cosine schedule keeps its original 100-epoch horizon; it is not compressed into a short refit.

All weights, preprocessing scales, class orders, architectures, per-role mapping and inference code are saved. This all-five refit has no new independent score. If no complete selection/evaluation fold is available, the notebook refuses an unvalidated deployment fallback. A deadline-stopped final fit is not labeled a ready model.''')
setsrc(11,'''## Results, training histories and downloadable model

The notebook exports real held-out class-wise F1, confusion matrices, participant/posture results, story detection, correct sign identity, full intent, false commands per routine hour, and quality coverage. Oracle-boundary identity and automatic event metrics remain separate.

Only P4/P5 provide isolated seated/cooking recordings. Those class/posture results have two-person coverage. More optimization cannot establish generalization that this dataset does not support.

The bundle includes the selected networks for each role, both seed weights, an all-five model card, and offline inference code. `best.pt` is an inference checkpoint; `last.pt` additionally stores optimizer/scheduler/scaler/random-state metadata. This notebook is a fresh run and does not resume the previous archive.

Save/download the completed version's Output ZIP. Running for close to two hours is not itself evidence of a better model; assess the held-out results and the train/validation gap.''')
setsrc(13,'''## Implementation checks

Checks before delivery cover notebook schema/syntax, embedded sources, fixed participant separation, CPU forward passes for all candidate architectures, GPU-bank indexing equivalence, dataset-scaled draw budgets, role-head combination, mixed-model inference, augmentation scale, saved checkpoint metadata, and watchdog/deadline behavior using fake processes. No model is fitted locally.

GPU speed, convergence and accuracy require this Kaggle run. The two-hour cap limits computation; hardware failures or insufficient time can still leave incomplete results, which are reported explicitly.

[PyTorch AMP](https://docs.pytorch.org/docs/stable/notes/amp_examples.html) · [Kaggle notebooks](https://www.kaggle.com/docs/notebooks)''')
for i,c in enumerate(cells):
 c['id']=hashlib.sha256(('balanced'+str(i)).encode()).hexdigest()[:8]
 if c['cell_type']=='code':ast.parse(''.join(c['source']))
p=HERE/'FYP_P1_P5_Kaggle_BALANCED_2_Hours.ipynb';p.write_text(json.dumps(nb,indent=1))
shutil.copy2(p,Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5')/p.name)
print(p,p.stat().st_size)
