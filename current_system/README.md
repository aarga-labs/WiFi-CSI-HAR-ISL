# Current Wi-Fi CSI implementation

See the [repository overview](../README.md) for the setup, training method and aggregate results.

| Path | Purpose |
|---|---|
| `capture_snapshot/wifi_csi_capture/` | USRP capture code and the P04/P05 protocol |
| `Kaggle_P1_P5/balanced_2h/` | Executed BALANCED notebook and training source |
| `Kaggle_P1_P5/balanced_results_audit_20261017/` | Aggregate outputs, model metadata and retained inference checkpoints |
| `current_impl/` | Analytical figures and nonparticipant setup imagery |
| `Model_Detect-Activity-and-Gestures/` | Earlier P01–P03 source and aggregate results |
| `paper/evidence/` | Retained aggregate result tables |

The retained benchmark is `FYP_BALANCED_2H_20261017_015419`: mean held-out participant macro-F1 is 50.2% for isolated activities and 33.2% for isolated signs. Automatic story detection finds 121/208 signs and correctly names 39/208. The all-five refit has no independent test score.

Raw data, original labels, individual-event arrays/predictions, videos, private access links, context and handoff files are not distributed in the current tracked tree. Aggregate results and event-level verification have different access requirements.

Run `python3 ../tools/verify_repository.py` from this directory for source/aggregate checks. The optional `--private-evidence` flag requires the separately retained local private evidence. New training belongs on Kaggle. The newer `robust_2h` notebook has no verified outputs here.
