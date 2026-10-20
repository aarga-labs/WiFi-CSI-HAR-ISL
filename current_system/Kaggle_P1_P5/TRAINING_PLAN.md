# Training plan for P1–P5

The goal is a model that recognizes an unseen person reliably and still works when signs and ordinary actions appear in the same recording. Model size and training accuracy are secondary to that test. No accuracy target is guaranteed by the available five-person dataset.

## What to retain from the existing work

The friend's selected system used a residual temporal CNN, four-second input for signs, six-second input for detection/actions, and CNN–ExtraTrees fusion for isolated action identity. Reported original participant-averaged action macro F1 was approximately 0.49, sign macro F1 0.21, and end-to-end story intent success approximately 0.03. The story result is the more demanding check; a high sign-vs-action AUC does not mean signs or intents are correctly recognized.

Retain the residual architecture, temporal filtering, class balancing, three-seed ensemble and action-feature benchmark. Correct hard-coded participant/class lists, missing `actions_seated`, and fitting normalization to whole held-out participants. Retain the difference between oracle-segment classification and automatic event detection.

This notebook is an adapted benchmark, not an exact reproduction of the old system. Both preprocessing and event matching are deliberately documented so old scores are not presented as a controlled before/after comparison.

## Data preparation

Use the verified archive of actual kept recordings, labels and session log. It includes all five participants, standing signs, new seated blocks, two cooking actions, stories, and available baselines. The model predicts 12 actions and 14 signs, plus idle/activity/sign state.

Check ZIP integrity and every file's SHA256 before preprocessing. Check CSI channel/schema, monotonic timestamps, finite values, label bounds and class names. Exclude incomplete P2 action intervals. Preserve bad-gap/coverage statistics; do not turn a packet outage into interpolated evidence of a gesture.

Resample amplitude-only CSI to 100 Hz, apply a causal 0.3–18 Hz band-pass, then decimate to 50 Hz. Reset the filter after severe gaps and mask startup. Fit the normalization scale only on training participants. No participant ID, file name, posture, true story context, or event duration is supplied as a model input. Fixed-length windows avoid directly encoding trial length.

Short inter-trial idle/routine labels follow the recording protocol, so those labels remain an assumption requiring future video checks. Empty-room captures are QC references and are not shared across folds as labelled training samples.

## Models to compare

| Candidate | Purpose |
|---|---|
| Residual CNN, 4 seconds | Adapt the existing architecture for short sign movements. |
| Residual CNN, 6 seconds | Retain longer action/detection context as a competing choice. |
| Compact multiscale CNN, 4 seconds | Learn short and longer patterns in parallel, with channel attention and group normalization. |
| ExtraTrees on motion/spectral features | CPU benchmark and optional isolated-action fusion. |

The multiscale model is inspired by InceptionTime, with approximately 148,000 parameters here. The residual candidates have approximately 167,000 parameters. These are alternatives to validate, not a claim that the new candidate will win. A large transformer is not the first experiment for this small set of independent participants.

The neural networks share an idle/activity/sign head and a 26-class identity head. Training uses state/class/participant balancing, AdamW, a cosine schedule, mild amplitude/noise/subcarrier augmentation, gradient clipping, dropout and validation-based early stopping. Averaging three seeds reduces reliance on a lucky run. GPU mixed precision, pinned-memory loading, batched inference and optional two-GPU execution improve throughput. Preprocessing and ExtraTrees remain CPU tasks.

## Unseen-person evaluation

Five outer folds: hold out P1, then P2, P3, P4 and P5. For every outer fold, split the other four people into four inner folds: train on three and validate on one. Every window from a participant stays in the same side of that split.

Use inner folds for architecture, stopping epoch, action fusion weight and story sign threshold. Give isolated and story recognition equal visibility in model selection. Fit the selected architecture on the four training people for the inner-selected duration, then score the held-out person. The outer participant never influences model selection, fitted scaling, or threshold tuning.

A full run contains 60 inner fits and 15 outer seed fits. It can span sessions and resumes from checkpoints. Do not promise a fixed runtime before seeing Kaggle's actual GPU and epoch timings.

After locking this protocol, further decisions based on outer results require a fresh session/person test for a clean final claim.

## Results worth presenting

1. Per-action and per-sign precision, recall, F1, support and confusion matrices.
2. Mean and spread across held-out people, not only a pooled accuracy.
3. The original common ten actions/14 signs separately from expanded classes and seated blocks.
4. Automatic story event detection, correctly identified signs, false commands per measured routine hour, and full intent success.
5. Oracle-boundary fine recognition separately from automatic segmentation. Story AUC is supplementary.
6. Training curves, low-quality coverage, excluded intervals and unavailable predictions.

P4/P5 are the only participants with isolated seated/cooking additions. Those results therefore have two-person test support, and one inner training split can have no cooking examples when both expanded participants are excluded. Report that limitation. P1–P3 have seated story actions/signs, but their missing explicit posture metadata must not be silently invented.

Story sequence patterns are repeated and recording day partly follows participant group. Good cross-person results in this room would not establish robustness to a new room, arbitrary sign order or a new antenna layout. CSI-only recognition of fourteen selected signs is not general sign-language translation.

## Final model and saving

After all five evaluation folds finish, choose the deployment architecture from the inner-selection decisions, not whichever outer score looks best. Refit a three-seed model on all five people, with the matching action tree, scale, class map and inference code. Keep the held-out evaluation results as the performance evidence; the all-five refit has no new independent score.

Save best weights and full resumable state after each epoch with atomic replacement and a previous-checkpoint copy. Include source/data/configuration fingerprints, optimizer, scheduler, mixed-precision scaler and RNG states. Save a portable checkpoint ZIP after each complete fold and on a graceful stop. Save Kaggle versions with outputs and download/backup the ZIP to Drive.

The model currently uses centered four/six-second windows. It is an offline prototype with look-ahead, not a zero-latency live recognizer. Continuous inference uses CNN predictions; the ExtraTrees fusion applies to known isolated event windows only. Deployment must preserve that distinction.

## What to do if signs remain weak

Inspect confusion pairs and event alignment first. Compare standing/seated performance and whether weak classes have visible CSI variation. More epochs cannot recover a signal that was barely measured. Video-review ambiguous examples, then collect a new balanced session with all actions/postures per participant.

Personal one-repetition calibration is a worthwhile separate experiment because the friend's results improved with calibration. It is not included in this first notebook: calibration trials, overlapping context windows and nearby filter support must be kept out of scoring. Report zero-shot and calibrated results separately. Self-supervised learning is a later validation-tested candidate, not an automatic improvement.

Sources: [friend's source repository](https://github.com/aarga-labs/FYP/tree/main/Model_Detect-Activity-and-Gestures), [InceptionTime](https://arxiv.org/abs/1909.04939), [PyTorch AMP](https://docs.pytorch.org/docs/stable/notes/amp_examples.html), [PyTorch checkpoints](https://docs.pytorch.org/tutorials/recipes/recipes/saving_and_loading_a_general_checkpoint.html), [Kaggle notebooks](https://www.kaggle.com/docs/notebooks).
