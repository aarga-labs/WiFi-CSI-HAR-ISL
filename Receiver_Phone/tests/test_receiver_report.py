import json
from pathlib import Path
import tempfile
import unittest

from receiver_report import capture_report


class ReceiverReportTest(unittest.TestCase):
    def test_preserves_partial_and_gap_evidence_on_trial_timeline(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            expected = ['Packet', 'Timestamp_us', 'Channel'] + [
                f'SC{index}_{part}' for index in range(52) for part in ('Re', 'Im')]
            payload = '1,0,' * 51 + '1,0'
            (folder / 'csi.csv').write_text(
                ','.join(expected) + '\n'
                + f'0,1000000,1,{payload}\n'
                + f'1,1150000,1,{payload}\n'
                + f'2,1155000,1,{payload}')
            (folder / 'host_timing.csv').write_text('Packet,Host_monotonic_ns\n0,300\n1,broken\n')
            rows = [
                dict(epoch_ns=1_000_000_000, monotonic_ns=1, udp={'RcvbufErrors': 0}),
                dict(epoch_ns=2_000_000_000, monotonic_ns=1_000_000_001, udp={'RcvbufErrors': 1}),
            ]
            (folder / 'receiver_health.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows))
            events = [dict(start_ns=1_100_000_000, end_ns=1_150_000_000, trial='gesture')]

            report = capture_report(folder, events)
            self.assertEqual(report['status'], 'review_required')
            self.assertEqual(report['rows'], 2)
            self.assertEqual(report['structure']['malformed_rows'], 1)
            self.assertFalse(report['timing_sidecar_valid'])
            self.assertEqual(report['udp_receive_errors_delta'], 1)
            gap = next(issue for issue in report['issues'] if issue['reason'].startswith('CSI gap'))
            self.assertEqual(gap['overlapping_trials'], ['gesture'])
