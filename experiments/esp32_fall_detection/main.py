import pandas as pd
import numpy as np
import tensorflow as tf
import os

# 1. Load the model
model = tf.keras.models.load_model('fall_detection_model.h5')

# 2. Load the CSV file with the correct UTF-16 settings
csv_path = './ESP32-CSI-Tool/active_sta/falling_01.csv'

try:
    # We use 'utf-16' because the 'ÿþ' characters appear in your column list
    # If 'utf-16' fails, try 'utf-16-le' or 'utf-16-be'
    df = pd.read_csv(csv_path, encoding='utf-16')
    
    # Clean up column names in case of hidden spaces
    df.columns = df.columns.str.strip()
    
    print("Model and CSV loaded successfully.")
    print(f"Verified Columns: {list(df.columns)}")

except Exception:
    # Fallback for some ESP32-CSI-Tool versions that use a different UTF-16 variant
    df = pd.read_csv(csv_path, encoding='utf-16-le')
    df.columns = df.columns.str.strip()
    print("Loaded with UTF-16-LE fallback.")

# 3. Process and Predict
if 'CSI_DATA' in df.columns:
    print("\n--- Starting Predictions ---")
    for i in range(len(df)):
        raw_csi_str = str(df['CSI_DATA'].iloc[i])
        
        # Split the string of 128 numbers
        clean_list = raw_csi_str.replace('[', '').replace(']', '').strip().split()
        
        if len(clean_list) == 128:
            numeric_data = np.array(clean_list, dtype=np.float32)
            model_input = numeric_data.reshape(1, 128, 1)
            
            prediction = model.predict(model_input, verbose=0)
            prob = prediction[0][0]
            status = "FALL DETECTED" if prob > 0.5 else "Normal"
            
            print(f"Row {i:03d} | Prob: {prob:.4f} | {status}")
else:
    print(f"STILL MISSING CSI_DATA. Current columns are: {list(df.columns)}")