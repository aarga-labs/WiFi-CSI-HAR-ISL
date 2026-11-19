"""Audit an existing paired recording; preserve all original sensor/CSI files."""
import bisect
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from capture_paths import saved_capture_path
from stream_quality import assess_saved_run


def read_json(path):
    return json.loads(path.read_text())


def rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(folder):
    folder = saved_capture_path(folder).resolve()
    known_runs = (ROOT/'data/recordings').glob('*/*/*')
    if not any(run.is_dir() and run.resolve() == folder for run in known_runs):
        raise ValueError('Choose an existing recording under data/recordings.')
    plan = read_json(folder/'plan.json')
    csi = saved_capture_path(plan['paired_csi_csv'])
    capture = csi.parent
    receipt = read_json(folder/'transfer_receipt.json')
    manifest = read_json(folder/'phone/manifest.json')
    phone = read_json(folder/'phone/metadata.json')
    receiver = read_json(capture/'metadata.json')
    quality = assess_saved_run(folder, csi)
    events = [e for e in plan['phases'] if e['kind'] in ('perform', 'baseline')]
    starts = [e['start_ns'] for e in events]
    report = dict(run=folder.name, phone_status=receipt['phone_status'],
                  phone_model=phone.get('phone_model'), phone_error=phone.get('error'),
                  status=quality['status'], issues=quality['issues'],
                  completed_events=quality['completed_events'],
                  strict_full_trials=quality['strict_full_trials'],
                  events_with_clean_2s_windows=quality['events_with_clean_2s_windows'],
                  clean_2s_windows=quality['clean_2s_windows'],
                  planned_counts=dict(collections.Counter(e['label'] for e in events)),
                  archive_hash_matches=sha(folder/'phone_original.zip') == receipt['sha256'],
                  archive_size_matches=(folder/'phone_original.zip').stat().st_size == receipt['bytes'],
                  all_member_hashes_match=all(sha(folder/'phone'/name) == item['sha256'] and
                      (folder/'phone'/name).stat().st_size == item['bytes'] for name, item in manifest.items()),
                  receiver_status=receiver['status'],
                  receiver_exists=Path('/proc/'+str(receiver['receiver_pid'])).exists(),
                  flags=read_json(folder/'flags.json'), phone={},
                  collection_setup=receiver.get('collection_setup'))
    errors = [d['start_error_ms'] for d in quality['decisions'] if d['start_error_ms'] is not None]
    report['cue_start_error_ms_min_max'] = [min(errors), max(errors)] if errors else None
    range_flags = []
    for name in ('accelerometer', 'gyroscope'):
        data = rows(folder/f'phone/{name}.csv')
        t = np.array([int(x['sensor_elapsed_ns']) for x in data], dtype=np.int64)
        ct = np.array([int(x['controller_time_est_ns']) for x in data], dtype=np.int64)
        v = np.array([[float(x[a]) for a in ('x', 'y', 'z')] for x in data])
        dt = np.diff(t)/1e6
        limit = phone[name]['max_range']
        near = np.max(abs(v), axis=1) >= .99*limit
        scored = collections.Counter()
        scored_above = unscored = 0
        for i in np.flatnonzero(near):
            index = bisect.bisect_right(starts, int(ct[i]))-1
            e = events[index] if index >= 0 and ct[i] <= events[index]['end_ns'] else None
            if e:
                scored[(e['trial'], e['label'])] += 1
                scored_above += int(np.max(abs(v[i])) > limit)
            else:
                unscored += 1
            for j, axis in enumerate(('x', 'y', 'z')):
                if abs(v[i, j]) >= .99*limit:
                    range_flags.append(dict(sensor=name, controller_time_ns=int(ct[i]),
                        trial=e['trial'] if e else '', label=e['label'] if e else '',
                        axis=axis, value=float(v[i, j]), reported_range=limit))
        report['phone'][name] = dict(rows=len(data), median_hz=float(1000/np.median(dt)),
            max_gap_ms=float(dt.max()), gaps_above_100ms=int(sum(dt > 100)),
            nonincreasing_sensor_timestamps=int(sum(dt <= 0)),
            nonincreasing_controller_timestamps=int(sum(np.diff(ct) <= 0)),
            nonfinite_values=int(np.sum(~np.isfinite(v))), max_abs_component=float(abs(v).max()),
            reported_max_range=limit, near_range_rows=int(sum(near)),
            scored_rows_above_reported_range=scored_above, unscored_range_flagged_rows=unscored,
            scored_events_with_range_flags=[dict(trial=k[0], label=k[1], rows=n) for k, n in scored.items()])
    timestamps = []
    bad = invalid = zero = 0
    with csi.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            try:
                if len(row) != len(header):
                    bad += 1
                    continue
                ts = int(row[1])
                values = [float(x) for x in row[3:]]
                invalid += sum(not math.isfinite(x) for x in values)
                zero += all(x == 0 for x in values)
                timestamps.append(ts)
            except (ValueError, IndexError):
                bad += 1
    t = np.array(timestamps, dtype=np.int64)
    gaps = np.diff(t)/1000
    bins = np.bincount((t-t[0])//1_000_000)
    report['csi'] = dict(rows=len(t), duration_s=float((t[-1]-t[0])/1e6),
        mean_rows_s=float((len(t)-1)/((t[-1]-t[0])/1e6)), max_gap_ms=float(gaps.max()),
        p99_gap_ms=float(np.percentile(gaps, 99)), gaps_above_100ms=int(sum(gaps > 100)),
        nonincreasing_timestamps=int(sum(gaps <= 0)), per_second_min=int(bins[:-1].min()),
        per_second_max=int(bins[:-1].max()), empty_seconds=int(sum(bins == 0)),
        malformed_rows=bad, nonfinite_values=invalid, all_zero_rows=zero)
    health = [json.loads(x) for x in (capture/'receiver_health.jsonl').read_text().splitlines()]
    report['udp_receive_errors_delta'] = health[-1]['udp']['RcvbufErrors']-health[0]['udp']['RcvbufErrors']
    live = [json.loads(x) for x in (capture/'live_receiver_checks.jsonl').read_text().splitlines()]
    report['live_checks'] = dict(total=len(live), flagged=sum(not x['csi']['ready'] or not x['host']['ready'] for x in live))
    log = (capture/'receiver.log').read_text(errors='replace')
    report['receiver_log'] = dict(overflow_events_reported=sum(map(int, re.findall(r'(\d+) overflows occurred', log))),
        overflow_lines=[x for x in log.splitlines() if 'overflow' in x.lower()],
        shutdown_error_mentions=len(re.findall(r'Traceback|RuntimeError|shutdown problem', log)))
    shared = rows(next(capture.glob('planned_labels_*.csv')))
    report['shared_labels_match_plan'] = len(shared) == len(plan['phases']) and all(
        a['label'] == b['label'] and int(a['t_start_us']) == b['start_ns']//1000 and
        int(a['t_end_us']) == b['end_ns']//1000 for a, b in zip(shared, plan['phases']))
    out = ROOT/'quality_reviews'/folder.name
    out.mkdir(exist_ok=True)
    if range_flags:
        with (out/'sensor_range_flags.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(range_flags[0]))
            writer.writeheader()
            writer.writerows(range_flags)
    windows = rows(folder/'usable_windows.csv')
    marked = [dict(w, sensor_range_flags=sum(int(w['start_controller_ns']) <= x['controller_time_ns'] <=
                 int(w['end_controller_ns']) for x in range_flags)) for w in windows]
    with (out/'windows_with_sensor_range_flags.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(marked[0]))
        writer.writeheader()
        writer.writerows(marked)
    report['range_flagged_scored_trials'] = sorted({x['trial'] for x in range_flags if x['trial'] != ''})
    report['windows_with_range_flags'] = sum(x['sensor_range_flags'] > 0 for x in marked)
    report['windows_without_range_flags'] = len(marked)-report['windows_with_range_flags']
    report['quality_scope'] = 'Timing/density checks are separate from amplitude-range flags. Range flags do not independently prove clipping. Group overlapping windows by original trial/session before splitting.'
    (ROOT/'quality_reviews'/f'{folder.name}_quality.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    print(json.dumps(audit(sys.argv[1]), indent=2))
