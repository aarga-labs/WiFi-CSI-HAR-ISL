# Comprehensive WiFi-HAR Research Guide

## ⚠️ Important Note on "Kastrons"
I conducted extensive research but could not locate a specific research project, framework, or dataset explicitly named "Kastrons" in relation to WiFi-based Human Activity Recognition. If you have additional context or clarification about what Kastrons refers to, please provide it for more targeted research.

---

## WiFi-HAR Overview

WiFi-based Human Activity Recognition (WiFi-HAR) is a non-intrusive sensing technique that uses Channel State Information (CSI) from WiFi signals to recognize human activities. It offers advantages over traditional methods:
- **Privacy-preserving** - No cameras needed
- **Non-intrusive** - Works through walls
- **Cost-effective** - Uses existing WiFi infrastructure
- **Device-free** - No wearables required

---

## Key Research Papers (Organized by Publication Date)

### 2024-2025 Latest Work

1. **Vision Transformers for Human Activity Recognition Using WiFi Channel State Information**
   - IEEE Internet of Things Journal (2024)
   - Topic: Vision transformers applied to WiFi CSI-based HAR

2. **Exposing Data Leakage in Wi-Fi CSI-Based Human Action Recognition**
   - Inventions (2024)
   - Topic: Critical analysis of benchmark dataset issues

3. **Towards Stable WiFi-based HAR from Imbalanced Data and Domain Shift**
   - ACM Transactions on Sensor Networks (2025)
   - Topic: Addressing real-world challenges in WiFi-HAR

4. **WiPhase: A Human Activity Recognition Approach by Fusing WiFi CSI Phase**
   - IEEE Transactions (2024)
   - Topic: Two-stream model using temporal and sub-carrier features

5. **Cross-Domain Human Activity Recognition Using Reconstructed WiFi CSI (TensFi)**
   - Digital Health (2024)
   - Topic: Tensor-based approach for cross-domain HAR

6. **WiFi CSI Based Temporal Activity Detection via Dual Pyramid Network**
   - AAAI Conference (2024)
   - ArXiv: 2412.16233
   - Topic: Temporal activity segmentation with signal semantic encoders

7. **CSI-Bench: A Large-Scale In-the-Wild Dataset for Multi-task WiFi Sensing**
   - ArXiv: 2505.21866 (2025)
   - **Dataset: 461+ hours of CSI data from 35 users, 26 environments**
   - Tasks: Fall detection, breathing monitoring, localization, HAR, user identification

### 2023 Key Works

1. **Enhanced Human Activity Recognition Using Wi-Fi Sensing (PA-CSI Model)**
   - Journal of Healthcare Engineering (2025)
   - Dataset Results: StanWiFi (99.9%), MultiEnv (98.0%), MINE lab (99.9%)
   - Topic: Multi-head attention with multi-scale convolutional networks

2. **MM-Fi: Multi-Modal Non-Intrusive 4D Human Dataset**
   - NeurIPS 2023 Datasets & Benchmarks Track
   - ArXiv: 2305.10345
   - **Dataset: 320k+ synchronized frames from 5 modalities (RGB, Depth, LiDAR, mmWave Radar, WiFi CSI)**
   - 40 human subjects, 27 action categories
   - GitHub: Available

3. **WiMANS: A Benchmark Dataset for WiFi-based Multi-user Activity Sensing**
   - ECCV 2024
   - ArXiv: 2402.09430
   - **Dataset: 11,286 CSI samples (9.4+ hours) of dual-band WiFi (2.4GHz & 5GHz)**
   - First multi-user WiFi CSI dataset with synchronized videos
   - Supports 0-5 simultaneous users

4. **SHARP: Environment and Person Independent Activity Recognition**
   - IEEE Transactions on Mobile Computing (2023)
   - Topic: Domain-independent WiFi-based HAR

5. **CSI-based Location-Independent HAR Using Feature Fusion**
   - IEEE Transactions on Instrumentation and Measurement (2022)
   - Topic: Cross-location generalization

### 2021-2022 Influential Works

1. **Two-Stream Convolution Augmented Transformer for Human Activity Recognition (THAT)**
   - AAAI Conference on AI (2021)
   - GitHub: https://github.com/windofshadow/THAT
   - State-of-the-art architecture combining temporal and channel-based feature streams

2. **Data Augmentation and Dense-LSTM for WiFi Signal HAR**
   - IEEE Internet of Things Journal (2021)
   - Topic: Data augmentation strategies for small WiFi datasets

3. **DeepSeg: Deep-Learning-Based Activity Segmentation Framework**
   - IEEE Internet of Things Journal (2021)
   - GitHub: Available
   - Topic: Accurate activity boundary detection

4. **EfficientFi: Towards Large-Scale Lightweight WiFi Sensing via CSI Compression**
   - IEEE Internet of Things Journal (2022)
   - GitHub: Available
   - Topic: Edge device deployment and compression techniques

### Earlier Foundational Works (2017-2020)

1. **Human Activity Recognition based on Wi-Fi CSI Data - A Deep Neural Network Approach**
   - Author: A Zhuravchak et al.
   - Cited by 78+
   - GitHub: https://github.com/Retsediv/WIFI_CSI_based_HAR
   - Dataset link: https://figshare.com/articles/dataset/

2. **Deep Learning Driven Wireless Real-time Human Activity Recognition**
   - IEEE Transactions (2020)
   - Topic: MIMO radar sensing for activity recognition

3. **WiFi Sensing on the Edge: Signal Processing Techniques**
   - IEEE Communications Surveys & Tutorials (2022)
   - ArXiv: Available
   - Topic: Edge computing implementation on ESP32

4. **WiFi-based Human Activity Recognition through wall using CSI**
   - Engineering Science and Technology (2024)
   - ArXiv: 2024-01-08
   - Topic: Through-wall activity recognition using MIMO technology

5. **Human Activity Sensing with Wireless Signals: A Survey**
   - IEEE Journal (2020)
   - Cited by 104+
   - Comprehensive review of wireless sensing approaches

6. **A Survey of Human Activity Recognition Using WiFi CSI**
   - ArXiv: 1708.07129
   - Topic: Early comprehensive survey of CSI-based methods

7. **Understanding and Modeling of WiFi Signal Based Human Activity Recognition**
   - MobiCom (2017)
   - Topic: Foundational work on WiFi-based HAR

### Deep Learning Architecture Papers

1. **CsiGAN: Robust CSI-Based Activity Recognition With GANs**
   - IEEE Internet of Things Journal (2019)
   - GitHub: Available
   - Topic: Generative adversarial networks for HAR

2. **Mitigating Data Leakage in WiFi CSI Benchmark**
   - IEEE Transactions on Mobile Computing (2024)
   - Topic: Proper data partitioning in benchmarks

3. **HARNet: Automatic Recognition Using CNN and LSTM**
   - Journal of Engineering (2024)
   - Topic: Hybrid CNN-LSTM architecture

---

## Public Datasets

### Large-Scale Datasets

| Dataset Name | Size | Modalities | Activities | Subcarriers | Notes |
|---|---|---|---|---|---|
| **CSI-Bench** | 461+ hours | WiFi CSI | Fall, Breathing, Loc., HAR, UID, Prox. | Multiple | In-the-wild, 35 users, 26 environments |
| **MM-Fi** | 320k+ frames | RGB, Depth, LiDAR, mmWave, WiFi | 27 actions | 114 | Multimodal, 40 subjects |
| **WiMANS** | 11,286 samples | WiFi CSI + Video | 6 activities | 114 (2.4 & 5GHz) | Multi-user, dual-band |
| **NTU-Fi** | Multiple sets | WiFi CSI | 6 HAR + 14 gaits | 114 | Atheros CSI tool |
| **Widar 3.0** | 258K instances | WiFi CSI | Gesture recognition | 30 | 75 domains, 8,620 mins total |
| **WiAR** | 30 reps × 10 users | WiFi CSI | 16 activities | RSSI+CSI | 10 volunteers, 3 environments |
| **UT_HAR** | Continuous | WiFi CSI | 6 activities | 30 | Continuous, no golden timestamps |
| **Wireless Sensing Dataset** | Multiple rooms | WiFi CSI + UWB | Multiple | 114 | 3 rooms, mixed modalities |
| **CSIHAR Dataset** | Zhuravchak et al. | WiFi CSI | 6 activities | 30 | 3 different rooms, LSTM-ready |
| **StanWiFi** | Large-scale | WiFi CSI | Multiple | 30 | Stanford collection |
| **MultiEnv** | Large-scale | WiFi CSI | Multiple | 30 | Multi-environment benchmark |

### Dataset Download Links

- **CSI-Bench**: Project page and code available
- **MM-Fi**: NeurIPS Datasets & Benchmarks (2023)
- **WiMANS**: https://arxiv.org/abs/2402.09430
- **Wireless Sensing Dataset (WiFi+UWB)**: https://figshare.com/articles/dataset/Wireless_sensing_dataset_for_human_activity_recognition_HAR_/20444538
- **CSIHAR (Zhuravchak)**: https://figshare.com/articles/dataset/ (with GitHub implementation)
- **WiAR**: https://github.com/linteresa/WiAR
- **StanWiFi & MultiEnv**: Available through SenseFi benchmark

---

## GitHub Repositories & Tools

### Benchmark Libraries

1. **SenseFi: WiFi CSI Sensing Benchmark**
   - GitHub: https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark
   - PyTorch implementation
   - Model Zoo with state-of-the-art architectures
   - Supports: UT_HAR, NTU-Fi-HumanID, NTU-Fi_HAR, Widar

2. **Awesome-WiFi-CSI-Sensing**
   - GitHub: https://github.com/NTUMARS/Awesome-WiFi-CSI-Sensing
   - Comprehensive resource list (70+ papers)
   - Organized by: Surveys, Applications, Datasets, Tools

3. **WIFI_CSI_based_HAR**
   - GitHub: https://github.com/Retsediv/WIFI_CSI_based_HAR
   - Complete pipeline from data collection to model training
   - LSTM-based architecture
   - Includes preprocessing and feature extraction

### Specific Paper Implementations

1. **THAT (Two-Stream Convolution Augmented Transformer)**
   - GitHub: https://github.com/windofshadow/THAT

2. **MM-Fi Dataset Code**
   - Available with dataset paper

3. **DeepSeg**
   - GitHub: Available

4. **EfficientFi**
   - GitHub: Available

5. **stability-csi-har**
   - GitHub: https://github.com/GeoTecINIT/stability-csi-har
   - Docker environment included

### CSI Collection Tools

1. **Intel 5300 NIC CSI Tool**
   - 30 subcarriers, 20MHz bandwidth

2. **Atheros CSI Tool**
   - 114 subcarriers, 40MHz bandwidth

3. **Nexmon CSI Tool**
   - Mobile/RasPi compatible
   - Up to 256 subcarriers, 80MHz

4. **ESP32 CSI Tool**
   - GitHub: https://github.com/StevenMHernandez/ESP32-CSI-Tool
   - Embedded device collection

---

## State-of-the-Art Methods

### Architecture Types

1. **Transformer-Based**
   - Two-Stream Convolution Augmented Transformer (THAT)
   - Vision Transformers for CSI
   - Achieves 99%+ accuracy on benchmarks

2. **CNN + LSTM Hybrid**
   - HARNet architecture
   - CNN for spatial feature extraction
   - LSTM for temporal modeling
   - 90%+ accuracy

3. **GAN-Based**
   - CsiGAN for robustness
   - Domain adaptation capabilities

4. **Multi-scale Convolutional Networks**
   - PA-CSI model with multi-head attention
   - Processes both amplitude and phase

### Key Performance Metrics

- **StanWiFi Dataset**: 99.9% accuracy (PA-CSI model)
- **MultiEnv Dataset**: 98.0% accuracy
- **MINE Lab Dataset**: 99.9% accuracy
- **Cross-domain generalization**: Emerging research area

---

## Signal Processing Pipeline

### 1. CSI Data Collection
- Extract from WiFi transmitter-receiver pairs
- Multiple antennas (MIMO) for better accuracy
- Dual-band (2.4GHz & 5GHz) when possible

### 2. Preprocessing
- Amplitude/Phase separation
- Butterworth filtering
- Principal Component Analysis (PCA)
- Kalman filtering
- Time alignment

### 3. Feature Extraction
- Temporal features (moving variance, speed)
- Spectral features (FFT, wavelets)
- Spatial features (multi-antenna correlation)
- Sub-carrier correlations
- Autospectra of principal components

### 4. Activity Segmentation
- Kalman-based segmentation
- Sliding window approaches
- Adaptive thresholding

### 5. Classification
- Deep learning models (CNN, LSTM, Transformers)
- Machine learning (SVM, Random Forest)
- Hybrid approaches

---

## Challenges & Open Problems

1. **Cross-Domain Generalization** - Models trained in one environment don't transfer well
2. **Data Leakage** - Improper partitioning inflates reported accuracy
3. **Multiple User Scenarios** - Limited datasets with multiple simultaneous users
4. **Real-World Noise** - Environmental interference affects accuracy
5. **Edge Deployment** - Computational efficiency on resource-constrained devices
6. **Robustness** - Performance degradation with environment changes

---

## Research Communities & Venues

### Top Publication Venues
- IEEE Transactions on Mobile Computing
- ACM Annual International Conference on Mobile Computing (MOBICOM)
- IEEE Internet of Things Journal
- AAAI Conference on Artificial Intelligence
- ECCV (European Conference on Computer Vision)
- IEEE Transactions on Vehicular Technology

### Research Groups
- NTU MARS Lab (Awesome-WiFi-CSI-Sensing)
- Stanford University
- University of Toronto
- Various IEEE research labs

---

## Recommended Learning Path

1. **Start with surveys**: 
   - "WiFi Sensing with Channel State Information: A Survey" (ACM Computing Surveys, 2019)
   - "Human Activity Sensing with Wireless Signals: A Survey" (IEEE Journal, 2020)

2. **Understand basics**:
   - Read foundational papers on WiFi-based HAR from MobiCom 2017-2018

3. **Learn state-of-the-art**:
   - THAT (Transformer approach)
   - PA-CSI (Multi-scale networks)
   - MM-Fi (Multimodal understanding)

4. **Hands-on implementation**:
   - Use SenseFi benchmark
   - Replicate THAT or CsiGAN
   - Try ESP32 CSI Tool for hardware experience

5. **Explore datasets**:
   - Start with WiAR or UT_HAR (smaller)
   - Progress to NTU-Fi or Widar 3.0
   - Use CSI-Bench for production-level work

---

## Recent Trends (2024-2025)

1. **Multimodal Fusion** - Combining WiFi with LiDAR, mmWave radar
2. **Large Language Models** - Wi-Chat integrating LLMs with WiFi sensing
3. **Edge AI** - On-device inference on ESP32, RasPi
4. **Cross-Domain Learning** - Domain adaptation and generalization
5. **Privacy-Preserving Methods** - Federated learning approaches
6. **Temporal Activity Detection** - Fine-grained activity segmentation

---

## Important References

**If you can provide more details about "Kastrons"**, such as:
- Is it a specific lab or research group?
- Is it a particular framework or tool name?
- Any papers or projects it's associated with?
- Alternative spellings?

This would help in conducting more targeted research.

---

## Citation for Research

If using this compilation, please cite relevant papers from the list above and acknowledge:
- NTU MARS Lab (Awesome-WiFi-CSI-Sensing)
- SenseFi benchmark paper (Yang et al., 2023)
- Individual dataset and method papers
