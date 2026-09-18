# Two-USRP WiFi CSI capture (TX + RX)

Active WiFi sensing setup for the FYP *Multimodal Human Activity and Sign Language Recognition for Inclusive Smart Homes* (Amrita Vishwa Vidyapeetham).

One Ettus USRP N210 (SBX) transmits IEEE 802.11 frames and a second one receives them. The receiver laptop decodes every frame in GNU Radio and writes its 52-subcarrier channel estimate (CSI) to a CSV.

## Layout

```
wifi_csi_capture/
├── receiver/                 USRP N210 #2, 192.168.10.7
│   ├── gr-ieee802-11/        modified module with the extract_csi block
│   │   └── examples/wifi_rx.py   receiver flowgraph (fixed to channel 1)
│   └── gain_sweep.sh         finds the best RX_GAIN for the room
├── transmitter/              USRP N210 #1, 192.168.10.9
│   ├── gr-ieee802-11/        upstream module + wifi_tx_multi_hop.py, packet_generator.py
│   └── gr-foo/               helper module (packet padding)
├── pilot_tools/              Phase-1 recording: protocol.py (classes, intents, scripts), cue_session.py,
│                             record_part.sh (one command per part), plot_pilot.py, site_check.py
├── qa/                       per-take CSI quality check and motion check on recorded data
├── docs/                     FULL_CONTEXT_2026-10-07.md = complete project handover
├── receiver_cmds.txt         every receiver command: install, build, run, troubleshoot
├── transmitter_cmds.txt      every transmitter command: install, build, run, troubleshoot
└── _archive/                 old/unused files kept for reference (not part of the repo)
```

## Quick start

Start the receiver first. Full steps are in the two `*_cmds.txt` files.

```bash
# Transmitter laptop
cd transmitter/gr-ieee802-11/examples
TX_CHANNEL=1 python3 wifi_tx_multi_hop.py              # terminal A
PPS=200 LABEL=session python3 packet_generator.py      # terminal B

# Receiver laptop
cd receiver/gr-ieee802-11/examples
export CSI_TA=02:00:00:00:00:01 CSI_RA=02:00:00:00:00:02
export CSI_OUT=~/usrp-projects/data/phase1/P01_test_$(date +%Y%m%d_%H%M%S).csv
python3 wifi_rx.py
```

## Rules that matter

- The receiver listens only on channel 1 (2412 MHz), so always start the transmitter with `TX_CHANNEL=1`.
- Use `PPS=200`; the default is 80.
- Install **only** `receiver/gr-ieee802-11` on the receiver laptop. The transmitter copy installs under the same name and replaces the CSI block.
- Old and unused files (channel-6 transmitter, broken headless receiver, old notes, old test CSVs) are in `_archive/`. Don't run them.
- Captured data (`*.csv`) and build folders are not stored in this repo.

## Phase-1 recording (current, from 2 Oct 2026)

- Locked settings: `TX_GAIN=15`, `RX_GAIN=12`, `PPS=200`, channel 1. (`pilot_tools/README.md` still shows an older `RX_GAIN=18` example; use 12.)
- On the TX laptop: `TX_GAIN=15 TX_CHANNEL=1 python3 -u wifi_tx_multi_hop.py` and `PPS=200 LABEL=phase1 python3 packet_generator.py`.
- On the RX laptop: `cd pilot_tools && unset DATA && export RX_GAIN=12 && ./record_part.sh <PID> <baseline|actions|signs_standing|signs_seated|scripts|empty>`.
- Daily check: `./record_part.sh DAY empty` must give at least 100 rows/s.
- Labels are written on the RX laptop clock, the same clock as the CSI `Timestamp_us`.
- Data is not in this repo (`*.csv` is ignored). It lives in `~/usrp-projects/data/phase1/` and in the backup zip.
- Read `docs/FULL_CONTEXT_2026-10-07.md` first: it lists the class set, dataset status, open problems and next steps.
