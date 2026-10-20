import serial
import csv
import time
import os

# --- CONFIGURATION ---
SERIAL_PORT = 'COM3'  # Keep your COM3
BAUD_RATE = 115200    # <--- CHANGED THIS BACK TO 115200
RECORD_SECONDS = 5    

# 1. Ask what we are recording
label = input("Enter action label (empty, walk, fall): ").strip().lower()
filename_base = f"{label}_"

# 2. Find the next available number automatically
counter = 1
while os.path.exists(f"{filename_base}{counter:02d}.csv"):
    counter += 1
filename = f"{filename_base}{counter:02d}.csv"

print(f"\n--- Get Ready! ---")
print(f"File will be saved as: {filename}")
input("Press ENTER to start the 5-second recording...")

# 3. Open Serial
try:
    # ADDED timeout=0.5 so it never freezes if a packet drops
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5)
    ser.setDTR(False) # Release the reset pin!
    ser.setRTS(False) # Release the boot pin!
    ser.reset_input_buffer() 
except Exception as e:
    print(f"Error opening port: {e}")
    exit()

# 4. Record Data
print(f"\n🔴 RECORDING FOR {RECORD_SECONDS} SECONDS... GO!")
start_time = time.time()
rows_recorded = 0

with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    
    while (time.time() - start_time) < RECORD_SECONDS:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line.startswith("CSI_DATA"):
                parts = line.split(',')
                if len(parts) == 65:
                    amplitudes = [float(x) for x in parts[1:]]
                    writer.writerow(amplitudes)
                    rows_recorded += 1
        except Exception:
            pass # Ignore random serial garbage

ser.close()

if rows_recorded > 0:
    print(f"✅ Done! Saved {filename} with {rows_recorded} rows of data.")
else:
    print("❌ ERROR: No data received! Make sure the Sender board is turned on.")