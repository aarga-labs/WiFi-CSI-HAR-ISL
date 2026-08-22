# Activity Recognition — Data Collection Protocol

Follow this top to bottom. Every command is meant to be run as written.

Two laptops are involved throughout: **RX** (this one, `receiver/`) and **TX**
(your friend's, `transmitter/`).

---

## 0. Why this document exists

The three-channel hopping setup **cannot produce usable activity-recognition
data**, and it isn't a tuning problem. Measured from your own captures:

| Setup | CSI rate | Median gap | 95th-pct gap |
|---|---|---|---|
| Single channel, parked (`csi_20260717`, 11 s) | **54.9 Hz** | 13 ms | 49 ms |
| Three channels, hopping (`3ch_test_001142`, 890 s) | **1.94 Hz** | 102 ms | 972 ms |

The hopping figure is a long-run average and it moves around a lot — the same
capture read 0.49 Hz over its first 114 s and 1.29 Hz over its first 785 s,
because the two hop loops drift in and out of phase. That instability is itself
part of the problem. Even at the most favourable reading it is **~28x short of
the parked rate**.

Three independent reasons ~2 Hz fails:

1. **Nyquist.** Human motion puts CSI energy from ~1 Hz (gait) up to tens of Hz
   (limb Doppler). At ~2 Hz you don't undersample that — you miss it and alias
   the remainder into noise. Coarse activity classification generally wants
   20–30 Hz minimum, so this is 10–15x short even before the gaps are counted.
2. **The gaps outrun the activity.** A fall lasts ~1 s, a wave ~2 s, and the
   95th-percentile gap is ~1 s (it was 6 s on shorter reads of the same capture).
   Whole events land inside a gap and never appear. Nearly every CSI pipeline
   (STFT, CWT, sliding-window PCA) also assumes uniform sampling, and you cannot
   honestly interpolate across multi-second holes.
3. **Hopping breaks CSI continuity even if it were fast.** Channels 1/6/11 are
   different frequencies with different multipath responses, so the three
   streams are not one signal and cannot be concatenated. Each retune also
   resets LO phase, so CFO/sampling offset jump discontinuously at every hop and
   phase-derived features — usually the most informative ones — are unusable
   across hops. This is inherent to time-division hopping on a single radio.

### "Can't we just hop faster — say 50 ms instead of 100 ms?"

No. It makes things strictly worse, and the reason is measurable.

Retuning costs a **fixed** amount of time per hop — the USRP LO has to settle and
the OFDM receiver has to re-acquire sync. Measured over a 784 s hopping capture
(1012 rows): a productive 100 ms dwell delivered a mean of **1.8 packets**
against the ~5 that a 50 pkt/s transmitter should fit into it, and 56 % of
productive dwells yielded exactly one packet. That puts the fixed cost at
**roughly 60 ms of every 100 ms dwell**, on each side independently.

Because that cost is per *hop* rather than per second, halving the dwell doubles
the number of hops and therefore doubles the total overhead:

| `DWELL_TIME` | Settling cost | Productive window | Verdict |
|---|---|---|---|
| 50 ms | ~60 ms | **none — dwell is shorter than settling** | Nothing gets through |
| 100 ms (current) | ~60 ms | ~40 ms (40 %) | Measured 1.94 Hz |
| 500 ms | ~60 ms | ~440 ms (88 %) | Much better, still split 3 ways |
| Parked | none | 100 % | ~50 Hz — what HAR needs |

Also worth correcting a figure quoted earlier in this project's history: two
free-running hop loops share a channel about **⅓** of the time on average, not
⅑. Alignment was never the main problem — per-hop settling is. And note that
hopping the receiver does not improve alignment at all: a *parked* receiver also
sees a hopping transmitter exactly ⅓ of the time.

**If your teammate wants this settled empirically**, it takes ten minutes — see
§10.

**The fix: don't hop during an activity, hop between sessions.** Record the
full activity set parked on channel 1, then repeat it parked on channel 6, then
channel 11. You get three complete ~50 Hz datasets instead of one unusable
~2 Hz interleaved stream, and the three-channel comparison that motivates the
project survives intact. You lose only simultaneity, which HAR does not need.

---

## 1. Corrections already applied

These are done — listed so you know the state of the tree, not as work for you.

| File | Change |
|---|---|
| `receiver/gr-ieee802-11/lib/extract_csi_impl.cc` | Accept `address 2`/`address 1` (Data frames) as TA/RA, not just `ta`/`ra` (Control frames only). Without this **every frame was silently dropped** |
| `receiver/gr-ieee802-11/lib/extract_csi_impl.cc` | Flush the CSV per row instead of per 100 rows |
| `receiver/gr-ieee802-11/examples/wifi_rx.py` | Added the channel-hop loop, which did not exist despite `RECEIVER.md` claiming it did |
| `receiver/gr-ieee802-11/examples/wifi_rx.py` | `CSI_CHANNEL=1\|6\|11` parks the RX; unset = hop |
| `transmitter/.../wifi_tx_multi_hop.py` | `TX_CHANNEL=1\|6\|11` parks the TX; unset = hop |
| `transmitter/.../packet_generator.py` | `PPS` / `LABEL` / `PAYLOAD_SIZE` from environment, default **200 pps** (was 50) |
| `receiver/capture.sh` | New — records one labelled instance to its own CSV |

**Verified working:** the C++ fixes and the hop loop (`(MATCH)` lines appear,
rows reach the CSV, all three channels observed).
**Not yet run against hardware:** the parked-mode (`CSI_CHANNEL`/`TX_CHANNEL`)
paths and `capture.sh`. Stage 3 below is what proves them.

### Send the updated transmitter to your friend

```bash
cd ~/usrp-projects/Three_Channel_Experiment
zip -r transmitter.zip transmitter/
```

They replace their `transmitter/` folder with this one. **No rebuild needed on
their side** — only Python files changed.

---

## 2. Environment setup

Get this right once and never touch it again. CSI multipath is specific to the
room; a chair moved mid-dataset is a distribution shift your model will learn
instead of the activity.

- **One room for the entire dataset.** Pick it now.
- **TX and RX 3–5 m apart, line of sight**, antennas at ~1 m (torso height).
- **The subject moves between the antennas**, crossing the direct path — that
  is where a body perturbs the signal most.
- **Tape-mark on the floor**: both antenna positions, and the subject's start
  position. If an antenna shifts between sessions the channels are no longer
  comparable and the dataset is quietly ruined.
- **Nobody else moves in the room.** Door closed and kept closed. Other people's
  phones on the far side.
- Write down room, date, subject, antenna geometry and channel for every session.

---

## 3. Stage 1 — Pilot (do this before anything else, ~5 minutes)

The point is to fail cheaply. If walking and an empty room look identical here,
no quantity of data or choice of model will rescue it.

**TX laptop, Terminal A** (flowgraph, parked on channel 1):
```bash
cd ~/usrp-projects/Three_Channel_Experiment/transmitter/gr-ieee802-11/examples
export TX_CHANNEL=1
python3 wifi_tx_multi_hop.py
```
Expect one line, then no further hop output:
```
[HH:MM:SS.mmm] PARKED on Channel 1 (2412 MHz) — not hopping
```

**TX laptop, Terminal B** (traffic, 200 pkt/s):
```bash
cd ~/usrp-projects/Three_Channel_Experiment/transmitter/gr-ieee802-11/examples
export PPS=200
python3 packet_generator.py
```
Expect `Connected — sending 200 pkt/s, ...` then one line per second.

**RX laptop:**
```bash
cd ~/usrp-projects/Three_Channel_Experiment/receiver
export CSI_CHANNEL=1
./capture.sh pilot walk 01 20      # walk back and forth for 20 s
./capture.sh pilot empty 01 20     # start it, leave the room during the countdown
```

`capture.sh` prints the achieved rate and warns below 20 Hz. **You want ≳40 Hz.**
If it warns, stop and fix that before continuing — see Troubleshooting.

**Now look at the data.** This is the decision point of the whole project:

```bash
python3 - <<'EOF'
import numpy as np, pandas as pd
for name in ("walk", "empty"):
    df = pd.read_csv(f"/home/rishiikesh/usrp-projects/data/har/ch1/pilot_{name}_01.csv")
    re = df[[f"SC{i}_Re" for i in range(52)]].values
    im = df[[f"SC{i}_Im" for i in range(52)]].values
    amp = np.sqrt(re**2 + im**2)
    # Std-dev over time per subcarrier: motion makes the channel vary, an
    # empty room does not. Averaged across subcarriers it is a blunt but
    # honest separability check.
    print(f"{name:6s} rows={len(df):5d}  mean|H|={amp.mean():.4f}  "
          f"temporal-std={amp.std(axis=0).mean():.4f}")
EOF
```

**`walk` should show a clearly larger temporal-std than `empty`** — ideally
several times larger. If the two are within noise of each other, do not proceed
to Stage 2; the link geometry is wrong (antennas too close, subject not crossing
the path, or gain saturated).

---

## 4. Stage 2 — Single-subject dataset (~25 minutes)

Only after Stage 1 separates cleanly. One subject, five activities, 20 reps.

### The activities

Use exactly these names — **no underscores** (the filename is the label and
loaders split on `_`; `capture.sh` will reject them).

| Name | What the subject does | Why it's included |
|---|---|---|
| `empty` | Room empty, nobody inside | Baseline. Non-negotiable — proves the pipeline sees something vs nothing |
| `stand` | Stand still, mid-path | Static presence; separates "person present" from "person moving" |
| `walk` | Walk back and forth across the path | Strongest, easiest signal — your sanity-check class |
| `sitstand` | Sit down then stand up, repeatedly | Vertical torso motion, distinct from walking |
| `wave` | Stand still, wave one arm | Limb-only motion — hardest of the five, tests real sensitivity |

Add `fall` (onto a mattress) and `run`/`jump` only once these five classify
cleanly. **Skip breathing and heart-rate entirely** — those need phase stability
this setup does not have.

### Timing

- **10 s per instance**, activity performed continuously throughout.
- **20 reps per activity.**
- At 50 Hz a 10 s instance is ~500 packets, which windows comfortably into
  2 s / 50 %-overlap segments.

### Recording

TX side stays running from Stage 1 (both terminals, parked on channel 1).

```bash
cd ~/usrp-projects/Three_Channel_Experiment/receiver
export CSI_CHANNEL=1
SUBJ=rishi          # your name, no underscores

for a in walk sitstand wave stand; do
  echo "=== $a — 20 reps ==="
  for r in $(seq -w 1 20); do ./capture.sh $SUBJ $a $r; done
done

# empty: start this, then leave the room until it finishes (~5 min)
for r in $(seq -w 1 20); do ./capture.sh none empty $r; done
```

Each rep gives you ~6–8 s between recordings (flowgraph restart plus the 3 s
countdown) to reset position.

> **Randomize order when you scale up.** Recording all 20 walks then all 20
> waves lets a model learn clock-time drift instead of the activity. For a
> single-subject pilot the blocked order above is acceptable; for the full
> dataset in Stage 4, shuffle.

### Verify before trusting it

```bash
cd ~/usrp-projects/data/har/ch1

# Per-class instance counts — expect 20 each
ls *.csv | sed 's/_[0-9]*\.csv$//' | sort | uniq -c

# Rows per file: at 10 s and ~50 Hz expect ~500. Anything under 200 is suspect.
for f in *.csv; do echo "$(( $(wc -l < "$f") - 1 ))  $f"; done | sort -n | head -10
```

The second command is the important one — it surfaces instances where the link
dropped out mid-recording. **Delete and re-record any file with under 200 rows**
rather than leaving it to poison training.

---

## 5. Stage 3 — Does it actually classify?

Before recording more subjects or channels, confirm the data supports the task.

```bash
python3 - <<'EOF'
import glob, os
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

X, y = [], []
for p in sorted(glob.glob(os.path.expanduser("~/usrp-projects/data/har/ch1/*.csv"))):
    subject, activity, rep = os.path.basename(p)[:-4].split("_")
    if subject == "pilot":
        continue
    df = pd.read_csv(p)
    if len(df) < 200:
        continue
    re = df[[f"SC{i}_Re" for i in range(52)]].values
    im = df[[f"SC{i}_Im" for i in range(52)]].values
    amp = np.sqrt(re**2 + im**2)
    # Simple per-subcarrier statistics. Deliberately crude: if this separates
    # the classes at all, richer features will do better. If it cannot, the
    # problem is the data, not the model.
    X.append(np.concatenate([amp.mean(0), amp.std(0),
                             np.percentile(amp, 90, axis=0) - np.percentile(amp, 10, axis=0)]))
    y.append(activity)

X, y = np.array(X), np.array(y)
print(f"{len(X)} instances, {len(set(y))} classes: {sorted(set(y))}")
scores = cross_val_score(RandomForestClassifier(n_estimators=300, random_state=0), X, y, cv=5)
print(f"5-fold accuracy: {scores.mean():.3f} +/- {scores.std():.3f}  (chance = {1/len(set(y)):.3f})")
EOF
```

Interpreting the number, for 5 classes (chance = 0.20):

- **> 0.80** — solid. Scale up to more subjects and the other channels.
- **0.50–0.80** — real signal, needs better features (spectrograms, PCA
  denoising) or more data. Proceed, but expect work.
- **< 0.40** — the data does not support the task. Do not add more of it. Revisit
  antenna geometry and re-run Stage 1.

Needs scikit-learn: `pip install scikit-learn` (or `sudo dnf install python3-scikit-learn`).

---

## 6. Stage 4 — Full dataset

Only once Stage 3 clears 0.80.

- **3–5 subjects** of differing height and build. Models trained on one person
  rarely transfer, and this is the single biggest gap in most student CSI
  datasets.
- Same five activities, 20 reps each, 10 s each.
- **Shuffle activity order** within each session.
- 5 classes × 20 reps × 4 subjects = **400 instances ≈ 100 minutes** per channel
  including overhead. Split it across sittings — but never move the antennas
  between them.

### Then the three-channel comparison

Repeat the entire Stage 4 set on channel 6, then channel 11. **Do not move the
antennas** — the whole point is that only the frequency changes.

```bash
# RX
export CSI_CHANNEL=6      # then 11

# TX (both terminals restarted)
export TX_CHANNEL=6       # then 11
```

Output lands in `~/usrp-projects/data/har/ch6/` and `ch11/` automatically. Now
you can honestly answer the project's actual question: does channel diversity
improve activity recognition, and by how much? That comparison is only valid
because each channel was recorded at full rate rather than time-sliced.

---

## 7. Loading the dataset later

```python
import glob, os
import numpy as np, pandas as pd

def load(channel=1, root="~/usrp-projects/data/har", min_rows=200):
    """Yield (amplitude[T,52], activity, subject, rep) per instance."""
    for p in sorted(glob.glob(os.path.expanduser(f"{root}/ch{channel}/*.csv"))):
        subject, activity, rep = os.path.basename(p)[:-4].split("_")
        df = pd.read_csv(p)
        if len(df) < min_rows:
            continue
        re = df[[f"SC{i}_Re" for i in range(52)]].values
        im = df[[f"SC{i}_Im" for i in range(52)]].values
        yield np.sqrt(re**2 + im**2), activity, subject, rep
```

CSV columns are `Packet, Timestamp_us, Channel, SC0_Re, SC0_Im, … SC51_Re,
SC51_Im`. `Timestamp_us` is epoch microseconds — use it to check for gaps, since
sampling is not perfectly uniform even when parked.

Note that `LABEL` in `packet_generator.py` is embedded in the packet payload but
**not** extracted into the CSV. The filename is the only source of truth for the
label.

---

## 8. Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `capture.sh` warns "under 20 Hz" | `TX_CHANNEL` and `CSI_CHANNEL` disagree, `packet_generator.py` isn't running, or `PPS` is still 50. Check the TX prints `PARKED on Channel N` for the **same** N as the RX |
| RX prints `Hopped to Channel ...` repeatedly | `CSI_CHANNEL` isn't set in *that* shell. `export` does not cross terminal tabs |
| No `(MATCH)` line, CSV header-only | See `receiver/RECEIVER.md` troubleshooting — most likely an old `.so` without the Data-frame TA/RA fallback; rebuild and `sudo make install` |
| `refusing to overwrite existing ...` | That instance already exists. Delete it deliberately if you meant to re-record |
| Rate good but `walk` ≈ `empty` in Stage 1 | Geometry. Antennas too close together, subject not crossing the line of sight, or RX gain saturated |
| Rates differ a lot between channels | Expected to a degree — 2.4 GHz interference differs per channel. If one channel is badly worse, note it rather than discarding; it is a finding |

---

## 9. Honest caveats

- The rate and gap figures in §0 are measured from your files. The **20–30 Hz
  minimum and the 10 s / 20 rep figures are typical values from the CSI-HAR
  literature, not measured on your hardware** — treat them as starting points,
  and let Stage 1 and Stage 3 tell you the truth for this rig.
- Parked mode and `capture.sh` are syntax-checked but have not yet run against
  the USRPs. Stage 1 is deliberately short so a problem there costs minutes.
- 2.4 GHz channels 1/6/11 are exactly where ambient WiFi lives. If a channel is
  congested your FER will rise. `uhd_fft --args="addr=192.168.10.7" -f 2.412e9 -s 20e6`
  shows what else is on the air before you commit to a session.

---

## 10. Settling the dwell-time question empirically

If there's disagreement about hop timing, measure it rather than argue. Ten
minutes gives you a curve instead of two opinions.

`DWELL_TIME` must match on both sides, so this needs coordinating with whoever
runs the TX. For each value in 0.05, 0.1, 0.5, 1.0:

1. Edit `DWELL_TIME` in **both** `receiver/gr-ieee802-11/examples/wifi_rx.py`
   and `transmitter/gr-ieee802-11/examples/wifi_tx_multi_hop.py`.
2. Leave `CSI_CHANNEL` / `TX_CHANNEL` **unset** so both sides hop.
3. Run for 120 s:

```bash
# RX — note this is plain wifi_rx.py, NOT capture.sh (capture.sh parks)
export CSI_TA=02:00:00:00:00:01
export CSI_RA=02:00:00:00:00:02
export CSI_OUT=~/usrp-projects/data/dwell_test_$(python3 -c "print('%03d'%(DWELL*1000))" 2>/dev/null || echo manual).csv
cd ~/usrp-projects/Three_Channel_Experiment/receiver/gr-ieee802-11/examples
timeout -s INT 120 python3 wifi_rx.py
```

Simplest is to name the files by hand — `dwell_050.csv`, `dwell_100.csv`,
`dwell_500.csv`, `dwell_1000.csv` — then compare:

```bash
cd ~/usrp-projects/data
python3 - <<'EOF'
import csv, glob, statistics
for p in sorted(glob.glob('dwell_*.csv')):
    ts = []
    with open(p) as f:
        r = csv.reader(f); h = next(r); ti = h.index('Timestamp_us')
        for row in r:
            if len(row) > ti: ts.append(int(row[ti]))
    if len(ts) < 2:
        print(f"{p:20s} {len(ts):5d} rows — nothing to measure"); continue
    span = (ts[-1] - ts[0]) / 1e6
    gaps = [(b-a)/1000 for a, b in zip(ts, ts[1:])]
    print(f"{p:20s} {len(ts):5d} rows  {len(ts)/span:6.2f} Hz  median gap {statistics.median(gaps):7.0f} ms")
EOF
```

**Predicted result**, so it's falsifiable rather than hand-waved: 50 ms comes
out at or near zero rows, 100 ms near the 1.94 Hz already measured, and the rate
climbs monotonically with dwell. If 50 ms instead beats 100 ms, the settling
model in §0 is wrong and this document should be revised.

Either way, **no hopping configuration reaches the ~50 Hz that activity
recognition needs** — that requires parking both radios. This experiment settles
which dwell is best *for hopping*, not whether hopping can do HAR.
