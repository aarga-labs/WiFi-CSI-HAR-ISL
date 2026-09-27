> HISTORICAL SNAPSHOT (7 October). Read Adhi_To_Amrith_Context.md first for completed P4/P5 collection, retained balanced training/results and the October 25 paper draft. Old instructions and planned work below are not current commands. The fabricated DATA_COMBINED warning remains important.

# PART 1 of 2: Sections 1–7

Status date: 7 Oct 2026. The last recorded data and the last QA are from 2 Oct 2026. Nothing from 3–7 Oct is known to me, so verify the current state with the user.

## 1. Project overview

**Project.** B.Tech CSE final-year project at Amrita Vishwa Vidyapeetham.
- Team of 5: Adhikkesh S K, Adithya Ajay, Amrith B, Gowreesh B, Rishiikesh S K. Rishiikesh is the user in this chat.
- Guide: Ms. Nalinadevi K.
- Title: "Multimodal Human Activity & Indian Sign Language Recognition for Inclusive Smart Homes".

**Problem statement.** Build a camera-free, privacy-preserving smart home for Deaf and hard-of-hearing residents. It recognises daily activities and Indian Sign Language (ISL) signs from WiFi CSI, optionally fused with a wearable phone IMU. It must tell sign vs routine activity vs idle, and infer intent (what the home should do) from the sign plus its context.

**Objectives.** One Q1 journal paper, with submission (not acceptance) by the end of October 2026.

**Current scope (decision of 28 Sep 2026).** One person at a time, WiFi CSI plus phone IMU if possible. Three tasks:
1. Sign vs routine vs idle.
2. Which sign or which action.
3. Intent = f(sign, context).

- The headline metric includes the false-command rate during routine activity.
- RO1 is single person, single modality.
- RO2 is single person, multi-modality (CSI+IMU).
- RO3 (multi-person) and RO4 (fusion) come after the paper.

**Architecture.**
- Hardware chain: TX laptop → USRP N210 (TX) → air → USRP N210 (RX) → RX laptop → CSI CSV.
- Labelling: a cue/label program on the RX laptop writes label CSVs on the same clock as the CSI.
- Planned recognition: state (idle/activity/sign/transition) → context → intent → fine class.

## 2. Project evolution (OLD vs CURRENT)

| Topic | OLD / SUPERSEDED / REJECTED | CURRENT | Why |
|---|---|---|---|
| Dataset | "Dataset 1" (Action/NoAction, 8 takes, 2 subjects, 17 Jul) and "Dataset 2" (15 classes, "5 participants", 600K rows, F1 0.71, "96% Action/NoAction") | Only new Phase-1 recordings (from 2 Oct 2026) | Dataset 2 P2–P5 were confirmed fabricated copies of P1 (timestamps shifted by exact 86,400 s steps, CSI correlation 0.97–0.997). **Excluded entirely. Never use or present it.** |
| Plan | `Revised_Action_Plan_Phase1.docx`: 41 classes (8 complex CASAS activities, 27 signs including KITCHEN, DOCTOR, MEDICINE, PEN, CARD, DIRTY, CLEAN, CLOTHING, SHIRT, GOOD MORNING/NIGHT, SICK, COLD, DOOR, THIEF), about 2.8 h per person | The `protocol.py` class set | Too long, and not adopted |
| Environment | Terrace considered; 3 environments considered | Env A is Rishiikesh's home (closed metal cabin). It is the main dataset, with the full protocol and all participants. Optional Env B uses a reduced protocol with 3 participants, `DATA=~/usrp-projects/data/phase1_envB`. A third environment is future work. | Quiet room, no outside motion. The terrace `site_check.py` was never run. |
| RX gain | 50 hard-coded (overload); 18 (29 Sep, TX 30); 16 (1 Oct, TX 15) | **TX_GAIN=15, RX_GAIN=12**, TX_CHANNEL=1, PPS=200 (2 Oct re-sweep, locked before any participant) | Gain sweeps (see §7) |
| Cues | espeak/Piper voice, Bluetooth speaker | **REJECTED**: the voice was unclear and Bluetooth is 2.4 GHz interference. CURRENT: full-screen colour block-letter cues plus WAV beeps (GO = one 1000 Hz beep, STOP = two 600 Hz beeps) via the laptop or a wired speaker | |
| Signs | 11 signs (HELLO, THANKYOU, LAMP, FAN, TELEVISION, WATER, HOT, CALL, HELP, PAIN, ACCIDENT) | **14 signs** (user decision, 2 Oct) | TOILET, COOK, HUNGRY added |
| Stories | 6 scripts (M/T/C × SEQ + INT), 12 runs, 25 min | **3 sequential scripts only**, 6 runs, about 12 min | Guide said interleaved is not required (2 Oct) |
| Video sync | Phone clock sync | **REJECTED**: Android only corrects its clock past a 2 s threshold, and MP4 creation time is whole seconds. CURRENT: 3 claps at the start and end of every part/run, Enter on the 3rd clap (`clap_x3` label rows). HD 30 fps phone video is fine. | |
| Old models | Model 1: ResNet-18 on recurrence plots (96% LOSO, but a single scalar got 99.1%, so the task was too easy). Model 2: 1D-CNN, LOFO macro-F1 0.71. | Not reportable, because Model 2 was built on fabricated data | |
| Kitchen action `cook` ("stir pot") | Proposed, then reverted | Not adopted. The COOK sign was adopted through the user's list. | |

## 3. Dataset

### Structure per participant (CURRENT)
Five parts. Each part gives one CSI CSV, one label CSV and one phone video.

1. **baseline:** stand_still 60 s, sit_still 60 s.
2. **actions:** 10 routine actions × 10 reps (fall × 5 max), random order, `--ready 4`.
3. **signs_standing:** 14 signs × 5 reps = 70 trials (`--ready 3`, 4 s sign window).
4. **signs_seated:** the same, in a chair.
5. **scripts:** 3 sequential stories × 2 runs = 6 runs, random order.

Also record "DAY empty" (120 s, everyone out of the room) at the start and end of each day.

**Targets.** 8–10 participants (5 team members plus 3–5 others), about 2 per day.

**Time per person.** About 63 min recording and about 1.5 h with setup. Breakdown: baseline 3 min, actions about 20 min, signs about 14 min each (standing and seated), stories about 12 min (estimate).

### Classes

**Actions (10).** Format: label (duration s, source dataset, look-alike sign).
- walk (6, UT-HAR, –)
- sitstand (6, UT-HAR, PAIN): starts seated, stand up then sit down
- pickup (6, UT-HAR, HELP)
- lightswitch (4, OPPORTUNITY, LAMP)
- drink (6, OPPORTUNITY, WATER)
- answerphone (6, CASAS/Lawton, CALL)
- eat (6, CASAS/Katz ADL, HOT/THANKYOU)
- wipetable (6, CASAS/OPPORTUNITY, FAN/HELLO)
- tvremote (5, CASAS, TELEVISION)
- fall (6, UT-HAR/XRF55, ACCIDENT): max 5 reps, on a mattress

**Signs (14, all with a 4 s window).** Format: sign, default intent, home action.

| Sign | Intent | Home action |
|---|---|---|
| HELLO | I4 | wake_system |
| THANKYOU | I4 | confirm_close |
| LAMP | I1 | toggle_light |
| FAN | I1 | toggle_fan |
| TELEVISION | I1 | toggle_tv |
| COOK | I1 | cooking_mode (exhaust + light + timer) |
| WATER | I2 | bring_water_reminder |
| HOT | I2 | cool_room |
| HUNGRY | I2 | food_request |
| TOILET | I2 | toilet_assist |
| CALL | I3 | call_caregiver |
| HELP | I3 | notify_caregiver |
| PAIN | I3 | health_alert |
| ACCIDENT | I3 | emergency_alert |

**Intent classes.**
- I0: no command (actions and idle). The home must NOT act.
- I1: device control.
- I2: personal need or comfort.
- I3: alert or assistance.
- I4: interaction.

**Stories (CURRENT, sequential).**
- **M-SEQ (meal, 13 steps):** clap, walk, lightswitch, sitstand(sit), eat, drink, HELLO, HUNGRY, COOK, HOT, WATER, THANKYOU, sitstand(stand), walk, clap.
- **T-SEQ (TV + phone, 12 steps):** clap, walk, sitstand, tvremote, answerphone, HELLO, TELEVISION, HOT, LAMP, CALL, TOILET, sitstand, walk, clap.
- **C-SEQ (cleaning → fall, 11 steps):** clap, walk, wipetable, pickup, FAN, HELP, walk, fall (context after_fall), HELP, PAIN, ACCIDENT, CALL, clap. It ends seated on the mattress.
- OLD/removed: M-INT, T-INT, C-INT.

### Recording setup (room layout, Env A)
- TX and RX sit at the ends of the window wall, raised about 6 in. The line between them is about 1.5 ft from the window wall.
- X is the standing spot at the middle, toes 1 ft from the line and facing it.
- W is 5 ft behind X (walk = X→W→X).
- The pickup book is 1 ft in front of X and 1 ft toward TX.
- A dead wall switch is in front of X, about 4 ft high.
- The table is toward RX. Its far edge is 0.5 ft from the line and its near end is 1 ft from X. The chair is tucked behind it.
- The mattress is toward TX, with its near end 1.5 ft from X and 1 ft from the line, marked with an F.
- The phone camera is on a stool by the window wall, 2–3 ft toward TX of the middle, about 4 ft high, in wide mode.
- Fans are off. Phones are in airplane mode. No Bluetooth.

### Labels and ground truth
`cue_session.py` writes the label CSV on the RX laptop clock, which is the same clock as the CSI `Timestamp_us`.
- Columns: `pid,mode,posture,trial,label,type,intent,home_action,context,script_id,run,step,t_start_us,t_end_us,source,note`.
- Types: activity, sign, idle, sync, flag.
- Flags: `BAD_TRIAL` (the operator types bad trial numbers at breaks, every 20 trials by default) and `BAD_RUN` ("Script OK?" = n).
- Isolated trials are auto-labelled from the cues (source=cue).
- Stories use the operator pressing Enter at the end of each step (source=keypress).
- Claps are logged as `clap_x3`.
- Video is only used to correct errors.

### Dataset status (kept takes, 2 Oct 2026, in `~/usrp-projects/data/phase1/`)

| Take | rows | s | rows/s | gaps >100 ms | note |
|---|---|---|---|---|---|
| DAY_empty_20261002_115654 | 15,512 | 126.0 | 123.1 | 0 | OK |
| P01_baseline_20261002_121522 | 22,973 | 219.6 | 104.6 | 74 (max 279 ms) | stand_still ran at 85 rows/s, usable |
| P01_actions_20261002_162956 | 170,393 | 1329.2 | 128.2 | 0 | RX_GAIN was 16, kept |
| P02_actions_20261002_171232 | 152,745 | 1175.5 | 129.9 | 3 | **Truncated: the RX link died at about 17:32 IST. CSI ends after trial 68, and trials 69–95 (27) have no CSI.** |
| P03_actions_20261002_175510 | 197,553 | 1509.8 | 130.8 | 0 | OK |
| P01_signs_standing_20261002_195615 | 107,928 | 835.7 | 129.1 | 0 | 70 trials OK |
| P02_signs_standing_20261002_193832 | 111,683 | 858.0 | 130.2 | 0 | OK |
| P03_signs_standing_20261002_204534 | 82,519 | 710.2 | 116.2 | 1 | OK |
| P01_scripts_20261002_210734 | 74,201 | 595.8 | 124.5 | 8 (max 912 ms, between runs) | 6 runs |
| P02_scripts_20261002_222939 | 56,859 | 458.0 | 124.1 | 0 | 6 runs |
| P03_scripts_20261002_224622 | 84,757 | 660.7 | 128.3 | 0 | 6 runs |

- All files have no NaN or short rows, monotonic timestamps, and channel 1 only.
- Per-class counts are correct (5 reps per sign, 10 per action, 5 falls).
- No BAD flags were used.
- Many aborted or no-packet takes sit in `phase1/discarded/` together with their labels.
- All 11 rx logs show a 4 MB UDP receive buffer, because `rmem_max` is not persistent across reboots.
- The P02 actions log has "link dead".
- Other data in `usrp-projects/data`: `gainsweep/` (6 dated folders, 272 MB), `pilot/` (18 MB, DAY_empty from 1 Oct), and `har/ch6` (tiny log). Total is 1.6 GB in 194 files.

### Dataset problems
1. P02 actions are truncated.
2. P01 baseline has 74 gaps. An optional 3-minute redo is possible, and the newest kept take wins.
3. P01 actions were recorded at RX_GAIN 16 instead of 12 (kept, and a gain guard was added to `record_part.sh`).
4. **No phone videos exist** in `phase1/videos/`, and the backup zip does not include them.
5. Still not recorded: P02 and P03 baseline, signs_seated for everyone, end-of-day empty room, P04 onwards.
6. Motion QA (peak motion energy in the window ÷ median 1.5–0.3 s before GO):
   - Signs have a median of 1.88 (P02), 1.97 (P01) and 2.31 (P03).
   - Weak signs (<1.5×): 7, 11 and 5 of 70.
   - Trials still moving at STOP: 14, 5 and 11.
   - Active sign motion lasts about 2.5–3.5 s.
   - Actions: P01 median 1.44 (50 of 86 weak), P02 1.33, P03 2.19.
   - walk (2.5–3.2×) and fall (2.4–2.8×) are the strongest. Small hand actions are weak for P01 and P02.
   - Conclusion: keep the 4 s sign window and tell participants to freeze during the yellow screen.

## 4. WiFi CSI setup

**Radios.**
- 2× Ettus USRP N210 with SBX daughterboards.
- The TX antenna is on RF1 (TX/RX) and the RX antenna is on RF2 (RX2), verified by opening a unit.
- The antennas are bare sleeve dipoles with the rubber cover missing, bent only at the black hinge to vertical, rod straight. Upright antennas radiate sideways omnidirectionally, and the tips are nulls.

**Software and signal.**
- GNU Radio with gr-ieee802-11 (Bloessl) and gr-foo.
- 802.11 OFDM, 20 MS/s (decimation 5 is odd, which gives a CIC roll-off warning; it is harmless and per-subcarrier normalisation handles it).
- BPSK 1/2, 128-byte frames, channel 1 (2412 MHz).
- 52 subcarriers (48 data + 4 pilots), LS channel estimate from two LTF symbols.
- **Amplitude only. There is no clock sync, so phase is unusable.**
- SISO.
- The sample rate was about 55 Hz originally and is now 110–130 rows/s.

**CSI file.** Columns are `Packet,Timestamp_us,Channel,SC0_Re,SC0_Im … SC51_Re,SC51_Im`. `Timestamp_us` is the RX host wall clock at decode.

**TX laptop (Amrith's HP, Ubuntu, UHD 4.1).**
- Path: `~/Desktop/usrp-csi-capture/transmitter/gr-ieee802-11/examples`. USRP at 192.168.10.9.
- Terminal A: `TX_GAIN=15 TX_CHANNEL=1 python3 -u wifi_tx_multi_hop.py 2>&1 | grep --line-buffered -E "PARKED|hop|rror|UHD"`. It must print "PARKED on Channel 1 (2412 MHz)". Any "Synced hop" means TX_CHANNEL was missed.
- Terminal B: `PPS=200 LABEL=phase1 python3 packet_generator.py`.
- MACs: 02:00:00:00:00:01 → 02:00:00:00:00:02.
- The TX prints one UHD underflow per packet because `usrp_sink` has no length tag. A 10,000-sample zero pad absorbs the restart. It is harmless; filter with `grep -v underflow`.

**RX laptop (Arch Linux, Python 3.14, UHD 4.9).**
- USRP at 192.168.10.7.
- Repo `~/adhikkesh/FYP/wifi_csi_capture` (git-initialised, never committed by Claude), with `receiver/gr-ieee802-11/examples/wifi_rx.py`.
- `wifi_rx.py` reads the `RX_GAIN` env variable, uses fixed channel 1, and takes env `CSI_TA`, `CSI_RA`, `CSI_OUT`.
- Requirements: `sudo cpupower frequency-set -g performance`, and `net.core.rmem_max` and `wmem_max` set to 50000000.

**Problems and fixes.**
- Added a `TX_GAIN` env to `wifi_tx_multi_hop.py` at line 101: `float(os.environ.get("TX_GAIN","30"))`. The PARKED message now prints the TX gain. Amrith applied this on his copy.
- Archived junk to `wifi_csi_capture/_archive/`, which has a README and is git-ignored.
- Deleted 3 stale `build/` dirs. A rebuild needs a fresh build dir because CMake caches paths.
- Kept 5 upstream demo `.grc` files because CMakeLists installs them.
- `wifi_rx_headless.py` is broken (IndentationError). Use `wifi_rx.py`.
- Earlier TX "no control response / link dead": NetworkManager dropped the IP. Fix: a persistent nmcli connection, a ping, a USRP power-cycle, and disabling suspend.
- Env B rule: same TX–RX distance, antenna heights and participant spot, re-run the gain sweep, and use a separate DATA dir.

## 5. Activity and sign recognition

**Class lists.** The current lists are in §3. The earlier lists (11 signs, 41 classes, 15-class Dataset 2) are in §2 and are superseded.

**Sign references.** Signs come from ISL sources only, not ASL.
- Sources: the ISL portal indiansignlanguage.org (FDMSE–RKMVERI dictionary), the Mendeley emergency-words dataset (accident, call, doctor, help, hot, lose, pain, thief), INCLUDE (Zenodo 4010759; Greetings, Electronics and Home categories, no Kitchen or Food), and the ISLRTC Sign Learn app and YouTube.
- ISL and ASL are separate languages. Woodward found 62–71% cognacy within Indo-Pakistani varieties, and only 7.7% of the Indian deaf in one survey knew ASL.
- SignFi (2018) is ASL, so WiFi ISL data is a gap the paper can claim.
- An ISL checker films reference clips as `sign_refs/<WORD>.mp4`.
- The forms for COOK, HUNGRY and TOILET are still to be fixed, because the ISL sites were blocked for me. THANKYOU, TELEVISION and WATER were also flagged "verify".

**Recording procedure.** See §3 and the `record_part.sh` details in Part 2 §8.
- For isolated signs, do the sign once, then stay still until STOP. No repeating. The window stays 4 s.
- Look-alike pairs (action vs sign) are a deliberate confuser design.
- Orders are randomised to avoid the packet-rate-by-class label leak. Resample on `Timestamp_us`.

**Recognition pipeline (PLANNED, not yet built on new data).**
- Baselines: a motion-energy scalar, and a random forest on handcrafted features.
- PCA → STFT/spectrogram → CNN.
- 1D-CNN or TCN.
- Hierarchical state → intent → class.
- Stream segmentation.
- LOSO (leave-one-subject-out) with calibration.
- A CSI vs IMU vs fusion ablation.
- Annotation: ELAN tiers or Label Studio are optional. An ELAN export from the label CSVs is not done.

## 6. Context and intent

- **Context** is the activity or situation that precedes or surrounds a sign. The values are meal, tv, cleaning and after_fall.
- **Intent** is what the home should do, given as a category I0–I4 plus a `home_action`.
- Routine movement must be ignored (I0). A sign is a command.
- The same sign gives a different intent depending on context. `CONTEXT_INTENT` in `protocol.py`:
  - HOT at meal → I3 kitchen_hazard_alert
  - HOT at tv → I2 cool_room
  - HELP at cleaning → I3 notify_caregiver
  - HELP after_fall → I3 emergency_alert
- `intent_of(label, typ, ctx)` returns `(category, home_action)`.
- The stories exist to test signs made right after everyday activity, where the preceding activity decides the intent.
- The SEQ vs INT comparison was dropped.

## 7. Experiments

**Gain sweeps.**
- Goal: choose RX_GAIN.
- Setup: sweep RX gain at fixed TX gain, measuring rows/s.
- 29 Sep, TX 30: gain 18 was chosen.
- 1 Oct, TX 30: overload, only RX 0–4 worked.
- 1 Oct, TX 15: peak at 16 dB (133.8 rows/s).
- 2 Oct re-sweep, TX 15 (rows/s): 0→20.8, 4→84.4, 8→108.6, 12→128.2, 16→116.5, 20→93.9, 24→57.1, 28→13.5, 31.5→7.7.
- Decision: **RX_GAIN=12**, locked. Daily check: `./record_part.sh DAY empty` must give at least 100 rows/s.

**Site check (terrace).** `site_check.py` has GOOD/USABLE/NOT GOOD rule-of-thumb limits. It was not run, and the closed home room was chosen instead.

**P01 pilot QC (2 Oct).** See the §3 quality table. Timing validation:
- Actions measured 19.6, 22.2 and 25.2 min against an 18.5 min timer.
- The signs part takes 14 min each, going from 55 to 70 trials. The fixed time is 9 s per trial (3 ready + 4 sign + 2 rest).

**Day-1 analysis (2 Oct).** All kept files are clean except the P02 truncation. The backup zip was created and CRC-verified. The motion check is in §3.

**Model experiments on new data.** None yet.

# PART 2 of 2: Sections 8–13 and MASTER CONTEXT

## 8. Important files and artifacts

**On the user's RX laptop (connected folders `/home/adhikkesh/adhikkesh/FYP` and `/home/adhikkesh/FYP`, plus `/home/adhikkesh/usrp-projects`).**

`~/adhikkesh/FYP/pilot_tools/`:
- `protocol.py`: single source of truth for classes, intents and scripts. md5 `73d912932706263b257ffb05fa099dda`.
- `cue_session.py`: the cue and label logger.
  - Modes: baseline, actions, signs, script, test.
  - Options: `--pid --posture --reps --runs --only --ready --rest --break-every --seed --plain --outdir`.
  - Ctrl+C exits with 130.
  - md5 `0f4116965b43c3080e96b8f4efa00038`.
- `cue_display.py`: the full-screen cue display.
- `record_part.sh`: md5 `1cd067e3d5fe548218a84dc36cdc8949`, executable (`chmod +x` after any redeploy).
  - Usage: `./record_part.sh <PID> <baseline|actions|signs_standing|signs_seated|scripts|empty> [extra args]`.
  - It needs `RX_GAIN`. REPO defaults to `$HOME/adhikkesh/FYP/wifi_csi_capture` and DATA to `~/usrp-projects/data/phase1`.
  - It has a keep/retake prompt. Discarded takes go to `$DATA/discarded/`.
  - It has a gain guard and copies the session log to `FYP/session_log_phase1.csv`.
- `plot_pilot.py`, `site_check.py`, `README.md` (md5 `c7afc5576d0bda066e9b1dce25deed34`).
- Local mirror in the cloud workspace: `/home/claude/pilot_tools/`.

Data and backup:
- `~/usrp-projects/data/{phase1,pilot,gainsweep,har}`. `phase1/` holds the CSI CSVs, `labels/`, `logs/*.rx.log`, `discarded/` and `session_log.csv`.
- Backup: `~/usrp-projects/backups/usrp_data_backup_2026-10-02.zip` (590 MB, 194 files, CRC-verified, sha256 prefix 283a1aca6e2b4b3c). The stray temp `backups/zi3RnL66` (82 MB) is not part of it and is safe to delete.
- QA scripts on the device: `~/qa/qa_take.py`, `qa_motion.py`, `zip_add.py`, `kept.txt`, and the JSON results.

**Claude Project "Final Year Project".** Docs: `claude/FYP_BRIEFING_2026-09-28.md` (sections 1–15, all decisions; §15 has the 2 Oct data check) and `main.tex`. File: `3_Month_Plan.pdf`.

**Links.**
- Recording SOP (Claude Doc): https://claude.ai/code/artifact/91aa8751-1f29-4bd6-95ed-ceb0f54a152d
- Participant Guide (Claude Doc): https://claude.ai/code/artifact/7d57275f-5bc9-4df5-b5ba-ec6ad9d53965
- CSI Label Player (artifact): https://claude.ai/artifact/8iV9zy48rqRBrfiippzsxs
  - It loads a CSI CSV and a label CSV in the browser.
  - It shows a heatmap (a high-pass "Motion" mode or a "Level" mode), a motion trace, a label strip, play and scrub controls, a segment table and QC chips.
  - It has synthetic example data and was tested with real files.

**Earlier referenced files (not all on the device now).** `FYP_FULL_CONTEXT.md`, `DATA_COLLECTION_PLAN.md`, `RO1_RO2_APPROVAL_PLAN.md`, `Revised_Action_Plan_Phase1.docx` (superseded), `Abstract_Introduction_Question_Mapping.pdf`.

## 9. Problems and blockers

| # | Problem | Tried | Result / status |
|---|---|---|---|
| 1 | P02 actions truncated (27 of 95 trials have no CSI; USRP "link dead") | Make-up command proposed | **Not yet run.** `record_part.sh` doesn't detect this. I offered a "CSI ends before labels" check and the user hasn't confirmed it. |
| 2 | `rmem_max` not persistent (UDP buffer 4 MB in all logs) | Sysctl.d snippet proposed | Not confirmed run |
| 3 | P01 baseline has 74 gaps | – | Optional 3-minute redo |
| 4 | COOK, HUNGRY and TOILET sign forms unverified | ISL sites blocked for me | The ISL checker must film reference clips. THANKYOU, TELEVISION and WATER also flagged "verify". |
| 5 | No videos copied; seated signs and some baselines missing | – | Pending |
| 6 | Mixed RX gain (P01 actions at 16) | Kept; gain guard added | Accepted; per-file normalisation |
| 7 | Timing reductions: `--ready 2 --rest 1.5 --break-every 35` for signs | Proposed | The user hasn't said to apply. The 4 s window is kept. |
| 8 | Earlier TX link-dead issue | See §4 fixes | Resolved |

Delete permission was granted in the session for the FYP folder only.

## 10. Important decisions and reasoning

1. The home closed room is the main environment: quiet, no outside motion. Env B is optional and reduced.
2. Dataset 2 is excluded because it is fabricated. The guide should be told (I advised this).
3. RX_GAIN 12 and TX_GAIN 15 are fixed for the whole dataset. Re-sweep only if DAY empty is below 100 rows/s or the antennas move.
4. On-screen cues and beeps, no voice, no Bluetooth (2.4 GHz interference).
5. Claps for video sync, since phone clock sync is unreliable. An automatic clap-detection sync script is planned once videos exist.
6. Retake: answer `r`, and Ctrl+C auto-discards. Nothing is deleted; takes are moved to `discarded/`.
7. 14 signs are final, learned from ISL references only.
8. Stories are sequential only, per the guide. Do each sign once, then stay still until STOP. The 4 s window is kept because sign motion lasts 2.5–3.5 s.
9. The COOK sign was adopted but the `cook` action was not.
10. Randomised trial order, with timestamp-based resampling, to avoid class-rate leakage.

## 11. Research, paper and guide feedback

- **Target:** Q1 journal. The target journal is still undecided.
- **Methodology:** the Phase-1 protocol above, with planned models in §5.
- **Expected contribution:**
  - A camera-free system that separates sign, routine and idle.
  - A false-command-rate metric on routine activity.
  - Context-dependent intent.
  - ISL WiFi-CSI data, which is a gap since SignFi is ASL.
  - Look-alike confuser pairs.
- **Results:** none yet on the new data. Old numbers (96%, F1 0.71) must not be reported.
- **Paper status:** `main.tex` exists, but the old abstract and introduction describe the discredited datasets. They must be rewritten around Phase-1 data, and the related work and introduction are pending.
- **Guide (Ms. Nalinadevi K.) feedback:**
  - CASAS-anchored activities.
  - ISL from INCLUDE/FDMSE references.
  - Confuser pairs.
  - Intent, not only context.
  - Ground-truth annotations.
  - Video-record every session.
  - Interleaved is NOT required (2 Oct).
- Consent form signed per participant. Ask the guide whether an Ethics Committee form is needed.
- **Timeline (briefing §9):**
  - 5–18 Oct: collect data.
  - 19–25 Oct: baselines and models.
  - 26–31 Oct: results, writing and submission.
- Precedents: SignFi (lab with 5 users plus home with 1) and Widar3.0.

## 12. CURRENT STATE (as of 2 Oct data; verify 3–7 Oct with the user)

- **Completed:** capture chain verified; tooling (14 signs, 3 SEQ stories, cues, retake logic) deployed; docs and briefing updated; day-1 QA done; verified backup zip; CSI Label Player published.
- **Recorded and kept:**
  - DAY empty.
  - P01: baseline, actions, signs_standing, scripts.
  - P02: actions (partial, 68 of 95 trials), signs_standing, scripts.
  - P03: actions, signs_standing, scripts.
- **In progress:** nothing is mid-edit.
- **Pending:** the items in §13.
- **Current architecture:** as in §1 and §4, with locked settings TX_GAIN=15, RX_GAIN=12, PPS=200, channel 1.
- **Current experiments:** none on models.

## 13. NEXT STEPS (discussed or required only)

1. Run the P02 actions make-up:
   ```
   cd ~/adhikkesh/FYP/pilot_tools && unset DATA && export RX_GAIN=12
   ./record_part.sh P02 actions --reps 4 --only walk,sitstand,pickup,lightswitch,drink,answerphone,eat,wipetable,tvremote
   ```
   Fall is omitted because P02 has 3 falls. First check that TX prints "PARKED on Channel 1" and that `DAY empty` is at least 100 rows/s.
2. Persist the buffer setting:
   ```
   echo -e "net.core.rmem_max=50000000\nnet.core.wmem_max=50000000" | sudo tee /etc/sysctl.d/99-usrp.conf && sudo sysctl --system
   ```
3. Record the remaining parts with `./record_part.sh <PID> <part>`: P02 and P03 baseline, signs_seated for P01–P03, end-of-day empty, then P04 onwards.
4. Copy the phone videos (named as printed, `<PID>_<part>_<timestamp>.mp4`) into `~/usrp-projects/data/phase1/videos/`, then write the automatic clap-detection sync script.
5. Film the ISL reference clips, especially COOK, HUNGRY and TOILET.
6. Optional: add a "CSI ends before labels / link dead" check to `record_part.sh`, apply the faster timing flags, or redo the P01 baseline. Only if the user says so.
7. Re-zip the backup after more recording. The user uploads it to Drive.
8. Start baselines and models (19–25 Oct) and the paper rewrite.

---

# MASTER CONTEXT (paste into another AI)

**Project.** B.Tech CSE final-year project at Amrita Vishwa Vidyapeetham. Team: Adhikkesh S K, Adithya Ajay, Amrith B, Gowreesh B, Rishiikesh S K (the user). Guide: Ms. Nalinadevi K. Title: "Multimodal Human Activity & Indian Sign Language Recognition for Inclusive Smart Homes". Goal: a camera-free smart home that recognises routine activities and ISL signs from WiFi CSI, tells sign vs routine vs idle, and infers intent (what the home should do) from the sign plus context. One Q1 journal paper, with submission by the end of Oct 2026 (journal undecided). Scope: single person, CSI plus optional phone IMU. Tasks: (1) sign/routine/idle, (2) which sign/action, (3) intent = f(sign, context). The headline metric includes the false-command rate on routine activity.

**Hard rules.**
- Never git commit; the user does that.
- Never use or present "Dataset 2" or DATA_COMBINED P2–P5. They are fabricated copies of P1.
- Never delete data without explicit permission. Use `discarded/`.
- Don't touch the recorded data.
- Don't edit files when only asked to suggest.
- The user wants short, crisp answers and for me to act on best judgement without asking.

**Hardware and software.**
- 2× USRP N210 with SBX, GNU Radio, gr-ieee802-11 and gr-foo.
- 802.11 BPSK 1/2, 20 MS/s, channel 1 (2412 MHz), 52 subcarriers, amplitude only (no clock sync), SISO.
- TX laptop (Amrith's, Ubuntu, UHD 4.1, USRP 192.168.10.9): `TX_GAIN=15 TX_CHANNEL=1 python3 -u wifi_tx_multi_hop.py` (must print "PARKED on Channel 1") plus `PPS=200 LABEL=phase1 python3 packet_generator.py`.
- RX laptop (Arch, Python 3.14, UHD 4.9, USRP 192.168.10.7): repo `~/adhikkesh/FYP/wifi_csi_capture`.
- Locked settings: TX_GAIN=15, RX_GAIN=12, PPS=200, channel 1, upright antennas. Daily check `./record_part.sh DAY empty` must give at least 100 rows/s.
- CSI CSV columns: `Packet,Timestamp_us,Channel,SC0_Re…SC51_Im`. `Timestamp_us` is the RX wall clock, and the label CSVs share that clock.

**Recording system (`~/adhikkesh/FYP/pilot_tools/`).**
- `protocol.py` defines everything.
- Run `cd ~/adhikkesh/FYP/pilot_tools && unset DATA && export RX_GAIN=12`, then `./record_part.sh <PID> <baseline|actions|signs_standing|signs_seated|scripts|empty>`.
- Data goes to `~/usrp-projects/data/phase1/` (CSI CSV, `labels/`, `logs/`, `discarded/`, `session_log.csv`).
- There is a keep/retake prompt, and Ctrl+C auto-discards.
- Colour screen cues plus beeps. Three claps (Enter on the 3rd) at the start and end of each part/run. One phone video per part.

**Protocol (CURRENT) per participant.**
- Baseline: stand 60 s and sit 60 s.
- 10 actions × 10 reps (fall × 5): walk, sitstand, pickup, lightswitch, drink, answerphone, eat, wipetable, tvremote, fall.
- 14 ISL signs × 5 standing plus × 5 seated, with a 4 s window (do once, then stay still until STOP): HELLO, THANKYOU, LAMP, FAN, TELEVISION, COOK, WATER, HOT, HUNGRY, TOILET, CALL, HELP, PAIN, ACCIDENT.
- 3 sequential stories × 2 runs: M-SEQ (meal), T-SEQ (TV/phone), C-SEQ (cleaning → fall). Interleaved stories were removed on the guide's instruction.
- Intents: I0 none; I1 device (LAMP, FAN, TELEVISION, COOK); I2 need (WATER, HOT, HUNGRY, TOILET); I3 alert (CALL, HELP, PAIN, ACCIDENT); I4 interaction (HELLO, THANKYOU).
- Context overrides: HOT at meal → kitchen_hazard_alert (I3); HOT at tv → cool_room (I2); HELP at cleaning → notify_caregiver (I3); HELP after_fall → emergency_alert (I3).
- Sign forms must come from ISL references (ISL portal, ISLRTC, INCLUDE, emergency dataset), not ASL. COOK, HUNGRY and TOILET forms are still to be fixed.

**Status (data as of 2 Oct 2026; the user may have recorded more since, so verify).** Recorded and kept at home (Env A):
- DAY empty.
- P01: baseline, actions, signs_standing, scripts.
- P02: actions (only 68 of 95 trials have CSI, because the USRP link died; make-up needed), signs_standing, scripts.
- P03: actions, signs_standing, scripts.

Quality: 116–131 rows/s, clean files, labels aligned. Signs show about 1.9–2.3× motion over rest, and sign motion lasts about 2.5–3.5 s, so the 4 s window stays.

Missing: P02 and P03 baseline, seated signs for everyone, end-of-day empty, P04 onwards, and all videos (none copied).

Backup: `~/usrp-projects/backups/usrp_data_backup_2026-10-02.zip` (590 MB, 194 files, verified).

Viewer: https://claude.ai/artifact/8iV9zy48rqRBrfiippzsxs.
Docs: Recording SOP https://claude.ai/code/artifact/91aa8751-1f29-4bd6-95ed-ceb0f54a152d, Participant Guide https://claude.ai/code/artifact/7d57275f-5bc9-4df5-b5ba-ec6ad9d53965, and the project briefing `claude/FYP_BRIEFING_2026-09-28.md`.

**Open items.**
1. P02 actions make-up: `./record_part.sh P02 actions --reps 4 --only walk,sitstand,pickup,lightswitch,drink,answerphone,eat,wipetable,tvremote`.
2. Persist the 50 MB `rmem_max` via `/etc/sysctl.d/99-usrp.conf`.
3. Optionally add a truncation / link-dead check to `record_part.sh`.
4. Optional faster timing flags (`--ready 2 --rest 1.5 --break-every 35` for signs). These are not applied.
5. Copy the videos to `phase1/videos/`, then build the clap-detection sync script.
6. Record the remaining participants. Env B is optional (3 participants, reduced protocol, separate DATA dir, re-run the gain sweep).
7. Models: baselines (motion-energy scalar, RF), PCA → spectrogram → CNN, 1D-CNN/TCN, hierarchical intent, LOSO with calibration, and a CSI vs IMU vs fusion ablation.
8. Rewrite the paper. The old abstract described the discredited datasets. Decide the target journal and confirm the IEC/consent requirement with the guide.

**Timeline.** 5–18 Oct collect data; 19–25 Oct baselines and models; 26–31 Oct results, writing and submission.