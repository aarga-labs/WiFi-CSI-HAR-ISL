# csi_tools — CSI data collection & ImgFi pipeline

Tools around the `extract_csi` block in `gnuradio/gr-ieee802-11`.
Classes: **walk, squat, bend, drink, nod, noaction (person still), empty (nobody)**.

## extract_csi configuration (env vars — no recompiling)

Set these in the SAME terminal before launching the flowgraph:

```bash
export CSI_TA=42:23:9e:d9:54:24     # MacBook WiFi MAC ("any" = no TA filter)
export CSI_RA=e2:63:84:5b:14:29     # hotspot BSSID    ("any" = no RA filter)
export CSI_OUT=~/usrp-projects/data/S01_squat_amrith_20260716.csv
# CSI_OUT unset -> auto-timestamped csi_YYYYmmdd_HHMMSS.csv (never overwrites)
```

The console prints every distinct `seen TA=.. RA=..` pair once — if your pair
never shows `(MATCH)`, a MAC rotated: re-check on the MacBook (`ifconfig en0`)
and the hotspot BSSID (Option-click the Wi-Fi icon on the Mac).

## Pre-session checklist (read aloud, every session)

1. Positions on tape (MacBook, USRP antenna, phone, subject spot, operator chair).
2. Hotspot channel still 11 → `freq` = 2462000000 (Option-click Wi-Fi icon on Mac).
3. MacBook: Private Wi-Fi Address OFF for the hotspot network; MAC unchanged.
4. MacBook: `sudo ping -i 0.01 <gateway-ip>` running (gateway: `netstat -nr | grep default`).
5. `CSI_TA` / `CSI_RA` / `CSI_OUT` exported; start `wifi_rx`; console shows `(MATCH)`
   and `~XX rows/s` reports ≥ 50 (target ~100).
6. Metadata sheet row filled (date, session, subject, class, channel, gain, rate).

## Session flow (discrete action, e.g. squat, 20–25 reps)

Terminal A (flowgraph):
```bash
export CSI_TA=... CSI_RA=... CSI_OUT=~/usrp-projects/data/S01_squat_amrith_20260716.csv
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
```

Terminal B (rep marking):
```bash
python3 session_logger.py --action squat --subject amrith \
        --name S01_squat_amrith_20260716 --channel 11
```
Per rep: coordinator cues → ENTER (start) → subject acts 2–3 s → ENTER (end)
→ 2 s still → next. Then stop both and immediately:
```bash
python3 check_capture.py ~/usrp-projects/data/S01_squat_amrith_20260716.csv
```
If the rate gate FAILs or MACs rotated mid-session, redo now.

Continuous classes (walk / noaction / empty): same, but
`session_logger.py --continuous` and record 90 s per take.

## After collection

```bash
# discrete (per session):
python3 segment_windows.py capture.csv --labels <name>_labels.csv --out-dir windows
# continuous (per take):
python3 segment_windows.py capture.csv --action walk --subject amrith --out-dir windows

python3 make_images.py windows/ --out dataset/
python3 train_imgfi.py dataset/ --test-subject gowreesh   # leave-one-subject-out
```

Never split randomly by image — all 52 subcarrier images of one window must
stay in one split, or the accuracy is fake. The per-window (majority-vote)
test accuracy is the number that matters.
