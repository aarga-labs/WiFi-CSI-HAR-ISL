# Team Member Contributions

This document outlines the collaborative and individual technical contributions of the team members for the Final Year Project: **"Multimodal Human Activity & Indian Sign Language Recognition for Inclusive Smart Homes"**.

---

## 1. Collaborative & Shared Responsibilities

- **Hardware Testbed Setup**: Joint configuration, alignment, and physical deployment of two Ettus USRP N210 SDRs, SBX daughterboards, tripod antenna mounting, and Gigabit Ethernet switches.
- **Environmental Controls**: Establishing and enforcing controlled room conditions (doors and windows shut, ceiling fan powered off, personal smartphones placed on airplane mode, fixed floor markings for participant positioning).
- **Participant Data Collection Sessions**: Rotating active participant and operator responsibilities across all 5 collection sessions (P01–P05), executing action trials, standing signs, seated signs, and scripted continuous stories.
- **Project Reviews & Deliverables**: Joint authoring and preparation of milestone presentation decks and reports for Semester 5, Semester 6, and Semester 7 reviews.

---

## 2. Individual Technical Domains

### Adhikkesh S K ([`@Adhikkesh`](https://github.com/Adhikkesh))
- **System Architecture**: Designed and maintained the active IEEE 802.11 single-link CSI capture system (`wifi_csi_capture`).
- **Data Collection Orchestration**: Authored automated cue session runners, take recording shell wrappers, and extended protocols (`cue_session.py`, `record_part.sh`, `protocol_p45.py`).
- **Signal Quality & Calibration**: Conducted RX gain sweep analysis and packet inter-arrival timing checks.
- **Model Orchestration**: Implemented Kaggle multi-GPU training orchestration runners (`fyp_fast.py`, `fast_runner.py`) and executed the retained balanced benchmark run (`FYP_BALANCED_2H`).
- **Presentation**: Designed and compiled the 43-slide maroon Beamer presentation (`main.tex`).

### Adithya Ajay ([`@Achilles80`](https://github.com/Achilles80))
- **Benchmark Modeling**: Evaluated SignFi 2D CNN gesture recognition models and subcarrier feature maps (`experiments/signfi/`).
- **Wearable Sensors**: Developed smartphone IMU data collection scripts, complementary filters, and acceleration threshold heuristics for fall detection (`experiments/imu_fall_detection/`).
- **Hardware Actuation**: Implemented ESP32 alarm buzzer and emergency strobe actuation for verified fall alerts.
- **Protocol & Logistics**: Assisted in participant scheduling, take logging, and protocol expansion for seated actions and signs.

### Amrith B ([`@AMRITH03`](https://github.com/AMRITH03))
- **Passive Sensing**: Led the passive USRP Activity Detection System project (`Activity-Detection-System`).
- **RF Flowgraphs**: Configured GNU Radio companion flowgraphs and 200 PPS packet generation routines.
- **Transmitter Station**: Served as primary transmitter operator during multi-USRP data collection sessions.
- **Research Manuscript**: Designated lead author for the IEEE PerCom 2027 Work-in-Progress (WiP) conference manuscript (`current_system/paper/`).

### Gowreesh B ([`@Gowreesh1905`](https://github.com/Gowreesh1905))
- **Deep Learning Architectures**: Developed Recurrence Plot (RP) phase-space trajectory encoders and ResNet-18 classifiers for coarse motion recognition.
- **Baseline Pipeline**: Authored the Phase-1 WiFi CSI activity and ISL sign recognition baseline pipeline (`Model_Detect-Activity-and-Gestures`).
- **Inference Tooling**: Developed standalone inference and training notebooks (`Action_NoAction_imgfi.ipynb`, `CSI_Action_Inference.ipynb`, `USRP_Action_Detection.ipynb`, `fall_detection_corrected_dataset (3).ipynb`).
- **Segmentation**: Evaluated temporal sliding window segmentation and start/stop detection heuristics.

### Rishiikesh S K ([`@Rishiikesh-20`](https://github.com/Rishiikesh-20))
- **Hardware Interfacing**: Developed USRP hardware library wrappers and diagnostic routines (`USRP_lib`).
- **Multi-Channel Experiments**: Built the Two-USRP Three-Channel experiment architecture (`Three_Channel_Experiment`).
- **C++ Block Integration**: Adapted GNU Radio receiver architecture to integrate Team67 C++ signal processing blocks, removing ZMQ dependencies (`USRP_HAR_Project`).
- **Signal Analysis**: Conducted OFDM subcarrier Doppler frequency analysis, phase unwrapping, and noise floor characterization across 52 subcarriers.
- **Review Compilation**: Compiled the 20-page Semester 7 review presentation deck and supporting materials (`FYP_Sem_7_Review (1).pdf`).
