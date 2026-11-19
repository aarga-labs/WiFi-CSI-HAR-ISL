#!/usr/bin/env python3
"""Generate one standard Wi-Fi probe once; continuously stream it at 200 packets/s."""
import argparse
import json
import hashlib
import platform
import secrets
import subprocess
import threading
from pathlib import Path
import signal
import time

import numpy as np
from gnuradio import blocks, gr, uhd
import foo
import ieee802_11
import pmt
from wifi_phy_hier import wifi_phy_hier

SAMPLE_RATE = 20_000_000
PPS = 200
FREQUENCY = 2_412_000_000


def make_waveform():
    """Use the existing encoder/MAC/padding, then stop that graph completely."""
    tb = gr.top_block('Build one Wi-Fi probe without opening any USRP')
    phy = wifi_phy_hier(bandwidth=SAMPLE_RATE, chan_est=ieee802_11.LS,
                       encoding=ieee802_11.BPSK_1_2, frequency=FREQUENCY, sensitivity=.56)
    # This hierarchy contains a receive path. Its dummy input is not radio data.
    zero = blocks.vector_source_c((0, 0, 0), True)
    slow = blocks.throttle(gr.sizeof_gr_complex, 1000, True)
    slow.set_max_noutput_items(100)
    mac = ieee802_11.mac([2, 0, 0, 0, 0, 1], [2, 0, 0, 0, 0, 2], [255]*6)
    scale = blocks.multiply_const_cc(.8)
    pad = foo.packet_pad2(False, False, .001, 10000, 1000)
    pad.set_min_output_buffer(98304)
    sink = blocks.vector_sink_c()
    tb.connect(zero, slow, phy, scale, pad, sink)
    tb.msg_connect((mac, 'phy out'), (phy, 'mac_in'))
    tb.msg_connect((phy, 'mac_out'), (mac, 'phy in'))
    payload = b'FYP_FIXED_CSI_PROBE;'+b'X'*(100-len(b'FYP_FIXED_CSI_PROBE;'))
    tb.start()
    try:
        mac.to_basic_block()._post(pmt.intern('app in'),
            pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(payload), list(payload))))
        deadline = time.monotonic()+5
        while len(sink.data()) == 0 and time.monotonic() < deadline:
            time.sleep(.005)
    finally:
        tb.stop()
        tb.wait()
    packet = np.asarray(sink.data(), dtype=np.complex64)
    tags = [(t.offset, pmt.to_long(t.value)) for t in sink.tags()
            if pmt.symbol_to_string(t.key) == 'packet_len']
    if tags != [(0, len(packet))] or not 0 < len(packet) < SAMPLE_RATE//PPS:
        raise RuntimeError('Probe encoding/length check failed. No radio was opened.')
    if not np.isfinite(packet).all() or not np.any(packet):
        raise RuntimeError('Probe waveform is invalid. No radio was opened.')
    waveform = np.zeros(SAMPLE_RATE//PPS, dtype=np.complex64)
    waveform[:len(packet)] = packet
    # OFDM has large peaks. The legacy 0.8 multiplier alone produces I/Q
    # components beyond UHD's normalized fullscale of 1.0. Normalize the
    # complete encoded probe and leave 6dB of complex-envelope headroom.
    waveform *= np.float32(.5 / np.max(np.abs(waveform)))
    if max(np.abs(waveform.real).max(), np.abs(waveform.imag).max()) > .500001:
        raise RuntimeError('Baseband headroom check failed. No radio opened.')
    return waveform, len(packet)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--addr', default='192.168.10.9')
    ap.add_argument('--gain', type=float, default=30)
    ap.add_argument('--build-only', action='store_true', help='Verify the waveform; do not open hardware.')
    args = ap.parse_args()
    if not 0 <= args.gain <= 31.5:
        ap.error('Use gain between 0 and 31.5 dB.')
    waveform, packet_length = make_waveform()
    settings = dict(tx_address=args.addr, sample_rate=SAMPLE_RATE, frequency_hz=FREQUENCY,
                    tx_gain_db=args.gain, packets_per_second=PPS,
                    period_samples=len(waveform), padded_packet_samples=packet_length,
                    baseband_complex_peak=float(np.abs(waveform).max()),
                    baseband_max_i=float(np.abs(waveform.real).max()),
                    baseband_max_q=float(np.abs(waveform.imag).max()),
                    source='fixed standard Wi-Fi frame with continuous zero-filled gaps',
                    mac_sequence_repeats=True, payload_timestamps_present=False,
                    note='Receiver host timestamps and laptop cue labels remain authoritative; do not use this fixed payload as a packet clock.')
    print(json.dumps(settings, indent=2), flush=True)
    if args.build_only:
        print('WAVEFORM VERIFIED. No USRP opened.', flush=True)
        return 0
    tb = gr.top_block('Continuous fixed Wi-Fi CSI transmitter')
    source = blocks.vector_source_c(waveform.tolist(), True, 1, [])
    source.set_min_output_buffer(1_048_576)
    # Continuous mode is correct here: every sample, including the gaps, is supplied.
    radio = uhd.usrp_sink(f'addr={args.addr},num_send_frames=256',
                          uhd.stream_args(cpu_format='fc32', channels=[0]), '')
    radio.set_clock_source('internal', 0)
    radio.set_samp_rate(SAMPLE_RATE)
    radio.set_center_freq(FREQUENCY, 0)
    radio.set_antenna('TX/RX', 0)
    radio.set_bandwidth(SAMPLE_RATE, 0)
    radio.set_gain(args.gain, 0)
    tb.connect(source, radio)
    settings.update(gnuradio=gr.version(), kernel=platform.release(),
                    transmitter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    waveform_sha256=hashlib.sha256(waveform.tobytes()).hexdigest(),
                    effective_rate=radio.get_samp_rate(),effective_gain=radio.get_gain(0),
                    effective_frequency=radio.get_center_freq(0),effective_bandwidth=radio.get_bandwidth(0),
                    effective_antenna=radio.get_antenna(0),effective_clock=radio.get_clock_source(0),
                    uhd=subprocess.check_output(['uhd_config_info','--version'],text=True).strip())
    class AsyncEvents(gr.basic_block):
        def __init__(self):
            super().__init__(name='tx_health',in_sig=None,out_sig=None)
            self.lock=threading.Lock()
            self.count=0
            self.recent=[]
            port=pmt.intern('events')
            self.message_port_register_in(port)
            self.set_msg_handler(port,self.receive)

        def receive(self,message):
            with self.lock:
                self.count+=1
                self.recent=(self.recent+[dict(epoch_ns=time.time_ns(),message=pmt.write_string(message))])[-10:]

    events=AsyncEvents()
    has_async='async_msgs' in pmt.write_string(radio.message_ports_out())
    if has_async:
        tb.msg_connect((radio,'async_msgs'),(events,'events'))
    settings['uhd_async_port_available']=has_async
    logs = Path(__file__).resolve().parent/'logs'
    logs.mkdir(exist_ok=True)
    dest = logs/('stable_tx_'+time.strftime('%Y%m%d_%H%M%S')+'_'+secrets.token_hex(3)+'.json')
    def save_status():
        with events.lock:
            settings['async_message_count']=events.count if has_async else None
            settings['recent_async_messages']=list(events.recent)
        settings['updated_epoch_ns']=time.time_ns()
        temp=dest.with_suffix('.tmp')
        temp.write_text(json.dumps(settings,indent=2)+'\n')
        temp.replace(dest)
    save_status()
    stopped = [False]
    signal.signal(signal.SIGINT, lambda *_: stopped.__setitem__(0, True))
    signal.signal(signal.SIGTERM, lambda *_: stopped.__setitem__(0, True))
    started = time.monotonic()
    tb.start()
    print(f'STABLE TX RUNNING: channel 1, 20 MHz, gain {args.gain:g}, 200 packets/s; baseband peak 0.5.', flush=True)
    print('No separate packet generator is needed. Keep this terminal open. Ctrl+C stops TX.', flush=True)
    try:
        next_report=started+5
        while not stopped[0]:
            time.sleep(.25)
            if time.monotonic()>=next_report:
                save_status()
                next_report=time.monotonic()+5
    finally:
        tb.stop()
        tb.wait()
        settings['stopped_after_s'] = time.monotonic()-started
        save_status()
        print('TX stopped cleanly.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
