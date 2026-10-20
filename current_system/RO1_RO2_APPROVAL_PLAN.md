> HISTORICAL PROPOSED PLAN. Read Adhi_To_Amrith_Context.md for actual capture/training. Proposed participant/day/session counts, classes and fusion work below were not all executed; the old DATA_COMBINED score is not reportable current evidence.

# RO1 and RO2 Approval Plan

## Purpose

This is the data-collection and research plan to approve before collecting the next dataset. It turns the guide's meeting feedback into one controlled progression:

1. RO1: one person present at a time, WiFi CSI only, with isolated, sequential, and interleaved activity-sign streams.
2. RO2: the same streams captured simultaneously with WiFi CSI and one wearable IMU, followed by synchronised multimodal fusion.
3. Only after RO2 is complete: extend to more than one active person.

"Single person" means one person is active in a recorded trial. It does not mean training and testing on only one human participant. The full study must involve several participants and hold out people, days, and sessions during evaluation.

## Evidence from the Current Folder

The current `DATA_COMBINED` CSI collection contains 15 labels: baseline empty, baseline stand, eight activity labels, and five greeting-style gesture labels. It has five participant files (`combined_person1.csv` through `combined_person5.csv`), each with packet timestamps plus `type`, `label`, and `subject_id`. In each file, every label is one contiguous time block; for example, all `bend_down` samples occur before all `drink_water` samples, which occur before all `eating` samples. Label changes provide sequential boundaries, but there are no repeated, randomised, or deliberately interleaved episodes.

Consequences:

- The data is a **sequential labelled stream**, not an interleaved dataset.
- It can support signal inspection and a preliminary activity-versus-gesture baseline. The current presentation reports macro F1 = 0.71 for this broad binary task.
- It must not be used as the principal evidence for interleaved recognition or temporal generalisation: every class occurs only once in the same capture order for a participant.
- A model could exploit capture order, session drift, or a long uninterrupted recording rather than human motion. The new data must randomise trial order and repeat every class in every session.
- Preserve the code, split definitions, normalisation procedure, trained weights, and raw classification report for the reported F1 before citing it in a paper. Those reproducibility artefacts are not currently stored alongside the combined dataset.

The earlier binary pilot also showed that action versus stillness is too easy to establish model novelty: a one-feature motion-energy threshold matched or exceeded the deep model. RO1 must therefore use fine-grained activity and ISL classes, plus the harder sequential and interleaved-stream tests.

## Standard References and Scope

### Activity reference

Use UT-HAR as the WiFi-CSI activity benchmark reference for collection and reporting. It provides seven daily activities: lie down, fall, walk, pick up, run, sit down, and stand up. It is a reference for activity taxonomy and WiFi evaluation, not a requirement to duplicate its hardware or every class.

For the present inclusive-smart-home task, collect five task-relevant ADLs:

| ID | Activity label | Controlled performance |
|---|---|---|
| A1 | drink_water | Lift cup, take a sip, return cup. |
| A2 | eat | Move spoon/hand from plate area to mouth, return. |
| A3 | write | Write a short fixed phrase on paper. |
| A4 | use_phone | Pick up phone, bring to ear or operate it for the prescribed interval. |
| A5 | sit_stand | Sit down and stand up from the same chair. |

Keep `idle_stand` and `empty_room` as controls, not headline activity classes. The team may retain `bend_down` as a sixth activity only if it can be collected consistently and has a matched ISL sign approved by the guide.

### ISL reference

Use Indian Sign Language, not ASL. The lexical source is the official Indian Sign Language Research and Training Centre dictionary. The academic dataset reference is INCLUDE, which contains 263 isolated ISL word signs. SignFi is valuable as a WiFi-CSI methodology comparator, but it uses ASL and must not be presented as the language source for this work.

Proposed ISL vocabulary for approval:

| ID | ISL concept to verify in the official dictionary | Matched ADL |
|---|---|---|
| G1 | WATER or DRINK | A1 drink_water |
| G2 | FOOD or EAT | A2 eat |
| G3 | WRITE | A3 write |
| G4 | PHONE or CALL | A4 use_phone |
| G5 | SIT or STAND | A5 sit_stand |

Before capture, a fluent ISL signer or ISL instructor must confirm the exact video reference, gloss, handedness, start/end pose, and repetitions for each sign. Do not invent or alter a sign from online images. This verification is part of the dataset protocol.

## What We Will Recognise

The study has two label levels:

1. **Fine-grained label:** A1-A5, G1-G5, `idle_stand`, and `empty_room`.
2. **State label:** `activity`, `ISL_gesture`, `idle`, and `empty`.

The fine-grained task tests whether similar physical movements can be separated. The state task connects directly to the smart-home use case: distinguish non-communicative daily action from deliberate communication.

## Stream Types

| Stream type | Meaning | Example | Why it matters |
|---|---|---|---|
| Isolated | One labelled action or sign in a trial. | `A3 write` | Establishes basic class separability. |
| Sequential | Different labels occur one after another; no resumption. | `A1 -> G3 -> A4` | Tests transitions in a continuous stream. |
| Interleaved | An activity is interrupted by a gesture, then the original activity resumes. | `A3 -> G5 -> A3` | Directly tests the guide's complex/interleaved requirement. |

Interleaved does **not** mean two movements performed simultaneously by two people. That is reserved for the later multi-person phase. Every transition must be explicitly annotated with start and end timestamps.

### Approved sequence templates

Use a randomised template list, not one fixed order:

| Template | Stream | Example |
|---|---|---|
| S1 | sequential | `idle -> A1 -> G3 -> A4 -> idle` |
| S2 | sequential | `idle -> A2 -> G4 -> A5 -> idle` |
| I1 | interleaved | `idle -> A1 -> G2 -> A1 -> idle` |
| I2 | interleaved | `idle -> A3 -> G4 -> A3 -> idle` |
| I3 | interleaved | `idle -> A4 -> G1 -obser4> A4 -> idle` |
| I4 | interleaved | `idle -> A5 -> G3 -> A5 -> idle` |

The final table must be signed off by the guide and ISL reviewer before collection. A balanced Latin-square/random schedule should change the order of templates across participants and sessions.

## RO1 Data Collection Protocol

### Hardware and environment

- One active person in the sensing area; no bystanders.
- Use one **validated fixed channel** during RO1; do not mix channel hopping with the first core experiment. The current 15-class dataset records Channel 1 for every packet, so use Channel 1 only after confirming from transmitter/receiver logs that both radios were genuinely parked there (the receiver documentation warns that a missing hop loop can also leave a default Channel-1 label). Otherwise choose the validated fixed channel and record it in every manifest row.
- Use the controlled two-USRP setup only after its packet rate, frequency, and CSI logging are verified. If using the older passive setup for a pilot, label it explicitly as passive and do not pool it with active data.
- Fix transmitter/receiver geometry, antenna height, chair, desk, cup, phone, and writing surface. Photograph and measure the layout.
- Run the existing capture gates before every session: device identity, channel/frequency, rate at least 50 CSI rows/s, motion/wiggle test, no saturation, and a capture-quality report.

### Participants and sessions

- Pilot: 1 participant, 1 day, to validate protocol and labels.
- Full RO1 collection: at least 5 participants, 2 days per participant, 2 sessions per day.
- One active person per recording, but evaluate leave-one-person-out and leave-one-day-out.
- Each isolated class: 25 valid repetitions per participant across days.
- Each sequence template: 10 valid repetitions per participant across days.
- Re-record failed trials immediately; retain a quality log and never silently delete failures.

### Annotation contract

Every trial must have a row in a master manifest with:

`trial_id, participant_id, date, session_id, setup_id, modality, stream_type, template_id, event_id, fine_label, state_label, start_us, end_us, channel, packet_rate, operator, quality_status, notes`.

The present `session_logger.py` is suitable for timestamping discrete events, but it must be extended or used repeatedly so every event inside a sequence has its own start/end record. Raw data filenames must contain the participant, date, session, stream type, and trial identifier.

## RO1 Preprocessing and Models

### Preprocessing owner tasks

1. Run capture-quality checks and reject low-rate, NaN, clipped, or MAC/channel-mismatched captures.
2. Convert complex CSI to amplitude only unless coherent multi-antenna phase is validated.
3. Remove the known truncated last CSV row before analysis.
4. Apply a documented detrending/denoising method chosen only from training data.
5. Resample each labelled event onto a shared time grid; record interpolation proportion and reject excessive gaps.
6. Segment both fixed windows and full continuous streams. Keep all windows from one trial in the same data split.

### Modelling owner tasks

1. Baselines: motion-energy threshold, random forest on handcrafted time/frequency features, and a simple temporal CNN/GRU.
2. Main model: an end-to-end temporal model that outputs a label sequence for continuous trials, not just a majority label for a whole file.
3. Compare all-subcarrier and selected-subcarrier inputs only when selection is learned inside each training fold.
4. Never use random window-level train/test splitting. Split by participant and session/trial group.

### RO1 metrics

- Fine-grained and state-level macro F1, precision, recall, and confusion matrix.
- Leave-one-person-out result as the main person-generalisation result.
- Leave-one-day/session-out result as the main temporal-generalisation result.
- Segment F1 and boundary tolerance for continuous streams.
- Edit score or sequence accuracy for sequential/interleaved templates.
- Explicit `activity <-> ISL gesture` confusion rate.
- Comparison against every baseline; do not lead with accuracy alone.

## RO2 Multimodal Plan

RO2 starts only after RO1 has a validated dataset and baseline. The minimal defensible multimodal configuration is **WiFi CSI plus one wearable IMU**. Ambient sensors can be added later; do not promise an ambient modality in the paper until the actual hardware and labelled data exist.

| Modality | Role | Raw data | Required work |
|---|---|---|---|
| WiFi CSI | Privacy-preserving room-scale motion sensing | complex CSI per packet | Controlled capture, QA, denoising, temporal segmentation. |
| Wearable IMU | Fine arm/body motion and participant-linked signal | 3-axis accelerometer and gyroscope | Device placement, calibrated rate, timestamped logger, filtering. |
| Optional ambient | Context only, not a substitute for identity | PIR/door/object events | Add only after installation, timestamping, and data-quality checks are ready. |

RO2 repeats the same participants, vocabulary, and sequence templates as RO1. It adds a modality-ablation study:

1. CSI only.
2. IMU only.
3. CSI + IMU late fusion.
4. CSI + IMU feature-level temporal fusion.

This makes the paper's fusion claim testable rather than assumed.

## Synchronisation Algorithm for RO2

Do not fuse data by merely matching row numbers or device clock times. Use this procedure:

1. **Common event protocol:** The experiment laptop is the reference clock. It records the schedule and event labels in microseconds.
2. **Three synchronisation gestures:** at the start, middle, and end of each session, perform a short, prescribed wrist/arm shake visible in both CSI motion energy and IMU acceleration magnitude.
3. **Clock model:** Estimate `t_CSI = a * t_IMU + b`, where `b` is offset and `a` accounts for drift, from the three anchor events.
4. **Signal refinement:** Within a small search range, maximise normalised cross-correlation between CSI motion energy and IMU acceleration magnitude around the anchors. Save the estimated lag and residual alignment error.
5. **Resampling:** Convert both streams to the same analysis grid, for example 50 Hz. Keep original timestamps as well as the aligned time grid.
6. **Quality gate:** Reject or re-record a session if anchor residuals exceed a pre-approved tolerance. The exact tolerance is decided from the pilot distribution, not guessed later.
7. **Fusion:** Start with late fusion of calibrated per-modality probabilities. Move to feature-level temporal fusion only when the alignment quality and late-fusion baseline are reported.

## Team Ownership

| Owner | Primary responsibility | Deliverable before approval |
|---|---|---|
| Adhikkesh | Research protocol, master manifest, paper introduction | Approved vocabulary, sequence table, consent/log template, introduction draft. |
| Adithya | ISL vocabulary validation and wearable capture | Official reference video list, wearable placement/rate plan, IMU logger test. |
| Amrith | CSI capture and quality assurance | Fixed-geometry sheet, active/passive setup verification, per-session QA report. |
| Gowreesh | Preprocessing and synchronisation | Denoising/segmentation specification, event-label schema, sync pilot result. |
| Rishiikesh | Modelling and evaluation | Baseline/model protocol, grouped split implementation, metric/report template. |

Gowreesh and Rishiikesh jointly own the final model and evaluation. All members must review the paper and take part in data collection. If the team prefers different people in these roles, retain the deliverables and reassign the owners in the approval meeting.

## Immediate Schedule

### Week 1: approval package, no bulk data

1. Freeze the exact five ADLs and five ISL signs after ISL reviewer validation.
2. Produce the one-page activity/sign reference table and six sequence templates.
3. Run an active-CSI capture and wearable logging pilot for one participant.
4. Measure rate, gaps, signal visibility, sync lag, and annotation feasibility.
5. Show the guide the protocol, a raw CSV row, event labels, one CSI trace, one IMU trace, and the synchronisation result.

### Weeks 2-3: RO1 full collection and analysis

1. Collect isolated, sequential, and interleaved CSI trials under the approved protocol.
2. Run QA after every trial and create immutable manifests.
3. Train grouped baselines and the temporal model; report unseen-person and unseen-day results.

### Weeks 4-5: RO2 collection and fusion

1. Repeat the same protocol with CSI and wearable IMU together.
2. Verify timestamp alignment and compare CSI-only, IMU-only, late fusion, and feature fusion.
3. Freeze the dataset, experiment table, error analysis, and figures.

### Start paper writing now

Write the introduction and literature review in parallel with collection. Do not wait for final accuracy.

Paper structure:

1. Introduction: privacy-preserving smart-home problem; why confusing intentional ISL gestures with daily action matters; contribution and research questions.
2. Literature review: WiFi CSI HAR, WiFi sign recognition, ISL resources, multimodal HAR/fusion, and the missing interleaved activity-sign setting.
3. Dataset and protocol: controlled hardware, ISL verification, sequential/interleaved templates, annotation, sync algorithm.
4. Methods and evaluation protocol.
5. Results, ablations, failure analysis, and limitations.

The first paper should cover RO1 + RO2 only. Multi-person concurrent activity is the next paper/phase, not a claim in this paper.

## Approval Checklist

- [ ] Exact ISL signs verified by an ISL-qualified reviewer and linked to official dictionary references.
- [ ] Exact activity performance instructions approved.
- [ ] Sequential and interleaved templates approved.
- [ ] One-person-at-a-time scope explicit.
- [ ] Participant/day/session and repetition counts approved.
- [ ] Active versus passive capture setup clearly declared.
- [ ] Event-level annotation manifest tested.
- [ ] CSI/IMU timestamp alignment pilot completed.
- [ ] Preprocessing, split, baselines, metrics, and roles approved.
- [ ] Paper scope restricted to RO1 + RO2.

## References to Cite in the Paper and Approval Slides

1. S. Yousefi et al., “A Survey on Behavior Recognition Using WiFi Channel State Information,” IEEE Communications Magazine, 2017. Use UT-HAR activity taxonomy/benchmark context.
2. Y. Ma et al., “SignFi: Sign Language Recognition Using WiFi,” Proceedings of the ACM on IMWUT, 2018. Use as WiFi-CSI sign-recognition methodology comparison; it is ASL, not ISL.
3. A. Sridhar et al., “INCLUDE: A Large Scale Dataset for Indian Sign Language Recognition,” ACM Multimedia Asia, 2020. Use as the academic ISL dataset reference.
4. Indian Sign Language Research and Training Centre, Government of India, Indian Sign Language Dictionary. Use as the authoritative source for the executed ISL signs.
5. A. A. Aguileta, R. Brena, O. Mayora, E. Molino Minero, and L. A. Trejo, “Multi-Sensor Fusion for Activity Recognition—A Survey,” Sensors, 2019. Use for the synchronisation and fusion literature.
