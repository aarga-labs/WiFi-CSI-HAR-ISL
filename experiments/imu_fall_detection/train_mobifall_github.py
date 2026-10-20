import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, Flatten, Dense, Concatenate, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

# --- 1. CONFIGURATION ---
# Make sure this path points exactly to the folder you git cloned!
DATA_DIR = "MobiAct_Dataset_v2.0-MobiFall_Dataset_v2.0/" 
WINDOW_SIZE = 128

FALL_ACTIVITIES = ['FOL', 'FKL', 'BSC', 'SDL']

X_acc_list, X_gyro_list, y_list = [], [], []

print("🚀 Step 1: Processing MobiFall with Bulletproof Parsing...")

# Bulletproof function to bypass the @DATA tag in the text files
def read_sensor_data(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    start_idx = 0
    for i, line in enumerate(lines):
        if '@DATA' in line:
            start_idx = i + 1
            break
            
    df = pd.read_csv(filepath, skiprows=start_idx, header=None)
    return df.iloc[:, 1:4].values # Extract only X, Y, Z columns

# --- 2. DATA PREPROCESSING ---
for root, dirs, files in os.walk(DATA_DIR):
    for file in files:
        if "_acc_" in file and file.endswith(".txt"):
            acc_path = os.path.join(root, file)
            gyro_path = acc_path.replace("_acc_", "_gyro_")
            
            if not os.path.exists(gyro_path):
                continue
                
            activity_code = file.split('_')[0]
            label = 1 if activity_code in FALL_ACTIVITIES else 0
            
            try:
                acc_data = read_sensor_data(acc_path)
                gyro_data = read_sensor_data(gyro_path)
                
                # Ensure equal length and downsample to ~43Hz
                min_len = min(len(acc_data), len(gyro_data))
                acc_data = acc_data[:min_len:2] 
                gyro_data = gyro_data[:min_len:2]
                
                # Magnitudes (Orientation Independent)
                acc_mag = np.sqrt(np.sum(acc_data**2, axis=1)).reshape(-1, 1)
                gyro_mag = np.sqrt(np.sum(gyro_data**2, axis=1)).reshape(-1, 1)
                
                if label == 1:
                    # Peak Impact Extraction for Falls
                    peak_idx = np.argmax(acc_mag)
                    
                    for offset in [-90, -64, -30]:
                        start_idx = peak_idx + offset
                        end_idx = start_idx + WINDOW_SIZE
                        
                        if start_idx >= 0 and end_idx <= len(acc_mag):
                            window_acc = acc_mag[start_idx:end_idx]
                            window_gyro = gyro_mag[start_idx:end_idx]
                            
                            # --- NEW: PER-WINDOW Z-SCORE NORMALIZATION ---
                            # This forces the AI to learn the SHAPE, not the raw force.
                            acc_mean, acc_std = np.mean(window_acc), np.std(window_acc) + 1e-6
                            gyro_mean, gyro_std = np.mean(window_gyro), np.std(window_gyro) + 1e-6
                            
                            X_acc_list.append((window_acc - acc_mean) / acc_std)
                            X_gyro_list.append((window_gyro - gyro_mean) / gyro_std)
                            y_list.append(1)
                else:
                    # ADL extraction 
                    for i in range(0, len(acc_mag) - WINDOW_SIZE, WINDOW_SIZE):
                        window_acc = acc_mag[i : i + WINDOW_SIZE]
                        window_gyro = gyro_mag[i : i + WINDOW_SIZE]
                        
                        # --- NEW: PER-WINDOW Z-SCORE NORMALIZATION ---
                        acc_mean, acc_std = np.mean(window_acc), np.std(window_acc) + 1e-6
                        gyro_mean, gyro_std = np.mean(window_gyro), np.std(window_gyro) + 1e-6
                        
                        X_acc_list.append((window_acc - acc_mean) / acc_std)
                        X_gyro_list.append((window_gyro - gyro_mean) / gyro_std)
                        y_list.append(0)
                        
            except Exception as e:
                pass # Skip broken files

X_acc = np.array(X_acc_list)
X_gyro = np.array(X_gyro_list)
y = np.array(y_list)

print(f"\n✅ Data Ready! Total Windows: {len(y)}")
print(f"Falls: {np.sum(y == 1)}, ADLs: {np.sum(y == 0)}")

if len(y) == 0:
    print("❌ ERROR: No data found! Please check your DATA_DIR folder path.")
    exit()

weights = compute_class_weight(class_weight='balanced', classes=np.unique(y), y=y)
class_weights = dict(zip(np.unique(y), weights))

X_acc_train, X_acc_test, X_gyro_train, X_gyro_test, y_train, y_test = train_test_split(
    X_acc, X_gyro, y, test_size=0.2, random_state=42
)

# --- 3. DUAL-STREAM CNN ---
print("\n🧠 Step 2: Building Model...")
input_acc = Input(shape=(WINDOW_SIZE, 1), name='acc_input')
x1 = BatchNormalization()(input_acc) 
x1 = Conv1D(32, kernel_size=3, activation='relu')(x1)
x1 = MaxPooling1D(2)(x1)
x1 = Conv1D(64, kernel_size=3, activation='relu')(x1)
x1 = MaxPooling1D(2)(x1)
x1 = Flatten()(x1)

input_gyro = Input(shape=(WINDOW_SIZE, 1), name='gyro_input')
x2 = BatchNormalization()(input_gyro) 
x2 = Conv1D(32, kernel_size=3, activation='relu')(x2)
x2 = MaxPooling1D(2)(x2)
x2 = Conv1D(64, kernel_size=3, activation='relu')(x2)
x2 = MaxPooling1D(2)(x2)
x2 = Flatten()(x2)

merged = Concatenate()([x1, x2])
z = Dense(128, activation='relu')(merged)
z = Dropout(0.5)(z)
output = Dense(1, activation='sigmoid')(z)

model = Model(inputs=[input_acc, input_gyro], outputs=output)
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

print("\n🏋️ Step 3: Training the Model...")
model.fit([X_acc_train, X_gyro_train], y_train, validation_data=([X_acc_test, X_gyro_test], y_test), epochs=10, batch_size=64, class_weight=class_weights)

print("\n📦 Step 4: Exporting to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT] 
tflite_model = converter.convert()

with open('mobiact_pocket_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("🎉 SUCCESS! 'mobiact_pocket_model.tflite' is ready!")