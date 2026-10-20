from pathlib import Path
import ast,json,hashlib,shutil
HERE=Path(__file__).parent
DEST=Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5')
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):cells.append(dict(cell_type='code',execution_count=None,metadata={},outputs=[],source=s.splitlines(True)))
md('''# P1–P5: GPU training within a two-hour run budget

Fresh training using the same verified private dataset. No old run or old checkpoint is needed.

**Run:** attach the P1–P5 private dataset, select **GPU T4 ×2**, then **Save Version → Save & Run All**. No settings need changing if the dataset is detected automatically.

This notebook performs **15 evaluation fits + 1 all-five deployment fit**, rather than the previous 75-fit search. Each outer test person has one predeclared validation person drawn from the other four; two compact CNNs compete, then the selected model is refitted on four people. Every test person's recordings stay outside training and model selection.

The notebook uses at most two independent training processes, one per GPU. It has no DataLoader worker processes and no DataParallel. Training samples are gathered directly from GPU memory. Validation runs every second epoch, early stopping is enabled, and one seed is used. This is a faster evaluation protocol with less model-selection coverage and no multi-seed uncertainty estimate.

**Budget:** measured from the first code cell. Data setup has a 10-minute ceiling; evaluation ends by minute 85; all training ends by minute 105; reporting/export has at most 5 minutes, capped by minute 115. The remaining margin is reserved for notebook completion. Background queue time and Kaggle publishing after execution are outside this code's control.

The watchdog can terminate a frozen training process independently of CUDA. If an operation fails or the budget prevents full evaluation, the outputs say **PARTIAL**; a stopped or incomplete run is never presented as a completed five-fold result. The code cannot guarantee a trained model if hardware fails. No actual training runtime or accuracy is claimed until this notebook runs on Kaggle.''')
code('''# Configuration — defaults are ready for the existing private P1–P5 dataset.
import time
RUN_STARTED=time.time()
EVALUATION_DEADLINE=RUN_STARTED+85*60
TRAINING_DEADLINE=RUN_STARTED+105*60
FINISH_DEADLINE=RUN_STARTED+115*60

DATA_ROOT=""    # optional explicit folder containing manifest.json and session_log.csv
ZIP_PATH=""     # optional explicit path to the verified ZIP
EXPECTED_ZIP_SHA256="74259c5718d512ffa9cd3bdf63f150badcd6887e0cd2b35f780602e6e13a165c"
STALL_SECONDS=300         # terminate a worker with no phase/checkpoint progress for five minutes
MAX_FOLD_MINUTES=24
MAX_FINAL_MINUTES=18
''')
md('''## Set up the notebook
The notebook contains all required source code. It uses Kaggle's installed packages and does not install or download training code. The raw input is read only. A new output directory is created for each run.''')
code('''from pathlib import Path
import os,sys,json,shutil,subprocess,importlib,importlib.util
assert Path("/kaggle/working").is_dir(),"Run on Kaggle; local training is disabled."
for module in ["torch","numpy","pandas","scipy","sklearn","joblib","matplotlib"]:
    assert importlib.util.find_spec(module) is not None,f"Missing Kaggle package: {module}"
import torch
assert torch.cuda.is_available(),"Enable a GPU in Kaggle Settings."
GPUS=min(torch.cuda.device_count(),2)
print("GPUs:",GPUS,"PyTorch:",torch.__version__)
for i in range(GPUS):print(i,torch.cuda.get_device_name(i))
WORK=Path("/kaggle/working")/("FYP_FAST_2H_"+time.strftime("%Y%m%d_%H%M%S",time.gmtime(RUN_STARTED)))
OUT=WORK/"results";OUT.mkdir(parents=True,exist_ok=True)
SOURCE_DIR=WORK/"source";SOURCE_DIR.mkdir(exist_ok=True)
''')
files=['fyp_fast.py','fast_runner.py','fast_prepare.py','fast_report.py']
code('''SOURCES = '''+repr({n:(HERE/n).read_text() for n in files})+'''
for filename,source in SOURCES.items():(SOURCE_DIR/filename).write_text(source)
sys.path.insert(0,str(SOURCE_DIR))
import fast_runner
print("Sources written:",SOURCE_DIR)
''')
md('''## Validate and prepare all five participants
ZIP CRC and SHA256 checks detect incomplete uploads. The manifest checks individual files. Missing P2 action intervals are excluded; P4/P5 seated/cooking additions and packet-gap masks are included. Normalization is fitted using training participants only. Empty-room files remain quality references.

The model input is 52 subcarriers at 50 Hz. Short and severe gaps are handled with the same fixed quality rules as the previous notebook. Video performance and cue/keypress label accuracy remain unverified.''')
code('''prep=dict(pid="PREPARE",spec_path=str(WORK/"prepare.json"),progress=str(WORK/"prepare.progress.json"),
          deadline=min(RUN_STARTED+10*60,TRAINING_DEADLINE),work=str(WORK),
          data=dict(root=DATA_ROOT,zip=ZIP_PATH,sha=EXPECTED_ZIP_SHA256))
prep_status=fast_runner.run_jobs([prep],SOURCE_DIR/"fast_prepare.py",max_parallel=1,stall_seconds=STALL_SECONDS)
assert prep_status[0]["status"]=="complete","Dataset preparation failed or exceeded its budget; read prepare.log. No training started."
prepared=json.loads((WORK/"prepared.json").read_text())
assert prepared["participants"]==["P01","P02","P03","P04","P05"] and prepared["streams"]==22
import pandas as pd
from IPython.display import display,FileLink,Image
display(pd.read_csv(WORK/"recording_audit.csv"))
coverage=pd.read_csv(WORK/"event_coverage.csv")
display(coverage.groupby(["pid","part","covered"]).size().rename("events").reset_index())
for filename in ["recording_audit.csv","event_coverage.csv","dataset_info.json"]:shutil.copy2(WORK/filename,OUT/filename)
for filename in SOURCES:shutil.copy2(SOURCE_DIR/filename,OUT/filename)
versions={m:importlib.import_module(m).__version__ for m in ["torch","numpy","pandas","scipy","sklearn"]}
(OUT/"environment.json").write_text(json.dumps(versions,indent=2))
''')
md('''## Run five held-out participant tests
Candidates: the friend's adapted residual CNN at four seconds, and a compact four-second multiscale CNN. Both predict idle/activity/sign and all 26 fine classes. The candidate, stopping epoch, story threshold, and isolated-action ExtraTrees fusion weight use the fixed validation person only.

| Test person | Validation person | Initial training people |
|---|---|---|
| P1 | P4 | P2, P3, P5 |
| P2 | P5 | P1, P3, P4 |
| P3 | P1 | P2, P4, P5 |
| P4 | P2 | P1, P3, P5 |
| P5 | P3 | P1, P2, P4 |

Each selected CNN is then refitted on all four training people before scoring the held-out person. Each fit has at most 28 epochs and 32 batches per epoch; validation runs every two epochs. A single seed and fixed validation split save time. The two GPUs run different test folds; models never exchange data or predictions during training.''')
code('''cfg=dict(epochs=28,patience=4,min_epochs=8,steps_per_epoch=32,batch_size=256,
         lr=0.001,weight_decay=0.01,seed=17,tree_estimators=300)
(OUT/"training_config.json").write_text(json.dumps(cfg,indent=2))
common=dict(out=str(OUT),streams=str(WORK/"cache/prepared_streams.joblib"),fingerprint=prepared["fingerprint"],cfg=cfg)
specs=[]
for participant in ["P01","P02","P03","P04","P05"]:
    specs.append(dict(common,pid=participant,spec_path=str(WORK/(participant+".json")),
        progress=str(WORK/(participant+".progress.json")),deadline=EVALUATION_DEADLINE,max_job_seconds=MAX_FOLD_MINUTES*60))
evaluation_status=fast_runner.run_jobs(specs,SOURCE_DIR/"fyp_fast.py",max_parallel=GPUS,stall_seconds=STALL_SECONDS)
(OUT/"evaluation_status.json").write_text(json.dumps(evaluation_status,indent=2))
display(pd.DataFrame(evaluation_status))
''')
md('''## Train and save the all-five model
The final model trains on **P1+P2+P3+P4+P5**. Architecture is chosen by validation-selection votes, never by outer test performance. Training duration and threshold come from those validation decisions.

This deployment refit is saved separately and has no new independent accuracy score. If evaluation was incomplete, the model card says so. If no fold completed, the code uses a predeclared residual model and threshold rather than inventing validation evidence. A failed or timed-out final fit is reported as missing.''')
code('''final_spec=dict(common,pid="FINAL",spec_path=str(WORK/"FINAL.json"),progress=str(WORK/"FINAL.progress.json"),
                deadline=TRAINING_DEADLINE,max_job_seconds=MAX_FINAL_MINUTES*60)
final_status=fast_runner.run_jobs([final_spec],SOURCE_DIR/"fyp_fast.py",max_parallel=1,stall_seconds=STALL_SECONDS)
(OUT/"final_status.json").write_text(json.dumps(final_status,indent=2))
completed=[p for p in ["P01","P02","P03","P04","P05"] if (OUT/p/"complete.json").exists()]
card=OUT/"deployment_all5/model_card.json"
print("Completed participant tests:",completed)
print("All-five final model ready:",card.exists())
if card.exists():display(json.loads(card.read_text()))
''')
md('''## Results, graphs and downloadable model
Per-class F1 and confusion matrices are generated from real held-out predictions. Story detection, correct sign identity, full intent success, false commands per hour and posture breakdowns remain separate from oracle-boundary scores.

Only P4/P5 have isolated seated and cooking additions. Those results have two-person coverage. The new faster protocol differs from the previous full nested/multi-seed search, so compare its results with that limitation stated.

Weights and full training state are written atomically each epoch, with a previous checkpoint copy. This notebook starts fresh and does not resume old training. Save the completed Kaggle version's outputs and download the result ZIP for a separate backup.''')
code('''report_spec=dict(common,pid="REPORT",spec_path=str(WORK/"REPORT.json"),progress=str(WORK/"REPORT.progress.json"),
                 deadline=min(FINISH_DEADLINE,time.time()+5*60))
report_status=fast_runner.run_jobs([report_spec],SOURCE_DIR/"fast_report.py",max_parallel=1,stall_seconds=240)
status=dict(completed_test_participants=completed,evaluation_complete=len(completed)==5,
            all_five_model_ready=card.exists(),elapsed_minutes=round((time.time()-RUN_STARTED)/60,2),
            runtime_measured_on_this_run=True,report_status=report_status)
(OUT/"run_completion.json").write_text(json.dumps(status,indent=2))
display(status)
archive=OUT.parent/"FYP_all_checkpoints_and_results.zip"
if archive.exists():display(FileLink(str(archive)))
else:print("ZIP export did not finish. Individual model and result files remain under:",OUT)
for figure in sorted((OUT/"figures").glob("*.png")):display(Image(filename=str(figure)))
print("Save/download the completed version's Output files. Output directory:",OUT)
''')
md('''## Interpretation and verification
Neural training uses amplitude-only CSI, mild augmentation, balanced state/class/participant sampling, AdamW, gradient clipping and mixed precision. The model uses centered windows and is an offline prototype, not zero-latency live recognition. Continuous inference uses CNN predictions; ExtraTrees fusion uses known isolated windows.

Before delivery, the notebook is checked for syntax, embedded-source consistency, split disjointness, GPU-bank indexing equivalence using synthetic CPU tensors, result export, and watchdog termination of fake stalled processes. **No training is executed on the laptop.** CUDA performance and accuracy require this Kaggle run.

[PyTorch AMP](https://docs.pytorch.org/docs/stable/notes/amp_examples.html) · [Kaggle notebooks](https://www.kaggle.com/docs/notebooks) · [InceptionTime inspiration](https://arxiv.org/abs/1909.04939)''')
for i,c in enumerate(cells):
 c['id']=hashlib.sha256(str(i).encode()).hexdigest()[:8]
 if c['cell_type']=='code':ast.parse(''.join(c['source']))
nb=dict(cells=cells,nbformat=4,nbformat_minor=5,metadata=dict(kernelspec=dict(name='python3',display_name='Python 3',language='python'),language_info=dict(name='python'),kaggle=dict(accelerator='gpu',isInternetEnabled=False,language='python',sourceType='notebook')))
path=HERE/'FYP_P1_P5_Kaggle_FAST_2_Hours.ipynb';path.write_text(json.dumps(nb,indent=1))
shutil.copy2(path,DEST/path.name)
print(path,len(cells),'cells',path.stat().st_size,'bytes')
