import pandas as pd
import numpy as np
from scipy.signal import find_peaks

print("Analyzing master_falling.csv...")
df = pd.read_csv("master_falling.csv")

# 1. Calculate the Total Force (Magnitude) of the accelerometer
# Formula: sqrt(x^2 + y^2 + z^2)
magnitude = np.sqrt(df['acc_x']**2 + df['acc_y']**2 + df['acc_z']**2)

# 2. Find the impact peaks
# 'height=20' looks for massive spikes. 'distance=150' ensures bounces aren't counted twice.
peaks, _ = find_peaks(magnitude, height=20, distance=150)

print(f"Detected {len(peaks)} falls in the recording.")

# 3. Reset all labels to 0 (Not falling)
df['Label'] = 0

# 4. For each fall, label the action window as '1'
# We capture 1 second before impact (50 rows) and 1.5 seconds after (75 rows)
for p in peaks:
    start_row = max(0, p - 50)  
    end_row = min(len(df), p + 75) 
    df.loc[start_row:end_row, 'Label'] = 1
    print(f" -> Labeled Fall at {p/50:.1f} seconds")

# 5. Save to a new, clean file
df.to_csv("master_falling_corrected.csv", index=False)
print("\nSuccess! Saved to master_falling_corrected.csv")