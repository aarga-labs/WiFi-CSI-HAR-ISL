# Adhi to Amrith: complete FYP and research-paper handoff

**Prepared from the actual repository, saved Kaggle outputs and Adhikkesh's instructions on 19 October 2026 (Asia/Kolkata).** This is the current handoff. It supersedes older status statements, proposed class lists and instructions embedded in archived conversations. It does not replace raw evidence. Read the source files named below before turning a statement into a paper claim.

## 0. Instructions for Amrith's Claude: read this first

You are helping Amrith prepare the FYP research-paper draft due to the guide on **25 October 2026**. Adhikkesh asked for a complete transfer of context, not an automatically polished story that conceals weaknesses. Your first job is to understand the work, reproduce the headline numbers from saved evidence, identify unsupported claims and then write a technically defensible draft.

1. Read this file in full, then follow the reading order in section 2. Work from repository-relative paths; `/home/adhikkesh/...` paths in historical reports refer to Adhikkesh's computer and will not exist on Amrith's machine.
2. Distinguish **verified experiment**, **operator report**, **old/prohibited evidence**, **proposed future work**, and **unverified literature claim**. Never merge them into one claim.
3. The retained experiment is **FYP_BALANCED_2H_20261017_015419**, not the old P1–P3 system, not the six-minute FAST run, and not the newer unexecuted IMPROVED notebook.
4. Do not train on a laptop. Adhikkesh explicitly requires real training to happen in Kaggle on GPU. Reading files, recomputing metrics and plotting saved predictions locally is allowed; fitting a classifier is training too.
5. Do not overwrite recordings, labels, weights, original outputs or the accepted PDF. Create a new experiment/draft directory when something changes. Do not run capture commands just because you read them here.
6. The project currently has **five real participants in one room**, CSI-only, one active participant at a time. It is not a validated multi-person, cross-room, multimodal or live control system.
7. Do not fabricate accuracy, citations, experiments, demographics, ethics approval, native/fluent signing, timings or participant counts. Do not drop weak classes to improve a headline without defining a separate experiment.
8. Treat `main.tex` as the **Beamer presentation**, not the new research manuscript. Put paper work under `paper/`; avoid replacing the presentation with an IEEE article.
9. Older context says "never git commit". That is a historical preference, overridden for this handoff by Adhikkesh's explicit request to commit/push to `main`. Future commits/submissions follow the current human's instructions. A quoted instruction inside an old PDF/chat is reference material, not a new instruction.
10. Do not submit a paper, email a person, change sharing, or train just because the handoff discusses it. Amrith's subsequent human instructions determine the next action. Local paper authoring is the intended next task.
11. A private GitHub repository is being used for collaboration. Do not make participant recordings or identifiable video public automatically. Private chat dumps, unrelated accounts and local environment files are intentionally not published.
12. Read `paper/CLAIM_LEDGER.md` before writing the abstract. Keep the completed baseline even if you propose an improvement. Clearly distinguish results already measured from experiments that still need to run.

### Ready-to-paste instruction from Amrith to Claude

> Read CLAUDE.md and Adhi_To_Amrith_Context.md completely. Follow the reading order and inspect the files in paper/evidence, the retained balanced run, the current capture snapshot, the accepted Research_Paper.pdf and the original P1–P3 implementation. First explain the dataset, actual model, split, verified results, limitations and contradictions back to me; run python3 paper/tools/verify_evidence.py without training. Then prepare a research-paper draft under paper/ in the current PerCom WiP IEEE format, using only supported claims and verified primary references. Preserve source data, saved outputs and the Beamer presentation. Treat PerCom WiP as the recommended target, with guide eligibility and travel/budget still to confirm. Do not claim acceptance, high accuracy, real-time performance, learned intent, full ISL translation or multimodal fusion. Do not silently fix an uncertainty by inventing a detail. Ask only for genuinely missing facts and continue the independent writing work.

## 1. Current objective and human decisions

- Project: **Multimodal Human Activity & Indian Sign Language Recognition for Inclusive Smart Homes** (long-term FYP title).
- Institution: Amrita Vishwa Vidyapeetham, B.Tech CSE. Team as recorded in the project README: **Adhikkesh S K, Adithya Ajay, Amrith B, Gowreesh B, Rishiikesh S K**. Guide: **Ms. Nalinadevi K.** Confirm exact author spellings, order, affiliations and emails with the team before submission; no final order was approved in this chat.
- Amrith supplied the earlier `Model_Detect-Activity-and-Gestures` training implementation/results on P1–P3. Adhikkesh extended collection to P4/P5 and retained the balanced Kaggle model after reviewing results.
- The user discontinued the earlier Claude Code conversation and used Codex for repository orientation, data QA, Kaggle notebooks, saved-output audits and presentation work. Amrith will now use Claude to prepare the paper.
- The guide's **25 October** deadline is the internal draft submission, not the PerCom submission deadline. No final conference requirement/template had been specified by the guide in this chat.
- Original ambition was a Q1 journal submission by end October; that is a historical goal, not current proof of readiness or a confirmed target.
- Latest recommendation discussed with Adhikkesh: **IEEE PerCom 2027 Work-in-Progress (WiP)**. The user then requested its format/rules and this handoff. Do not represent guide approval of WiP or an actual conference submission as completed.
- Location preference: **India first; overseas only if online presentation is allowed**. PerCom requires travel to Goa. Fee/funding and whether a WiP/workshop-proceedings paper satisfies FYP rules remain unresolved.
- User wants actual evidence, understandable graphs, natural technical writing, exact file paths and usable artifacts. They do not want fabricated improvements, repeated unnecessary confirmations, laptop training, or vague promises about runtime/acceptance.

## 2. Reading order and source authority

### First pass: enough to understand and start drafting

1. `Adhi_To_Amrith_Context.md` — current integrated context and corrections.
2. `paper/README.md`, `paper/CLAIM_LEDGER.md`, `paper/PERCOM_WIP_RULES.md` — writing workflow, supported claims, venue requirements.
3. `Kaggle_P1_P5/balanced_results_audit_20261017/AUDIT_FINDINGS.md` — completed benchmark and limitations.
4. `paper/evidence/summary.csv`, `fold_metrics.csv`, `story_metrics.csv`, `verified_dataset_counts.json`, `all_out_of_fold_predictions.csv` — actual numbers. Run the read-only verifier.
5. `Research_Paper.pdf` — two-page abstract/introduction first accepted by the guide. It is an image-only PDF: inspect the rendered pages. `paper/reference_notes/Research_Paper_accepted_OCR.txt` is a convenience OCR reading aid, not an authoritative transcription.
6. `capture_snapshot/wifi_csi_capture/pilot_tools/protocol.py`, `protocol_p45.py`, `cue_session.py` and `P04_P05_COMMANDS.md` — actual collection and label logic, including later additions.
7. `Kaggle_P1_P5/balanced_2h/START_HERE_BALANCED.md`, `fyp_fast.py`, `fast_runner.py`, `fast_prepare.py` — the executed balanced implementation and orchestration. Read the source archived in the completed run when describing that exact experiment.
8. `Model_Detect-Activity-and-Gestures/README.md`, `RESULTS.md`, `final_system.py`, `preprocess.py`, `dense.py`, `cnn.py`, `stream_eval.py` — earlier baseline and differing evaluation conventions.
9. `Kaggle_P1_P5/friend_comparison_20261017/Friend_vs_Our_Results.md` and `paper/evidence/Comparison_For_Mam.md` — comparisons, metric definitions and why screenshots are not independent evidence.
10. `main.tex`, `current_impl/`, `presentation_current/OVERLEAF_README.md` — supervisor presentation, graphs, counts and recorded-video excerpts.

### Second pass: history and research motivation, with caveats

- `Full_Context_7_Oct_26.md`: detailed October 2–7 handoff and collection history. Status saying P4/P5 unrecorded is now obsolete. Its "three SEQ stories" and fabricated-data warning are important. It is not current model evidence.
- `FYP_FULL_CONTEXT.md`: older September overview, literature notes, IMU/fall-detection work and long-term architecture. Proposed features and high scores here must not be imported into the current paper as completed results.
- `RO1_RO2_APPROVAL_PLAN.md`, `DATA_COLLECTION_PLAN.md`, `3_Month_Plan.pdf`, `Revised_Action_Plan_Phase1.docx`: historical proposals, not actual final recording manifests. Their proposed schedules/classes/session counts are not what was fully collected.
- `Papers/`, `Latex/`, `ImagePi/`: reference PDFs, old paper fragments and baseline notebooks. Read original references before citing. File names/summaries alone are insufficient.
- `Reports/`, `Review/`, `others/Works/`: earlier review deliverables and prototypes; not evidence that current fusion/real-time/multi-person goals are achieved.
- `SEM7_Rubrics_Instructions/`: official local course documents. Research-based and technical-enrichment rubrics include paper/draft activities; verify which category and publication requirement the guide applies. Do not infer a guaranteed publication requirement from a generic rubric.

**Authority order for factual contradictions:** actual raw manifest/labels + exact experiment source + saved predictions/metrics > audit with reproducible checks > current integrated handoff > presentations > historical plans/chat summaries. Presentation wording can be wrong.

## 3. Repository map and what a pull contains

| Path | Meaning / use |
|---|---|
| `CLAUDE.md` | Automatic entry pointer for Claude Code |
| `Adhi_To_Amrith_Context.md` | Complete human/AI handoff |
| `paper/` | New paper workspace; evidence, claim ledger, rules, reading aid and portable verification |
| `paper/evidence/labels/` | All 22 annotation CSVs from the verified real P1–P5 archive |
| `handoff/` | Dataset manifest, archive delivery/checksums, capture/model provenance and download helper |
| `Kaggle_P1_P5/balanced_results_audit_20261017/run/FYP_BALANCED_2H_20261017_015419/results/` | Exact retained metrics, predictions, fold choices, histories, model card and final two inference checkpoints |
| `Kaggle_P1_P5/balanced_2h/` | Executed balanced notebook and its source |
| `Kaggle_P1_P5/fast_2h/`, `results_audit_20261017/` | Earlier completed FAST run and diagnostic audit; historical comparator |
| `Kaggle_P1_P5/robust_2h/` | Newer IMPROVED notebook delivered later; no verified result from it is present |
| `Kaggle_P1_P5/FYP_P1_P5_Kaggle_Training.ipynb` | Original extensive/nested training notebook; not the retained run |
| `Model_Detect-Activity-and-Gestures/` | Friend's original P1–P3 code, CSV results and figures, now normal files in the outer repo |
| `capture_snapshot/wifi_csi_capture/` | Portable snapshot of the separate capture repository, including dirty working changes/P4–P5 additions as found during handoff |
| `pilot_tools/` | Older outer-repo recording-tool mirror; use capture snapshot to understand actual later P4/P5 protocol |
| `current_impl/` | Presentation graphs and three short MP4/frame-PDF animations plus setup JPEG |
| `presentation_current/` | Figure/deck builders, evidence exports, backups, preview PDFs; some old files are superseded |
| `main.tex` | Current maroon Beamer slides, NOT a research article |
| `Research_Paper.pdf` | Original guide-accepted abstract/introduction; preserve unchanged |
| `session_log_phase1.csv` | Full take history, including aborted takes, not a ready-to-train manifest |
| `session_log_rain_check.csv` | Small rain-check QA session log; not a training recording |
| `paper/evidence/selected_session_log.csv` | Exact 25 selected takes in the verified dataset archive |

Large raw recordings/full checkpoint archives are private release assets, not Git blobs. Read `handoff/ASSETS.json` and `handoff/README.md`. A normal pull supplies paper evidence, annotation files, source, saved predictions, graphs and the retained small inference weights. Optional release downloads recover full training states and raw CSI. No access to Adhikkesh's Downloads directory should be necessary to write the draft.

Original nested capture repo `wifi_csi_capture/` is intentionally still local/separate and ignored; its portable snapshot is committed. The nested model repo Git metadata was preserved locally under `_backup_git/` while importing its working files normally. No submodule checkout is required to read the friend's code.

## 4. Research question and paper direction

### Core problem

A smart home responding to non-verbal commands must distinguish ordinary motion from deliberate communication. Detecting movement alone is insufficient: lifting a cup should not accidentally cause a WATER command. The current research question is:

**Can one Wi-Fi CSI link distinguish everyday activities from a selected sign vocabulary, identify the movements, and find/name signs in continuous activity–sign recordings for a participant excluded from training?**

Separate three tasks:
1. Movement type: idle / activity / sign.
2. Identity: one of the action or sign labels, often evaluated with true event boundaries/type supplied.
3. Continuous recognition: automatically locate signs, name them and map them to a rule-defined response.

Suggested working title: **From Isolated Trials to Continuous Streams: Activity and Sign-Gesture Recognition Using Wi-Fi CSI.** This is a proposal, not a fixed submission title.

### Defensible contribution being developed

- A documented five-person single-link capture protocol containing activities and selected signs in separate and shared recordings.
- A reproducible temporal pipeline evaluated on held-out participants.
- An empirical measurement of the difference between known-boundary recognition and automatic story recognition.
- Error analysis and a controlled improvement, if actually executed and properly validated.

This is currently a preliminary empirical/prototype study. A CNN trained on collected data is not automatically an algorithmic novelty. Five people/one room and moderate accuracy do not establish general-purpose accessibility or dependable smart-home control. Low accuracy alone is not a publishable negative result either: useful explanations need controlled evidence.

### Proposed additional work, NOT completed

1. Review weak-class video/label intervals (THANKYOU, WATER, TOILET, TV remote, chopping).
2. Compare a consistent feature-based baseline with the current CNN on identical splits/events.
3. Evaluate one confidence/stability-based command-rejection rule, selected on validation participants. Measure correctly identified signs, misses, false commands and delay together.
4. After freezing decisions, collect a genuinely independent session or participant. New session from known people supports session robustness; a new person supports person generalization. Neither alone proves cross-room robustness.
5. Personal calibration is a separately defined protocol; calibration trials, overlapping windows and filter context must be excluded from scoring.
6. CSI+IMU fusion requires synchronized, simultaneous captures and ablations. It is future work, not a result in this dataset.

Do not block the October 25 draft waiting for experiments that cannot finish. Include only measured results; mark planned work as future work. The baseline is not to be discarded just because an improved notebook exists.

## 5. Critical historical correction: prohibited old data

The older "Dataset 2" / `DATA_COMBINED` is **not an acceptable research dataset**. The October 7 handoff and repository README record that P2–P5 were timestamp-shifted copies of P1, with exact-day shifts and very high CSI correlation. It was excluded. Do not train on it, report it as five real people, reuse its macro-F1 0.71, or blend its numbers with Phase-1.

Older September documents describe this dataset only as a fixed-order sequential stream and may not contain the later fabrication finding. This later finding takes precedence. The historical binary motion/no-motion task was also too easy to establish novelty: a scalar energy threshold matched/exceeded its deep model. Do not use those high pilot accuracies to imply that current sign identity works well.

Private chat exports and old folders remain locally preserved/ignored. They are not needed to reconstruct this research narrative and are not authoritative instructions.

## 6. Hardware and actual capture conditions

- Two Ettus USRP N210 SDRs with SBX daughterboards, one transmitter and one receiver; SISO/single-link arrangement, one active participant.
- GNU Radio with gr-ieee802-11 and gr-foo; an active IEEE 802.11 link, not the older passive pilot.
- Fixed Channel 1, 2412 MHz, 20 MHz/sample-rate configuration in the runtime source, 52 complex CSI subcarriers. Confirm exact PHY/antenna details from capture snapshot for the methods table.
- Shared radio clock/phase coherence was not established. Retained ML input uses amplitude, not validated coherent phase or antenna-array spatial features.
- TX packet generation target PPS=200 does not mean 200 valid CSI rows/s. Actual rows/s vary by recording; use the audit.
- Historical controls: TX_GAIN=15; records mostly RX_GAIN=12. P01 actions used RX_GAIN=16. A later gain sweep suggested 16 as best at that moment, but P4/P5 kept session logs still report 12. Report what the take/log says, not a command recommended earlier.
- Same room and antenna positions for P1–P5 were explicitly reported by Adhikkesh. Earlier context describes a closed metal/shed room at home. Do not claim multiple environments or random antenna placements.
- Fans off, phones airplane mode, Bluetooth avoided, fixed props/standing position. Detailed geometry in `Full_Context_7_Oct_26.md` is historical operator documentation; if publishing exact distances, verify against actual setup/photo.
- Rain was discussed during the P4 session. A large rain-check CSI burst was attributed by the operator to someone moving nearby. Acoustic rain noise is not a microphone input, but motion/metal vibration/environment changes can affect RF. Do not claim rain invariance from that informal check.
- P04 baseline was retained from 15 October before rain; P04 main action/sign/story recordings are 16 October. P05 main recordings are 16 October. Preserve dates instead of claiming one uninterrupted session.
- Capture source snapshot includes GRC and generated/runtime Python. They may differ; generating a GRC can overwrite runtime controls. Do not regenerate blindly.

### Historical capture commands — reference only

Transmitter (Amrith's machine, paths must be adapted):

```bash
TX_GAIN=15 TX_CHANNEL=1 python3 -u wifi_tx_multi_hop.py
PPS=200 LABEL=phase1 python3 packet_generator.py
```

TX should be parked on Channel 1. Receiver experiments use `wifi_rx.py`; recording orchestration uses `record_part.sh` / `record_p45.sh`. `gain_sweep.sh` is for measurement, not a prerequisite for writing. Do not operate radios or start collection without a current human instruction.

## 7. Collection protocol: intended vs actually completed

P1/P2/P3 were collected on 2 October; P4 baseline on 15 October; P4/P5 principal parts on 16 October. P1–P3 have the original ten action labels and standing sign blocks, with actions/signs also present in stories. They do **not** have separate isolated seated blocks. This does not mean the `sitstand` action or seated story movement was absent.

P4/P5 preserve the original protocol and add:
- `chop_food` and `stir_pot`, using cold/safe props; no third extra cooking action.
- Separate seated action block: drink, eat, answerphone, tvremote, wipetable, chop_food, stir_pot.
- Separate seated sign block for all fourteen signs.
- Two cooking steps added to the meal story and a new all-seated S-SEQ story.

The original action target was ten repetitions/class, fall five. P4/P5 action block has 115 events and seated block 70. Sign blocks have five repetitions/class = 70 events each. P2 truncation reduces actual eligible support.

### Vocabulary (exact model order)

Actions (12): `walk`, `sitstand`, `pickup`, `lightswitch`, `drink`, `answerphone`, `eat`, `wipetable`, `tvremote`, `fall`, `chop_food`, `stir_pot`.

Signs (14): `HELLO`, `THANKYOU`, `LAMP`, `FAN`, `TELEVISION`, `COOK`, `WATER`, `HOT`, `HUNGRY`, `TOILET`, `CALL`, `HELP`, `PAIN`, `ACCIDENT`.

These are 26 identity labels plus a separate three-state head; do not call the system "29 mutually exclusive action classes". Sign recording duration is nominally four seconds; action durations vary around four–six seconds. Fixed model windows are a different concept from cue interval duration.

### Stories: important terminology correction

The original guide feedback removed INT templates before collection. Actual scripts are **SEQ**, usually activity blocks followed by sign blocks, not arbitrary interleaving or simultaneous multi-person actions.

- M-SEQ: meal — walk/light switch/sit–stand/eat/drink, followed by meal signs; P4/P5 insert chop/stir before sitting.
- T-SEQ: TV/phone — walk, sit–stand, TV remote, answer phone; HELLO, TELEVISION, HOT, LAMP, CALL, TOILET; stand and leave.
- C-SEQ: cleaning/fall — walk, wipe, pick up; FAN/HELP; walk/fall; HELP, PAIN, ACCIDENT, CALL on the mattress.
- S-SEQ: P4/P5 only, seated — wipe, chop, stir, eat, drink; HELLO, HUNGRY, COOK, HOT, WATER, HELP, THANKYOU.

Each available template has two runs/person: 3 people × 3 × 2 + 2 people × 4 × 2 = **34 runs**. There are **416 action/sign steps**, split 208 + 208. Sync/idle markers are not included in that total. Read the exact step lists from the snapshot instead of reconstructing them from this prose.

The presentation currently calls a slide "Interleaved Stories". Treat that as imprecise presentation wording. The paper should say **scripted continuous activity–sign sequences/stories** and describe their actual order. Do not claim validated arbitrary interleaved recognition.

## 8. Dataset counts and units

Source of truth: `paper/evidence/verified_dataset_counts.json`, selected session log, raw-row tables, raw archive manifest.

| Recording block | Files | Raw CSI rows |
|---|---:|---:|
| Main actions | 5 | 844,426 |
| Seated actions | 2 | 173,297 |
| Standing signs | 5 | 457,408 |
| Seated signs | 2 | 127,209 |
| Stories/scripts | 5 | 354,465 |
| Still-person baselines | 3 | 54,094 |
| Empty-room QC | 3 | 39,131 |
| **Retained collection total** | **25** | **2,050,030** |
| **Participant/model recordings, excluding empty QC** | **22** | **2,010,899** |

These counts include rest/ready intervals. They are not two million independent training examples. Five participants remain five independent people.

- Fully covered isolated action intervals: **628 trials, 416,836 raw packets**.
- Fully covered isolated sign intervals: **490 trials, 222,570 raw packets**.
- Actions in original main blocks: 488 events; extra seated actions: 140.
- Standing signs: 350 events; extra seated signs: 140. Every sign has pooled support 35 (25 standing + 10 seated).
- Story events: 416. Total saved eligible action/sign event predictions: **1,534** (628 + 490 + 416).
- The raw-row count per class is in `isolated_raw_rows_by_class.csv`; pooled class precision/recall/F1 are in separate performance tables. Never use a packet count as a trial count.
- Three baseline recordings are P1/P4/P5. P2/P3 missing baselines must not be filled with synthetic copies. Empty checks are day-specific QC references, not five participant examples.
- Do not count both `.csv` and `.csv.gz` copies as different takes. Aborted/no-packet takes and `discarded/` are excluded from the selected dataset.

## 9. Schema, labels, quality and video

Raw CSV: 107 columns = `Packet`, `Timestamp_us`, `Channel`, then `SC0_Re`, `SC0_Im` through `SC51_Re`, `SC51_Im`. There is no fine label embedded in the raw radio schema. Samples in `paper/evidence/actual_CSI_sample.csv` are actual values, not invented screenshot data.

Label CSV schema includes `pid,mode,posture,trial,label,type,intent,home_action,context,script_id,run,step,t_start_us,t_end_us,source,note`. Labels and CSI share the receiver's clock. Isolated events come from cue intervals; story steps use operator keypress boundaries. Claps were planned/logged as sync markers. These are not automatically verified video annotations.

Quality facts:
- P02 action CSI stops before labels end: **27 uncovered action intervals excluded**. The friend's original output includes one partial lightswitch interval not in the shared-event comparison.
- P01 baseline has substantial gaps in older QA; P01 actions RX gain differs from most recordings.
- P04 T-SEQ run 1 HOT contains an approximately **470 ms** packet gap. Full start/end coverage alone does not establish adequate within-event quality.
- P04/P05 audits passed structural checks; some individual events have low row rates. "All structural checks passed" does not establish correct sign performance or annotation alignment.
- One eligible event in the saved balanced evaluation has no usable windows; its unavailable prediction counts as a miss. Do not drop missing predictions from the denominator to inflate results.
- A P4 baseline from the preceding day was accepted by the operator under the same reported geometry; it remains a different dated take.

Video/annotation work:
- Video tools such as ELAN were discussed; labels were copied/zipped for possible annotation. A completed video-based relabelling/alignment pass was **not demonstrated**.
- The verified raw-data ZIP contains no full phone-video collection. The repository now includes one real setup JPEG and three short MP4 excerpts in `current_impl/media/`.
- Those clips are not enough to certify every action/sign or establish linguistic correctness. Filename `collection_sign_cook_seated.mp4` does not independently prove the exact gesture.
- ISL references include INCLUDE/ISLRTC and emergency-sign resources. Historical protocol entries explicitly say "verify" for several signs. Do not claim all participants are fluent/native ISL signers or that an ISL-qualified reviewer certified the signs unless evidence is supplied.
- Older context reports signed participant consent, but forms/ethics approval were not independently inspected in this handoff. Confirm with the team before making an approval statement; do not invent a committee/approval number.

## 10. Data packaging and recovery

Verified real archive: `FYP_Phase1_P01_P05_verified.zip`.
- Size: **901,985,586 bytes**.
- SHA256: **74259c5718d512ffa9cd3bdf63f150badcd6887e0cd2b35f780602e6e13a165c**.
- Contains `phase1/`: 22 participant takes, 3 empty checks, 22 label CSVs, selected session log, receiver logs, applicable QA reports and `manifest.json` with file hashes.
- Preprocessing manifest fingerprint (SHA256 of that JSON): **f01651df3c4b758f3cbec5dd742669b4f0605a9f11c24162aecd662949dede62**. This is NOT the ZIP SHA256.
- Excludes discarded takes, duplicate gzip copies, rejected fabricated DATA_COMBINED and full phone videos.
- A previously expanded Google Drive `data` folder was reported corrupted. Do not rely on it just because it exists. The verified ZIP is the reproducible baseline.
- Uploading a ZIP and extracting in Kaggle is supported. Private Kaggle Dataset attachment avoids private Drive authentication/quota issues. Actual Drive upload completion was not independently verified; no usable Drive file ID was supplied in this handoff.

For optional large-asset recovery use `python3 handoff/fetch_assets.py` and its help. The private release is `https://github.com/aarga-labs/FYP/releases/tag/handoff-2026-10-19`. Amrith must have repository access and authenticate his own GitHub CLI; no credentials are stored here. See `handoff/ASSETS.json` for exact filenames, hashes and extraction locations. The initial handoff publication is complete only when remote release assets and pushed main are verified, not just when this document is written.

## 11. Model history: do not mix experiments

| Stage | What happened | How to use it |
|---|---|---|
| Historical binary/old-data pilots | Motion/no-motion and activity-vs-gesture numbers appeared in older reports | Historical chain validation only; prohibited old-data claims are excluded |
| Friend P1–P3 | Original residual-CNN/classical/streaming/calibration work in model folder | Earlier saved-system comparator, with its own data/split/preprocessing/matching |
| Initial full Kaggle notebook | Broad nested workload; a background run appeared stalled after >6 hours | Not the retained final result; do not promise GPU use alone makes it fast |
| FAST attempts and completed FAST run | Early failures/logs were reviewed; a completed roughly six-minute run saved all-five models but was weak | `results_audit_20261017/` is historical diagnostic evidence |
| **BALANCED completed** | **FYP_BALANCED_2H_20261017_015419**, all five tests and all-five refit complete | **Retained benchmark for the draft** |
| IMPROVED / robust_2h delivered | More elaborate roughly 100–115-minute planned notebook | No verified execution/results supplied; do not cite its proposed architecture as the current trained model |

The user explicitly said to keep the trained balanced model. No new model training was authorized as part of preparing this repository handoff.

The run's current `results/run_completion.json` records **41.18 measured minutes**. Earlier presentation text rounds the run differently (about 41.4 min); prefer the completion JSON and identify what timing includes. Filename "2_Hours" is a software-budget target, not an observed two-hour run.

## 12. Exact retained method and evaluation

Read the archived `source/fyp_fast.py`, `results/fyp_fast.py`, `training_config.json`, each `P0x/selection.json`, `complete.json`, `validation_selection.csv`, `validation_thresholds.csv`, and deployment `model_card.json`. Source hashes/provenance are in the handoff manifest. Some functions/classes are redefined later in the file; the later balanced implementations override earlier base definitions. Reading only the first `CSIModel` or `load_deployment` definition is incorrect.

### Preprocessing

Complex CSI → per-subcarrier magnitude → logarithm → timestamp-based interpolation to 100 Hz → second-order Butterworth band-pass 0.3–18 Hz using a causal SOS filter → decimation to 50 Hz. Gaps >100 ms are masked; severe gaps >250 ms reset filtering and trigger an approximately three-second warm-up mask. Use exact source for edge cases. Avoid inventing phase processing/PCA/spectrogram input for this run.

Fitted scaling uses training participants. No participant identifier, filename, true story context or event duration is a classifier input. Windows are fixed-length and centered, so despite a causal filter the complete recognizer is **offline/noncausal**. At a 0.2-second prediction hop, overlapping windows are not independent samples.

### Architecture and optimization

Candidates: residual 1D CNN with 4 s input, residual 1D CNN with 6 s input, and `normalized4` with 4 s input. Residual blocks use increasing dilations and pooling. The normalized candidate replaces batch normalization with group normalization, normalizes the window's energy while retaining log energy/temporal-difference energy features, and predicts a 3-state output plus a 26-class identity output.

Training defaults: AdamW, learning rate 0.001, weight decay 0.01, batch 256, up to 100 epochs, validation every four epochs, early stopping, cosine schedule, gradient clipping and mild relative-noise/amplitude/subcarrier augmentation. Class/state/participant balancing uses sampling with replacement; a scaled epoch draw budget does not guarantee every distinct window is seen once. The saved final all-five models each received 12 epochs × 246 batches = 2,952 updates. Seeds are 17 and 29.

GPU execution: Kaggle T4 ×2 with independent workers/GPU-resident batches. Preprocessing and ExtraTrees are CPU operations. All saved model training ran on Kaggle, not during the laptop audits. No GPU execution is implied merely because a notebook was syntax-checked locally.

### Actual split design

Five outer tests, one held-out person each. Within each outer fold, one **fixed validation participant**, not a full four-way inner cross-validation:

| Outer test | Fixed validation person for candidate selection |
|---|---|
| P01 | P04 |
| P02 | P05 |
| P03 | P01 |
| P04 | P02 |
| P05 | P03 |

Initial candidate fitting uses the other three participants. Select detector/action/sign roles, stopping epochs, threshold and optional action-fusion weight on validation. Refit the selected networks on all four non-test participants using two seeds; then score the fifth. Do not describe the original expensive plan's twenty inner splits as executed balanced training. Preparation tests that checked twenty possible splits are validation tooling, not evidence those twenty model fits were run.

Macro-F1 is calculated over labels with actual support in that participant/slice, then averaged equally over participants. Some held-out people have ten supported actions and others twelve; absent cooking classes are not fabricated as support. Show common/expanded coverage and support explicitly.

### Deployment refit

Final roles are all `normalized4`; seeds 17 and 29; all P1–P5 used for fitting. Final detector threshold is approximately 0.6. Selected ExtraTrees action-fusion weight is **zero**. Trees were evaluated/trained, but the final deployed predictor is not a CNN–ExtraTrees fusion win. Continuous inference is CNN-based. The final all-five refit has **no new independent test score**; held-out folds provide the reported evidence.

The protocol was revised after inspecting earlier benchmark outputs. Thus, although each recorded fold excludes its test person during fitting/selection, this is not a pristine untouched final benchmark for every human design decision. A fresh recording/session/person is needed for stronger confirmation after freezing the design.

## 13. Verified results: metric definitions are part of the result

Primary table from `paper/evidence/summary.csv`:

| Evaluation | Mean participant macro-F1 | Participants | Events |
|---|---:|---:|---:|
| Isolated actions, expanded available data | 50.23% | 5 | 628 |
| Isolated signs, standing + seated | 33.23% | 5 | 490 |
| Actions in original main blocks | 53.04% | 5 | 488 |
| Standing isolated signs | 36.54% | 5 | 350 |
| Isolated seated actions | 19.39% | 2 | 140 |
| Isolated seated signs | 19.95% | 2 | 140 |
| Story actions, true boundaries/type supplied | 52.37% | 5 | 208 |
| Story signs, true boundaries/type supplied | 24.71% | 5 | 208 |

Separately, pooled isolated correct-count **accuracy/recall**:
- Actions: **311/628 = 49.52%**.
- Signs: **171/490 = 34.90%**.

These are not the 50.23%/33.23% mean macro-F1 values. The presentation's per-class "correctly named" bars are **recall**, not F1. Use `isolated_activity_per_class.csv` and `isolated_sign_per_class.csv` for precision/recall/F1; use correct-count tables for human-readable recall.

Examples: action recall walk 46/46=100%, pickup 40/48=83%, TV remote 6/67=9%, chopping 4/40=10%. Sign recall COOK 25/35=71%, THANKYOU 1/35=3%, WATER and TOILET 4/35=11%. Pooled F1 ranks differ because false positives affect precision. The complete per-class tables are appended below and stored as CSVs.

### Automatic continuous story evaluation

From `paper/evidence/story_metrics.csv`, pooled counts:
- True signs: **208**.
- Matched detections: **121 = 58.17%** of true signs.
- Correct sign names: **39 = 18.75%** of true signs.
- Correct complete sign/context rule-defined responses: **32 = 15.38%** of true signs.
- Predicted commands: **239**.
- Unmatched commands during measured routine activity: **50 over 1,218.06 seconds (~20.30 minutes)**, approximately **147.8 per routine hour** when extrapolated. This is a short-duration estimate, not a measured hour of home use. It excludes other categories of incorrect output, so it is not "all wrong reactions".
- P1 has zero correctly identified story signs in this evaluation. Do not hide it behind an aggregate.

Automatic matching is one-to-one overlap/IoU >=0.10 with validation-selected thresholds per fold. Sign detection does not require the name to be right; identity and full response are successively stricter. Known-boundary fine classification supplies the event type/bounds and is an oracle-style supportive test, not the end-to-end result.

### Fixed-threshold table shown to the guide: separate protocol

This is **P1–P3 only**, isolated + stories, **318 true signs**, using the friend's detection/matching implementation and common source rules. It is not the all-five story-only result above.

| Threshold | Mean detected-sign recall | Mean false triggers / measured routine hour |
|---|---:|---:|
| 0.3 | 71.38% | 27.53 |
| 0.5 | 68.87% | 14.62 |
| 0.7 | 54.72% | 10.45 |

One-second smoothing/minimum run, gap merging and ±1 s matching; approximately 58 measured routine minutes. Values average participant rates, rather than silently pooling all durations. Higher threshold catches fewer signs and produces fewer routine false detections. A threshold is a score cutoff, not calibrated certainty. Do not say tau=0.7 means "70% sure". Approximate screenshot claims such as 9/10 and one wrong reaction/hour were not verified by these outputs.

Sources: `paper/evidence/threshold_comparison_same_detection_rules.csv`, `our_threshold_details_by_person.csv`, `our_threshold_details_by_source.csv`, `comparison_method.json`, `Comparison_For_Mam.md`. Prefer the consistent all-five main protocol in the paper; the secondary threshold sweep needs its own scope label if used.

## 14. Intent/context: what is implemented

Context anchors use the most recent predicted action in a two-minute history: eat/drink/chop/stir→meal; TV remote/phone→TV; wipe/pickup→cleaning; fall→after_fall. State confidence gating and exact update logic are in `commands()`.

Intent is a **predefined mapping**, not learned semantic understanding. I0 means no command; I1 device control; I2 needs/comfort; I3 alerts/assistance; I4 interaction. HOT during meal maps to kitchen hazard; otherwise HOT maps to cooling. HELP after fall maps to emergency; otherwise caregiver notification. Other signs map to fixed predefined responses.

Do not present intended home actions as actual actuated devices or a deployment with Deaf residents. Do not equate a label called "intent" with evidence of a human's latent mental intent. The reported end-to-end value scores correctness against the protocol-defined mapping.

## 15. Friend's baseline and comparison limits

Original P1–P3 code uses different preprocessing (including whole-file/noncausal operations and per-file noise-floor normalization), 10 action labels/14 signs, its own nested selection and ±1 s streaming matching. It also has one/two-repetition calibration experiments. Calibrated results use labelled test-person examples and must not be called zero-shot/unseen-person-without-adaptation results.

Matched original P1–P3 evaluation covers **684 shared action/sign events**:

| Mean macro-F1 | Friend final zero-shot | Retained balanced system |
|---|---:|---:|
| Isolated actions | 48.6% | 54.9% |
| Isolated signs | 20.8% | 34.3% |
| Story actions, oracle type/bounds | 60.5% | 55.2% |
| Story signs, oracle type/bounds | 20.6% | 20.8% |

This is not a controlled architecture ablation. The friend fits on two other people for each original test; the balanced system fits on four, adding P4/P5, and changes preprocessing/selection/augmentation. Use "saved-system comparison on shared test events," not "our architectural innovation caused the gain." Some tasks/classes regress.

The friend's final calibrated sign F1 is about 29.8%; an earlier 38% figure belongs to a different earlier CNN experiment. The friend's high streaming event F1 combines isolated/story detection and does not require sign identity; it cannot be compared directly with our story-only identity success. Read the detailed comparison before using any older number.

The user's presentation request said not to include references to "my friend's signs" in the slides. The paper can describe an earlier baseline professionally and credit its authors/source; do not call team members' work an external state of the art or hide the different data support.

## 16. Research_Paper.pdf: accepted direction, not current validated manuscript

The PDF is two pages (abstract, keywords, introduction), generated earlier and accepted by the guide as an initial direction. Preserve it. It describes old binary tasks, 8 activities/5 signs/2 baseline classes, recurrence plots/ResNet-18 and scores 96%, 71%, macro-F1 0.71. Those are **not the current balanced model/data results** and must be replaced or excluded.

Other issues to fix:
- Placeholder citations `[CITE: ...]` are not references. Check each claim against original publications.
- It asserts that no reported WiFi system distinguishes everyday motion from deliberate communication. This is too broad: earlier gesture systems such as WiSee already study accidental activation/false detections. Narrow the contribution to the exact protocol/question we evaluate.
- Its SignFi/Wi-SL descriptions and split labels need rechecking. A dataset collected from multiple users is not necessarily a strict leave-one-user-out test; do not call 86.66% unseen-user performance without reading the original protocol. A search also found a Wi-SL paper dated 2020, while the PDF cites a 2023 Wang source—resolve the exact reference instead of silently substituting one.
- Claims about market growth, hearing-loss prevalence and camera privacy percentages need primary sources or can be removed. Do not retain unsupported statistics to make the introduction sound important.
- Camera-free inference is an accurate system property; a formal privacy guarantee was not demonstrated.
- No simultaneous CSI+IMU dataset/fusion experiment exists for the retained result. The long-term project title must not turn into an unsupported paper title/abstract claim.

## 17. Presentation and other completed artifacts

`main.tex` is a 16:9 maroon Beamer presentation with compact RO banners; 43 frames including two unnumbered opening frames. Current implementation covers numbered 21–26 and 32–36. Two old dataset slides were replaced; result slides were added.

`current_impl/` has vector PDF and PNG graphs: actual dataset excerpt, per-action recall, per-sign recall, fixed-threshold tradeoff, story recognition. The graph source reads saved outputs and does not train. It now resolves the checkout and threshold table portably.

Media: `current_impl/media/collection_setup.jpeg`, three short MP4s named `collection_action_pickup`, `collection_sign_cook_seated`, `collection_story_meal`, corresponding `_frames.pdf` and poster JPEGs. Original native rate 25/3 fps; frame counts 25/31/30, durations 3.00/3.72/3.60 s. Main Beamer embeds frame-PDF animations using official `animate.sty` version 2024/10/14, `method=widget`, autoplay+loop. A downloaded PDF shown in Brave was static because its built-in viewer does not support this method; desktop Firefox 130+ or Adobe Reader is the prescribed test. Interactive playback was not independently exercised here.

The 11-slide animated implementation preview was compiled and visually checked with no text overflow. Local full-deck layout checks substituted missing **older** external images only for diagnostics. Do not treat those diagnostic PDFs as the actual complete presentation or claim every older image exists in this checkout. Keep original Overleaf assets. `presentation_current/update_deck.py` rebuilds from an older backup and can erase animation edits; do not run it blindly. Use `add_video_animations.py` carefully and inspect its backup assumptions.

Paper figures should be static, legible, reproducible PDF/PNG plots, not PDF JavaScript animations. Do not embed our collection clip faces in a publication without checking the applicable consent.

## 18. Conference discussion and current target

PerCom WiP is a recommendation based on topic, India location and work maturity. It was not chosen because it guarantees acceptance. A WiP/workshop publication must be acceptable under the guide's FYP rules, and travel/full-registration funding must be confirmed.

As checked on 19 October 2026:
- PerCom WiP: **4 pages including all figures/tables/references**, IEEE two-column, US Letter, PDF, **single-blind with authors included**, HotCRP. Submission November 17, 2026 23:59 AoE; notification January 8, 2027; final version February (exact WiP date unannounced). Goa March 8–12, 2027. One full registration and in-person presentation required. Publishes in PerCom Workshops proceedings/IEEE Xplore, not the main-conference full-paper proceedings. Fees unannounced.
- PerFail (PerCom workshop): November 17; negative results/lessons with a useful supported finding, not ordinary bugs or merely poor accuracy; 6–7 pages; in-person/full registration.
- PeRConAI (PerCom workshop): November 17; resource-constrained/pervasive AI, 6–7 pages. Adding measured inference/memory evidence may improve fit. No automatic acceptance for being a student project.
- ICACCS 2027 Coimbatore: organizer's indexed page listed November 28 submission, March 11–12 conference, student fee around INR 8,500 and virtual presentation allowed. Direct site access was intermittent and some dates/edition text were inconsistent. Verify live 2027 CFP/sponsorship/requirements before committing to it.
- NCC 2027 IISc Bengaluru: October 31 firm deadline; six pages, double-blind, February 17–20 event; relevant but short preparation time and demanding evidence.
- IDCIoT 2027 Ottapalam: October 29 deadline, January 21–23 event, listed student fees INR 11,400–12,400; short preparation window. Organizer's publication statements are not a guarantee of acceptance/indexing.
- IMWUT/UbiComp: excellent long-term topical fit, but a **journal** with Feb 1/May 1/Nov 1 cycles, not an ordinary direct conference submission. Later February/May preparation may be more sensible; mapping to a particular UbiComp year depends on publication timing.
- SenSys 2027 second cycle: Oct 29 abstract / Nov 5 paper AoE. Six-page short route exists for visions, experiences, tools/datasets/benchmarks; still needs originality/impact. Requires in-person attendance apart from exceptional approved cases.
- MobiSys 2027: Nov 27 abstract / Dec 4 paper AoE; Emerging Ideas route exists; Ho Chi Minh City. General remote presentation permission was not verified.
- CVPR 2027: Nov 10 registration / Nov 16 paper AoE; currently poor topical fit without a clear vision/pattern-recognition contribution. It is not literally limited to camera HAR, but its existence does not make it appropriate for our engineering study.

Do not submit the same manuscript to several venues at once. This is a shortlist, not a set of authorized submissions. Dates are time-sensitive; recheck official sources before acting. See `paper/PERCOM_WIP_RULES.md` for sources and exact target rules.

## 19. Draft plan and writing rules

Suggested four-page structure:
1. Introduction and focused related work: problem, specific research question, contribution.
2. System/data protocol and recognition method: hardware, actual collection, annotation, processing/model.
3. Evaluation and preliminary results: held-out folds, support, one consistent primary protocol, main figure/table.
4. Discussion/limitations, ongoing work/conclusion, acknowledgment as appropriate, references.

Suggested visuals: one setup/pipeline figure, one compact isolated-vs-continuous result figure, one main results/support table. Large per-class charts can be supplemental working material; do not exceed four pages or shrink template fonts/margins to fit everything. The conference's rules take priority over our suggested outline.

Write in plain, precise language. Explain the question before the architecture. Do not claim "novel" without identifying what is new. Explain what each metric counts and what information the model receives. Report weak classes and P1 failure alongside strong classes. Use supported effect descriptions, not inferred causes. A wider training set and changed method are not a clean architecture comparison.

No model is "very good" merely because the user previously said to keep it. That decision retained the best audited benchmark then available. Current continuous results are weak, and a strong regular paper would require stronger evidence. A short/WiP submission still needs a defensible contribution.

No final author order, paper title, guide approval of WiP, registration budget, accessible overseas-online option or institutional ethics statement was established. Ask Amrith for those if they become necessary for the draft/submission, without blocking independent evidence-based writing.

IEEE's current published policy requires acknowledging AI-generated article content (including text/figures/images/code), identifying the system and its scope. Editing/grammar-only assistance is generally outside that requirement. Keep an accurate assistance record; do not invent a claim that everything was human-authored. Conference policies can change; verify before submission.

## 20. Primary reference map and literature cautions

- SignFi authors' site: https://yongsen.github.io/SignFi/ ; DOI https://doi.org/10.1145/3191755 . Segmented WiFi sign traces, different hardware/antenna setup and split protocol. The site includes instance-level cross-validation example code; don't assume every quoted multi-user score is LOSO.
- WiSee original author paper: https://ubicomplab.cs.washington.edu/pdfs/whole-home-gesture.pdf ; author site https://wisee.cs.washington.edu/ . It explicitly considers false activations/startup gesture sequences, so broad "no prior system" claims fail.
- INCLUDE and ISLRTC: retrieve original dataset paper and exact official dictionary clips for the performed signs. Protocol naming alone does not certify linguistic validity. Do not use SignFi's ASL vocabulary as an ISL reference.
- Widar3.0, ImgFi and joint WiFi activity/localization: original PDFs under `Papers/` and `Latex/`; cite exact publication metadata and comparable evaluation settings. A public-dataset result is not a score of this private Phase-1 experiment.
- Recent continuous-activity and generalization literature was discussed as research leads, not an exhaustive novelty search. Do not claim the gap is globally unique based on a few search results.

Use a literature matrix with task, sensor/links, people/sessions/environments, split, segmentation assumptions, metrics and main limitation. Distinguish ordinary interaction gestures, selected lexical signs, and full continuous sign-language translation.

## 21. Completion checklist for Claude before returning a draft

- [ ] Current handoff read; historical status contradictions resolved explicitly.
- [ ] `python3 paper/tools/verify_evidence.py` passes from Amrith's checkout without raw-data download or training.
- [ ] All key claims trace to `paper/CLAIM_LEDGER.md` and evidence rows; all-five vs P1–P3 scopes remain distinct.
- [ ] Actual split described as fixed validation + outer held-out participant, not exhaustive nested CV.
- [ ] Raw packet count, trial count, person count and macro-F1/accuracy/recall are not mixed.
- [ ] Scripted SEQ stories not misrepresented as arbitrary interleaving or multi-person recognition.
- [ ] Rejected fabricated dataset and old pilot scores excluded from the new experimental claims.
- [ ] No new experiments, real-time capabilities, fusion, native signing or ethics approval invented.
- [ ] Proposed improvement/results-free notebook marked unexecuted unless actual outputs are provided.
- [ ] References checked against original sources; citation placeholders removed or explicitly marked unresolved during drafting.
- [ ] IEEE four-page Letter conference layout respected; authors included for WiP single-blind review.
- [ ] Figures legible and paper source separated from Beamer source.
- [ ] Limitations and failed classes reported; conclusions match the evidence.
- [ ] Human author/order/affiliation and guide's publication eligibility checked before submission.
- [ ] AI assistance disclosure follows applicable policy and actual use.
- [ ] Source compiled and final PDF visually inspected before calling the draft complete.

## 22. Reproducible context-transfer commands

Existing checkout (preserve local changes before pulling):

```bash
git switch main
git pull --ff-only origin main
python3 paper/tools/verify_evidence.py
```

Fresh clone:

```bash
git clone git@github.com:aarga-labs/FYP.git
cd FYP
python3 paper/tools/verify_evidence.py
```

Optional raw/checkpoint downloads require GitHub CLI authentication and private repository access:

```bash
python3 handoff/fetch_assets.py --list
python3 handoff/fetch_assets.py --asset dataset
python3 handoff/fetch_assets.py --asset balanced_checkpoints
```

The downloader verifies SHA256 and stores assets under ignored `handoff/assets/`; it does not train or extract. Read its instructions before restoring any archive. For paper drafting, ordinary pull + evidence verifier is sufficient. Do not use `git reset --hard` or overwrite Amrith's existing work to obtain this handoff.

## 23. Scope of this transfer

This file transfers project-related decisions, source/evidence locations, experimental facts, caveats, venue discussion and next actions. It is not a raw transcript of unrelated private chats or hidden assistant/system instructions. The full older FYP context files remain available for detail. Everything newly described as verified is backed by files; future work remains future work. If a needed fact cannot be established from these sources, record the uncertainty and ask the team rather than filling it with plausible prose.

## 24. Automatically exported per-class evidence

The tables below are generated from committed saved outputs. Counts are per fully covered isolated event; rows are raw packets inside those label intervals. Pooled F1 differs from participant-mean F1. See CSVs for full precision/recall and per-person results.

### Actions

| Label | Correct / trials | Recall | Pooled F1 | Raw rows | People |
|---|---:|---:|---:|---:|---:|
| walk | 46/46 | 100.0% | 91.1% | 33,371 | 5 |
| sitstand | 31/48 | 64.6% | 63.9% | 33,576 | 5 |
| pickup | 40/48 | 83.3% | 80.8% | 35,094 | 5 |
| lightswitch | 25/48 | 52.1% | 51.0% | 23,817 | 5 |
| drink | 29/67 | 43.3% | 43.3% | 46,554 | 5 |
| answerphone | 22/67 | 32.8% | 32.8% | 46,741 | 5 |
| eat | 45/67 | 67.2% | 52.6% | 46,401 | 5 |
| wipetable | 33/67 | 49.3% | 49.3% | 44,783 | 5 |
| tvremote | 6/67 | 9.0% | 11.2% | 39,134 | 5 |
| fall | 10/23 | 43.5% | 48.8% | 16,512 | 5 |
| chop_food | 4/40 | 10.0% | 16.3% | 25,679 | 2 |
| stir_pot | 20/40 | 50.0% | 44.0% | 25,174 | 2 |

### Signs

| Label | Correct / trials | Recall | Pooled F1 | Raw rows | People |
|---|---:|---:|---:|---:|---:|
| HELLO | 17/35 | 48.6% | 35.1% | 16,019 | 5 |
| THANKYOU | 1/35 | 2.9% | 4.3% | 15,697 | 5 |
| LAMP | 14/35 | 40.0% | 43.1% | 15,689 | 5 |
| FAN | 16/35 | 45.7% | 49.2% | 15,956 | 5 |
| TELEVISION | 7/35 | 20.0% | 23.0% | 15,641 | 5 |
| COOK | 25/35 | 71.4% | 65.8% | 15,792 | 5 |
| WATER | 4/35 | 11.4% | 11.1% | 16,152 | 5 |
| HOT | 11/35 | 31.4% | 32.4% | 16,097 | 5 |
| HUNGRY | 20/35 | 57.1% | 47.6% | 16,140 | 5 |
| TOILET | 4/35 | 11.4% | 17.4% | 15,875 | 5 |
| CALL | 8/35 | 22.9% | 25.8% | 15,815 | 5 |
| HELP | 14/35 | 40.0% | 37.8% | 15,782 | 5 |
| PAIN | 18/35 | 51.4% | 36.7% | 16,051 | 5 |
| ACCIDENT | 12/35 | 34.3% | 36.4% | 15,864 | 5 |
