import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def extract_csi_amplitude(csi_string):
    """
    Parses the CSI string, extracts Imaginary and Real parts, 
    and computes the signal amplitude.
    """
    # Remove brackets and split by whitespace
    clean_str = csi_string.replace('[', '').replace(']', '').strip()
    
    # Convert string values to integers
    vals = [int(v) for v in clean_str.split() if v]
    
    # Ensure even length for Imaginary/Real pairs
    if len(vals) % 2 != 0:
        vals = vals[:-1]
        
    vals = np.array(vals)
    
    # In standard CSI data (like ESP32), values are interleaved [Imaginary, Real, Imaginary, Real...]
    imag = vals[0::2]
    real = vals[1::2]
    
    # Calculate Amplitude: sqrt(imag^2 + real^2)
    amplitude = np.sqrt(imag**2 + real**2)
    return amplitude

def main():
    print("Loading data...")
    # 1. Load the dataset
    df = pd.read_csv('falling_06.csv',encoding='utf-16')

    print("Parsing CSI arrays...")
    # 2. Apply the parsing to all rows
    amplitudes = []
    for idx, row in df.iterrows():
        try:
            amp = extract_csi_amplitude(row['CSI_DATA'])
            amplitudes.append(amp)
        except Exception as e:
            print(f"Skipping row {idx} due to error: {e}")

    # Convert to a 2D numpy array: rows = time (packets), cols = subcarriers
    amplitudes = np.array(amplitudes)

    # 3. Calculate Variance
    # Motion (like falling) disrupts the channel, causing spikes in variance.
    csi_variance = np.var(amplitudes, axis=1)

    print("Generating plots...")
    # 4. Plot the data
    plt.figure(figsize=(14, 8))

    # --- Plot 1: The Heatmap ---
    plt.subplot(2, 1, 1)
    # Transpose (.T) to have Time on X-axis and Subcarriers on Y-axis
    plt.imshow(amplitudes.T, aspect='auto', cmap='jet', interpolation='nearest')
    plt.title('CSI Amplitude Heatmap (Subcarriers vs. Time)')
    plt.ylabel('Subcarrier Index')
    plt.xlabel('Packet Index (Time)')
    plt.colorbar(label='Amplitude')

    # --- Plot 2: Variance Spikes (Motion / Fall Detection) ---
    plt.subplot(2, 1, 2)
    plt.plot(csi_variance, color='crimson', linewidth=1.5)
    plt.title('CSI Variance over Time (Spikes indicate falling / motion)')
    plt.ylabel('Variance')
    plt.xlabel('Packet Index (Time)')
    plt.grid(True, linestyle='--', alpha=0.7)

    # Adjust layout and show
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()