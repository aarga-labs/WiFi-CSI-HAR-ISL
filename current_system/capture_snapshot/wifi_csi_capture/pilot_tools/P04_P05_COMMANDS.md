# P04 and P05 recording

Same room, antenna positions, channel and radio settings as P01-P03.
Use `record_p45.sh` for this version. The original `record_part.sh` defaults
to the original protocol, and `protocol.py` has not been changed.

## Additions

- `chop_food`: six seconds of repeated chopping motions using a blunt prop
  on a board. Keep the board and prop consistent for both people.
- `stir_pot`: six seconds stirring a spoon in an empty/cold pot. Use the same
  pot and spoon for both people.
- These correspond to the existing COOK, HUNGRY, HOT and WATER signs. No new
  signs or home-control intents have been added. Cooking actions are I0.
- Standing actions: the original 95 trials plus 10 of each new cooking action
  = 115 trials across 12 classes. Falls stay capped at five.
- Seated actions: drink, eat, answerphone, tvremote, wipetable, chop_food,
  stir_pot, ten trials each = 70 trials. Remain seated throughout this part.
- Signs: the original 14 signs, five trials each, in both standing and seated
  postures = 70 trials per posture.
- Stories: M-SEQ adds chopping and stirring before sitting. T-SEQ and C-SEQ
  keep the original steps. S-SEQ is the new seated cooking/meal story. Each
  story runs twice, in random order = eight runs.
- Labels explicitly record standing, seated, moving, transition or mattress
  posture and `protocol=p45-v1` in the note column.

Standing/moving actions still include walking, sit-to-stand-to-sit and the
original mattress fall. Those are not repeated in the seated-only part.

## TX laptop: keep both terminals running

Use the same TX checkout as before. Its recorded location on the TX laptop
was `~/Desktop/usrp-csi-capture`; if that checkout has moved, use its current
`transmitter/gr-ieee802-11/examples` directory.

Terminal 1:

```bash
cd ~/Desktop/usrp-csi-capture/transmitter/gr-ieee802-11/examples
TX_GAIN=15 TX_CHANNEL=1 python3 -u wifi_tx_multi_hop.py
```

Check that it prints PARKED on Channel 1 (2412 MHz).

Terminal 2:

```bash
cd ~/Desktop/usrp-csi-capture/transmitter/gr-ieee802-11/examples
PPS=200 LABEL=phase1 python3 packet_generator.py
```

## RX laptop: setup once in the recording terminal

```bash
export REPO=/home/adhikkesh/adhikkesh/FYP/wifi_csi_capture
export DATA=/home/adhikkesh/usrp-projects/data/phase1
export RX_GAIN=12
cd "$REPO/pilot_tools"
sudo sysctl -w net.core.rmem_max=50000000
sudo sysctl -w net.core.wmem_max=50000000
sudo cpupower frequency-set -g performance
ping -c 3 192.168.10.7
python3 cue_session.py test
```

The recorder starts/stops the receiver for each part. Do not start a second
`wifi_rx.py` manually. Keep the room and antennas fixed. Use laptop/wired
sound, keep Bluetooth off, and keep phones in airplane mode.

## Record in this order

Run each command after the preceding part finishes. The recorder asks you
to start the phone video, handles claps and cues, and prints the suggested
video filename. Enter on the third clap at each sync marker. Freeze during
the yellow/ready and red/stop intervals. In stories, press Enter when each
displayed step ends, including the separate sit/stand transition.

Start-of-day empty room:

```bash
bash record_p45.sh DAY empty
```

P04:

```bash
bash record_p45.sh P04 baseline
bash record_p45.sh P04 actions
bash record_p45.sh P04 actions_seated
bash record_p45.sh P04 signs_standing
bash record_p45.sh P04 signs_seated
bash record_p45.sh P04 scripts
```

P05:

```bash
bash record_p45.sh P05 baseline
bash record_p45.sh P05 actions
bash record_p45.sh P05 actions_seated
bash record_p45.sh P05 signs_standing
bash record_p45.sh P05 signs_seated
bash record_p45.sh P05 scripts
```

End-of-day empty room:

```bash
bash record_p45.sh DAY empty
```

At the keep/retake prompt, use `r` for a bad take, then repeat that command.
Keep each phone video with the name printed by the recorder. Record the
fully seated story at the same table/chair position for both participants.
Allow roughly 1.5-2 hours per person including setup, breaks and retakes;
story timing depends on the operator and participant.

## Story instructions

M-SEQ: clap, walk, lightswitch, chop_food, stir_pot, sit down, eat, drink,
HELLO, HUNGRY, COOK, HOT, WATER, THANKYOU, stand up, walk, clap.

T-SEQ: clap, walk, sit down, tvremote, answerphone, HELLO, TELEVISION, HOT,
LAMP, CALL, TOILET, stand up, walk, clap.

C-SEQ: clap, walk, wipetable, pickup, FAN, HELP, walk, fall, HELP, PAIN,
ACCIDENT, CALL, clap. After the fall the participant stays on the mattress.

S-SEQ: sit in the chair before the start clap and remain seated for the
whole run. Clap, wipetable, chop_food, stir_pot, eat, drink, HELLO, HUNGRY,
COOK, HOT, WATER, HELP, THANKYOU, clap.

## Preview without recording

```bash
python3 cue_session.py actions --pid P04 --protocol p45 --plan
python3 cue_session.py actions --pid P04 --protocol p45 --posture seated --plan
python3 cue_session.py script --pid P04 --protocol p45 --plan
```

These preview commands do not start the receiver or save label files.

## Analysis after collection

P01-P03 have no isolated seated block or these cooking actions. Report the
common original classes across all five participants separately from the
new cooking/seated subset, which initially has only P04 and P05. Do not
interpret participant differences as a posture effect. The existing model
training code will need to include `actions_seated` and the two new labels
before retraining; collecting data does not update the trained model.
