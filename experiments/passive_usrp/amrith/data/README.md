# CSI Data Format

## Privacy

Subjects are anonymised as `S01`, `S02`, `S03`. No mapping to real identities is
published in this repository. The captures contain PHY-layer channel estimates
only — no MAC addresses, no payload, no decrypted traffic.

## Layout

```
data/pilot/
├── P01_<class>_<subject>_<date>_<take>.csv        raw CSI captures  (committed)
├── P01_<class>_<subject>_<date>_<take>_check.png  quality plot      (committed)
└── windows/                                       generated, NOT committed
    ├── action/*.npy                               segmented model inputs
    └── noaction/*.npy
```

Only the raw captures are version-controlled. `windows/` is derived output and
is gitignored — regenerate it after cloning with the command below.

### Filename fields

| Field | Values | Meaning |
|---|---|---|
| `P01` | `P01` | pilot collection round |
| `class` | `action`, `noaction` | label — person moving vs. present but still |
| `subject` | `S01`, `S02`, `S03` | anonymised participant |
| `date` | `YYYYMMDD` | capture date |
| `take` | `walk`, `mixed` (action)<br>`sit`, `stand` (noaction) | what the person was doing |

`mixed` takes contain a sequence of smaller motions (squat, side-step, bend,
drink) rather than a single sustained one.

## Raw capture CSV

One row per successfully decoded 802.11 frame, written by the `WiFi Extract
CSI` block in the GNU Radio flowgraph.

| Column | Type | Description |
|---|---|---|
| `Timestamp_us` | int64 | capture timestamp in microseconds |
| `SC0_Re` … `SC51_Re` | float | real part of the channel estimate, per subcarrier |
| `SC0_Im` … `SC51_Im` | float | imaginary part of the channel estimate, per subcarrier |

105 columns total. The 52 subcarriers are the usable data + pilot subcarriers of
802.11a/g OFDM at 20 MHz (64 slots minus DC and guard bands).

The sensing signal is the amplitude:

```
|H_k| = sqrt(SCk_Re^2 + SCk_Im^2)
```

Phase is deliberately unused — see the Model section of the top-level README.

### Two things to know when loading

1. **The last row of every capture is truncated.** The flowgraph is stopped
   mid-write, leaving an incomplete final line. Drop rows with NaNs in any
   subcarrier or timestamp column.
2. **Packets arrive irregularly.** The link is sniffed passively, so the rate is
   whatever the transmitter happens to emit and `gr-ieee802-11` can decode
   (legacy OFDM only; 802.11n HT frames are dropped). Measured rates in this set
   range roughly 50–80 Hz. Derive duration and rate from `Timestamp_us`, never
   from row counts.

## Segmented windows

`scripts/segment_windows.py` converts each capture into 2-second windows:

1. compute amplitude `|H|` per packet;
2. resample a 2 s span onto a uniform time grid by linear interpolation using
   the real timestamps, producing exactly `52 x 200`;
3. skip the window if fewer than 50% of the expected packets are present.

Step 2 matters: because packets arrive irregularly, slicing by *packet count*
would produce windows of inconsistent physical duration. Interpolating onto a
time grid makes every window exactly 2 s of wall-clock time.

Each `.npy` file is a float32 array of shape `(52, 200)` — subcarriers × time
steps — stored under its class directory, named
`<capture_stem>_<class>_<subject>_rep<NNN>.npy`.

### Regenerating

```bash
for f in data/pilot/P01_*.csv; do
  b=$(basename "$f" .csv)
  python3 scripts/segment_windows.py "$f" \
      --action  "$(echo "$b" | cut -d_ -f2)" \
      --subject "$(echo "$b" | cut -d_ -f3)" \
      --out-dir data/pilot/windows
done
```

Expected result — 496 windows:

| Subject | action | noaction | total |
|---|---|---|---|
| S01 | 92 | 90 | 182 |
| S02 | 86 | 88 | 174 |
| S03 | 76 | 64 | 140 |
| **All** | **254** | **242** | **496** |

Some windows are skipped where the packet rate dips below the 50% fill
threshold; this is expected and reported per capture.

**Do not change `--rate` or `--window`.** Output width is `rate x window`, and
the model expects 200 time steps. The defaults produce that.

## Quality-check plots

Each `*_check.png` is a per-capture sanity plot produced at collection time,
used to confirm the capture is usable before segmenting it.
