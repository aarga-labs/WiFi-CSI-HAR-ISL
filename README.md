# Multimodal Human Activity & Indian Sign Language Recognition for Inclusive Smart Homes

Final Year Project (FYP) repository developed by **Adhikkesh S K, Adithya Ajay, Amrith B, Gowreesh B, and Rishiikesh S K** under the guidance of **Ms. Nalinadevi K**, Department of Computer Science & Engineering, Amrita Vishwa Vidyapeetham.

---

## Team Members & Responsibilities

| Name | GitHub Username | Role / Key Focus Areas |
|---|---|---|
| **Adhikkesh S K** | [`@Adhikkesh`](https://github.com/Adhikkesh) | Active CSI capture pipeline, Kaggle multi-GPU training orchestration, presentation design |
| **Adithya Ajay** | [`@Achilles80`](https://github.com/Achilles80) | SignFi CNN benchmarks, wearable IMU fall detection models, smart home alarm actuator interfacing |
| **Amrith B** | [`@AMRITH03`](https://github.com/AMRITH03) | Passive USRP sensing, GNU Radio RF flowgraphs, transmitter operations, conference manuscript lead |
| **Gowreesh B** | [`@Gowreesh1905`](https://github.com/Gowreesh1905) | Recurrence plot modeling, 2D/1D CNN architectures, Phase-1 baseline activity/sign pipeline |
| **Rishiikesh S K** | [`@Rishiikesh-20`](https://github.com/Rishiikesh-20) | USRP hardware interfacing, multi-channel RF receiver architecture, OFDM subcarrier Doppler analysis |

---

## Project Overview

Smart homes designed for inclusive living and non-verbal accessibility must reliably distinguish between everyday background movements (such as walking, sitting, eating, or drinking) and deliberate communicative gestures (such as sign language commands). Detecting motion alone is insufficient: picking up a glass should not inadvertently trigger an automated water dispensing command.

This project investigates whether a single-link **Wi-Fi Channel State Information (CSI)** connection can:
1. Differentiate routine daily living activities from deliberate sign language gestures.
2. Accurately identify individual actions (12 classes) and Indian Sign Language (ISL) gestures (14 classes).
3. Automatically detect and recognize signs within continuous, scripted daily living activity sequences (stories) for unseen individuals excluded from training.

---

## Hardware Testbed & RF Specifications

- **Software-Defined Radios**: Two Ettus USRP N210 SDRs equipped with SBX daughterboards (1 Transmitter, 1 Receiver in SISO configuration).
- **PHY / Link Standard**: Active IEEE 802.11 link using GNU Radio (`gr-ieee802-11` and `gr-foo`).
- **Operating Frequency**: 2412 MHz (Channel 1, 2.4 GHz ISM band).
- **Bandwidth & Subcarriers**: 20 MHz channel bandwidth with 52 OFDM complex CSI subcarriers.
- **Packet Transmission**: Target 200 packets per second (PPS).
- **RF Configuration**: Transmitter gain TX_GAIN=15; Receiver gain RX_GAIN=12 (empirically calibrated via gain sweeps).
- **Environment**: Fixed room geometry with controlled antenna placement and environmental constraints (doors/windows closed, appliances stationary, phones in airplane mode).

---

## Dataset & Vocabulary (P01 – P05)

The experimental dataset covers **5 real participants** across **25 structured recording sessions** comprising **2,050,030 raw CSI rows** (2,010,899 participant modeling rows + 3 empty-room QC checks):

- **12 Daily Living Activities**: `walk`, `sitstand`, `pickup`, `lightswitch`, `drink`, `answerphone`, `eat`, `wipetable`, `tvremote`, `fall`, `chop_food`, `stir_pot`.
- **14 Indian Sign Language (ISL) Signs**: `HELLO`, `THANKYOU`, `LAMP`, `FAN`, `TELEVISION`, `COOK`, `WATER`, `HOT`, `HUNGRY`, `TOILET`, `CALL`, `HELP`, `PAIN`, `ACCIDENT`.
- **Scripted Sequential Stories**:
  - `M-SEQ` (Meal Routine): Walk $\rightarrow$ Lightswitch $\rightarrow$ Cooking $\rightarrow$ Sit/Stand $\rightarrow$ Eat $\rightarrow$ Drink $\rightarrow$ Meal Signs.
  - `T-SEQ` (TV / Phone Routine): Walk $\rightarrow$ Sit/Stand $\rightarrow$ TV Remote $\rightarrow$ Answer Phone $\rightarrow$ Home Signs $\rightarrow$ Stand and Leave.
  - `C-SEQ` (Cleaning / Emergency Routine): Walk $\rightarrow$ Wipe Table $\rightarrow$ Pick Up $\rightarrow$ Fan/Help $\rightarrow$ Walk/Fall $\rightarrow$ Emergency Signs.
  - `S-SEQ` (Seated Routine): Wipe $\rightarrow$ Chop $\rightarrow$ Stir $\rightarrow$ Eat $\rightarrow$ Drink $\rightarrow$ Needs/Assistance Signs.

---

## Repository Structure

```text
├── capture/
│   └── esp32/                 # ESP32 CSI sender, standalone receiver, and ESPectre motion demo
├── current_system/
│   ├── capture_snapshot/      # Active USRP capture runtime scripts and session logs
│   ├── current_impl/          # Vector figures, media excerpts, and presentation graphs
│   ├── handoff/               # Dataset manifests, checksums, and context transfer docs
│   ├── Kaggle_P1_P5/          # Executed balanced training runs, model cards, checkpoints, audits
│   ├── Model_Detect.../       # Phase-1 baseline CNN models and evaluation scripts
│   ├── paper/                 # Research claim ledger, evidence tables, IEEE PerCom WiP draft
│   └── main.tex               # 43-slide supervisor review Beamer presentation
├── docs/
│   ├── meetings/              # Transcripts and minutes of advisor meetings (Sem 6)
│   ├── reviews/               # Milestone review presentation decks (Sem 5, Sem 6, Sem 7)
│   ├── CONTRIBUTIONS.md       # Detailed breakdown of individual technical deliverables
│   └── TIMELINE.md            # Month-by-month research and engineering progression
├── experiments/
│   ├── casas/                 # CASAS smart home sequence preprocessing & LSTM models
│   ├── esp32_fall_detection/  # ESP32 CSI fall detection classifiers and notebooks
│   ├── imu_fall_detection/    # Smartphone IMU fall heuristics and alarm actuator interface
│   ├── member_versions/       # Member-specific exploratory pipelines and analysis
│   ├── passive_usrp/          # Amrith's passive USRP activity detection project
│   └── signfi/                # SignFi 2D CNN gesture recognition models and benchmarks
├── provenance/                # File manifests, dependency matrices, and security audits
├── research/                  # Early dataset surveys and reference literature
└── tools/
    ├── switch_identity.sh     # Team identity configuration utility
    └── verify_repository.py   # Automated integrity and evidence verification script
```

---

## Verification & Integrity Checks

To verify all dataset files, notebooks, evidence tables, and model evaluations:

```bash
python3 tools/verify_repository.py
```

This script:
- Verifies all files against their recorded SHA256 hashes.
- Audits notebook JSON structure validity across all experimental notebooks.
- Validates the 9 historical component backups in `.local_history/`.
- Recomputes all participant fold metrics and macro-F1 evaluation tables from saved out-of-fold predictions without requiring GPU re-training.
