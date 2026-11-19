# Data Capture Runbook — Activity vs Gesture

Commands in execution order. Every block is labelled with the laptop it runs on:

- **[TX]** — transmitter laptop (USRP at `192.168.10.7`)
- **[RX]** — receiver laptop (USRP at `192.168.10.9`)

Set this once per terminal on each machine, adjusting to where your copy lives:

```bash
export REPO=~/usrp-projects/Three_Channel_Experiment    # your path to this repo
```

> Rule for the whole session: **`export` does not cross terminal tabs.** Every
> new terminal needs its own `export` block. Most "it stopped working" reports
> are this.

---

## Phase 0 — Fresh-machine setup (skip if `gnuradio-companion` already opens)

Do this on **both** laptops if they are new. It installs GNU Radio, UHD, and
the toolchain needed to build this project's two custom OOT modules
(`gr-ieee802-11` — the patched CSI extractor — and `gr-foo`, TX-side only).
A generic UHD/GNU Radio guide (Ettus's own included) stops short of this: it
gets you `gnuradio-companion` opening, but `cmake ..` in Phase 1 will fail
without the `-dev` packages below, because those don't ship in the plain
`gnuradio` package.

Written for **Ubuntu 22.04/24.04**. Check what you actually have first:
```bash
lsb_release -ds
```
If it says something else (Fedora is the other OS this project's docs
support), the package manager and names differ — ask before improvising, or
see `transmitter/TRANSMITTER.md` Part 0.

### [TX] and [RX] — both laptops

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  gnuradio gnuradio-dev \
  libuhd-dev uhd-host \
  cmake build-essential git pkg-config \
  libboost-all-dev pybind11-dev python3-dev \
  python3-pyqt5 python3-pyqt5.qtsvg \
  python3-mako python3-click python3-click-plugins \
  python3-pip

sudo uhd_images_downloader
```

What each group is for, since it's easy to cut corners on a list this long:

| Packages | Needed for |
|---|---|
| `gnuradio`, `gnuradio-dev` | the runtime **and** the headers — `gnuradio-dev` is the one a generic guide skips, and its absence is why `cmake ..` fails with "Gnuradio not found" |
| `libuhd-dev`, `uhd-host` | UHD driver + `uhd_find_devices` / `uhd_usrp_probe` / `uhd_fft` |
| `cmake`, `build-essential`, `git`, `pkg-config` | building `gr-ieee802-11` and `gr-foo` from source |
| `libboost-all-dev` | `extract_csi_impl.cc` uses `boost::bind` directly — confirmed in the source, not a guess |
| `pybind11-dev`, `python3-dev` | this OOT module generates its Python bindings via pybind11 at build time (see `gr-ieee802-11/python/CMakeLists.txt`) |
| `python3-pyqt5*` | both flowgraphs are Qt GUI apps (`Qt.QApplication`, `qtgui.*` sinks) |
| `python3-mako`, `python3-click*` | needed by `grcc` to regenerate `wifi_phy_hier.grc` (`TRANSMITTER.md` Part 4) |
| `sudo uhd_images_downloader` | N210 FPGA/firmware images — UHD will refuse to talk to the USRP without these |

Verify before going further:
```bash
uhd_config_info --version          # some UHD versions call this uhd_config_info, not --version alone
gnuradio-config-info --version     # want 3.10.x — this project targets 3.10, not 3.11+
python3 -c "from gnuradio import qtgui, uhd; print('gnuradio+uhd+qtgui OK')"
python3 -c "import PyQt5; print('PyQt5 OK')"
```

If `gnuradio-config-info --version` reports 3.11 or newer: this project's
`CMakeLists.txt` only requires `Gnuradio "3.9"` as a floor, so it may well
build, but it hasn't been verified against anything past 3.10.x. Build it
(Phase 1) and run `./preflight.sh` before assuming it's fine.

### [RX only] — analysis-side Python packages

Only needed on whichever machine runs `analysis/`. Doesn't have to be the RX
laptop — copy `~/usrp-projects/data/` to any machine with Python.

```bash
pip3 install --user numpy scikit-learn pandas
# optional, only for `train.py --model cnn`:
pip3 install --user torch --index-url https://download.pytorch.org/whl/cpu
```

`dataset.py` and `train.py` work with just `numpy` + `scikit-learn`; `pandas`
makes the CSV loader faster but isn't required (there's a stdlib fallback).

### USRP network cabling (both laptops, direct cable, no switch)

**This project's addresses are `192.168.10.7` (TX) and `192.168.10.9` (RX) —
not the `192.168.10.2` used as a generic example in most UHD tutorials.**
If you followed a guide that flashed the N210 to `.2`, re-flash its EEPROM to
match, or override `TX_ADDR`/`RX_ADDR` later rather than editing the
flowgraphs. Also prefer `ip addr add` over `ifconfig` below — `ifconfig` comes
from `net-tools`, which Ubuntu no longer installs by default, and the address
it sets does not survive a reboot either way (that's `netplan`'s job, out of
scope here — just re-run this after every reboot).

```bash
ip link                                       # find your USRP-facing interface, e.g. enp2s0
sudo ip addr add 192.168.10.1/24 dev <iface>  # same /24 on BOTH laptops — fine, separate physical links
sudo ip link set <iface> up
```

Then, **per role**:
```bash
# [TX] laptop
ping -c 3 192.168.10.7
uhd_find_devices                              # expect addr=192.168.10.7

# [RX] laptop
ping -c 3 192.168.10.9
uhd_find_devices                              # expect addr=192.168.10.9
```

If `uhd_find_devices` finds nothing: check the cable, re-check `ip addr show
<iface>` reports the `192.168.10.1/24` you just set, and disable the firewall
rather than opening ports (`sudo ufw disable`, USRP discovery uses broadcast
which most default firewalls block).

Optional deeper checks (not required, but useful once if this is new
hardware to you):
```bash
uhd_usrp_probe --args="addr=192.168.10.9"      # full device tree — confirms daughterboard, clock, etc.
benchmark_rate --args="addr=192.168.10.9" --rx_rate 1e6   # RX-side raw throughput sanity check
benchmark_rate --args="addr=192.168.10.7" --tx_rate 1e6   # TX-side raw throughput sanity check
```

---

## Phase 1 — Build (once per machine)

### [RX] Rebuild the CSI block — REQUIRED

`lib/extract_csi_impl.cc` changed, and the flowgraph loads the **installed**
`.so`, not the one in your build tree.

```bash
cd $REPO/receiver/gr-ieee802-11
mkdir -p build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Verify:
```bash
python3 -c "import ieee802_11; print(hasattr(ieee802_11.extract_csi,'set_channel'))"
# expect: True
```

### [TX] No rebuild needed

Only Python files changed on the transmitter side. If `gr-foo` and
`gr-ieee802-11` are already built there, just copy the updated folder over:

```bash
# on the RX laptop
cd $REPO && zip -r transmitter.zip transmitter/
# then send transmitter.zip to the TX laptop and unzip it in place
```

If the TX laptop is fresh, follow `transmitter/TRANSMITTER.md` Parts 2–4 first
(build `gr-foo`, build `gr-ieee802-11`, generate `wifi_phy_hier`).

---

## Phase 2 — Preflight and channel choice

### [RX] Check the receiver

```bash
cd $REPO/receiver
./preflight.sh
```

Expect `0 failures`. If it reports the USRP is not at `192.168.10.9`, it prints
the address that answered — use it:

```bash
export RX_ADDR=<address it printed>
```

### [RX] Pick the quietest channel

2.4 GHz channels 1/6/11 are exactly where ambient WiFi lives. Look at each for
~15 seconds and pick the emptiest:

```bash
uhd_fft --args="addr=192.168.10.9" -f 2.412e9 -s 20e6   # channel 1
uhd_fft --args="addr=192.168.10.9" -f 2.437e9 -s 20e6   # channel 6
uhd_fft --args="addr=192.168.10.9" -f 2.462e9 -s 20e6   # channel 11
```

**Write down which you chose.** Both laptops use it for the whole dataset.
The rest of this runbook assumes channel **1** — substitute yours everywhere.

---

## Phase 3 — Start the transmitter (leave running all day)

### [TX] Terminal A — flowgraph

```bash
cd $REPO/transmitter/gr-ieee802-11/examples
export TX_CHANNEL=1        # MUST match CSI_CHANNEL on the RX
export TX_GAIN=30          # keep FIXED for the entire dataset
python3 wifi_tx_multi_hop.py
```

Expect a banner then exactly one channel line:
```
   mode         : PARKED on channel 1 (2412 MHz)
[HH:MM:SS.mmm] PARKED on Channel 1 (2412 MHz) — not hopping
```

> If you see repeating `Synced hop ->` lines, `TX_CHANNEL` is not set in *this*
> terminal. Stop and fix it — hopping gives ~2.4 Hz and the data is unusable.

### [TX] Terminal B — traffic

```bash
cd $REPO/transmitter/gr-ieee802-11/examples
export PPS=300
python3 packet_generator.py
```

Expect `Connected — sending 300 pkt/s, 100-byte payload, LABEL=walking`.

Leave both terminals running. Do not restart them between instances.

---

## Phase 4 — Pilot and the go/no-go decision

Do not skip this. It costs 5 minutes and it is the point where the project
either works or needs the geometry changed.

### [RX] Set up the capture terminal

```bash
cd $REPO/receiver
export CSI_CHANNEL=1       # MUST match TX_CHANNEL
export RX_GAIN=50
export ROOM="LabA"
```

### [RX] Record four pilot instances

```bash
./capture.sh pilot walk 01 20        # walk back and forth across the link
./capture.sh pilot hello 01 20       # stand still, wave one hand in the path
./capture.sh pilot standstill 01 20  # stand still, hands down
./capture.sh pilot empty 01 20       # start it, then LEAVE THE ROOM
```

Each must end with a green `OK` line showing **≥40 Hz** and **100% usable
windows**. If one fails, the message says why — fix that before continuing.

### [RX] The decision

```bash
cd $REPO/analysis
python3 pilot_check.py --channel 1 --subject pilot
```

| Verdict | What to do |
|---|---|
| **GO** | Proceed to Phase 5 |
| **PARTIAL** | Hands not visible. Raise `RX_GAIN` to 55, shorten TX–RX to ~2 m, make sure the hand crosses the direct path. Re-record `hello`/`standstill` and re-run |
| **NO-GO** | Link not seeing motion at all. Re-run `preflight.sh`, check antenna orientation and that the subject crosses the direct path |

To re-record after a change, delete the old instance first:
```bash
rm ~/usrp-projects/data/har/ch1/pilot_hello_01.*
RX_GAIN=55 ./capture.sh pilot hello 01 20
```

---

## Phase 5 — Full session

Geometry is now frozen. **Do not move the antennas again** — not between
subjects, not between days.

### [RX] The eight person-present classes, randomised

```bash
cd $REPO/receiver
export CSI_CHANNEL=1
export RX_GAIN=50          # whatever the pilot settled on
export ROOM="LabA"

CLASSES="walk sitstand bend standstill hello comehere stop thankyou" \
  ./session.sh rishi 20 10
```

~160 instances, roughly 50 minutes including overhead. It prints a checklist
and waits for Enter, pauses for a break every 30 instances, and is **safe to
re-run** — already-recorded instances are skipped, so an interrupted session
resumes where it stopped.

### [RX] Then the empty-room baseline, as one block

Recorded separately on purpose: in randomised order you would be walking in and
out of the room 20 times, and there is only ~8 s between instances.

```bash
CLASSES="empty" ./session.sh none 20 10
```

Start it, leave the room, come back in ~6 minutes.

### [RX] Repeat for each subject

```bash
CLASSES="walk sitstand bend standstill hello comehere stop thankyou" \
  ./session.sh amrith 20 10
```

`empty` only needs recording once per room, not per subject.

---

## Phase 6 — Verify before trusting it

```bash
cd ~/usrp-projects/data/har/ch1

# per-class counts — expect 20 each
ls *.csv | sed 's/_[0-9]*\.csv$//' | sort | uniq -c

# smallest files first — anything unusually short is suspect
for f in *.csv; do echo "$(( $(wc -l < "$f") - 1 ))  $f"; done | sort -n | head

# re-check any individual instance
python3 $REPO/receiver/qc.py rishi_hello_07.csv --expect-channel 1
```

Delete and re-record anything that fails rather than leaving it to poison
training:
```bash
rm ~/usrp-projects/data/har/ch1/rishi_hello_07.*
cd $REPO/receiver && CSI_CHANNEL=1 ./capture.sh rishi hello 07 10
```

---

## Phase 7 — Analysis

```bash
cd $REPO/analysis

# structural report: counts, balance, subjects, warnings
python3 dataset.py --channel 1

# train + evaluate (RandomForest baseline)
python3 train.py --channel 1 --out results/ch1_rf.json

# deep model, if torch is installed
python3 train.py --channel 1 --model cnn --out results/ch1_cnn.json
```

Read the report in this order:

1. **shuffled-label control** — must be at chance. If it is not, there is
   leakage and nothing else in the report means anything.
2. **LOSO** — the headline number, accuracy on an unseen person.
3. **standstill vs gesture** — whether hand motion is genuinely detected.
4. **per-fine-class recall** — which classes carry the errors.

Needs `numpy` and `scikit-learn`:
```bash
pip install numpy scikit-learn        # add torch only for --model cnn
```

---

## Phase 8 (optional) — Other channels

Only after channel 1 is complete and analysed. **Do not move the antennas.**

```bash
# [TX] restart BOTH terminals with:
export TX_CHANNEL=6

# [RX]
export CSI_CHANNEL=6
CLASSES="walk sitstand bend standstill hello comehere stop thankyou" \
  ./session.sh rishi 20 10
CLASSES="empty" ./session.sh none 20 10
```

Output lands in `~/usrp-projects/data/har/ch6/` automatically. Then
`python3 train.py --channel 6` and compare.

---

## Quick reference

### Environment variables

| Variable | Side | Default | Purpose |
|---|---|---|---|
| `CSI_CHANNEL` | RX | *(required)* | parked channel, 1/6/11 |
| `RX_GAIN` | RX | 50 | receiver gain dB — main lever for weak gestures |
| `RX_ADDR` | RX | 192.168.10.9 | receiver USRP |
| `ROOM` | RX | unspecified | recorded into every `.json` sidecar |
| `NOTES` | RX | *(empty)* | free text into the sidecar |
| `MIN_RATE` | RX | 40 | Hz below which an instance is rejected |
| `LINKUP_TIMEOUT` | RX | 30 | seconds to wait for the link |
| `CLASSES` | RX | 9 classes | which classes `session.sh` records |
| `SEED` | RX | random | reproduce a specific randomised order |
| `BREAK_EVERY` | RX | 30 | instances between breaks |
| `TX_CHANNEL` | TX | *(hop)* | parked channel — must match `CSI_CHANNEL` |
| `TX_GAIN` | TX | 30 | transmit gain dB — keep fixed |
| `TX_ADDR` | TX | 192.168.10.7 | transmitter USRP |
| `PPS` | TX | 300 | packets/sec — ceiling on the CSI rate |

### Class names (no underscores — the filename is the label)

```
activity : walk  sitstand  bend  standstill
gesture  : hello  comehere  stop  thankyou
control  : empty
```

### Troubleshooting

| Symptom | Fix |
|---|---|
| `No CSI after 30s` | `packet_generator.py` not running, or `TX_CHANNEL` ≠ `CSI_CHANNEL`. Check the TX console says `PARKED on Channel <N>` for the same N |
| `The receiver exited during startup` | Wrong `RX_ADDR`, or the block is not installed. Run `./preflight.sh` |
| `rate ... below the 40 Hz minimum` | Raise `PPS` on TX, raise `RX_GAIN`, or check for interference on this channel |
| `largest gap ... link dropped` | Something moved or interference spiked. Re-record the instance |
| `rows labelled channel [...] but expected N` | RX is not actually parked — `CSI_CHANNEL` missing from *this* terminal |
| `refusing to overwrite` | That instance exists. `rm` the `.csv` and `.json`, then re-record |
| RX prints `Synced hop ->` | `CSI_CHANNEL` not set in this terminal |
| `CSI_CHANNEL must be one of [1, 6, 11]` | Typo — it aborts rather than silently hopping |

### Time budget

| Step | Time |
|---|---|
| Fresh-machine setup (once ever, per laptop) | 20-40 min, mostly `apt` downloading |
| Build + preflight | 20 min |
| Channel scan | 10 min |
| Pilot + go/no-go | 15 min |
| One subject, 8 classes × 20 reps × 10 s | ~50 min |
| `empty`, 20 reps (once per room) | ~6 min |
| Analysis run | 2 min |
