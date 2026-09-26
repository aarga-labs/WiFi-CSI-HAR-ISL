> HISTORICAL PROPOSAL. Actual vocabulary and completed coverage are in Adhi_To_Amrith_Context.md and paper/evidence. Do not report this proposed larger class set or unverified literature-gap claims as completed work.

# Data Collection Plan — Multimodal HAR & ISL Recognition (WiFi CSI, 2× USRP N210)

The plan anchors every class to a published source, pairs signs with look-alike activities on purpose, and records the same activity content in both sequential and interleaved form so the only difference between the two is the structure.

## 1. Standard references

| Role | Reference | Why it fits |
|---|---|---|
| Complex and interleaved activities | CASAS interweaved ADL study (Singla, Cook & Schmitter-Edgecombe, 2009–10) | The standard definition of "interleaved" |
| Atomic actions near signs | OPPORTUNITY (Roggen et al., 2010), mid-level gestures | Short hand/arm actions like "drink from cup" and "toggle switch" |
| RF feasibility and protocol | XRF55 (Wang et al., IMWUT 2024) | The largest WiFi/RF action dataset |
| ISL emergency signs | Adithya V. & Rajesh R., Data in Brief 2020 | ISL signs for alerts |
| ISL home and greeting signs | INCLUDE / INCLUDE-50 (Sridhar et al., ACM MM 2020) | The most-cited ISL word dataset |

CASAS is the right anchor for three reasons:
- Its activities come from clinical tools. The 8 ADLs were selected because they appear in clinical questionnaires, and difficulties in them help identify people who struggle to live independently.
- It defines interleaving the way the guide means it. Participants first did each activity separately, then did the set again, ordering and interleaving the activities however they liked; many did several at once (e.g., talking on the phone while watching the DVD and watering plants).
- CASAS used motion, door and item sensors. Those are the same sensor types as Pipeline 1, which makes the RO4 ambient fusion story straightforward.

XRF55 is the RF-side justification: its 55 actions were selected from 19 RF sensing papers and 16 video action recognition datasets.

For ISL, the advantage is local. The emergency dataset's signs follow the ISL dictionary published by the Faculty of Disability Management and Special Education (FDMSE), Ramakrishna Mission Vivekananda University, Coimbatore. Contact them for a fluent signer to validate participants' signing. That one step makes the ISL claim credible to reviewers.

## 2. Class set: 7 atomic + 8 complex activities + 9 ISL signs

### Atomic activities (5–10 s each)
From OPPORTUNITY and basic ADLs; several overlap with Dataset 2 so that data can still be used for pretraining.
- A1 Walk across the link
- A2 Sit down / stand up
- A3 Pick up an object from the floor
- A4 Drink from a cup
- A5 Toggle a light switch
- A6 Answer the phone (lift it to the ear)
- A7 Fall, onto a crash mat

### Complex activities (30–90 s each)
The CASAS eight, adapted to one room. (Original CASAS tasks: fill medication dispenser, watch DVD, water plants, answer the phone, prepare birthday card, prepare soup, clean, choose outfit.)
- C1 Fill a pill organizer
- C2 Watch TV (seated, using the remote)
- C3 Water 3 plants
- C4 Phone conversation
- C5 Write a card
- C6 Prepare instant noodles or tea at the counter
- C7 Sweep and dust
- C8 Select and fold an outfit

### ISL signs (9)
- Emergency signs: Help, Pain, Call, Doctor, Hot, Accident (from the emergency dataset, whose eight words were accident, call, doctor, help, hot, lose, pain, thief).
- Home and greeting signs: Fan, Lamp, Hello (INCLUDE-50 includes Fan and Lamp under Electronics and Hello under Greetings).

Smart-home role of each sign:
- Hello = wake gesture
- Fan, Lamp = device control
- Hot = context cue
- Help, Pain, Doctor, Call, Accident = caregiver alerts

Keeping Hello also gives continuity with Dataset 2.

### Deliberate confuser pairs
Treat these as hypotheses. Check each sign's form against the dictionary videos, then keep only the pairs that are actually close in the pilot CSI.

| Sign | Look-alike activity |
|---|---|
| Call | Answer phone (A6), phone conversation (C4) |
| Lamp | Toggle light switch (A5) |
| Fan | Dusting (C7) |
| Hot | Drinking (A4), eating (C6) |
| Hello | Dusting or reaching motions |
| Accident | Fall (A7), a semantic pair |
| Doctor | Standing still or pill organizer (C1) |

Doctor is a hard case: it is the only one of the eight emergency words that is not a dynamic gesture, so it tests whether low-motion signs are detectable at all over CSI.

Record half of each participant's sign repetitions seated and half standing. Seated signing next to seated activities (TV, writing) is where the model will actually struggle.

## 3. Recording structures

For every script, record a sequential version and an interleaved version with the same activity content. That matched design lets us claim the difference comes from interleaving and nothing else.

- Isolated: cue beep, 3 s still, action, 3 s still, repeated. XRF55 had each participant perform each action 20 times; use that as the repetition standard.
- Sequential (SEQ): a continuous stream in which each activity finishes before the next starts, with natural transitions and no rest.
- Interleaved (INT): an activity is paused, another is done, and the first resumes. Signs are embedded mid-activity.
- Free (CASAS second pass): the participant gets task cards and 3 sign cards, and orders and interleaves them however they like.

### Scripts
SEQ scripts have no interruptions. INT scripts contain interruptions, embedded signs, and one concurrent segment (INT-2).
- SEQ-1 (morning): Walk in → Toggle switch → Prepare meal → Drink → Fill pill organizer → Sit, watch TV
- SEQ-2 (chores): Sweep/dust → Water plants → Select outfit → Write card
- INT-1 (kitchen): Prepare meal → sign HOT → phone rings → answer and converse → resume meal → drink
- INT-2 (living room): Watch TV → sign FAN (seated) → phone conversation while TV is still on → sign LAMP → toggle switch
- INT-3 (emergency): Water plants → sweep → pause for pill organizer → resume sweep → fall on the mat → seated signs HELP, PAIN, DOCTOR

## 4. Per-participant protocol

Split each participant into 2 sessions of ~75 minutes, on different days and parked on different channels. Rotate channels 1, 6 and 11 across participants for day and channel diversity.

| Block | Volume | Time |
|---|---|---|
| Empty room + standing-still baseline (start and end of each session) | — | ~8 min |
| Sync marker (3 claps + stomp) at start and end of every stream | — | — |
| Isolated signs | 9 × 20 reps | ~18 min |
| Isolated atomic activities | 7 × 15 reps | ~16 min |
| Isolated complex activities | 8 × 3 reps | ~30 min |
| SEQ-1 and SEQ-2 | 3 runs each | ~24 min |
| INT-1, INT-2, INT-3 | 3 runs each | ~36 min |
| Free run | 2 runs | ~12 min |

Total ≈ 2.5 hours per person. With 12 participants ≈ 30 hours of CSI.

### Participants
- 5 team members + at least 7 others, gender-mixed.
- Ideally 1–2 fluent or deaf ISL signers. Precedent: FDMSE-ISL was built with 20 native deaf ISL signers from southern India, 10 male and 10 female.
- Before recording, every participant learns the signs from the dictionary videos and has each sign checked by a signer.

## 5. Setup and labeling

### Room
Stage one room as a compact home with these stations placed around the TX–RX line of sight:
- Counter for kitchen tasks
- Table and chair for writing and eating
- TV and sofa corner
- Plants
- Clothes rack
- Light switch prop
- Crash mat

XRF55 set transceiver height at 1.2 m, based on ARIL's finding that this works well for full-body actions; our ~1 m rule is close. Mark every station on the floor with tape.

### Labels for isolated blocks
A small cue script on the RX laptop plays beeps and logs their timestamps on the same clock as the CSI. Labels come out automatically.

### Labels for streams
Record low-resolution phone video for annotation only (never a model input; deleted after labeling). Align it to the CSI using the clap markers, then annotate in ELAN or Label Studio. Schema:

start_us, end_us, label, type (activity/sign/transition/null), script_id, parent_activity

The parent_activity field records which activity a sign or interruption happened inside, which is what captures the interleaving.

### Wearable
Strap the phone IMU on during every session. It costs nothing now, and the same clap markers become the first sync algorithm for multimodal fusion (guide's item 9).

### File naming
Pattern: P03_INT2_r2_ch6_20261005.csv plus an annotation JSON sidecar.

### Ethics
Get Institutional Ethics Committee (IEC) approval and signed consent forms, especially because video is recorded. Q1 reviewers will check for this.

## 6. QC and evaluation

After every file, check:
- Packet rate is within ±10% of nominal.
- No gaps longer than 100 ms.
- Empty-room drift between session start and end is small.
- Sync markers are detected.

Evaluation plan:
- Leave-one-subject-out (LOSO) and cross-session splits.
- Isolated classification.
- Stream segmentation, scored with frame accuracy, segmental F1 and edit score.
- Detection of signs embedded inside activities.
- Confuser-pair confusion matrix.
- The mean-std scalar baseline, reported explicitly. It must fail on this data; that failure is the evidence that the task is no longer trivial.

## 7. Roles and timeline

### Roles
- Protocol lead: reads scripts and runs cues.
- RX/capture operator.
- TX/room and hardware.
- Two model members: run preprocessing and QC as data arrives (covers the guide's "2 on models").

### Timeline
- Week 1: lock references, verify signs with a signer, stage the room, IEC paperwork, pilot with 1 person to confirm the confuser pairs and 5-minute continuous capture stability.
- Weeks 2–4: collect data at 3–4 participants per week.
- Week 5: finish annotation and QC.
- Throughout: draft the Introduction and Literature Survey in parallel.

In the paper, state upfront that CASAS was a multi-room ambient-sensor study and that its tasks were adapted spatially to a single WiFi link. Also note that all prior ISL datasets are vision-based, which is exactly the gap being claimed.

## References
- Singla, G., Cook, D. J., & Schmitter-Edgecombe, M. (2009/2010). Tracking activities in complex settings using smart environment technologies / Recognizing independent and joint activities among multiple residents in smart environments. CASAS interweaved ADL dataset.
- Roggen, D. et al. (2010). Collecting complex activity datasets in highly rich networked sensor environments (OPPORTUNITY).
- Wang, F., Lv, Y., Zhu, M., Ding, H., & Han, J. (2024). XRF55: A Radio Frequency Dataset for Human Indoor Action Analysis. Proc. ACM IMWUT 8(1).
- Adithya, V., & Rajesh, R. (2020). Hand gestures for emergency situations: A video dataset based on words from Indian sign language. Data in Brief 31, 106016.
- Sridhar, A., Ganesan, R. G., Kumar, P., & Khapra, M. (2020). INCLUDE: A Large Scale Dataset for Indian Sign Language Recognition. ACM Multimedia.
- FDMSE, Ramakrishna Mission Vivekananda University, Coimbatore. Indian Sign Language Dictionary (3rd ed., 2016).
- FDMSE-ISL dataset (2024). Hierarchical Windowed Graph Attention Network and a Large Scale Dataset for Isolated Indian Sign Language Recognition. arXiv:2407.14224.

---

## 8. Feasibility Analysis — What to Expect

### Expected accuracy by class type

| Task | Expected accuracy | Why |
|---|---|---|
| Idle vs activity vs sign | High | Different motion energy and duration |
| Atomic whole-body (walk, sit/stand, fall, pick up) | High | Large reflecting body, big CSI changes |
| Complex activities (sweep, water plants, cook) | Good to moderate | Long, distinct rhythms, but some share a posture |
| Specific signs, cross-subject | Moderate, drops on unseen people | Small hand/arm reflector and person-specific style |
| Confuser pairs (Call vs answer phone, Lamp vs switch) | Hard, by design | Nearly identical arm path |
| Static signs (Doctor) | Likely fails | No motion means little change in CSI |

SignFi reached ~98.9% on 276 signs in the lab but fell to ~86.6% on unseen users. It had 3 antennas, used phase, and placed the signer close to the devices. This project has 1 antenna and amplitude only, and analysis found only ~4 effective independent dimensions across the 52 subcarriers.

### Why signs are the hard part

**Resolution.** The link sees a one-dimensional summary of how path lengths change. No direction information. A hand is a small reflector compared with the torso, so different signs can collapse onto similar amplitude patterns.

**Sampling rate.** Doppler shift from a moving hand: f = 2v/λ. At 2.4 GHz, λ = 0.125 m.
- Hand at 1 m/s → ~16 Hz
- Fast sign at 2 m/s → ~32 Hz

The earlier "everything below 18 Hz" finding was for whole-body motion. At ~55 Hz effective rate in Dataset 2, Nyquist limit is ~27 Hz, so fast signs alias. This is fixable.

### Changes that most improve sign recognition

1. **Raise received packet rate to ≥200 Hz.** TX already supports ~200 pps. Find where packets are lost on RX side.
2. **Fix the signing spot.** Place mid-link, close to line of sight, antennas at hand height (~1–1.2 m). Mark spot and facing direction with tape.
3. **Try making phase usable.** Feed both USRPs from a shared 10 MHz + PPS reference (OctoClock or GPSDO). With a shared reference and parked channel, remaining phase error is mostly a linear slope across subcarriers — fit and remove.
4. **Classify hierarchically.** First decide idle/activity/sign, then classify within type. Use surrounding activity as context.
5. **Trim the sign set using pilot.** Keep signs that differ in size, speed, one/two-handed, repetition. Drop pairs CSI can't separate. Doctor is the first candidate to drop.
6. **Report two cross-subject numbers.** Strict LOSO accuracy + accuracy after small per-user calibration (3–5 samples per sign).

### How to present this in the paper

The strongest story for RO2:
- CSI alone handles context and activities
- Here is exactly where it fails on specific signs and look-alike activities
- Adding wearable IMU resolves those failures

A per-class breakdown showing that gap is more convincing than a single 99% figure. It justifies the multimodal design.

---

## 9. IMMEDIATE PRIORITY: Test on Existing Dataset 2 First

Before collecting anything new, run these experiments on the existing data:

1. **13-class classification** (8 activities + 5 gestures), both within-subject and LOSO
2. **5-class gesture-only classification** — the real "can we tell specific signs apart" test
3. **The confusion matrix** — shows which gestures merge with which activities

Also revisit the 0.71 F1 binary result. Try:
- Reduce 52 subcarriers to 3–5 principal components with PCA
- Compute STFT spectrogram of those components (Doppler-like)
- Train a small CNN on the spectrograms

If the 5 gestures separate well within a subject, fine-grained classification is viable. If not, change the setup before the big collection.
