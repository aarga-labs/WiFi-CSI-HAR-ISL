import serial
import numpy as np
import tensorflow as tf
import re
import time

# 1. Configuration
MODEL_PATH = 'fall_detection_model.h5'
SERIAL_PORT = 'COM3'  # <--- CHANGE THIS TO YOUR ESP32 PORT
BAUD_RATE = 921600    # The default baud rate for ESP32-CSI-Tool

# 2. Load the AI Model
print("Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully.")

# 3. Connect to the ESP32
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Successfully connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"Error: Could not open serial port {SERIAL_PORT}. Is it plugged in and not open in Arduino/Putty?")
    print(f"Details: {e}")
    exit()

print("\n--- Listening for Real-Time CSI Data ---")
print("Press Ctrl+C to stop.\n")

# 4. The Real-Time Loop
while True:
    try:
        # Read a line of data coming from the USB cable
        # We use errors='ignore' to skip over any corrupted serial characters
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        # Steven's tool usually starts CSI packets with the string "CSI_DATA"
        if line.startswith("CSI_DATA"):
            
            # Use Regular Expressions (re) to find everything between the brackets [ ]
            match = re.search(r'\[(.*?)\]', line)
            
            if match:
                raw_csi_str = match.group(1)
                
                # Split the string of numbers by spaces
                clean_list = raw_csi_str.split()
                
                # Ensure we have exactly 128 numbers before feeding the AI
                if len(clean_list) == 128:
                    numeric_data = np.array(clean_list, dtype=np.float32)
                    model_input = numeric_data.reshape(1, 128, 1)
                    
                    # Run inference
                    prediction = model.predict(model_input, verbose=0)
                    prob = prediction[0][0]
                    
                    # Display the result
                    if prob > 0.5:
                        print(f"[{time.strftime('%H:%M:%S')}] Prob: {prob:.4f} | 🚨 FALL DETECTED 🚨")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] Prob: {prob:.4f} | Normal Activity")
                else:
                    # Occasional dropped packets happen over serial, we just skip them
                    pass
                    
    except KeyboardInterrupt:
        print("\nStopping real-time stream...")
        ser.close()
        break
    except Exception as e:
        print(f"Processing error: {e}")
        continue