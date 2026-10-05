# Smart Home Multi-User Activity Recognition FYP - Complete Context Document
## Team 67, CSE Department, Amrita Vishwa Vidyapeetham

---

## 1. PROJECT OVERVIEW

Your Final Year Project (FYP) is focused on **Smart Home Automation with Multi-User Activity Recognition and Privacy-Preserving Federated Learning**. The project is being conducted by a team of **5 final-year Computer Science students** at Amrita Vishwa Vidyapeetham under the guidance of **Dr. Nalinadevi K** (Associate Professor, Department of CSE). The project duration is approximately **1 year** (ongoing until December 2026), with the constraint that the team is working part-time (approximately 70% effort) as they have other coursework and commitments.

The fundamental goal of the project is to create a **complete product-level solution** that can be deployed in real-world smart home environments, capable of identifying multiple users in a home and personalizing automation based on individual user preferences and patterns, all while maintaining user privacy through federated learning techniques.

---

## 2. CURRENT PROBLEM STATEMENT (USER'S UNDERSTANDING)

### 2.1 Initial Problem Definition

Your team has identified that current smart home systems have significant limitations:

1. **Lack of Personalization**: Most commercial smart home systems treat all residents as a single entity (e.g., "the home" rather than "User A" or "User B"). There is no way to distinguish which user is performing which activity.

2. **Privacy Concerns**: Many existing solutions use cameras for surveillance, which raises serious privacy concerns. Your team wants to avoid this entirely by using **only ambient sensors** (motion, door contact, temperature) and **wearable devices** (smartwatches with sensors, not cameras).

3. **Dataset Gap**: The major challenge is that **most state-of-the-art smart home datasets cannot identify multiple users**. Even CASAS (the gold standard with 2000+ hours of data from 18 apartments) cannot answer the fundamental question: "Which person triggered this sensor?" This is called the **data association problem**.

4. **Hardware Deployment**: Currently, smart home research focuses on either:
   - Ambient sensors only (CASAS, ARAS) - which cannot identify individual users
   - Wearable sensors only (Opportunity dataset) - which uses unrealistically dense sensor networks (15+ sensors per person)
   
   No existing solution combines **minimal practical wearables** (e.g., 1 smartwatch per person) with ambient sensors in real multi-user homes.

5. **Federated Learning Gap**: Federated learning (where models train locally on each device and only share model updates, not raw data) is theoretically ideal for privacy-preserving smart homes. However, existing federated learning papers for activity recognition (FedHome, FeL-MAR) use datasets like CASAS that cannot properly identify users, making their validation incomplete.

### 2.2 Proposed Direction from Guide

Your guide, Dr. Nalinadevi K, has provided specific direction on what the actual research contribution should be:

1. **Focus on Datasets, Not Models**: "Don't focus on models and do something on this area, identify what problem is there." Your guide emphasized that the major work is with **dataset creation and validation**, not in building yet another LSTM vs. GRU comparison. The model is a tool to validate that your dataset works, not your contribution.

2. **Multi-User Identification is Key**: Your guide specifically mentioned that you need to "know exactly who triggered a particular event." This requires using wearables with unique identifiers (e.g., smartwatch with a unique ID tag), not relying on ambient sensors alone.

3. **Minimal Sensor Placement Optimization**: A critical research question is: "How many sensors should be implanted on the body [minimally], and in what positions, to read efficient readings of all activities involving different parts of the body?" Your guide noted that "not many made it" and head motion sensors are rarely explored for activity recognition.

4. **Real-World Deployment**: The "complete product at the end" means deploying the system in actual homes with real residents, not just simulating or prototyping in a lab. The system should continuously learn and adapt based on actual usage.

5. **Federated Learning for Personalization**: The federated learning framework should enable **continuous personalization** - each resident's local model on their edge device learns their personal patterns while the global model improves across all homes without sharing raw data.

6. **Security and Privacy by Design**: Using wearables instead of cameras (no visual surveillance), and using federated learning (data never leaves home), are core privacy-preserving design choices.

---

## 3. GUIDE'S FEEDBACK FROM MEETINGS (December 18, 2025 Meeting Transcript)

### 3.1 Federated Learning Implementation

During the December 18 meeting with Dr. Nalinadevi K:

**Your Team's Status**:
- Member 1 (Adhikesh S K) reported: "We are currently using multiple types of sensors to capture data inside a home environment. These include ambient sensors such as motion, door, temperature, pressure, and object usage. Datasets include CASAS, Kastrons, and ARAS. These datasets mainly focus on ambient sensing with some object-based sensors."

- Member 1 also mentioned: "We are using Basil's VLE Gateway in the lab, and the nRF 52480 with WiFi support as part of our sensing infrastructure."

- The team has already done a **prototype of federated learning**, not a complete model yet, just proof of concept.

**Guide's Specific Direction**:

1. **Sensor Placement Focus**: "How many sensors should be implanted on the body [minimal], and in what positions can have an efficient reading about all the activities involving different parts of the body? Some of them even involve a head, right? Not many have experimented with head motions and things like that."

2. **Wearable ID for User Identification**: "We need wearable. I'm planning to go with wearable so that we know exactly who triggered a particular event. Till now in all the data sets we don't have a distinction between user one and user."

3. **Federated Learning Necessity**: "You want to hide the privacy of an individual. This personal choices should be totally secure and private. That's when Federated learning comes in."

4. **Research Paper References**: Your guide mentioned she will send papers on:
   - Federated learning approaches they have published (heavily referenced)
   - Papers on sensor placement optimization
   - Work addressing minimal IMU placement for activity recognition

5. **Not About Model Comparison**: When members asked about using LSTM vs. GRU vs. TCN models, the guide said: "Don't focus on model and do something on this area, identify what problem is there. Formulate the problem statement, don't change the problem statement, focus on literature survey, what is happening in this field."

### 3.2 Dataset Requirements Clarified

From the guide's feedback across multiple meetings:

1. **CASAS Limitations are Known**: The guide explicitly referenced CASAS and pointed out that despite having 2000+ hours of data, it cannot identify which user did what. This is the core gap your project must address.

2. **Multi-Resident Context Required**: "How many dataset came from that particular [dataset]? Different places all across the world, and how many papers used it and solved problems like sequential, what are the significance of the data (CASAS talks about inter-class variation and intra-class similarity), data association, put three columns - challenge they handled, how many sensors they used, what were they not able to reach the accuracy, interoperability."

3. **Ontology and Common Kits**: Your guide mentioned exploring "ontology based" work and studying "common kits like for smart home, smart office."

4. **Abnormal Detection and Applications**: The literature should cover "abnormal detection, list of applications, list of products, industry works, academic works."

5. **Proof of Novelty**: "First have a proof that this ps is still new by searching between 2021 to 2025." Your research contribution must be justified by showing that the problem hasn't been fully solved in recent literature.

---

## 4. TEAM STRUCTURE AND MEMBER ASSIGNMENTS

Your team consists of **5 members**, each assigned to research a different dataset or sensing modality:

### 4.1 Member 1: Adhikesh S K (CB.SC.U4CSE23101) - CASAS Dataset

**Assignment**: Ambient sensor-based smart home activity recognition using CASAS dataset

**Research Findings**:
- CASAS is the "gold standard" for ambient sensor-based smart home research
- Uses Zigbee wireless protocol for sensor communication
- Sensor types: Motion (PIR), Door/Window contact sensors, Temperature, Light, Item sensors
- Three-layer architecture: Physical Layer (sensors) → Middleware Layer (Zigbee network) → Application Layer (AI decision-making)
- Activity Recognition (AR) tested in 18 apartments with 84% accuracy
- Activity Discovery (AD) using unsupervised learning to find repeating patterns
- Applications: Health assistance (aging in place), energy efficiency
- **Key Problem Identified**: CASAS cannot identify which user triggered a sensor when multiple residents are present. The data association problem means that simultaneous activities cannot be properly distinguished between different users

---

### 4.2 Member 2: Aditya Ajay (CB.SC.U4CSE23102) - ARAS Dataset

**Assignment**: Multi-resident ambient sensor smart home dataset analysis

**Research Findings**:
- ARAS collected from 2 real houses: House A (50m², 2 male roommates age 25) and House B (90m², married couple average age 34)
- 30 days continuous recording per house (60 days total)
- 20 binary sensors per house using ZigBee protocol
- Sensor types: Force Sensitive Resistors (FSR) under beds/couches, PIR motion sensors, Reed switches on doors/cabinets, Photocells in drawers, Temperature sensors on kitchen appliances, Sonar distance sensors
- 27 distinct activities captured: Sleeping, Toileting, Showering, Brushing Teeth, Watching TV, Studying, Using Internet, Preparing Breakfast/Lunch/Dinner, Having conversations, Having guests
- Deep Learning results: GRU models achieved 88% accuracy on House B
- **Key Problem Identified**: Although ARAS is explicitly multi-resident, it suffers from the same fundamental limitation as CASAS. As documented in Liang et al. (2021) research: "Once single-person activity recognition is applied to the multi-person environment, it will fail to identify different residents' activities." The paper states: "ambient sensors are anonymous" - no feature exists to indicate if motion was Resident 1 or Resident 2. Complex workarounds using historical habit modeling were required but these don't enable real-time detection of behavior changes

---

### 4.3 Member 3: Amrith B (CB.SC.U4CSE23105) - Opportunity Dataset

**Assignment**: Wearable sensor-based multi-modal activity recognition

**Research Findings**:
- Opportunity dataset: 4 subjects, 25 hours total recording, 72 sensors per person
- Wearable configuration (heavily over-instrumented): 5 XSense IMUs on motion jacket, 12 Bluetooth 3-axis accelerometers on upper/lower limbs, 2 InertiaCube3 inertial sensors on feet
- Recorded in single studio-flat mock-up with kitchen, doors, drawers, fridge, dishwasher, table, deckchair
- 27,000+ atomic activities annotated at multiple levels: high-level situations, composite activities, atomic activities/gestures
- Excellent benchmark capability with weighted F-measure evaluation
- Tasks: locomotion modes (stand, sit, walk, lie), activity spotting, right-arm gesture recognition (17 classes), robustness to sensor noise
- **Critical Limitations Identified**: 
  1. **Unrealistic Wearable Setup**: 15+ sensors vs. practical 1-2 wearables that residents would tolerate
  2. **Lab-Only Environment**: Single controlled studio-flat, not real homes with diverse layouts
  3. **Scripted Activities**: Limited morning routine repertoire, not the rich diversity of everyday life
  4. **Short-Term Data**: Only handful of ADL runs plus one drill run; no weeks/months data needed for personalization
  5. **No Multi-Resident Context**: Assumes single instrumented subject per recording
  6. **Domain Gap**: Models trained on Opportunity's dense sensor network won't work when deployed with minimal practical wearables

---

### 4.4 Member 4: Smartphone-Based HAR (UCI-HAR & UniMiB-SHAR)

**Assignment**: Mobile phone accelerometer-based activity recognition

**Research Findings**:

**UCI-HAR Dataset**:
- 30 subjects (males), Samsung Galaxy S II smartphone worn on waist
- Fixed sensor placement on phone
- Sensors: Accelerometer + Gyroscope (3-axis each), Sampling Rate 50 Hz
- 6 activities: Walking, Walking upstairs/downstairs, Sitting, Standing, Laying
- Pre-segmented data windows (2.56 seconds, 128 samples)
- Clean, structured activity labels

**UniMiB-SHAR Dataset**:
- 30 subjects (6 male, 24 female), Samsung Galaxy Nexus smartphone
- Variable placement (typically front trouser pockets)
- Sensors: Accelerometer only (3-axis), Sampling Rate 50 Hz
- 17 daily activities + 8 fall types (25 total classes)
- Raw accelerometer windows around events (~3 seconds)

**Technical Solution Proposed**: TCN-GRU hybrid network
- Temporal Convolutional Network (TCN) for spatial features
- Gated Recurrent Unit (GRU) for temporal dependencies
- Significantly reduces computational cost compared to LSTM
- Results: 97.25% accuracy on UCI-HAR, 93.51% on UniMiB-SHAR with only 0.18-0.19 million trainable parameters

**Research on Missing Data Issues**:
- Investigated handling of simulated missing sensor data using SimpleImputer (mean/median) and KNNImputer
- Activity recognition maintained 93.89% accuracy with missing data handling
- Subject recognition dropped to 80.19% accuracy with missing data
- KNN imputation performed better than mean/median imputation

**Applications Identified**:
- AAL (Ambient Assisted Living): Remote monitoring of elderly with dementia
- Healthcare: e-health systems, remote patient care, respiratory biofeedback, movement assessment
- Fitness and Sports: Automated movement detection, athlete performance evaluation
- Security and Surveillance

**Critical Issues Identified**:
1. **Fall Detection Ambiguity**: Phone drops captured as falls (acceleration signature identical)
2. **Stationary Activity Confusion**: Sitting, Standing, Lying difficult to distinguish from accelerometer alone
3. **Sensor Data Loss Impact**: Subject recognition accuracy drops significantly with missing sensor data
4. **No Multi-User Context**: All datasets purely single-user in lab environments
5. **No Smart Home Integration**: Smartphone-only approach doesn't leverage ambient home context
6. **Gyroscope Importance**: Gyroscope adds crucial information but not all phones have reliable gyroscope sensors

---

### 4.5 Member 5: Non-Wearable/Ambient Sensing (WiFi-HAR & Kastrons)

**Assignment**: WiFi-based and alternative ambient sensing approaches

**Research Findings**:

**WiFi-HAR via Channel State Information (CSI)**:
- Uses standard WiFi signals without cameras
- How it works: When human moves between transmitter (router) and receiver, signals scatter and reflect. CSI (Channel State Information) captures fine-grained signal changes (amplitude & phase) across multiple subcarriers
- Dataset: Single room deployment, 7 activities (Walking, Sitting, Standing, Lying, Getting Up/Down, No Activity)
- Setup: TP-Link TL-WDR4300 router, 60 (5 GHz band), 40 MHz bandwidth, 2 Tx × 2 Rx (MIMO), 114 subcarriers
- Model: DeepConvLSTM (convolutional layers for spatial features + LSTM for temporal patterns)
- Performance: 87% test accuracy with 11 ADL classes
- Democratization: Moved from obsolete Intel 5300 NIC to Raspberry Pi 4 for accessibility
- Released CSIKit (Python tool) for easy data parsing

**Advanced WiFi Research**:

1. **Wisor-DL (Cross-Domain Robustness)**:
   - Solves "cross-domain" problem: training in Room A, testing in Room B
   - Uses Tensor Decomposition for noise cleaning
   - GTCN-RC (Gated Temporal Convolutional Network) + Dendrite Network
   - Accuracy drop <1% when changing rooms (vs. 15% for standard models)
   - Limitation: Cannot handle multi-user tracking

2. **CSI-Bench (Large-Scale In-the-Wild)**:
   - Scale: 461 hours, 35 users, 26 environments
   - Multi-Task Learning: One model predicts Identity, Activity, AND Proximity simultaneously
   - Models: VIT (Vision Transformer) and PatchTST
   - Performance drops significantly on "Out of Distribution" (new) users

3. **WIMANS (Multi-User Benchmark)**:
   - Handles 0-5 concurrent users
   - Dual-band (2.4/5 GHz), synchronized video ground truth
   - Benchmarked THAT (Two-Stream Transformer) and CNNs
   - **Critical Finding**: WiFi models struggle to distinguish activities when 3+ people moving (~60% accuracy)
   - Can identify WHO is there but cannot reliably identify WHAT each person is doing

4. **Advanced Techniques**:
   - TED-Net: Fall detection via skeleton reconstruction (privacy-preserving visualization)
   - DPWIT: Temporal activity detection (finding when actions start/stop in continuous stream)
   - RIS for WiFi 6E: Hand gesture recognition using Reconfigurable Intelligent Surfaces (emerging hardware)

**Critical Gaps Identified**:
1. **Multi-User Activity Recognition Failure**: WiFi can identify user presence but activity recognition collapses with 3+ concurrent users (~60% accuracy)
2. **Privacy Claims Overstated**: While no camera, WiFi CSI signals can potentially be reverse-engineered to infer behavior
3. **Domain Shift Problem**: Models trained in one environment often fail in new environments without adaptation
4. **Fine-Grained Recognition Limits**: Cannot distinguish detailed interactions (hand positions, precise movements)
5. **Robustness Issues**: Phase errors and signal noise reduce reliability compared to wearable accelerometers

---

## 5. IDENTIFIED PROBLEMS WITH EXISTING DATASETS

### 5.1 Universal Problem: Data Association Ambiguity

**The Core Issue**: All existing smart home datasets suffer from an inability to explicitly identify which user performed which activity in multi-resident scenarios.

- **CASAS**: 2000+ hours but cannot answer "Which person triggered this motion sensor?"
- **ARAS**: Explicitly multi-resident but has "anonymous" ambient sensors
- **Opportunity**: Explicitly identifies users BUT is lab-only with unrealistic 15+ sensors per person
- **UCI-HAR & UniMiB-SHAR**: Single-user only, smartphone-based
- **WiFi-HAR**: Can identify presence but struggles with activity distinction in multi-user scenarios
- **CSI-Bench**: Can identify users but accuracy drops for new users and multi-user scenarios

### 5.2 CASAS Specific Problems

1. **Cannot Distinguish Users**: Motion sensors in shared spaces (living room, kitchen) cannot determine which resident is moving
2. **Streaming Recognition Challenges**: Sliding window approach struggles with concurrent activities
3. **Short vs. Long Activity Bias**: System performs well on long activities like "Reading Magazine" (94% accuracy) but poorly on short activities like "Setting the Table" (21% accuracy)
4. **50% "Other" Class Problem**: About 50% of real-world data is "Other" (random movements not labeled activities); system struggles to distinguish specific activities from this noise

### 5.3 ARAS Specific Problems

1. **Same Room Ambiguity**: If Resident A is sitting and Resident B is walking in same room, system cannot determine which sensor event belongs to which person
2. **Complex Activity Confusion**: Difficulty distinguishing cooking steps; captures only general "Preparing Meal" state
3. **Concurrent Activity Failure**: When multiple residents engage in different activities simultaneously in different rooms, the system works, but overlapping activities cause confusion
4. **Multi-Resident Accuracy Drop**: Accuracy of 88% in controlled scenarios drops significantly in realistic multi-person overlapping situations

### 5.4 Opportunity Specific Problems

1. **Over-Instrumentation**: 15+ sensors per person completely impractical for real-world deployment
2. **Lab Artifact**: Single controlled studio environment doesn't represent real home diversity
3. **Scripted Routines**: Limited activity repertoire (morning routine) vs. real everyday diversity
4. **Short-Term Recording**: Insufficient data to model personalization, routine changes, or long-term adaptation
5. **No Ecological Validity**: Realistic homes have different layouts, appliances, family structures, and cultural practices

### 5.5 Smartphone-Based (UCI-HAR, UniMiB-SHAR) Problems

1. **Fall Detection False Positives**: Phone drops register as falls; acceleration signatures identical
2. **Stationary Activity Confusion**: Sitting, Standing, Lying very difficult to distinguish from accelerometer alone
3. **Placement Variability**: Performance depends heavily on where phone is worn (pocket, waist, hand, etc.)
4. **Single-User Only**: No multi-resident capability
5. **Missing Sensor Resilience**: Subject recognition drops 20-25% with missing gyroscope data
6. **No Home Context**: No ambient information to provide activity context

### 5.6 WiFi-HAR Specific Problems

1. **Multi-User Activity Recognition Collapse**: Accuracy drops to ~60% when 3+ concurrent users with different activities
2. **Requires Line-of-Sight**: Performance depends on router-to-person visibility
3. **Environment Sensitivity**: Furniture, walls, materials significantly impact CSI signal quality
4. **Privacy False Sense**: While no video, CSI can potentially be reverse-engineered to infer detailed behavior
5. **Cross-Domain Generalization**: Models trained in one environment often fail in new environments

---

## 6. RESEARCH CONTRIBUTIONS YOUR PROJECT WILL MAKE

Based on the identified gaps, your project will contribute:

### 6.1 Primary Contribution: Multi-User Dataset with Explicit User Identification

**What Exists**: CASAS (2000+ hours but anonymous), Opportunity (4 users but 15+ sensors, lab-only)

**What You'll Create**: First smart home dataset with:
- Explicit user identification using minimal wearables (not cameras for privacy)
- 3-5+ residents per home across 3-4 real houses
- 500-1000+ hours of annotated activity data
- Every activity explicitly labeled: [User ID, Activity Type, Timestamp]
- Multi-modal: Wearable sensors + Ambient sensors + Synchronized timestamps
- **Solves 15-year gap**: CASAS still can't do this despite 2000+ hours

### 6.2 Secondary Contribution: Optimal Sensor Placement for Federated Learning

**What's Known**: General literature shows 5-8 sensors optimal for full-body HAR

**What's Unknown**: Minimal sensor placement specifically optimized for:
- Federated learning on edge devices (power constraints)
- Resource-constrained IoT devices (computation limits)
- Real home deployment (not lab conditions)
- Multi-user activity distinction

**Your Contribution**: Systematic study showing "For multi-home federated learning with edge devices, N sensors at positions [X,Y,Z] achieve >85% accuracy while consuming <W watts"

### 6.3 Tertiary Contribution: Practical Federated Learning Framework

**What Exists**: FedHome, FeL-MAR papers use broken datasets (CASAS which can't identify users)

**What You'll Do**:
- Implement federated learning on PROPER multi-user data
- Demonstrate privacy-utility trade-off
- Show personalization improvements with federated vs. centralized training
- Provide reproducible framework for future researchers
- Document real-world deployment challenges

### 6.4 Quaternary Contribution: Practical Deployment Knowledge

**What's Rare**: Actual hardware deployed in real homes for months

**Your Contribution**:
- Document hardware synchronization issues
- Describe solutions to power management challenges
- Detail resident engagement strategies
- Provide templates for reproducible deployments
- Release anonymized dataset (de-identified for privacy)

---

## 7. PROPOSED SYSTEM ARCHITECTURE

### 7.1 Three-Layer Architecture

**Layer 1: Household Level (Bottom)**
- **Ambient Sensors** (replicate CASAS/ARAS approach):
  - Motion sensors (PIR) - room localization
  - Door/window contact sensors - entry/exit detection, cabinet/fridge interaction
  - Temperature sensors - cooking heat signatures
  - Optional: Light sensors, pressure mats
  - Wireless Protocol: Zigbee or BLE

- **Wearable Devices** (solve user identification):
  - Minimal IMU sensors (3-5 per person depending on optimization results)
  - Accelerometer, Gyroscope, Magnetometer
  - Unique Identifier: MAC address, user ID tag, smartwatch serial number
  - Wearable Form Factor: Smartwatch, wristband, or clip-on device
  - Power: Battery lasts 1+ weeks on charge

- **Key Principle**: Data stays on-device or goes directly to local edge gateway; never leaves home except as encrypted model updates

**Layer 2: Local Edge Processing (Home-Level)**
- **Edge Gateway** per home:
  - Raspberry Pi 4 OR nRF 52480 development board
  - Local storage: SD card for raw data backup
  - WiFi/BLE connectivity to communicate with central server
  - Processing: Run local activity recognition model

- **Local Model Training**:
  - Each household trains personalized activity recognition model on local data
  - Model learns individual movement patterns (how User A walks vs. User B)
  - Receives data with explicit user identification (from wearables)
  - Stores only model parameters locally; can retrain as new data arrives
  - Enables continuous personalization to that household

- **Local Inference**:
  - Real-time activity recognition for automation triggers
  - Example: "User A is cooking" → turn on ventilation fan
  - All decisions happen on-device, no raw data exposure

**Layer 3: Central Federated Aggregation (Cloud/University Server)**
- **Federated Server**:
  - Receives encrypted model updates from multiple homes (kilobytes, not raw data)
  - Aggregates using Federated Averaging (FedAvg) or similar algorithm
  - Generates improved global model incorporating patterns from all homes
  - Sends global model back to homes for local personalization

- **Privacy Guarantees**:
  - Raw activity data never centralized
  - Only model parameter updates transmitted
  - Can add differential privacy (noise) to model updates for additional privacy
  - Each home retains full autonomy over their data

- **Personalization Mechanism**:
  - Home 1 receives global model → fine-tunes on local data → personalized model
  - Home 2 does same → different personalized model (suited to Home 2 residents' patterns)
  - Global model improves from diversity of homes; local models remain personalized

### 7.2 Data Flow

```
Wearable Sensors (IMU with User ID) → Edge Gateway
Ambient Sensors (Motion, Door, Temp) → Edge Gateway
                                              ↓
                            Local Data Processing & Storage
                            (Raw data stays on-device)
                                              ↓
                            Local Model Training
                            (Learn from local data)
                                              ↓
                            Encrypted Model Update
                            (Only parameters, not data)
                                              ↓
                            Central Aggregation Server
                            (Federated Averaging)
                                              ↓
                            Global Model Generation
                            (Improved from all homes)
                                              ↓
                            Download to All Homes
                                              ↓
                            Local Personalization
                            (Fine-tune on home's data)
                                              ↓
                            Improved Personalized Models
```

---

## 8. RESEARCH QUESTIONS AND HYPOTHESES

### 8.1 Primary Research Question

**"How can privacy-preserving federated learning enable personalized activity recognition in multi-occupant smart homes using minimal wearable sensors?"**

### 8.2 Sub-Questions

1. **Dataset Question**: Can we create a multi-user smart home dataset with explicit user identification that enables federated learning better than existing datasets (CASAS, ARAS, Opportunity)?

2. **Sensor Placement Question**: What is the minimal wearable sensor configuration (number of sensors and body locations) that enables activity recognition on resource-constrained edge devices?

3. **Personalization Question**: Does federated learning with personalization on local data improve accuracy compared to centralized training?

4. **Privacy Question**: What is the privacy-utility trade-off when adding differential privacy to federated learning model updates?

5. **Deployment Question**: What are the practical challenges and solutions for deploying federated learning in real homes?

### 8.3 Hypotheses

1. **H1**: A multi-user dataset with explicit wearable-based user identification will enable federated learning models to achieve >85% activity recognition accuracy across multiple homes, compared to ~60-70% accuracy when using CASAS (which can't identify users).

2. **H2**: Optimal placement of 3-4 wearable sensors (vs. current 5-8 or 15+ in literature) on specific body locations (wrist, upper arm, hip) will maintain >85% accuracy while reducing power consumption by 40% for edge devices.

3. **H3**: Federated learning with local personalization will improve per-user accuracy by 5-10% compared to global-only models, because local models learn individual movement patterns.

4. **H4**: Federated learning with differential privacy (ε<10) will maintain >80% accuracy while providing formal privacy guarantees against user pattern inference.

5. **H5**: Real deployment in 3-4 homes will reveal synchronization and data consistency challenges not apparent in lab settings, requiring custom solutions.

---

## 9. PROJECT TIMELINE AND MILESTONES

### 9.1 Phase Breakdown (52 Weeks Total)

**Phase 1: Literature Review & Gap Analysis (Weeks 1-8)**
- **Team Allocation**: 5 people, full engagement
- **Tasks**:
  - Document all smart home datasets (CASAS, ARAS, Opportunity, UCI-HAR, UniMiB-SHAR, WiFi-HAR, Kastrons, others)
  - Map research landscape by sensor type, activity complexity, multi-user capability
  - Create comparison matrix: sensor types used, activities recognized, challenges addressed
  - Identify specific problems each dataset has
  - Search 2021-2025 literature to prove problem is "still new"
  - Study federated learning papers in activity recognition context
  - Create literature map with 50+ papers
  
- **Deliverables**:
  - Comprehensive literature review document
  - Dataset comparison table with significance analysis
  - Identified gaps proving novelty
  - Finalized problem statement
  - Architecture design document
  
- **Milestone (Week 8)**: Literature review complete, problem statement locked in, team consensus on contributions

### Phase 2: Hardware Design & Protocol Finalization (Weeks 9-12)
- **Team Allocation**: 3 people (hardware specialists + lead)
- **Tasks**:
  - Sensor selection: test various IMU modules with nRF 52480
  - Determine minimal configuration: 3, 4, or 5 sensors per person
  - Battery life calculations and testing
  - Accuracy baseline for different sensor counts
  - Data collection protocol design:
    - Define 15-20 Activities of Daily Living (ADLs)
    - Create annotation guidelines (detailed, unambiguous)
    - Design annotation forms for annotators
    - Create data storage & encryption plans
    - Develop consent forms & privacy agreements
  - Software infrastructure design:
    - Data collection mobile/embedded app architecture
    - Synchronization mechanism (time-stamping all events)
    - Local processing pipeline
    - Encryption for model update transmission
  - Pilot testing in lab (2-3 team members, 1-2 weeks):
    - Collect sample data
    - Identify synchronization bugs
    - Validate annotation protocol
    - Fix issues before real deployment

- **Deliverables**:
  - Tested hardware kits (ready for deployment)
  - Data collection protocol (final version)
  - Software pipeline functioning and tested
  - Pilot data showing system works
  - Risk assessment document
  
- **Milestone (Week 12)**: Hardware ready, protocol finalized, confidence in real deployment

### Phase 3A: Real Data Collection - Homes 1-2 (Weeks 13-20)
- **Team Allocation**: 4 people (rotation: deployment coordinator, on-site monitor, annotation lead, analysis)
- **Tasks**:
  - Home recruitment (active search for 3-4 households):
    - 3-5 residents per home minimum
    - Diverse age/gender if possible
    - Explain privacy guarantees (no cameras, federated learning)
    - Ongoing consent process
    - Address privacy concerns
  - Physical sensor deployment in Home 1:
    - Install ambient sensor network (motion, door, temp sensors)
    - Calibrate against ground truth
    - Distribute wearables to residents
    - Establish edge gateway (local compute device)
    - Test all systems before residents start
  - Continuous monitoring (4 weeks per home):
    - Daily check-ins with residents
    - Troubleshoot hardware issues
    - Verify data is being collected
    - Maintain system uptime (target 95%+)
    - Replace batteries, fix broken sensors
  - Real-time annotation:
    - Residents or trained annotators log activities (with exact timestamps)
    - Cross-reference sensor events with activity logs
    - Resolve ambiguities
    - Build ground truth labels
  
- **Data Target for Phase 3A**: 100-150 hours per home × 2 homes = 200-300 hours raw data
  
- **Deliverables**:
  - 200-300 hours raw sensor data from 2 homes
  - Ground truth activity annotations
  - System reliability assessment
  - Lessons learned document
  - Resident feedback
  
- **Milestone (Week 20)**: First 2 homes completed, 200-300 hours collected, data quality acceptable

### Phase 3B: Real Data Collection - Homes 3-4 (Weeks 21-28)
- **Team Allocation**: Same 4 people, continuing rotation
- **Same Process as Phase 3A for Homes 3-4**

- **Data Target for Phase 3B**: 100-150 hours per home × 2 homes = 200-300 more hours
  
- **Total Data After Phase 3B**: 400-600 hours across 4 homes
  
- **Milestone (Week 28)**: Multiple homes deployed, 400-600 hours data collected, real-world validation

### Phase 4: Dataset Preparation & Annotation (Weeks 29-40)
- **Team Allocation**: 5 people (distributed task)
- **Tasks**:
  - Data synchronization:
    - Align wearable timestamps with ambient sensor timestamps
    - Handle sensor dropouts and connection losses
    - Resolve timing misalignments
    - Create unified time-series for each resident
  - Annotation validation:
    - Check consistency across annotators
    - Measure inter-rater agreement
    - Resolve conflicts in activity labeling
    - Ensure every data segment labeled with [User ID, Activity, Timestamp, Location]
    - Create validation set (10% of data for testing annotation quality)
  - Class balancing analysis:
    - Document activity distribution per home
    - Identify severely imbalanced classes
    - Plan mitigation strategies (oversampling, class weighting, cost-sensitive learning)
    - Document findings in paper
  - Feature extraction:
    - Extract statistical features from wearable data (mean, std, variance, entropy, quartiles)
    - Prepare raw time-series for deep learning models
    - Create both feature representations (traditional ML + deep learning)
    - Normalize and scale appropriately
  - Dataset versioning:
    - Split into train/test (70-30% stratified by user)
    - Create metadata documentation
    - Anonymize data (remove identifying information)
    - Test reproducibility with simple ML baseline model
    - Prepare anonymized dataset for potential release

- **Deliverables**:
  - Clean, fully annotated dataset (400-600 hours)
  - Feature extraction code (reproducible)
  - Dataset documentation & metadata
  - Baseline classifier results (proves data quality)
  - Analysis of class imbalance and mitigation strategies
  
- **Milestone (Week 40)**: Dataset fully prepared, validated, and ready for federated learning

### Phase 5: Federated Learning Implementation (Weeks 41-48)
- **Team Allocation**: 3-4 people (ML specialists + systems person)
- **Tasks**:
  - Federated framework setup:
    - Use existing FL library (Flower framework or custom implementation)
    - Simulate homes as clients in federation
    - Design central aggregation server
    - Create communication protocol (model updates)
  - Local model training:
    - Implement activity recognition model (LSTM or GRU recommended based on Member 4's findings)
    - Train separate local model for each home
    - Measure per-home local accuracy
    - Validate that local models learn home-specific patterns
  - Global aggregation:
    - Implement Federated Averaging (FedAvg) algorithm
    - Aggregate local model weights from all homes
    - Generate improved global model
    - Distribute global model back to homes
  - Personalization evaluation:
    - Compare: Global-only model vs. Local+Global (personalized) model
    - Measure accuracy on held-out test data
    - Show personalization improves per-user accuracy
    - Compare with centralized training baseline (privacy cost)
  - Privacy analysis:
    - Implement differential privacy (add Laplace/Gaussian noise to model updates)
    - Measure privacy-accuracy trade-off
    - Document privacy guarantees (ε values)
    - Analyze feasibility of different privacy levels

- **Deliverables**:
  - Working federated learning system
  - Performance metrics (accuracy, F1-score per activity)
  - Comparison tables (centralized vs. federated vs. federated+DP)
  - Privacy analysis report
  - Code documentation
  
- **Milestone (Week 48)**: Federated learning system fully functional and evaluated

### Phase 6: Evaluation, Testing & Documentation (Weeks 45-52)
- **Team Allocation**: 4-5 people (parallel work)
- **Tasks**:
  - Validation on holdout test set:
    - Ensure fair evaluation (stratified by user, activity, home)
    - Report precision, recall, F1-score per activity class
    - Generate confusion matrices
    - Compare with baselines (single-home models, centralized training)
  - Ablation studies:
    - Impact of sensor count (3 vs. 4 vs. 5 sensors)
    - Impact of homes (1-home model vs. 4-home federated)
    - Impact of activity complexity (simple vs. complex activities)
    - Impact of personalization (global only vs. personalized)
  - Reproducibility package:
    - Code for data preprocessing and feature extraction
    - Federated learning implementation
    - Evaluation scripts and notebooks
    - Sample anonymized dataset (for others to reproduce)
    - Detailed README with setup instructions
  - Paper writing:
    - Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion
    - Figures: Architecture diagram, results graphs, confusion matrices, ablation studies
    - Tables: Dataset statistics, activity classes, performance comparisons, participant demographics
    - References: 50+ papers cited
  - Presentation preparation:
    - Create 20-30 slide presentation
    - Prepare demo (real-time activity recognition demo if possible)
    - Create demo video showing deployment
    - Prepare poster for panel review

- **Deliverables**:
  - Complete evaluation report
  - Reproducibility package (code + data + documentation)
  - Research paper (conference submission quality)
  - Presentation slides and materials
  - Demo video
  
- **Milestone (Week 52)**: All deliverables complete, ready for submission and review

### 9.2 Critical Path & Risk Points

**Bottleneck: Data Collection (Weeks 13-28)**
- Cannot be parallelized effectively
- Depends on real homes and willing residents
- Weather, resident availability, hardware failures all affect timeline
- **Mitigation**: 
  - Start recruiting homes NOW (January 2026)
  - Target first home deployment by February-March 2026
  - Have backup homes identified
  - Plan for 6-8 weeks per home, not 4 weeks

**Risk: Hardware Reliability**
- Wearables may fail, batteries may not last
- Sensors may disconnect from edge gateway
- **Mitigation**:
  - Redundant sensors where possible
  - Daily backups of data
  - Frequent hardware checks
  - Clear resident instructions

**Risk: Annotation Inconsistency**
- Multiple annotators may label same activities differently
- **Mitigation**:
  - Detailed annotation guidelines
  - Multiple annotators with validation
  - Inter-rater agreement measurement
  - Adjudication process for conflicts

---

## 10. HARDWARE AND RESOURCE REQUIREMENTS

### 10.1 Wearable Devices (Per Resident)

**Required Sensors per Device**:
- 3-Axis Accelerometer (measure motion in 3 directions)
- 3-Axis Gyroscope (measure rotational motion)
- 3-Axis Magnetometer (optional, for orientation)
- Microcontroller (Arduino Nano RP2040 or nRF 52480)
- Battery (rechargeable or coin cell)
- Wireless Module (BLE for local communication)
- Comfortable case/wristband for wearing

**Specifications**:
- Weight: <50 grams (comfortable for all-day wear)
- Battery Life: 1+ week on single charge
- Sampling Rate: 50-100 Hz (per Member 4's findings)
- Data Transmission: BLE to edge gateway
- Unique Identifier: MAC address or user ID tag

**Cost Per Device**: Approximately ₹2,000-4,000 (~$25-50 USD)

**Quantity Needed**: 5 people/home × 4 homes = 20 wearable devices
**Total Cost**: ~₹40,000-80,000

### 10.2 Ambient Sensors (Per Home)

**Required Sensors**:
- Motion Sensors (PIR - Passive Infrared): 5-10 per home (different rooms)
  - Detect presence and movement
  - Mounted on ceilings or high walls
  
- Door/Window Contact Sensors (Reed Switches): 5-15 per home
  - Entry/exit doors (front, back, garage)
  - Bedroom, bathroom doors
  - Cabinet, fridge, drawers
  
- Temperature Sensors: 2-3 per home
  - General ambient temperature
  - Kitchen (for cooking detection)
  - Optional: Bathroom (for shower detection)
  
- Light Sensors (optional): 2-3 per home
  - Detect sleep/wake cycles
  - Monitor artificial lighting usage
  
- Pressure Sensors/Mats (optional): 2-3 per home
  - Under beds to detect lying down
  - Under couches to detect sitting

**Wireless Protocol**: Zigbee or BLE (for local mesh networking)

**Cost Per Home**: Approximately ₹5,000-10,000 sensors + installation

**Quantity Needed**: 4 homes
**Total Cost**: ~₹20,000-40,000

### 10.3 Edge Gateway (Per Home)

**Hardware Options**:

**Option A: Raspberry Pi 4 (Recommended)**
- 4GB RAM minimum, 8GB recommended
- 64-bit processor, quad-core
- Built-in WiFi and Bluetooth
- GPIO pins for sensor integration
- SD card slot for local storage
- Cost: ~₹4,000-6,000

**Option B: nRF 52480 Development Board**
- Highly specialized for IoT
- Built-in BLE
- Lower power than RPi
- More limited processing power
- Cost: ~₹3,000-5,000

**Recommended Setup**: Raspberry Pi 4 (8GB RAM) for flexibility

**Roles**:
- Collect data from all sensors (wearable + ambient)
- Store raw data locally (encrypted)
- Run local activity recognition model
- Train local federated learning model
- Transmit encrypted model updates to central server
- Download global model updates

**Cost Per Home**: ~₹4,000-6,000

**Quantity Needed**: 4 homes
**Total Cost**: ~₹16,000-24,000

### 10.4 Central Server

**For Federated Aggregation**:
- Can be university server, AWS, Google Cloud
- Requirements:
  - Ability to store models from 4 homes
  - Aggregation computation
  - Secure communication (HTTPS)
  - Database for tracking experiments

**Estimated Cost**: 
- If using university infrastructure: ₹0 (existing resources)
- If cloud-based: ₹1,000-2,000 per month
- Total for 12 months: ~₹12,000-24,000

### 10.5 Total Hardware Budget

```
Wearable Devices (20 units)        : ₹40,000-80,000
Ambient Sensors (4 homes)          : ₹20,000-40,000
Edge Gateways (4 homes)            : ₹16,000-24,000
Central Server (12 months)         : ₹12,000-24,000
Miscellaneous (cables, adapters, etc.): ₹5,000-10,000
Buffer (contingency)               : ₹10,000-20,000
─────────────────────────────────────────────────
TOTAL ESTIMATED BUDGET             : ₹103,000-198,000
```

**Realistic Budget**: **₹120,000-150,000** (approximately $1,500-1,800 USD)

---

## 11. PROJECT CLASSIFICATION: Research vs. Application

### 11.1 Why This is a Research Project (Not Just Application)

**Research Project Characteristics** (Your project HAS these):

1. **Novel Dataset Creation**: 
   - First dataset with explicit multi-user identification in smart homes
   - Addresses 15-year gap in CASAS research
   - Solves fundamental data association problem

2. **Systematic Optimization Study**: 
   - Determines minimal sensor placement for federated learning context
   - Literature shows 5-8 sensors generally optimal, but federated context unexplored

3. **Framework Contribution**: 
   - Practical federated learning framework validated on real multi-user data
   - Previous work (FedHome, FeL-MAR) use invalid datasets (CASAS which can't identify users)
   - Privacy-utility trade-off analysis with differential privacy

4. **Knowledge Contribution**: 
   - Documents real deployment challenges and solutions
   - Provides reproducible framework for future research
   - Enables new research directions in privacy-preserving smart homes

5. **Evaluation Rigor**: 
   - Proper statistical validation
   - Ablation studies showing impact of design choices
   - Comparison with baselines and state-of-the-art

**Application Project Characteristics** (Your project does NOT have these):

1. ❌ "Build a commercial product for market"
   - You're building research infrastructure, not consumer product
   - End goal is scientific contribution, not product launch

2. ❌ "Apply existing technology to new domain"
   - Federated learning + activity recognition exist
   - But combining them with multi-user identification in real homes is novel

3. ❌ "Optimize existing system for performance"
   - You're not optimizing a known solution
   - You're creating entirely new dataset and framework

### 11.2 Assessment Rubric Alignment

**For Research Project, you'll be assessed on**:

1. **Literature Review (Research Problem Novelty)**: ✅ 
   - You've clearly identified unresolved problem
   - Shown gap in datasets (CASAS can't identify users)
   - Shown gap in federated learning validation

2. **Research Contribution (Originality)**: ✅
   - First multi-user dataset with explicit identification
   - First practical federated learning validation on proper data
   - Sensor placement optimization study

3. **Methodology (Rigor & Reproducibility)**: ✅
   - Clear experimental protocol
   - Proper data collection and annotation procedures
   - Reproducible code and anonymized dataset

4. **Results (Evidence of Contribution)**: ✅
   - Dataset statistics proving multi-user capability
   - Federated learning performance metrics
   - Privacy-utility analysis
   - Ablation studies

5. **Impact (Significance)**: ✅
   - Solves real research gap in multi-user smart homes
   - Enables future federated learning research
   - Practical framework for deployment

### 11.3 How to Position in Submission

**On LaTeX Template**:
- Change "Type 2: Application" to **"Type 3: Research Project with Product Instantiation"**
- Or create new header: **"Type: Research Project"**

**In Report**:
- Emphasize research contributions (dataset, framework, optimization)
- Discuss product as validation mechanism, not main goal
- Focus on what researchers can do with your dataset/framework
- Document lessons learned for future smart home deployments

---

## 12. CLARIFICATIONS NEEDED FROM YOUR GUIDE

Based on your project and the meeting notes, you should clarify the following with Dr. Nalinadevi K:

### 12.1 Scope Clarifications

1. **Multi-User Scale**: "Should we target 3-5 residents per home, or would 2-3 be acceptable given time constraints?"

2. **Activity Coverage**: "Is 15-20 ADL activities sufficient, or should we target 25-27 like ARAS?"

3. **Home Count**: "Is 3-4 homes the right target, or would 2 homes with more data be better?"

4. **Data Volume Target**: "Is 500+ hours our target, or can we go with 300-400 hours if fully annotated and of high quality?"

### 12.2 Technical Clarifications

1. **Sensor Placement**: "Should we start by testing 3, 4, and 5 sensor configurations to find optimal, or do you want us to target specific body locations (wrist, hip, chest)?"

2. **Edge Device Preference**: "Should we use Raspberry Pi 4 or nRF 52480 as primary edge gateway, or test both?"

3. **Federated Learning Algorithm**: "Should we implement custom FedAvg or use existing library (Flower Framework)?"

4. **Model Choice**: "You mentioned not focusing on models, but should we use LSTM, GRU, or TCN as baseline for validation?"

### 12.3 Deployment Clarifications

1. **Ethics Approval**: "What university ethics approval process do we need for deploying in real homes? Should we start this process now?"

2. **Consent Management**: "What are the required privacy agreements and consent forms for multi-resident homes?"

3. **Data Anonymization**: "For the dataset we release, what level of anonymization do you recommend (complete removal of identifying features vs. pseudonymization)?"

### 12.4 Project Type Clarification

1. **Official Project Type**: "Should we officially designate this as Type 3 (Research + Implementation) rather than Type 2 (Application)?"

2. **Assessment Focus**: "Will assessment emphasize dataset contribution and framework, or implementation quality?"

---

## 13. NEXT STEPS AND IMMEDIATE ACTIONS

### 13.1 This Week (January 6-12, 2026)

**Priority 1: Confirm Project Direction**
- [ ] Meet with guide to confirm:
  - Problem statement is correctly scoped
  - Project type clarification (Research vs. Application)
  - Timeline is realistic with other coursework
  - Hardware budget approved

**Priority 2: Start Home Recruitment**
- [ ] Identify recruitment channels:
  - Amrita alumni network
  - University community groups
  - Local community centers
  - Social media networks
- [ ] Create recruitment materials:
  - Flyer describing project
  - Consent form (draft)
  - FAQ about privacy (no cameras, federated learning)
  - Privacy guarantees document
- [ ] Begin outreach (target: 10-15 household inquiries)

**Priority 3: Finalize Team Roles**
- [ ] Assign project lead (overall coordinator)
- [ ] Assign hardware lead (sensor sourcing and testing)
- [ ] Assign data collection lead (home coordination)
- [ ] Assign ML lead (model and federated learning)
- [ ] Assign documentation lead (writing, presentation)

**Priority 4: Lock in Hardware Selections**
- [ ] Finalize sensor list and vendors
- [ ] Get cost quotes
- [ ] Order non-urgent components (long lead time items)

### 13.2 Next Two Weeks (January 13-26, 2026)

- [ ] Complete literature review (50+ papers)
- [ ] Create dataset comparison table
- [ ] Finalize activity list (15-20 ADLs)
- [ ] Write annotation protocol (detailed guidelines)
- [ ] Draft data collection protocol
- [ ] Submit ethics approval (if required)
- [ ] Follow up on home recruitment (target: 3-4 homes confirmed by late January)
- [ ] Order hardware

### 13.3 By End of January 2026

- [ ] Literature review complete and documented
- [ ] Problem statement finalized and approved by guide
- [ ] Team roles and responsibilities clear
- [ ] Hardware ordered and budget confirmed
- [ ] 3-4 homes recruited and initial meetings scheduled
- [ ] Data collection protocol finalized
- [ ] Annotation guidelines completed
- [ ] Ready to start hardware setup in February

### 13.4 February 2026 (Hardware Setup & Pilot)

- [ ] Hardware arrives and testing begins
- [ ] Pilot data collection in lab (1-2 weeks)
- [ ] System debugging and refinement
- [ ] Preparation for first real home deployment
- [ ] Target: First real home deployment by end of February or early March

---

## 14. SUMMARY OF KEY INSIGHTS

### 14.1 The Central Problem Your Project Solves

**The Data Association Problem**: For 15+ years, even the best ambient sensor smart home datasets (CASAS with 2000+ hours) cannot definitively answer: "Which person triggered this sensor when multiple residents are home?" This fundamental limitation has prevented:
- True personalization (systems treat all residents as "the home")
- Proper federated learning validation (previous FL papers use invalid data)
- Multi-resident health monitoring (can't track individual wellness patterns)

**Your Solution**: Combine minimal practical wearables (smartwatch with unique ID) with ambient sensors to create explicit user-activity mapping that has never existed before in real smart home deployments.

### 14.2 Why Each Dataset You Researched Falls Short

| Dataset | Strength | Fatal Flaw |
|---------|----------|-----------|
| **CASAS** | 2000+ hours, real homes, established | Can't identify users (anonymous sensors) |
| **ARAS** | Explicit multi-resident, 30 days per home | Can't distinguish overlapping activities (data association problem) |
| **Opportunity** | Explicitly identifies users, well-annotated | 15+ sensors (unrealistic), lab-only, 25 hours total |
| **UCI-HAR** | Excellent for edge devices (97% accuracy, 0.18M params) | Smartphone-only, single-user, no smart home context |
| **WiFi-HAR** | No cameras, 461 hours, 35 users | Activity recognition fails with 3+ concurrent users (~60% accuracy) |

**Your Dataset Will Be**: First to have BOTH explicit user identification AND real homes AND federated learning design.

### 14.3 The Research vs. Application Distinction

This is a **Research Project** because:
- You're creating NEW infrastructure (dataset, framework) that didn't exist
- You're NOT applying existing solutions to new domain
- You're NOT optimizing a known system

The deployed smart home is VALIDATION, not the contribution.

### 14.4 Timeline Critical Success Factors

1. **Start Home Recruitment NOW** (January 2026) - This is your critical path bottleneck
2. **Expect 6-8 weeks per home** (not 4 weeks) - Account for setup, troubleshooting, resident engagement
3. **Data Quality > Quantity** - 400 hours of clean, well-annotated data better than 1000 hours of messy data
4. **Annotator Consistency** - Have clear protocols, multiple annotators, validation sets to ensure data quality
5. **Hardware Reliability** - Plan for failures, have backups, test extensively before deployment

---

## 15. FULL CONTEXT INTEGRATED INTO PROJECT FRAMEWORK

Your project now has:

✅ **Clear Problem Statement**: Multi-user identification gap in smart homes

✅ **Research Novelty Justified**: Shown how CASAS (15+ years), ARAS, Opportunity, and others all fall short

✅ **Dataset Gap Identified**: First dataset with explicit user ID + real homes + wearables + federated-ready

✅ **Contributions Defined**: Dataset, sensor optimization, federated framework, practical deployment knowledge

✅ **Architecture Designed**: Three-layer (ambient + wearable + federated)

✅ **Timeline Created**: 52-week plan with realistic milestones and risk mitigation

✅ **Team Roles Assigned**: Each member researched specific datasets, contributing to overall understanding

✅ **Hardware Budget Estimated**: ₹120-150k for complete deployment

✅ **Next Steps Clear**: Start recruiting homes, finalize literature review, order hardware

✅ **Project Type Clarified**: Research (not application) - dataset and framework are contributions

This comprehensive context document serves as your project bible. Reference it in all discussions with your guide, use it to coordinate team efforts, and ensure all members understand the complete project scope and rationale.

---

**Document Prepared**: January 2, 2026
**For**: Team 67, Amrita Vishwa Vidyapeetham CSE Department
**Scope**: Complete project context and strategic planning document
**Status**: Ready for guide approval and team coordination
