import numpy as np
import tensorflow as tf
from collections import deque
import time
import os
from datetime import datetime

# ==========================
# CONFIGURATION
# ==========================
WINDOW_SIZE = 15
FEATURES = 128
CSI_FILE = "csi_stream.txt"

CLASS_NAMES = {
    0: "Falling",
    1: "Empty",
    2: "Small Activity"
}

# Predict once every N CSI packets. At 100Hz, a stride of 10 means 10 predictions per second.
PREDICTION_STRIDE = 10
FALL_THRESHOLD = 2 

# ==========================
# LOAD MODEL
# ==========================
print("=" * 70)
print("Loading model...")
# Disabling custom operations warnings if there are any
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

try:
    model = tf.keras.models.load_model("fall_detection_3class.h5")
    print("Model loaded successfully")
    print("Expected Input Shape :", model.input_shape)
    print("Expected Output Shape:", model.output_shape)
except Exception as e:
    print(f"Failed to load model. Error: {e}")
    exit()

print("=" * 70)

# Initialize buffer and counters
buffer = deque(maxlen=WINDOW_SIZE)
fall_count = 0
empty_count = 0
activity_count = 0

# ==========================
# CSI PARSER
# ==========================
def extract_amplitude(line):
    try:
        start = line.rfind("[")
        end = line.rfind("]")

        if start == -1 or end == -1:
            return None

        # Extract the string containing the numbers
        csi_values_str = line[start + 1:end].strip()

        # Safely convert to numpy array
        values = np.fromstring(csi_values_str, sep=" ", dtype=np.float32)

        if len(values) == 0:
            return None

        # Ensure we have an even number of pairs (Real, Imaginary)
        if len(values) % 2 != 0:
            values = values[:-1]

        # Standard ESP32 format: Imaginary first, then Real
        imag = values[0::2]
        real = values[1::2]

        # Calculate Amplitude
        amplitude = np.sqrt(imag ** 2 + real ** 2)

        # Pad with zeros if the model demands 128 features but ESP32 only gives 64
        if len(amplitude) < FEATURES:
            padded = np.zeros(FEATURES)
            padded[:len(amplitude)] = amplitude
            amplitude = padded

        # Truncate if it somehow exceeds 128
        return amplitude[:FEATURES]

    except Exception:
        # Silently fail on bad lines to keep the 100Hz stream running smoothly
        return None

# ==========================
# NORMALIZATION
# ==========================
def normalize_window(window_data):
    """Applies Z-score normalization to the entire time window before prediction."""
    mean_val = np.mean(window_data, axis=0)
    std_val = np.std(window_data, axis=0)
    return (window_data - mean_val) / (std_val + 1e-8)

# ==========================
# WAIT FOR ESP32 DATA STREAM
# ==========================
print(f"Waiting for ESP32 to create '{CSI_FILE}' ...")

while not os.path.exists(CSI_FILE):
    time.sleep(1)

print(f"Found {CSI_FILE}! Initializing live CSI stream...")
print("=" * 70)

# ==========================
# REALTIME INFERENCE LOOP
# ==========================
with open(CSI_FILE, "r") as f:
    
    # Jump to the end of the file to only read fresh 100Hz data
    f.seek(0, 2)
    packet_counter = 0

    while True:
        line = f.readline()

        # If no new data is written yet, yield CPU briefly
        if not line:
            time.sleep(0.005) 
            continue

        line = line.strip()

        if not line.startswith("CSI_DATA"):
            continue

        amplitude = extract_amplitude(line)

        if amplitude is None:
            continue

        buffer.append(amplitude)
        packet_counter += 1

        # Wait until the deque is fully populated
        if len(buffer) < WINDOW_SIZE:
            print(f"Buffering CSI frames ({len(buffer)}/{WINDOW_SIZE})...", end="\r")
            continue

        # Run inference based on stride
        if packet_counter % PREDICTION_STRIDE != 0:
            continue

        try:
            # Convert buffer to numpy array and normalize it
            raw_window = np.array(buffer)
            normalized_window = normalize_window(raw_window)

            # Expand dims to match (Batch_Size, Timesteps, Features) -> (1, 15, 128)
            x = np.expand_dims(normalized_window, axis=0)

            # Predict
            probs = model.predict(x, verbose=0)[0]
            pred_idx = int(np.argmax(probs))
            confidence = float(probs[pred_idx] * 100)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # -------------------
            # Detection Counters
            # -------------------
            if pred_idx == 0:
                fall_count += 1
                empty_count = 0
                activity_count = 0
            elif pred_idx == 1:
                empty_count += 1
                fall_count = 0
                activity_count = 0
            else:
                activity_count += 1
                fall_count = 0
                empty_count = 0

            # -------------------
            # Terminal Output
            # -------------------
            print("\n" + "-" * 40)
            print(f"[{timestamp}] -> {CLASS_NAMES[pred_idx].upper()} ({confidence:.1f}%)")
            print(f"   Fall: {probs[0]:.2f} | Empty: {probs[1]:.2f} | Activity: {probs[2]:.2f}")

            # -------------------
            # FALL ALERT LOGIC
            # -------------------
            if fall_count >= FALL_THRESHOLD:
                print("\n" + "=" * 50)
                print(" 🚨🚨🚨 CRITICAL: FALL DETECTED 🚨🚨🚨")
                print("=" * 50 + "\n")
                # Reset counter to avoid continuous spamming
                fall_count = 0 

        except Exception as e:
            print(f"\nInference Error: {e}")