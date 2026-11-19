# Activity vs Gesture — Collection and Evaluation Guide

Single-modality WiFi CSI, single person, **Activity vs Gesture** classification.
This is the operational guide for the 3-day sprint; `DATA_COLLECTION.md` covers
the general HAR protocol and why hopping was abandoned.

Everything here assumes **both radios parked on one channel**. Hopping yields
~2.4 Hz of CSI against the ~50 Hz human motion needs — see
`doc/THREE_CHANNEL_ANALYSIS.md`.

---

## 0. Hardware addresses — read this first

The two USRPs are, verified against the flowgraphs that produced every working
capture in `doc/`:

| Role | USRP address | Flowgraph |
|---|---|---|
| **Transmitter** | `192.168.10.7` | `transmitter/.../wifi_tx_multi_hop.py` |
| **Receiver** | `192.168.10.9` | `receiver/.../wifi_rx.py` |

Revisions of `RECEIVER.md` / `TRANSMITTER.md` before 2026-09-01 had these
backwards. If your hardware differs, override without editing any file:

```bash
export RX_ADDR=192.168.10.7      # receiver laptop
export TX_ADDR=192.168.10.9      # transmitter laptop
```

`receiver/preflight.sh` prints which USRPs actually answer.

---

## 1. The classes

Nine classes, **10 s per instance**, gestures repeated continuously for the
full 10 s so window counts stay balanced against the activities.

| Group | Class | What the subject does |
|---|---|---|
| activity | `walk` | Walks back and forth across the TX–RX line |
| activity | `sitstand` | Repeated sit-down / stand-up at the midpoint |
| activity | `bend` | Repeatedly bends to pick something up |
| activity | `standstill` | Stands motionless at the midpoint |
| gesture | `hello` | Open-palm wave, repeated |
| gesture | `comehere` | Beckoning motion, repeated |
| gesture | `stop` | Palm-out push forward, repeated |
| gesture | `thankyou` | Hand from chin outward, repeated |
| control | `empty` | Nobody in the room |

**No underscores in any name** — the filename is the label and loaders split it
on `_`. `capture.sh` rejects them.

The fine class always goes in the filename. The Activity/Gesture binary label is
derived at training time from `CLASS_GROUP` in `analysis/dataset.py`. You can
always collapse fine labels to coarse ones; you can never recover fine labels
you did not record.

---

## 2. Geometry — the confound that decides whether any of this is publishable

**Identical geometry for every class.** If gestures were recorded up close and
activities at a distance, the model learns position, not motion, and the result
is worthless.

- TX and RX **3 m apart**, line of sight, antennas at **~1.1 m**.
- Subject stands at the **midpoint** for every class. `walk` crosses that same
  midpoint; gestures are performed standing at it with **hands raised into the
  direct path**, body otherwise still.
- **Tape-mark** both antenna feet and the subject's spot. Do not move them for
  the entire collection — not between subjects, not between days.
- Door closed, nobody else moving, phones on the far side of the room.

### The number that actually matters

`standstill` vs the gestures is the meaningful contrast: both have a stationary
torso and differ **only** in hand motion. `analysis/train.py` reports it
separately. If the full binary score is excellent but this pair is near chance,
the system is a "big motion vs small motion" detector, not a gesture detector —
report that honestly rather than letting a panel member find it.

---

## 3. Recording

### Transmitter laptop (two terminals, both stay running)

```bash
cd transmitter/gr-ieee802-11/examples
export TX_CHANNEL=1          # 1, 6 or 11 — must match the receiver
python3 wifi_tx_multi_hop.py # expect: PARKED on Channel 1 (2412 MHz)
```

```bash
cd transmitter/gr-ieee802-11/examples
export PPS=300               # ceiling on the receiver's CSI rate
python3 packet_generator.py  # expect: Connected — sending 300 pkt/s
```

Keep `TX_GAIN` **fixed** for the whole dataset. Changing transmit power
mid-collection is a distribution shift the model will learn instead of the
activity.

### Receiver laptop

```bash
cd receiver
export CSI_CHANNEL=1         # MUST match TX_CHANNEL
./preflight.sh               # run this once per collection day
```

One instance at a time:
```bash
./capture.sh rishi walk 01 10
```

A whole subject in randomised order, with resume:
```bash
export ROOM="LabA"
./session.sh rishi 20 10     # 20 reps x 9 classes x 10 s
```

`session.sh` is safe to re-run — instances already on disk are skipped, so an
interrupted session resumes where it stopped.

### What capture.sh does, and why the order matters

1. Starts the flowgraph and **waits until CSI is actually arriving**.
2. Only then beeps and prints `GO`, recording the exact microsecond.
3. Records for the requested duration, then stops cleanly (SIGINT, so the CSV
   is flushed and closed).
4. Writes a `.json` sidecar with the exact `go_us` / `stop_us` interval.
5. Runs `qc.py` on **that interval only** and fails the instance if it is bad.

Step 1 is the point. Bringing up the USRP and acquiring OFDM sync takes several
seconds; cueing the subject before that (as the pre-2026-09-01 script did) meant
every instance recorded the tail of the activity rather than the activity.

---

## 4. Quality gates

`capture.sh` rejects an instance if any of these fail, while the subject is
still in the room:

| Gate | Default | Why |
|---|---|---|
| mean rate | ≥ 40 Hz | below ~36 Hz the motion band is aliased, not merely degraded |
| usable 2 s windows | ≥ 70 % | a burst-then-hole capture can average 50 Hz and still have no usable window |
| largest gap | < 1 s | a whole gesture fits inside a 1 s hole |
| channel label | matches `CSI_CHANNEL` | catches a receiver that is not actually parked |

Override per run: `MIN_RATE=35 ./capture.sh ...`

Check any capture by hand:
```bash
python3 qc.py ~/usrp-projects/data/har/ch1/rishi_walk_01.csv --expect-channel 1
```

---

## 5. Analysis

```bash
cd analysis
python3 pilot_check.py --channel 1 --subject pilot   # Day-1 go/no-go
python3 dataset.py --channel 1            # inspect before training
python3 train.py --channel 1              # RandomForest baseline
python3 train.py --channel 1 --model cnn  # recurrence plots + CNN (needs torch)
```

`dataset.py` slices each capture to its `go_us`/`stop_us` interval, resamples
every 2 s window onto a uniform 50 Hz grid (CSI arrives irregularly, and a CNN
needs a fixed shape), and tags every window with its instance id and subject.

### Evaluation protocol

`train.py` reports, in this order:

| Report | What it answers |
|---|---|
| majority baseline | what you get by always guessing the larger class |
| **LOSO** | **the headline** — accuracy on a person never seen in training |
| by-instance CV | upper bound: unseen recordings, same people |
| standstill vs gesture | is hand motion really being detected? |
| shuffled-label control | must collapse to chance, or there is leakage |
| per-fine-class recall | which classes carry the errors |
| instance-level | windows majority-voted per recording, as deployed |

**Windows are never split at random.** They overlap 50 %, so neighbouring
windows from one recording are near-duplicates. Measured on this pipeline, a
random window split scored **0.997** where leave-one-subject-out scored
**0.742** on the same data and model — a 25-point overstatement. Every split
here is on whole instances or whole subjects.

Requirements: `numpy` and `scikit-learn` for the baseline; `torch` additionally
for `--model cnn`. The baseline is a legitimate result on its own.

---

## 6. Plan

| Day | Work |
|---|---|
| 1 | `preflight.sh` on both laptops. Spectrum-scan 1/6/11, park on the quietest. Pilot: `walk`, `hello`, `standstill`, `empty` at 20 s each. **Go/no-go: does `hello` separate from `standstill`?** Send the professor the protocol with the pilot numbers attached. |
| 2 | Subjects 1 and 2, full set, Room A (~2 h). QC after each subject. First training run in the evening. |
| 3 | Room B set for cross-environment. Final training, LOSO, baseline, confusion matrices. Slides. |

**The Day-1 go/no-go is the real risk.** Hand gestures perturb the channel far
less than walking. If `hello` does not separate from `standstill`, raise
`RX_GAIN`, shorten TX–RX to ~2 m, and make sure the hands cross the direct
path. If it still fails, fall back to three large-amplitude gestures (two-arm
wave, big beckon, arm raise) and say so in the write-up.

---

## 7. Known limitations to state up front

- Amplitude only. Phase needs CFO/SFO sanitisation this setup does not do.
- Single link, single person, single parked channel per session.
- 10 s repeated-gesture instances are **not** word-level continuous sign
  language recognition — they support Activity-vs-Gesture discrimination only.
- The binary task is expected to score high because whole-body and hands-only
  motion differ greatly in CSI variance. The `standstill`-vs-gesture number and
  the fine-class confusion matrix are what make the result meaningful.
