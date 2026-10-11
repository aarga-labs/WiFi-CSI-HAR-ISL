from pathlib import Path
import json, hashlib, ast, shutil
HERE=Path(__file__).parent
UPLOAD=Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5')
sha=(UPLOAD/'FYP_Phase1_P01_P05_verified.zip.sha256').read_text().split()[0]
cells=[]
def md(s):cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
def code(s):cells.append(dict(cell_type='code',execution_count=None,metadata={},outputs=[],source=s.splitlines(True)))
md('''# Wi-Fi CSI: P1–P5 training and evaluation

Train only on Kaggle GPUs. This notebook includes its own training code; the friend's repository does not need to be uploaded.

**What is being compared:** the existing residual CNN design at 4 and 6 seconds, a compact multiscale CNN, and an ExtraTrees action classifier. Model and fusion choices use training participants only. All models use 12 action classes and 14 sign classes, with an idle/activity/sign state head.

**What the data can establish:** same-room recognition on five recorded people. Only P4/P5 contain isolated seated and cooking additions. P2's missing action tail is excluded by timestamp coverage. Cue and keypress labels have not been video-verified. P4's large story gap is masked and missed events remain visible in evaluation.

**Before Run All**
1. Upload `FYP_Phase1_P01_P05_verified.zip` to Google Drive as a backup. Keep the SHA256 file beside it.
2. Recommended training source: create a **private Kaggle Dataset** from that ZIP and attach it with Add Input. Kaggle may extract the archive automatically; both formats are supported below.
3. Enable an available GPU in Notebook Settings. T4 ×2 is supported if offered; available hardware and quotas depend on your account. Select persistent files if available.
4. Run the notebook. For a short first check set `RUN_MODE = "smoke"`; then switch to `"evaluate"` with a separate output directory automatically selected below.
5. Evaluation may span multiple sessions. Save/download output bundles after each session and reattach them to resume. Do not assume an interactive session's disk is permanent.

No accuracy has been measured for this new pipeline yet. A 90% or 95% target is not a promised outcome.''')
code('''# Configuration — these are the only settings normally requiring changes.
RUN_MODE = "evaluate"       # "smoke", "evaluate", or "final"
FOLDS = ["P01", "P02", "P03", "P04", "P05"]
SESSION_HOURS = 5.0          # graceful stop between epochs, then create a resumable ZIP
BATCH_SIZE = 256             # if GPU memory is insufficient, use 128 in a NEW output run
MULTI_GPU = True             # use both GPUs if available; CPU ExtraTrees remains on CPU
OUTPUT_TAG = "v1"            # change when intentionally changing model/training settings

# Attached private Kaggle Dataset is recommended. Leave blank for automatic discovery.
DATA_ROOT = ""              # folder containing manifest.json and session_log.csv
ZIP_PATH = ""               # alternatively, explicit path to the ZIP in /kaggle/input
DRIVE_URL = ""              # optional share-accessible file link; private links need authentication
EXPECTED_ZIP_SHA256 = "'''+sha+'''"

# On a new session: attach prior notebook output as Input and give the bundle paths here.
# Example: ["/kaggle/input/my-checkpoints/FYP_all_checkpoints_and_results.zip"]
RESUME_BUNDLES = []
''')
md('''## Runtime and GPU check
The neural networks use mixed precision, pinned-memory batches, GPU augmentation, and optional multi-GPU execution. Preprocessing, ZIP verification, plotting, and ExtraTrees are CPU tasks. High GPU occupancy is useful only when it improves throughput; a small dataset does not justify a huge network.''')
code('''from pathlib import Path
import sys, subprocess, importlib.util, json, shutil, os, time
assert Path("/kaggle/working").is_dir(), "Run this notebook on Kaggle. Local training is disabled."
needed = {"numpy":"numpy", "pandas":"pandas", "scipy":"scipy", "sklearn":"scikit-learn", "matplotlib":"matplotlib", "joblib":"joblib"}
missing = [package for module,package in needed.items() if importlib.util.find_spec(module) is None]
if missing:
    subprocess.check_call([sys.executable,"-m","pip","install",*missing])
import torch
assert torch.cuda.is_available(), "Enable GPU in Kaggle Settings, then restart the session."
print("Python:",sys.version)
print("PyTorch:",torch.__version__,"CUDA:",torch.version.cuda)
for i in range(torch.cuda.device_count()):
    prop=torch.cuda.get_device_properties(i)
    print(f"GPU {i}: {prop.name}; {prop.total_memory/2**30:.1f} GiB")
print("Free workspace:",round(shutil.disk_usage('/kaggle/working').free/2**30,1),"GiB")
''')
md('''## Self-contained training implementation
This cell installs the exact source embedded in this notebook. It does not download mutable code from GitHub. Checkpoints store the source/data/configuration fingerprints, class map, preprocessing scale, optimizer, scheduler, mixed-precision scaler, random states, and progress. A mismatched configuration is rejected on resume.''')
source=(HERE/'fyp_pipeline.py').read_text()
code('''ENGINE_SOURCE = '''+repr(source)+'''
ENGINE_PATH = Path("/kaggle/working/fyp_pipeline.py")
ENGINE_PATH.write_text(ENGINE_SOURCE)
sys.path.insert(0,str(ENGINE_PATH.parent))
import importlib
import fyp_pipeline as fyp
fyp=importlib.reload(fyp)
print("Pipeline:",fyp.VERSION,"source SHA256:",fyp.sha256(ENGINE_PATH))
# Synthetic forward pass only; catches CUDA/model incompatibilities before training.
for arch in fyp.CANDIDATES:
    model=fyp.CSIModel(arch).cuda().eval()
    with torch.inference_mode(), torch.autocast("cuda",dtype=torch.float16):
        state,fine=model(torch.zeros(2,52,arch["seconds"]*fyp.FS,device="cuda"))
    assert state.shape==(2,3) and fine.shape==(2,26)
    assert torch.isfinite(state).all() and torch.isfinite(fine).all()
    print(arch["name"],sum(p.numel() for p in model.parameters()),"parameters: forward pass OK")
    del model
torch.cuda.empty_cache()
''')
md('''## Load the ZIP or an extracted private dataset
The archive's SHA256 catches an incomplete or changed download; ZIP CRC checks compression integrity; the internal manifest checks every individual file. An old corrupted Drive folder is not used. The optional Drive downloader needs Internet access and a file that the notebook can access; it does not mount your private Google Drive. Prefer the private Kaggle Dataset route for participant data.''')
code('''if DATA_ROOT:
    dataset_root=Path(DATA_ROOT)
    fyp.verify_data(dataset_root)
else:
    candidates=list(Path("/kaggle/input").rglob("manifest.json"))
    candidates=[p.parent for p in candidates if (p.parent/"session_log.csv").is_file()]
    if len(candidates)==1 and not ZIP_PATH and not DRIVE_URL:
        dataset_root=candidates[0]
        fyp.verify_data(dataset_root)
    else:
        if DRIVE_URL:
            if importlib.util.find_spec("gdown") is None:
                subprocess.check_call([sys.executable,"-m","pip","install","gdown"])
            import gdown
            archive=Path("/kaggle/working/FYP_Phase1_P01_P05_verified.zip")
            if not archive.exists() or fyp.sha256(archive)!=EXPECTED_ZIP_SHA256:
                result=gdown.download(url=DRIVE_URL,output=str(archive),fuzzy=True,quiet=False)
                assert result is not None,"Drive download failed. Attach the ZIP as a private Kaggle Dataset instead."
        elif ZIP_PATH:
            archive=Path(ZIP_PATH)
        else:
            archives=list(Path("/kaggle/input").rglob("FYP_Phase1_P01_P05_verified.zip"))
            assert len(archives)==1,"Set DATA_ROOT or ZIP_PATH to the correct attached dataset."
            archive=archives[0]
        dataset_root=fyp.extract_verified(archive,Path("/kaggle/temp/fyp_verified"),EXPECTED_ZIP_SHA256)
print("Verified dataset:",dataset_root)
''')
md('''## Restore progress and inspect the data
Raw recordings are read only. Missing P2 intervals are excluded; low-rate but complete recordings are retained. Interpolation never treats a severe packet gap as real movement. The 100 Hz resampling/18 Hz causal band-pass is decimated to 50 Hz. Normalization is fitted using training participants only. Empty-room recordings stay as references and do not enter shared training/test data.

A 6-second quality context is used for every candidate so model comparison uses the same valid centers. Short gaps over 100 ms are masked; windows spanning a gap over 250 ms or having less than 95% valid context are rejected. These are fixed quality rules, not tuned to test scores. A fully covered test event with no usable prediction still counts as a miss.''')
code('''assert RUN_MODE in ["smoke","evaluate","final"]
WORK=Path("/kaggle/working") / ("FYP_smoke_"+OUTPUT_TAG if RUN_MODE=="smoke" else "FYP_P1_P5_"+OUTPUT_TAG)
OUT=WORK/"results"
OUT.mkdir(parents=True,exist_ok=True)
for bundle in RESUME_BUNDLES:
    fyp.restore_outputs(bundle,OUT)
streams,dataset_fingerprint=fyp.prepare(dataset_root,WORK)
import pandas as pd
from IPython.display import display, FileLink
coverage=pd.read_csv(WORK/"event_coverage.csv")
display(pd.read_csv(WORK/"recording_audit.csv"))
display(coverage.groupby(["pid","part","covered"]).size().rename("events").reset_index())
display(coverage[~coverage.covered][["pid","part","label","trial","reason"]])
# Preserve the audit with model outputs, too.
for filename in ["recording_audit.csv","event_coverage.csv","dataset_info.json"]:
    shutil.copy2(WORK/filename,OUT/filename)
shutil.copy2(ENGINE_PATH,OUT/"fyp_pipeline.py")
versions={m:importlib.import_module(m).__version__ for m in ["numpy","pandas","scipy","sklearn","torch"]}
fyp.atomic_json(versions,OUT/"environment.json")
''')
md('''## Train and select models
For each outer test participant, the other four undergo four inner folds: train on three, validate on one. Compare residual 4 s, residual 6 s, and multiscale 4 s. Select with equal weighting across isolated action/sign, story action/sign, and story state F1. Early stopping and training duration use these inner folds.

Select action fusion (CNN / 50–50 CNN+ExtraTrees / ExtraTrees) on inner isolated actions. Select the story sign threshold on inner stories, prioritizing **correct-identity event F1**, then detection F1. Refit the selected neural model on all four training people for the inner-selected epoch count, using three seeds. Average their predictions and evaluate the fifth person once.

This is 12 inner neural fits plus three outer fits per participant: 75 fits for a complete evaluation. Run one or several folds per session; completed fits resume or skip. Check the printed epoch timings before estimating completion. Do not change hyperparameters based on outer test results and still call them untouched tests.

`final` runs only after all five folds have been restored. It chooses architecture by the inner-selection vote, derives duration/threshold from inner decisions, and trains three models on **P1+P2+P3+P4+P5**. That deployment refit has no new independent accuracy score.''')
code('''cfg=dict(fyp.DEFAULTS)
cfg.update(folds=FOLDS,batch_size=BATCH_SIZE,multi_gpu=MULTI_GPU,session_hours=SESSION_HOURS)
assert set(FOLDS)<=set(fyp.PIDS) and FOLDS
fyp.atomic_json(cfg,OUT/"run_config.json")
fyp.SESSION_DEADLINE=time.time()+SESSION_HOURS*3600
try:
    if RUN_MODE=="smoke":
        smoke=dict(cfg,epochs=2,min_epochs=1,patience=2,steps_per_epoch=2,seeds=[17])
        train_streams=[s for s in streams if s["pid"] in ["P01","P02","P03"]]
        val_streams=[s for s in streams if s["pid"]=="P04"]
        model,scale,epoch,history=fyp.train(train_streams,val_streams,fyp.CANDIDATES[0],smoke,
                                           OUT/"smoke",dataset_fingerprint,17)
        fyp.release(model)
        print("GPU smoke run completed. These are NOT reportable final results.")
        print("Switch RUN_MODE to evaluate and rerun. Evaluation uses a separate output folder.")
    elif RUN_MODE=="evaluate":
        for participant in FOLDS:
            fyp.run_fold(streams,participant,cfg,OUT,dataset_fingerprint)
    else:
        fyp.final_train(streams,cfg,OUT,dataset_fingerprint)
except fyp.SessionBudgetReached as exc:
    print(exc)
    print("This is a planned pause, not a completed five-person evaluation.")
finally:
    # Runs for a normal finish, handled pause, or Python exception; a force-killed
    # machine cannot execute finally, so keep Kaggle saved output versions too.
    bundle=fyp.archive_outputs(OUT)
    print("Resumable bundle:",bundle)
    display(FileLink(str(bundle)))
''')
md('''## Results and presentation graphs
These graphs are created **after training**, from held-out predictions. No sample numbers are substituted.

- Per-class precision, recall, F1 and confusion matrices for actions and signs.
- Common original classes, all supported classes, seated parts and participant-level results.
- Story detection, correctly recognized signs, false commands per hour and full intent success.
- Training curves, quality coverage and excluded intervals.

Isolated and story-step fine scores use known event boundaries/type and are labeled accordingly. The continuous event evaluation uses predicted segments with one-to-one IoU ≥ 0.10 matching. Adjacent predicted signs are separated only after an identity change persists for one second. This protocol differs from the friend's old ±1-second matching, so compare old numbers as context, not a controlled improvement claim.

Report mean and spread across the five held-out participants, alongside pooled per-class results. P4/P5 cooking and isolated seated evidence involves only two people. Unknown original story postures stay unknown. Fixed story order and shared room limit generalization claims.''')
code('''if RUN_MODE!="smoke":
    summary=fyp.summarize(OUT)
    if summary is not None:
        display(summary)
        display(pd.read_csv(OUT/"posture_participant_metrics.csv"))
    bundle=fyp.archive_outputs(OUT)
    display(FileLink(str(bundle)))
''')
md('''## Keep the models safely
`best.pt` saves inference weights and class/preprocessing metadata. `last.pt` saves full training progress after each epoch; `.previous.pt` provides recovery if a checkpoint becomes unreadable. Each job also records its source/data/configuration signature. Re-running a completed fold skips it; resuming an unfinished one restores optimizer, scheduler, scaler and random states.

**After each session:** use Kaggle Save Version and ensure outputs are saved. Download the checkpoint ZIP or create a private Kaggle Dataset from the saved output. Copy the ZIP to Google Drive as a second backup. A local `/kaggle/working` checkpoint alone is not a guarantee against session expiry. The five-hour setting is a software budget, not Kaggle's account quota or a platform time guarantee.

**Resume elsewhere:** attach those saved outputs as input, list their ZIP paths in `RESUME_BUNDLES`, retain the same code/configuration, and run again. Use one latest complete bundle, or non-conflicting per-fold bundles. Bundles include the training code and all checkpoints; avoid loading checkpoints from unknown sources.

**All-five model:** after all five evaluation folds finish, set `RUN_MODE="final"`. Final models appear in `results/deployment_all5/`. The training routine is disabled outside Kaggle. This notebook does not automatically upload files to your Google Drive account.''')
code('''print("Output directory:",OUT)
print("Completed held-out folds:",[p for p in fyp.PIDS if (OUT/p/"complete.json").exists()])
print("Deployment model ready:",(OUT/"deployment_all5/model_card.json").exists())
if (OUT/"deployment_all5/model_card.json").exists():
    display(json.loads((OUT/"deployment_all5/model_card.json").read_text()))
# Future offline use on a new recording:
# frames,commands=fyp.predict_unlabelled_csv("/path/new_recording.csv",OUT/"deployment_all5")
# frames.to_csv(OUT/"new_recording_predictions.csv",index=False)
''')
md('''## References and next experiments
- Friend's starting point: `Model_Detect-Activity-and-Gestures/{cnn.py,final_system.py,RESULTS.md}`. The residual network is retained as an adapted benchmark; updated normalization, data coverage and evaluation mean this is not a bit-for-bit reproduction.
- [InceptionTime paper](https://arxiv.org/abs/1909.04939): inspiration for the new multiscale convolution candidate; this implementation is a compact variant with channel attention, not the original published ensemble.
- [PyTorch mixed precision](https://docs.pytorch.org/docs/stable/notes/amp_examples.html), [checkpoint guidance](https://docs.pytorch.org/tutorials/recipes/recipes/saving_and_loading_a_general_checkpoint.html).
- [Kaggle notebooks](https://www.kaggle.com/docs/notebooks), [optional gdown downloader](https://github.com/wkentaro/gdown).

After the first locked evaluation: inspect wrong sign pairs and weak seated signals, verify suspicious labels against video, and plan a fresh session/participant test. One-repetition personal calibration is a separate follow-up experiment: calibration trials and nearby windows must be removed from scoring, and no test-person normalization may be fit using the remaining test recording. Calibration and self-supervised pretraining are not included in this first notebook. Do not add them merely to inflate the same test score.''')
for i,c in enumerate(cells):
    c['id']=hashlib.sha256(str(i).encode()).hexdigest()[:8]
    if c['cell_type']=='code':ast.parse(''.join(c['source']))
nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),
    language_info=dict(name='python',version='3.11'),kaggle=dict(accelerator='gpu',isInternetEnabled=True,language='python',sourceType='notebook')),
    nbformat=4,nbformat_minor=5)
path=HERE/'FYP_P1_P5_Kaggle_Training.ipynb'
path.write_text(json.dumps(nb,indent=1))
shutil.copy2(path,UPLOAD/path.name)
print(path, path.stat().st_size, len(cells),'cells')
