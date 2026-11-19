#!/usr/bin/env python3
"""Correct packet-burst signaling and remove debug sinks; no RF setting changes."""
import ast
from pathlib import Path
import time


def patch(source):
    tree = ast.parse(source)
    sinks = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'usrp_sink']
    if len(sinks) != 1 or len(sinks[0].args) != 3:
        raise ValueError('Unexpected USRP sink layout; file left unchanged.')
    tag = sinks[0].args[2]
    if not isinstance(tag, ast.Constant) or tag.value not in ('', 'packet_len'):
        raise ValueError('Unexpected burst tag setting; file left unchanged.')
    lines = source.splitlines(keepends=True)
    if tag.value == '':
        line = lines[tag.lineno-1]
        lines[tag.lineno-1] = line[:tag.col_offset]+'"packet_len"'+line[tag.end_col_offset:]
    lines = [line for line in lines if not ('self.msg_connect(' in line and 'self.blocks_message_debug_' in line)]
    result = ''.join(lines)
    old = '        self.connect((self.blocks_vector_source_x_0, 0), (self.wifi_phy_hier_0, 0))'
    if 'blocks_throttle_rx_dummy_0' not in result:
        if old not in result:
            raise ValueError('Unexpected dummy receive branch; file left unchanged.')
        new = '''        # The TX hierarchy's unused receiver gets only rate-limited dummy zeros.
        self.blocks_throttle_rx_dummy_0 = blocks.throttle(gr.sizeof_gr_complex, 1000, True)
        self.blocks_throttle_rx_dummy_0.set_max_noutput_items(100)
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_throttle_rx_dummy_0, 0), (self.wifi_phy_hier_0, 0))'''
        result = result.replace(old, new)
    check = ast.parse(result)
    sink = next(node for node in ast.walk(check) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute) and node.func.attr == 'usrp_sink')
    assert sink.args[2].value == 'packet_len'
    return result


def main():
    path = Path(__file__).resolve().parent/'source/gr-ieee802-11/examples/wifi_tx_multi_hop.py'
    original = path.read_text()
    updated = patch(original)
    if updated != original:
        backup = path.with_name(path.name+'.before_burst_fix_'+time.strftime('%Y%m%d_%H%M%S'))
        with backup.open('x') as f:
            f.write(original)
        temporary = path.with_suffix('.py.tmp')
        temporary.write_text(updated)
        temporary.replace(path)
        print('Saved original:', backup)
    print('TX burst-length tag: packet_len. Packet debug branches disconnected.')
    print('Unused dummy receive chain rate-limited; actual transmit sample rate remains 20 MHz.')
    print('RF channel, gain, sample rate, payload and packet cadence are unchanged. No rebuild required.')


if __name__ == '__main__':
    main()
