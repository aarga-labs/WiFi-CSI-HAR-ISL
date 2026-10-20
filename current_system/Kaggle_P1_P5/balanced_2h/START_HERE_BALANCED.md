# Corrected P1–P5 training

Import **FYP_P1_P5_Kaggle_BALANCED_2_Hours.ipynb** into a fresh Kaggle notebook. Attach the same private P1–P5 dataset, select **GPU T4 ×2**, and click **Save Version → Save & Run All** once. No old checkpoint, output ZIP or mode change is needed.

The downloaded six-minute run was complete and correctly saved its model. Its held-out action macro F1 was 0.355 and sign macro F1 0.181. The final fit used only 384 optimizer updates. Diagnostic CPU inference also showed a large gap between training-person and unseen-person recognition. Longer training alone is therefore not treated as a solution.

This revision changes:

- Epoch draw budgets scale with available windows. For the current all-five data, one epoch is 246 batches at batch size 256, rather than 32. Balanced sampling uses replacement, so this is an expected draw budget, not a guarantee that every unique window appears once.
- Up to 100 epochs, validation every four epochs, early stopping, and the same cosine learning-rate horizon during candidate selection and refits.
- Three validation-tested candidates: residual four seconds, residual six seconds, and a window-normalized four-second residual network with group normalization and retained energy information.
- Candidate choice is made separately for detection, action identity and sign identity. The two-seed ensemble is refitted on the four training participants; the fifth participant stays outside all selection.
- Augmentation noise is relative to each window's signal level, avoiding a fixed noise level that can overwhelm weak seated motion.
- Training probes, learning rate, draw counts and update counts are saved so that underfitting and poor generalization are visible.

The final model uses all five participants. The original class coverage, missing-P2 exclusions, quality masks, participant-separated tests, class-wise plots, story metrics and model saving remain in place.

The compute budget is measured from the first code cell: evaluation ends by minute 75, all training ends by minute 105, and reporting/export ends by minute 115. The independent supervisor stops stalled jobs. Partial evaluation and failed final training remain explicitly labeled. Queue time and Kaggle publishing are outside these code limits. Actual completion/runtime and improvement require this Kaggle run; no high-accuracy claim is made in advance.

The maximum workload is 51 neural fits, usually fewer because roles can share models. Efficient GPU-resident batches and two independent GPU workers are retained. There are no DataLoader worker processes and no DataParallel.

Download the completed version's `FYP_all_checkpoints_and_results.zip`. It includes all model weights, per-role architecture choices, class maps, preprocessing scales, histories, metrics, plots and inference code. The deployment refit has no independent new score. Final confirmation after this benchmark-informed revision needs a fresh recording session or participant.

Local validation covers schema/syntax, embedded sources, split separation, all three CPU forward passes, checkpoint round trips, relative-noise scaling, role-head combination, dataset-scaled batches, and fake-fit orchestration through all five folds and the final ensemble. Real saved weights were inspected by CPU inference for the audit. No model fitting, optimizer update or classifier training ran on the laptop.
