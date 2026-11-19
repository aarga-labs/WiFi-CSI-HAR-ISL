"""Check data-quality decisions independently of radio hardware."""
import csv,json,tempfile,unittest,sys
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stream_quality import inspect_csi_tail,inspect_receiver_health,assess_saved_run,ensure_receive_buffer

class StreamChecks(unittest.TestCase):
    def test_preflight_can_log_short_failed_and_ready_streams_as_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'csi.csv'
            # The short initial stream reproduced the actual early-false
            # NumPy boolean failure; a completed warmup must serialize too.
            for duration,step,expected in [(2,10000,False),(22,5000,True),(22,100000,False)]:
                count=int(duration*1_000_000/step)+1
                p.write_text('Packet,Timestamp_us,Channel\n'+''.join(f'{i},{i*step},1\n' for i in range(count)))
                probe=inspect_csi_tail(p,minimum_seconds=20,maximum_gap_ms=100,now_us=duration*1_000_000)
                saved=json.loads(json.dumps(dict(csi=probe,host=dict(ready=False))))
                self.assertIs(type(probe['ready']),bool)
                self.assertIs(saved['csi']['ready'],expected)

    def test_short_good_burst_cannot_pass_sustained_preflight(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'csi.csv'
            for duration,ready in [(2,False),(22,True)]:
                p.write_text('Packet,Timestamp_us,Channel\n'+''.join(f'{i},{i*5000},1\n' for i in range(duration*200+1)))
                self.assertEqual(inspect_csi_tail(p,minimum_seconds=20,maximum_gap_ms=100,now_us=duration*1_000_000)['ready'],ready)
            # A high mean rate must not hide a 200ms hole inside that interval.
            p.write_text('Packet,Timestamp_us,Channel\n'+''.join(f'{i},{i*5000},1\n' for i in range(4401) if not 2000<=i<2040))
            self.assertFalse(inspect_csi_tail(p,minimum_seconds=20,maximum_gap_ms=100,now_us=22_000_000)['ready'])

    def test_preflight_uses_new_udp_errors_not_old_cumulative_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'health.jsonl'
            for increase,ready in [(0,True),(1,False)]:
                rows=[dict(monotonic_ns=i*1_000_000_000,uhd_overflows=0,nic_rx_dropped=0,nic_rx_errors=0,udp=dict(RcvbufErrors=355048+(increase if i==21 else 0))) for i in range(22)]
                p.write_text(''.join(json.dumps(x)+'\n' for x in rows)+'{"partial":')
                self.assertEqual(inspect_receiver_health(p,now_ns=21_000_000_000)['ready'],ready)
    def test_startup_refuses_a_low_rate_or_long_gap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'csi.csv'
            for step,ready in [(5_000,True),(10_000,False),(100_000,False)]:
                p.write_text('Packet,Timestamp_us,Channel\n'+''.join(f'{i},{i*step},1\n' for i in range(201)))
                self.assertEqual(inspect_csi_tail(p,now_us=200*step)['ready'],ready)
    def test_stale_or_future_data_and_independent_host_overflow(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'csi.csv'
            p.write_text(''.join(f'{i},{i*5000},1\n' for i in range(3000)))
            for now in [16_000_000,14_000_000]:
                self.assertFalse(inspect_csi_tail(p,now_us=now)['ready'])
            p=Path(d)/'health.jsonl'
            rows=[dict(monotonic_ns=i*10**9,udp={'RcvbufErrors':0},uhd_overflows=int(i>=4),
                       nic_rx_errors=0,nic_rx_dropped=0,target_crc_valid_frames=i*200)
                  for i in range(15)]
            p.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            result=inspect_receiver_health(p,minimum_seconds=12,now_ns=14*10**9)
            self.assertFalse(result['ready'])
            self.assertEqual(result['uhd_overflows_delta'],1)
            self.assertTrue(inspect_receiver_health(p,minimum_seconds=3,now_ns=14*10**9)['ready'])
            self.assertFalse(inspect_receiver_health(p,minimum_seconds=3,now_ns=18*10**9)['ready'])

    def test_small_receive_buffer_is_reported_before_capture(self):
        with mock.patch('pathlib.Path.read_text',return_value='4194304'):
            with self.assertRaisesRegex(ValueError,'SETUP_RX_BUFFERS'):ensure_receive_buffer()
        with mock.patch('pathlib.Path.read_text',return_value='50000000'):ensure_receive_buffer()
    def test_finished_recording_with_a_lost_sensor_interval_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'phone').mkdir();start=1_000_000_000;end=5_000_000_000
            plan={'phases':[dict(kind='perform',index=0,trial=1,label='walk',start_ns=start,end_ns=end)]}
            (p/'plan.json').write_text(json.dumps(plan));(p/'phone/metadata.json').write_text('{"status":"complete"}')
            for gaps,expected,off_grid in [(0,'passed_window_checks',False),(1,'review_required',False),(0,'passed_window_checks',True)]:
                quality={n:dict(invalid_rows_or_order=0,gaps_over_100ms=gaps) for n in ['accelerometer','gyroscope']}
                (p/'phone/quality.json').write_text(json.dumps(quality))
                for name in ['accelerometer','gyroscope']:
                    with (p/f'phone/{name}.csv').open('w',newline='') as f:
                        w=csv.writer(f);w.writerow(['controller_time_est_ns']);w.writerows([[t] for t in range(0,6_020_000_000,20_000_000) if not (gaps and 2_000_000_000<=t<2_500_000_000)])
                with (p/'phone/labels.csv').open('w',newline='') as f:
                    w=csv.writer(f);w.writerow(['phase_index','phase_complete','start_controller_est_ns']);w.writerow([0,'true',start])
                csi=p/'csi.csv'
                with csi.open('w',newline='') as f:
                    w=csv.writer(f);w.writerow(['Packet','Timestamp_us','Channel','SC0_Re','SC0_Im']);w.writerows([[i,t//1000,1,1,0] for i,t in enumerate(range(0,6_010_000_000,10_000_000)) if not (off_grid and (990_000_000<=t<1_100_000_000 or 3_310_000_000<=t<4_500_000_000))])
                result=assess_saved_run(p,csi);self.assertEqual(result['status'],expected)
                self.assertEqual(result['events_with_clean_2s_windows'],1)
