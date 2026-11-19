"""Summarize a completed CSI capture and locate quality issues on the cue timeline."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np

from stream_quality import MIN_CAPTURE_RATE, health_deltas


def read_csi_summary(path):
    timestamps = []
    malformed = nonfinite = zero = wrong_id = 0
    expected = ['Packet','Timestamp_us','Channel'] + [
        f'SC{i}_{part}' for i in range(52) for part in ('Re','Im')]
    with path.open('rb') as stream:
        header = stream.readline().decode().strip().split(',')
        for index,line in enumerate(stream):
            try:
                if not line.endswith(b'\n'):
                    raise ValueError('incomplete CSI row')
                packet, stamp, channel, payload = line.split(b',',3)
                t = int(stamp)
                values = np.fromstring(payload.decode(),sep=',')
                if len(values)!=104 or int(channel)!=1:
                    raise ValueError('unexpected CSI row')
                wrong_id += int(packet)!=index
                nonfinite += not np.isfinite(values).all()
                zero += not values.any()
                timestamps.append(t)
            except (ValueError, UnicodeError):
                malformed += 1
    return np.asarray(timestamps,dtype=np.int64), dict(header_valid=header==expected,
                    malformed_rows=malformed,nonfinite_rows=nonfinite,zero_rows=zero,
                    discontinuous_saved_packet_ids=wrong_id)


def capture_report(folder, events=()):
    folder = Path(folder)
    timestamps, structure = read_csi_summary(folder/'csi.csv')
    health = [json.loads(line) for line in (folder/'receiver_health.jsonl').read_text().splitlines()]
    if len(health) < 2:
        raise ValueError('Missing receiver telemetry')
    issues = []
    def issue(start, end, reason):
        start, end = sorted((start, end))
        trials = [e['trial'] for e in events if e['start_ns'] <= end and e['end_ns'] >= start]
        issues.append(dict(start_ns=int(start), end_ns=int(end), reason=reason, overlapping_trials=trials))

    for row in health:
        if row.get('bench_stop_reason'):
            issue(row['epoch_ns'],row['epoch_ns'],row['bench_stop_reason'])
    for a,b in zip(health, health[1:]):
        reasons = [key for key, value in health_deltas(a,b).items() if value]
        # Historical builds retained the text of the asynchronous UHD messages.
        if 'uhd_overflows' not in b and a.get('uhd_async_events') != b.get('uhd_async_events'):
            reasons.append('UHD asynchronous message')
        if b['monotonic_ns'] - a['monotonic_ns'] > 2.5e9:
            reasons.append('telemetry gap')
        if reasons:
            issue(a['epoch_ns'], b['epoch_ns'], ', '.join(reasons))

    gaps = np.diff(timestamps)
    for idx in np.flatnonzero((gaps > 100000) | (gaps <= 0)):
        issue(timestamps[idx]*1000, timestamps[idx+1]*1000, 'CSI gap or clock discontinuity')
    # Use the health clock as the observation boundary to catch silent starts/ends.
    start_us, end_us = health[0]['epoch_ns']//1000, health[-1]['epoch_ns']//1000
    if not structure['header_valid'] or any(v for k,v in structure.items() if k!='header_valid'):
        issue(start_us*1000,end_us*1000,'CSI schema, values or saved packet indices invalid')
    # Allow device startup and shutdown at the edges, but score every full 10 s thereafter.
    if not np.any(gaps <= 0):
        for start in range(start_us + 2_000_000, end_us - 10_000_000 + 1, 10_000_000):
            count = np.searchsorted(timestamps, start+10_000_000) - np.searchsorted(timestamps, start)
            if count / 10 < MIN_CAPTURE_RATE:
                issue(start*1000, (start+10_000_000)*1000, 'low ten-second CSI rate')
    if len(timestamps) and timestamps[0]-start_us>2_500_000:
        issue(start_us*1000,timestamps[0]*1000,'delayed first target CSI')
    if not len(timestamps):
        issue(start_us*1000, end_us*1000, 'no target CSI')
    elif end_us - timestamps[-1] > 2_500_000:
        issue(timestamps[-1]*1000, end_us*1000, 'CSI stopped before receiver shutdown')

    timing = folder/'host_timing.csv'
    valid_timing = None
    if timing.exists():
        try:
            with timing.open() as f:
                reader = csv.reader(f, strict=True)
                count = 0
                previous = -1
                valid_timing = next(reader, None) == ['Packet','Host_monotonic_ns']
                for index, (packet, stamp) in enumerate(reader):
                    mono = int(stamp)
                    valid_timing &= int(packet) == index and mono > previous
                    previous = mono
                    count += 1
            valid_timing &= count == len(timestamps)
        except (OSError, ValueError, csv.Error):
            valid_timing = False
        if not valid_timing:
            issue(start_us*1000, end_us*1000, 'timing sidecar disagrees with CSI')
    elif (folder/'metadata.json').exists() and 'timing_source' in json.loads((folder/'metadata.json').read_text()):
        issue(start_us*1000, end_us*1000, 'missing timing sidecar')

    if 'uhd_overflows' in health[-1]:
        for key in ('uhd_overflows','nic_rx_errors','nic_rx_dropped'):
            if health[-1].get(key) is None:
                issue(start_us*1000,end_us*1000,key + ' telemetry unavailable')
    if len(timestamps) != health[-1].get('target_crc_valid_frames', len(timestamps)):
        issue(start_us*1000,end_us*1000,'saved count differs from decoded target-frame count')
    span = (int(timestamps[-1])-int(timestamps[0]))/1e6 if len(timestamps)>1 else 0
    duration = (health[-1]['monotonic_ns'] - health[0]['monotonic_ns'])/1e9
    meta_file = folder/'metadata.json'
    required = json.loads(meta_file.read_text()).get('diagnostic_seconds') if meta_file.exists() else None
    if required and duration < required - 1:
        issue(start_us*1000,end_us*1000,'timed rehearsal incomplete')
    temps=[r.get('temperature_c',{}).get('x86_pkg_temp') for r in health]
    throttle='package_throttle_total_time_ms'
    values=[r.get('thermal_throttle',{}).get(throttle) for r in (health[0],health[-1])]
    thermal = [t for t in temps if t is not None]
    thermal_warning = bool(None not in values and values[1]>values[0])
    return dict(structure=structure, thermal_throttling_observed=thermal_warning,
                initial_cpu_c=thermal[0] if thermal else None,
                median_cpu_c=float(np.median(thermal)) if thermal else None,
                status='review_required' if issues else 'passed', rows=len(timestamps),
                rows_per_s=(len(timestamps)-1)/span if span else 0, duration_s=duration,
                max_gap_ms=float(gaps.max()/1000) if gaps.size else None,
                profile=sorted({r['platform_profile'] for r in health if r.get('platform_profile')}),
                cpu_max_perf_pct=sorted({r['cpu_max_perf_pct'] for r in health if r.get('cpu_max_perf_pct') is not None}),
                peak_cpu_c=max((t for t in temps if t is not None),default=None),
                throttle_time_delta_ms=values[1]-values[0] if None not in values else None,
                fan_rpm_ranges={k:[min(v),max(v)] for k in ('cpu_fan_rpm','gpu_fan_rpm')
                                if (v:=[r[k] for r in health if r.get(k) is not None])},
                timing_sidecar_valid=valid_timing, issues=issues, **health_deltas(health[0],health[-1]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    plans = list(args.folder.glob('phone_plan_*.json'))
    events = json.loads(plans[0].read_text())['plan']['phases'] if plans else []
    report = capture_report(args.folder,[e for e in events if e['kind'] in ('baseline','perform')])
    print(json.dumps(report,indent=2))
    raise SystemExit(report['status'] != 'passed')
