#!/usr/bin/env python3
"""
CSI to CSV Logger

Connects to the ESP32-S3 serial port and silently writes real-time CSI data to a CSV file.
It logs Timestamp, RSSI, Channel, State, MovementScore, and the Amplitude/Phase of the top 14 subcarriers.

Usage:
    python tools/csi_to_csv.py --port COM3 --output my_data.csv
"""

import argparse
import sys
import time
import csv
import glob
import platform

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

def auto_detect_port():
    system = platform.system()
    if system == "Darwin":
        for pattern in ["/dev/cu.usbmodem*", "/dev/cu.usbserial*",
                        "/dev/cu.SLAB_USBtoUART*", "/dev/cu.wchusbserial*"]:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
    elif system == "Windows":
        for p in serial.tools.list_ports.comports():
            desc = (p.description or "").lower()
            if any(kw in desc for kw in ["cp210", "ch340", "ch9102", "usb", "uart", "jtag"]):
                return p.device
    elif system == "Linux":
        for pattern in ["/dev/ttyUSB*", "/dev/ttyACM*"]:
            matches = glob.glob(pattern)
            if matches:
                return matches[0]

    ports = serial.tools.list_ports.comports()
    return ports[0].device if ports else None

def main():
    parser = argparse.ArgumentParser(description="Save Real-Time CSI to CSV")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--output", type=str, default="csi_data.csv", help="Output CSV filename")
    parser.add_argument("--debug", action="store_true", help="Print raw lines to console for debugging")
    args = parser.parse_args()

    port = args.port
    if port is None:
        print("Auto-detecting serial port...")
        port = auto_detect_port()
        if port is None:
            print("No serial port found. Connect your ESP32 and try again.")
            sys.exit(1)

    try:
        ser = serial.Serial(port, args.baud, timeout=0.5)
        # For ESP32-S3 Native USB (USB CDC), setting DTR/RTS can cause the board to halt
        # ser.dtr = True
        # ser.rts = False
        time.sleep(0.5)
        ser.reset_input_buffer()
        print(f"✅ Connected to {port} at {args.baud} baud.")
        print(f"✅ Silently saving real-time data to '{args.output}' ...")
        print("Press Ctrl+C to stop recording.")
    except Exception as e:
        print(f"❌ Error opening port: {e}")
        sys.exit(1)

    # Prepare CSV file
    with open(args.output, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the headers (Amplitude and Phase)
        headers = ["Timestamp_ms", "RSSI", "Channel", "State", "MovementScore"]
        for i in range(1, 15):
            headers.extend([f"Amp_{i}", f"Phase_{i}"])
        writer.writerow(headers)

        packet_count = 0
        import re
        CSI_RE = re.compile(
            r"CSI_DATA,"
            r"(-?\d+),"
            r"(-?\d+),"
            r"(\d+),"
            r"(MOTION|IDLE),"
            r"([\d.]+),"
            r"\[([^\]]+)\]?"
        )

        try:
            while True:
                raw_line = ser.readline()
                if not raw_line:
                    continue

                try:
                    line = raw_line.decode('utf-8', errors='ignore').strip()
                    if args.debug:
                        print(f"[DEBUG] {line}")
                except Exception:
                    continue

                m = CSI_RE.search(line)
                if m:
                    ts_ms = m.group(1)
                    rssi = m.group(2)
                    channel = m.group(3)
                    state = m.group(4)
                    score = m.group(5)
                    
                    # Parse amplitudes and phases
                    raw_vals = m.group(6).split()
                    
                    pairs = []
                    for v in raw_vals:
                        if ':' in v:
                            parts = v.split(':')
                            if len(parts) == 2:
                                try:
                                    amp = int(parts[0])
                                    phase = int(parts[1])
                                    pairs.append((amp, phase))
                                except ValueError:
                                    pass
                        elif v.lstrip('-').isdigit(): # Fallback for old firmware without phase
                            pairs.append((int(v), 0))
                    
                    # Sort descending by amplitude to find Top 14
                    pairs.sort(key=lambda x: x[0], reverse=True)
                    top_14_pairs = pairs[:14]
                    
                    # Pad with zeros if less than 14
                    while len(top_14_pairs) < 14:
                        top_14_pairs.append((0, 0))
                        
                    # Flatten into Amp_1, Phase_1, Amp_2, Phase_2...
                    flattened = []
                    for amp, phase in top_14_pairs:
                        flattened.extend([amp, phase])
                        
                    data_row = [ts_ms, rssi, channel, state, score] + flattened
                    
                    # Print to terminal
                    top_pairs_str = ", ".join([f"{flattened[i]}:{flattened[i+1]}°" for i in range(0, len(flattened), 2)])
                    print(f"[{ts_ms}] {state} (Score: {score}) | RSSI: {rssi}dBm | Top 14 (Amp:Phase): {top_pairs_str}")
                    
                    # Save to CSV
                    writer.writerow(data_row)
                    csvfile.flush() # Ensure it's saved in real-time
                    
                    packet_count += 1

        except KeyboardInterrupt:
            print(f"\n👋 Stopped recording. Total packets saved: {packet_count}")
        finally:
            ser.close()

if __name__ == "__main__":
    main()
