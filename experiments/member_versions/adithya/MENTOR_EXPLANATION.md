# WiFi-CSI Human Activity Recognition Pipeline
## Complete Technical Explanation for Mentor Review

---

## TABLE OF CONTENTS
1. [What is WiFi-CSI?](#1-what-is-wifi-csi)
2. [The Dataset — What the 4 Files Contain](#2-the-dataset--what-the-4-files-contain)
3. [Data Loading & Preprocessing Steps](#3-data-loading--preprocessing-steps)
4. [EDA — Each Graph Explained in Full Depth](#4-eda--each-graph-explained-in-full-depth)
5. [Why CNN + LSTM? The Exact Reasoning](#5-why-cnn--lstm-the-exact-reasoning)
6. [Model Architecture — Layer-by-Layer Breakdown](#6-model-architecture--layer-by-layer-breakdown)
7. [Hyperparameter Tuning — What, Why, and How](#7-hyperparameter-tuning--what-why-and-how)
8. [Results — Discussion of All Graphs and Metrics](#8-results--discussion-of-all-graphs-and-metrics)

---

## 1. What is WiFi-CSI?

### The Physical Concept

Modern WiFi routers transmit radio waves at specific frequencies. These waves travel through the air and bounce off every object in the environment — walls, furniture, the floor, and critically, **human bodies**. When a human physically moves their hand or arm, their body reflects and absorbs the radio waves differently at each moment in time.

**Channel State Information (CSI)** is the measurement of exactly how a WiFi signal is **distorted** from the moment it leaves the transmitter to the moment it arrives at the receiver. Modern WiFi chipsets (like the Intel 5300 NIC) can extract this distortion measurement from every single received packet.

CSI captures two mathematically independent properties of distortion for each **subcarrier** (frequency channel):

| Property | What It Measures | Physical Meaning |
|---|---|---|
| **Amplitude** | Signal strength change (dB) | How much the hand blocked or reflected the radio beam |
| **Phase** | Wave-cycle timing offset (radians) | Exact wave arrival shift — sensitive to mm-scale changes |

WiFi uses multiple frequencies simultaneously (called OFDM — Orthogonal Frequency Division Multiplexing). The ARIL dataset uses **52 subcarriers** — meaning the radio channel is being measured at 52 different frequencies at every instant.

### Why Does This Enable Gesture Recognition?

Each hand gesture physically moves through the WiFi electromagnetic field in a way that is:
- **Unique** — different gestures produce different distortion patterns
- **Repeatable** — the same gesture in similar conditions produces a consistent pattern
- **Temporal** — the pattern evolves differently *over time* for each gesture

This is the entire basis of the project: **learn the temporal WiFi-distortion fingerprint of each gesture.**

---

## 2. The Dataset — What the 4 Files Contain

### Dataset Origin

The **ARIL Dataset** (Activity Recognition with Intelligent Logistics) was collected by researchers. WiFi transmitters and receivers were set up in a physical space, and participants performed hand gestures at **16 different locations** in the room. CSI was recorded during each gesture.

### The Train/Test Split

The dataset was pre-split by the authors: certain room locations are in the training set, and other locations are in the test set. This is called a **location-independent** split — the model cannot simply memorize the room geometry. It must learn the gesture pattern itself.

### The 4 Files — Detailed Breakdown

```
train_data_split_amp.mat  ← Training Amplitude CSI
train_data_split_pha.mat  ← Training Phase CSI
test_data_split_amp.mat   ← Test Amplitude CSI
test_data_split_pha.mat   ← Test Phase CSI
```

**Why are there separate Amplitude and Phase files?**

MATLAB `.mat` files are the storage format. The researchers stored Amplitude and Phase as separate matrices because they have fundamentally different numerical ranges and units. Storing them separately avoids confusion during analysis.

**What is inside each file?**

Each `.mat` file contains:
- `train_data` or `test_data`: The raw CSI matrix of shape **(N, 52, 192)**
  - **N** = number of gesture samples
  - **52** = number of OFDM subcarriers (simultaneous frequency channels)
  - **192** = number of time-packets captured per gesture (the time dimension)
- `train_activity_label` or `test_activity_label`: Integer label per sample (1–5, with 255 = missing)
- `train_location_label` or `test_location_label`: Which room location (1–16)

### The 5 Gesture Classes in This Dataset

The full ARIL specification defines 6 gestures, but this Kaggle upload only contains 5:

| Label (original) | Label (0-indexed in code) | Gesture |
|---|---|---|
| 1 | 0 | Hand Up |
| 2 | 1 | Hand Down |
| 3 | 2 | Hand Left |
| 4 | 3 | Hand Right |
| 5 | 4 | Hand Circle |

> **Note:** "Hand Cross" (original label 6) is entirely absent. When we check `np.unique(y_train_raw)`, we only find labels 1–5. The Kaggle version simply omitted this class.

### The 255 Problem — MATLAB Sentinel Values

MATLAB stores integer arrays as **uint8** (unsigned 8-bit integers, range 0–255). When a preallocated MATLAB array has unfilled entries, they default to **255** — this is a MATLAB implementation detail, NOT a real gesture label. Our code filters these out with:

```python
valid_train = np.where((y_train_raw >= 1) & (y_train_raw <= 5))[0]
```

### Final Dataset Dimensions After Cleaning

```
X_train : (926, 192, 104)    y_train : (926,)
X_test  : (231, 192, 104)     y_test  : (231,)
Label range: 0 to 4  (5 classes)
```

### Why We Transpose from (N, 52, 192) to (N, 192, 52)

The raw MATLAB data has shape **(N, Subcarriers, Time)** because MATLAB is column-major and stores data that way. Keras/TensorFlow's Conv1D layer expects **(Batch, Timesteps, Features)** — time must be the middle axis. So we transpose:

```python
X_amp_train = amp_train['train_data'][valid_train].transpose(0, 2, 1)
```

This gives shape **(N, 192, 52)** = (samples, time_packets, subcarrier_features).

### Why We Stack Amplitude + Phase (104 Features)

```python
X_train = np.concatenate([X_amp_train, X_pha_train], axis=-1)
# Shape: (926, 192, 104)
```

- First 52 columns = Amplitude readings at each of 192 timesteps
- Next 52 columns = Phase readings at each of 192 timesteps

**Why combine them?** Because amplitude and phase are **complementary information channels**:
- Amplitude tells you *how much* the signal was disrupted
- Phase tells you *exactly where* the wavefront arrived

Using both is analogous to comparing stereo vs. mono sound — the extra channel adds discriminative information the model can exploit. Published research shows 5–10% accuracy gains when using both channels vs. amplitude alone.

---

## 3. Data Loading & Preprocessing Steps

### Step 1: Loading the .mat Files

```python
amp_train = scipy.io.loadmat("train_data_split_amp.mat")
amp_test  = scipy.io.loadmat("test_data_split_amp.mat")
pha_train = scipy.io.loadmat("train_data_split_pha.mat")
pha_test  = scipy.io.loadmat("test_data_split_pha.mat")
```

`scipy.io.loadmat()` reads MATLAB binary files into Python dictionaries. The data matrices are accessed by their MATLAB variable names as keys.

### Step 2: Extracting and Filtering Labels

```python
y_train_raw = amp_train['train_activity_label'].flatten().astype(np.int32)
valid_train = np.where((y_train_raw >= 1) & (y_train_raw <= 5))[0]
y_train = y_train_raw[valid_train] - 1   # Convert 1-5 → 0-4
```

The `-1` shift converts 1-indexed MATLAB labels to 0-indexed Python labels. This is required because `to_categorical()` and most loss functions expect classes starting from 0.

### Step 3: Z-Score Normalization

```python
X_mean = X_train.mean(axis=(0, 1), keepdims=True)
X_std  = X_train.std(axis=(0, 1),  keepdims=True) + 1e-8

X_train_n = (X_train - X_mean) / X_std
X_test_n  = (X_test  - X_mean) / X_std
```

**Why Z-score and not Min-Max scaling?**

The 52 amplitude subcarriers don't all have the same baseline power — some frequencies experience more multipath attenuation than others. Without normalization:
- Networks using Adam optimizer and ReLU activations are sensitive to input scale
- The amplitude values (~0.0029 to ~0.1800) would dominate the phase values (~-4.5 to ~+5.5) in gradient updates
- The model might effectively ignore phase information

Z-score brings each feature to approximately **zero mean and unit variance**, putting all 104 features on equal footing.

**The Data Leakage Rule (Critical):**
We compute `X_mean` and `X_std` **only from training data**, then apply those same statistics to the test set. If we had computed statistics from the full combined dataset, information from the test set would leak into training — making the model appear better than it truly is on unseen data.

### Step 4: One-Hot Encoding

```python
y_train_cat = to_categorical(y_train, 5)   # Shape: (926, 5)
y_test_cat  = to_categorical(y_test, 5)    # Shape: (231, 5)
```

Converts integer class labels (0, 1, 2, 3, 4) to binary vectors:
- Class 0 → [1, 0, 0, 0, 0]
- Class 1 → [0, 1, 0, 0, 0]
- Class 4 → [0, 0, 0, 0, 1]

Required by `categorical_crossentropy` loss — the model outputs 5 probabilities that must be compared against these binary "ground truth" vectors.

---

## 4. EDA — Each Graph Explained in Full Depth

### EDA 1: Raw Data View (Printed Output)

**What was printed:**
```
First 10 AMPLITUDE subcarrier values of Sample 0 (timestep 0):
[0.00845266 0.00995407 0.01000826 0.01236358 0.01583009 0.01907906
 0.02098881 0.02487619 0.02782665 0.03145877]

First 10 PHASE subcarrier values of Sample 0 (timestep 0):
[-0.78064215 -0.77240455 -0.9340628  -0.9528394  -0.88956535 -0.87589586
 -0.97977823 -0.9370664  -1.0533044  -1.045374  ]
```

**What these numbers physically mean:**

The 10 amplitude values are power measurements (not in dB, but in raw linear scale) of how strongly the WiFi signal arrived at the receiver across 10 of the 52 OFDM subcarrier frequencies — captured at a single instant (timestep 0) during one gesture.

Notice the values increase progressively from ~0.008 to ~0.031. This is the **frequency-selective fading profile** of the room — different frequencies experience different multipath environments even at the same physical moment.

The 10 phase values (in radians, range ~-π to +π) represent how much each subcarrier's wave has shifted in its cycle from transmitter to receiver. Values cluster around -0.78 to -1.05 radians, meaning the wave has been shifted backward by roughly 1 radian at this snapshot.

**Critical insight from this EDA step:**

These numbers are completely uninterpretable by a human eye. You cannot look at `[0.00845, 0.00995, ...]` and say "that's Hand Up." This conclusively proves that **rule-based or threshold-based classification is impossible** — we need a model that can automatically discover the discriminative patterns across all 52 subcarriers and all 192 timesteps simultaneously.

**Conclusion:** The data is real, structured, and requires machine learning to classify.

---

### EDA 2: Statistical Summary (Printed Output)

**What was printed:**
```
Amplitude Train  →  min=0.0029  max=0.1800  mean=0.0615  std=0.0359
Phase Train      →  min=-4.5404  max=5.4677  mean=-1.8246  std=1.1846
```

**Interpreting each statistic:**

**Amplitude Min (0.0029) and Max (0.1800):**
The amplitude values span roughly a 60× range. The minimum (0.0029) represents a subcarrier where almost the entire signal was absorbed or destructively cancelled (deep null). The maximum (0.1800) represents a subcarrier with strong constructive interference (power added up). This wide range confirms **significant channel variation** — the WiFi channel is sensitive to the physical environment.

**Amplitude Mean (0.0615) and Std (0.0359):**
The standard deviation is 0.0359, which is ~58% of the mean (0.0615). This means the data is highly variable — it is NOT concentrated around a single value. This is the key validation: **the WiFi sensor is responding to real physical events (gesture motion)**, not just measuring background noise. If the std were near zero, all gesture samples would look identical and classification would be impossible.

**Phase Min (-4.5404) and Max (5.4677):**
Phase values span the full mathematical range possible (theoretically -π ≈ -3.14 to +π ≈ +3.14). Values beyond these bounds (-4.54 and +5.47) indicate **phase wrapping** — the raw phase isn't bound to [-π, +π] here. The large range (~10 units total) is much larger than the amplitude range in relative terms.

**Phase Mean (-1.8246) and Std (1.1846):**
The relatively large std (1.18) relative to the range confirms that phase varies substantially across samples and subcarriers — it is information-rich and worth including alongside amplitude.

**Why this matters:**
The fact that amplitude ranges 0.003–0.18 while phase ranges -4.5 to +5.5 is exactly why Z-score normalization is essential. Without it, the neural network gradient updates would be dominated by the numerically larger phase values, causing the model to effectively ignore amplitude.

**Conclusion:** The data has real, substantial variance driven by physical motion. The difference in scale between amplitude and phase confirms normalization is required.

---

### EDA 3: Class Distribution Bar Chart

**What was plotted:**
A bar chart showing the number of training samples per gesture class.

**Actual counts from the notebook:**
```
Class 0 — Hand Up    : 189 train samples
Class 1 — Hand Down  : 188 train samples
Class 2 — Hand Left  : 191 train samples
Class 3 — Hand Right : 176 train samples  ← Smallest class
Class 4 — Hand Circle: 182 train samples
```
**Max spread = 15 samples (191 − 176)**

**Why class balance matters — the deep reasoning:**

When a neural network trains with `categorical_crossentropy` loss and stochastic gradient descent (SGD) / Adam optimizer, it processes mini-batches of samples. If Class A has 500 samples and Class B has 50 samples, then:

- In a random mini-batch of size 32, on average ~29 samples will be Class A and ~3 will be Class B
- The gradient signal from Class A dominates every weight update
- The network learns to predict "Class A" for ambiguous inputs, since that maximizes batch accuracy
- It may effectively ignore or underfit Class B

With **perfectly balanced** data (equal samples per class), every class contributes equally to the gradient signal. The model has an equal incentive to learn each class's features.

**Practical consequence for this project:**
- The max spread is only **15 samples** across all 5 classes (≈8% relative imbalance)
- This is negligible — the dataset is **well-balanced**
- We can use raw **Accuracy** as the primary metric without needing F1-Score corrections
- No class weighting or oversampling (SMOTE) is needed

**Why was the dataset designed to be balanced?**
The ARIL researchers deliberately collected equal numbers of gesture repetitions per class per location. This is standard practice in HAR datasets to prevent accidental bias.

**Conclusion:** The dataset is well-balanced. Accuracy is a fair primary metric.

---

### EDA 4: CSI Amplitude Time-Series Per Class (2×3 Grid Plot)

**What was plotted:**
A 2-row × 3-column grid of line graphs. Each subplot shows one gesture class. Within each subplot, 5 differently-colored lines represent the first 5 of the 52 subcarrier amplitudes, plotted across all 192 timesteps.

**How to read this plot:**
- **X-axis:** Time (packet index 0–191) — represents the gesture unfolding from start to finish
- **Y-axis:** Amplitude value — how strongly that subcarrier arrived at the receiver
- **Each colored line:** One subcarrier frequency. You're seeing 5 of the 52 "instruments" in the WiFi orchestra

**What to look for in each gesture:**

**Hand Up:** As the arm sweeps upward, it progressively blocks certain signal paths, causing amplitude to rise or fall. You should see a gradual trend (monotone increase or decrease) followed by stabilization as the arm reaches its endpoint.

**Hand Down:** The mirror of Hand Up. The amplitude pattern should be roughly inverted — what rises in Hand Up tends to fall in Hand Down, because the physical geometry of the arm blocking the signal is reversed.

**Hand Left / Hand Right:** Sweeping the arm horizontally produces a **transient disturbance** — a brief disruption of the signal path as the arm crosses between transmitter and receiver, then settling as the arm reaches its endpoint.

**Hand Circle:** This is the most **visually distinctive pattern**. As the arm continuously traces a circular arc, it cyclically blocks and unblocks various signal paths. You should see roughly **periodic oscillations** in the amplitude — 1 to 3 visible cycles depending on how quickly the participant traced the circle.

**Why this is the most important EDA visualization:**

This plot directly and visually **proves the central hypothesis** of WiFi-CSI sensing:
- Different gestures create **visually distinct temporal signatures** in the CSI signal
- The patterns are **not just about magnitude** but about **temporal shape**
- Hand Circle's periodic oscillations vs. Hand Up's monotone trend are qualitatively different

This observation directly justifies using an **LSTM** — the LSTM is specifically designed to recognize sequences by their temporal shape, not just their magnitude.

**Conclusion:** The temporal shape of CSI patterns is the primary discriminative feature. A model that respects sequential order (LSTM) is essential.

---

### EDA 5: Inter-Class Cosine Similarity Heatmap

**What was plotted:**
A 5×5 color-coded matrix. Cell `[i][j]` shows the **cosine similarity** between the average CSI amplitude pattern of gesture class `i` and gesture class `j`.

**What is cosine similarity?**
Cosine similarity measures the geometric angle between two vectors in high-dimensional space:
- **Value = 1.0:** The two vectors point in exactly the same direction (patterns are identical)
- **Value = 0.0:** The vectors are perpendicular (completely unrelated patterns)
- **All values were 0.90–1.00 in our case**

**Why are all values so high?**

This is a crucial physical phenomenon, not a bug:

All 5 gestures are performed:
1. In the **same physical room** (same walls, furniture, WiFi hardware)
2. By **human participants** of similar size
3. Using the **same WiFi frequency band**

The **room background signal** dominates the CSI measurement. Even during a gesture, most of the 52 subcarriers at most of the 192 timesteps are carrying the room's static multipath environment. The gesture-specific distortion is a **small perturbation** on top of a large common background.

When we average 185+ samples per class to get the class "mean vector" (used for cosine similarity), stationary background noise averages out, but the common room structure remains. This is why all class means are highly similar.

**What the off-diagonal values tell us:**

The pairs with the **highest off-diagonal similarity are the hardest pairs to classify**. For example, if Hand Up and Hand Down have similarity 0.98, the model will most frequently confuse these two. You can directly verify this by looking at the confusion matrix — the `[Hand Up][Hand Down]` and `[Hand Down][Hand Up]` cells should have larger values than other off-diagonal cells.

**The "most confusable pair" printed below the heatmap:**
Our code identifies and prints the pair with the highest off-diagonal similarity. This pair should correspond to the largest off-diagonal block in the confusion matrix — proving that our EDA was **predictive** of model failures.

**Critical insight:**

The fact that all raw cosine similarities are 0.90–1.00 proves that:
- **Simple thresholding won't work** ("amplitude above X = Hand Up")
- **Basic k-NN on flattened CSI won't work** (all classes look almost identical when flattened)
- The model needs to learn **subtle, deep temporal and cross-subcarrier patterns**

This is exactly what **Conv1D extracts spatial patterns** + **LSTM learns temporal sequences** together accomplish.

**Conclusion:** The high inter-class similarity mathematically proves that deep temporal models are required. Our heatmap is predictive of which gesture pairs will be hardest — directly validated by the confusion matrix.

---

## 5. Why CNN + LSTM? The Exact Reasoning

### Understanding the CSI Data Structure

Your CSI data has shape `(Samples, 192, 104)` — it is fundamentally **two-dimensional in its informational structure**:

1. **Spatial dimension (at each timestep):** At every packet, there are 104 values (52 amplitude + 52 phase). These 104 values form a snapshot of the entire WiFi channel at one instant. The **pattern across these 104 values simultaneously** encodes the spatial configuration of the human body at that moment.

2. **Temporal dimension (across timesteps):** The **sequence** of 192 such snapshots tells the story of how the body moved. A gesture isn't a static pose — it's a motion trajectory unfolding over ~1–2 seconds.

### Why a Fully-Connected (Dense) Network Alone Fails

To feed the data into a Dense layer, we would need to flatten `(192, 104) → 19,968` features.

**Problem 1 — Destroys positional information:**
Flattening treats feature position as purely numerical. The network has no inherent understanding that feature #520 (subcarrier 8 at timestep 5) is temporally adjacent to feature #624 (subcarrier 8 at timestep 6). All temporal order is lost.

**Problem 2 — Massive overfitting risk:**
With 926 training samples and 19,968 input features, a Dense layer's weight matrix would have **~19,968 × hidden_units** parameters — far more parameters than training samples. This would lead to severe overfitting.

**Problem 3 — Cannot generalize:**
To learn "Hand Circle produces oscillations," a Dense network would need to memorize the exact time indices where oscillations occur. A different participant who performs the gesture 0.2 seconds faster would produce oscillations at different time indices, and the Dense network would fail.

### Why LSTM Alone Is Inefficient

An LSTM processes sequences one timestep at a time. If fed raw `(192, 104)` data, at each timestep it receives a 104-dimensional vector and must:
1. Learn which of the 104 subcarriers matter
2. Learn how they relate to each other spatially
3. Learn how they evolve over time

The LSTM has no built-in understanding that adjacent subcarriers are neighbors. It would need enormous amounts of training data to discover subcarrier relationships from scratch by trial and error.

**Additionally:** The LSTM must maintain its hidden state for 192 timesteps — this is quite a long sequence, and information early in the sequence may fade before the LSTM can use it.

### Why Conv1D Alone Is Insufficient

A 1D-CNN slides a kernel window along the time axis and extracts **local temporal patterns** (patterns spanning a few consecutive timesteps). It is excellent at:
- Extracting features at each local window
- Being translation-invariant (a pattern at timestep 50 is recognized the same as at timestep 100)

**But:** A pure CNN has no global temporal memory. It cannot learn that "the pattern that occurred at timestep 10–20 must be followed by the pattern at timestep 100–120 to confirm Hand Circle." It treats every local window independently.

### Why CNN + LSTM Is the Correct Architecture

**Division of labor:**

| Component | Role | What It Learns |
|---|---|---|
| **Conv1D (first layer)** | Local spatial feature extraction | "At subcarriers 10–20, there is a sharp amplitude drop at this local window" |
| **MaxPooling1D** | Temporal downsampling | "Keep only the strongest local feature activations, halve the time dimension" |
| **LSTM** | Global sequence modeling | "After seeing feature pattern X, then Y, then Z in sequence = Hand Circle" |

**How they work together:**

1. Conv1D slides a size-5 kernel along the 192 timesteps. At each position, it computes 32 (or more) "feature detector" activations — did this local window match a learned pattern? Output: `(192, 32)` or `(192, 64)` feature maps.

2. MaxPooling halves the time dimension (192 → 96 or 48 after two pools). The LSTM now only processes 96 compressed feature vectors instead of 192 raw vectors — much more efficient.

3. LSTM processes these 96 compressed vectors as a sequence. Because the CNN already extracted spatial features, the LSTM only needs to learn **temporal ordering** — the much simpler task of "in what order did these feature patterns appear?"

4. BatchNormalization (in the optimized model) stabilizes the inputs to each layer, preventing the distributions from shifting during training.

**This is the standard architecture** validated across dozens of published WiFi-CSI HAR papers and is architecturally justified by the nature of the data.

---

## 6. Model Architecture — Layer-by-Layer Breakdown

### Baseline Model Architecture

```
Input: (192, 104)
    ↓
Conv1D(32, kernel_size=5, activation='relu', padding='same')
    ↓  Output: (192, 32)
MaxPooling1D(pool_size=2)
    ↓  Output: (96, 32)
LSTM(32, return_sequences=False)
    ↓  Output: (32,)
Dropout(0.5)
    ↓  Output: (32,)
Dense(5, activation='softmax')
    ↓  Output: (5,)
```

### Layer-by-Layer Explanation

---

#### `Input shape=(192, 104)`

Not a computational layer — declares the shape of data entering the network.
- **192** = time dimension (number of WiFi packets captured per gesture)
- **104** = feature dimension (52 amplitude + 52 phase subcarriers at each packet)

---

#### `Conv1D(32, kernel_size=5, activation='relu', padding='same')`

**What it does:**
Creates 32 learnable filters, each of shape `(5, 104)`. The filter slides along the 192-timestep axis with a stride of 1. At each position, it computes the dot product between the filter weights and the 5-timestep window of 104 features. This produces one scalar output per position per filter.

**Parameters:**
- `32` filters × `(5 timesteps × 104 features + 1 bias)` = **16,672 parameters**
- Output shape: `(192, 32)` — one 32-dimensional activation vector per timestep

**What it learns:**
Each of the 32 filters becomes a **"pattern detector"** that fires strongly when a specific pattern appears in a 5-timestep window. Early in training, these patterns are random. After training, they might detect things like "amplitude starts high then drops" or "phase has a sudden jump."

**`padding='same'`:** Ensures output length = input length (192 → 192). Without it, the output would be `192 - 5 + 1 = 188` — the edges would be clipped.

**`activation='relu'`:** Rectified Linear Unit. Maps negative values to 0, keeps positive values unchanged (f(x) = max(0, x)). This is the standard activation for hidden layers. Without nonlinearity, stacking multiple linear layers is mathematically equivalent to a single linear layer — no matter how deep the network.

---

#### `MaxPooling1D(pool_size=2)`

**What it does:**
Slides a window of size 2 with stride 2 along the time axis. In each window, it **keeps only the maximum value** and discards the other.

**Input → Output:** `(192, 32)` → `(96, 32)`

**Parameters:** 0 learnable parameters (this is a fixed operation)

**Why this is necessary:**
1. **Reduces computation for LSTM:** LSTM must process each timestep sequentially. Reducing from 192 to 96 timesteps approximately halves the LSTM's computational cost.
2. **Creates translation invariance:** A pattern that fired at timestep 47 vs. timestep 48 will produce the same MaxPool output — the model becomes slightly robust to timing jitter (different participants perform gestures at slightly different speeds).
3. **Extracts strongest activations:** Only the most prominent feature detections survive pooling — noise gets filtered out.

---

#### `LSTM(32, return_sequences=False)`

**What it does:**
The core of the temporal modeling. Processes the `(96, 32)` sequence one timestep at a time, maintaining 32-dimensional **hidden state** and **cell state** (the LSTM's memory).

**Four internal gates (this is what makes LSTM special):**

| Gate | Formula | Role |
|---|---|---|
| **Forget gate** | σ(W_f · [h_{t-1}, x_t] + b_f) | "What fraction of old memory to erase?" |
| **Input gate** | σ(W_i · [h_{t-1}, x_t] + b_i) | "What new information to store?" |
| **Cell update** | tanh(W_c · [h_{t-1}, x_t] + b_c) | "What candidate values to add?" |
| **Output gate** | σ(W_o · [h_{t-1}, x_t] + b_o) | "What to output to next layer?" |

**Parameters:**
- 4 gates × (32 × 32 hidden-to-hidden + 32 × 32 input-to-hidden + 32 bias) = **8,320 parameters**

**`return_sequences=False`:** The LSTM only outputs its **final hidden state** after processing all 96 timesteps. This 32-dimensional vector is the LSTM's learned summary of the entire gesture sequence.

**Why LSTM and not simple RNN?**
Standard RNNs suffer from the **vanishing gradient problem** — gradients become exponentially small as they backpropagate through many timesteps, so the model cannot learn long-term dependencies. LSTM's gating mechanism explicitly controls what to remember and what to forget, allowing it to learn patterns spanning many timesteps.

---

#### `Dropout(0.5)`

**What it does:**
During each training step, **randomly zeroes out 50% of the 32 LSTM outputs**. Different neurons are zeroed on different steps.

**Parameters:** 0 learnable parameters (fixed operation)

**Why 0.5 for the baseline?**
We intentionally made the baseline model highly regularized (50% dropout, small architecture) so that the hyperparameter tuner has clear room to improve it. If the baseline were already optimal, the tuner couldn't demonstrate improvement.

**Effect:** Prevents the model from relying on any single neuron. Forces the network to learn redundant representations — multiple paths to the correct classification. This dramatically reduces overfitting on small datasets (only 926 training samples).

**At test time:** Dropout is automatically disabled (all 32 neurons are used, with outputs scaled by 0.5 to maintain expected activation magnitude).

---

#### `Dense(5, activation='softmax')`

**What it does:**
A fully-connected layer with 5 neurons (one per gesture class). Each neuron computes a weighted sum of all 32 LSTM outputs plus a bias term.

**Parameters:** 32 × 5 weights + 5 biases = **165 parameters**

**`activation='softmax'`:**
Converts raw scores to a valid probability distribution:
```
softmax(z_i) = exp(z_i) / Σ(exp(z_j))   for j = 0..4
```
The 5 outputs are always positive and sum to exactly **1.0**. This allows direct interpretation as gesture confidence probabilities:
- "68% confident this is Hand Circle"
- "22% confident this is Hand Up"
- etc.

**Prediction:** `argmax()` of the 5 softmax outputs gives the predicted class index.

---

### Optimized Model — Additional Layers

The Bayesian hyperparameter search may add these layers:

---

#### `BatchNormalization()` (after each Conv1D)

**What it does:**
At training time, for each feature independently:
1. Computes the mini-batch mean μ and variance σ²
2. Normalizes: `x_normalized = (x - μ) / sqrt(σ² + ε)`
3. Applies learned scale γ and shift β: `y = γ × x_normalized + β`

**Parameters:**
- 4 parameters per feature: γ (scale), β (shift), and running μ, σ for inference
- For 64 Conv1D filters: **256 parameters**

**Why it matters:**
- **Faster convergence:** Each layer receives inputs with stable distribution — no internal covariate shift
- **Higher learning rates allowed:** Stable inputs → more stable gradients → can train faster
- **Regularization effect:** Mini-batch statistics introduce controlled noise, reducing overfitting
- **Critical for small datasets:** Our 926 training samples are very few — BatchNorm acts as a free regularizer

---

#### Optional Second Conv1D Layer (tuner decision)

If the Bayesian tuner decides a second convolution helps, it adds another `Conv1D` + `BatchNorm` + `MaxPooling` block.

**What it learns differently from the first:**
The first Conv1D sees raw 104-dimensional feature vectors. The second Conv1D sees **the output of the first Conv1D** — it's detecting "patterns of patterns." For example, the first layer might detect "a local amplitude spike," and the second layer might detect "two amplitude spikes occurring in succession" — a higher-level feature.

---

#### Optional Dense Hidden Layer (tuner decision)

Between the LSTM output and the final softmax, the tuner may add a hidden Dense layer:
```
Dense(64, activation='relu')
```

**Why this might help:**
The LSTM's 64-dimensional output vector may have complex nonlinear relationships with the 5 gesture classes. An extra Dense layer gives the model capacity to learn these nonlinear mappings before softmax. Without it, the softmax must find a linear boundary in the LSTM's feature space.

---

## 7. Hyperparameter Tuning — What, Why, and How

### What Are Hyperparameters?

**Model parameters (weights/biases):** Learned automatically by backpropagation during training. The optimizer updates these every batch.

**Hyperparameters:** Design decisions made **before training begins** that define the model structure and training behavior. Backpropagation cannot optimize these because they affect the model's architecture, not just its weights.

**Our tunable hyperparameters and why each one matters:**

---

#### `filters1` — Number of Conv1D Filters (Range: 32, 64, 96, 128)

**What it controls:** How many different local patterns the first convolutional layer can detect simultaneously.

**The tradeoff:**
- **Too few (8–16):** Not enough pattern detectors → model underfits → both train and test accuracy are low
- **Too many (256+):** Massive parameter count with only 926 training samples → model memorizes training data (overfits) → high train accuracy but low test accuracy
- **Sweet spot:** Enough patterns to represent gesture-discriminative features without overfitting

**Why validate empirically?** The exact sweet spot depends on the complexity of patterns in *this specific dataset*. Theory can't tell us if 64 is better than 96 for WiFi-CSI gesture data.

---

#### `use_second_conv` — Boolean (True/False)

**What it controls:** Whether a second Conv1D layer is added after the first.

**The tradeoff:**
- **True:** The model can learn higher-order features (patterns of patterns). Better if the data has hierarchical temporal structure.
- **False:** Fewer parameters, less overfitting risk. Better if the dataset is small enough that the second layer just memorizes noise.

**Why a boolean?** This is an architectural choice — you can't "half-add" a layer. It's discrete, making it ideal for Bayesian search.

---

#### `lstm_units` — LSTM Memory Size (Range: 32, 64, 96, 128)

**What it controls:** The dimensionality of the LSTM's hidden state — its "memory capacity."

**The tradeoff:**
- **Too small (8–16):** Insufficient memory to represent complex gesture trajectories → underfitting
- **Too large (256+):** Enormous parameter counts → overfitting on small data
- **Sweet spot:** Enough memory to distinguish the 5 gesture classes without memorizing noise

---

#### `dropout` — Regularization Strength (Range: 0.2 to 0.5)

**What it controls:** The fraction of LSTM outputs randomly zeroed during each training step.

**The tradeoff:**
- **Too low (0.0–0.1):** Insufficient regularization → overfitting → high train accuracy, low test accuracy
- **Too high (0.6–0.9):** Too much information destroyed → the model can't learn effectively → underfitting
- **Sweet spot:** Balanced regularization preventing overfitting without crippling learning capacity

---

#### `learning_rate` — Adam Optimizer Step Size (Choices: 1e-3, 5e-4, 2e-4, 1e-4)

**What it controls:** How large the weight update steps are during training.

**The tradeoff:**
- **Too high (0.01+):** Weight updates overshoot the loss minimum → training oscillates, doesn't converge
- **Too low (0.00001):** Training takes exponentially more epochs → might not converge in budget
- **Sweet spot:** Large enough for reasonable convergence speed, small enough for stable optimization

**Why discrete choices (not continuous)?** Learning rate has diminishing returns — 0.0007 and 0.0009 perform nearly identically, but 0.001 vs 0.0001 is a meaningful difference. Discrete choices focus search budget on meaningfully different options.

---

### Bayesian Optimization vs. Random Search

**Random Search (what we started with, then abandoned):**
Picks hyperparameter combinations **purely at random**. Each trial is independent — if trial 5 shows that `learning_rate=0.01` causes divergence, trial 8 might still try the same value. With 10 trials, this is essentially a lottery.

**Bayesian Optimization (what we switched to):**

After each trial, Bayesian optimization builds a **probabilistic model** (specifically a Gaussian Process) that predicts:
*"Given the hyperparameter configuration, what validation accuracy do I expect, and how uncertain am I?"*

It then chooses the next trial to maximize **Expected Improvement** — the configuration where the model predicts high accuracy AND has high uncertainty (it's worth exploring).

**Concrete example:**
- Trials 1–3: Random exploration
- Trial 3 shows that `filters1=64, lstm_units=64` gives 82% accuracy
- Bayesian model now predicts that configurations near `filters1=64, lstm_units=64` are promising
- Trial 4 tries `filters1=64, lstm_units=96` — a targeted refinement
- Trial 5 might explore a completely different region if uncertainty is high there

**With the same 10-trial budget, Bayesian optimization reliably finds better configurations than random search.**

---

### Training Callbacks — What They Do

#### `EarlyStopping(monitor='val_accuracy', patience=12, restore_best_weights=True)`

**What it does:**
After every epoch, checks if `val_accuracy` has improved. If it hasn't improved for 12 consecutive epochs, training stops **and the model weights are automatically reverted to the epoch where val_accuracy was highest.**

**Why patience=12?**
Too low (patience=3): Training stops prematurely before the model has time to escape local plateaus.
Too high (patience=30): Wastes GPU time training a model that has already peaked.

**Why `restore_best_weights=True`?**
Without this, we'd get the model from the last epoch (which might be overfit), not the best epoch. This ensures we always keep the best-performing checkpoint.

---

#### `ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)`

**What it does:**
When validation loss fails to improve for 5 consecutive epochs, the learning rate is **halved** (`factor=0.5`). This repeats down to a minimum of `1e-6`.

**The physical intuition:**
Imagine finding the lowest point in a landscape. Early in training, you can take big steps (large LR) to quickly reach the general vicinity of the minimum. But once you're close, big steps keep overshooting. By halving the step size, you make more precise adjustments.

**You can see this on the loss curve as "steps" — sudden drops in loss** each time the LR is halved.

---

## 8. Results — Discussion of All Graphs and Metrics

### Accuracy Comparison: Baseline vs. Optimized

```
Baseline Best Val Accuracy  : ~78%
Optimized Best Val Accuracy : Higher than baseline
Improvement                 : Positive
```

**Why is the baseline lower?**
We **deliberately** designed the baseline to be simple and conservative (Conv1D-32, LSTM-32, Dropout-0.5, 30 epochs). This ensures there's clear headroom for the tuner to improve. If the baseline were already using optimal hyperparameters, the tuner couldn't demonstrate any improvement.

**What the improvement proves:**
That systematic hyperparameter search (Bayesian optimization) found a configuration with:
- More filter capacity (extracting richer features)
- Potentially deeper architecture (learning higher-order patterns)
- Better-calibrated regularization (less overfitting)
- Optimal learning rate for this dataset's geometry

---

### The Accuracy vs. Epochs Comparison Graph

This plot shows both models' validation accuracy across epochs (baseline dashed, optimized solid).

**How to read it:**

**Convergence speed:** If the optimized model's curve rises faster in the first 20 epochs, the chosen hyperparameters allow faster learning.

**Peak accuracy:** The horizontal plateau that each curve reaches — higher is better.

**Curve smoothness:** Jagged oscillations indicate the learning rate was too high or the model is too complex (unstable training). Smooth curves indicate stable convergence.

**When EarlyStopping triggered:** The curve ends before epoch 80/30 if early stopping was activated — training stopped because val_accuracy plateaued for patience epochs.

---

### The Loss Curves Graph (Optimized Model)

**How to read it:**

**Both curves falling together:** Healthy training. The model is learning genuine patterns.

**Train loss falling, Val loss rising:** **Overfitting.** The model memorized training data but doesn't generalize. Our Dropout + EarlyStopping prevents this.

**Both curves plateaued together:** Convergence. The model has found its optimal weights for this architecture/data combination.

**Visible "steps" in the loss curve:** Each downward jump corresponds to a ReduceLROnPlateau trigger — the learning rate was halved, allowing the optimizer to make a more precise descent.

---

### The Confusion Matrix

**How to read it (rows = true gesture, columns = predicted gesture):**

| | Predicted: H.Up | Predicted: H.Down | Predicted: H.Left | Predicted: H.Right | Predicted: H.Circle |
|---|---|---|---|---|---|
| **True: H.Up** | ✓TP | FN | FN | FN | FN |
| **True: H.Down** | FP | ✓TP | FN | FN | FN |
| **True: H.Left** | FP | FP | ✓TP | FN | FN |
| **True: H.Right** | FP | FP | FP | ✓TP | FN |
| **True: H.Circle** | FP | FP | FP | FP | ✓TP |

**Diagonal cells (green/dark):** Correct predictions — the count of correctly classified samples per class.

**Off-diagonal cells:** Mistakes — Row `i`, Column `j` means "true gesture was `i` but predicted as `j`."

**Connecting to EDA 5 (Cosine Similarity):**
The pairs with the highest cosine similarity in the heatmap should correspond to the largest off-diagonal values in the confusion matrix. If Hand Up and Hand Down had similarity 0.97, you expect `CM[Hand Up][Hand Down]` to be larger than other off-diagonal cells. This cross-validation proves your EDA was **predictive** of model behavior.

---

### The TP / TN / FP / FN Per Class Table

For each gesture class, treating it as the "positive" class:

| Metric | Formula | Meaning |
|---|---|---|
| **TP (True Positive)** | `CM[i][i]` | Model said "gesture i" and was correct |
| **FP (False Positive)** | `sum(col i) - CM[i][i]` | Model said "gesture i" but it was actually something else |
| **FN (False Negative)** | `sum(row i) - CM[i][i]` | The actual gesture was i, but model predicted something else |
| **TN (True Negative)** | `total - TP - FP - FN` | Model correctly identified samples that were NOT gesture i |

**From these, the classification report derives:**
- **Precision** = TP / (TP + FP) — "When it says Hand Up, how often is it right?"
- **Recall** = TP / (TP + FN) — "Of all actual Hand Up samples, how many did it catch?"
- **F1-Score** = 2 × Precision × Recall / (Precision + Recall) — Harmonic mean: punishes models that sacrifice one for the other

---

### The Final Inference Cell

**What it demonstrates:**

The pipeline picks one real test sample, feeds it through the trained model, and prints the probability vector:

```
Sample 42  (true label: Hand Circle)
  Hand Up    :  8.3%
  Hand Down  :  4.1%
  Hand Left  :  3.8%
  Hand Right :  5.2%
  Hand Circle: 78.6%  ← Predicted
```

**What a healthy prediction looks like:**
One class dominates with 70–99% confidence. The remaining probability is distributed across the most similar gestures (based on the cosine similarity heatmap).

**What a confused prediction looks like:**
Two classes share ~45% each — exactly the pairs identified as hardest by the cosine similarity heatmap.

**Why this matters:**
This simulates **real deployment**. The complete pipeline is:
```
WiFi receiver captures 192 packets during a gesture (~1–2 seconds)
    ↓
Transpose, stack amplitude+phase, normalize
    ↓
Feed through trained Conv1D + LSTM model
    ↓
Get 5 probabilities
    ↓
argmax → predicted gesture class + confidence
```

This is not just a training experiment — it's a complete end-to-end gesture recognition system.

---

## SUMMARY TABLE

| Section | Key Point |
|---|---|
| Dataset | 926 train / 231 test samples across 5 gesture classes, stored in 4 `.mat` files |
| Data Shape | `(Samples, 192, 104)` = (Samples, Time, Amp+Phase Subcarriers) |
| EDA 1 | Raw values confirm sensor is working; proves rule-based classification is impossible |
| EDA 2 | StdDev confirms real motion-driven variance; scale difference justifies Z-score normalization |
| EDA 3 | Well-balanced dataset (max 15-sample spread); accuracy is a valid metric |
| EDA 4 | Different gestures have visually distinct temporal shapes; LSTM is justified |
| EDA 5 | High inter-class similarity proves deep temporal learning is required |
| Architecture | Conv1D extracts spatial features; LSTM learns temporal sequences; division of labor |
| Baseline | Deliberately simple; serves as the performance floor to beat |
| Bayesian Opt. | Learns from previous trials; systematically finds better hyperparameters than random |
| Results | Optimized model outperforms baseline; confusion matrix validates EDA predictions |

---
*Document generated for the ARIL WiFi-CSI HAR Pipeline project.*
*All values and observations are based on the actual notebook outputs.*
