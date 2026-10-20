# Data and results boundaries

## Current system

The retained model is the completed BALANCED P1–P5 run. Work from `current_system/Adhi_To_Amrith_Context.md`, `current_system/paper/CLAIM_LEDGER.md` and saved evidence. The verifier recomputes the headline results without training or model loading. It distinguishes mean held-out macro F1, pooled accuracy, oracle-boundary classification and automatic continuous-story evaluation.

The existing private `aarga-labs/FYP` release contains the verified raw P1–P5 ZIP and full checkpoint archives; metadata and downloader are retained under `current_system/handoff/`. These archives are not duplicated into normal Git or silently merged with old captures.

## Legacy material

The optional consolidation release archive contains 156 unique legacy recordings/model files. A source file's presence is not a claim that the model is correct, trained without leakage, reproducible in the current environment or safe for deployment. September-era combined/derived recordings are unvalidated history and must not replace the verified P1–P5 corpus. Explicit rejected DATA_COMBINED copies were excluded.

Models are archived as files only. No pickle, PyTorch checkpoint, Keras model or notebook was executed during this consolidation. Inspect trusted source and use an isolated environment before loading a legacy model.

Public SignFi/CASAS/wearable benchmark data and rebuildable arrays are listed in `provenance/external_data.csv` and retained in the original source folders, rather than republished as team-collected data. Use each experiment's original README/source references for upstream retrieval and verify the split/shape before rerunning. This repository is not a complete offline mirror of every public dataset or SDK.

## Empty or incomplete copies

`provenance/empty_files.csv` records 71 empty files. They were not promoted to working source or valid recordings. Several have intact copies elsewhere; exact hashes and destinations make the choice auditable. Two zero-byte ZIP placeholders in Rishiikesh's copy are not usable backups.

The original phone/IMU fall-alert branch and ESP32 HTTP actuator are separate from the current CSI-only experiment. Their existence does not establish validated multimodal fusion or real-world safety performance.
