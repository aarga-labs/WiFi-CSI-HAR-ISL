


## Week - 1:

Wsu , casas , joto , milan , kyro , thulum , aruda
Opportunity dataset for wearables
Microaoft adl

## Week - 2



My Notes: 

1) Various smart home product available in the market , what level they can recognize

2) Complete integrated environment , smart security system , survilance system , all are in separate products,  Electronic + non electronic items

3) Abnormal detection , list of application , list of producta , industry works , academic works

4) Search in google scholar

5) Significantly all the papers in the last 5 years

6) Ontology based also we will work on , what area is this

7) Common kit like for smart home , smart office

8) Casas - ambience dataset , object dataset

9) SDHAR dataset

10) Personalization - Take user preferences , it's not currently exist

11) Gyro sensor

12) First have a proof that this ps is still new by sesrching b/w 2021 to 2025

13) Applications and products


## Week - 3 

1. Sensor-Based Data Collection for Smart Homes

We are currently using multiple types of sensors to capture data inside a home environment. These include:

Ambient Sensors such as motion, door, temperature, pressure, and object usage.
Datasets include CASAS, Kastrons, and ARAS.
These datasets mainly focus on ambient sensing with some object-based sensors.
CASAS is a multi-person dataset with two persons, but it does not explicitly identify which person triggers a particular sensor.

Wearable or Body-Level Sensors
These sensors are used to identify human activities at the body level.
Important datasets include UCI-HAR which is mobile-based with 7 to 8 activity classes, the Opportunity Dataset, and the UniMiB-SHAR Dataset.
These datasets mainly capture activities like walking, sitting, standing, running, etc.

WiFi-Based Sensing
Datasets and systems such as WiHAR or WiFi-HAR are used.
WiFi signals are used to infer human activity without direct contact sensors.

Power Utilization Monitoring
These datasets track appliance-level energy consumption, for example kettle usage.
They help in recognizing activity patterns based on power usage.

Audio Sensors
Audio signals can be used to recognize environmental and human activities such as cooking, talking, washing, etc.

NLP with Sensor Data
Natural Language Processing can be combined with sensor data for activity description, explanation, and reasoning.

We are using Basil’s VLE Gateway in the lab, and the nRF 52480 with WiFi support as part of our sensing infrastructure.


2. Multi-Modality and Future Data Expansion

We are currently working with CASAS integrated multi-modal data, and we plan to expand the number of modalities such as combining ambient, wearable, WiFi, power, and audio sensors.
The goal is to move from single-sensor activity recognition to multi-modal context-aware activity recognition.


3. Activity Types and Context Understanding

Simple activities include walking, sitting, standing, and opening doors.
Complex activities include cooking, cleaning, working, and collaborative tasks.

Sequential activities are activities performed one after the other in a continuous manner.

Interrupted activities are activities that are stopped and resumed later, which makes recognition difficult.

Concurrent activities refer to a single person performing multiple activities at the same time.

Parallel activities refer to multiple people performing activities simultaneously.

These contexts are much harder to recognize, especially using only ambient sensors.


4. Multi-Person and Group Activity Challenges

In ambient sensor datasets like CASAS, we cannot easily identify which person activated a sensor.
Earlier works around 2017 mainly focused on simple single-person activities.
Some recent works focus on group activity recognition and collaborative activities, for example four people carrying a table together.
Collaborative activity is not the same as general group activity and requires special modeling.


5. Dataset Categorization and Team Task Division

We will divide the work such that each team member works on every dataset instead of only one.
The main dataset categories are:

Ambient and Object Sensors: CASAS, Kastrons, ARAS
Wearable Sensors: UCI-HAR, Opportunity, UniMiB-SHAR
WiFi-Based Sensing: WiHAR or WiFi-HAR
Power Usage Monitoring Datasets
Audio-Based Activity Recognition Datasets

Each member will study all categories and identify what type of activities can be detected and what kind of problems are solved using each dataset.


6. Research Paper Survey Requirements

We need to identify related research papers for each dataset and modality.
We must select and summarize at least 10 high-quality papers.
They must be classified based on sensor type, activity complexity, single-person versus multi-person, and sequential versus concurrent versus parallel activities.
The final outcome should be a chart, table, or flow diagram showing the types of problems addressed, sensors used, activities recognized, and key challenges.


7. Purpose of Our Data Collection for the 1.5-Year Research Vision

Before collecting new data, we must clearly define what problems we aim to solve, which types of data are currently missing in existing datasets, why new data collection is necessary, what new capabilities the models will achieve using our dataset, and what challenges exist.
The challenges include multi-person ambiguity, concurrent and parallel activities, activity interruption, sensor noise, data synchronization, and context understanding.

We must formally justify why we are collecting this data, what research gaps it fills, and how this dataset will enable new models and new problem formulations.


8. Immediate Task for Thursday

By Thursday, we must be ready with broad research areas, a structured summary of 10 key research papers, clear categorization of datasets, sensors, activities, and problems addressed, a visual representation such as a chart or flow diagram, and a list of open research problems, unsolved challenges, and possible directions for our 1.5-year research plan.



WEEK 4 - 18/12

1) federated learnign , we did a prototype ,
2) focus on how many sensors should be implanted in a body (minimal) can read a efficient reading , no many made it , so we need ot do it , we need to go with wearables, Personalization (secure and private) that's only federated learnign should come 

3) Should refer federated learnign (done by us) 

4) how many dataset come from that particular 
5) dyan cook - casas fist see how many dataset came? diff palces all across the world , and how many paper used it and solved problems like sequential , what are the significant of the data(casas talks about inter class variation and intra class similarity ) , data association , put three columns , challenge theyu handled , how much of sensors they used , what were they not able to reach the acucuracy , interoperabily , take two or three datasets and compare them , how many found out 

draw this as a complete federated 

pluck dataset (no annotation so we cannot able to use it ) under casas deals with multi modals , object , wearables 


flower model , mtech student - 

don't focus on model and do something on this area , identify what problem is there . 


formulate the problem statement , don't change the problem statement

focus on literature survey , what is happening in this field ,




Final Year Project – Meeting 5 

Meeting Details 

- Meeting Number: 5 
    

- Date: 17 April 2026 
    

- Duration: ~25 minutes 
    

- Mode: Online 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Discussion Summary 

We presented our work on the SignFi dataset and the CNN model we trained. We explained that the dataset contains around 5000+ samples with 276 sign gesture classes, and that we used amplitude and phase information from WiFi CSI as input. 

We described that we used a 2D CNN model for classification. However, during the discussion, it became clear that we had directly moved to model training without properly understanding the dataset. We were not able to clearly explain how the data looks, how signals vary, or how different gestures are represented. 

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Suggestions / Improvements Given 

We were told to first understand the dataset properly before working on models. We should visualize the data by plotting signals and observing how different gestures appear. 

We were asked to analyze: 

- Signal patterns 
    

- Similarities between different gesture classes 
    

- Range and behavior of CSI values 
    

We were also told to understand how the data was collected, including details like antennas and subcarriers. 

We need to clearly explain our model, including layer details, parameters, and why we chose that architecture. 

The mentor also pointed out that our current work was too basic and our approach was not professional. 

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Decisions Made 

We decided to pause further model improvements and first focus on properly understanding and analyzing the dataset. 

Work Assigned / Next Steps 

We need to complete full data analysis, including plotting and visualizing signals. 

We have to study how different gestures look in the data and identify similarities and differences between them. 

We need to prepare a PPT explaining the dataset, analysis, and our observations. 

We also need to: 

- Print and understand model details 
    

- Work in parts within the team (data analysis and model understanding) 
    

We were asked to complete this work within the same day 

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Issues / Challenges Discussed 

We had not explored the dataset properly and had no clear visualization or understanding of it. 

We were not able to justify our model or explain decisions clearly. 

Our progress was considered slow and not up to expectations.




Final Year Project – Meeting 6 

Meeting Details 

Date: 17 April 2026 

- Duration: 1hr  
    

- Mode: Online 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Discussion Summary 

- We presented our work on training a CNN model using the SignFi dataset for sign language recognition. 
    

- We explained our model architecture, which includes: 
    

- Convolution layers, batch normalization, and pooling layers 
    

- Dense layers with softmax for classification (276 classes) 
    

- We used amplitude and phase (magnitude + phase) from CSI data as input features. 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Suggestions / Improvements Given 

- We were advised to first focus on activity detection (sign vs no sign) instead of directly performing full sign classification. 
    

- We should implement time-series segmentation to identify when an activity starts and stops in WiFi signals. 
    

- We should improve evaluation by including: 
    

- Precision, recall, and F1-score 
    

- Class-wise performance analysis 
    

- We were encouraged to explore WiFi-based human activity recognition before moving to complex tasks. 
    

- We were suggested to explore multimodal approaches, such as: 
    

- WiFi + Vision 
    

- WiFi + Ambient sensors 
    

- Wearable sensors  
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Decisions Made 

- We decided to first work on: 
    

- Activity detection (sign vs no sign) as a simpler problem 
    

1. Simple motion detection 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Work Assigned / Next Steps 

- We will implement activity detection using WiFi CSI data 
    

- We will perform signal segmentation (start/stop detection) 
    

- We will explore datasets for WiFi-based human activity recognition 
    

- We will validate whether WiFi alone is sufficient for activity detection 
    

- We will start working with ESP32 for data capture 
    

- We will divide tasks: 
    

- Some team members will focus on hardware 
    

- Others will focus on model development 
    

- We will prepare a clear explanation of CNN operations with a small working example 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC)



Final Year Project – Meeting 7 

Meeting Details 

- Meeting Number: 7 
    

- Date: 24 April 2026 
    

- Duration: 1 Hour 
    

- Mode: Offline 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Discussion Summary 

We demonstrated our progress on motion detection. We showed how we are detecting whether a person is in motion or idle using ESP32 with the help of Espectre. 

We also presented our CNN models trained on two datasets: 

- UT-HAR dataset 
    

- Ariyel dataset 
    

Both datasets are based on WiFi CSI. We explained the dataset structure and how we trained the models. 

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Suggestions / Improvements Given 

We were told that for complex activity detection, WiFi CSI can be used to capture micro-level activities. Based on this, we can move towards a multimodal approach. 

We were advised that: 

- For short duration activities, RSSI (signal strength) can be used 
    

- For long duration activities, WiFi CSI is more suitable 
    

We were asked to refer to a fall detection study (Springer link shared) to understand how such systems are designed. 

We were suggested to explore the use of Sync LSTM for better modeling of temporal data. 

The mentor also mentioned the importance of understanding and handling the data association problem. 

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Decisions Made 

We decided to move towards combining multiple data sources (multimodality), especially WiFi CSI and wearable sensors. 

We agreed to explore fall detection as a use case to better understand activity recognition. 

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Work Assigned / Next Steps 

1. Fall Detection using Wearable + WiFi CSI We will collect data using: 
    

- Smartphone (wearable sensors) 
    

- WiFi CSI 
    

We will record both simultaneously and share the collected data with the model development team. The model team will use this data to build and train a model. 

From this, we aim to understand: 

- How to differentiate between sign and general activity 
    

- Whether WiFi CSI alone is sufficient or not 
    

2. Recording Sign, Activity, and Idle States 
    

We will record data for three cases: 

- Signing 
    

- General activity 
    

- Idle 
    

This will help us build a system that can identify whether a person is: 

- Signing 
    

- Performing some activity 
    

- Idle 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC) 

Issues / Challenges Discussed 

We need to handle: 

- Differentiating between similar activities and signs 
    

- Data association between multiple sensors 
    

- Deciding whether a single modality (WiFi CSI) is enough or multimodality is required 
    

![Shape](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAANSURBVBhXY2BgYGAAAAAFAAGKM+MAAAAAAElFTkSuQmCC)



the above all are context of meetings we have took 


below i will provide those works we have done as a report 


this reports have only some things that previously taken , but we have done somewhat more , that u can get from above meetign discussion 


﻿AMRITA VISHWA VIDYAPEETHAM
SCHOOL OF COMPUTING

DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING

Smart Home HAR for
Speech-Impaired & Hearing-Impaired Users

23CSE399 – Project Phase 1 (Panel Review 2) March 30, 2026

Team Members Guide Project Type Marks

CB.SC.U4CSE23101 Adhikkesh S K

CB.SC.U4CSE23102 Adithya Ajay
Ms. Nalinadevi K Type 2

CB.SC.U4CSE23105 Amrith B . . . / 5
Dept. of CSE Implementation

CB.SC.U4CSE23119 Gowreesh B

CB.SC.U4CSE23236 Rishiikesh S K

1 Problem Definition & Relevance

Real-World Use Cases: Resolving Conflicting Interpretations
Because single sensors suffer from context blindness, they critically misclassify transitions be-
tween physical states. Our multi-modal fusion architecture specifically resolves these conflicts:

• UC1: Kitchen (Action → Sign): A user stops cooking to sign to someone entering the
room. An ambient sensor only sees ongoing presence, and a wearable confuses the sign
language with cooking arm motions. By gating these inputs with WiFi CSI, the fusion model
successfully identifies the shift from a chore to Communication.

• UC2: Coffee (Idle → Sign): A user sitting idle receives a video call and begins signing.
Ambient sensors incorrectly assume a purely static/idle state, while the wearable triggers on
sudden, structured arm movement. Fusion combines these to confirm the Intent to Com-
municate.

• UC3: Resting (Action → Idle): A user finishes chores and sits down to rest. Wearable
macro-acceleration drops to zero, and ambient motion sensors deactivate. The fusion model
gates off the WiFi processing to save compute power, safely logging the state as Idle.

Motivation:

1



• The Voice-First Bias: Modern smart hubs inherently assume users can speak commands or
hear audible alarms, completely excluding speech- and hearing-impaired users from seam-
less home automation.

• The Privacy Barrier: To accommodate sign language, current systems force users to place
invasive video cameras in personal spaces, creating an unacceptable trade-off between ac-
cessibility and privacy.

• The Wearable Burden: While accurate, requiring an elderly or impaired user to wear heavy,
full-body sensor suits every day is highly impractical for continuous daily living.

• Context Blindness: When non-visual sensors are used in isolation, they suffer from con-
text blindness—easily confusing daily household chores with deliberate communication at-
tempts.

The Ultimate Goal:
Currently, single sensors misclassify Action → Sign transitions as generic continuous movement.
A solution is required that intelligently fuses multiple privacy-preserving sensor modalities to iso-
late deliberate communication intent. By doing so, this project aims to build a silent, invisible
home that seamlessly adapts to the user’s intent without relying on voice or cameras.

The Need for Fusing Modalities

To achieve these use cases without cameras, we rely on non-intrusive sensors:

• Ambient Sensors: Motion detectors that know where you are in the house.
• Minimal Wearables: Simple sensors that track broad body movements.
• WiFi Signals (CSI): Invisible waves that can detect tiny, fine-grained movements like finger

gestures.

Using just one of these sensors fails. For example, WiFi can read sign language in the air, but the
signal gets completely confused if the person is simultaneously walking around the room. This is
why fusing modalities is our primary focus. By combining these sensors, we create a system that
understands the big picture (macro-movements) and the fine details (micro-gestures) at the same
time.

2



Problem Statement: Activity & Communication

Current smart home systems face a critical trade-off between privacy and functional depth, signif-
icantly limiting their real-world applicability. While camera-based architectures offer high recog-
nition accuracy, they severely compromise user privacy in personal spaces; conversely, traditional
non-visual sensors preserve privacy but are restricted to detecting only basic, isolated actions. Con-
sequently, these privacy-centric systems fail to navigate the complexity of natural human behavior,
particularly when multiple activities occur simultaneously within a household. When users engage
in concurrent tasks, existing frameworks lack the multi-modal intelligence required to disentangle
and accurately classify these parallel data streams. This limitation poses a significant barrier to
inclusivity, as fine-grained, deliberate actions—such as sign language communication—are fre-
quently misclassified or missed entirely amidst everyday background motion.

The problem becomes more difficult in homes with multiple people, where current systems can-
not reliably determine which activity belongs to which individual. In addition, most smart home
systems are reactive in nature. They respond only after an action has occurred and do not have
the ability to understand user intent or anticipate future actions. Overall, there is no existing
approach that can reliably handle concurrent activities, identify individuals, and understand
user intent while maintaining user privacy in a real home environment.

Research Objectives

To solve this problem, the project focuses on four clear research objectives:

1. Multi-Modal Sensor Fusion: To combine ambient, wearable, and WiFi sensor data into
a single intelligent framework capable of tracking complex, parallel activities in a home
environment.

2. Accessible Communication (Sign Language): To utilize ambient sensor data as a filter to
remove ”body movement noise” from WiFi signals, allowing the system to accurately read
device-free sign language even when the user is moving.

3. Predictive Intent Awareness: To move beyond just recognizing what the user is doing right
now. By learning the sequence of a user’s daily habits, the system will predict their future
intent (e.g., predicting they are going to bed) to proactively adjust the home environment.

4. Real-Time Edge Actuation: To deploy this combined activity-and-communication model
onto local hardware, triggering immediate smart home responses (like turning on lights or
sending SMS alerts) without relying on cloud processing.

3



2 Literature & Market Survey

Literature Survey The following table summarizes key datasets used to benchmark HAR, cat-
egorized by sensor modality, including datasets focused on fine-grained gestures and predictive
intent.

Type Dataset Description & Sensors Critical Limitation

Ambient CASAS The gold standard for smart homes. Uses Identity Ambiguity: Cannot dis-
(Cook et al.) PIR motion, door, and temp sensors in tinguish who triggered a sensor in

real apartments. multi-resident homes.

Ambient ARAS Collected in 2 real houses with multiple Sensor Noise: High false positives
(Alemdar et al.) residents using 20 ambient sensors. from pets/visitors; lacks ground

truth for overlapping activities.

Wearable UCI-HAR Smartphone (Waist) accelerometer & Location Blind: Detects ”Walk-
(Anguita et al.) gyroscope data for 6 basic ADLs. ing” but not ”Where” (e.g.,

Kitchen vs. Bedroom).

Wearable Opportunity 72 sensors on body/objects capturing Impracticality: Users must wear a
(Roggen et al.) complex gestures (opening doors, drink- full body suit of sensors; unrealis-

ing). tic for daily living.

Wearable UniMiB-SHAR Smartphone accelerometer data focused Limited Granularity: Good for
(Micucci et al.) on fall detection and basic activities. falls, but poor at distinguishing

fine-grained ADLs (e.g., eating).

WiFi Widar 3.0 Large-scale WiFi CSI dataset for gesture Single User Focus: Accuracy
(Zheng et al.) recognition using commodity routers. drops significantly when multiple

users move simultaneously.

WiFi CSI-Bench Robustness benchmark across different Domain Shift: Models trained on
(Wang et al.) domains (rooms/environments). Room A fail in Room B without

extensive retraining.

WiFi WIMANS Multi-user dataset using dual-band WiFi Computational Load: Requires
(Gu et al.) CSI and synchronized cameras. heavy processing to separate mixed

signals from multiple bodies.

WiFi SignFi Fine-grained finger gesture recognition Short Range: Only effective at
(Ma et al.) (Sign Language) using WiFi CSI. very close range (< 1m); not

suitable for whole-home tracking.

WiFi TED-Net Focuses on privacy-preserving Fall Detec- Hardware Specific: Relies on
(Wang et al.) tion using WiFi skeleton formation. specific router configurations that

are hard to deploy universally.

4



Type Dataset Description & Sensors Critical Limitation

WiFi WiFinger Fine-grained finger and gesture recogni- Stationary Assumption: Fails
(Li et al.) tion using CSI, serving as a foundation for catastrophically when micro-

SignFi-like systems. gestures are masked by concurrent
macro-movements (e.g., walking).

Ambient Aruba (CASAS) Longitudinal ambient dataset spanning Concept Drift: Models predict-
(Cook et al.) several months, utilized for sequence ing user intent fail as daily habits

modeling and intent prediction. naturally change over time without
continuous edge-learning.

Market Survey (Competitor Analysis): We analyzed existing commercial solutions to identify
gaps in current technology.

Competitor Primary Focus The Research Gap Reference Link
Smart Home Voice Command & Automa- Context Unaware: They de- Frontiers in
Hubs tion: Excellent at ”if this, then tect motion but do not under- Robotics & AI
(Google Nest, that” triggers (e.g., motion → stand activity. They cannot
Alexa) lights on). distinguish ”Fall” from ”Lying

Down”.

Wearable Tech Biometrics & Fitness: Track- Indoor Blindness: Cannot PMC Healthcare
(Fitbit, Apple ing heart rate, steps, and GPS interact with the home environ- Localization
Watch) outdoor location. ment (e.g., doesn’t know if you

are at the stove or the sink).

Security Systems Perimeter Safety: Intrusion Privacy & Granularity: Re- OVIC IoT Privacy
(ADT, Ring) detection via door sensors and lies on invasive cameras. Non- Report

cameras. camera sensors are binary and
miss daily habits.

Elderly Monitors Emergency Response: Reac- Reactive Only: Triggers after Arquella Care
(LifeAlert) tive systems (button press) for an accident. Cannot predict Insights

falls. varying behavior patterns or
prevent incidents.

WiFi Sensing Device-Free Sensing: Using Identity Confusion: Cannot arXiv (Cornell, Jan
(Origin Wireless) WiFi waves to detect pres- robustly track multiple people. 2026)

ence/breathing. Signals mix, making it impossi-
ble to say who is where.

Table 2: Market Survey highlighting the need for Multi-Modal Fusion.

Research Paper Survey:

5



Paper (Year) Method / Technique Description

HAR in Smart Living ML/DL-based HAR using Comprehensive review of HAR tech-
(2023) multi-sensor data niques for smart living applications.

IoT Smart Home Au- IoT-based automation us- Proposes an IoT system for automat-
tomation ing sensors and APIs ing and controlling smart home de-
(2021) vices.

Activity Predictors via Imitation Learning with Develops models to predict future
Sensor Data Regression models human activities using sensor data.
(2017)

SignFi: Sign Language CNN (9-layer) using WiFi Uses deep learning on WiFi signals to
via WiFi CSI signals recognize sign language gestures.
(2018)

Table 3: State of the Art & Open Problems

Takeaway: Existing research treats IoT, predictive modeling, and WiFi sensing as isolated do-
mains. We bridge this gap by unifying them into a single, multi-modal intent-aware framework.

3 Proposed System Architecture

Core Solution: We propose a system integrating Bazel Board, WiFi CSI (for device-free activity
recognition), and Minimal Wearables (for identity tagging).

1. Hybrid Deep Learning Model: Implement a dual-branch neural network using CNNs to
extract spatial features and LSTMs to capture temporal dependencies from the heterogeneous
sensor data.

2. Attention-Enhanced Fusion: Specific Attention Mechanism within the fusion module to
dynamically weight the importance of different modalities (e.g., prioritizing wearables over
WiFi for fine motor tasks) before final classification.

3. Synchronized Preprocessing Pipeline: Establish a rigid preprocessing workflow focused
on Temporal Alignment and sliding-window segmentation to standardize the varying sam-
pling rates between ambient, wearable, and WiFi signals.

6



Figure 1: Proposed Multi-Modal Architecture

4 Current Status & Plan

Completed Work (Phase 1 Status):

• Dataset Preprocessing: Acquired and preprocessed multiple CASAS smart home datasets (Mi-
lan, Cairo, Kyoto2, Kyoto3, Kyoto4). Converted raw sensor logs into padded temporal sequences
using activity-based segmentation and numerical encoding suitable for sequential deep learning
models.

• Sequential LSTM Architecture Implementation: Implemented and systematically compared
Uni-LSTM (baseline), Bi-LSTM (bidirectional context), Casc-LSTM (stacked refinement), Ens2-
LSTM (ensemble), and CascEns-LSTM (cascade-ensemble) for temporal modeling of ambient
smart home data.

• Model Optimization & Comparative Benchmarking: Performed hyperparameter tuning (32,
64, 128 units), with 64 units yielding optimal generalization. Cross-validation across selected
CASAS datasets showed incremental improvements from bidirectional and ensemble models,
while deeper architectures resulted in diminishing returns relative to computational complexity.

Completed Work (Phase 2 Status):

7



Figure 2: LSTM Model Performance Comparison across evaluated architectures.

Spatial Feature Extraction via CNN

• Spatial Feature Extraction: Trained a Convolutional Neural Network (CNN) to extract high-
dimensional spatial features (such as Frequency Patterns, Posture changes, etc.) from complex
sensor data streams.

• Dataset Selection (OPPORTUNITY): Chosen for its exceptional versatility in tracking daily
living. It comprehensively covers both short-duration micro-movements (e.g., Open Drawer,
Drink from cup) and extended macro-sequences (e.g., Prepare sandwich, Use dishwasher).

• Performance Benchmark: The model achieved a classification accuracy of 99.4% on the OP-
PORTUNITY dataset.

5 Future Implementation

Next Phase Objectives & System Expansion

• Proprietary Data Capture: Construct a homegrown dataset by capturing real-world ambient,
wearable, and WiFi CSI sensor streams to validate the system in a custom environment.

• Hybrid Fusion Models: Develop an attention-guided architecture to merge the temporal se-
quence knowledge (LSTM) with the extracted spatial features (CNN) for robust activity recog-
nition.

• Sign Language Recognition: Integrate WiFi and wearable-based gesture recognition to specif-
ically accommodate users with speech or hearing disabilities.

8



Figure 3: Accuracy graph of CNN on the OPPORTUNITY Dataset.

• End-User App Development: Develop a user interface allowing end-users to seamlessly ob-
serve system status, interact with the smart home, and receive real-time anomaly alerts.

9



References

[1] Diane J. Cook, Aaron S. Crandall, Brian L. Thomas, and Narayanan C. Krishnan. CASAS:
A Smart Home in a Box. Computer (Long Beach Calif), 46(7), July 2013. https://doi.
org/10.1109/MC.2012.328.

[2] H. Alemdar, H. Ertan, O. D. Incel and C. Ersoy. ARAS human activity datasets in
multiple homes with multiple residents. 2013 7th International Conference on Pervasive
Computing Technologies for Healthcare and Workshops, Venice, Italy, 2013. https:
//ieeexplore.ieee.org/document/6563930.

[3] Davide Anguita, Alessandro Ghio, Luca Oneto, Xavier Parra, and Jorge L. Reyes-Ortiz. A
Public Domain Dataset for Human Activity Recognition Using Smartphones on Smartphones.
21st European Symposium on Artificial Neural Networks, Computational Intelligence and
Machine Learning (ESANN), 2013. https://archive.ics.uci.edu/dataset/
240/human+activity+recognition+using+smartphones.

[4] Ricardo Chavarriaga, Hesam Sagha, Alberto Calatroni, Sundara Tejaswi Digumarti, Ger-
hard Tröster, José Del R. Millán, and Daniel Roggen. The Opportunity challenge: A bench-
mark database for on-body sensor-based activity recognition. Pattern Recognition Let-
ters, 34(15):2033–2042, November 2013. https://doi.org/10.1016/j.patrec.
2012.12.014.

[5] Daniela Micucci, Marco Mobilio, and Paolo Napoletano. UniMiB SHAR: A Dataset for Hu-
man Activity Recognition Using Acceleration Data from Smartphones. Applied Sciences,
7(10):1101, 2017. https://doi.org/10.3390/app7101101.

[6] Yue Zheng, Yi Zhang, Kun Qian, Guidong Zhang, Yunhao Liu, Chenshu Wu, and Zheng
Yang. Widar3.0: Zero-Effort Cross-Domain Gesture Recognition Using Wi-Fi. IEEE Trans-
actions on Pattern Analysis and Machine Intelligence, 43(9), 2021. https://tns.thss.
tsinghua.edu.cn/widar3.0/data/TPAMI_Widar3.0_paper.pdf.

[7] Guozhen Zhu, Yuqian Hu, Weihang Gao, Wei-Hsiang Wang, Beibei Wang, and K. J. Ray Liu.
CSI-Bench: A Large-Scale In-the-Wild Dataset for Multi-task WiFi Sensing. arXiv preprint
arXiv:2505.21866, 2025. https://arxiv.org/abs/2505.21866.

[8] Shuokang Huang, Jianwei Gu, et al. WiMANS: A Benchmark Dataset for Multi-User WiFi
Sensing. arXiv preprint arXiv:2402.09430, 2024. https://arxiv.org/abs/2402.
09430.

10



[9] Yongsen Ma, Gang Zhou, and Shuangquan Wang. SignFi: Sign Language Recognition Using
WiFi. Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technolo-
gies, 2(1), 2018. https://dl.acm.org/doi/10.1145/3191755.

[10] Wang et al. TedNet: A Device-free Real-time Fall Detection System using Commercial Wi-
Fi Devices. arXiv preprint arXiv:2504.16655, 2025. https://arxiv.org/abs/2504.
16655.

[11] Jianpu Li, Yan Sun, Rui Zhang, and Yanyong Zhang. WiFinger: talk to smart devices with
finger-grained free-space gesture recognition. Proceedings of the 2016 ACM International
Joint Conference on Pervasive and Ubiquitous Computing (UbiComp ’16), 2016. https:
//dl.acm.org/doi/10.1145/2971648.2971690.

[12] Bryan D. Minor, Janardhan Rao Doppa, and Diane J. Cook. Learning Activity Predictors from
Sensor Data: Algorithms, Evaluation, and Applications. IEEE Transactions on Knowledge
and Data Engineering, 29(12):2744–2757, 2017. https://ieeexplore.ieee.org/
document/8031060.




below are jsut documentation soem works we have done

ESPectre Documentation 

1. Introduction 

ESPectre is a motion detection system based on Wi-Fi Channel State Information (CSI) analysis. It leverages the native capabilities of ESP32 chips to detect movement without the need for cameras or microphones, ensuring total privacy. It integrates natively with Home Assistant via ESPHome. 

2. Key Advantages 

- Privacy-Preserving: No cameras or audio recording. 
    

- Works Through Walls: Wi-Fi signals penetrate drywall and other materials. 
    

- Cost-Effective: Uses standard ESP32 devices (~€10). 
    

- Native Integration: Seamless auto-discovery in Home Assistant via ESPHome Native API. 
    

3. Hardware Requirements 

To set up ESPectre, you will need the following hardware: 

- 2.4GHz Wi-Fi Router (802.11b/g/n/ax supported). 
    

- ESP32 device with CSI support (ESP32-C6, ESP32-S3, or ESP32-C3 recommended). 
    

- Home Assistant (running on Raspberry Pi, PC, or NAS). 
    

4. Setup Guide (ESPHome CLI) 

This method is recommended for developers and those wanting deep customization. 

Step 1: Install ESPHome 

Create a virtual environment and install the ESPHome CLI tool: 

python3 -m venv venv venv\Scripts\activate pip install esphome 

Step 2: Download Configuration 

Download the example YAML for your hardware (e.g., espectre-c6.yaml, espectre-s3.yaml). 

Step 3: Build and Flash 

Connect your ESP32 via USB and run: 

esphome run espectre-c6.yaml 

Step 4: Configure WiFi 

After flashing, use BLE (via Home Assistant app) or the Captive Portal to connect the device to your Wi-Fi network. 

5. System Architecture & Algorithms 

ESPectre uses a sophisticated signal processing pipeline to convert raw Wi-Fi data into motion events. 

- Gain Lock: Stabilizes hardware AGC and FFT scaling to ensure clean amplitude measurements (locks in ~3 seconds). 
    

- NBVI (Normalized Band Variance Index): Automatically selects the optimal 12 subcarriers for motion detection, avoiding noise and guards. 
    

- MVS (Moving Variance Segmentation): The default algorithm that identifies motion by analyzing turbulence variance over a sliding window. 
    

- ML (Neural Network): An experimental MLP-based detector (12→16→8→1) that provides fast boot and robust generalization. 
    

6. Sensor Placement Guide 

Optimal placement is crucial for reliable performance: 

- Range: 3-8 meters from the router is optimal. 
    

- Height: 1-1.5 meters (desk height) is recommended. 
    

- Obstacles: Avoid metal obstacles (fridges, cabinets) in the direct path if possible. 
    

- Orientation: External antennas should be oriented vertically for better coverage. 
    

7. Deployment Reference 

The image below illustrates a typical deployment setup with a Station and an Access Point. 




Rishiikesh S K
The Physics of WiFi Sensing: Why These
Specifications?
The hardware setup relies on an Access Point (AP - Router) and a Station (STA - Laptop).
● Why the 5GHz Band? WiFi operates primarily on 2.4GHz or 5GHz. The 5GHz band has a
shorter wavelength. Shorter wavelengths are more sensitive to micro-movements, making
it possible to detect small finger spelling alongside large arm waving.
● Why 20MHz Channel Width? A 20MHz channel isn't a single wave; it is divided into
smaller frequency bands called "sub-carriers" (like lanes on a highway). The Intel 5300 WiFi
card extracts data from 30 of these sub-carriers, giving us 30 distinct frequency
perspectives of the movement.
● Why 3 Antennas (MIMO)? The AP has 3 antennas, and the STA has 1. This 3x1
Multiple-Input Multiple-Output (MIMO) setup provides "spatial diversity." Because the
antennas are physically separated, the receiver gets three slightly different geometric
angles of how the signal bounced off the body.
Data Characteristics and Preprocessing
The raw data is collected as Channel State Information (CSI). CSI is a matrix of complex
numbers (having a real and imaginary part) that measures the state of the radio wave.
The Raw Data Shape
The raw data for a single gesture has the shape (200, 30, 3):
● 200: Time steps (snapshots taken every 5 milliseconds).
● 30: Sub-carriers (frequencies).
● 3: Receiving/Transmitting antennas.
The raw Channel State Information (CSI) is not a simple list of numbers; it is a multi-dimensional
matrix of complex numbers. A complex number consists of a real part and an imaginary part
(denoted by j in Python). If you print a single snapshot of the raw data, it looks like this:
[ 2.45 - 1.2j, 2.41 - 1.3j, 2.38 - 1.1j, ... ]
Each complex number represents the exact physical state of a radio wave at a specific
millisecond. However, neural networks struggle to process raw complex numbers efficiently.
Therefore, we must use complex math to split these numbers into two distinct physical
features: Amplitude and Phase.
Decoding the Waveforms
The generated graphs plot the extraction of these features over 200 time steps (approximately 1
second of movement).
● The Amplitude Graph:
Amplitude represents the physical strength or "power" of the WiFi signal arriving at the
receiver. As the user performs a sign gesture, their arm and hand act as physical
obstacles. They temporarily block, absorb, or reflect the radio waves. The peaks and
valleys you see in the Amplitude curve represent the macro-movements of the
gesture—for example, a hand sweeping across the chest will create a distinct dip and
rise in the signal strength.
● The Raw Phase Graph: Phase measures the alignment of the radio wave (how much
the wave has shifted in time compared to when it was sent). If you look at the Raw
Phase graph, it looks like a chaotic, jagged "sawtooth" wave. This is a mathematical
artifact. In physics, phase is measured in angles (radians). Because a circle is $2\pi$
radians, the WiFi hardware wraps all phase measurements to stay within a strict
boundary of $-\pi$ to $\pi$. When the hand movement causes the wave to shift past
$\pi$, the measurement mathematically "teleports" to $-\pi$, creating a false cliff in the
data.
● The Unwrapped Phase Graph: This graph is the result of our preprocessing function
(np.unwrap). By computationally unwrapping the phase, we stitch those jagged cliffs
back together into a continuous line. The resulting smooth curve is a highly precise
trajectory of the gesture. Because phase is sensitive to changes in distance as small as
a fraction of a wavelength, this curve captures the microscopic movements of the user's
fingers, which the Amplitude graph completely misses.
Visual Proof of Domain Shift and Sensor Fusion
By plotting the exact same gesture across three different perspectives, the graphs provide
undeniable visual proof of our architectural decisions.
● Why we need Sensor Fusion (Lab Downlink vs. Lab Uplink): Row 1 (Downlink) and
Row 2 (Uplink) show the exact same gesture occurring in the exact same room at the
exact same time. However, because the Downlink is recorded by the Laptop and the
Uplink is recorded by the Router, their waveforms are slightly different. The peaks occur
at different magnitudes. By feeding both of these streams into our Dual-Stream 1D-CNN,
we provide the network with a 360-degree "stereo" view of the movement.
● Why the Original Paper Failed (Lab vs. Home): Row 3 represents the Home
Downlink. The user is performing the exact same sign language gesture. However, the
red graphs look completely different from the blue and green graphs. The macro-curves
peak at different times, and the baseline structure has shifted. This happens because
the room has changed—the distance between the antennas shrunk from 230cm to
130cm, and the signal is now bouncing off a bed instead of lab desks.
Preprocessing: Extracting True Features
Neural networks struggle with raw complex numbers. Furthermore, hardware clocks on the AP
and STA are never perfectly synchronized, causing Sampling Time/Frequency Offsets
(STO/SFO) that introduce massive, random noise into the signal.
1. Amplitude Extraction: We calculate the absolute value (np.abs) of the complex numbers
to get the physical strength of the signal.
2. Phase Unwrapping: Phase measures signal alignment in angles (radians). Because math
wraps angles between and , a continuous hand movement creates artificial,
jagged "cliffs" in the data. We use np.unwrap to stitch these cliffs back together, revealing
the true, continuous trajectory of the hand.
3. Reshaping: We flatten the 30 sub-carriers and 3 antennas into a single array. 90
Amplitude features + 90 Phase features = 180 features per time step. The final shape fed
to the model is (200, 180).
The Flaws in the Original SignFi Approach
The original authors proposed a 9-layer 2D Convolutional Neural Network (CNN) and claimed
94.81% accuracy across environments. However, our technical audit revealed two severe flaws:
Flaw 1: Spatial Modeling of Temporal Data (The 2D CNN issue)
The original paper feeds the (200, 60, 3) data into a 2D CNN, using filters.
● The Problem: A 2D CNN treats the data like a static photograph. The filter slides across
the time axis and the frequency axis simultaneously. This mathematically blurs the
sequential nature of human movement. It fails to effectively track the chronological
trajectory of the hand.
Flaw 2: Time-Series Autocorrelation and Data Leakage
During data collection, users repeated the exact same sign 20 times in a row while sitting in the
same chair.
● The Problem: By using a random train_test_split, the original authors caused severe data
leakage. The model tested on gestures that happened seconds apart from the training
gestures. The network hit 100% accuracy because it memorized the highly specific,
temporary multi-path reflections of that 2-minute window, rather than learning the
abstract concept of the sign.
Novel Approach: Dual-Stream 1D-CNN Sensor Fusion
To solve the spatial modeling issue, we designed a completely new architecture.
Why Sensor Fusion?
WiFi is a two-way street. The AP transmits to the STA (Downlink), and the STA transmits to the
AP (Uplink). The original paper largely ignored the Uplink. We built a Dual-Stream architecture
that processes the Downlink and Uplink streams in parallel and fuses them. This gives the
network a "stereo" 360-degree profile of the room from both devices' perspectives.
Why 1D-CNN?
Instead of a 2D filter, we use Conv1D. The 1D filter slides only across the time axis (the 200
snapshots). It learns exactly how the 180 physical features change from millisecond to
millisecond, properly mapping the temporal physics of the gesture.
Layer-by-Layer Breakdown
● Conv1D: Extracts temporal sequence features (how the wave changes over time).
● Batch Normalization: Normalizes the data batches. WiFi signals are highly sensitive to tiny
environmental changes; this stabilizes the gradients during training and prevents the
model from over-indexing on small signal anomalies.
● ReLU (Rectified Linear Unit): Replaces negative values with zero. Real-world human
motion is non-linear. Without ReLU, the network would just act like a flat linear regression
model and fail to learn complex curves.
● AveragePooling1D: Shrinks the data by averaging neighboring values. We specifically
avoided Max Pooling because WiFi CSI data contains high-frequency hardware noise
spikes; Max Pooling would amplify that noise, whereas Average Pooling smooths it out.
● Concatenate: The fusion layer where the Downlink spatial features and Uplink spatial
features are mathematically combined.
● Dropout (0.6): Randomly deactivates 60% of the neurons during training. This prevents
overfitting by forcing the network to learn robust, universal patterns rather than
memorizing exact data points.
● Dense (512): A fully connected layer that acts as the "brain," combining all the extracted
temporal features to make a decision.
● Dense (276) + Softmax: The final output layer. Softmax converts the raw model scores
into a beautiful probability distribution (0 to 100%) across all 276 possible sign gestures.
Final Evaluation: Exposing Domain Shift
To prove the data leakage flaw, we discarded random splitting. We trained our Dual-Stream
network exclusively on the Lab dataset and evaluated it exclusively on the unseen Home
environment.
The Result: 0.36% Accuracy.
What this proves to the team:
Since (0.36%), the model was reduced to pure random guessing. This
mathematically proves the phenomenon of Domain Shift. WiFi CSI does not track the human
body in isolation; it tracks the entire room. Because the home environment had different
furniture, dimensions, and antenna distances, the physical radio wave signatures changed
completely.
The original authors claimed 94.81% across environments, but our audit proves they artificially
inflated this by mixing the Lab and Home datasets prior to cross-validation, forcing the network
to memorize both rooms rather than proving true generalization.
Conclusion
We successfully identified a major data leakage flaw in a published paper, diagnosed the
weakness in their spatial 2D modeling, engineered a superior Dual-Stream 1D-CNN temporal
architecture, optimized the data pipeline to run on constrained hardware, and conducted a
rigorous cross-domain evaluation. To make this viable for real-world production, future work
must focus on Domain Adversarial Neural Networks (DANN) to strip away background room
noise and isolate the human subject.
def create_branch(input_shape, branch_name):
# This creates the entry point for the data. 'input_shape' is exactly 200 time steps and 180
features.
inputs = layers.Input(shape=input_shape, name=f'{branch_name}_input')
# Block 1: The First 1D Convolution
# filters=64: The network will learn 64 different temporal patterns (like a wave dropping, or a
wave spiking).
# kernel_size=3: The window looks at 3 time steps (about 15 milliseconds) at a time, sliding
forward.
# padding='same': Adds zeros to the edges of the data so the output size doesn't shrink
during the slide.
x = layers.Conv1D(filters=64, kernel_size=3, padding='same')(inputs)
# Normalizes the batch data. This stabilizes the learning process so the network doesn't get
# confused by random, tiny spikes in the WiFi hardware noise.
x = layers.BatchNormalization()(x)
# Rectified Linear Unit. This converts any negative numbers to 0.
# It introduces non-linearity, allowing the model to learn complex, curved physical
movements instead of just straight mathematical lines.
x = layers.ReLU()(x)
# Down-sampling. It looks at a window of 2 time steps and outputs the average.
# This cuts the sequence length in half, reducing computational load and smoothing out
high-frequency sensor noise.
x = layers.AveragePooling1D(pool_size=2)(x)
# Block 2: The Second 1D Convolution (Extracting higher-level movement features)
# Now it uses 128 filters to learn even more complex patterns from the smoothed data.
x = layers.Conv1D(filters=128, kernel_size=3, padding='same')(x)
x = layers.BatchNormalization()(x)
x = layers.ReLU()(x)
x = layers.AveragePooling1D(pool_size=2)(x)
# At this point, the data is still a 2D matrix (remaining time steps x 128 filters).
# Flatten squashes it into a single, massive 1D array of numbers so it can be fed into a
standard Dense layer.
x = layers.Flatten()(x)
# The function returns the starting point (inputs) and the ending point (x) of this branch.
return inputs, x
—-------------
# Grabs the shape from our training data to tell the Input layer what to expect.
input_shape = (X_dl_train.shape[1], X_dl_train.shape[2])
# We call our factory function twice.
# 'dl_features' contains the flattened patterns learned from the Router.
# 'ul_features' contains the flattened patterns learned from the Laptop.
dl_inputs, dl_features = create_branch(input_shape, 'DL')
ul_inputs, ul_features = create_branch(input_shape, 'UL')
# THE SENSOR FUSION: This layer simply glues the Downlink array and the Uplink array
together
# end-to-end. The network now possesses a complete 3D perspective of the room.
fused_features = layers.Concatenate(name='sensor_fusion_layer')([dl_features, ul_features])
—-------------------
# Drops 60% of the connections randomly during training. This forces the network to
generalize
# and look at the whole picture, severely preventing overfitting.
x = layers.Dropout(0.6)(fused_features)
# A standard neural network layer with 512 neurons. Every neuron connects to every single
feature
# coming out of the fusion layer. This is where the complex reasoning happens.
x = layers.Dense(512)(x)
x = layers.BatchNormalization()(x)
x = layers.ReLU()(x)
# Another heavy dropout layer just before the final decision to ensure strict regularization.
x = layers.Dropout(0.6)(x)
# The Output Layer. It has exactly 276 neurons, one for every possible sign language gesture.
# The 'softmax' activation function converts the raw math scores into a probability percentage
# (e.g., 98% chance it's "Father", 1% chance it's "Mother", 1% distributed among the rest).
outputs = layers.Dense(276, activation='softmax', name='classification_output')(x)
—-------
# This ties the whole graph together, specifying exactly where the data enters (the two inputs)
# and where the prediction exits.
model = models.Model(inputs=[dl_inputs, ul_inputs], outputs=outputs)
# model.compile sets the rules for training:
# 1. optimizer=Adam: An advanced algorithm that automatically adjusts how big of a step it
takes
# when updating the weights, speeding up training.
# 2. loss='sparse_categorical_crossentropy': The mathematical formula used to calculate how
"wrong"
# the model's predictions are. We use "sparse" because our labels are single integers (0 to
275).
# 3. metrics=['accuracy']: Tells the model to report its performance in a simple percentage
format for us to read.
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
loss='sparse_categorical_crossentropy',
metrics=['accuracy'])










