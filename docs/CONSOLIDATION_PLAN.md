# Project Architecture & Development Plan

This document outlines the architectural structure, technical subsystems, and developmental milestones for the Final Year Project: **"Multimodal Human Activity & Indian Sign Language Recognition for Inclusive Smart Homes"**.

---

## 1. System Development Stages

1. **Stage 1: Literature Review & Problem Formulation (Nov 2025 – Jan 2026)**
   - Analysis of ambient and wearable sensing modalities for indoor smart home automation.
   - Initial exploration of WiFi CSI physical layer characteristics and multipath fading.

2. **Stage 2: Public Benchmark Exploration (Feb – Mar 2026)**
   - Sequential activity modeling using CASAS smart home sensor datasets (`experiments/casas/`).
   - Sign language gesture recognition evaluation using the public SignFi CSI dataset (`experiments/signfi/`).
   - Semester 5 and Semester 6 milestone reviews.

3. **Stage 3: Embedded Microcontroller Prototyping (Apr – May 2026)**
   - Implementation of ESP32 CSI standalone receiver and sender firmware (`capture/esp32/`).
   - Real-time motion vs. idle classification using ESPectre.
   - Development of WiFi CSI fall detection classifiers and smartphone IMU acceleration heuristics (`experiments/esp32_fall_detection/`, `experiments/imu_fall_detection/`).

4. **Stage 4: Software-Defined Radio Testbed Bringup (Jun – Jul 2026)**
   - Transition to Ettus USRP N210 SDRs for full 52-subcarrier 20 MHz OFDM CSI acquisition.
   - Authoring UHD hardware interfacing utilities (`experiments/member_versions/rishiikesh/USRP_lib/`).
   - Passive USRP activity sensing and Recurrence Plot ResNet-18 classification (`experiments/passive_usrp/`).

5. **Stage 5: Multi-Channel & Active 802.11 Link Experiments (Aug – Sep 2026)**
   - Evaluation of two-USRP three-channel frequency hopping setups (`Three_Channel_Experiment`).
   - Integration of Team67 C++ signal processing blocks into GNU Radio (`USRP_HAR_Project`).
   - Deployment of dedicated single-channel active IEEE 802.11 CSI capture system on Channel 1 (2412 MHz) (`wifi_csi_capture`).

6. **Stage 6: Phase-1 Participant Dataset, Modeling & Paper Draft (Oct 2026)**
   - Execution of calibrated data collection across 5 participants (P01–P05).
   - Execution of Kaggle multi-GPU training pipeline across 5 leave-one-subject-out (LOSO) folds.
   - Comprehensive model audit, story detection evaluation, and IEEE PerCom WiP manuscript authoring.

---

## 2. Repository Subsystems

| Module | Primary Path | Description |
|---|---|---|
| **Early Studies** | `research/early_studies/`, `research/literature/` | Foundational dataset studies and background surveys. |
| **CASAS Benchmark** | `experiments/casas/` | Sequence preprocessing and 5 LSTM architecture comparisons. |
| **SignFi Benchmark** | `experiments/signfi/` | 2D CNN model implementations for 276 CSI gesture classes. |
| **ESP32 Firmware** | `capture/esp32/` | Sender, receiver, and ESPectre motion detection firmware. |
| **Fall Detection** | `experiments/esp32_fall_detection/`, `experiments/imu_fall_detection/` | WiFi CSI fall classifiers and wearable IMU thresholding. |
| **Passive USRP** | `experiments/passive_usrp/` | Passive SDR activity detection and recurrence plot models. |
| **Three Channel USRP** | `current_system/Three_channel_Exp/` | Historical two-USRP multi-channel capture experiments. |
| **Active CSI Capture** | `current_system/capture_snapshot/` | Active IEEE 802.11 capture runtime and session protocols. |
| **Phase-1 Baseline** | `current_system/Model_Detect.../` | Phase-1 activity and ISL sign recognition baseline pipeline. |
| **Kaggle GPU Training** | `current_system/Kaggle_P1_P5/` | Fast and balanced multi-worker training runs, model cards, and predictions. |
| **Presentation** | `current_system/main.tex`, `current_system/current_impl/` | 43-slide supervisor review Beamer presentation and vector figures. |
| **Conference Manuscript** | `current_system/paper/` | Claim ledger, primary evidence CSVs, and IEEE PerCom WiP draft. |
| **Verification Tools** | `tools/` | Automated integrity, SHA256 hashing, and metric recomputation scripts. |
