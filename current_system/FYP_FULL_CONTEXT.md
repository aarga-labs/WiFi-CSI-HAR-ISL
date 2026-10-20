> HISTORICAL SEPTEMBER CONTEXT. Read Adhi_To_Amrith_Context.md first. Old datasets, results, plans and claimed future capabilities below are not current paper evidence. Later October findings prohibit use of fabricated DATA_COMBINED P2–P5.

# Full Project Context — FYP: Multimodal Human Activity & Sign Language Recognition for Inclusive Smart Homes

> **Purpose of this document:** This is a complete context dump of a B.Tech CSE Final Year Project (FYP). It captures everything from inception to the current state (20 September 2026) so that any AI assistant can understand the full picture and provide informed help.

---

## 1. Project Identity

| Field | Detail |
|-------|--------|
| **Title** | Multimodal Human Activity and Sign Language Recognition for Inclusive Smart Homes |
| **Alt Title (earlier)** | Smart Home HAR for Speech-Impaired & Hearing-Impaired Users |
| **Course Code** | 23CSE399 — Project Phase 2 |
| **Project Type** | Type 2: Application Project (also referenced as Type 3: Research + Implementation in some documents) |
| **University** | Amrita Vishwa Vidyapeetham, Department of Computer Science and Engineering |
| **Guide** | Ms. Nalinadevi K (Associate Professor, CSE) |
| **Goal** | Build a privacy-preserving, multimodal sensing system that recognizes human activities AND sign language gestures in a smart home WITHOUT cameras, using WiFi CSI + wearable sensors |
| **Publication Target** | Q1 journal paper |

### Team Members (5)
| Name | Roll Number |
|------|-------------|
| Adhikkesh S K | CB.SC.U4CSE23101 |
| Adithya Ajay | CB.SC.U4CSE23102 |
| Amrith B | CB.SC.U4CSE23105 |
| Gowreesh B | (not listed in docs) |
| Rishiikesh S K | (not listed in docs) |

---

## 2. The Core Idea — What This Project Does

### The Problem
1. **Smart homes are growing fast** — 82.1% projected increase by 2026 (Statista)
2. **1.5 billion people have hearing loss** (WHO) → need non-verbal communication for home control
3. **Cameras violate privacy** — 87% of studies report privacy concerns with smart home surveillance (JMIR)
4. **Existing systems are single-modality** — WiFi-only OR wearable-only OR camera-only. Each has blind spots
5. **Sign language recognition** has been camera-based since 1991 — no privacy-preserving WiFi-based ISL system exists

### The Solution
A **multimodal, privacy-preserving system** that:
- Uses **WiFi Channel State Information (CSI)** from Software-Defined Radio (SDR) to sense human motion without cameras
- Combines with **wearable IMU sensors** (accelerometer + gyroscope) for person identification and fine-grained motion
- Optionally adds **ambient sensors** (PIR motion, door contact, temperature) for context
- Distinguishes **daily activities** (walking, sitting, cooking) from **sign language gestures** (ISL signs for smart home commands)
- Understands **context** (what is happening) and **intent** (why it's happening) to make smart home decisions

### Key Differentiation
- **Privacy-preserving:** No cameras — WiFi signals pass through walls and don't record visual data
- **Multimodal:** WiFi CSI + Wearable + Ambient sensors fused together
- **Sign language for smart homes:** Gestures are mapped to home control actions (turn on light, call for help)
- **Interleaved activities:** Handle real-world scenarios where activities overlap and transition naturally

---

## 3. Research Objectives (ROs)

| RO | Description | Status |
|----|-------------|--------|
| **RO1** | Design a privacy-preserving, single-person, single-modality data acquisition methodology, and develop classification models that distinguish daily Activities from Sign Gestures | ⚠️ Mostly done, but gestures need to be changed to ISL and activity-related |
| **RO2** | Extend to single-person, multi-modality setting, and develop models for complex, interleaved activities | 🔵 CURRENT FOCUS — data collection and paper writing needed |
| **RO3** | Extension to multi-person, multi-modality sign and activity recognition for parallel/concurrent activities | ⏳ Future — after RO2 paper |
| **RO4** | Multimodal fusion for context- and intent-aware smart-home control | ⏳ Future — after RO3 |

---

## 4. Technical Stack & Hardware

### 4.1 WiFi CSI Sensing Hardware
| Component | Details |
|-----------|---------|
| **SDR** | 2× Ettus Research USRP N210 (one TX, one RX) |
| **Daughterboard** | SBX (400 MHz – 4.4 GHz) |
| **Host Interface** | Gigabit Ethernet (direct point-to-point cable to each laptop) |
| **TX Laptop** | Runs GNU Radio flowgraph for IEEE 802.11 frame transmission |
| **RX Laptop** | Fedora Linux — runs GNU Radio flowgraph for reception + CSI extraction |
| **Frequency** | 2.4 GHz WiFi band — Channels 1 (2412 MHz), 6 (2437 MHz), 11 (2462 MHz) |
| **Bandwidth** | 20 MHz per channel (hardware limitation — cannot do all 3 simultaneously) |
| **Antenna Config** | SISO (single antenna each side) — no MIMO, no DFS/BVP features possible |

### 4.2 Software Stack
| Layer | Tool |
|-------|------|
| **SDR Framework** | GNU Radio 3.x |
| **WiFi PHY** | gr-ieee802-11 (open-source OOT module — modified for CSI extraction) |
| **UHD** | USRP Hardware Driver |
| **CSI Extraction** | Custom C++ block (`extract_csi_impl.cc`) — extracts 52 complex subcarrier values per decoded 802.11 frame |
| **Data Format** | CSV files with columns: `Packet, Timestamp_us, Channel, SC0_Re, SC0_Im, ... SC51_Re, SC51_Im, type, label` |
| **ML Framework** | PyTorch (CNN, CNN-GRU, ResNet-18) |
| **Wearable** | Android phone IMU (accelerometer + gyroscope at 50 Hz) with TFLite on-device inference |

### 4.3 CSI Data Schema
Each row in a CSV file represents one decoded 802.11 packet:
```
Packet          — sequential packet number
Timestamp_us    — epoch microseconds
Channel         — WiFi channel (1, 6, or 11)
SC0_Re, SC0_Im  — Real and Imaginary parts of subcarrier 0
SC1_Re, SC1_Im  — Real and Imaginary parts of subcarrier 1
...
SC51_Re, SC51_Im — Real and Imaginary parts of subcarrier 51
type            — "activity" | "gesture" | "baseline"
label           — specific class name (e.g., "Walking", "hello", "baseline_empty")
```
- **52 OFDM subcarriers** × 2 (Re, Im) = **104 CSI values per packet**
- **Amplitude:** `|H_k| = sqrt(Re² + Im²)` — this is the primary sensing feature
- **Phase:** `∠H_k = atan2(Im, Re)` — NOT usable in current setup (no clock sync between TX/RX → phase is scrambled by CFO/SFO)

---

## 5. System Evolution — How It Got Here

### Phase 1: Passive CSI Sensing (Earlier — completed)
```
Phone Hotspot → MacBook WiFi Traffic → Single USRP (passive sniffing) → CSI
```
- USRP passively eavesdropped on existing WiFi traffic between a MacBook and an Android phone hotspot
- **Problems:** Traffic-dependent, limited channel control, ~51–78 Hz packet rate (variable)
- Captured pilot data: 2 subjects (Rishiikesh, Amrith), binary Action vs. No-Action
- 8 takes × ~90 seconds = ~752 seconds total, 322 windowed samples

### Phase 2: Active CSI Sensing (Current — Setup 2)
```
USRP N210 TX (controlled 802.11 frames) → Wireless Channel → USRP N210 RX → CSI Extraction
```
- Dedicated TX/RX pair — full control over transmission parameters
- IEEE 802.11 frames generated by GNU Radio, sent via USRP TX
- RX decodes frames and extracts CSI
- **Channel hopping:** Sequential hop across channels 1, 6, 11 (100 ms dwell per channel)
- **Critical finding:** Channel hopping during activity is NOT viable (~2 Hz rate). Solution: **park on one channel during activity, hop between sessions**

### Phase 3: Three-Channel Experiment (Current)
- Located in `Three_channel_Exp/` directory
- Separate TX and RX folders with complete GNU Radio projects
- `capture.sh` script for labeled instance recording
- `DATA_COLLECTION.md` — comprehensive protocol with pilot → dataset → classification stages

---

## 6. Datasets Collected

### 6.1 Pilot Dataset (July 2026 — Passive Sensing)
| Property | Value |
|----------|-------|
| **Location** | `pilot/pilot/` and `others/Works/Action and No action/data/` |
| **Setup** | Passive sniffing (MacBook ↔ Phone hotspot, single USRP) |
| **Subjects** | 2 (Rishiikesh, Amrith) |
| **Classes** | 2 — Action (walking, mixed activity) vs. No-Action (standing, sitting) |
| **Takes** | 8 CSVs (~90 s each, ~752 s total) |
| **Rate** | 51–78 Hz (mean 66.4 Hz) |
| **Windows** | 322 (2-second windows with ~50% overlap) |
| **Files** | `P01_action_amrith_20260717_walk.csv`, `P01_noaction_rishiikesh_20260717_sit.csv`, etc. |

### 6.2 Dataset 2: Activity vs. Gesture (September 2026 — Active Sensing)
| Property | Value |
|----------|-------|
| **Location** | `DATA_COMBINED-20260906T145148Z-1-001/DATA_COMBINED/` |
| **Setup** | Active sensing (Two-USRP TX/RX, controlled 802.11) |
| **Subjects** | 5 (P1–P5), ~2 hours per participant |
| **Total Records** | ~600,000 CSI packets (~10 hours of recording) |
| **Files** | `combined.csv` (~169 MB), `combined_person1.csv` through `combined_person5.csv` (~170 MB each) |

**15 Classes in Dataset 2:**

| Type | Classes | Count (Person 1) |
|------|---------|-------------------|
| **Activity (8)** | Walking, Sit-Stand, Bend Down, Squats, Drink Water, Eating, Writing, Use Mobile Phone | ~71,412 total |
| **Gesture (5)** | Hello, Thank You, Friend, Name, Nice to Meet You | ~50,495 total |
| **Baseline (2)** | Empty Room, Standing Still | ~16,974 total |

**Per-label distribution (Person 1):**
- drink_water: 13,480 | sit_stand: 11,392 | thank_you: 11,160
- baseline_empty: 10,320 | nice_to_meet_you: 10,314 | bend_down: 10,111
- name: 10,060 | hello: 9,573 | friend: 9,388
- use_mobile_phone: 9,038 | Walking: 8,329 | writing: 8,256
- squats: 7,441 | baseline_Stand: 6,654 | eating: 3,365

---

## 7. Models Built & Results

### 7.1 Model 1: Action vs. No-Action (Binary — Pilot Data)
| Property | Value |
|----------|-------|
| **Pipeline** | CSI → 2-second window → Recurrence Plot (per subcarrier) → ResNet-18 → Binary prediction → Majority voting across subcarriers |
| **Architecture** | Pre-trained ResNet-18 (ImageNet), adapted final layer for binary classification |
| **Input** | 224×224 Recurrence Plot images from 2-second CSI windows, 52 subcarriers |
| **Training** | Adam optimizer + dynamic learning rate scheduling |
| **Evaluation** | Leave-One-Subject-Out (LOSO) — test on unseen subject |
| **Result** | **96% overall accuracy** (Precision: 0.96, Recall: 0.96, F1: 0.96) |
| **Per-class** | NoAction: P=0.93, R=0.99, F1=0.96 / Action: P=0.99, R=0.93, F1=0.96 |
| **Also used** | CNN-GRU-Attention hybrid model — scored 98.4–99.3% |
| **Caveat** | A single scalar (mean temporal std of amplitude) achieves 99.1% — the binary task is nearly trivial |

### 7.2 Model 2: Activity vs. Gesture (Binary — Dataset 2)
| Property | Value |
|----------|-------|
| **Pipeline** | Raw CSI → Phase unwrap + CFO/SFO removal → Per-window normalization → 1D-CNN → Binary prediction |
| **Architecture** | Lightweight 1D-CNN (~100K parameters) |
| **Input** | 2.0-second windows at ~55 Hz, 52 subcarriers |
| **Training** | 30 epochs, Leave-One-File-Out (LOFO) validation |
| **Key Fix** | Initial 100% accuracy was caused by mean-amplitude DC bias leak. Fixed via per-window normalization |
| **Result** | **Macro F1: 0.71** (Activity: P=1.00, R=0.58, F1=0.73 / Gesture: P=0.53, R=1.00, F1=0.69) |
| **Issue** | Model has bias — perfect precision for Activity but low recall; overpredicts Gesture |

### 7.3 Wearable Fall Detection (Multi-Modal Extension)
| Property | Value |
|----------|-------|
| **Pipeline** | Phone IMU (Accel+Gyro, 50 Hz) → 2.56s window → Dual-stream 1D-CNN → TFLite → On-device alert |
| **Classes** | ADL (normal) vs. Fall |
| **Result** | ADL score: 4.8×10⁻⁴ vs. Fall score: 0.29 → ~600× relative spike, threshold at 0.20 |
| **Known Issue** | False positive: placing phone hard on table triggers alarm (model learned "any hard impact = fall") |
| **Fix Planned** | Add high-impact non-fall ADL data + multi-orientation recordings |
| **Location** | `ImagePi/fall_detection_amrith_pipeline.ipynb` |

### 7.4 ImgFi Replication
| Property | Value |
|----------|-------|
| **Paper** | ImgFi: High Accuracy & Lightweight HAR Using CSI Images |
| **What** | CSI → Recurrence Plot → Lightweight 2D-CNN (90× fewer params than ResNet-50) |
| **Status** | Replicated on Widar 3.0 dataset |
| **Location** | `ImagePi/ImgFi_Widar_Complete.ipynb`, `ImagePi/ImagePi_Model_Kaggle_Notebook.ipynb` |
| **Finding** | 52 subcarriers are NOT independent — effective rank is 3.5–4.2. Treating them as 52 separate images is misleading |

---

## 8. Comparative Analysis — Honest Assessment

A thorough comparative analysis was done (located at `usrp-projects/usrp-projects/analysis/comparative_analysis.tex`) comparing this project's pilot data against three published datasets:

| Aspect | This Project (Pilot) | ARIL (2019) | UT-HAR (2017) | Widar 3.0 (2019) |
|--------|---------------------|-------------|---------------|-------------------|
| Radio | USRP N210 | USRP N210 ×2 | Intel 5300 | Intel 5300 |
| Acquisition | **Passive sniff** (then evolved to active) | Controlled TX+RX | Controlled | Controlled |
| Subcarriers | 52 | 52 | 30 | 30 |
| Links × antennas | **1 (SISO)** | 1 (SISO) | 3 | **18** |
| Packet rate | ~51–78 Hz | Not reported | **1000 Hz** | **1000 Hz** |
| Uses phase | ✗ (unsynced) | ✗ (discarded) | ✗ | ✓ DFS/BVP |
| Classes | **2** | 6 | 7 | **22** |
| Subjects | **2** | **1** | 6 | **16** |
| Samples | **322** | 1,394 | 4,477 | **258,000** |
| Test split | **LOSO** (strictest) | Every 5th sample (leaky) | Random (leaky) | **Cross-domain** |

**Key findings:**
- ✅ Hardware/front-end matches ARIL (peer-reviewed USRP dataset)
- ✅ Amplitude-only decision is correct (even ARIL discards phase)
- ✅ 66 Hz is adequate — all discriminative information lives below 18 Hz for whole-body motion
- ✅ Evaluation protocol (LOSO) is strictest of the four
- ❌ Dataset is 4×–800× smaller than references
- ❌ Binary task is nearly trivial (one scalar gets 99.1%)
- ❌ Only 2 subjects, 1 room, 1 day — overfitting undetectable

---

## 9. System Architecture (Three-Pipeline Design)

The full system architecture (from `Arch_FYP.jpg`) has three sensing pipelines feeding into a fusion core:

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Pipeline 1    │   │   Pipeline 2    │   │   Pipeline 3    │
│ Ambient Sensing │   │ Wearable Sensing│   │ WiFi CSI Sensing│
│                 │   │                 │   │                 │
│ PIR Motion,     │   │ 3-Axis Accel    │   │ WiFi TX & RX    │
│ DoorContact,    │   │ & Gyroscope     │   │                 │
│ Temperature     │   │                 │   │ Amplitude Ext.  │
│                 │   │ Noise Filtering │   │ & Denoising     │
│ Event Filtering │   │ & Windowing     │   │                 │
│ & State Encoding│   │                 │   │ CSI Feature     │
│                 │   │ Inertial Feature│   │ Extractor (CNN) │
│ Ambient Feature │   │ Extractor       │   │                 │
│ Extractor (LSTM)│   │ (1D-CNN)        │   │                 │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────┬───────┴─────────────────────┘
                       │
            ┌──────────▼──────────┐
            │ Fusion & Decision   │
            │ Core                │
            │                     │
            │ Time Sync &         │
            │ Alignment           │
            │                     │
            │ Multi-Modal Feature │
            │ Fusion (Attention)  │
            │                     │
            │ Context State       │
            │ Classifier          │
            │ Idle/Activity/Sign  │
            └──────────┬──────────┘
                       │
         ┌─────────────┼─────────────────┐
         │             │                 │
    ┌────▼────┐  ┌─────▼─────┐   ┌──────▼──────┐
    │Activity │  │Sign-to-   │   │Daily Routine│
    │Recog &  │  │Text       │   │& Intent     │
    │Fall Det │  │Translation│   │Prediction   │
    └────┬────┘  └─────┬─────┘   └──────┬──────┘
         │             │                 │
         └─────────────┼─────────────────┘
                       │
            ┌──────────▼──────────┐
            │ Smart Home          │
            │ Actuation &         │
            │ Caregiver Alerting  │
            └─────────────────────┘
```

**Current status:** Only Pipeline 3 (WiFi CSI) is operational. Pipeline 2 (Wearable) has a prototype fall detector. Pipeline 1 (Ambient) and the Fusion Core are not built yet.

---

## 10. Literature Survey — Key Papers Referenced

### WiFi CSI for HAR
| Paper | Year | Key Contribution | Limitation |
|-------|------|-----------------|------------|
| **SignFi** (Ma et al.) | 2018 | 9-layer CNN on WiFi CSI, 276 sign gestures, 98.9% lab accuracy | Falls to 86.6% on unseen users; nearby motion corrupts signal |
| **Widar 3.0** (Zheng et al.) | 2019 | Domain-independent BVP features + CNN-GRU, 83–92% cross-domain | Needs multiple synchronized links, line-of-sight |
| **ImgFi** | 2023 | CSI → Recurrence Plot → lightweight 2D-CNN, 99.5–99.8% | Within-domain only, 90× fewer params than ResNet50 |
| **PA-CSI** (Quy et al.) | 2025 | WiFi amplitude + phase attention fusion, 99.9% in-room | Multi-person motion overlap in RF signals |
| **Joint Activity+Localization** (ARIL) | 2019 | Dual-branch 1D-CNN, 88% activity + 95.7% location | Single-user, single-room |

### Sign Language Recognition
| Paper | Year | Key Contribution | Limitation |
|-------|------|-----------------|------------|
| **CorrNet** (Hu et al.) | 2023 | Correlates hand/face regions for CSLR, 19.4% WER | Camera-based, occlusion and privacy issues |
| **LLMs SLT** (Gong et al.) | 2024 | Visual sign tokens → LLM translation, BLEU-1: 45.2 | Camera-based, fails with background motion |
| **Wi-SL** (Wang et al.) | 2023 | WiFi CSI + CNN + nearest-neighbor, 98.9% gesture accuracy | Single-signer, overlapping motion degrades performance |
| **WatchSign** (Liu et al.) | 2023 | Smartwatch + smart ring IMU, 94.2% on 100 ASL words | Cannot detect ambient multi-person activities |
| **RF-ASLR** (Nosheen et al.) | 2026 | SDR CSI + LSTM, 98% on 20 ASL signs | Tested only in controlled, static, single-user setups |
| **ASL Translation** (Gu et al.) | 2024 | Wearable inertial + Bi-LSTM, 99% word / 97.3% sentence accuracy | Full-body suit too intrusive for daily home use |

### Multi-Person HAR
| Paper | Year | Key Contribution | Limitation |
|-------|------|-----------------|------------|
| **LAHAR** (Chen et al.) | 2024 | LLM-based ambient sensor reasoning for multi-person HAR | No fine hand/finger motion detection |
| **Multi-Skel** (Li et al.) | 2024 | Multi-person skeleton tracking, 98% on MOT16 | Body occlusion hides keypoints |
| **Interact-Obj** (Wen et al.) | 2025 | Object-aware skeleton graph, 96.7% cross-subject | Vision-based, struggles with simultaneous actions |
| **AttCLHAR** | 2024 | Self-attention on wearable IMU, 98.1% WISDM | Little context about surrounding people |
| **OAHR** | 2024 | 3D skeleton volume for missing joints, 97.1% NTU RGB+D 60 | Vision-based, no multi-user separation |

### Research Gaps Identified
1. Single-modality systems have **context blindness**
2. Vision-based systems degrade under **occlusion and multi-user overlap**
3. No **multimodal fusion framework** for complex parallel activities exists
4. No **WiFi CSI-based ISL recognition** system exists
5. No system handles **interleaved activity + sign language** in one framework

---

## 11. Known Limitations (Acknowledged)

1. **Bandwidth limitation:** Multi-channel needs ~70 MHz; hardware supports only 20 MHz at a time
2. **Isolated window classification:** Current CNN evaluates pre-segmented 2-second windows; no real-time continuous segmentation
3. **Phase unusable:** Single-antenna SISO with no clock sync → phase is scrambled, only amplitude is used
4. **Dataset size:** Small compared to published benchmarks (322–600K records vs. 258K instances in Widar)
5. **Domain diversity:** Few subjects (2–5), one room, limited days
6. **Subcarrier redundancy:** 52 subcarriers have only ~4 effective independent dimensions during motion
7. **Gesture choice:** Current gestures (Hello, Thank You, Friend, etc.) are social/conversational, NOT related to smart home activities — **this must be fixed**

---

## 12. Guide Meeting Feedback (20 September 2026) — CRITICAL

The guide (Ms. Nalinadevi K) gave the following instructions in the most recent meeting:

### Direct Instructions
1. **Sequential AND interleaved activities** — check if current data has this; if not, capture it
2. **Complex activity = interleaved** — activities that transition into each other naturally
3. **Gestures must be related to activities** — "Hello" and "Thank You" are not enough
4. **Change activities properly** — use a standard reference for activity selection
5. **Use Indian Sign Language (ISL)** — not generic gestures
6. **Standard reference for choosing activities** — cite a recognized paper/benchmark
7. **Single person + single modality → interleaved first** (both single and multi-modality)
8. **Write plan of action for each modality** (WiFi CSI, Wearable, Ambient)
9. **Research sync algorithms for fusion** — how to align multi-modal data streams
10. **Single modality + single person + proper activities first**
11. **Write paper on multi-modality** — target completion at RO2
12. **Multi-person comes AFTER the paper**

### Paper Writing Instructions
- **Start writing NOW** — Introduction first, then Literature Survey
- **Write paper when RO2 is finished** — full domain for RO2 before multi-person
- **Introduction for RO1 and RO2** — cover both in the paper
- **Standard for sign gestures** — replicate a recognized ISL paper's gesture set

### Key Clarifications from Meeting
- Gestures need MORE similarity with activities → makes classification harder, more publishable
- Need to refer to a **standard paper** for taking gestures — ISL or ASL, choose 1
- For activities, take a **standard reference** and collect data accordingly
- Plot data for **sequential** AND for **interleaved** scenarios
- Need full plan approval: what data is being collected, by whom, when
- **2 members must focus on models** — noise filtering, preprocessing must be done correctly
- Each member must have a clearly assigned role with deliverables

---

## 13. Folder Structure

```
FYP/
├── main.tex                     # Latest presentation (32 slides, Phase 2 Panel Review 1)
├── ppt.tex                      # Earlier presentation version
├── Arch_FYP.jpg                 # System architecture diagram (3 pipelines + fusion core)
├── USRP_IMAGE_1.jpeg            # USRP N210 front panel photo
├── USRP_IMAGE_2.jpeg            # USRP N210 internal SBX daughterboard photo
├── csi_equations.jpeg            # CSI mathematical model equations
├── 3_Month_Plan.pdf             # 3-month project timeline
├── falldetection_rishi.pdf      # Fall detection related document
│
├── DATA_COMBINED-.../            # Dataset 2 (Activity vs Gesture, 5 participants)
│   └── DATA_COMBINED/
│       ├── combined.csv          # ~169 MB, all participants merged
│       ├── combined_person1.csv  # ~169 MB
│       ├── combined_person2.csv  # ~170 MB
│       ├── combined_person3.csv  # ~173 MB
│       ├── combined_person4.csv  # ~172 MB
│       └── combined_person5.csv  # ~173 MB
│
├── ImagePi/                      # ImgFi replication + models
│   ├── ImagePi_Model_Kaggle_Notebook.ipynb
│   ├── ImgFi_Widar_Complete.ipynb
│   ├── SignFi-CNN.ipynb
│   ├── fall_detection_amrith_pipeline.ipynb
│   └── ImgFi_Widar_Weights.pth
│
├── Latex/                        # Reference papers + earlier presentation
│   ├── sample.tex
│   ├── SignFi ACM.pdf
│   ├── TPAMI_Widar3.0_paper.pdf
│   └── ...
│
├── Papers/                       # Reference papers (PDFs)
│
├── Reports/                      # Final reports
│   ├── FYP_updated.pdf
│   └── Final_Report_FYP.pdf
│
├── Three_channel_Exp/            # Three-channel USRP experiment (active sensing)
│   ├── README.md                 # Setup documentation
│   ├── DATA_COLLECTION.md        # Comprehensive data collection protocol (451 lines)
│   ├── transmitter/              # TX-side GNU Radio project
│   └── receiver/                 # RX-side GNU Radio project
│
├── pilot/                        # Pilot experiment data
│   └── pilot/                    # CSI captures + check plots
│
├── others/
│   └── Works/
│       ├── Action and No action/ # Pilot dataset + CNN-GRU model
│       │   ├── data/             # Raw CSI captures
│       │   ├── CNN_GRU_Method/   # Action_NoAction_CNN_GRU.ipynb
│       │   └── comparative_analysis.pdf
│       └── USRP/                 # Guides and cheatsheets
│           ├── 1_DATA_CAPTURE_GUIDE.md
│           ├── 2_TRAINING_GUIDE.md
│           └── 3_COMMANDS_CHEATSHEET.md
│
├── usrp-projects/                # Full USRP project repository
│   └── usrp-projects/
│       ├── USRP_lib/             # USRP library, GNU Radio modules
│       │   └── FinalYearProject/ # Report tex + reference papers
│       ├── analysis/             # Comparative analysis (tex + 10 figures)
│       └── gr-ieee802-11/        # GNU Radio 802.11 module
│
├── new/                          # Newer receiver/transmitter copies
│   ├── receiver/
│   └── transmitter/
│
└── Context/                      # WhatsApp chat exports (team communication)
```

---

## 14. Timeline / Progress

| Milestone | Status | Date |
|-----------|--------|------|
| Literature survey & ROs defined | ✅ Done | ~May 2026 |
| RF Pipeline — passive WiFi CSI capture | ✅ Done | ~June 2026 |
| RF Pipeline — active USRP TX/RX setup | ✅ Done | ~July 2026 |
| Pilot dataset (Action vs No-Action, passive) | ✅ Done | 17 July 2026 |
| Pilot validation + comparative analysis | ✅ Done | 20 July 2026 |
| Three-channel experiment framework | ✅ Done | ~Aug 2026 |
| Dataset 2 (15 classes, 5 persons, active) | ✅ Done | ~6 Sep 2026 |
| Model 1 (Action/NoAction ResNet-18) — 96% | ✅ Done | ~Aug 2026 |
| Model 2 (Activity/Gesture 1D-CNN) — F1: 0.71 | ✅ Done | ~Sep 2026 |
| Wearable fall detection prototype | ✅ Done | ~Aug 2026 |
| **Guide Meeting 1 — Phase 2** | ✅ Done | **20 Sep 2026** |
| Fix gestures → ISL, fix activity reference | 🔴 TODO | — |
| Sequential + Interleaved data collection | 🔴 TODO | — |
| Multi-modality data (WiFi + wearable simultaneously) | 🔴 TODO | — |
| Sync algorithm for multi-modal fusion | 🔴 TODO | — |
| Paper: Introduction + Lit Survey draft | 🔴 TODO | — |
| Paper: Full RO2 paper submission to Q1 journal | 🔴 TODO | — |
| Multi-person experiments (RO3) | ⏳ After paper | — |
| Context/intent-aware control (RO4) | ⏳ After RO3 | — |

---

## 15. What Needs To Happen Next (Priority Order)

1. **Choose standard references** — one paper for activity selection, one for ISL gesture selection
2. **Redesign gesture set** — ISL gestures related to home activities (light, fan, water, help, etc.)
3. **Design interleaved activity sequences** — scripted but natural transitions for data capture
4. **Start writing Introduction + Lit Survey** for the paper (don't wait for experiments)
5. **Collect sequential activity data** — single person, single modality (WiFi CSI), proper activities
6. **Collect interleaved activity data** — continuous CSI streams with annotated transitions
7. **Add wearable modality** — simultaneously capture phone IMU data with WiFi CSI
8. **Research and implement sync algorithm** — cross-correlate calibration events across modalities
9. **Build fusion model** — attention-based multi-modal feature fusion
10. **Complete and submit RO2 paper** — then move to multi-person (RO3)

---

## 16. Key Technical Details for Any AI Helper

### CSI Math
- Channel response: H_k = |H_k| × e^(j × ∠H_k) for subcarrier k
- Human motion causes temporal variation in |H_k| — this is the sensing signal
- Amplitude features: mean, std, percentiles across time windows
- All discriminative information for whole-body motion lives **below 18 Hz**
- At ~55 Hz sampling rate, Nyquist limit is ~27.5 Hz — adequate for current activities
- **Phase is NOT used** — no clock sync → CFO/SFO scrambles phase

### Windowing
- 2-second sliding windows with 50% overlap
- At ~55 Hz → ~110 packets per window
- Each window → 52 subcarrier amplitude time series → input to model

### Model Input Formats
- **ResNet-18 (Model 1):** 224×224 Recurrence Plot images (one per subcarrier, majority vote)
- **1D-CNN (Model 2):** Raw amplitude time series [window_length × 52]
- **CNN-GRU hybrid:** Full 52-subcarrier matrix input, temporal feature extraction

### Critical Finding from Comparative Analysis
> A single scalar (mean temporal standard deviation of amplitude across subcarriers) classifies Action vs. No-Action with **99.1% accuracy**. This means the binary task is too easy. The project MUST move to multi-class and interleaved activities to be publishable in a Q1 journal.

---

## 17. Data Capture Technical Details (for reproducing setup)

### Passive Setup (Legacy)
```
MacBook (WiFi MAC: 42:23:9e:d9:54:24) → Android Hotspot (BSSID: e2:63:84:5b:14:29)
USRP N210 (addr: 192.168.10.7) passively sniffs on Channel 11 (2.462 GHz)
Traffic generated by: sudo ping -i 0.01 <gateway-ip> on MacBook (100 pps)
CSI extraction: custom gr-ieee802-11 extract_csi block
MAC filter: CSI_TA and CSI_RA environment variables
```

### Active Setup (Current)
```
Laptop A (TX): packet_generator.py → wifi_tx_multi_hop.py → USRP N210 TX (addr: 192.168.10.9)
  ↕ RF over the air (human moves in between)
Laptop B (RX): USRP N210 RX (addr: 192.168.10.7) → wifi_rx.py → extract_csi → CSV

TX: IEEE 802.11 frames with src=02:00:00:00:00:01, dst=02:00:00:00:00:02
RX: CSI_TA=02:00:00:00:00:01, CSI_RA=02:00:00:00:00:02
Rate: ~200 pps (configurable via PPS env var)
Channel: CSI_CHANNEL=1|6|11 (parked) or unset (hopping)
Dwell time: 100ms per channel when hopping
```

### Room Setup Rules
- TX and RX 3–5 m apart, line of sight, antennas at ~1 m height
- Subject moves BETWEEN the antennas (crossing the direct RF path)
- Tape marks on floor for all positions
- Same room for entire dataset; door closed; no other people moving
- Never move furniture or antennas between sessions

---

## 18. Approved Data Collection Plan (20 Sep 2026)

A comprehensive data collection plan has been developed and saved to `DATA_COLLECTION_PLAN.md` in the FYP folder. Key decisions:

### Standard References Locked
- **Activities:** CASAS interweaved ADL study (Singla, Cook & Schmitter-Edgecombe, 2009–10) — the gold standard for interleaved activity definition
- **Atomic actions:** OPPORTUNITY (Roggen et al., 2010) — mid-level gesture vocabulary
- **RF protocol:** XRF55 (Wang et al., IMWUT 2024) — largest WiFi/RF action dataset, 20 reps per action
- **ISL Emergency signs:** Adithya V. & Rajesh R., Data in Brief 2020 — ISL dictionary from FDMSE, Coimbatore
- **ISL Home/Greeting signs:** INCLUDE / INCLUDE-50 (Sridhar et al., ACM MM 2020) — most-cited ISL word dataset

### New Class Set: 7 Atomic + 8 Complex Activities + 9 ISL Signs
**Atomic (5–10 s):** Walk, Sit/Stand, Pick up object, Drink from cup, Toggle light switch, Answer phone, Fall
**Complex (30–90 s, from CASAS):** Fill pill organizer, Watch TV, Water plants, Phone conversation, Write a card, Prepare meal, Sweep/dust, Select/fold outfit
**ISL Signs (9):** Help, Pain, Call, Doctor, Hot, Accident, Fan, Lamp, Hello

### Deliberate Confuser Pairs (the hard problem)
Call ↔ Answer phone | Lamp ↔ Toggle switch | Fan ↔ Dusting | Hot ↔ Drinking/Eating | Accident ↔ Fall | Doctor ↔ Standing still

### Recording Structures
1. **Isolated:** Single action, 20 reps, with cue beeps
2. **Sequential (SEQ):** Continuous stream, activities finish before next starts
3. **Interleaved (INT):** Activities interrupted, signs embedded mid-activity
4. **Free (CASAS-style):** Participant chooses own order and interleaving

### Scale
- 12 participants × 2 sessions × ~75 min = ~30 hours of CSI
- 2 sessions on different days AND different channels for domain diversity
- Wearable IMU captured simultaneously from day 1
- Sync via 3-clap markers at stream boundaries

### CRITICAL: Test Existing Data First
Before any new collection, run on Dataset 2:
1. 13-class classification (8 activities + 5 gestures), within-subject and LOSO
2. 5-class gesture-only classification
3. Full confusion matrix
4. PCA → STFT spectrogram → CNN pipeline as alternative to current 1D-CNN

### Feasibility Expectations
- Whole-body activities: HIGH accuracy expected
- Complex activities: GOOD-MODERATE accuracy
- Specific signs cross-subject: MODERATE, drops on unseen people
- Confuser pairs: HARD by design (this is the novelty)
- Static signs (Doctor): LIKELY FAILS on CSI alone → justifies multimodal fusion

### Key Technical Improvements Planned
1. Raise packet rate to ≥200 Hz (TX already supports it)
2. Fix signing spot mid-link at hand height (~1.2 m)
3. Explore shared clock reference (OctoClock/GPSDO) to make phase usable
4. Hierarchical classification: idle → activity/sign → specific class
5. Report both strict LOSO and calibrated (3–5 samples) accuracy
