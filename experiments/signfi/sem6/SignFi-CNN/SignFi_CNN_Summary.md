# SignFi-CNN: Comprehensive Summary & Analysis Report

---

## 1. Project Overview

**SignFi-CNN** is a WiFi-based sign language recognition system that uses **Channel State Information (CSI)** captured from standard WiFi devices to classify **276 sign language gestures**. Instead of cameras or wearable sensors, it leverages the way human hand movements distort WiFi signals propagating between a transmitter and receiver.

### How It Works
```
Person performs a sign gesture
        ↓
WiFi signal path is altered by hand/arm movement
        ↓
CSI (Channel State Information) is captured at the receiver
        ↓
CSI contains amplitude (strength) and phase (timing) for each subcarrier-antenna pair
        ↓
CNN processes the CSI "image" and classifies the gesture
```

---

## 2. Dataset Description

### Source
- **Dataset**: SignFi Lab Environment Dataset
- **File**: `dataset_lab_276_dl.mat` (MATLAB format, ~1.4 GB)
- **Keys**: `csid_lab` (CSI data), `label_lab` (labels)

### Dimensions

| Axis | Size | Name | Physical Meaning |
|------|------|------|-----------------|
| 0 | ~5,520 | Samples | Each sample = one recorded gesture performance |
| 1 | 200 | Subcarriers | OFDM frequency sub-bands (frequency resolution of WiFi) |
| 2 | 30 | Antennas | 3 receivers × 10 antennas each (MIMO spatial diversity) |
| 3 | 3 | Channels | Complex-valued transmit-receive antenna pair combinations |

### Key Properties
- **Complex-valued data**: Each CSI entry is a complex number `a + bj`
- **Extracted features**: Amplitude `|z| = √(a² + b²)` and Phase `∠z = atan2(b, a)`
- **Final input shape**: `(N, 200, 30, 6)` — 6 channels (3 amplitude + 3 phase)
- **Classes**: 276 unique sign language gestures
- **Samples per class**: ~20 (balanced dataset)
- **Total features per sample**: 200 × 30 × 6 = 36,000

### Why .mat Format?
The data is 4-dimensional (samples × subcarriers × antennas × channels), which cannot be represented as a simple 2D CSV. The `.mat` format natively supports multi-dimensional arrays. For visualization, we generate:
- An **HTML report** (`SignFi_Data_Report.html`) with structured tables
- **CSV files** for per-class statistics (`class_statistics.csv`)

---

## 3. Data Analysis Findings

### 3.1 Summary Statistics

The CSI data shows these key characteristics:

| Metric | Amplitude | Phase (radians) |
|--------|-----------|-----------------|
| Range | 0 to ~50+ | -π to +π |
| Distribution | Right-skewed (most values small, few large) | Approximately uniform |
| Noise level | Moderate | High |
| Information content | High (gesture-dependent patterns) | Medium (noisy but useful) |

### 3.2 Class Distribution
- The dataset is **balanced**: each of the 276 classes has approximately the same number of samples (~20)
- This means no class weighting or oversampling is needed
- However, 20 samples per class is **very few** for deep learning

### 3.3 Signal Characteristics

**Amplitude signals**:
- Show clear spatial patterns (vertical streaks for antenna-specific variations, horizontal bands for frequency-dependent changes)
- Different gestures create visually distinct amplitude heatmaps
- Signal strength varies across subcarriers (frequency-selective fading)

**Phase signals**:
- More chaotic/noisy than amplitude
- WiFi phase is highly sensitive to hardware clock offsets, sampling timing, and environmental perturbations
- Despite noise, phase carries complementary gesture information
- Phase wrapping (jumps between -π and +π) adds complexity

### 3.4 Antenna Correlation
- Antennas within the **same receiver** are more correlated (they share hardware)
- Antennas across **different receivers** are less correlated (different spatial positions)
- This spatial diversity is exactly what makes MIMO useful — each receiver captures the gesture from a different angle

### 3.5 Channel Correlation
- The 3 CSI channels may show varying degrees of correlation
- Lower cross-channel correlation means each channel provides independent/diverse information
- This justifies using all 3 channels rather than any single one

---

## 4. Data Challenges

### Challenge 1: Extreme Inter-Class Similarity
- **Problem**: Many gesture classes have very similar CSI patterns (cosine similarity > 0.95)
- **Impact**: The CNN must learn extremely subtle differences between classes
- **Why it happens**: Similar hand positions produce similar WiFi signal distortions
- **Mitigation**: Using both amplitude AND phase features, careful regularization

### Challenge 2: Limited Training Data
- **Problem**: Only ~20 samples per class (total ~5,520)
- **Impact**: High risk of overfitting, especially with complex models
- **Why it matters**: Deep learning typically needs 1,000+ samples per class
- **Mitigation**: Shallow network (1 conv layer), strong L2 regularization, data augmentation (future work)

### Challenge 3: High Dimensionality
- **Problem**: 36,000 features per sample with only 5,520 total samples
- **Impact**: Curse of dimensionality — the feature space is sparsely populated
- **Mitigation**: Conv + MaxPooling drastically reduces dimensions before classification

### Challenge 4: Phase Noise
- **Problem**: WiFi phase measurements are inherently noisy
- **Impact**: Phase features may mislead rather than help the model
- **Why it happens**: Clock synchronization issues, hardware imperfections, temperature variations
- **Mitigation**: Combining phase with more stable amplitude features, BatchNormalization

### Challenge 5: 276 Classes
- **Problem**: Very large number of classes with thin decision boundaries
- **Impact**: Random chance is only 0.36% — the model must learn very specific patterns
- **Mitigation**: Using softmax with full 276-way classification, L2 regularization

---

## 5. Preprocessing Pipeline

```
Step 1: Load raw CSI data (complex-valued)
            Shape: (200, 30, 3, N) from MATLAB
            
Step 2: Transpose to sample-first format
            Shape: (N, 200, 30, 3)
            
Step 3: Extract Amplitude: |z| = np.abs(csi)
            Shape: (N, 200, 30, 3)
            
Step 4: Extract Phase: ∠z = np.angle(csi)
            Shape: (N, 200, 30, 3)
            
Step 5: Concatenate [amplitude, phase] along last axis
            Shape: (N, 200, 30, 6)    ← 3 amp + 3 phase channels
            
Step 6: Convert labels from 1-indexed to 0-indexed
            y = labels - 1
            
Step 7: Stratified train/test split (80/20)
            X_train, X_test, y_train, y_test
```

### Why No Normalization?
- The model includes **BatchNormalization** which normalizes activations internally
- Raw values preserve the natural scale relationships between subcarriers
- Normalization can be added per-sample or per-channel in future iterations

---

## 6. CNN Model Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: (200, 30, 6)                       │
│         200 subcarriers × 30 antennas × 6 features          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            Conv2D(4 filters, 4×4 kernel, valid)              │
│                   Output: (197, 27, 4)                       │
│  Learns 4 local spatial patterns in the CSI grid             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  BatchNormalization                           │
│                   Output: (197, 27, 4)                        │
│  Normalizes activations for stable, faster training          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   ReLU Activation                            │
│                   Output: (197, 27, 4)                        │
│  Non-linearity: f(x) = max(0, x)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│             MaxPooling2D(4×4, stride 4)                      │
│                   Output: (49, 6, 4)                         │
│  16× dimensionality reduction, keeps strongest features      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                      Flatten                                 │
│                   Output: (1176,)                             │
│  Reshape for dense layer input                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│          Dense(276, softmax, L2 regularization)              │
│                   Output: (276,)                              │
│  Final classification into 276 gesture classes               │
└─────────────────────────────────────────────────────────────┘
```

### Layer-by-Layer Justification

#### Layer 1: Conv2D(4 filters, 4×4 kernel, 'valid' padding)
- **4 filters**: Intentionally small to prevent overfitting. With only ~20 samples per class, more filters would memorize the training data rather than learn general patterns.
- **4×4 kernel**: Captures correlations between 4 neighboring subcarriers (frequency domain) and 4 neighboring antennas (spatial domain). This is the fundamental "feature detector" — it looks for local signal patterns that indicate specific hand positions.
- **'valid' padding**: No zero-padding means the output shrinks slightly (200→197, 30→27). This avoids introducing artificial edge effects.
- **Parameter count**: 4 filters × (4×4 kernel × 6 input channels) + 4 biases = 388

#### Layer 2: BatchNormalization
- **What**: Normalizes activations to zero mean, unit variance per feature map
- **Why**: Without BatchNorm, gradient magnitudes can vary wildly across layers, leading to unstable training. Especially important in shallow networks where each layer must work well.
- **Parameters**: 16 (4 gamma + 4 beta trainable, 4 mean + 4 variance tracked)

#### Layer 3: ReLU Activation
- **What**: `f(x) = max(0, x)` — zeroes out negative values
- **Why ReLU over Sigmoid/Tanh**: ReLU doesn't suffer from vanishing gradients, is computationally cheap, and promotes sparse representations.
- **Parameters**: 0

#### Layer 4: MaxPooling2D(4×4, stride 4)
- **What**: Takes the maximum value in each non-overlapping 4×4 window
- **Why MaxPooling**: 
  - **Dimensionality reduction**: Input (197, 27, 4) → Output (49, 6, 4) — 16× fewer values
  - **Feature selection**: Max operation keeps the strongest/most important activations
  - **Translation invariance**: The exact position of a pattern in the 4×4 window doesn't matter
  - **Why not Average Pooling?**: In CSI, peak signal values are more informative than averages. Averaging would dilute strong signal features.
- **Why 4×4 stride?**: Our correlation analysis shows adjacent CSI values are highly correlated. 4×4 pooling exploits this redundancy without losing important information.
- **Parameters**: 0

#### Layer 5: Flatten
- **What**: Reshapes 3D tensor (49, 6, 4) → 1D vector (1,176)
- **Why**: Dense layers require 1D input
- **Parameters**: 0

#### Layer 6: Dense(276, softmax, L2=0.01)
- **276 units**: One output per gesture class
- **softmax**: Converts raw logits to probability distribution (all outputs sum to 1.0)
- **L2 regularization**: Adds `λ × Σ(w²)` to the loss function, penalizing large weights. This is critical because:
  - The 1176→276 connection has 324,252 parameters
  - With only ~4,400 training samples, this layer could easily overfit
  - L2 forces the model to spread weight importance across features rather than relying on a few
- **Parameter count**: 1176 × 276 + 276 = 324,852

### Why This Architecture (and Not Deeper)?

| Consideration | Observation |
|---------------|-------------|
| **Data size** | ~5,520 samples for 276 classes = ~20 per class. Deeper networks need 100x more data. |
| **Overfitting risk** | With limited data, every additional layer multiplies the risk of overfitting. |
| **CSI simplicity** | CSI patterns are relatively simple compared to natural images. One conv layer is sufficient to extract meaningful features. |
| **SignFi paper** | The original research paper recommends this shallow architecture for the lab dataset. |
| **Computational efficiency** | ~325K total parameters trains in minutes, enabling hyperparameter tuning. |

---

## 7. Hyperparameter Tuning

### Method: RandomizedSearchCV
- **Why not GridSearch?**: Full grid of 5 hyperparameters would require thousands of fits
- **Why not Bayesian Optimization?**: Overkill for this problem, RandomSearch is simpler and effective
- **Settings**: `n_iter=10, cv=3` → 30 total model fits

### Search Space

| Hyperparameter | Range | Distribution | Rationale |
|----------------|-------|--------------|-----------|
| Learning Rate | 0.001 — 0.1 | Uniform | Too low = slow convergence; too high = unstable training |
| Momentum | 0.5 — 0.99 | Uniform | Higher momentum accelerates training but can overshoot |
| L2 Regularization | 0.001 — 0.05 | Uniform | Too low = overfitting; too high = underfitting |
| Batch Size | 32, 64, 128 | Discrete | Larger batches = more stable gradients but less generalization |
| Epochs | 10, 15, 20, 25 | Discrete | More epochs = more training but risk of overfitting |

### Optimizer: SGD with Momentum
- **Why SGD over Adam?**: 
  - SGD with momentum generalizes better than Adam on small datasets (well-documented in literature)
  - Fewer internal variables = less memory overhead
  - More predictable learning dynamics
  - The momentum parameter gives us an additional tunable hyperparameter

---

## 8. Training Configuration

### Final Model Training
- **Optimizer**: SGD with best learning rate and momentum from tuning
- **Loss Function**: Sparse Categorical Crossentropy (integer labels, 276 classes)
- **Callbacks**:
  - **EarlyStopping**: Monitors `val_loss`, patience=5, restores best weights
  - **ReduceLROnPlateau**: Halves learning rate if `val_loss` stalls for 3 epochs
- **Data Split**: 80% train, 20% test (stratified by class)

### Why These Callbacks?
- **EarlyStopping**: Prevents the model from training past the point where validation loss stops improving. Without it, the model would memorize the training data.
- **ReduceLROnPlateau**: When the model stops improving, reducing the learning rate allows for finer-grained weight updates. Like shifting to a lower gear when climbing a hill.

---

## 9. Evaluation Metrics

### Metrics Computed
1. **Test Accuracy**: Overall classification accuracy on held-out test data
2. **Top-5 Accuracy**: Whether the correct class is in the top 5 predictions (useful for 276-class problems)
3. **Per-Class Accuracy**: Which gestures are easiest/hardest to recognize
4. **Confusion Matrix**: Which classes are most commonly confused
5. **Training Curves**: Accuracy and loss over epochs (for overfitting analysis)

### Overfitting Assessment
- **Train-Validation accuracy gap > 15%**: Significant overfitting → need more regularization
- **Gap 5-15%**: Mild overfitting → acceptable
- **Gap < 5%**: Good generalization

---

## 10. Generated Files Reference

| File | Format | Purpose |
|------|--------|---------|
| `SignFi-CNN.ipynb` | Jupyter Notebook | Complete analysis and model training notebook |
| `SignFi_Data_Report.html` | HTML | Interactive data report (open in browser for presenting) |
| `class_statistics.csv` | CSV | Per-class amplitude statistics for all 276 classes |
| `hyperparameter_results.csv` | CSV | All hyperparameter tuning results ranked by accuracy |
| `class_distribution.png` | Image | Class distribution bar chart |
| `amplitude_heatmaps.png` | Image | CSI amplitude heatmaps for 6 gesture classes |
| `phase_heatmaps.png` | Image | CSI phase heatmaps for 6 gesture classes |
| `signal_traces.png` | Image | 1D amplitude signals across subcarriers |
| `multi_class_comparison.png` | Image | 12-class side-by-side CSI comparison |
| `antenna_correlation.png` | Image | 30×30 antenna correlation matrix |
| `inter_class_similarity.png` | Image | 276×276 inter-class cosine similarity |
| `channel_correlation.png` | Image | 3×3 cross-channel correlation |
| `similarity_challenge.png` | Image | Most/least similar class pair comparison |
| `intra_class_variance.png` | Image | Per-class variance analysis |
| `hyperparameter_effects.png` | Image | Hyperparameter effects on accuracy |
| `training_curves.png` | Image | Final model training accuracy & loss |
| `confusion_matrix.png` | Image | Confusion matrix + per-class accuracy |

---

## 11. Key Takeaways

1. **WiFi CSI is a viable modality** for sign language recognition — no cameras needed
2. **The data challenge is inter-class similarity** — many gestures produce very similar CSI patterns
3. **Shallow CNNs are appropriate** when data is limited (~20 samples per class)
4. **Both amplitude and phase matter** — amplitude is more stable, phase adds sensitivity
5. **Regularization is critical** — L2, BatchNorm, and early stopping all combat overfitting
6. **Hyperparameter tuning matters** — even small changes in learning rate can significantly impact accuracy
7. **MaxPooling 4×4 is effective** because CSI values are locally correlated (confirmed by correlation analysis)
8. **MIMO antennas provide spatial diversity** — antennas within and across receivers capture different aspects of gestures

---

*Report generated as part of the SignFi-CNN comprehensive analysis notebook.*
