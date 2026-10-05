# PILOT — `action` vs `noaction` (binary sanity check)

A **one-evening, 2-person pilot** to prove the whole chain works — capture rate,
motion sensitivity, segmentation, RT images, training, honest accuracy — **before**
investing in the full 7-class / 3-subject / 2-day collection
([1_DATA_CAPTURE_GUIDE.md](1_DATA_CAPTURE_GUIDE.md)).

This guide is self-contained: every command you need is here.

---

## 1. Purpose and pass/fail

Binary problem, chance level = 50%. The number that matters is the
**per-window TEST accuracy with `--test-subject`** (trained on member 1, tested on member 2).

| Result | Meaning | Next step |
|---|---|---|
| **≥ 95%** | Pipeline + signal are healthy | Green light → full 7-class plan |
| **85–95%** | Something is weak | Diagnose per take type (Section 8), fix, re-run |
| **< 85%** | Signal problem (rate, gain, geometry) | Do NOT start multi-class. Redo wiggle test / Gates |

---

## 2. The two classes — exactly what to do

The person is **present in both classes**. That is deliberate: the model must learn
*motion*, not *presence*. (`empty` is excluded from the pilot.)

Each subject records **4 takes of 90 seconds** (2 per class):

### `action` — take A: **walk** (90 s)
- Walk back and forth **through the MacBook↔USRP line**, crossing the subject spot
  each pass. Turn around ~1 m past the line on each side.
- Natural indoor pace (~1 step/second). **Never stop moving** for the full 90 s.

### `action` — take B: **mixed** (90 s)
- Stand ON the subject spot and loop this sequence continuously:

  ```
  squat (down + up, ~3 s)
  → bend forward as if picking something up, back up (~3 s)
  → raise hand to mouth like drinking, lower it (~3 s)
  → two side-steps left, two side-steps right (~4 s)
  → repeat  (one loop ≈ 13–15 s → ~6–7 loops in 90 s)
  ```

- Keep transitions flowing — **no freezes**. Every still second becomes a
  mislabeled `action` window (the segmenter labels the *entire* file).
- Exaggerate the drink motion a little; small motions are the hard case we are testing.

### `noaction` — take A: **stand** (90 s)
- Stand still on the subject spot, arms relaxed at sides, look forward.
- Breathe normally, small natural sway is fine. **No phone, no talking, no fidgeting.**

### `noaction` — take B: **sit** (90 s)
- Put a chair on the subject spot, sit still, hands on thighs.
- Same rules: no phone, no talking. Remove the chair after the take.

> **Golden rule for every take:** the subject must already be *in the class state*
> (moving for `action`, frozen for `noaction`) **before the first CSV row is written**,
> and stay in it until the flowgraph is stopped. The auto-chunker slices the whole
> file — anything else in it is labeled wrong.

---

## 3. Environment (same rules as the main guide)

1. One room, door closed, no other people/pets. Same room you'll use for multi-class.
2. Tape marks on the floor:
   - **MacBook ↔ USRP antenna**: 3–4 m apart, antenna ~1–1.2 m high, orientation fixed.
   - **Subject spot**: exactly midway on that line (body must disturb the direct path).
   - **Android phone**: ~1 m behind the MacBook (only keeps the link alive).
   - **Walk lane** (new for the pilot): tape the two turn-around points for the walk
     take, ~1 m either side of the MacBook↔USRP line, so both members walk the same path.
3. Operator sits **behind the USRP, off the path**, and does not move during a take.
4. Photo the setup. Nothing moves between takes.

```
MacBook ──WiFi──> Android hotspot
    \
     \··· RF ···> USRP N210 ──eth──> Fedora laptop ──> CSV
            ^
      subject spot (midway) — walk lane crosses here
```

---

## 4. Roles with 2 members

| Role | Does |
|---|---|
| **Subject** | Performs the take on/through the spot |
| **Operator** | Everything else: Fedora terminal, MacBook ping (start once, leave running), channel/MAC checks, cueing "3-2-1-go", 90 s stopwatch (phone), log sheet |

- The main guide's Coordinator duties fold into the Operator — that works because
  continuous takes need no per-rep ENTER marking.
- **Swap roles** after subject 1 finishes all 4 takes.
- `session_logger.py` is **not needed** for the pilot (auto-chunk mode segments the
  capture CSV directly). Optional: run it with `--continuous` if you want the
  `_meta.json` provenance, but the stopwatch is what times the take.

---

## 5. Verification gates (run first — do not record before all pass)

### Gate 1 — Current MACs (they rotate — check today, not last week's values)

On the MacBook:
```bash
ifconfig en0 | grep ether          # -> CSI_TA
```
**Option-click** the Wi-Fi menu bar icon → note **BSSID** (→ `CSI_RA`) and **Channel**.

### Gate 2 — Channel/frequency match

| Channel | freq |
|---|---|
| 1 | 2412000000 |
| 6 | 2437000000 |
| 11 | 2462000000 |

`wifi_rx` currently uses `freq = 2462000000` (ch 11). If the hotspot moved, fix the
`freq` variable in GNU Radio Companion (or edit `wifi_rx.py`) before continuing.

### Gate 3 — Traffic

On the MacBook (leave this Terminal running the whole evening):
```bash
netstat -nr | grep default            # gateway IP, e.g. 172.20.10.1
sudo ping -i 0.01 <gateway-ip>        # ~100 packets/s
```

### Gate 4 — Rate gate (the make-or-break one)

On the Fedora laptop:
```bash
export CSI_TA=<macbook-mac>  CSI_RA=<hotspot-bssid>
unset CSI_OUT                          # throwaway timestamped file
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
# run 60 s: must show (MATCH) and "~XX rows/s" reports, then Ctrl+C
python3 ~/usrp-projects/USRP_lib/csi_tools/check_capture.py ~/usrp-projects/data/csi_<latest>.csv
```
**PASS = sustained ≥ 50 rows/s (target ~100).** If FAIL → Troubleshooting table in
[1_DATA_CAPTURE_GUIDE.md](1_DATA_CAPTURE_GUIDE.md).

### Gate 5 — Wiggle test (do it today even if it passed before)

Record ~30 s still + ~30 s of arm-waving on the subject spot into one throwaway file,
then `check_capture.py` it and open the `_check.png`: the waving half must look
obviously different by eye. **If you can't see it, the CNN can't either.**

---

## 6. Recording protocol

### 6.1 Naming and location

One **fresh CSV per take** — 8 files total. Create the pilot folder once:

```bash
mkdir -p ~/usrp-projects/data/pilot
```

| Take | File name |
|---|---|
| subject 1, walk | `P01_action_<subject1>_<yyyymmdd>_walk.csv` |
| subject 1, stand | `P01_noaction_<subject1>_<yyyymmdd>_stand.csv` |
| subject 1, mixed | `P01_action_<subject1>_<yyyymmdd>_mixed.csv` |
| subject 1, sit | `P01_noaction_<subject1>_<yyyymmdd>_sit.csv` |
| subject 2 | same 4 names with `<subject2>` |

> ⚠️ `CSI_OUT` **appends**. If a take goes bad, `rm` the bad CSV before redoing it
> with the same name (or name the redo `_try2`) — otherwise junk stays in the file.

### 6.2 Recording order (interleave classes — avoids time-of-day bias)

```
S1 walk → S1 stand → S1 mixed → S1 sit → SWAP ROLES → S2 walk → S2 stand → S2 mixed → S2 sit
```

### 6.3 Per-take procedure (Operator, Fedora terminal)

```bash
# once per evening, in the terminal you'll use for all takes:
export CSI_TA=<today's macbook mac>
export CSI_RA=<today's hotspot bssid>

# per take: set the output file, e.g.
export CSI_OUT=~/usrp-projects/data/pilot/P01_action_rishiikesh_20260717_walk.csv
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
```

Cue script — the difference between the two classes matters:

**`action` takes** (subject moving before first row):
1. Subject in start position. Operator: "3, 2, 1, **go**" → subject starts moving.
2. Operator starts the flowgraph *at "go"* (UHD takes a few seconds to init — by the
   time rows are written, the subject is already moving).
3. First `saved ... rows/s` report appears → check `(MATCH)` and rate ≥ 50 →
   **start the 90 s stopwatch**.
4. At 90 s: **Ctrl+C immediately.** Subject may stop.

**`noaction` takes** (subject frozen before first row):
1. Subject takes position and **freezes** (or sits still).
2. Operator starts the flowgraph, checks `(MATCH)` + rate, starts the stopwatch.
3. At 90 s: **Ctrl+C immediately**, then the subject may move.

**Immediately after every take:**
```bash
python3 ~/usrp-projects/USRP_lib/csi_tools/check_capture.py $CSI_OUT
```
- Rate PASS, duration ≈ 90 s, no NaN/zero warnings → log it, next take.
- Rate FAIL or `(no match)` flood mid-take → MAC rotated or channel hopped:
  re-run Gate 1, fix env vars, `rm` the bad CSV, **redo the take now**.

Bonus eyeball check: the `_check.png` of an `action` take should look wildly wiggly;
a `noaction` take should look almost flat. If they look the same, stop and investigate.

### 6.4 Log sheet (one row per take)

```
date | file name | subject | class | take type | channel | mean rows/s | check PASS? | notes
```

---

## 7. Processing and training (Fedora, after all 8 takes)

### 7.1 Segment into 2 s windows (auto-chunk mode)

The class folder comes from `--action` — so **both walk and mixed use `--action action`**,
and both stand and sit use `--action noaction`:

```bash
cd ~/usrp-projects/USRP_lib/csi_tools
D=~/usrp-projects/data/pilot
S1=rishiikesh   # your two members
S2=amrith
DATE=20260717

python3 segment_windows.py $D/P01_action_${S1}_${DATE}_walk.csv    --action action   --subject $S1 --out-dir $D/windows
python3 segment_windows.py $D/P01_action_${S1}_${DATE}_mixed.csv   --action action   --subject $S1 --out-dir $D/windows
python3 segment_windows.py $D/P01_noaction_${S1}_${DATE}_stand.csv --action noaction --subject $S1 --out-dir $D/windows
python3 segment_windows.py $D/P01_noaction_${S1}_${DATE}_sit.csv   --action noaction --subject $S1 --out-dir $D/windows

python3 segment_windows.py $D/P01_action_${S2}_${DATE}_walk.csv    --action action   --subject $S2 --out-dir $D/windows
python3 segment_windows.py $D/P01_action_${S2}_${DATE}_mixed.csv   --action action   --subject $S2 --out-dir $D/windows
python3 segment_windows.py $D/P01_noaction_${S2}_${DATE}_stand.csv --action noaction --subject $S2 --out-dir $D/windows
python3 segment_windows.py $D/P01_noaction_${S2}_${DATE}_sit.csv   --action noaction --subject $S2 --out-dir $D/windows
```

Each 90 s take → **~45 windows**. Watch the `Saved N windows (M skipped)` line:
more skipped than saved on any file = rate/gap problem in that capture.

### 7.2 Windows → RT images

```bash
python3 make_images.py $D/windows --out $D/dataset
```

Expect ~360 windows total → **~18 700 images** (×52 subcarriers), ~9 400 per class,
under `dataset/action/` and `dataset/noaction/`.

### 7.3 Train — the honest cross-subject test

```bash
python3 train_imgfi.py $D/dataset --test-subject $S2 --out $D/imgfi_pilot_test-${S2}.pt
```

Then swap the held-out subject and run again:

```bash
python3 train_imgfi.py $D/dataset --test-subject $S1 --out $D/imgfi_pilot_test-${S1}.pt
```

**Report the worse of the two per-window accuracies** — that is the pilot's number.
(~10–20 min per run on the GPU; watch the `val_win` column climb during training.)

---

## 8. Reading the result

| Observation | Interpretation | Action |
|---|---|---|
| Both splits ≥ 95% per-window | Motion sensing works end-to-end | **Proceed to the 7-class plan** in the main guide |
| 85–95% | One take type is probably weak — run the diagnostics below | Fix the weak motion / geometry, redo just those takes |
| < 85%, or confusion matrix shows heavy action↔noaction mixing | The CSI barely encodes motion | Back to Gate 5/6: gain, geometry, subject-spot placement. Do not start multi-class |
| Suspiciously = 100.0% on everything | Fine for binary walk-vs-still, but double-check you used `--test-subject`, not a random split | — |

**Diagnostics (only if mediocre):** the take type is embedded in every filename, so a
`--test-match` split isolates it. Each run below tests ONLY that take type (single-class
test set) — its per-window accuracy = how reliably that motion/stillness type is recognized
by a model trained on everything else:

```bash
python3 train_imgfi.py $D/dataset --test-match mixed   # weak-motion sensitivity (the likely culprit)
python3 train_imgfi.py $D/dataset --test-match walk    # strong-motion sensitivity (should be ~100%)
python3 train_imgfi.py $D/dataset --test-match sit     # stillness while seated
python3 train_imgfi.py $D/dataset --test-match stand   # stillness while standing
```

Typical finding: `walk` ≈ 100% but `mixed` low → small motions (drink-like) are under
the noise floor → exaggerate them, check the subject spot really blocks the direct path,
re-check gain — exactly the things that would sink `drink`/`nod` in the 7-class run.

---

## 9. What this data is (and isn't) for

- The pilot dataset is a **throwaway** for the 7-class effort: `mixed` deliberately blends
  squat/bend/drink into one class, so it can't be relabeled later.
- The `walk`, `stand`, `sit` takes *match* the final class definitions (`walk`, `noaction`)
  and *may* be reusable if the geometry never changes — but plan as if they aren't.
- Keep everything under `~/usrp-projects/data/pilot/` so it never mixes with the real dataset.

---

## 10. Time budget (one evening)

| Step | Time |
|---|---|
| Gates 1–5 (MACs, channel, ping, rate, wiggle) | 20–30 min (longer the first time) |
| 8 takes × 90 s + checks + role swap | ~40 min |
| Segmentation + images | ~10 min |
| Training (2 cross-subject runs) | ~20–40 min |
| **Total** | **~1.5–2 h** |

---

## Pre-take mini checklist (Operator reads before each take)

```
[ ] Everything on tape marks, chair on/off spot as required
[ ] CSI_OUT points at the RIGHT new file (no leftover from a bad take)
[ ] ping still running on the MacBook
[ ] Subject briefed: which take, 90 s, no freezes / no fidgeting
[ ] Subject in class state BEFORE first CSV rows (moving / frozen)
[ ] (MATCH) + rate >= 50 seen before stopwatch starts
[ ] After: check_capture.py PASS + log sheet row written
```
