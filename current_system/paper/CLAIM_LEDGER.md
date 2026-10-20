# Paper claim ledger

Updated 19 October 2026. Paths are relative to the repository root. "Verified" means supported by the named artifact; it does not imply an independently validated deployment.

| Claim | Status | Evidence / required wording |
|---|---|---|
| Five real participants, one room, one active participant at a time | Manifest-supported participant count; geometry operator-reported | `handoff/manifest.json`, `paper/evidence/selected_session_log.csv`; no cross-room claim |
| 25 selected takes, 2,050,030 raw CSI rows including QC | Verified | `paper/evidence/verified_dataset_counts.json`; includes rest/ready and 3 empty checks |
| 22 model recordings, 2,010,899 raw rows | Verified | Same; empty-room QC is excluded from model training |
| 12 actions, 14 sign labels | Verified | `paper/evidence/dataset_info.json`, capture protocols |
| Every person has all posture/cooking conditions | FALSE | Only P4/P5 have isolated seated blocks and cooking additions |
| 628 isolated actions / 490 isolated signs / 416 story events | Verified | Saved 1,534 event predictions and annotation exports |
| 34 repeated story runs | Verified | Original labels: 3 templates for P1–P3, 4 for P4/P5; two runs each |
| Arbitrary interleaved recognition was evaluated | Unsupported/misleading | Actual protocol uses scripted SEQ blocks; presentation title is imprecise |
| P2 actions are complete | FALSE | 27 uncovered intervals excluded; capture manifest/coverage tables |
| All annotation times/sign forms are video-verified | NOT established | Cue/operator labels; no completed full alignment/certification shown |
| All participants are native/fluent ISL signers | NOT established | Do not claim without actual evidence |
| Institutional ethics approval / approval number | NOT verified | Old context reports consent; inspect applicable documents and guide requirements |
| Balanced isolated action macro-F1 50.23%, sign macro-F1 33.23% | Verified | `paper/evidence/summary.csv`, mean equally over held-out people |
| 49.52% action / 34.90% sign accuracy | Verified, different metric | 311/628, 171/490 correct pooled isolated events |
| Class plot "correctly named" is F1 | FALSE | Those bars are per-class recall; separate CSV contains precision and F1 |
| Story sign identity 24.71% mean F1 | Verified with ORACLE type/boundaries | Do not call this automatic continuous success |
| 58.17% detected / 18.75% correctly named / 15.38% correct full response | Verified pooled automatic story counts | 121/208, 39/208, 32/208; IoU >=0.10 matching and fold-specific thresholds |
| Approximately 148 false commands per routine hour | Short-duration extrapolation | 50 commands over 1,218.06 measured routine seconds; not all wrong responses and not a one-hour deployment |
| P1 has no correctly named story signs | Verified limitation | `paper/evidence/story_metrics.csv` |
| Tau 0.3/0.5/0.7 table is all-five story performance | FALSE | Separate P1–P3, isolated+story ±1 s sweep, 318 signs; average participant rates |
| Tau is calibrated percent certainty | FALSE | It is a model score cutoff |
| Five-person exhaustive nested cross-validation was run | FALSE for retained balanced run | Fixed one-person validation per outer fold, then refit on four and test fifth |
| Test participant excluded from each fold's training/validation | Verified for saved fits | Fold selection metadata + audit; overall design was revised after earlier test results |
| Final all-five deployment model has a new independent score | FALSE | Refit on all P1–P5; use held-out folds for performance evidence |
| Balanced retained model is a CNN–ExtraTrees deployment fusion | FALSE | Final model card action tree weight is zero; continuous path is CNN-only |
| Multimodal CSI+IMU fusion was trained/evaluated | NOT done for current collection | Separate older wearable work does not establish synchronized fusion |
| Context-dependent response is learned intent inference | FALSE | `intent()` is predefined rules over predicted sign/recent action context |
| Real-time/zero-look-ahead recognition | Unsupported | Centered 4/6 s windows; offline prototype |
| Novel architecture beats prior systems | NOT established | Changes in data, preprocessing and selection confound saved-system comparisons |
| Better than friend on every task/class | FALSE | Some story metrics and weak classes regress; matched report gives scope |
| 96% / 71% / macro-F1 0.71 old figures support this paper | PROHIBITED as current evidence | Old pilot/invalid DATA_COMBINED history; replace or exclude |
| New IMPROVED notebook produced stronger results | NOT established | Notebook delivered, no verified execution/output provided |
| Formal privacy guarantee / deployed accessible home | Unsupported | Camera-free CSI inference is supported; privacy proof and user deployment are not |
| No prior wireless system studies accidental gesture activation | FALSE as broad literature claim | WiSee explicitly studies false detections/startup sequences |
| Conference submission/acceptance or guide-approved WiP target | NOT done | Recommendation and format discussion only |

## Rules for new claims

Every main numeric claim needs dataset/slice, metric, averaging, support and exact source. A new claim of improvement needs comparable experiments; a causal explanation needs evidence beyond confusion counts. New validation/rejection settings must be selected without using the current outer test results as an untouched development set. Confirm on independent recordings after freezing the design when possible.
