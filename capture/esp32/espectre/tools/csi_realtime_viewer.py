#!/usr/bin/env python3
"""
ESPectre — Real-Time CSI Visualizer with Motion/Idle Labels

Connects to ESP32-S3 serial port and displays a live 4-panel dashboard:
  1. Subcarrier Amplitude Heatmap (time × 64 subcarriers)
  2. Selected Subcarrier Amplitude Time-Series
  3. Motion State Timeline (green=IDLE, red=MOTION)
  4. Movement Score over time

Usage:
    python csi_realtime_viewer.py                     # auto-detect port
    python csi_realtime_viewer.py --port /dev/cu.usbmodem14101
    python csi_realtime_viewer.py --port COM3          # Windows

Requirements:
    pip install pyserial matplotlib numpy
"""

import argparse
import sys
import time
import threading
import re
import glob
from collections import deque
import platform

import numpy as np

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

import matplotlib
# Use TkAgg on Windows; let macOS/Linux auto-detect
if platform.system() == "Windows":
    matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.gridspec as gridspec


# ─────────────────────────────── Constants ────────────────────────────────

NUM_SUBCARRIERS = 64
WINDOW_SIZE = 100          # packets to show in scrolling window
BAUD_RATE = 115200
UPDATE_INTERVAL_MS = 250   # dashboard refresh rate (~4 fps)

# Subcarriers to highlight in time-series plot
HIGHLIGHT_SC = [16, 24, 36, 48]

# Custom color map
CSI_CMAP = LinearSegmentedColormap.from_list(
    "csi", ["#0d1b2a", "#1b3a5c", "#2ec4b6", "#e8c547", "#ff6b6b", "#c0392b"]
)

# Motion bar colors (RGB uint8)
_COLOR_MOTION = np.array([248, 81, 73], dtype=np.uint8)
_COLOR_IDLE   = np.array([63, 185, 80], dtype=np.uint8)
_COLOR_EMPTY  = np.array([22, 27, 34], dtype=np.uint8)


# ─────────────────────────────── Data Store ───────────────────────────────

class CSIDataStore:
    """Thread-safe circular buffer for CSI packets.

    The lock is held only for the brief moment needed to shallow-copy the
    deque references.  The expensive np.array() conversion happens OUTSIDE
    the lock so the serial-reader thread is never blocked for long.
    """

    def __init__(self, maxlen=WINDOW_SIZE):
        self.lock = threading.Lock()
        self.amplitudes = deque(maxlen=maxlen)
        self.states = deque(maxlen=maxlen)
        self.scores = deque(maxlen=maxlen)
        self.rssi_vals = deque(maxlen=maxlen)
        self.timestamps = deque(maxlen=maxlen)
        self.packet_count = 0
        self._snap_count = 0  # last count consumed by the dashboard

    # ── writer (serial thread) ──
    def add(self, amplitudes, state, score, rssi, ts):
        with self.lock:
            self.amplitudes.append(amplitudes)
            self.states.append(state)
            self.scores.append(score)
            self.rssi_vals.append(rssi)
            self.timestamps.append(ts)
            self.packet_count += 1

    # ── reader (GUI thread) ──
    def snapshot(self):
        """Return a snapshot of the current data or None if nothing new."""
        with self.lock:
            count = self.packet_count
            if count == 0 or count == self._snap_count:
                return None
            # Shallow copies — very fast, no numpy work under the lock
            amps_list = list(self.amplitudes)
            states_list = list(self.states)
            scores_list = list(self.scores)
            rssi_list = list(self.rssi_vals)
            self._snap_count = count

        # Expensive conversion happens outside the lock
        return {
            "amplitudes": np.array(amps_list, dtype=np.float32),
            "states": states_list,
            "scores": scores_list,
            "rssi": rssi_list,
            "count": count,
        }


# ─────────────────────────── Serial Parser ────────────────────────────────

CSI_RE = re.compile(
    r"CSI_DATA,"
    r"(-?\d+),"
    r"(-?\d+),"
    r"(\d+),"
    r"(MOTION|IDLE),"
    r"([\d.]+),"
    r"\[([^\]]+)\]?"
)

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def parse_csi_line(line: str):
    line = ANSI_RE.sub('', line)
    m = CSI_RE.search(line)
    if not m:
        return None
    try:
        ts_ms = int(m.group(1))
        rssi = int(m.group(2))
        channel = int(m.group(3))
        state = m.group(4)
        score = float(m.group(5))
        raw_vals = m.group(6).split()
        amps = np.array([int(v) for v in raw_vals if v.lstrip('-').isdigit()], dtype=np.float32)
    except (ValueError, IndexError):
        return None

    amplitudes = np.zeros(NUM_SUBCARRIERS, dtype=np.float32)
    n = min(len(amps), NUM_SUBCARRIERS)
    amplitudes[:n] = amps[:n]

    return {"ts": ts_ms, "rssi": rssi, "channel": channel,
            "state": state, "score": score, "amplitudes": amplitudes}


# ─────────────────────────── Serial Reader ────────────────────────────────

def serial_reader(port, baud, store, stop_event):
    """Continuously read serial lines and feed parsed CSI data into *store*.

    Uses a larger-than-default receive buffer so that slow GUI frames don't
    cause the OS serial buffer to overflow and drop data.
    """
    try:
        ser = serial.Serial(port, baud, timeout=0.1)
        # Try to enlarge the OS-level receive buffer (pyserial ≥ 3.x)
        try:
            ser.set_buffer_size(rx_size=131072)  # 128 KiB
        except Exception:
            pass  # not all platforms support this; it's fine
        ser.dtr = True
        ser.rts = False
        time.sleep(0.5)
        ser.reset_input_buffer()
        print(f"✅  Connected to {port} @ {baud} baud")
        print("    Waiting for CSI_DATA packets...")
    except serial.SerialException as e:
        print(f"❌  Could not open {port}: {e}")
        stop_event.set()
        return

    first_packet = True
    debug_count = 0

    # Pre-compiled quick filter to skip lines early
    csi_marker = b"CSI_DATA"

    while not stop_event.is_set():
        try:
            # Read ALL available lines in a burst to keep the buffer drained
            raw = ser.readline()
            if not raw:
                continue

            # Quick binary check before decoding — skip non-CSI lines cheaply
            if csi_marker not in raw:
                if debug_count < 3:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if line:
                        preview = line[:100] + "..." if len(line) > 100 else line
                        print(f"    [{debug_count+1}] {preview}")
                        debug_count += 1
                continue

            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            if debug_count < 3:
                preview = line[:100] + "..." if len(line) > 100 else line
                print(f"    [{debug_count+1}] {preview}")
                debug_count += 1

            parsed = parse_csi_line(line)
            if parsed:
                if first_packet:
                    print(f"✅  Receiving CSI data! (ch={parsed['channel']}, RSSI={parsed['rssi']}dBm)")
                    first_packet = False
                store.add(parsed["amplitudes"], parsed["state"],
                          parsed["score"], parsed["rssi"], parsed["ts"])
        except serial.SerialException:
            print("⚠️  Serial connection lost")
            stop_event.set()
        except Exception:
            pass

    try:
        ser.close()
    except Exception:
        pass


# ──────────────────────────── Port Detection ──────────────────────────────

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


# ──────────────────────────── Dashboard ───────────────────────────────────

def run_dashboard(store, stop_event):
    plt.rcParams.update({
        "figure.facecolor": "#0d1117",
        "axes.facecolor": "#161b22",
        "axes.edgecolor": "#30363d",
        "axes.labelcolor": "#c9d1d9",
        "xtick.color": "#8b949e",
        "ytick.color": "#8b949e",
        "text.color": "#c9d1d9",
        "font.family": "monospace",
        "font.size": 9,
    })

    fig = plt.figure(figsize=(13, 8))
    fig.canvas.manager.set_window_title("ESPectre — Real-Time CSI Viewer")
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 2, 0.5, 2], hspace=0.4)

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    ax4 = fig.add_subplot(gs[3])

    # 1. Heatmap
    heatmap_data = np.zeros((NUM_SUBCARRIERS, WINDOW_SIZE), dtype=np.float32)
    heatmap_img = ax1.imshow(
        heatmap_data, aspect="auto", origin="lower",
        cmap=CSI_CMAP, vmin=0, vmax=40, interpolation="nearest"
    )
    ax1.set_ylabel("Subcarrier")
    ax1.set_title("Subcarrier Amplitude Heatmap", fontsize=11, fontweight="bold", color="#58a6ff")

    # 2. Time-series
    colors = ["#58a6ff", "#f0883e", "#3fb950", "#d2a8ff"]
    ts_lines = []
    for i, sc in enumerate(HIGHLIGHT_SC):
        ln, = ax2.plot([], [], color=colors[i], linewidth=1.2, label=f"SC {sc}")
        ts_lines.append(ln)
    ax2.set_ylabel("Amplitude")
    ax2.set_title("Selected Subcarrier Amplitudes", fontsize=11, fontweight="bold", color="#58a6ff")
    ax2.legend(loc="upper right", fontsize=7, framealpha=0.4, facecolor="#161b22", edgecolor="#30363d")
    ax2.set_xlim(0, WINDOW_SIZE)
    ax2.set_ylim(0, 50)

    # 3. Motion bar
    motion_data = np.full((1, WINDOW_SIZE, 3), _COLOR_EMPTY, dtype=np.uint8)
    motion_img = ax3.imshow(motion_data, aspect="auto", interpolation="nearest")
    ax3.set_yticks([])
    ax3.set_title("Motion State (green=IDLE, red=MOTION)", fontsize=9, color="#58a6ff")

    # 4. Score
    score_line, = ax4.plot([], [], color="#f0883e", linewidth=1.5, label="Score")
    ax4.set_ylabel("Score")
    ax4.set_title("Movement Score", fontsize=11, fontweight="bold", color="#58a6ff")
    ax4.set_xlim(0, WINDOW_SIZE)
    ax4.set_ylim(0, 5)

    status_text = fig.text(0.02, 0.98, "Waiting for data...",
                           fontsize=10, color="#8b949e", va="top")

    fig.subplots_adjust(left=0.08, right=0.97, top=0.95, bottom=0.06, hspace=0.45)

    # Pre-allocate scratch arrays so we don't allocate every frame
    _padded = np.zeros((WINDOW_SIZE, NUM_SUBCARRIERS), dtype=np.float32)
    _bar = np.full((1, WINDOW_SIZE, 3), _COLOR_EMPTY, dtype=np.uint8)

    # Track previous axis limits to avoid unnecessary rescaling
    _prev_clim = [0.0, 40.0]
    _prev_ylim2 = [0.0, 50.0]
    _prev_ylim4 = [0.0, 5.0]

    def animate(_frame):
        snap = store.snapshot()
        if snap is None:
            return []

        n = len(snap["scores"])
        if n < 2:
            return []

        amps = snap["amplitudes"]      # shape (n, 64)
        states = snap["states"]
        scores = snap["scores"]

        # ── 1. Heatmap ──
        _padded[:] = 0
        if n < WINDOW_SIZE:
            _padded[-n:] = amps
        else:
            _padded[:] = amps[-WINDOW_SIZE:]
        heatmap_img.set_data(_padded.T)

        # Clim: use simple max instead of expensive percentile
        new_vmax = max(float(np.max(_padded)) * 0.9, 10.0)
        if abs(new_vmax - _prev_clim[1]) > 2.0:
            heatmap_img.set_clim(0, new_vmax)
            _prev_clim[1] = new_vmax

        # ── 2. Time-series ──
        x = np.arange(n)
        for i, sc in enumerate(HIGHLIGHT_SC):
            ts_lines[i].set_data(x, amps[:, sc])

        new_xlim = max(n, WINDOW_SIZE)
        ax2.set_xlim(0, new_xlim)
        new_ymax2 = max(float(np.max(amps[:, HIGHLIGHT_SC])) * 1.2, 10.0)
        if abs(new_ymax2 - _prev_ylim2[1]) > 3.0:
            ax2.set_ylim(0, new_ymax2)
            _prev_ylim2[1] = new_ymax2

        # ── 3. Motion bar (vectorized) ──
        _bar[0, :] = _COLOR_EMPTY
        offset = max(0, WINDOW_SIZE - n)
        recent = states[-WINDOW_SIZE:]
        for i, s in enumerate(recent):
            _bar[0, offset + i] = _COLOR_MOTION if s == "MOTION" else _COLOR_IDLE
        motion_img.set_data(_bar)

        # ── 4. Score ──
        score_line.set_data(np.arange(n), scores)
        ax4.set_xlim(0, new_xlim)
        new_ymax4 = min(max(max(scores) * 1.5, 2.0), 20.0)
        if abs(new_ymax4 - _prev_ylim4[1]) > 1.0:
            ax4.set_ylim(0, new_ymax4)
            _prev_ylim4[1] = new_ymax4

        # ── Status line ──
        nm = sum(1 for s in states if s == "MOTION")
        rssi = snap["rssi"][-1] if snap["rssi"] else 0
        status_text.set_text(
            f"Pkts: {snap['count']:,}  |  RSSI: {rssi}dBm  |  MOTION: {nm}  IDLE: {n-nm}"
        )

        return [heatmap_img, motion_img, score_line, status_text] + ts_lines

    # Use blit=False but with a fast interval.
    # On TkAgg (Windows), blit=True can cause rendering glitches with imshow,
    # so we keep blit=False but compensate with a lighter animate() function.
    anim = FuncAnimation(
        fig, animate,
        interval=UPDATE_INTERVAL_MS,
        blit=False,
        cache_frame_data=False,
        save_count=0,
    )

    def on_close(event):
        stop_event.set()
    fig.canvas.mpl_connect("close_event", on_close)

    try:
        plt.show()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()


# ──────────────────────────── Main ────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ESPectre — Real-Time CSI Visualizer")
    parser.add_argument("--port", type=str, default=None, help="Serial port")
    parser.add_argument("--baud", type=int, default=BAUD_RATE, help="Baud rate")
    args = parser.parse_args()

    port = args.port
    if port is None:
        print("🔍 Auto-detecting serial port...")
        port = auto_detect_port()
        if port is None:
            print("❌  No serial port found. Connect your ESP32 and try again.")
            sys.exit(1)
        print(f"   Found: {port}")

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║    ESPectre — Real-Time CSI Viewer              ║")
    print("║    Close the window or press Ctrl+C to quit     ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    store = CSIDataStore(maxlen=WINDOW_SIZE)
    stop_event = threading.Event()

    reader = threading.Thread(target=serial_reader,
                              args=(port, args.baud, store, stop_event), daemon=True)
    reader.start()

    run_dashboard(store, stop_event)

    stop_event.set()
    reader.join(timeout=2)
    print("\n👋 Viewer closed.")


if __name__ == "__main__":
    main()
