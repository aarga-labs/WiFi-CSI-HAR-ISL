# pilot_tools — recording with ground-truth labels (does not touch `wifi_csi_capture/`)

For P04/P05 with cooking and seated trials, use `record_p45.sh` and the
commands in [P04_P05_COMMANDS.md](P04_P05_COMMANDS.md). The original class
and story definitions below remain in `protocol.py`; the additions are in
`protocol_p45.py`.

Copy this folder to the **RX laptop** (the one connected to USRP 192.168.10.7).
The labels must be written on the same laptop that writes the CSI, because both use its clock.

## Recommended: one command per part (`record_part.sh`)

The transmitter runs all day. For each part the operator types ONE command on the receiver laptop;
it starts the receiver, checks packets arrive, runs the cues/labels, stops the receiver and prints a
quality summary (also appended to `~/usrp-projects/data/phase1/session_log.csv`).

```bash
cd ~/adhikkesh/FYP/pilot_tools
python3 cue_session.py test           # check the big screen cues + beeps (full screen, zoom in)
export RX_GAIN=18                     # from gain_sweep.sh, same for the whole dataset
./record_part.sh DAY empty            # start and end of each day (everyone out of the room)
./record_part.sh P01 baseline
./record_part.sh P01 actions
./record_part.sh P01 signs_standing
./record_part.sh P01 signs_seated
./record_part.sh P01 scripts
```
**Mistake? Record the part again.** At the end of every part the script asks
`Keep this take? [Enter = keep / r = retake]`. Answer `r` and that take (CSI, labels, log) is moved to
`$DATA/discarded/` and marked `retake` in `session_log.csv`; then run the same command again.
Ctrl+C in the middle of a part discards it automatically (`aborted`). Only kept takes stay in `$DATA`.

The manual steps below still work and do the same thing.

## New place? Test it first (about 20 min, `site_check.py`)

Every time the recording place or the antenna positions change:
```bash
cd ~/adhikkesh/FYP/wifi_csi_capture/receiver && ./gain_sweep.sh          # new place = new RX_GAIN
cd ~/adhikkesh/FYP/pilot_tools && export RX_GAIN=<best>
./record_part.sh SITE empty            # nobody inside; one teammate walks up and down OUTSIDE the open side
./record_part.sh P00 signs_standing --reps 3
D=~/usrp-projects/data/phase1
python3 site_check.py --empty "$D/SITE_empty_*.csv" --signs "$D/P00_signs_standing_*.csv" \
                      --labels "$D/labels/labels_P00_signs_*.csv"
```
It prints GOOD / USABLE / NOT GOOD: how strong outside movement is compared with a weak ISL sign.

## Second environment (Env B, reduced protocol)

Main dataset = home (default data folder). For the second place, keep everything in its own folder,
re-run the gain sweep there, and keep the TX-RX distance, antenna heights and participant spot the same as at home:
```bash
export DATA=~/usrp-projects/data/phase1_envB   # every terminal in Env B; its own session_log.csv + labels/
export RX_GAIN=<best from gain_sweep.sh at Env B>
./record_part.sh DAY empty
./record_part.sh P01 baseline
./record_part.sh P01 signs_standing
./record_part.sh P01 actions --reps 5
./record_part.sh P01 scripts --runs 1
```
Use 3 participants who were already recorded at home.

## Every session: start the radios

TX laptop, terminal 1 and 2:
```bash
cd wifi_csi_capture/transmitter/gr-ieee802-11/examples
TX_CHANNEL=1 python3 wifi_tx_multi_hop.py        # must print "PARKED on Channel 1"
PPS=200 LABEL=session python3 packet_generator.py
```

RX laptop, terminal 1 (one CSV per part; Ctrl+C at the end of the part):
```bash
cd wifi_csi_capture/receiver/gr-ieee802-11/examples
export CSI_TA=02:00:00:00:00:01 CSI_RA=02:00:00:00:00:02
mkdir -p ~/usrp-projects/data/phase1
export CSI_OUT=~/usrp-projects/data/phase1/P00_part2_actions_$(date +%Y%m%d_%H%M%S).csv
python3 wifi_rx.py            # this receiver is fixed to channel 1 (2412 MHz)
```
Use `wifi_rx.py` (old receiver variants are in `wifi_csi_capture/_archive/`; don't run them).

RX laptop, terminal 2: wait ~10 s, then check that rows are growing, `wc -l $CSI_OUT` twice, 10 s apart.
Aim for 100–150 new rows per second. If it's under 60 per second, close other apps and set the CPU to performance mode:
`sudo cpupower frequency-set -g performance` (Fedora: `sudo dnf install kernel-tools`; Ubuntu: `sudo apt install linux-tools-common`).

## Parts of one participant session (each part = one CSI file + one label file)

| Part | CSI_OUT name | Command in terminal 2 | Time |
|---|---|---|---|
| 1 | `Pxx_part1_baseline_...csv` | `python3 cue_session.py baseline --pid Pxx` | 3 min |
| 2 | `Pxx_part2_actions_...csv` | `python3 cue_session.py actions --pid Pxx --reps 10` | 20 min |
| 3 | `Pxx_part3_signs_standing_...csv` | `python3 cue_session.py signs --pid Pxx --posture standing --reps 5` | 12 min |
| 4 | `Pxx_part4_signs_seated_...csv` | `python3 cue_session.py signs --pid Pxx --posture seated --reps 5` | 12 min |
| 5 | `Pxx_part5_scripts_...csv` | `python3 cue_session.py script --pid Pxx --runs 2` | 12 min |

Empty room: at the start and end of each day, record 2 min with nobody inside (`CSI_OUT=..._empty_...csv`, no labels needed).
Start the phone video before each part. Keep the RX laptop screen with the terminal in the frame for the claps.

## Pilot (today): the 6 look-alike pairs + 4 scripts, about 25 min of recording

Use `--only` to record a subset:
```bash
python3 cue_session.py baseline --pid P00
python3 cue_session.py actions  --pid P00 --only lightswitch,drink,answerphone,eat,tvremote,wipetable --reps 5
python3 cue_session.py signs    --pid P00 --only LAMP,WATER,CALL,HOT,TELEVISION,FAN --reps 5
python3 cue_session.py script   --pid P00 --only M-SEQ,T-SEQ --runs 1
```

## Plots

Run on any laptop with numpy, pandas and matplotlib:
```bash
D=~/usrp-projects/data
python3 plot_pilot.py --csi $D/phase1/P00_part2_actions_*.csv --labels "$D/labels/labels_P00_actions_*.csv" --out figs
python3 plot_pilot.py --csi $D/phase1/P00_part3_signs_*.csv   --labels "$D/labels/labels_P00_signs_*.csv"   --out figs
python3 plot_pilot.py --csi $D/phase1/P00_part5_scripts_*.csv --labels "$D/labels/labels_P00_script_*.csv"  --out figs
```
To plot signs next to their look-alike actions in one figure, record them in the same CSI file
(or send me both files and I'll merge them).

Class names, intents and scripts are defined in `protocol.py`; change them there only.

**ISL signs (final, 2 Oct, 14):** HELLO, THANKYOU, TOILET, HELP, CALL, COOK, TELEVISION, HOT, LAMP, FAN, ACCIDENT,
HUNGRY, PAIN, WATER. Signs part = 14 x 5 = 70 trials per posture. HUNGRY and COOK are in the Meal stories,
TOILET in the TV stories.

**Stories (2 Oct): sequential only.** M-SEQ, T-SEQ, C-SEQ, each run twice in random order = 6 runs.
