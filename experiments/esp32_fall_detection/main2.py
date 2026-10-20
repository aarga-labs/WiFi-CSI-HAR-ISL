import serial
import numpy as np
import tensorflow as tf
import re
import time
from collections import deque

# ==========================================
# 1. CONFIGURATION
# ==========================================
MODEL_PATH = 'pro_fall_detector_2d.keras' # Or .h5, both work with this trick
SERIAL_PORT = 'COM3'  # <--- Verify this matches your ESP32
BAUD_RATE = 921600
TIME_STEPS = 40       
SUBCARRIERS = 64
PREDICTION_STRIDE = 10 # Predict 10 times per second

# ==========================================
# 2. SETUP SLIDING WINDOW
# ==========================================
window = deque(maxlen=TIME_STEPS)

# ==========================================
# 3. MATH PARSER
# ==========================================
def parse_csi_string(raw_csi_str):
    """Converts the raw string of 128 Real/Imaginary pairs into 64 Amplitudes."""
    clean_list = raw_csi_str.split()
    if len(clean_list) != 128:
        return None
        
    vals = np.array(clean_list, dtype=float)
    imag = vals[0::2]
    real = vals[1::2]
    amplitude = np.sqrt(imag**2 + real**2)
    return amplitude



# ==========================================
# 4. BUILD THE BRAIN LOCALLY & INJECT KNOWLEDGE
# ==========================================
print("Building 2D CNN Architecture...")

# We build the exact same model we used in Colab to bypass version errors
model = tf.keras.models.Sequential([
    tf.keras.layers.Input(shape=(TIME_STEPS, SUBCARRIERS, 1)),
    tf.keras.layers.Conv2D(32, kernel_size=(3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Conv2D(64, kernel_size=(3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(pool_size=(2, 2)),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

print("Injecting learned weights from Colab...")
try:
    model.load_weights(MODEL_PATH)
    print("Brain transplant successful! Model is ready.")
except Exception as e:
    print(f"Error loading weights: Make sure {MODEL_PATH} is in the exact same folder!")
    print(f"Details: {e}")
    exit()

# ==========================================
# 5. CONNECT ESP32
# ==========================================
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print(f"Successfully connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"Error: Could not open serial port {SERIAL_PORT}.")
    print("Make sure no other programs (like ESP-IDF monitor) are using it.")
    exit()

print("\n--- Listening for Real-Time CSI Data ---")

# ==========================================
# 6. THE REAL-TIME LOOP
# ==========================================
packet_count = 0

while True:
    try:
        # Read the raw serial line
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        
        if line.startswith("CSI_DATA"):
            match = re.search(r'\[(.*?)\]', line)
            
            if match:
                raw_csi_str = match.group(1)
                amplitudes = parse_csi_string(raw_csi_str)
                
                if amplitudes is not None:
                    window.append(amplitudes)
                    
                    # Phase 1: Show the buffer filling up initially
                    if len(window) < TIME_STEPS:
                        print(f"Gathering initial environment data: {len(window)}/{TIME_STEPS} packets...", end='\r')
                    
                    # Phase 2: Buffer is full, start predicting
                    else:
                        packet_count += 1
                        
                        # Only run the AI prediction every 10th packet
                        if packet_count % PREDICTION_STRIDE == 0:
                            # Reshape for CNN: (1, 40, 64, 1)
                            model_input = np.array(window).reshape(1, TIME_STEPS, SUBCARRIERS, 1)
                            
                            # Run Inference
                            prediction = model.predict(model_input, verbose=0)
                            prob = prediction[0][0]
                            
                            # LIVE TRACKER
                            print(f"[{time.strftime('%H:%M:%S')}] Pkts: {packet_count} | AI Confidence: {prob*100:05.2f}%      ", end='\r')
                            
                            # FALL DETECTION THRESHOLD
                            if prob > 0.50: 
                                print(f"\n\n[{time.strftime('%H:%M:%S')}] 🚨 FALL DETECTED! (Confidence: {prob*100:.1f}%) 🚨")
                                
                                # Clear the window so it resets after the event
                                window.clear()
                                packet_count = 0
                                print("Resetting buffer, waiting for room to stabilize...\n")
                            
    except KeyboardInterrupt:
        print("\n\nStopping real-time stream...")
        ser.close()
        break
    except Exception as e:
        # Ignore random serial noise errors over USB
        continue