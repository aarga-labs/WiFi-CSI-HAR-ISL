"""Debug script: Capture live CSI data and compare to training data"""
import serial
import numpy as np
import re
import time
import os
import glob
import pandas as pd

SERIAL_PORT = 'COM3'
BAUD_RATE = 921600
DATASET_DIR = 'ESP32-CSI-Tool/active_sta/dataset'

def parse_csi_serial(raw_csi_str):
    clean_list = raw_csi_str.split()
    if len(clean_list) != 128:
        return None
    vals = np.array(clean_list, dtype=float)
    imag = vals[0::2]
    real = vals[1::2]
    return np.sqrt(imag**2 + real**2)

def parse_csi_csv(csi_str):
    match = re.search(r'\[(.*?)\]', str(csi_str))
    if not match: return None
    vals = np.fromstring(match.group(1), sep=' ', dtype=float)
    if len(vals) != 128: return None
    return np.sqrt(vals[0::2]**2 + vals[1::2]**2)

# --- Load stats from training data ---
print("=== TRAINING DATA STATS ===")
for label, fpath in [("no_falling.csv", os.path.join(DATASET_DIR, 'no_falling.csv')),
                      ("amrith_falling_03.csv", os.path.join(DATASET_DIR, 'amrith_falling_03.csv'))]:
    try: df = pd.read_csv(fpath, on_bad_lines='skip', header=None, encoding='utf-8')
    except: df = pd.read_csv(fpath, on_bad_lines='skip', header=None, encoding='utf-16')
    amps = np.array([a for row in df.iloc[:, 25] if (a := parse_csi_csv(row)) is not None])
    print(f"  {label}: shape={amps.shape}, mean={np.mean(amps):.2f}, std={np.std(amps):.2f}, min={np.min(amps):.2f}, max={np.max(amps):.2f}")
    print(f"    First 5 values of row 0: {amps[0][:5]}")

# --- Capture live data ---
print("\n=== LIVE DATA (capturing 50 packets from ESP32) ===")
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
live_amps = []
while len(live_amps) < 50:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line.startswith("CSI_DATA"):
        match = re.search(r'\[(.*?)\]', line)
        if match:
            amp = parse_csi_serial(match.group(1))
            if amp is not None:
                live_amps.append(amp)
                print(f"  Packet {len(live_amps)}/50", end='\r')

ser.close()
live_amps = np.array(live_amps)
print(f"\n  LIVE: shape={live_amps.shape}, mean={np.mean(live_amps):.2f}, std={np.std(live_amps):.2f}, min={np.min(live_amps):.2f}, max={np.max(live_amps):.2f}")
print(f"    First 5 values of row 0: {live_amps[0][:5]}")

print("\n=== COMPARISON ===")
print(f"  If means/ranges are wildly different, that's the domain gap causing 0% confidence.")
