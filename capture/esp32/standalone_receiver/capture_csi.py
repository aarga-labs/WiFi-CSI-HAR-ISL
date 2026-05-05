import serial
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- CONFIGURATION ---
# Change this to your actual COM port (e.g., 'COM3', 'COM5')
SERIAL_PORT = 'COM3' 
BAUD_RATE = 115200

# Setup the live graph
fig, ax = plt.subplots()
x_data = list(range(64))  # 64 subcarriers
line, = ax.plot(x_data, [0]*64, color='blue')
ax.set_ylim(0, 50)  # Adjust this if your waves go higher than 50
ax.set_title('Live CSI Fall Detection Radar')
ax.set_ylabel('Signal Amplitude')
ax.set_xlabel('Subcarrier Index')

# Open the USB serial connection and the CSV file
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    print(f"Successfully connected to {SERIAL_PORT}")
except Exception as e:
    print(f"Error opening port: {e}")
    exit()

csv_file = open('fall_dataset.csv', 'w', newline='')
writer = csv.writer(csv_file)

def update(frame):
    try:
        # Read a line of text from the ESP32
        line_data = ser.readline().decode('utf-8').strip()
        
        # If it is our CSI data, process it
        if line_data.startswith("CSI_DATA"):
            parts = line_data.split(',')
            
            # Make sure we have the header + 64 numbers
            if len(parts) == 65:
                # Convert the text numbers to floats
                amplitudes = [float(val) for val in parts[1:]]
                
                # 1. Save it to the CSV for your ML model
                writer.writerow(amplitudes)
                
                # 2. Update the live graph on the screen
                line.set_ydata(amplitudes)
                return line,
                
    except Exception as e:
        pass # Ignore random serial garbage
        
    return line,

print("Listening for CSI Data... Close the graph window to stop recording.")

# Start the live animation loop
ani = animation.FuncAnimation(fig, update, interval=10, blit=True, cache_frame_data=False)
plt.show()

# When you close the window, cleanly shut down
csv_file.close()
ser.close()
print("Recording saved to fall_dataset.csv!")