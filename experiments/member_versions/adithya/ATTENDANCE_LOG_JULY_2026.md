# Attendance & Project Progress Log (July 1 - July 20, 2026)

This log tracks the daily work, collaborative coding sessions, data collection runs, and theoretical studies completed for the **USRP N210 Channel State Information (CSI) Human Activity Recognition (HAR)** project. 

- **Period**: July 1, 2026 to July 20, 2026 (Monday to Friday only).
- **Format**: Daily task entries divided into **Work Planned**, **Work Completed**, and **Technical Study & Research** sections. Tuesdays, Wednesdays, and Thursdays feature more detailed tasks to highlight research investigations, hardware debugging, and model design decisions.
- **Collaborators**: Rishiikesh, Amrith, Gowreesh (collaborative team effort).

---

## Daily Logs

### Week 1: July 1 – July 3

#### Wednesday, July 1 (Extra Tasks Day) — Hardware Workspace Setup & Link Alignment
* **Work Planned**:
  * Establish the physical sensing environment, define geometry parameters, and configure network links for the USRP N210.
* **Work Completed**:
  * Aligned the USRP N210, MacBook Pro, and Android phone (hotspot) on the floor using fixed tape marks for geometric consistency across capture sessions.
  * Configured host and USRP network interfaces (Fedora host IP `192.168.10.1/24`, USRP IP `192.168.10.7` on interface `eno1`).
* **Technical Study & Research**:
  * **Link Geometry**: Measured and documented link parameters. Set MacBook-to-USRP distance to 3.5 meters and antenna height to 1.1 meters (matching the torso level of standing subjects) to ensure direct path signal blocking. Locked Channel 11 ($2.462\text{ GHz}$) as the initial operating frequency.

#### Thursday, July 2 (Extra Tasks Day) — Physical CSI Principles & Phase Noise Study
* **Work Planned**:
  * Conduct a literature review on CSI fundamentals and evaluate if carrier phase can be used for motion classification.
* **Work Completed**:
  * Studied OFDM physical layer details and the representation of subcarriers.
* **Technical Study & Research**:
  * **OFDM Subcarrier Extraction**: Determined that standard 20 MHz 802.11a/g frames have 64 FFT subcarrier slots, with 12 null/guard subcarriers and 52 active subcarriers.
  * **Phase Noise Analysis**: Studied three phase noise sources: CFO (Carrier Frequency Offset), SFO (Sampling Frequency Offset), and PBD (Packet Boundary Detection) timing errors that randomize phase packet-to-packet. Since a SISO (single antenna) system cannot use differential phase subtraction, we officially decided to drop phase and utilize amplitude only ($|H_k| = \sqrt{Re_k^2 + Im_k^2}$).

#### Friday, July 3 — GNU Radio Companion Verification
* **Work Planned**:
  * Verify GNU Radio companion setup and analyze Bastian Bloessl's `gr-ieee802-11` block layout.
* **Work Completed**:
  * Checked the installation and compatibility of the `gr-ieee802-11` OOT block. Outlined code changes for `extract_csi_impl.cc` to log data directly to CSV from PDU inputs instead of passing vectors downstream.

---

### Week 2: July 6 – July 10

#### Monday, July 6 — Implementing Custom MAC Filtering
* **Work Planned**:
  * Modify `extract_csi_impl.cc` to implement dynamic MAC filtering and CSV saving.
* **Work Completed**:
  * Edited C++ files `extract_csi_impl.cc` and `extract_csi_impl.h`. Coded custom PDU handling that reads environment variables `CSI_TA`, `CSI_RA`, and `CSI_OUT` at runtime, filtering frames by MAC and appending to CSV directly.

#### Tuesday, July 7 (Extra Tasks Day) — Module Compilation & Verification Gates Design
* **Work Planned**:
  * Rebuild the modified `gr-ieee802-11` module and establish QA gates for recording sessions.
* **Work Completed**:
  * Recompiled the module (`make -j$(nproc) && sudo make install && sudo ldconfig`). Verified compilation using `strings` to check environment variable detection.
* **Technical Study & Research**:
  * **QA Gates formulation**: Formulated **6 Verification Gates** to prevent corrupted data collection: Gate 1 (MAC check), Gate 2 (channel-frequency mapping), Gate 3 (macOS gateway ping at `-i 0.01` to enforce 100 pkt/s), Gate 4 (Rate Gate for $\ge 50$ rows/s), Gate 5 (Wiggle Test to confirm motion sensitivity), and Gate 6 (Gain/Saturation checking via `uhd_fft`).

#### Wednesday, July 8 (Extra Tasks Day) — ImgFi Paper Study & Image Conversion
* **Work Planned**:
  * Study the ImgFi paper (Zhang & Jiao, 2023) and write image conversion scripts.
* **Work Completed**:
  * Developed `make_images.py` to convert CSI amplitude matrices into 224x224 grayscale recurrence transformation (RT) images.
* **Technical Study & Research**:
  * **RT Image Math**: Analyzed why RT ($RT[i,j]=|x_i-x_j|$) outperforms other transformations (GASF, GADF, MTF, STFT) by preserving continuous amplitude relationships between times $i$ and $j$ without arbitrary thresholds. Verified that treating each of the 52 subcarriers as a separate image increases training data by $52\times$ without losing temporal relationships.

#### Thursday, July 9 (Extra Tasks Day) — Session Logger Scripting & Activity Definitions
* **Work Planned**:
  * Develop session recording scripts and standardize activity performance protocols.
* **Work Completed**:
  * Programmed `session_logger.py` supporting both discrete repetition logging (saving start/end timestamps on ENTER) and continuous logging (`--continuous`).
* **Technical Study & Research**:
  * **Standard Activity Rules**: Defined exact protocols for the 7 classes: `walk` (continuous traversal), `squat` (2-3s full range), `bend` (2-3s pick-up motion), `drink` (2-3s sip motion), `nod` (3-4 clear head movements), `noaction` (sitting/standing still), and `empty` (room vacated).

#### Friday, July 10 — Verification Gate Testing
* **Work Planned**:
  * Run verification gates on the host systems and resolve environment issues.
* **Work Completed**:
  * Tested MacBook gateway pinging and verified Fedora receiver compatibility under rotating MACs. Handled MAC changes by updating environment variables.

---

### Week 3: July 13 – July 17

#### Monday, July 13 — Preliminary Calibration Captures
* **Work Planned**:
  * Perform test captures and evaluate packet interval statistics.
* **Work Completed**:
  * Saved calibration data (`csi_noaction.csv`) and verified packet rates under ambient noise conditions.
* **Technical Study & Research**:
  * **Packet Jitter**: Analyzed arrival timestamps, identifying a median gap of 12 ms and maximum gap of 464 ms, highlighting the need for linear time-resampling.

#### Tuesday, July 14 (Extra Tasks Day) — Window Segmentation & Resampling Design
* **Work Planned**:
  * Write window segmentation scripts and analyze resampling frequencies.
* **Work Completed**:
  * Developed `segment_windows.py` to slice CSI amplitude and resample irregular packets onto a uniform 100 Hz grid using linear interpolation.
* **Technical Study & Research**:
  * **Interpolation Gating**: Evaluated the interpolation trade-off. Since the actual average packet rate is ~66 Hz, windowing with a target of 100 Hz requires a high packet count. Implemented a fill check threshold that skips any window with $<50\%$ of expected packets to prevent artificial signal patterns.

#### Wednesday, July 15 (Extra Tasks Day) — Multi-Subject Captures & QA Script Development
* **Work Planned**:
  * Capture preliminary multi-subject data and automate QA checks.
* **Work Completed**:
  * Captured test files for Amrith and Rishiikesh (`Amrith_action_test_1.csv`, `Rishikesh_action_test.csv`, `csi_data_noaction_15july.csv`). Coded `check_capture.py` to automate QA checks.
* **Technical Study & Research**:
  * **QA Criteria**: Programmed check criteria in `check_capture.py` to automatically detect row rate drops, NaNs, all-zero columns, and plot amplitude-over-time curves (Wiggle Test verification).

#### Thursday, July 16 (Extra Tasks Day) — Doppler Shift & Sampling Frequency Study
* **Work Planned**:
  * Calculate Doppler shift parameters and check sampling rate sufficiency.
* **Work Completed**:
  * Conducted spectral analysis on `action` vs `noaction` calibration files.
* **Technical Study & Research**:
  * **Doppler Shift math**: Calculated Doppler scaling: $f_d = \frac{2 v f_c}{c}$. At 2.462 GHz, Doppler shift is $16.4\text{ Hz}$ per m/s of radial movement. Found that discriminative signal energy drops to the noise floor above $18\text{ Hz}$. Checked Nyquist headroom: our worst-case rate (51.5 Hz) gives a Nyquist frequency of 25.8 Hz, and our median (66.4 Hz) gives 33.2 Hz, providing sufficient headroom for body movements (though fast hand gestures could alias).

#### Friday, July 17 — Formal Pilot Dataset Collection
* **Work Planned**:
  * Capture the official binary pilot dataset for the action vs noaction study.
* **Work Completed**:
  * Collected 8 official pilot CSVs for Rishiikesh and Amrith (walk, stand, mixed, sit) spanning 90 seconds each. Ran `check_capture.py` on all files to confirm they passed QA (51-78 rows/s, 0 NaNs).

---

### Week 4: July 20

#### Monday, July 20 — Model Development & Comparative Analysis
* **Work Planned**:
  * Process the pilot dataset, train the ResNet-18 ImgFi baseline, and build the custom CNN-BiGRU-Attention model.
* **Work Completed**:
  * Segmented windows with `--rate 50` to avoid dropped windows. Trained ResNet-18 majority-vote baseline (`Action_NoAction_imgfi.ipynb`) and custom CNN-BiGRU-Attention model (`Action_NoAction_CNN_GRU.ipynb`). Ran leave-one-subject-out (LOSO) cross-validation.
* **Technical Study & Research**:
  1. **Effective Rank**: Calculated $Rank_{eff} = \exp(-\sum \tilde{\lambda}_i \ln \tilde{\lambda}_i)$. Found a rank of 3.8 for action and 11.9 for noaction, proving that subcarriers collapse to ~4 independent dimensions during movement due to a single large perturber.
  2. **Stand vs. Sit**: Observed that `stand` was the hardest class (95.1% acc) due to postural sway and breathing, whereas `sit` was 100% due to mechanical bracing.
  3. **Model comparison**: Verified that our 0.57 M parameter CNN-BiGRU-Attention model matches the 11.2 M parameter ResNet-18 majority-vote accuracy (98.35% test accuracy) while using 19.6x fewer parameters and 52x fewer forward passes (0.55 ms inference).
  4. **Baseline comparison**: Checked a single motion energy scalar threshold (average subcarrier standard deviation), which also got 98.35% accuracy, indicating that the binary task is simple and the custom model's real value lies in sequential multi-class actions.

---

## Attendance Summary Table

| Date | Day | Hours | Planned Work Summary | Completed Work Summary | Key Parameters / Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **July 1** | Wed | 8.0 | Setup physical environment & links | Aligned USRP, MacBook, Android phone; configured IP links | 3.5 m line-of-sight path, 1.1 m antenna height, Channel 11 |
| **July 2** | Thu | 8.0 | Review OFDM & carrier phase noise | Studied FFT sizes, 52 subcarrier output, and CFO/SFO/PBD offsets | Selected amplitude-only $|H| = \sqrt{Re^2 + Im^2}$ |
| **July 3** | Fri | 6.0 | Check GNU Radio module setup | Evaluated Bastian Bloessl's `gr-ieee802-11` module installation | Identified code changes for CSV output |
| **July 6** | Mon | 7.5 | Code dynamic MAC filtering in C++ | Modified `extract_csi_impl.cc` to read filter variables | Support `CSI_TA`, `CSI_RA`, `CSI_OUT` env vars |
| **July 7** | Tue | 8.0 | Compile OOT module & design QA gates | Recompiled `gr-ieee802-11` module; defined 6 QA gates | Gates include Rate Gate ($\ge 50$ rows/s) and Wiggle Test |
| **July 8** | Wed | 8.0 | Study ImgFi paper & image coding | Developed `make_images.py` for recurrence transformations | $RT[i, j] = \|x_i - x_j\|$, grayscale 224x224 |
| **July 9** | Thu | 8.0 | Script logging & activity boundaries | Coded `session_logger.py` with discrete and continuous modes | Defined standard protocols for 7 target classes |
| **July 10** | Fri | 6.0 | Test verification gates | Ran MAC check and wiggle tests; resolved MAC drift | Gateway pinging stabilized MAC detection |
| **July 13** | Mon | 6.5 | Ambient capture & interval analysis | Captured `csi_noaction.csv`; checked packet spacing | Observed packet spacing jitter (up to 464 ms) |
| **July 14** | Tue | 8.0 | Code segmentation & resampling | Programmed `segment_windows.py` linear resampling | Standardized windows onto uniform 100 Hz grid |
| **July 15** | Wed | 8.0 | Collect multi-subject test data & QA | Captured test data; coded automated QA script `check_capture.py` | Automatically flags row drops, NaNs, and zero rows |
| **July 16** | Thu | 8.0 | Study Doppler shifts & sample rates | Checked Nyquist sufficiency; analyzed discriminative frequency bands | Doppler scaling: $16.4\text{ Hz}$ per m/s; signal band $<18\text{ Hz}$ |
| **July 17** | Fri | 7.0 | Collect official pilot dataset | Captured 8 official action/noaction CSVs (walk, stand, mixed, sit) | Checked all files passed QA checks |
| **July 20** | Mon | 8.5 | Segment windows and train ML models | Segmented data at rate 50; trained ResNet-18 and CNN-BiGRU-Attention | CNN-BiGRU-Attention got 98.35% accuracy using 0.57 M parameters |
