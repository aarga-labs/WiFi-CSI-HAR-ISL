# Audit of the six-minute Kaggle run

The downloaded results.zip passed CRC checks. All five outer-fold completion markers and the all-five deployment model are present. The run completed; it was not terminated by the 300-second watchdog.

| Held-out result | Macro F1 |
|---|---:|
| isolated / activity | 0.3546 |
| isolated / sign | 0.1806 |
| isolated_seated / activity | 0.1102 |
| isolated_seated / sign | 0.0957 |
| stories_oracle_boundaries / activity | 0.3823 |
| stories_oracle_boundaries / sign | 0.1284 |

## Verified problems

1. Every epoch used 32 batches irrespective of training-set size. The final all-five model received only 384 optimizer updates and 98,304 sampled windows, against 62,807 available eligible windows. These draws were balanced and with replacement; they were not 98,304 distinct trials.
2. Refits shortened the cosine learning-rate horizon to the selected epoch count. For example, choosing epoch 10 from a 28-epoch selection run refitted with a 10-epoch schedule. That changed the learning-rate trajectory instead of preserving the selection recipe.
3. Six-second candidates were absent, so selection could not choose the friend's selected six-second action/detector window. The prior search compared only four-second residual and multiscale candidates.
4. Generalization is also weak. CPU forward-only diagnostic samples show strong training-person recognition and much weaker unseen-person recognition. These are diagnostic window accuracies, not replacement event-level scores.
5. Only one of 1,534 fully covered action/sign/story events had no usable model window. The poor overall metrics cannot be explained by the quality mask removing most events.

## Diagnostic sign-recognition samples

Balanced random diagnostic windows, known central event type, 768 draws per set; no retraining or optimization.

| Outer test | Training-person sign accuracy | Test-person sign accuracy |
|---|---:|---:|
| P01 | 99.1% | 15.3% |
| P02 | 66.4% | 23.9% |
| P03 | 90.9% | 22.2% |
| P04 | 83.8% | 15.3% |
| P05 | 69.0% | 16.5% |

## Class-level observations

Walk has pooled isolated F1 0.804. Chop_food has F1 0.000; TOILET has F1 0.000. Several seated/hand activities are confused with eat; HUNGRY, CALL, TELEVISION and TOILET are often predicted as PAIN.

Longer training is one correction, not evidence that the generalization problem is solved. The revised notebook tests local waveform normalization, relative rather than fixed-amplitude noise, separate role selection, and two-seed refits. Validation alone determines those choices.

The original friend results and this run use different class coverage and evaluation details. They should not be described as a controlled before/after experiment. The revised model must be evaluated in Kaggle; final confirmation needs a fresh session/person after design choices are fixed.

## Local checks performed

Archive CRC, completion metadata, saved histories, class metrics, confusion counts and saved checkpoint shapes were inspected. Existing saved weights were run for CPU inference on diagnostic samples from their original train/test participant groups. No optimizer step, classifier fitting or model training was performed on the laptop.
