#!/usr/bin/env python3
"""Preserved receiver DSP without the two live plotting branches, with diagnostics."""
import argparse
import cmath
from collections import deque
import json
import math
import os
from pathlib import Path
import re
import socket
import signal
import sys
import threading
import time
from capture_paths import RECEIVER_EXAMPLES

ROOT = Path(__file__).resolve().parent


def read_value(path, convert=str):
    try:
        return convert(Path(path).read_text().strip())
    except (OSError, ValueError):
        return None


def radio_sockets(address):
    """Read the actual buffers on this child's connected radio sockets."""
    found = []
    for fd in Path('/proc/self/fd').iterdir():
        try:
            with socket.fromfd(int(fd.name),socket.AF_INET,socket.SOCK_DGRAM) as sock:
                peer = sock.getpeername()
                if isinstance(peer,tuple) and peer[0] == address:
                    found.append(dict(peer_port=peer[1],
                        receive_bytes=sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF),
                        send_bytes=sock.getsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF)))
        except OSError:
            continue
    return found


def laptop_sensors(interface):
    paths = {
        'nic_rx_dropped': (Path('/sys/class/net')/interface/'statistics/rx_dropped', int),
        'nic_rx_errors': (Path('/sys/class/net')/interface/'statistics/rx_errors', int),
        'link_mbps': (Path('/sys/class/net')/interface/'speed', int),
        'ac_online': ('/sys/class/power_supply/AC/online', int),
        'platform_profile': ('/sys/firmware/acpi/platform_profile', str),
        'governor': ('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', str),
        'cpu_freq_khz': ('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', int),
        'cpu_max_perf_pct': ('/sys/devices/system/cpu/intel_pstate/max_perf_pct', int),
    }
    for chip in Path('/sys/class/hwmon').glob('hwmon*'):
        if read_value(chip/'name') == 'alienware_wmi':
            for label in chip.glob('fan*_label'):
                name = read_value(label)
                if name:
                    paths[name.lower().replace(' ', '_') + '_rpm'] = (
                        label.with_name(label.name.replace('_label','_input')), int)
    return paths


def host_snapshot():
    out = {'epoch_ns': time.time_ns(), 'monotonic_ns': time.monotonic_ns()}
    lines = Path('/proc/net/snmp').read_text().splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.startswith('Udp:'):
            out['udp'] = dict(zip(line.split()[1:], map(int, lines[i+1].split()[1:])))
            break
    out['temperature_c'] = {}
    for zone in Path('/sys/class/thermal').glob('thermal_zone*'):
        try:
            name = (zone/'type').read_text().strip()
            if name in ('x86_pkg_temp', 'TCPU', 'TCPU_PCI'):
                out['temperature_c'][name] = int((zone/'temp').read_text()) / 1000
        except OSError:
            pass
    throttle = Path('/sys/devices/system/cpu/cpu0/thermal_throttle')
    out['thermal_throttle'] = {}
    for name in ('package_throttle_count', 'package_throttle_total_time_ms',
                 'core_throttle_count', 'core_throttle_total_time_ms'):
        try:
            out['thermal_throttle'][name] = int((throttle/name).read_text())
        except OSError:
            pass
    fields = Path('/proc/self/stat').read_text().split()
    out['process_cpu_ticks'] = int(fields[13])+int(fields[14])
    return out


def configure_capture_graph(tb, notch_hz, notch_pole):
    from gnuradio import filter
    # These three connections are display-only branches in the original graph.
    # All source, synchronization, FFT, equalization, decode, parse and CSV paths remain.
    tb.disconnect((tb.blocks_divide_xx_0, 0), (tb.qtgui_time_sink_x_0, 0))
    tb.msg_disconnect((tb.ieee802_11_frame_equalizer_0, 'symbols'), (tb.pdu_pdu_to_tagged_stream_0, 'pdus'))
    tb.disconnect((tb.pdu_pdu_to_tagged_stream_0, 0), (tb.qtgui_const_sink_x_0, 0))
    if notch_hz is not None:
        if not 0 < notch_pole < 1 or abs(float(notch_hz)) >= tb.samp_rate/2:
            raise ValueError('Invalid calibrated receiver notch setting.')
        z = cmath.exp(2j*math.pi*float(notch_hz)/tb.samp_rate)
        # Narrow notch at the measured unwanted carrier, inside the unused
        # Wi-Fi DC region. Raw captures and the offline same-input comparison
        # document this frontend change; it is not applied to old recordings.
        tb.frontend_carrier_notch = filter.iir_filter_ccc([1, -z], [1, -notch_pole*z], False)
        for target, port in [(tb.blocks_complex_to_mag_squared_0, 0),
                             (tb.blocks_delay_0_0, 0), (tb.blocks_multiply_xx_0, 0)]:
            tb.disconnect((tb.uhd_usrp_source_0, 0), (target, port))
            tb.connect((tb.frontend_carrier_notch, 0), (target, port))
        tb.connect((tb.uhd_usrp_source_0, 0), (tb.frontend_carrier_notch, 0))
        print(f'Calibrated narrow frontend notch: {float(notch_hz):.3f} Hz; pole radius {notch_pole}.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, help='Diagnostic only: stop after this duration.')
    parser.add_argument('--gain-sequence', help='Diagnostic only: comma-separated gains, never used by named recordings.')
    parser.add_argument('--phase-seconds', type=float, default=25)
    args = parser.parse_args()
    if args.seconds is not None and args.seconds <= 0:
        parser.error('--seconds must be positive')
    gains = [float(x) for x in args.gain_sequence.split(',')] if args.gain_sequence else []
    if gains and (args.phase_seconds <= 3 or any(not 0 <= x <= 31.5 for x in gains)):
        parser.error('Use phases longer than three seconds and gains between 0 and 31.5 dB.')
    from PyQt5 import Qt
    from gnuradio import gr, blocks, filter
    import pmt
    sys.path.insert(0, str(RECEIVER_EXAMPLES))
    from wifi_rx import wifi_rx

    class HealthMessages(gr.basic_block):
        def __init__(self):
            gr.basic_block.__init__(self, name='capture_health', in_sig=None, out_sig=None)
            self.lock = threading.Lock()
            self.checked = self.bad_crc = self.target_frames = self.other_frames = 0
            self.snr = deque(maxlen=1000)
            self.async_events = deque(maxlen=50)
            self.overflows = None
            self.sequence = None
            for port, callback in [('parsed', self.parsed), ('crc', self.crc), ('uhd', self.uhd)]:
                self.message_port_register_in(pmt.intern(port))
                self.set_msg_handler(pmt.intern(port), callback)

        @staticmethod
        def field(meta, key):
            value = pmt.dict_ref(meta, pmt.intern(key), pmt.PMT_NIL)
            if pmt.is_null(value):
                return None
            return pmt.to_python(value)

        def parsed(self, message):
            if not pmt.is_pair(message):
                return
            meta = pmt.car(message)
            ta = self.field(meta, 'address 2') or self.field(meta, 'ta')
            ra = self.field(meta, 'address 1') or self.field(meta, 'ra')
            match = str(ta).lower() == os.environ['CSI_TA'].lower() and str(ra).lower() == os.environ['CSI_RA'].lower()
            with self.lock:
                if not match:
                    self.other_frames += 1
                    return
                self.target_frames += 1
                value = self.field(meta, 'snr')
                if value is not None and math.isfinite(float(value)):
                    self.snr.append(float(value))
                self.sequence = self.field(meta, 'sequence number')

        def crc(self, message):
            with self.lock:
                self.checked = int(self.field(message, 'checked'))
                self.bad_crc = int(self.field(message, 'bad_crc'))

        def uhd(self, message):
            with self.lock:
                description = pmt.write_string(message)
                self.async_events.append(description)
                match = re.search(r'\(overflows\s+\.\s+(\d+)\)', description)
                if match:
                    self.overflows += int(match.group(1))

        def snapshot(self):
            with self.lock:
                values = sorted(self.snr)
                return dict(decoded_frames_checked=self.checked, bad_crc_frames=self.bad_crc,
                            target_crc_valid_frames=self.target_frames, other_crc_valid_frames=self.other_frames,
                            target_recent_snr_median_db=values[len(values)//2] if values else None,
                            target_recent_snr_min_db=min(values) if values else None,
                            uhd_overflows=self.overflows, latest_target_sequence=self.sequence, uhd_async_events=list(self.async_events))

    app = Qt.QApplication([])
    tb = wifi_rx()
    setup_path = ROOT/'COLLECTION_SETUP.json'
    setup = json.loads(setup_path.read_text()) if setup_path.exists() else {}
    notch_hz = setup.get('receiver_frontend_notch_hz')
    notch_pole = float(setup.get('receiver_frontend_notch_pole_radius', .9995))
    configure_capture_graph(tb, notch_hz, notch_pole)
    monitor = HealthMessages()
    tb.msg_connect((tb.ieee802_11_parse_mac_0, 'out'), (monitor, 'parsed'))
    ports = pmt.write_string(tb.ieee802_11_decode_mac_0.message_ports_out())
    if 'rx_stats' in ports:
        tb.msg_connect((tb.ieee802_11_decode_mac_0, 'rx_stats'), (monitor, 'crc'))
    if 'async_msgs' in pmt.write_string(tb.uhd_usrp_source_0.message_ports_out()):
        monitor.overflows = 0
        tb.msg_connect((tb.uhd_usrp_source_0, 'async_msgs'), (monitor, 'uhd'))
    tb.ieee802_11_extract_csi_0.set_channel(1)
    power_probe = blocks.probe_signal_f()
    tb.connect((tb.blocks_moving_average_xx_0, 0), (power_probe, 0))
    output = Path(os.environ['CSI_OUT']).parent/'receiver_health.jsonl'
    print('Capture mode: original DSP, display branches disconnected; receiver_health.jsonl enabled', flush=True)
    radio = tb.uhd_usrp_source_0
    effective = dict(rate=radio.get_samp_rate(), frequency_hz=radio.get_center_freq(0),
                     gain_db=radio.get_gain(0), antenna=radio.get_antenna(0),
                     bandwidth_hz=radio.get_bandwidth(0), clock=radio.get_clock_source(0),
                     notch_hz=notch_hz, notch_pole_radius=notch_pole)
    effective['udp_sockets'] = radio_sockets(os.environ['RX_ADDR'])
    with (output.parent/'effective_rx.json').open('x') as f:
        json.dump(effective, f, indent=2)
    package_limit_c = None
    for label in Path('/sys/class/hwmon').glob('hwmon*/temp*_label'):
        if read_value(label)=='Package id 0':
            limit=read_value(label.with_name(label.name.replace('_label','_crit')),int)
            package_limit_c=limit/1000 if limit else None
            break
    thermal_window=deque()
    sensors = laptop_sensors(os.environ.get('CSI_INTERFACE', ''))
    started = time.monotonic()
    with output.open('x') as log:
        def tick():
            row = host_snapshot()
            row.update(monitor.snapshot())
            row.update({key: read_value(path, convert) for key, (path, convert) in sensors.items()})
            row['rx_gain_db'] = tb.uhd_usrp_source_0.get_gain(0)
            row['recent_input_power_estimate'] = float(power_probe.level()) / (tb.window_size+16)
            row['package_critical_c']=package_limit_c
            # End unattended *bench* runs if the CPU spends most of 30 s at its
            # own critical limit and is actively throttling. Keep participant cues intact.
            now=time.monotonic()
            temp=row['temperature_c'].get('x86_pkg_temp')
            if args.seconds and package_limit_c and temp is not None:
                throttle_ms = row['thermal_throttle'].get('package_throttle_total_time_ms', 0)
                thermal_window.append((now,temp,throttle_ms))
                while thermal_window and thermal_window[0][0]<now-31:
                    thermal_window.popleft()
                if (now-thermal_window[0][0]>=29 and thermal_window[-1][2]>thermal_window[0][2]
                        and sum(t>=package_limit_c for _,t,_ in thermal_window)>=20):
                    row['bench_stop_reason']='sustained CPU critical temperature with active throttling'
                    print(row['bench_stop_reason'],flush=True)
                    app.quit()
            log.write(json.dumps(row)+'\n')
            log.flush()
            if args.seconds is not None and time.monotonic()-started >= args.seconds:
                app.quit()
        timer = Qt.QTimer()
        timer.timeout.connect(tick)
        signal.signal(signal.SIGINT, lambda *_: app.quit())
        signal.signal(signal.SIGTERM, lambda *_: app.quit())
        try:
            if gains:
                tb.uhd_usrp_source_0.set_gain(gains[0], 0)
                def next_gain():
                    index = int((time.monotonic()-started)//args.phase_seconds)
                    if index >= len(gains):
                        app.quit()
                        return
                    tb.uhd_usrp_source_0.set_gain(gains[index], 0)
                gain_timer = Qt.QTimer()
                gain_timer.timeout.connect(next_gain)
                gain_timer.start(100)
            tick()
            tb.start()
            tb.flowgraph_started.set()
            timer.start(1000)
            app.exec_()
        finally:
            timer.stop()
            if gains:
                gain_timer.stop()
            tb.stop()
            tb.wait()
            if not tb.ieee802_11_extract_csi_0.stop():
                raise OSError('CSI output flush failed')
            tick()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
