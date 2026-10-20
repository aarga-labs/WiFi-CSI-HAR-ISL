import nbformat as nbf
import json

nb = nbf.v4.new_notebook()
cells = []

# Section 1
cells.append(nbf.v4.new_markdown_cell("""# ESP32-CSI Fall Detection: Deep Learning Model

**Dataset**: ESP32 CSI Tool Collected Data (Falls vs No Falls)  
**Model**: Convolutional Neural Network (CNN) with Hyperparameter Optimization  

---

## Notebook Sections
1. Setup & Data Loading
2. Data Analysis & Understanding
3. Signal Visualization
4. Preprocessing Pipeline
5. Model Architecture & Fine Tuning
6. Model Training
7. Evaluation & Results
8. Model Export"""))

# Section 1 Setup
cells.append(nbf.v4.new_markdown_cell("## 1. Setup & Data Loading"))
cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import glob
import os
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

plt.rcParams.update({'figure.figsize': (12, 5), 'font.size': 11, 'figure.dpi': 100})
sns.set_theme(style="whitegrid", palette="muted")"""))

cells.append(nbf.v4.new_code_cell("""TIME_STEPS = 100
SUBCARRIERS = 64

csi_columns = [
    "type", "role", "mac", "rssi", "rate", "sig_mode", "mcs", "bandwidth", 
    "smoothing", "not_sounding", "aggregation", "stbc", "fec_coding", "sgi", 
    "noise_floor", "ampdu_cnt", "channel", "secondary_channel", "local_timestamp", 
    "ant", "sig_len", "rx_state", "real_time_set", "real_timestamp", "len", "csi_array"
]"""))

cells.append(nbf.v4.new_code_cell("""def parse_csi_string(csi_str):
    clean_str = str(csi_str).replace('[', '').replace(']', '').strip()
    vals = np.fromstring(clean_str, sep=' ', dtype=float)
    if len(vals) % 2 != 0:
        vals = vals[:-1]
    imag = vals[0::2]
    real = vals[1::2]
    amplitude = np.sqrt(imag**2 + real**2)
    return amplitude"""))

cells.append(nbf.v4.new_code_cell("""X = []
y = []

fall_files = glob.glob('falling_*.csv')

for file in fall_files:
    df = pd.read_csv(file, names=csi_columns, on_bad_lines='skip')
    amplitudes = [parse_csi_string(s) for s in df['csi_array'] if pd.notna(s)]
    if len(amplitudes) == 0:
        continue
    amp_matrix = np.array(amplitudes)
    if len(amp_matrix) > TIME_STEPS:
        amp_matrix = amp_matrix[:TIME_STEPS, :]
    elif len(amp_matrix) < TIME_STEPS:
        padding = np.zeros((TIME_STEPS - len(amp_matrix), amp_matrix.shape[1]))
        amp_matrix = np.vstack((amp_matrix, padding))
    X.append(amp_matrix)
    y.append(1)

if os.path.exists('no_falling.csv'):
    df_nofall = pd.read_csv('no_falling.csv', names=csi_columns, on_bad_lines='skip')
    amplitudes_nofall = [parse_csi_string(s) for s in df_nofall['csi_array'] if pd.notna(s)]
    amp_matrix_nofall = np.array(amplitudes_nofall)
    for i in range(0, len(amp_matrix_nofall) - TIME_STEPS, TIME_STEPS):
        window = amp_matrix_nofall[i : i + TIME_STEPS, :]
        if len(window) == TIME_STEPS:
            X.append(window)
            y.append(0)

X = np.array(X)
y = np.array(y)
X = np.expand_dims(X, axis=-1)"""))

# Section 2 EDA
cells.append(nbf.v4.new_markdown_cell("## 2. Data Analysis & Understanding\n\nDataset Dimensions and Summary Statistics"))

cells.append(nbf.v4.new_code_cell("""total_samples = len(y)
num_falls = sum(y)
num_nofalls = total_samples - num_falls

dims = pd.DataFrame({
    'Property': ['Total Samples', 'Time Steps', 'Subcarriers', 'Classes', 'Fall Samples', 'No-Fall Samples'],
    'Value': [total_samples, TIME_STEPS, SUBCARRIERS, 2, num_falls, num_nofalls]
})
display(dims.style.hide(axis='index'))"""))

cells.append(nbf.v4.new_code_cell("""plt.figure(figsize=(8, 5))
sns.countplot(x=y, palette="viridis")
plt.title("Class Distribution: Fall (1) vs No-Fall (0)", fontsize=14, fontweight='bold')
plt.xlabel("Class", fontsize=12)
plt.ylabel("Count", fontsize=12)
plt.show()"""))

# Section 3 Visualization
cells.append(nbf.v4.new_markdown_cell("## 3. Signal Visualization\n\nVisualizing the amplitude of CSI subcarriers across time."))

cells.append(nbf.v4.new_code_cell("""def plot_csi_heatmap(sample_matrix, title):
    plt.figure(figsize=(10, 6))
    sns.heatmap(sample_matrix.squeeze(), cmap="magma", cbar=True)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel("Subcarriers", fontsize=12)
    plt.ylabel("Time Steps", fontsize=12)
    plt.show()

if num_falls > 0:
    fall_sample = X[np.where(y == 1)[0][0]]
    plot_csi_heatmap(fall_sample, "CSI Amplitude Heatmap - Fall Event")

if num_nofalls > 0:
    nofall_sample = X[np.where(y == 0)[0][0]]
    plot_csi_heatmap(nofall_sample, "CSI Amplitude Heatmap - No Fall Event")"""))

cells.append(nbf.v4.new_code_cell("""plt.figure(figsize=(14, 6))
if num_falls > 0:
    plt.plot(X[np.where(y == 1)[0][0]].squeeze()[:, 10], label='Fall - Subcarrier 10', linewidth=2)
    plt.plot(X[np.where(y == 1)[0][0]].squeeze()[:, 30], label='Fall - Subcarrier 30', linewidth=2)
if num_nofalls > 0:
    plt.plot(X[np.where(y == 0)[0][0]].squeeze()[:, 10], label='No Fall - Subcarrier 10', linestyle='--', linewidth=2)
    plt.plot(X[np.where(y == 0)[0][0]].squeeze()[:, 30], label='No Fall - Subcarrier 30', linestyle='--', linewidth=2)

plt.title("Time Series Amplitude of Selected Subcarriers", fontsize=14, fontweight='bold')
plt.xlabel("Time Steps", fontsize=12)
plt.ylabel("Amplitude", fontsize=12)
plt.legend()
plt.show()"""))

# Section 4 Preprocessing
cells.append(nbf.v4.new_markdown_cell("## 4. Preprocessing Pipeline"))

cells.append(nbf.v4.new_code_cell("""if len(y) > 0:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.1, random_state=42, stratify=y_train)

    print(f"Training shapes: X={X_train.shape}, y={y_train.shape}")
    print(f"Validation shapes: X={X_val.shape}, y={y_val.shape}")
    print(f"Testing shapes: X={X_test.shape}, y={y_test.shape}")
else:
    print("Insufficient data to perform splits.")"""))

# Section 5 Model Architecture
cells.append(nbf.v4.new_markdown_cell("## 5. Model Architecture & Fine Tuning\n\nDesigning a multi-layered CNN with regularization and dropout to prevent overfitting."))

cells.append(nbf.v4.new_code_cell("""def build_model(input_shape):
    model = models.Sequential([
        layers.Input(shape=input_shape),
        
        layers.Conv2D(32, (3, 3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        layers.Conv2D(64, (3, 3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.3),
        
        layers.Conv2D(128, (3, 3), padding='same', activation='relu'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.4),
        
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(64, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])
    return model

model = build_model((TIME_STEPS, SUBCARRIERS, 1))
model.summary()"""))

# Section 6 Training
cells.append(nbf.v4.new_markdown_cell("## 6. Model Training\n\nTraining with Early Stopping and Model Checkpointing."))

cells.append(nbf.v4.new_code_cell("""if len(y) > 0:
    early_stopping = callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)

    history = model.fit(
        X_train, y_train, 
        epochs=50, 
        batch_size=32, 
        validation_data=(X_val, y_val),
        callbacks=[early_stopping, reduce_lr],
        verbose=1
    )
else:
    print("Insufficient data to train model.")"""))

# Section 7 Evaluation
cells.append(nbf.v4.new_markdown_cell("## 7. Evaluation & Results\n\nVisualizing accuracy, loss, and classification performance."))

cells.append(nbf.v4.new_code_cell("""if len(y) > 0 and 'history' in locals():
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    axes[0].plot(history.history['accuracy'], label='Train Accuracy', linewidth=2)
    axes[0].plot(history.history['val_accuracy'], label='Validation Accuracy', linewidth=2)
    axes[0].set_title('Model Accuracy', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Epoch', fontsize=12)
    axes[0].set_ylabel('Accuracy', fontsize=12)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(history.history['loss'], label='Train Loss', linewidth=2)
    axes[1].plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
    axes[1].set_title('Model Loss', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Epoch', fontsize=12)
    axes[1].set_ylabel('Loss', fontsize=12)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()"""))

cells.append(nbf.v4.new_code_cell("""if len(y) > 0:
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)

    y_pred_prob = model.predict(X_test)
    y_pred = (y_pred_prob > 0.5).astype(int).reshape(-1)

    cm = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False, 
                xticklabels=['No Fall', 'Fall'], yticklabels=['No Fall', 'Fall'])
    plt.title(f'Confusion Matrix (Test Acc: {test_acc*100:.2f}%)', fontsize=14, fontweight='bold')
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    plt.show()"""))

cells.append(nbf.v4.new_code_cell("""if len(y) > 0:
    report = classification_report(y_test, y_pred, target_names=['No Fall', 'Fall'])
    print(report)"""))

# Section 8 Export
cells.append(nbf.v4.new_markdown_cell("## 8. Model Export"))

cells.append(nbf.v4.new_code_cell("""model.save("fall_detection_cnn.h5")
print("Model saved successfully as 'fall_detection_cnn.h5'")"""))

nb['cells'] = cells

with open('c:\\\\ADHIKKESH\\\\SEM6\\\\FYP\\\\Fall_Detection\\\\ESP32-CSI-Tool\\\\Model\\\\main.ipynb', 'w') as f:
    nbf.write(nb, f)
