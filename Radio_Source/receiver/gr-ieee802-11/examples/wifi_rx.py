#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Wifi Rx
# GNU Radio version: 3.10.11.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
from gnuradio import uhd
import time
import ieee802_11
import os
import sip
import threading
from datetime import datetime


# Wi-Fi 2.4 GHz non-overlapping channels, and how long to dwell on each.
# Must match the transmitter's CHANNELS/DWELL_TIME in wifi_tx_multi_hop.py.
CHANNELS = {
    1: 2412e6,
    6: 2437e6,
    11: 2462e6,
}

DWELL_TIME = 0.5

# Ordered channel list for wall-clock-synchronized hopping. Both TX and RX
# derive the current slot from time.time(), so two independently started
# processes land on the same channel without any message passing between them.
# This mirrors current_hop_channel() in wifi_tx_multi_hop.py exactly — if you
# change one, change the other. Requires both laptops within ~50 ms (NTP).
CHANNELS_ORDER = [(1, 2412e6), (6, 2437e6), (11, 2462e6)]


def current_hop_channel():
    """Return (channel_number, freq_hz) for the current wall-clock slot."""
    slot = int(time.time() / DWELL_TIME) % len(CHANNELS_ORDER)
    return CHANNELS_ORDER[slot]


def _env_channel():
    """
    Resolve CSI_CHANNEL into a parked channel number, or None to hop.

    Unset / empty / "hop" means hop. A channel number parks. ANYTHING else is
    a typo (CSI_CHANNEL=ch6, =2, =eleven) and aborts rather than silently
    hopping — a run that quietly hops when you meant to park produces a CSV
    that looks fine and is unusable, which is the single most expensive
    failure mode in this project. Fail at startup instead.
    """
    raw = os.environ.get("CSI_CHANNEL", "").strip()

    if raw in ("", "hop"):
        return None

    try:
        chan = int(raw)
    except ValueError:
        chan = None

    if chan not in CHANNELS:
        sys.exit(
            f"CSI_CHANNEL must be one of {sorted(CHANNELS)} (or 'hop'/unset "
            f"to hop) — got '{raw}'.\n"
            f"Park the transmitter on the same channel with TX_CHANNEL."
        )

    return chan


# CSI_CHANNEL=1|6|11 parks the receiver on one channel for the whole run.
# Unset (or "hop") keeps hopping 1 -> 6 -> 11 every DWELL_TIME.
#
# ALWAYS park for activity-recognition captures, and park the transmitter on
# the SAME channel (TX_CHANNEL). Hopping measures out at ~2.4 Hz of CSI against
# the ~50 Hz human motion needs — 0 of 854 windows usable in a 28-minute
# capture. The cost is not channel alignment (two loops share a channel ~1/3 of
# the time, the same as a parked RX would) but per-hop settling: ~60 ms of every
# 100 ms dwell goes to retune plus OFDM re-sync, on each side. Shorter dwells
# make that worse, not better. See doc/THREE_CHANNEL_ANALYSIS.md.
PARKED_CHANNEL = _env_channel()

# Which USRP to open, and how much RX gain to apply.
#
# NOTE ON THE ADDRESS: the receiver USRP is at .9 and the transmitter's is at
# .7 — this is the reverse of what older revisions of RECEIVER.md claimed. The
# value below is the one that produced every working capture in doc/. If your
# hardware differs, set RX_ADDR rather than editing this file:
#     RX_ADDR=192.168.10.7 python3 wifi_rx.py
# Run ../preflight.sh to see which USRPs actually answer on this machine.
RX_ADDR = os.environ.get("RX_ADDR", "192.168.10.9").strip()

# RX_GAIN is the main lever for weak signals. Hand gestures perturb the channel
# far less than whole-body motion, so gesture captures may need more gain than
# walking does. Too much gain saturates the front end and flattens the CSI;
# sweep it in a pilot rather than guessing. 0-31.5 dB useful range on SBX.
RX_GAIN = float(os.environ.get("RX_GAIN", "50"))


class wifi_rx(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Wifi Rx", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Wifi Rx")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "wifi_rx")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.window_size = window_size = 48
        self.sync_length = sync_length = 320
        self.samp_rate = samp_rate = 20e6
        self.lo_offset = lo_offset = 0
        self.gain = gain = RX_GAIN
        # Start already tuned to the parked channel so a parked capture never
        # retunes at all. capture.sh restarts this flowgraph once per instance,
        # so a retune here would cost LO settling + OFDM re-sync at the head of
        # every single recording — exactly the samples the subject is moving in.
        self.freq = freq = CHANNELS[PARKED_CHANNEL] if PARKED_CHANNEL else 2412000000
        self.chan_est = chan_est = 0

        ##################################################
        # Blocks
        ##################################################

        # Create the options list
        self._chan_est_options = [0, 1, 2, 3]
        # Create the labels list
        self._chan_est_labels = ['LS', 'LMS', 'Linear Comb', 'STA']
        # Create the combo box
        # Create the radio buttons
        self._chan_est_group_box = Qt.QGroupBox("'chan_est'" + ": ")
        self._chan_est_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._chan_est_button_group = variable_chooser_button_group()
        self._chan_est_group_box.setLayout(self._chan_est_box)
        for i, _label in enumerate(self._chan_est_labels):
            radio_button = Qt.QRadioButton(_label)
            self._chan_est_box.addWidget(radio_button)
            self._chan_est_button_group.addButton(radio_button, i)
        self._chan_est_callback = lambda i: Qt.QMetaObject.invokeMethod(self._chan_est_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._chan_est_options.index(i)))
        self._chan_est_callback(self.chan_est)
        self._chan_est_button_group.buttonClicked[int].connect(
            lambda i: self.set_chan_est(self._chan_est_options[i]))
        self.top_layout.addWidget(self._chan_est_group_box)
        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join((f'addr={RX_ADDR}', "")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        # No synchronization enforced.

        self.uhd_usrp_source_0.set_center_freq(freq, 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_bandwidth(20e6, 0)
        self.uhd_usrp_source_0.set_gain(RX_GAIN, 0)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
            1024, #size
            samp_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(True)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_x_0_win)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            (48*10), #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.complex_t, 'packet_len')
        # Create the options list
        self._lo_offset_options = [0, 6000000.0, 11000000.0]
        # Create the labels list
        self._lo_offset_labels = ['0', '6000000.0', '11000000.0']
        # Create the combo box
        self._lo_offset_tool_bar = Qt.QToolBar(self)
        self._lo_offset_tool_bar.addWidget(Qt.QLabel("'lo_offset'" + ": "))
        self._lo_offset_combo_box = Qt.QComboBox()
        self._lo_offset_tool_bar.addWidget(self._lo_offset_combo_box)
        for _label in self._lo_offset_labels: self._lo_offset_combo_box.addItem(_label)
        self._lo_offset_callback = lambda i: Qt.QMetaObject.invokeMethod(self._lo_offset_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._lo_offset_options.index(i)))
        self._lo_offset_callback(self.lo_offset)
        self._lo_offset_combo_box.currentIndexChanged.connect(
            lambda i: self.set_lo_offset(self._lo_offset_options[i]))
        # Create the radio buttons
        self.top_layout.addWidget(self._lo_offset_tool_bar)
        self.ieee802_11_sync_short_0 = ieee802_11.sync_short(0.56, 2, False, False)
        self.ieee802_11_sync_long_0 = ieee802_11.sync_long(sync_length, False, False)
        self.ieee802_11_parse_mac_0 = ieee802_11.parse_mac(False, False)
        self.ieee802_11_frame_equalizer_0 = ieee802_11.frame_equalizer(ieee802_11.Equalizer(chan_est), freq, samp_rate, False, False)
        self.ieee802_11_extract_csi_0 = ieee802_11.extract_csi()
        self.ieee802_11_decode_mac_0 = ieee802_11.decode_mac(False, False)
        # RX gain in dB, live-adjustable. Previously this slider ran 0-1 and was
        # wired to a set_gain() that only stored the value — it did nothing at
        # all, while the real gain sat hardcoded at 50. It now drives the USRP,
        # which makes it the fastest way to find the right gain during a pilot.
        self._gain_range = qtgui.Range(0, 60, 0.5, RX_GAIN, 200)
        self._gain_win = qtgui.RangeWidget(self._gain_range, self.set_gain, "RX gain (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._gain_win)
        self.fft_vxx_0 = fft.fft_vcc(64, True, window.rectangular(64), True, 1)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 64)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_gr_complex*52)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_moving_average_xx_1 = blocks.moving_average_cc(window_size, 1, 4000, 1)
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff((window_size  + 16), 1, 4000, 1)
        self.blocks_divide_xx_0 = blocks.divide_ff(1)
        self.blocks_delay_0_0 = blocks.delay(gr.sizeof_gr_complex*1, 16)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_gr_complex*1, sync_length)
        self.blocks_conjugate_cc_0 = blocks.conjugate_cc()
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.ieee802_11_decode_mac_0, 'out'), (self.ieee802_11_parse_mac_0, 'in'))
        self.msg_connect((self.ieee802_11_frame_equalizer_0, 'symbols'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.ieee802_11_parse_mac_0, 'out'), (self.ieee802_11_extract_csi_0, 'pdu in'))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_conjugate_cc_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.blocks_delay_0, 0), (self.ieee802_11_sync_long_0, 1))
        self.connect((self.blocks_delay_0_0, 0), (self.blocks_conjugate_cc_0, 0))
        self.connect((self.blocks_delay_0_0, 0), (self.ieee802_11_sync_short_0, 0))
        self.connect((self.blocks_divide_xx_0, 0), (self.ieee802_11_sync_short_0, 2))
        self.connect((self.blocks_divide_xx_0, 0), (self.qtgui_time_sink_x_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.blocks_moving_average_xx_1, 0), (self.blocks_complex_to_mag_0, 0))
        self.connect((self.blocks_moving_average_xx_1, 0), (self.ieee802_11_sync_short_0, 1))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_moving_average_xx_1, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.ieee802_11_frame_equalizer_0, 0))
        self.connect((self.ieee802_11_extract_csi_0, 0), (self.blocks_null_sink_0, 0))
        self.connect((self.ieee802_11_frame_equalizer_0, 0), (self.ieee802_11_decode_mac_0, 0))
        self.connect((self.ieee802_11_sync_long_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.ieee802_11_sync_short_0, 0), (self.blocks_delay_0, 0))
        self.connect((self.ieee802_11_sync_short_0, 0), (self.ieee802_11_sync_long_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_delay_0_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_multiply_xx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "wifi_rx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_window_size(self):
        return self.window_size

    def set_window_size(self, window_size):
        self.window_size = window_size
        self.blocks_moving_average_xx_0.set_length_and_scale((self.window_size  + 16), 1)
        self.blocks_moving_average_xx_1.set_length_and_scale(self.window_size, 1)

    def get_sync_length(self):
        return self.sync_length

    def set_sync_length(self, sync_length):
        self.sync_length = sync_length
        self.blocks_delay_0.set_dly(int(self.sync_length))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.ieee802_11_frame_equalizer_0.set_bandwidth(self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_lo_offset(self):
        return self.lo_offset

    def set_lo_offset(self, lo_offset):
        self.lo_offset = lo_offset
        self._lo_offset_callback(self.lo_offset)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.uhd_usrp_source_0.set_gain(self.gain, 0)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.ieee802_11_frame_equalizer_0.set_frequency(self.freq)
        self.uhd_usrp_source_0.set_center_freq(self.freq, 0)

    def get_chan_est(self):
        return self.chan_est

    def set_chan_est(self, chan_est):
        self.chan_est = chan_est
        self._chan_est_callback(self.chan_est)
        self.ieee802_11_frame_equalizer_0.set_algorithm(ieee802_11.Equalizer(self.chan_est))




def print_banner():
    """Print every effective setting before the USRP is opened.

    If the radio fails to open, this is the last thing on screen — which makes
    a wrong address or channel obvious instead of leaving a UHD backtrace to
    interpret.
    """
    mode = (f"PARKED on channel {PARKED_CHANNEL} "
            f"({CHANNELS[PARKED_CHANNEL]/1e6:.0f} MHz)"
            if PARKED_CHANNEL else
            f"HOPPING 1/6/11, {DWELL_TIME}s dwell (wall-clock synced)")

    print("=" * 62)
    print(" wifi_rx")
    print(f"   USRP address : {RX_ADDR}          (override: RX_ADDR=)")
    print(f"   RX gain      : {RX_GAIN} dB           (override: RX_GAIN=)")
    print(f"   mode         : {mode}")
    print(f"   TA filter    : {os.environ.get('CSI_TA', '(block default)')}")
    print(f"   RA filter    : {os.environ.get('CSI_RA', '(block default)')}")
    print(f"   CSV out      : {os.environ.get('CSI_OUT', '(block default)')}")
    if not PARKED_CHANNEL:
        print("   WARNING: hopping yields ~2.4 Hz CSI and is unusable for")
        print("            activity recognition. Set CSI_CHANNEL=1|6|11.")
    print("=" * 62)


def main(top_block_cls=wifi_rx, options=None):

    print_banner()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    hopping = threading.Event()
    hopping.set()

    def hop_channels():
        if PARKED_CHANNEL:
            # __init__ already tuned the USRP and the equalizer to this
            # channel, so there is deliberately no set_freq() here — retuning
            # now would throw away the settling we just avoided. All that is
            # left is to tell extract_csi how to label its rows: the block
            # defaults d_current_channel to 1, so parking on 6 or 11 without
            # this call would write a plausible-looking but wrong Channel
            # column.
            tb.ieee802_11_extract_csi_0.set_channel(PARKED_CHANNEL)

            print(
                f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                f"PARKED on Channel {PARKED_CHANNEL} "
                f"({CHANNELS[PARKED_CHANNEL]/1e6:.0f} MHz) — not hopping"
            )
            return

        # Wall-clock-synchronized hopping, identical to the transmitter's
        # current_hop_channel(). Both sides derive the slot from time.time(),
        # so they stay on the same channel without talking to each other —
        # unlike the previous free-running sleep() loop here, which drifted
        # against the TX from the moment it started.
        last_ch = None
        while hopping.is_set():
            ch_num, freq = current_hop_channel()

            if ch_num != last_ch:
                # Retune the USRP and the equalizer together...
                tb.set_freq(freq)

                # ...then tell extract_csi which channel its rows belong to,
                # so the Channel column tracks where we actually are.
                tb.ieee802_11_extract_csi_0.set_channel(ch_num)

                print(
                    f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                    f"Synced hop -> Channel {ch_num} ({freq/1e6:.0f} MHz)"
                )
                last_ch = ch_num

            time.sleep(0.01)  # poll every 10 ms

    hopper_thread = threading.Thread(target=hop_channels, daemon=True)
    hopper_thread.start()

    def sig_handler(sig=None, frame=None):
        hopping.clear()
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
