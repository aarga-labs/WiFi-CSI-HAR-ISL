# 1 — Data Capture Guide (End to End)

Everything needed to collect the CSI dataset, from empty room to labeled CSV files.
Read once fully, then use the **checklist** and **session workflow** sections during real sessions.

---

## What we are collecting

| | |
|---|---|
| Classes (7) | `walk`, `squat`, `bend`, `drink`, `nod`, `noaction` (person standing/sitting still), `empty` (nobody in room) |
| Subjects (3) | rishiikesh, amrith, gowreesh — everyone performs every class |
| One sample | ~2 seconds of CSI ≈ 200 packets at ~100 packets/sec |
| Target | 25 reps per person per discrete action, 2×90 s takes for continuous classes, over **2 different days** |

```
MacBook ──WiFi packets──> Android hotspot          (the "link" we sense)
    \                        
     \··· RF also reaches ···> USRP N210 ──ethernet──> Fedora laptop ──> CSV
                  ^
            person moves HERE (between MacBook and USRP)
            and disturbs the channel → CSI changes → that's the signal
```

The USRP never joins the network. It passively decodes MacBook→hotspot frames and
saves the channel estimate (52 complex subcarriers) of each frame.

---

## Part 0 — One-time setup (do once)

### 0.1 Install the updated extract_csi block (if not done yet)

```bash
cd ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/build
sudo make install && sudo ldconfig
```

Verify the new version is installed (must print nothing OLD — new version reads env vars):

```bash
strings /usr/local/lib64/libgnuradio-ieee802_11.so | grep "CSI_TA"   # should print CSI_TA
```

### 0.2 How the block is configured (no recompiling, ever)

Set these **in the same terminal** before starting the flowgraph:

| Variable | Meaning | Example |
|---|---|---|
| `CSI_TA` | Only save frames FROM this MAC (MacBook WiFi MAC). `any` = accept all | `42:23:9e:d9:54:24` |
| `CSI_RA` | Only save frames TO this MAC (hotspot BSSID). `any` = accept all | `e2:63:84:5b:14:29` |
| `CSI_OUT` | Output CSV path. **If not set** → auto file `~/usrp-projects/data/csi_YYYYmmdd_HHMMSS.csv` | `~/usrp-projects/data/S01_squat_amrith_20260716.csv` |

Nothing is ever overwritten: unset `CSI_OUT` gives a new timestamped file each run,
and a set `CSI_OUT` appends to an existing file.

The console tells you what is happening:

```
extract_csi: TA filter = 42:23:9e:d9:54:24, RA filter = e2:63:84:5b:14:29
extract_csi: writing to /home/rishiikesh/usrp-projects/data/S01_....csv
extract_csi: seen TA=42:23:9e:d9:54:24 RA=e2:63:84:5b:14:29 (MATCH)     <- good!
extract_csi: seen TA=aa:bb:cc:11:22:33 RA=ff:ff:ff:ff:ff:ff (no match)  <- other traffic, ignored
extract_csi: saved 100 packets (~95.2 rows/s)                            <- your live rate
```

**If your pair never shows `(MATCH)` → a MAC rotated. Fix env vars, restart flowgraph.**

### 0.3 MacBook one-time settings

1. Connect to the Android hotspot.
2. System Settings → Wi-Fi → hotspot network → Details → **Private Wi-Fi Address → OFF** (or "Fixed").
   Otherwise the MacBook changes its MAC and the filter silently stops matching.
3. Re-check the MAC after this change (it may change once when you turn it off):
   `ifconfig en0 | grep ether`

---

## Part 1 — Room and geometry (fix once, tape it, never move it)

1. Choose ONE room. Same room for the entire dataset. Door closed during recording.
2. Place with **tape marks on the floor**:
   - **MacBook** and **USRP antenna**: 3–4 m apart, antenna ~1–1.2 m high, orientation fixed.
   - **Subject spot**: exactly midway on the MacBook↔USRP line. The body must block/disturb this direct path — that is what creates the CSI signal.
   - **Android phone**: fixed spot ~1 m behind the MacBook (it only keeps the link alive).
   - **Operator chair**: behind the USRP, off the path. Operator does not move during recording.
3. Do not move furniture between sessions. No other people/pets in the room while recording.
4. Photo the setup with your phone so day 2 looks identical.

---

## Part 2 — Verification gates (run before EVERY collection day)

Do these in order. **Do not collect labeled data until all pass.** First time takes ~1 evening.

### Gate 1 — Current MACs

On the MacBook:
```bash
ifconfig en0 | grep ether                    # -> CSI_TA value
```
Hold **Option** and click the Wi-Fi icon in the menu bar → shows **BSSID** (→ `CSI_RA`)
and **Channel** of the hotspot.

### Gate 2 — Channel and frequency

| Channel | freq value |
|---|---|
| 1 | 2412000000 |
| 6 | 2437000000 |
| 11 | 2462000000 |

`wifi_rx.grc` currently has `freq = 2462000000` (channel 11). If the hotspot moved,
open the flowgraph in GNU Radio Companion and change the `freq` variable — or edit
`wifi_rx.py` directly. Android hops channels silently: **check every session**.

### Gate 3 — Traffic running

On the MacBook (keep this Terminal open the whole session):
```bash
netstat -nr | grep default          # find gateway IP (the phone), e.g. 172.20.10.1
sudo ping -i 0.01 <gateway-ip>      # 100 packets/second
```

### Gate 4 — Rate gate (THE critical one)

On the Fedora laptop:
```bash
export CSI_TA=<macbook-mac>  CSI_RA=<hotspot-bssid>
unset CSI_OUT
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
# let it run 60 seconds, watch for "(MATCH)" and "~XX rows/s", then Ctrl+C
python3 ~/usrp-projects/USRP_lib/csi_tools/check_capture.py ~/usrp-projects/data/csi_<latest>.csv
```

**PASS = sustained ≥ 50 rows/s (target ~100).** If FAIL, see Troubleshooting below.

### Gate 5 — Wiggle test (proves the CSI actually senses motion)

1. Record 30 s with the room completely still.
2. Then 30 s while someone waves an arm on the subject spot.
3. `check_capture.py` on that file → open the `_check.png` plot.
   The waving part must look obviously different (big fluctuations) from the still part.
   **If you cannot see it by eye, the CNN cannot see it either.** Fix gain/geometry first.

### Gate 6 — Gain / saturation (usually once, then freeze)

```bash
uhd_fft --args="addr=192.168.10.7" -f 2.462e9 -s 20e6
```
Signal clearly above the noise floor, not flat-topped/clipping. The UHD source gain
is `50` (set inside wifi_rx.grc, `gain0`). Change only if this test says so, then never again.

---

## Part 3 — Session workflow: discrete actions (squat, bend, drink, nod)

One **session** = one subject × one action ≈ 5 minutes total.

**Roles (rotate every session):**
- **Subject** — performs on the taped spot.
- **Operator** — Fedora laptop: flowgraph + session_logger + watches the console.
- **Coordinator** — MacBook + phone: ping running, channel checked, cues the subject, fills the log sheet.

**Naming convention:** `S<nn>_<action>_<subject>_<yyyymmdd>` e.g. `S03_squat_amrith_20260716`

### Steps

**Terminal A (Operator) — flowgraph:**
```bash
export CSI_TA=42:23:9e:d9:54:24            # today's verified values!
export CSI_RA=e2:63:84:5b:14:29
export CSI_OUT=~/usrp-projects/data/S03_squat_amrith_20260716.csv
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
```
Wait until you see `(MATCH)` and `~XX rows/s` reports ≥ 50.

**Terminal B (Operator) — rep marking:**
```bash
cd ~/usrp-projects/USRP_lib/csi_tools
python3 session_logger.py --action squat --subject amrith \
        --name S03_squat_amrith_20260716 --channel 11
```

**Per rep (repeat 25×):**
1. Coordinator: "ready… 3, 2, 1, go"
2. Operator presses **ENTER** (rep start)
3. Subject performs ONE squat, completing it **within 2–3 seconds**, then freezes
4. Operator presses **ENTER** (rep end)
5. Everyone still for ~2 s → next rep
6. Bad rep (tripped, too slow, someone walked by)? Operator types `u` + ENTER to undo, redo it.

**Finish:** Operator types `q` in the logger, then Ctrl+C the flowgraph, then **immediately**:
```bash
python3 check_capture.py ~/usrp-projects/data/S03_squat_amrith_20260716.csv
```
Rate OK + no warnings → session done, write the row in the log sheet.
Rate dropped or MAC rotated mid-session → **redo the session now**, not next week.

### Action definitions (keep them consistent!)

| Action | What exactly (2–3 s each) |
|---|---|
| squat | From standing: full squat down + stand back up |
| bend | From standing: bend forward as if picking something off the floor, back up |
| drink | From standing, bottle in hand at side: raise to mouth, sip motion, lower |
| nod | Standing still: 3–4 clear head nods (this is the hardest/smallest — exaggerate a bit) |

---

## Part 4 — Session workflow: continuous classes (walk, noaction, empty)

Same terminals, but the logger runs with `--continuous` (one ENTER to start the take,
one to end). Chunking into 2 s windows happens later, automatically.

| Class | Recording (2 takes × 90 s per subject per day) |
|---|---|
| `walk` | Walk back and forth naturally THROUGH the MacBook↔USRP path, turn at the ends |
| `noaction` | Take 1: stand still on the spot. Take 2: sit still on a chair on the spot. Breathe normally, no phone |
| `empty` | Nobody in the sensing area. Operator starts recording and steps out/away. **Once per day only** (not per subject) |

```bash
python3 session_logger.py --action walk --subject amrith \
        --name S07_walk_amrith_20260716 --continuous
```

---

## Part 5 — How much data (the plan)

| | Day 1 | Day 2 |
|---|---|---|
| Each of 3 subjects | 4 discrete actions × 25 reps + walk + noaction takes | same again (fresh setup from tape marks) |
| Once per day | 90 s `empty` take ×2 | same |
| Time | ~2 hours | ~2 hours |

Result: ≥ 75 windows per class (~3900 images/class after the ×52 subcarrier expansion).
Day 2 exists so the model can be tested on data from a different day — that's the honest test.

Balance rule: `noaction`/`empty` are easy to over-collect. Later, the segmentation step
caps them to match the action classes (~75 windows) — don't record 20 minutes of idle.

---

## Part 6 — The pre-session checklist (Coordinator reads aloud)

```
[ ] Everything on its tape marks (compare with photo)
[ ] Hotspot channel checked (Option-click Wi-Fi on Mac) and freq matches
[ ] MacBook MAC checked:  ifconfig en0 | grep ether
[ ] Hotspot BSSID checked (same Option-click panel)
[ ] sudo ping -i 0.01 <gateway> running on MacBook
[ ] CSI_TA / CSI_RA / CSI_OUT exported in the flowgraph terminal
[ ] Flowgraph console shows (MATCH) and >= 50 rows/s
[ ] Log sheet row: date, session name, subject, action, channel, rate
```

---

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| Console shows pairs but never `(MATCH)` | MAC rotated → re-check Gate 1, update `CSI_TA`/`CSI_RA`, restart |
| No `seen TA=...` lines at all | Nothing decodes: wrong channel/freq (Gate 2), no ping traffic (Gate 3), or gain problem (Gate 6) |
| Rate < 50 rows/s with `(MATCH)` | First try `CSI_TA=any CSI_RA=any` — if rate jumps, filter/MAC issue. If still low: the MacBook likely sends 802.11n (HT) frames which gr-ieee802-11 **cannot decode** (legacy OFDM only). Try iperf3 UDP (see commands file), different ping sizes; worst case accept the real rate but stay ≥ 30 rows/s |
| Rate collapses mid-session | Hotspot changed channel, or Mac MAC rotated. Console `(no match)` lines reveal which. Redo session |
| CSV empty but flowgraph runs | Check the `extract_csi: writing to ...` line — are you looking at the right file? `CSI_OUT` from another terminal doesn't apply |
| `Odd decimation`, `No GPSDO`, `thread priority` warnings | Ignore, harmless |
