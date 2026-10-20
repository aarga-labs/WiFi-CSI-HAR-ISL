# Run the new two-hour-budget notebook

Use **FYP_P1_P5_Kaggle_FAST_2_Hours.ipynb**. This is fresh training and does not use the stalled run or its checkpoints.

1. Stop the old background run so it no longer uses GPU quota.
2. Create a new Kaggle notebook and import this new `.ipynb`.
3. Attach the same private P1–P5 dataset. No dataset upload is needed again.
4. Select **GPU T4 ×2**.
5. Click **Save Version → Save & Run All** once.

Defaults already run the five participant tests and then the all-five final model. There is no separate smoke/evaluate/final setting. Internet is unnecessary when Kaggle's normal packages and your attached dataset are available.

The previous pipeline ran 75 neural fits. This one runs 15 evaluation fits plus one final fit. It compares a residual four-second CNN with a compact multiscale four-second CNN, using one fixed validation person inside each outer training group. It refits the winner on four people before testing the fifth. A single seed, validation every two epochs, early stopping, and 32 batches per epoch limit the workload. Both GPUs run independent jobs; training batches are gathered directly from GPU memory. No DataLoader worker processes or DataParallel are used.

The time budget starts at the first code cell:

| Stage | Limit |
|---|---:|
| Data setup | At most 10 minutes |
| Five held-out tests | Stop by minute 85 |
| All-five deployment training | Stop by minute 105 |
| Graphs / output ZIP | At most 5 minutes, capped by minute 115 |

Each individual fold has a 24-minute cap; the final refit has an 18-minute cap. A separate supervisor terminates a worker after five minutes without a completed phase/checkpoint. That timeout does not depend on the training process returning from a CUDA operation.

These are code-enforced compute budgets, not a GPU benchmark or a guarantee that hardware will complete every fit. Queue time and Kaggle's final output publishing are outside notebook control. An interrupted, failed or incomplete fold is clearly marked. If fewer than five folds finish, do not call the result a completed five-fold evaluation. If final training fails, the notebook reports the model as missing.

The completed version saves class-wise metrics, confusion matrices, posture and participant results, story detection / identity / intent results, training curves, checkpoints and an all-five model card. Download `FYP_all_checkpoints_and_results.zip` from Output and keep a separate copy. Exact inference weights, class order, preprocessing scale, configuration and source are included. Every epoch also saves full optimizer/scheduler/scaler state and random-state metadata; this fresh-run notebook does not load old checkpoints.

Local checks cover notebook syntax/schema, embedded sources, five disjoint participant splits, model forward shapes, sample-indexing equivalence, watchdog handling, deadline skipping and synthetic metrics/plot export. No real model fitting was done locally. GPU speed and accuracy will be known only after the Kaggle run.
