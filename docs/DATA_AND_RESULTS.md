# Data and Results Boundaries

## Current System

The retained primary model is the completed BALANCED P1–P5 run. Work from `current_system/Adhi_To_Amrith_Context.md`, `current_system/paper/CLAIM_LEDGER.md` and saved evidence. The verifier recomputes the headline results without training or model loading. It distinguishes mean held-out macro F1, pooled accuracy, oracle-boundary classification and automatic continuous-story evaluation.

The private repository release contains the verified raw P1–P5 ZIP and full checkpoint archives; metadata and downloader are retained under `current_system/handoff/`. These archives are not duplicated into normal Git or silently merged with older exploratory captures.

## Legacy & Exploratory Material

The repository cleanly separates earlier exploratory recordings from the primary verified P1–P5 corpus. Synthetically perturbed dataset variations have been excluded to preserve experimental integrity.

Models are archived as source files and weights. No pickle, PyTorch checkpoint, Keras model or notebook was executed without isolation. Inspect trusted source and use an isolated environment before loading a model.

Public SignFi/CASAS/wearable benchmark data and rebuildable arrays are listed in `provenance/external_data.csv` and retained in the original source folders, rather than republished as team-collected data. Use each experiment's original README/source references for upstream retrieval and verify the split/shape before rerunning.

## Empty or Incomplete Files

`provenance/empty_files.csv` records empty placeholder files. They were not promoted to working source or valid recordings. Several have intact copies elsewhere; exact hashes make the choice auditable.

The original phone/IMU fall-alert branch and ESP32 actuator are separate from the current CSI-only experiment. Their existence does not establish validated multimodal fusion or real-world safety performance.
