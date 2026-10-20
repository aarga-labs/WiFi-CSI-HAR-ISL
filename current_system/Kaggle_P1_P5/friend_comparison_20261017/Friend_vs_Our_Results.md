# Friend’s results compared with our balanced run

Our run improves isolated recognition on the original participants. Continuous stories remain a limitation, and several story measures are lower. There is no evidence that our model is better at every task.

## Matched original test recordings

Both columns below use the same 684 P1–P3 events and the same 10-action/14-sign class lists. Values are macro F1 averaged equally across held-out participants. Each scored participant was excluded from that system’s training. Story identity is evaluated with the true event boundaries and type supplied.

| Metric | Friend’s final zero-shot | Our balanced run | Change |
|---|---:|---:|---:|
| Isolated actions F1 | 48.6% | 54.9% | +6.3 points |
| Isolated signs F1 | 20.8% | 34.3% | +13.5 points |
| Story actions F1 | 60.5% | 55.2% | -5.3 points |
| Story signs F1 | 20.6% | 20.8% | +0.3 points |
| Story sign-versus-action AUC | 91.5% | 88.0% | -3.5 points |

F1 is not accuracy. AUC measures separation of signs from actions across thresholds; it does not measure correct sign identity or successful commands.

The friend’s published action F1 is 48.8%. It becomes 48.6% when restricting both systems to shared events. Their output includes one extra P02 lightswitch event (repetition 9) whose full labelled interval is not covered by the recording. Our preparation excludes that partial interval. No predictions were changed for this comparison.

The friend trained on two other people for each P1–P3 test. Our run trained on four other people, adding P4/P5 and their seated/cooking examples. Architecture, preprocessing, validation and training also differ. These figures compare the saved systems on shared test data; they cannot isolate which change caused a gain. With only three matched test people, small differences are uncertain.

![Matched result comparison](/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/Friend_vs_Our_Results/friend_vs_ours.png)

## Isolated results for each original participant

| Participant | Friend action F1 | Our action F1 | Friend sign F1 | Our sign F1 |
|---|---:|---:|---:|---:|
| P01 | 44.2% | 50.5% | 24.8% | 30.4% |
| P02 | 56.7% | 63.3% | 25.3% | 36.0% |
| P03 | 44.9% | 50.9% | 12.4% | 36.5% |

## Which classes improved

These class F1 values pool the matched original participants, rather than averaging their individual class F1 scores.

| Class | Friend | Ours | Interpretation |
|---|---:|---:|---|
| wipetable | 45.0% | 76.2% | Large gain |
| pickup | 52.3% | 75.0% | Large gain |
| sitstand | 71.6% | 86.7% | Gain |
| COOK | 48.0% | 80.0% | Large gain |
| FAN | 22.2% | 56.0% | Large gain |
| HELLO | 0.0% | 32.8% | Gain |
| eat | 55.3% | 44.9% | Lower |
| tvremote | 24.0% | 16.1% | Lower and still weak |
| TOILET | 16.7% | 9.5% | Lower |
| WATER | 28.6% | 22.2% | Lower |
| THANKYOU | 0.0% | 0.0% | Neither system recognizes these isolated examples correctly |

![All matched class scores](/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/Friend_vs_Our_Results/matched_class_results.png)

THANKYOU has 0% F1 for both systems on these original isolated examples. That is a reason to inspect the recorded movement, signal and annotation boundaries. The saved predictions alone cannot establish the cause.

## Full five-person results

Our full held-out P1–P5 results are 50.2% isolated action F1, 33.2% isolated sign F1, 52.4% story action F1 and 24.7% story sign F1 with known story boundaries/type. Those are a wider evaluation: they include P4/P5, seated recordings and two extra action classes. They should not replace the matched table when comparing the original participants.

Isolated seated action/sign F1 is only 19.4%/20.0%, evaluated on P4/P5. The friend has no equivalent isolated seated test set. Chopping and stirring likewise have no matching old classes.

## Calibration is a separate experiment

The friend’s final one-repetition calibration system scores 53.4% action F1 and 29.8% sign F1. It uses a labelled example from the test person per class and excludes those examples from evaluation. Our reported run uses no test-person calibration. These protocols and test sets differ, so the calibrated numbers are not an equal comparison.

The 38% calibrated sign F1 in the friend’s earlier table comes from an earlier CNN experiment. Their saved final-system sign F1 is 29.8%. Keep the experiment names and protocols attached to every figure instead of combining the best numbers from different runs.

## Continuous commands need separate treatment

The friend’s reported 78.3% streaming event F1 combines isolated and story sign detections and does not require correct sign identity. It uses one-second matching tolerance. Our story metrics use stories only, identity-aware scoring and one-to-one overlap matching. Their false-command rate also includes routine time outside stories. Directly comparing those exported streaming F1 or hourly false-command numbers would be misleading.

On the 108 original story sign steps, the friend reports 25.9% detected and 2.8% correct full intent. Our counts are 52 detected (48.1%) and 9 correct full intents (8.3%). These are descriptive because detection matching and context implementations differ. A common re-evaluation of continuous outputs is needed for a defensible improvement claim.

Across all five participants, our system detects 121 of 208 story signs, correctly identifies 39 and produces 32 correct full intents (15.4% end-to-end success). It produces 50 false commands over 20.3 minutes of measured story routine time. Continuous operation is therefore still weak despite better isolated F1.

## What to do next

Keep both baselines. The next experiment should address continuous sign identity, seated performance and false commands. Audit THANKYOU, WATER, TOILET and TV remote examples and boundaries first. Evaluate personal calibration as a separately named protocol, or test changes on a fresh session after validation-based selection. More epochs alone have not been shown to solve these failures.

Use the same stream matching, threshold-selection objective and routine-time denominator for both pipelines before presenting a streaming comparison. A controlled experiment using the same folds, preprocessing and data would be required to attribute improvement to an architecture.

## Evidence

- Friend: `results_final_segments_cal0.csv`, `results_final_summary.csv`, `results_final_stream_cal0.csv`, `final_system.py`, `dense.py`, `RESULTS.md` in `Model_Detect-Activity-and-Gestures`.
- Ours: `all_out_of_fold_predictions.csv`, `summary.csv`, `fold_metrics.csv` and `story_metrics.csv` in `FYP_BALANCED_2H_20261017_015419/results`.
- `participant_comparison.csv`, `matched_class_comparison.csv`, `matched_predictions.csv` and `unmatched_events.csv` preserve the matched comparison. `comparison_manifest.json` records input hashes.

This comparison only reads saved outputs and computes metrics/plots. No training ran on the laptop.
