# Phase-1 results — 14 Oct 2026 (P01–P03, data of 2 Oct)

3 participants only. LOSO = train on 2 people. All numbers are preliminary.
Hyper-parameters were fixed before testing; nothing was tuned on a test participant.

## 1. Data findings (act on these before recording more)
| Finding | Evidence | Action |
|---|---|---|
| **Seated signs are near the noise floor** | peak motion above floor: standing signs 7–25×, mattress 7–17×, **seated 1.6–2.4×** (`figs/story_energy.png`) | Test seating position / antenna height before `signs_seated` and P04 |
| Action-file gaps are not idle | participants reset (walk back, sit, get up) during rest/ready; gap energy > many actions (`figs/go_locked_energy.png`) | Labelled `transition` (routine, I0). Explains "weak actions" in the 2 Oct QA |
| File-level cues exist | actions vs signs file predictable from static level (0.60–0.96) and quietest-second noise (0.78–0.94) | Band-pass + per-file noise-floor normalisation; **stories are the honest test** |
| Packet rate / trial length | 85–131 rows/s; trials 4–6 s | 100 Hz resample on `Timestamp_us`; fixed-length windows |

## 2. Isolated trials, oracle segmentation (macro-F1, mean over held-out participants)
| Model | 10 actions | 14 signs |
|---|---|---|
| B0 motion-energy scalar, LOSO | 0.06 | 0.11 |
| B1 handcrafted + RF, LOSO | 0.34 | 0.20 |
| B2 MiniRocket + ridge, LOSO | 0.27 | 0.18 |
| CNN (iso+story), LOSO | 0.38 | 0.23 |
| CNN + 1-rep calibration | 0.47 | **0.38** |
| CNN + 2-rep calibration | **0.52** | 0.30* |
| B2 within-subject (held-out reps) | 0.63 | 0.38 |

Chance: 0.10 / 0.07. *2-rep leaves only 3 test reps per sign, so it is noisier.
Sign vs action on isolated trials is 0.96–0.99 for every model, but it is inflated by file cues.

## 3. Stories (signs and actions in the same file), CNN step-level sign-vs-action accuracy
| Training | seated signs | standing signs | mattress signs | seated actions |
|---|---|---|---|---|
| isolated only | 0.35 | 0.58 | 0.63 | 0.74 |
| + other participants' stories | 0.65 | 0.58 | 0.54 | 0.80 |

Sign identity on story signs: 7–29 % (chance 7 %).

## 4. Streaming commands (smoothed P(sign) > τ for ≥ 1 s; ±1 s match)
| Config | Source | τ | sign recall | sign ID given detected | false commands / h routine |
|---|---|---|---|---|---|
| iso+story | isolated | 0.7 | 0.70 | 0.25 | 6.1 |
| cal1 | isolated | 0.7 | **0.83** | **0.40** | **1.4** |
| cal2 | isolated | 0.7 | 0.86 | 0.34 | 0.0 |
| iso+story | story | 0.7 | 0.25 | 0.15 | 19.8 |
| cal1 | story | 0.7 | 0.31 | 0.09 | 19.8 |

Story routine time is only 9 min in total, so story FC/h is very noisy. Full τ sweeps are in `results_stream_*.csv`.

## 5. Intent (story sign steps)
- End-to-end (detect + identify + context): 3–4 %. Limited by story detection (~27 %) and sign ID.
- With the true sign: predicted context 0.88, no context 0.89, true context 1.00.
  Only HOT (meal vs tv) and HELP (cleaning vs after_fall) depend on context. Context from
  predicted actions fails because seated eat/drink/tvremote/answerphone are near chance,
  and `fall` steps are often called `walk` (the step includes walking to the mattress).

## 6. What this means
1. The pipeline works end to end. The bottleneck is **signal for seated activity** plus **only 2 training people**.
2. Calibration is the biggest lever: 1 rep per class from the user adds +0.09 (actions) and +0.15 (signs) F1
   and cuts false commands about 4×. This is a realistic deployment step and a good paper experiment.
3. Story results only become meaningful once seated signs are visible in the CSI. After the geometry is fixed,
   record `signs_seated` and add P04+.
4. For the paper, report stories as the main evaluation, isolated trials as supporting results, and the
   file-cue probe as a methodological point.

## 7. Final model (nested-LOSO selection, `final_system.py`)
Every choice was made on inner folds (train on one training participant, validate on the other).
The test participant was used only for the final score.

| Part | Choice | Rejected (nested) |
|---|---|---|
| Sign detector + action head | CNN, 6 s window, raw input, no adaptation | 3 s / 4 s window, energy-envelope input, story weighting ×3, AdaBN |
| Action identity | mean of CNN(6 s) and ExtraTrees (handcrafted, per-participant feature z-score) | either alone |
| Sign identity | CNN, 4 s window | Rocket / RF / ET, fusion with ET |
| Threshold τ | maximise event F1 on inner folds (selected 0.3–0.4) | – |

| Metric (mean over held-out participants) | zero-shot | 1-rep calibration |
|---|---|---|
| Action macro-F1, 10 classes (isolated) | **0.49** | **0.53** |
| Sign macro-F1, 14 classes (isolated) | 0.21 | 0.30 |
| Intent category accuracy, I1–I4, from sign head (isolated / story) | 0.46 / 0.48 | 0.51 / 0.46 |
| Story sign-vs-action AUC (step level) | **0.92** | 0.89 |
| Streaming at inner τ: sign recall / precision / event F1 | 0.69 / 0.92 / 0.78 | 0.63 / 0.85 / 0.72 |
| Streaming at inner τ: false commands per hour of routine | 14.9 | 21.1 |
| Streaming at τ = 0.5: recall / FC/h | 0.64 / 6.0 | 0.62 / 6.7 |
| Streaming at τ = 0.7: recall / FC/h | 0.51 / 4.1 | 0.52 / 3.5 |
| Story signs detected / intent end-to-end | 0.26 / 0.03 | 0.23 / 0.03 |

Chance: actions 0.10, signs 0.07, intent category 0.25 (majority 0.29).

Notes
- Run-to-run variance is large with 3 participants: sign F1 with 1-rep calibration was 0.38 in the
  earlier run and 0.30 here. Treat differences below about 0.05 as noise.
- Story AUC is high, but story detection at a fixed τ is low: story P(sign) values are lower overall
  (seated, continuous motion), so a threshold that works on isolated recordings misses them.
- The inner-chosen τ favours recall (event F1). For a home, τ ≈ 0.5–0.7 (4–6 false commands per hour)
  is probably the better operating point.

## Reproduce
See README.md. Training all CNN configs takes about 10 min each on the RTX 4060.
