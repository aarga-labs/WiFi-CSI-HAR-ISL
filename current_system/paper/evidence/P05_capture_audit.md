# P05 capture audit

All structural checks passed: True

| Part | Date | CSI rows | Rows/s | Events covered | Gaps >100 ms | Max event gap (ms) |
|---|---|---:|---:|---:|---:|---:|
| baseline | 2026-10-16 | 15223 | 105.8 | 2/2 | 0 | 72.8 |
| actions | 2026-10-16 | 163324 | 116.4 | 115/115 | 4 | 118.8 |
| actions_seated | 2026-10-16 | 90872 | 105.9 | 70/70 | 0 | 80.7 |
| signs_standing | 2026-10-16 | 77507 | 118.4 | 70/70 | 0 | 58.2 |
| signs_seated | 2026-10-16 | 58527 | 89.5 | 70/70 | 9 | 164.3 |
| scripts | 2026-10-16 | 67427 | 104.0 | 100/100 | 5 | 100.8 |
| empty | 2026-10-16 | 11402 | 90.1 | n/a | 1 | n/a |

P05 totals: 472,880 CSI rows; 425 action/sign/story events plus two idle baselines.

## Review notes

- Below-80 rows/s events are flagged for review, not automatically rejected. No recognition accuracy or correct physical performance is established by file integrity checks.
- The expected videos were not found in this dataset directory; their existence on the phone and performed movements/signs have not been verified.
- All P05 participant captures are from 16 October.
- Latest kept empty-room reference: DAY_empty_20261016_204217.csv, recorded on 2026-10-16. Earlier empty-room takes remain in the source dataset.

## Story verification

All four stories have runs 1 and 2. All step labels, order, postures and intent mappings match the P04/P05 protocol. There are 100 story events (50 activities and 50 signs) and 16 sync markers.

## Events below 80 rows/s

| Part | Trial/step | Label | Rows/s |
|---|---:|---|---:|
| signs_seated | 2.0 | LAMP | 70.0 |
| signs_seated | 3.0 | TELEVISION | 69.0 |
| signs_seated | 4.0 | COOK | 79.7 |
| signs_seated | 5.0 | CALL | 55.5 |
| signs_seated | 12.0 | CALL | 63.5 |
| signs_seated | 13.0 | HUNGRY | 73.7 |
| signs_seated | 17.0 | ACCIDENT | 71.7 |
| signs_seated | 19.0 | CALL | 69.7 |
| signs_seated | 23.0 | HOT | 79.2 |
| signs_seated | 24.0 | TOILET | 78.7 |
| signs_seated | 26.0 | COOK | 77.7 |
| signs_seated | 27.0 | HELP | 66.5 |
| signs_seated | 28.0 | THANKYOU | 75.2 |
| signs_seated | 29.0 | TOILET | 73.2 |
| signs_seated | 30.0 | TELEVISION | 72.5 |
| signs_seated | 31.0 | ACCIDENT | 78.5 |
| signs_seated | 32.0 | THANKYOU | 71.2 |
| signs_seated | 34.0 | ACCIDENT | 78.2 |
| signs_seated | 36.0 | HELLO | 75.0 |
| signs_seated | 37.0 | HELP | 71.2 |
| signs_seated | 38.0 | TOILET | 76.0 |
| signs_seated | 39.0 | COOK | 67.5 |
| signs_seated | 40.0 | LAMP | 76.0 |
| signs_seated | 43.0 | CALL | 71.2 |
| signs_seated | 49.0 | HELLO | 78.5 |
| signs_seated | 62.0 | THANKYOU | 77.0 |
| scripts | 4 | answerphone | 78.3 |

## Sources

- CSI: [P05_baseline_20261016_184716.csv](/home/adhikkesh/usrp-projects/data/phase1/P05_baseline_20261016_184716.csv)
- Labels: [labels_P05_baseline_20261016_184735.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P05_baseline_20261016_184735.csv)
- CSI: [P05_actions_20261016_185132.csv](/home/adhikkesh/usrp-projects/data/phase1/P05_actions_20261016_185132.csv)
- Labels: [labels_P05_actions_standing_20261016_185158.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P05_actions_standing_20261016_185158.csv)
- CSI: [P05_actions_seated_20261016_192001.csv](/home/adhikkesh/usrp-projects/data/phase1/P05_actions_seated_20261016_192001.csv)
- Labels: [labels_P05_actions_seated_20261016_192014.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P05_actions_seated_20261016_192014.csv)
- CSI: [P05_signs_standing_20261016_194820.csv](/home/adhikkesh/usrp-projects/data/phase1/P05_signs_standing_20261016_194820.csv)
- Labels: [labels_P05_signs_standing_20261016_194836.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P05_signs_standing_20261016_194836.csv)
- CSI: [P05_signs_seated_20261016_200623.csv](/home/adhikkesh/usrp-projects/data/phase1/P05_signs_seated_20261016_200623.csv)
- Labels: [labels_P05_signs_seated_20261016_200742.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P05_signs_seated_20261016_200742.csv)
- CSI: [P05_scripts_20261016_202646.csv](/home/adhikkesh/usrp-projects/data/phase1/P05_scripts_20261016_202646.csv)
- Labels: [labels_P05_script_20261016_202659.csv](/home/adhikkesh/usrp-projects/data/phase1/labels/labels_P05_script_20261016_202659.csv)
- CSI: [DAY_empty_20261016_204217.csv](/home/adhikkesh/usrp-projects/data/phase1/DAY_empty_20261016_204217.csv)
- Session log: [/home/adhikkesh/usrp-projects/data/phase1/session_log.csv](/home/adhikkesh/usrp-projects/data/phase1/session_log.csv)
