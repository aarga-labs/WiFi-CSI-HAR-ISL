# csi_ml — Phase-1 CSI recognition pipeline

Reads the Phase-1 dataset (read-only), writes caches to `cache/`, plots to `figs/`, results to `results_*.csv`.

## Setup
```
pip install -r requirements.txt
```
The dataset is not in this repo. By default it is read from a `phase1/` folder next to the repo
(containing the CSI CSVs, `labels/` and `session_log.csv`). Point elsewhere with the `CSI_DATA`
environment variable. A CUDA GPU is used for Rocket features and the CNN when available.

## Run order
```
python data.py          # cache amplitude of every kept take, check label coverage
python windows.py       # fixed 5 s trial windows (+ idle/transition) for the classical baselines
python eval_iso.py      # B0 scalar, B1 handcrafted+RF, B2 Rocket+ridge; LOSO + within-subject; leakage probe
python eval_stories.py  # baselines trained on isolated trials, tested on held-out stories
python dense.py         # continuous streams with per-sample labels (50 Hz)
python run_cnn.py       # LOSO multi-task CNN (3 seeds); configs iso, iso+story, cal1, cal2 -> cache/dense_*.pkl
python stream_eval.py   # segment accuracy, streaming sign recall vs FC/h, intent on stories
python select_fine.py   # nested-LOSO selection: classical fine classifiers
python select_state.py  # nested-LOSO selection: CNN variants (window, input, story weight)
python select_adapt.py raw6   # nested check of AdaBN (rejected)
python ens_fine.py      # nested check of CNN + ExtraTrees fusion
python final_system.py  # FINAL model, LOSO zero-shot + 1-rep calibration
python intent_cat.py    # intent-category (I1-I4) accuracy from the final predictions
```
Delete `cache/streams.pkl` / `cache/iso_*.npy` after adding recordings; caches are rebuilt on demand.
New takes are picked up automatically from `session_log.csv` (status `kept`, newest per pid+part).

## Preprocessing (`preprocess.py`)
|H| per subcarrier → despike (running median, 5 MAD) → log → linear resample to 100 Hz on
`Timestamp_us` (gap mask > 100 ms) → 0.3–20 Hz band-pass (removes the static per-file level)
→ divide by the file's noise floor (5th percentile of 1 s energy; label-free).

## Labels
- Trials `[GO, STOP]` → activity / sign. Story steps keypress → keypress.
- Gaps ≤ 7 s between trials: **signs files → idle; actions files → routine/transition**
  (participants reset between action trials, and that motion is larger than many actions).
- State classes: idle / routine (actions + transitions) / sign. Fine: 10 actions + 14 signs.

## Models
- B0 motion-energy scalar, B1 handcrafted + RandomForest, B2 MiniRocket-style features (GPU) + ridge.
- CNN (`cnn.py`): 52×200 window (4 s @ 50 Hz), dilated residual 1D-CNN (~170k params),
  heads state(3) + fine(24); label = majority of the central 2 s; class-balanced sampling;
  augment: scale, sign flip, noise, subcarrier dropout. 3-seed ensemble per fold.

## Evaluation
Results summary: RESULTS.md.
- LOSO is the main split. `calK` = LOSO plus the test participant's first K reps per isolated class
  in training (up-weighted 3x), masked out of testing. Hyper-parameters are fixed a priori (no tuning on the test participant).
- Isolated scores are optimistic: actions and signs are in different files, so file-level cues
  exist (see the leakage probe). **Stories (signs and actions in one file) are the honest test.**
- Streaming: P(sign) smoothed 1 s, threshold τ, ≥ 1 s run → command. Matched to a GT sign with ±1 s.
  Unmatched commands = false commands; FC/h is per hour of routine-labelled time.
- Intent: `intent_of(sign, context)`; context = most recent predicted anchor action in the last
  120 s (eat/drink→meal, tvremote/answerphone→tv, wipetable/pickup→cleaning, fall→after_fall).

## Notes
- Band-pass (`sosfiltfilt`) and the noise floor use the whole file (offline). A deployed system
  needs a causal filter and a running noise floor.
