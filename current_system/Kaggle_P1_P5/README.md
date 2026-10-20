> CURRENT ENTRY: read ../Adhi_To_Amrith_Context.md. This README documents the original extensive notebook before later runs. The retained completed result is BALANCED under balanced_results_audit_20261017; the newer robust_2h notebook has no verified outputs. Do not rerun training to write the paper.

# P1–P5 Kaggle training

Start with **FYP_P1_P5_Kaggle_Training.ipynb**. The notebook contains the complete implementation; upload that notebook and the verified data archive. Training is explicitly blocked outside Kaggle. No model has been trained during preparation.

## Files to upload

In `/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/`:

- `FYP_Phase1_P01_P05_verified.zip`: 901,985,586 bytes, about 902 MB / 860 MiB.
- `FYP_Phase1_P01_P05_verified.zip.sha256`: archive checksum.
- `FYP_P1_P5_Kaggle_Training.ipynb`: self-contained GPU notebook.
- `TRAINING_PLAN.md`: experiment and interpretation guide.

The ZIP contains 22 latest kept participant takes, three empty-room references, 22 label files, selected session log, receiver logs, P4/P5 audit reports and a SHA256 manifest. Discarded takes, duplicate compressed copies, and old fabricated DATA_COMBINED data are excluded. Phone videos are not included.

Archive SHA256:

```
74259c5718d512ffa9cd3bdf63f150badcd6887e0cd2b35f780602e6e13a165c
```

Upload this ZIP to Google Drive as the backup. Do not rely on the previously damaged expanded `data` folder. The screenshot alone cannot establish whether the older ZIP is intact. This new archive was independently compressed, read back, CRC-tested, and all member hashes checked.

For training, create a **private Kaggle Dataset** from the ZIP and attach it to the notebook using Add Input. Kaggle may automatically unpack it; the notebook supports both packed and extracted layouts. This avoids Drive permissions/download-quota interruptions. An optional Drive URL setting is provided for a file the notebook can access; it does not authenticate to or mount your private Drive. Do not make participant data public just to use the downloader.

## First run

1. Import `FYP_P1_P5_Kaggle_Training.ipynb` into a new Kaggle notebook.
2. Attach the private dataset; select an available GPU in Settings. Enable Internet only if needed for a missing package or the optional Drive download.
3. Set `RUN_MODE = "smoke"` for a two-epoch GPU/checkpoint check. This has its own output folder and produces no final research score.
4. Set `RUN_MODE = "evaluate"` and run. The default covers all five outer folds, with a five-hour software budget. For a shorter session set `FOLDS = ["P01"]`; continue the other participants in later sessions.
5. Inspect the data audit before trusting any results. There should be five participants, 22 participant takes, and P4/P5 each have 425 covered action/sign/story events.
6. Save the Kaggle notebook version **with outputs**. Download the checkpoint bundle and copy it to Drive as a second backup.

Available GPU types, quotas and platform session limits vary. The five-hour software budget is not a claim about Kaggle's session allowance. It stops between epochs and exports progress; a force-killed machine cannot execute cleanup. Check printed epoch timings and save outputs during long work.

## Resume or move to another Kaggle session

Attach the previous saved outputs as a private input. Set `RESUME_BUNDLES` to the path of `FYP_all_checkpoints_and_results.zip`, or several non-conflicting per-participant ZIPs. Keep the same source and training settings. Run again; unfinished jobs resume at the next epoch and completed folds skip. An incompatible dataset/configuration is rejected rather than silently reusing a checkpoint.

Do not list an older and newer bundle containing different copies of the same files together. Prefer the latest full bundle. A changed batch size, architecture, or optimizer setting is a new experiment: choose a new `OUTPUT_TAG` and do not restore incompatible jobs.

After all five evaluation folds finish, set `RUN_MODE = "final"`. This trains the deployment ensemble using **all P1–P5**. The final model is under `results/deployment_all5/`. This refit does not produce another independent test accuracy.

## Saved results

- `best.pt`: model weights, preprocessing scale, class order, architecture and dataset fingerprint.
- `last.pt`: model, optimizer, scheduler, mixed-precision scaler, RNG states, epoch and best model.
- `.previous.pt`: recovery copy of the previous checkpoint.
- Per-fold selection, training curves, probability arrays, trial/step predictions, per-class metrics, confusion matrices, story events and inferred intents.
- Coverage audit, excluded intervals, environment versions, configuration, code and checksums.
- Full and per-fold ZIPs for downloading and resuming.

Google Drive uploads are manual in this version. The notebook does not contain account credentials. Kaggle's saved-version outputs and a downloaded/Drive copy provide the backups; simply writing to `/kaggle/working` does not make a checkpoint permanently safe.

## Local verification completed

`validation/verification.json` records actual checks: all archive/file hashes, all 22 recordings parsed and preprocessed, all 20 nested participant splits disjoint, 27 incomplete P2 action intervals excluded, P4/P5 coverage, synthetic model forward passes, checkpoint recovery, unsafe archive path rejection, feature extraction and metric export.

No optimizer step, classifier fitting, or real model training was performed locally. CUDA, multi-GPU, and actual accuracy remain unverified until the Kaggle smoke/evaluation runs. The notebook is structurally checked and intentionally has no fabricated training outputs.

Implementation source: `fyp_pipeline.py`. Notebook builder: `build_notebook.py`. Packaging: `prepare_upload.py`. Read-only validation: `test_pipeline.py`. The friend's original files are unchanged.
