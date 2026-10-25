# Data and Results Boundaries

## Current System

The retained primary model is the completed BALANCED P1–P5 run. The repository README, saved evidence and model card describe the implementation and current results. The verifier recomputes headline results without training or model loading. It distinguishes mean held-out macro F1, pooled accuracy, supplied-boundary classification and automatic continuous-story evaluation.

The numerical P01–P05 dataset is published at https://doi.org/10.21227/tbq2-nc86. It contains the selected raw CSI, event labels, quality checks, documentation and reader scripts. It is a Standard DataPort record; download access depends on DataPort subscription or institutional access. Its academic release layout differs from the original training ZIP.

The retired consolidation release is no longer a download source. Original training/archive metadata remains under `current_system/handoff/`; that metadata refers to a separate historical FYP repository release and is not a replacement for the current dataset DOI. Legacy consolidation archives remain backed up locally. Large raw data and optimizer/checkpoint archives are not duplicated into normal Git.

## Legacy & Exploratory Material

The repository cleanly separates earlier exploratory recordings from the primary verified P1–P5 corpus. Synthetically perturbed dataset variations have been excluded to preserve experimental integrity.

Models are archived as source files and weights. No pickle, PyTorch checkpoint, Keras model or notebook was executed without isolation. Inspect trusted source and use an isolated environment before loading a model.

Public SignFi/CASAS/wearable benchmark data and rebuildable arrays are listed in `provenance/external_data.csv` and retained in the original source folders, rather than republished as team-collected data. Use each experiment's original README/source references for upstream retrieval and verify the split/shape before rerunning.

## Empty or Incomplete Files

`provenance/empty_files.csv` records empty placeholder files. They were not promoted to working source or valid recordings. Several have intact copies elsewhere; exact hashes make the choice auditable.

The original phone/IMU fall-alert branch and ESP32 actuator are separate from the current CSI-only experiment. Their existence does not establish validated multimodal fusion or real-world safety performance.
