import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv1D, MaxPooling1D, Flatten, Dense, Concatenate, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

# --- 1. CONFIGURATION ---
DATA_DIR = "SisFall_dataset/" 
WINDOW_SIZE = 128

X_acc_list = []
X_gyro_list = []
y_list = []

print("🚀 Step 1: Processing SisFall with Peak Impact Extraction...")

# --- 2. DATA PREPROCESSING ---
for root, dirs, files in os.walk(DATA_DIR):
    for file in files:
        if file.endswith(".txt") and not file.startswith("Readme"):
            filepath = os.path.join(root, file)
            label = 1 if file.startswith('F') else 0
            
            try:
                df = pd.read_csv(filepath, header=None, sep=',', usecols=[0,1,2,3,4,5])
                df = df.iloc[::4, :].reset_index(drop=True) # Downsample 200Hz -> 50Hz
                
                # Convert units to match Android (m/s^2 and rad/s)
                acc_data = (df.iloc[:, 0:3].values / 256.0) * 9.81
                gyro_data = (df.iloc[:, 3:6].values * (4000.0 / 65536.0)) * (np.pi / 180.0)
                
                # Calculate Magnitudes
                acc_mag = np.sqrt(np.sum(acc_data**2, axis=1)).reshape(-1, 1)
                gyro_mag = np.sqrt(np.sum(gyro_data**2, axis=1)).reshape(-1, 1)
                
                if label == 1:
                    # --- THE FIX: EXTRACT ONLY THE ACTUAL FALL IMPACT ---
                    peak_idx = np.argmax(acc_mag) # Find the exact moment of the crash
                    
                    # Create 3 augmented windows around the crash to give the AI more data
                    for offset in [-90, -64, -30]:
                        start_idx = peak_idx + offset
                        end_idx = start_idx + WINDOW_SIZE
                        
                        if start_idx >= 0 and end_idx <= len(acc_mag):
                            X_acc_list.append(acc_mag[start_idx:end_idx])
                            X_gyro_list.append(gyro_mag[start_idx:end_idx])
                            y_list.append(1)
                else:
                    # ADL (Non-Fall) files: Extract non-overlapping windows
                    for i in range(0, len(acc_mag) - WINDOW_SIZE, WINDOW_SIZE):
                        X_acc_list.append(acc_mag[i : i + WINDOW_SIZE])
                        X_gyro_list.append(gyro_mag[i : i + WINDOW_SIZE])
                        y_list.append(0)
                        
            except Exception as e:
                pass 

X_acc = np.array(X_acc_list)
X_gyro = np.array(X_gyro_list)
y = np.array(y_list)

print(f"✅ Data Ready! Total Windows: {len(y)}")
print(f"Falls: {np.sum(y == 1)}, ADLs: {np.sum(y == 0)}")

# Balance the weights because there are more ADLs than Falls
weights = compute_class_weight(class_weight='balanced', classes=np.unique(y), y=y)
class_weights = dict(zip(np.unique(y), weights))

X_acc_train, X_acc_test, X_gyro_train, X_gyro_test, y_train, y_test = train_test_split(
    X_acc, X_gyro, y, test_size=0.2, random_state=42
)

# --- 3. DUAL-STREAM CNN WITH NORMALIZATION ---
print("\n🧠 Step 2: Building Model with Batch Normalization...")

# Stream 1: Accelerometer
input_acc = Input(shape=(WINDOW_SIZE, 1), name='acc_input')
x1 = BatchNormalization()(input_acc) # Automatically scales Android physics data!
x1 = Conv1D(32, kernel_size=3, activation='relu')(x1)
x1 = MaxPooling1D(2)(x1)
x1 = Conv1D(64, kernel_size=3, activation='relu')(x1)
x1 = MaxPooling1D(2)(x1)
x1 = Flatten()(x1)

# Stream 2: Gyroscope
input_gyro = Input(shape=(WINDOW_SIZE, 1), name='gyro_input')
x2 = BatchNormalization()(input_gyro) # Automatically scales Android physics data!
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

# --- 4. TRAINING & EXPORT ---
print("\n🏋️ Step 3: Training the Model...")
model.fit(
    [X_acc_train, X_gyro_train], y_train, 
    validation_data=([X_acc_test, X_gyro_test], y_test), 
    epochs=12, 
    batch_size=64,
    class_weight=class_weights # Forces AI to pay equal attention to falls!
)

print("\n📦 Step 4: Exporting to TFLite...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT] 
tflite_model = converter.convert()

with open('sisfall_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("🎉 SUCCESS! The Smart Model is Ready!")