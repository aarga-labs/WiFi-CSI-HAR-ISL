# P04 capture audit

All structural checks passed: True

| Part | Date | CSI rows | Rows/s | Events covered | Gaps >100 ms | Max event gap (ms) |
|---|---|---:|---:|---:|---:|---:|
| baseline | 2026-10-15 | 15898 | 98.4 | 2/2 | 0 | 86.3 |
| actions | 2026-10-16 | 160411 | 105.7 | 115/115 | 9 | 122.0 |
| actions_seated | 2026-10-16 | 82425 | 94.4 | 70/70 | 8 | 147.1 |
| signs_standing | 2026-10-16 | 77771 | 115.0 | 70/70 | 0 | 68.0 |
| signs_seated | 2026-10-16 | 68682 | 100.5 | 70/70 | 3 | 109.0 |
| scripts | 2026-10-16 | 71221 | 109.1 | 100/100 | 1 | 470.4 |
| empty | 2026-10-16 | 11402 | 90.1 | n/a | 1 | n/a |

P04 totals: 476,408 CSI rows; 425 action/sign/story events plus two idle baselines.

## Review notes

- Below-80 rows/s events are flagged for review, not automatically rejected. No recognition accuracy or correct physical performance is established by file integrity checks.
- The expected videos were not found in this dataset directory; their existence on the phone and performed movements/signs have not been verified.
- P04 baseline is from 15 October; action/sign/story captures are from 16 October. Operator reports same person/environment and baseline before rain. Retain date/session distinction.
- T-SEQ run 1 HOT (step 7) contains a 470.433 ms packet gap, inside a 4.561 s segment. This segment requires quality review before modelling; do not assume full temporal coverage from its start/end bounds alone.
- Latest kept empty-room reference: DAY_empty_20261016_204217.csv, recorded on 2026-10-16. Earlier empty-room takes remain in the source dataset.

## Story verification

All four stories have runs 1 and 2. All step labels, order, postures and intent mappings match the P04/P05 protocol. There are 100 story events (50 activities and 50 signs) and 16 sync markers.

## Events below 80 rows/s

| Part | Trial/step | Label | Rows/s |
|---|---:|---|---:|
| actions_seated | 1.0 | chop_food | 76.8 |
| actions_seated | 3.0 | drink | 71.5 |
| actions_seated | 4.0 | chop_food | 62.8 |
| actions_seated | 5.0 | stir_pot | 66.8 |
| actions_seated | 6.0 | eat | 52.0 |
| actions_seated | 7.0 | drink | 65.3 |
| actions_seated | 8.0 | eat | 61.5 |
| actions_seated | 9.0 | stir_pot | 76.0 |
| actions_seated | 10.0 | chop_food | 68.5 |
| actions_seated | 11.0 | answerphone | 64.8 |
| actions_seated | 12.0 | stir_pot | 77.0 |
| signs_seated | 1.0 | TELEVISION | 64.5 |
| signs_seated | 6.0 | HELLO | 79.5 |
| signs_seated | 7.0 | PAIN | 67.2 |
| signs_seated | 8.0 | HELP | 75.0 |
| signs_seated | 12.0 | HUNGRY | 80.0 |
| signs_seated | 14.0 | THANKYOU | 79.7 |
| signs_seated | 15.0 | ACCIDENT | 75.2 |
| signs_seated | 16.0 | COOK | 55.5 |
| signs_seated | 17.0 | TOILET | 76.0 |
| scripts | 9 | HUNGRY | 77.4 |
| scripts | 14 | sitstand | 77.0 |

## Sources

- CSI: [P04_baseline_20261015_210905.csv](/home/adhikkesh/usrp-projects/data/phase1/P04_baseline_20261015_210905.csv)
- Labels: [labels_P04_baseline_20261015_210933.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P04_baseline_20261015_210933.csv)
- CSI: [P04_actions_20261016_110306.csv](/home/adhikkesh/usrp-projects/data/phase1/P04_actions_20261016_110306.csv)
- Labels: [labels_P04_actions_standing_20261016_110318.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P04_actions_standing_20261016_110318.csv)
- CSI: [P04_actions_seated_20261016_114344.csv](/home/adhikkesh/usrp-projects/data/phase1/P04_actions_seated_20261016_114344.csv)
- Labels: [labels_P04_actions_seated_20261016_114353.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P04_actions_seated_20261016_114353.csv)
- CSI: [P04_signs_standing_20261016_133515.csv](/home/adhikkesh/usrp-projects/data/phase1/P04_signs_standing_20261016_133515.csv)
- Labels: [labels_P04_signs_standing_20261016_133528.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P04_signs_standing_20261016_133528.csv)
- CSI: [P04_signs_seated_20261016_174235.csv](/home/adhikkesh/usrp-projects/data/phase1/P04_signs_seated_20261016_174235.csv)
- Labels: [labels_P04_signs_seated_20261016_174247.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P04_signs_seated_20261016_174247.csv)
- CSI: [P04_scripts_20261016_180612.csv](/home/adhikkesh/usrp-projects/data/phase1/P04_scripts_20261016_180612.csv)
- Labels: [labels_P04_script_20261016_180623.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P04_script_20261016_180623.csv)
- CSI: [DAY_empty_20261016_204217.csv](/home/adhikkesh/usrp-projects/data/phase1/DAY_empty_20261016_204217.csv)
- Session log: [/home/adhikkesh/usrp-projects/data/phase1/session_log.csv](/home/adhikkesh/usrp-projects/data/phase1/session_log.csv)
