from tensorflow.keras.models import load_model
import numpy as np
from collections import deque
import time
import os
from datetime import datetime

# ==========================
# CONFIG
# ==========================

WINDOW_SIZE = 15
FEATURES = 128

CSI_FILE = "csi_stream.txt"

CLASS_NAMES = {
    0: "Falling",
    1: "Empty",
    2: "Small Activity"
}

# Predict once every N CSI packets
PREDICTION_STRIDE = 10

# For testing keep 1
# Later increase to 3-5
FALL_THRESHOLD = 1

# ==========================
# LOAD MODEL
# ==========================

print("=" * 70)
print("Loading model...")

model = load_model("fall_detection_3class.h5")

print("Model loaded successfully")
print("Input Shape :", model.input_shape)
print("Output Shape:", model.output_shape)

print("=" * 70)

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

        csi_values = line[start + 1:end]

        values = np.fromstring(
            csi_values,
            sep=" ",
            dtype=np.float32
        )

        if len(values) == 0:
            return None

        if len(values) % 2 != 0:
            values = values[:-1]

        imag = values[0::2]
        real = values[1::2]

        amplitude = np.sqrt(
            imag ** 2 + real ** 2
        )

        if len(amplitude) < FEATURES:
            padded = np.zeros(FEATURES)
            padded[:len(amplitude)] = amplitude
            amplitude = padded

        amplitude = amplitude[:FEATURES]

        return amplitude

    except Exception as e:
        print("Parse Error:", e)
        return None

# ==========================
# WAIT FOR FILE
# ==========================

print(f"Waiting for {CSI_FILE} ...")

while not os.path.exists(CSI_FILE):
    time.sleep(1)

print(f"Found {CSI_FILE}")
print("Waiting for live CSI stream...")
print("=" * 70)

# ==========================
# REALTIME LOOP
# ==========================

with open(CSI_FILE, "r") as f:

    # Start reading only new data
    f.seek(0, 2)

    packet_counter = 0

    while True:

        line = f.readline()

        if not line:
            time.sleep(0.01)
            continue

        line = line.strip()

        if not line.startswith("CSI_DATA"):
            continue

        amplitude = extract_amplitude(line)

        if amplitude is None:
            continue

        buffer.append(amplitude)

        packet_counter += 1

        # Wait until full window is ready
        if len(buffer) < WINDOW_SIZE:

            print(
                f"Collecting CSI packets "
                f"({len(buffer)}/{WINDOW_SIZE})",
                end="\r"
            )

            continue

        # Predict every N packets
        if packet_counter % PREDICTION_STRIDE != 0:
            continue

        try:

            x = np.array(buffer)

            x = np.expand_dims(
                x,
                axis=0
            )

            probs = model.predict(
                x,
                verbose=0
            )[0]

            pred_idx = int(np.argmax(probs))

            confidence = float(
                probs[pred_idx] * 100
            )

            timestamp = datetime.now().strftime(
                "%H:%M:%S"
            )

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
            # Normal Prediction
            # -------------------

            print("\n" + "-" * 70)

            print(
                f"[{timestamp}] "
                f"Prediction : {CLASS_NAMES[pred_idx]}"
            )

            print(
                f"Confidence : {confidence:.2f}%"
            )

            print(
                f"Falling      = {probs[0]:.4f}"
            )

            print(
                f"Empty        = {probs[1]:.4f}"
            )

            print(
                f"SmallActivity= {probs[2]:.4f}"
            )

            # -------------------
            # FALL DETECTED
            # -------------------

            if fall_count >= FALL_THRESHOLD:

                print("\n")
                print("=" * 70)
                print("🚨🚨🚨 FALL DETECTED 🚨🚨🚨")
                print("=" * 70)
                print("\n")

                fall_count = 0

        except Exception as e:

            print("Prediction Error:", e)