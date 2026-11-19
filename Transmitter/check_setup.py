"""Validate imported private TX modules without opening a USRP."""
from pathlib import Path
import sys
from gnuradio import gr, uhd, qtgui, network
from PyQt5 import Qt
import foo
import ieee802_11
from wifi_phy_hier import wifi_phy_hier

root=Path(__file__).resolve().parent
for module,attrs in [(foo,['packet_pad2']),(ieee802_11,['mac','mapper','sync_short','sync_long','frame_equalizer','signal_field'])]:
    assert Path(module.__file__).resolve().is_relative_to(root/'install'), 'Build the private TX modules with bash BUILD.sh'
    for attr in attrs:
        assert hasattr(module,attr), f'Missing {module.__name__}.{attr}'
assert gr.version().startswith('3.10.'), 'Use GNU Radio 3.10.x'
print('TX imports verified. No USRP opened.')
