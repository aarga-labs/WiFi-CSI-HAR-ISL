# 2 — From CSV to Trained Model (ImgFi Pipeline)

How the captured CSI becomes a working activity classifier, with the reasoning
behind every step. All scripts are in `csi_tools/`.

```
capture CSVs + labels CSVs
        │  segment_windows.py
        ▼
amplitude windows  (52 subcarriers × 200 samples, .npy)
        │  make_images.py
        ▼
RT images  (one 224×224 image PER SUBCARRIER per window, .png)
        │  train_imgfi.py
        ▼
ImgFi CNN  →  per-window prediction (majority vote of 52 images)
```

---

## Step 1 — Segmentation: `segment_windows.py`

### What it does

- Loads a capture CSV, computes **amplitude** per subcarrier: `|H| = sqrt(Re² + Im²)`.
- Cuts out 2-second windows and **resamples each onto a uniform 100 Hz grid**
  (linear interpolation) → every window is exactly a `52 × 200` matrix, regardless
  of the slightly irregular real packet arrival times.
- Skips windows with too few packets (default: less than 50% of expected) and tells you.

### Why amplitude only, never raw phase?

The USRP is not synchronized to the MacBook. Every packet has random carrier
frequency offset, sampling offset and timing offset, which completely scramble the
raw phase. Amplitude is immune to this. ImgFi uses amplitude only for the same
reason — the activity information lives in the magnitude variation.

### Commands

```bash
cd ~/usrp-projects/USRP_lib/csi_tools

# discrete actions (uses the rep timestamps from session_logger):
python3 segment_windows.py ~/usrp-projects/data/S03_squat_amrith_20260716.csv \
        --labels ~/usrp-projects/data/S03_squat_amrith_20260716_labels.csv \
        --out-dir ~/usrp-projects/data/windows

# continuous classes (auto-chunk the whole take into 2 s windows):
python3 segment_windows.py ~/usrp-projects/data/S07_walk_amrith_20260716.csv \
        --action walk --subject amrith \
        --out-dir ~/usrp-projects/data/windows
```

Run this for **every** session file. Output: `windows/<action>/<file>_<action>_<subject>_repNNN.npy`.

Useful options: `--rate` (if your real capture rate is lower than 100, e.g. `--rate 50`
→ windows become 52×100), `--window` (seconds), `--step` (overlapping chunks for
continuous takes, e.g. `--step 1.0` doubles your walk windows).

**Balance check:** after segmenting everything, count windows per class:
```bash
for d in ~/usrp-projects/data/windows/*/; do echo "$d: $(ls $d | wc -l)"; done
```
If `noaction`/`empty`/`walk` have far more than the discrete actions, delete the excess
(keep every class within ~±20% of the smallest).

---

## Step 2 — Image conversion: `make_images.py`

### The technique: RT (Recurrence Transformation)

For one subcarrier's amplitude time series `x = (x₁ … x₂₀₀)`, build a 200×200 matrix:

```
RT[i][j] = | xᵢ − xⱼ |
```

Every pixel compares the signal at time *i* with the signal at time *j*.
This is a recurrence plot with threshold ε = 0 and **no binarization** — the raw
distances are kept as grayscale, so no information is thrown away.

### Why convert to images at all? (the core ImgFi idea)

A CNN looking at the raw 1-D time series only ever learns from single time points.
In the RT image, **every pixel is already a relationship between two timestamps** —
the basic feature unit becomes "how the signal changed between any two moments",
which is exactly what a human movement is. The time order is still preserved along
the diagonal (top-left = start, bottom-right = end). ImgFi tested 5 conversion methods
(RP/RT, GASF, GADF, MTF, STFT) — **RT scored highest (99.8%)** and is also the cheapest
to compute. That is why we use it.

### Why one image per subcarrier?

Each of the 52 subcarriers is a slightly different "view" of the same movement
(different frequency → different multipath sensitivity). Treating each as its own
training image multiplies the dataset ×52 for free: 75 windows/class → ~3900
images/class, which is enough to train the small CNN from scratch.

### Command

```bash
python3 make_images.py ~/usrp-projects/data/windows --out ~/usrp-projects/data/dataset
```

Output: `dataset/<action>/<window_stem>_scNN.png` (224×224 grayscale, min-max
normalized per image). ~200 MB for the full dataset. Rerunning skips existing images.

---

## Step 3 — Training: `train_imgfi.py`

### The model (ImgFi CNN, 3-layer variant)

```
input 1×224×224 (grayscale RT image)
  → Conv 3×3, 64  → BatchNorm → ReLU → MaxPool 2×2      (112×112)
  → Conv 3×3, 128 → BatchNorm → ReLU → MaxPool 2×2      (56×56)
  → Conv 3×3, 256 → BatchNorm → ReLU → MaxPool 2×2      (28×28)
  → AdaptiveAvgPool → 256 values
  → Dropout 0.5 → Linear 256→512 → ReLU → Linear 512→7
```

Why so small? The RT conversion already did the hard feature-engineering work; the
paper shows 3 conv layers reach >99.5% with RT input, matching ResNet50/VGG19 with
~90× fewer parameters. Each piece: **BatchNorm** stabilizes/speeds up training,
**ReLU** adds nonlinearity, **MaxPool** halves resolution and keeps the strongest
response, **AdaptiveAvgPool** replaces giant flatten layers (huge parameter saving),
**Dropout** fights overfitting on our small dataset.

### Hyperparameters (from the paper)

| Parameter | Value |
|---|---|
| Loss | CrossEntropyLoss |
| Optimizer | Adam, lr = 0.001 |
| LR schedule | ×0.8 each epoch (exponential decay) |
| Epochs | 20 |
| Batch | 64 (paper used 128; 64 is safer on our GPU) |

### The one rule that keeps the results honest: split by SUBJECT, never randomly

All 52 subcarrier images of one window come from the **same physical 2 seconds**.
If you shuffle images randomly, near-copies of the same event land in both train and
test → you get a fake ~99% that means nothing. The script therefore refuses random
splits; you must name what is held out:

```bash
# main evaluation: leave-one-subject-out (train on 2 people, test on the 3rd)
python3 train_imgfi.py ~/usrp-projects/data/dataset --test-subject gowreesh
python3 train_imgfi.py ~/usrp-projects/data/dataset --test-subject amrith
python3 train_imgfi.py ~/usrp-projects/data/dataset --test-subject rishiikesh

# secondary evaluation: leave-one-day-out (tests environment drift)
python3 train_imgfi.py ~/usrp-projects/data/dataset --test-match 20260717
```

Validation (15% of training windows, used for model selection) is also split by
window, never by image.

### Two accuracies are reported — which one matters?

- **per-image** — accuracy over individual subcarrier images. Diagnostic only.
- **per-window** — the 52 images of a window vote, majority wins. **This is the real
  system accuracy** ("someone squatted → did we say squat?"). It is always higher
  than per-image and is the number you report.

### Reading the output

- `imgfi_model.pt` — best model (chosen by validation per-window accuracy).
- `imgfi_model_confusion.csv` + printed confusion matrix — rows = truth, columns =
  prediction. Look at what confuses what: expect `nod` ↔ `noaction` to be the
  weakest pair (smallest motion), and `walk` to be the easiest.

### What counts as success?

| Result | Meaning |
|---|---|
| >90% per-window on an **unseen subject**, 7 classes | Genuinely good — the model learned the motions, not the people |
| ~99% only when you test on the same subjects/days you trained on | Normal but weaker claim — report the unseen-subject number as the headline |
| ~99% with a random image shuffle | Leakage. Not a result. The script blocks this on purpose |
| `nod` mostly confused with `noaction` | Expected; either exaggerate nods when re-collecting or merge/drop the class |

### If accuracy is bad (<70% per-window on unseen subject)

1. Look at RT images by eye (`dataset/walk/...png` vs `dataset/noaction/...png`) —
   if *you* can't see texture differences, the data is the problem, not the model:
   go back to the wiggle test / rate gate.
2. Check class balance and window counts.
3. Check that capture rate was steady in each session (`check_capture.py` plots).
4. Only then try model-side changes: more epochs, `--val-frac 0.2`, or a 4th conv
   layer (512 channels — edit `channels=(64,128,256,512)` in the script).

---

## Optional experiments (after the baseline works)

- **Other imaging methods from the paper** (GASF/GADF/MTF/STFT) — all read the same
  windows `.npy`, so only `make_images.py` needs a variant. RT should stay best.
- **Overlapping windows** (`--step 1.0` at segmentation) — cheap data doubling for
  the continuous classes.
- **3-layer vs 4-layer CNN** — the paper's headline comparison; easy ablation.
