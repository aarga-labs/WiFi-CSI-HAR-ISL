#!/usr/bin/env python3
import time
import sys
import os
import threading
from datetime import datetime
from PyQt5 import Qt

# Set environment variables for the new Team67 extract_csi block
# We configure the MAC filtering here natively
os.environ["CSI_TA"] = "42:42:42:42:42:42" # Match our transmitter
os.environ["CSI_RA"] = "any" # Accept any destination MAC

# Point PYTHONPATH and LD_LIBRARY_PATH to the local build tree for Team67 block
# We calculate this dynamically so it works on any laptop regardless of username
script_dir = os.path.dirname(os.path.abspath(__file__))
team67_build = os.path.abspath(os.path.join(script_dir, "../Team67_USRP_Receiver/gr-ieee802-11/build"))

if team67_build + "/python" not in os.environ.get("PYTHONPATH", ""):
    print("Restarting with Team67 library paths...")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{team67_build}/python:{env.get('PYTHONPATH', '')}"
    env["LD_LIBRARY_PATH"] = f"{team67_build}/lib:{env.get('LD_LIBRARY_PATH', '')}"
    os.execve(sys.executable, [sys.executable] + sys.argv, env)

# Import the GNU Radio generated flowgraph
try:
    from wifi_rx import wifi_rx
except ImportError:
    print("Error: Could not import wifi_rx.py. Make sure you ran 'grcc wifi_rx.grc'")
    sys.exit(1)

# Wi-Fi 2.4 GHz non-overlapping channels
CHANNELS = {
    1: 2412e6,
    6: 2437e6,
    11: 2462e6
}

# The duration to listen on each channel (in seconds)
DWELL_TIME = 0.1

if __name__ == '__main__':
    # Initialize Qt app since the flowgraph contains Qt GUI elements
    qapp = Qt.QApplication(sys.argv)
    
    # Initialize the top block
    tb = wifi_rx()
    tb.start()
    tb.show()
    
    global current_channel
    current_channel = 1

    print("Starting Channel Hopping with Team67 CSI Extractor...")

    # Main hopping loop
    def hop_channels():
        global current_channel
        while True:
            for ch_num, freq in CHANNELS.items():
                current_channel = ch_num
                
                # Update the frequency of the USRP and the Equalizer
                tb.set_freq(freq)
                
                # Pass the current channel down to the C++ block so it logs the channel in the CSV
                if hasattr(tb, 'ieee802_11_extract_csi_0'):
                    tb.ieee802_11_extract_csi_0.set_channel(ch_num)
                
                print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Hopped to Channel {ch_num} ({freq/1e6} MHz)")
                time.sleep(DWELL_TIME)

    hopper_thread = threading.Thread(target=hop_channels, daemon=True)
    hopper_thread.start()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        Qt.QApplication.quit()

    import signal
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    qapp.exec_()
