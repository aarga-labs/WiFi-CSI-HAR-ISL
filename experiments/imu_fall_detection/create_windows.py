import pandas as pd
import numpy as np

WINDOW_SIZE = 128  # 2.56 seconds at 50Hz
STEP_SIZE = 64     # 50% overlap for better accuracy

def create_sliding_windows(df):
    X_list, y_list = [], []
    
    # Grab only the 6 sensor columns (acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z)
    sensor_data = df.iloc[:, 2:8].values
    labels = df['Label'].values
    
    for i in range(0, len(df) - WINDOW_SIZE, STEP_SIZE):
        window_features = sensor_data[i : i + WINDOW_SIZE]
        window_labels = labels[i : i + WINDOW_SIZE]
        
        # If there is even one '1' in this 2.5 second window, label the whole window as a Fall (1)
        window_label = 1 if np.any(window_labels == 1) else 0
        
        X_list.append(window_features)
        y_list.append(window_label)
        
    return np.array(X_list), np.array(y_list)

print("Loading data...")
# Read the ADL file and the NEW corrected Fall file
df_adl = pd.read_csv("master_adl_walking.csv")
df_fall = pd.read_csv("master_falling_corrected.csv")

# Create windows
X_adl, y_adl = create_sliding_windows(df_adl)
X_fall, y_fall = create_sliding_windows(df_fall)

# Combine them into one master dataset
X_total = np.concatenate((X_adl, X_fall), axis=0)
y_total = np.concatenate((y_adl, y_fall), axis=0)

print(f"\nFinal Neural Network Dataset Shape:")
print(f"Features (X): {X_total.shape} -> (Total Windows, 128 timesteps, 6 sensors)")
print(f"Labels (y):   {y_total.shape}")

# Save as highly compressed NumPy files for TensorFlow
np.save("X_data.npy", X_total)
np.save("y_data.npy", y_total)

print("\nSuccess! Saved X_data.npy and y_data.npy. Ready for Deep Learning!")