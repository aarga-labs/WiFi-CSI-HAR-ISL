# Current Wi-Fi CSI implementation

The [repository overview](../README.md) describes the setup, published dataset, training pipeline and verified results.

## Main entry points

| Path | Purpose |
|---|---|
| `capture_snapshot/wifi_csi_capture/` | USRP capture source snapshot, including the P04/P05 protocol |
| `Kaggle_P1_P5/balanced_2h/` | Executed BALANCED GPU notebook and training source |
| `Kaggle_P1_P5/balanced_results_audit_20261017/` | Retained run, saved predictions and all-five inference checkpoints |
| `current_impl/` | Class-performance figures, setup media and presentation assets |
| `handoff/` | Original training-archive metadata and source provenance |
| `Model_Detect-Activity-and-Gestures/` | Earlier P01–P03 implementation and results |
| `paper/evidence/` | Existing curated evaluation tables and annotation evidence |
| `paper/tools/verify_evidence.py` | Read-only checks and metric recomputation |

## Dataset and results

Published dataset: **https://doi.org/10.21227/tbq2-nc86**. It contains 25 selected recordings, including three empty-room references, and 2,050,030 raw CSI rows. The 22 participant recordings contain 2,010,899 rows. The DataPort release and the original training archive use different directory layouts and checksums.

Retained run: `FYP_BALANCED_2H_20261017_015419`. Mean held-out participant macro-F1 is 50.2% for isolated activities and 33.2% for isolated signs. In automatic stories, 121/208 signs are detected and 39/208 are correctly named. The all-five refit has no independent test score.

```bash
python3 paper/tools/verify_evidence.py
```

This verifies saved evidence without training, model loading or downloading raw recordings. New training belongs on Kaggle. The newer `robust_2h` notebook has no verified execution outputs in this repository.

## Earlier material

Historical handoff notes, proposals and pilot experiments document earlier stages. Their dataset claims and metrics are not interchangeable with the retained P01–P05 benchmark. Earlier ESP32/IMU/public-benchmark experiments do not establish multimodal fusion in the current CSI-only system.

The newer, unfinished research-paper workspace is maintained separately and is not imported by this documentation update.
