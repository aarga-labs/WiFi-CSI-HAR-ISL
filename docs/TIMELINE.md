# Project Development Timeline (February – October 2026)

This timeline documents the key technical milestones, experimental deliverables, and research progression accomplished by the team throughout the project lifecycle.

| Period | Milestone & Scope | Key Artifacts & Deliverables |
|---|---|---|
| **Before February** | Literature review, smart home ambient sensing surveys, and preliminary sensor feasibility studies. | `research/early_studies/`, `research/literature/` |
| **February** | **Semester 5 Review 1**: CASAS smart home sequence preprocessing, comparative evaluation of 5 LSTM architectures, and multimodal smart home design. | `current_system/Review/Sem5_Review1/final_ig.pdf`, `experiments/casas/` |
| **March** | **Semester 6 Review 2**: Wearable and ambient sensor benchmarks (OPPORTUNITY dataset), initial SignFi CSI gesture study, and emergency alarm actuator designs. | `current_system/Review/Sem6_Review2/FYP_updated.pdf`, `Final_Report_FYP.pdf`, `docs/reviews/sem6_supporting/Review_2/` |
| **April** | SignFi 2D CNN gesture modeling; Advisor feedback (Meetings 5, 6, 7) on CSI signal analysis and segmentation; ESPectre motion vs. idle demo on ESP32. | `docs/meetings/sem6/17_April_11AM.docx`, `17_April_3PM.docx`, `24_April.docx`, `capture/esp32/espectre/`, `experiments/signfi/` |
| **May** | ESP32 CSI standalone receiver, sender firmware, serial data logging, WiFi CSI fall detection classifiers, and smartphone IMU logging scripts. | `capture/esp32/sender/`, `capture/esp32/standalone_receiver/`, `experiments/esp32_fall_detection/`, `experiments/imu_fall_detection/` |
| **June** | Transition to Ettus USRP N210 SDRs; GNU Radio companion flowgraphs, UHD hardware library wrappers (`USRP_lib`), and laboratory RF setup. | `experiments/member_versions/rishiikesh/USRP_lib/`, `current_system/setup_img/`, `current_system/others/` |
| **July** | Passive USRP Activity Detection System (`Activity-Detection-System`); July 17 & 20 pilot CSI recordings; Recurrence Plot (RP) ResNet-18 model; comparative analysis report. | `experiments/passive_usrp/`, `current_system/others/Works/Action and No action/comparative_analysis.pdf`, `experiments/member_versions/gowreesh/` |
| **August** | Active Two-USRP Three-Channel experiment (`Three_Channel_Experiment`); Team67 C++ GNU Radio block integration; Doppler analysis across 52 subcarriers; **Semester 7 Review**. | `experiments/member_versions/rishiikesh/FYP_Sem_7_Review (1).pdf`, `experiments/member_versions/rishiikesh/usrp-projects/` |
| **September** | Active IEEE 802.11 CSI link on Channel 1 (2412 MHz); dedicated `wifi_csi_capture` suite; Phase-1 protocol definition; cueing tools and session orchestration. | `capture_snapshot/wifi_csi_capture/`, `current_system/pilot_tools/`, `RO1_RO2_APPROVAL_PLAN.md` |
| **October** | Receiver gain calibration; P01–P03 data collection; Phase-1 baseline model; protocol extension for P04–P05 (cooking, seated blocks, S-SEQ story); Kaggle multi-GPU balanced benchmark (`FYP_BALANCED_2H`); 43-slide Beamer presentation; IEEE PerCom WiP draft. | `current_system/Adhi_To_Amrith_Context.md`, `CLAIM_LEDGER.md`, `Kaggle_P1_P5/balanced_results_audit_20261017/`, `main.tex` |

---

## Technical Progress Overview

As the project transitioned from public benchmarks (CASAS, SignFi) to embedded microcontrollers (ESP32) and ultimately to Software-Defined Radio (USRP N210), experimental resolution and system capabilities increased significantly:
- **RF Fidelity**: Single-carrier RSSI / coarse ESP32 CSI $\rightarrow$ 52 OFDM subcarriers with 200 PPS temporal sampling on USRP N210.
- **Task Scope**: Coarse motion vs. idle $\rightarrow$ 12 isolated activities $\rightarrow$ 14 ISL signs $\rightarrow$ continuous scripted sequential stories.
- **Model Progression**: Vanilla LSTMs $\rightarrow$ 2D CNNs $\rightarrow$ Recurrence Plot ResNet-18 $\rightarrow$ Dilated Residual 1D CNN with Group Normalization.
