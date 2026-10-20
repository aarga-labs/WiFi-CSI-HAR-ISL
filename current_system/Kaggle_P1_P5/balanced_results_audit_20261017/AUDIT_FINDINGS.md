# Activity and sign recognition results

The balanced Kaggle run completed all five participant tests and saved the all-five model. Both final seed models load correctly. The archive passed CRC validation, saved participant splits exclude the test person, and 34 exported metric rows were independently recomputed from the predictions. The old and new runs evaluated the same 1,534 event IDs.

| Held-out mean macro F1 | Previous | Balanced | Change |
|---|---:|---:|---:|
| Isolated actions | 35.5% | 50.2% | +14.8 percentage points |
| Isolated signs | 18.1% | 33.2% | +15.2 percentage points |
| Isolated seated actions | 11.0% | 19.4% | +8.4 percentage points |
| Isolated seated signs | 9.6% | 20.0% | +10.4 percentage points |
| Story actions, known boundaries/type | 38.2% | 52.4% | +14.1 percentage points |
| Story signs, known boundaries/type | 12.8% | 24.7% | +11.9 percentage points |

These are F1 scores, not accuracy. Headline figures average the held-out participants equally. The class-specific values below pool their event predictions, so their averaging does not exactly reproduce the headline score. P4/P5 alone provide isolated seated and cooking recordings.

## Which classes work

| Group | Stronger classes, pooled F1 | Weak classes, pooled F1 |
|---|---|---|
| Actions | walk 91.1%, pickup 80.8%, sitstand 63.9% | tvremote 11.2%, chop_food 16.3%, answerphone 32.8% |
| Signs | COOK 65.8%, FAN 49.2%, HUNGRY 47.6% | THANKYOU 4.3%, WATER 11.1%, TOILET 17.4% |

Most classes improved. TV remote and THANKYOU became worse, so the higher overall F1 should not be used to imply improvement on every class. Inspect these classes' examples and label alignment before another broad training change.

![Previous and balanced class-wise results](/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/Balanced_Result_Review/classwise_comparison.png)

## Continuous recognition is the main remaining limitation

There were 208 true story signs. The model matched a detection to 121 of them (58.2%), correctly identified 39 signs (18.8% of all true signs), and produced 32 correct full intents (15.4%). Known-boundary story scores therefore do not describe end-to-end command success.

The system produced 239 predicted sign commands. Fifty unmatched commands occurred during 20.3 minutes of measured routine activity. That corresponds to about 148 false commands per measured routine hour; the short observation period makes the hourly estimate uncertain. P1 had no correctly identified story signs. These remain substantial limitations for continuous use.

![Story detection and identity counts](/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/Balanced_Result_Review/story_pipeline_counts.png)

## What the model contains

The final package contains two normalized four-second networks, trained with seeds 17 and 29, using all P1–P5. Each final network received 12 epochs of 246 batches: 2,952 updates each. The final all-five refit has no separate independent score; the results above come from the held-out participant folds.

The package includes class order, preprocessing scales, architecture and role choices, the model card, both weight files and offline inference code. Continuous inference uses CNNs. ExtraTrees fusion applies only to known isolated windows, and its final selected weight is zero. The model uses centered windows; it is an offline prototype rather than a zero-latency live recognizer.

## Next work

Keep this run as the current benchmark. Check the performed movements and annotation boundaries for THANKYOU, WATER, TV remote and chopping, and compare seated examples with standing examples. The saved results show which cases fail but cannot prove whether a failure comes from the recording, labels or model.

For another experiment, evaluate either a separately reported personal-calibration protocol or a new balanced seated session. Calibration examples and their overlapping windows must be excluded from scoring. Use validation data for rejection/threshold changes aimed at reducing false commands. Do not repeatedly select changes by the same test results and then call that an untouched final test.

The earlier six-minute run showed a large training-person versus unseen-person gap. This revision improves the recorded benchmark, but more training time alone is not established as the solution. A fresh recording session or new person is needed to confirm final generalization after fixing the design.

## Verification limits

The audit checked archive integrity, participant metadata, class order, learning-rate horizon, draw/update counts, model loading, CPU forward output shapes, metric recomputation and matched event IDs. Existing weights were used for CPU inference only. No training or optimizer update ran on the laptop. A new live recording was not tested in this audit.
