# Correctly named actions and signs

Compared on identical original P1–P3 isolated events, using our completed balanced run. The newer improved notebook has no verified results here. Each person was excluded from their model’s training. Our model learned from four other people; the friend’s model learned from two. These are per-class correct-count percentages (recall), not F1. Event boundaries and action/sign type are supplied.

## Actions

| Class | Friend | Ours | Our common mistakes |
|---|---:|---:|---|
| walk | 26/26 (100.0%) | 26/26 (100.0%) | — |
| sit–stand | 24/28 (85.7%) | 26/28 (92.9%) | lightswitch (1), wipetable (1) |
| fall | 9/13 (69.2%) | 8/13 (61.5%) | sitstand (2), tvremote (1) |
| pick up | 17/28 (60.7%) | 21/28 (75.0%) | drink (3), answerphone (2) |
| eat | 13/27 (48.1%) | 11/27 (40.7%) | tvremote (10), answerphone (3) |
| drink | 11/27 (40.7%) | 10/27 (37.0%) | answerphone (6), tvremote (6) |
| answer phone | 10/27 (37.0%) | 8/27 (29.6%) | drink (10), tvremote (8) |
| wipe table | 9/27 (33.3%) | 24/27 (88.9%) | tvremote (3) |
| light switch | 6/28 (21.4%) | 5/28 (17.9%) | answerphone (7), drink (5) |
| TV remote | 6/27 (22.2%) | 5/27 (18.5%) | eat (10), answerphone (4) |
| **Overall** | **131/258 (50.8%)** | **144/258 (55.8%)** | |

## Signs

| Class | Friend | Ours | Our common mistakes |
|---|---:|---:|---|
| LAMP | 8/15 (53.3%) | 8/15 (53.3%) | COOK (3), FAN (2) |
| HUNGRY | 8/15 (53.3%) | 7/15 (46.7%) | PAIN (7), LAMP (1) |
| HELP | 7/15 (46.7%) | 7/15 (46.7%) | HELLO (2), THANKYOU (2) |
| COOK | 6/15 (40.0%) | 12/15 (80.0%) | LAMP (3) |
| HOT | 4/15 (26.7%) | 3/15 (20.0%) | HELLO (5), WATER (4) |
| PAIN | 4/15 (26.7%) | 6/15 (40.0%) | CALL (3), TELEVISION (2) |
| FAN | 3/15 (20.0%) | 7/15 (46.7%) | WATER (3), HELLO (2) |
| WATER | 3/15 (20.0%) | 4/15 (26.7%) | HELLO (5), HOT (3) |
| ACCIDENT | 3/15 (20.0%) | 5/15 (33.3%) | HELLO (4), HELP (2) |
| TOILET | 2/15 (13.3%) | 1/15 (6.7%) | HELLO (5), HELP (2) |
| CALL | 1/15 (6.7%) | 3/15 (20.0%) | HELLO (4), HELP (2) |
| HELLO | 0/15 (0.0%) | 10/15 (66.7%) | WATER (3), PAIN (1) |
| THANKYOU | 0/15 (0.0%) | 0/15 (0.0%) | HELLO (6), TOILET (3) |
| TELEVISION | 0/15 (0.0%) | 4/15 (26.7%) | HELP (3), LAMP (3) |
| **Overall** | **49/210 (23.3%)** | **77/210 (36.7%)** | |

One partial P02 light-switch interval is excluded from both columns. The screenshot includes it: 7/29 and 132/259 actions overall. Matched values are 6/28 and 131/258. Common mistakes list up to two most frequent wrong labels; ties may have other equally frequent labels.

## Signs caught and wrong reactions at fixed thresholds

The screenshot’s approximate 9/10, 8/10 and 6–7/10 values cannot be verified against the saved final CSV. Use the verified final table below instead. Our saved probabilities were re-evaluated with the friend’s own detector and matching code. Both include isolated recordings and stories (318 true signs); values average the three people equally. Quality masks/coverage still differ slightly. This is a retrospective threshold sweep, not a newly selected deployment threshold.

| Threshold | Friend: signs caught | Ours: signs caught | Friend: false reactions / routine hour | Ours: false reactions / routine hour |
|---|---:|---:|---:|---:|
| 0.3 | 67.6% | 71.4% | 16.8 | 27.5 |
| 0.5 | 63.5% | 68.9% | 6.0 | 14.6 |
| 0.7 | 51.3% | 54.7% | 4.1 | 10.5 |

“Caught” means detected as a sign; it does not mean the correct sign was named. A threshold is a model-score cutoff, not verified percentage certainty. The hourly rate counts unmatched detections during labelled routine movement, excludes idle/unknown periods and incorrect names during actual signs, and is extrapolated from about 58 measured routine minutes. It is not a count of every wrong home reaction.

## What to say

On the same original participant recordings, correctly named actions improved from about 51% to 56%, and correctly named signs improved from 23% to 37%. The strongest gains are wiping the table, pickup, sit–stand, COOK and HELLO. THANKYOU and several small movements remain weak. At the same detector thresholds, the updated model catches slightly more signs but also produces more false triggers. Continuous use still needs improvement.

The complete P1–P5 isolated dataset, including new seated/cooking examples, has 311/628 correctly named actions (49.5%) and 171/490 correctly named signs (34.9%). Those are a different, broader test set than the matched comparison above.

All calculations use saved predictions. No model was fitted.
