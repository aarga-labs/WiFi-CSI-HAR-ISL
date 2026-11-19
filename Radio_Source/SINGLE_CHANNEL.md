# Single-Channel Operation (No Hopping, No Clock Sync)

This is the quick reference for running the transmitter and receiver **parked
on one fixed WiFi channel**, with no hopping and no wall-clock synchronization
between the two laptops. Both flowgraphs already support this mode — it is
not a code change, just the right environment variables.

- **[TX]** — transmitter laptop (USRP at `192.168.10.7`)
- **[RX]** — receiver laptop (USRP at `192.168.10.9`)

Pick one channel for the whole session — **1**, **6**, or **11** — and use it
everywhere below. This doc uses **6** as the example; substitute yours.

---

## Why this needs no synchronization

`wifi_tx_multi_hop.py` and `wifi_rx.py` both contain a wall-clock-synced
hopping mode (1 → 6 → 11 every 0.5 s), which is what needs NTP-synced clocks
between the two laptops. That code path only runs when `TX_CHANNEL` /
`CSI_CHANNEL` is **unset**. Setting them:

- tunes the USRP to the fixed frequency once, at startup
- skips the hopping thread entirely (it checks the channel and returns
  immediately)
- requires no coordination between the laptops beyond both naming the same
  channel number

If either script ever prints a `Synced hop ->` / `HOPPING` line, the env var
wasn't set in *that* terminal — `export` does not carry across terminal tabs.

---

## [TX] Transmitter — two terminals

**Terminal A — flowgraph:**
```bash
cd transmitter/gr-ieee802-11/examples
export TX_CHANNEL=6        # MUST match CSI_CHANNEL on the RX
export TX_GAIN=30          # keep FIXED for the entire dataset
python3 wifi_tx_multi_hop.py
```

Expect a banner then exactly one channel line, with no further hop lines:
```
   mode         : PARKED on channel 6 (2437 MHz)
[HH:MM:SS.mmm] PARKED on Channel 6 (2437 MHz) — not hopping
```

**Terminal B — traffic generator, started after Terminal A is up:**
```bash
cd transmitter/gr-ieee802-11/examples
export PPS=300              # packets/sec, ceiling on the CSI rate at the RX
python3 packet_generator.py
```

Expect `Connected — sending 300 pkt/s, 100-byte payload, LABEL=...`. Leave
both terminals running for the whole session — do not restart them between
captures.

---

## [RX] Receiver

### Option A — single capture (`capture.sh`)

```bash
cd receiver
export CSI_CHANNEL=6        # MUST match TX_CHANNEL
export RX_GAIN=50           # main lever for weak signals/gestures
./capture.sh <subject> <class> <rep> [seconds]

# e.g.
./capture.sh rishi walk 01 10
```

`capture.sh` already hard-requires `CSI_CHANNEL` and starts `wifi_rx.py`
parked on it internally — nothing else to set for hopping. Output goes to
`~/usrp-projects/data/har/ch6/<subject>_<class>_<rep>.csv` plus a `.json`
sidecar.

### Option B — a full labelled session (`session.sh`)

```bash
cd receiver
export CSI_CHANNEL=6
export RX_GAIN=50
export ROOM="LabA"          # optional, recorded into every sidecar

CLASSES="walk sitstand bend standstill hello comehere stop thankyou" \
  ./session.sh <subject> 20 10
```

Randomised order, resumable, pauses for a break every 30 instances (see
`BREAK_EVERY`). Record `empty` separately, as its own block:
```bash
CLASSES="empty" ./session.sh none 20 10
```

### Option C — run the raw flowgraph directly (quick link check, no CSV)

```bash
cd receiver/gr-ieee802-11/examples
export CSI_CHANNEL=6
python3 wifi_rx.py
```

Expect `PARKED on channel 6 (2437 MHz)` in the console, with no `Synced hop
->` lines afterward.

---

## Verify a capture is real single-channel data

```bash
python3 receiver/qc.py <path-to-csv> --expect-channel 6
```

Fails loudly if any row is labelled a different channel (RX wasn't actually
parked) or if the row rate is too low to be usable.

---

## Environment variable reference

| Variable | Side | Default | Purpose |
|---|---|---|---|
| `TX_CHANNEL` | TX | *(hop if unset)* | parked channel — 1, 6, or 11 |
| `TX_GAIN` | TX | 30 | transmit gain dB — keep fixed for a dataset |
| `TX_ADDR` | TX | 192.168.10.7 | transmitter USRP address |
| `PPS` | TX | 300 | packets/sec from `packet_generator.py` |
| `CSI_CHANNEL` | RX | *(required — hop if unset)* | parked channel — must match `TX_CHANNEL` |
| `RX_GAIN` | RX | 50 | receiver gain dB |
| `RX_ADDR` | RX | 192.168.10.9 | receiver USRP address |
| `MIN_RATE` | RX | 40 | Hz below which `capture.sh` rejects the instance |
| `LINKUP_TIMEOUT` | RX | 30 | seconds `capture.sh` waits for the link before giving up |
| `ROOM`, `NOTES` | RX | *(empty)* | free text recorded into the `.json` sidecar |
| `CLASSES` | RX | 9 classes | which classes `session.sh` records |
| `SEED` | RX | random | reproduce a specific randomised order |
| `BREAK_EVERY` | RX | 30 | instances between breaks in `session.sh` |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| TX/RX console prints `HOPPING 1/6/11` or `Synced hop ->` | `TX_CHANNEL`/`CSI_CHANNEL` not set in *this* terminal |
| `set CSI_CHANNEL to 1, 6 or 11 first` (capture.sh/session.sh abort) | Export `CSI_CHANNEL` before running the script |
| `TX_CHANNEL must be one of [1, 6, 11]` | Typo in the value — it aborts rather than silently hopping |
| `No CSI after 30s` | `packet_generator.py` not running, or `TX_CHANNEL` ≠ `CSI_CHANNEL` |
| `rows labelled channel [...] but expected N` (qc.py) | RX was not actually parked — check `CSI_CHANNEL` in that terminal |
| `rate ... below the 40 Hz minimum` | Raise `PPS` on TX, raise `RX_GAIN`, or check for interference on this channel |

---

For the full pipeline (fresh-machine setup, build, channel scan, pilot
go/no-go, analysis), see [RUNBOOK.md](RUNBOOK.md), which already runs
entirely in this single-channel mode by default.
