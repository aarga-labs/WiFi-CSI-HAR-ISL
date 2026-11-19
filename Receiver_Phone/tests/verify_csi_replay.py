"""Exercise the installed RX chain with known subcarrier gains and saved raw IQ. No radio."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from start_csi_rx import RECEIVER, clean_environment


def decode(work, name, samples, notch=None):
    from PyQt5 import Qt
    from gnuradio import blocks, gr, uhd
    from unittest.mock import patch
    from capture_receiver import configure_capture_graph
    sys.path.insert(0,str(RECEIVER.parent))
    from wifi_rx import wifi_rx

    csv_path = work/(name+'.csv')
    timing = work/(name+'_timing.csv')
    os.environ.update(CSI_OUT=str(csv_path),CSI_TIMING_OUT=str(timing))
    iq=work/(name+'.iq')
    with iq.open('wb') as stream:
        np.asarray(samples,dtype=np.complex64).tofile(stream)
        np.zeros(1_000_000,dtype=np.complex64).tofile(stream)
    class FileRadio(gr.hier_block2):
        def __init__(self,*args,**kwargs):
            gr.hier_block2.__init__(self,'replay',gr.io_signature(0,0,0),gr.io_signature(1,1,gr.sizeof_gr_complex))
            self.source=blocks.file_source(gr.sizeof_gr_complex,str(iq),False)
            self.pace=blocks.throttle(gr.sizeof_gr_complex,2_000_000,True)
            self.pace.set_max_noutput_items(2048)
            self.connect(self.source,self.pace,self)
        def set_samp_rate(self,*args): pass
        set_center_freq = set_antenna = set_bandwidth = set_gain = set_samp_rate

    with patch.object(uhd,'usrp_source',FileRadio):
        graph=wifi_rx()
    configure_capture_graph(graph,notch,.9995)
    graph.start()
    try:
        deadline=time.monotonic()+30
        while graph.ieee802_11_sync_short_0.nitems_read(0) < len(samples)+300000:
            if time.monotonic() >= deadline:
                raise RuntimeError('Replay timed out: '+name)
            time.sleep(.02)
        time.sleep(.25)
    finally:
        graph.stop()
        graph.wait()
        if not graph.ieee802_11_extract_csi_0.stop():
            raise OSError('CSI output flush failed')
    with csv_path.open() as f:
        rows=list(csv.DictReader(f))
    with timing.open() as f:
        clock=list(csv.DictReader(f))
    assert [r['Packet'] for r in rows] == [r['Packet'] for r in clock]
    assert all(int(b['Host_monotonic_ns'])>int(a['Host_monotonic_ns']) for a,b in zip(clock,clock[1:]))
    return np.asarray([[complex(float(r[f'SC{i}_Re']),float(r[f'SC{i}_Im'])) for i in range(52)] for r in rows])


def verify():
    from PyQt5 import Qt
    app=Qt.QApplication([])
    wave=np.load(ROOT/'build/stable_tx_waveform.npy')
    wave=wave*(.5/np.max(np.abs(wave)))
    base=np.tile(wave,20)
    # Thermal noise gives the detector a finite idle-power denominator.
    rng=np.random.default_rng(67)
    base += (rng.normal(size=len(base))+1j*rng.normal(size=len(base))).astype(np.complex64)*.005
    # Asymmetric complex echo gives the positive and negative bins distinct gains.
    taps=np.array([.78,0,.19+.16j,0,0,-.12j])
    bins=np.r_[np.arange(-26,0),np.arange(1,27)]
    expected=np.abs(np.fft.fft(taps,64)[bins % 64])
    with tempfile.TemporaryDirectory() as tmp:
        work=Path(tmp)
        flat=decode(work,'flat',base)
        echo=decode(work,'echo',np.convolve(base,taps)[:len(base)])
        assert flat.shape==echo.shape==(20,52),(flat.shape,echo.shape)
        relative=np.abs(echo)/np.abs(flat)
        error=float(np.max(np.abs(relative-expected)))
        assert error < .02,error
        print(f'Known channel: 20/20 flat and echo frames, all 52 bin gains checked; max amplitude-ratio error {error:.6f}.')
        raw=np.fromfile(ROOT/'diagnostics/raw_normalized_20261113_175258/iq.dat',dtype=np.complex64)
        setup=json.loads((ROOT/'COLLECTION_SETUP.json').read_text())
        before=decode(work,'before',raw)
        after=decode(work,'after',raw,setup['receiver_frontend_notch_hz'])
        assert len(before)==0 and after.shape==(49,52) and np.isfinite(after).all(),(before.shape,after.shape)
        print('Saved RF replay: 0 baseline / 49 calibrated frames. All packet IDs aligned with monotonic timestamps.')


if __name__=='__main__':
    if '--worker' in sys.argv:
        verify()
    else:
        env=clean_environment()
        env.update(QT_QPA_PLATFORM='offscreen',CSI_CHANNEL='1',CSI_DISABLE_PLOT_MESSAGES='1',
                   CSI_TA='02:00:00:00:00:01',CSI_RA='02:00:00:00:00:02')
        raise SystemExit(subprocess.call([sys.executable,__file__,'--worker'],env=env,cwd=ROOT))
