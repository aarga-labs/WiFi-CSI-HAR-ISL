"""Capture readiness and sample-coverage checks, without changing raw files."""
import csv,json,math,time
from pathlib import Path
import numpy as np

def ensure_receive_buffer():
    value=int(Path('/proc/sys/net/core/rmem_max').read_text())
    if value<50_000_000:
        raise ValueError('Receive buffer is too small. Run bash SETUP_RX_BUFFERS.sh once (requires your sudo password), then retry this command.')

# A new 200-probe/s capture should sustain at least 90% of nominal.
# assess_saved_run separately identifies salvageable historical windows.
MIN_CAPTURE_RATE = 180

def complete_tail(path, byte_limit):
    """Drop only partial boundary lines from a bounded read of a growing file."""
    with path.open('rb') as stream:
        end = stream.seek(0, 2)
        start = max(0, end - byte_limit)
        stream.seek(start)
        lines = stream.read(end - start).split(b'\n')[:-1]
    return lines[1:] if start else lines

def inspect_csi_tail(path, minimum_seconds=1, maximum_gap_ms=100, *, now_us=None):
    path = Path(path)
    if not path.is_file():
        return dict(ready=False, reason='waiting for CSI file')
    lines = complete_tail(path, int((minimum_seconds + 3) * 450000))
    timestamps = []
    for line in lines:
        if line.startswith(b'Packet,'):
            continue
        try:
            timestamps.append(int(line.split(b',', 2)[1]))
        except (ValueError, IndexError):
            return dict(ready=False, reason='malformed complete CSI row')
    if len(timestamps) < 2:
        return dict(ready=False, reason='waiting for CSI rows')
    ts = np.asarray(timestamps, dtype=np.int64)
    # Preserve the predecessor at the cut so a gap across the boundary counts.
    recent = np.flatnonzero(ts >= ts[-1] - (minimum_seconds + .25) * 1e6)
    ts = ts[max(0, int(recent[0]) - 1):]
    span = float(ts[-1] - ts[0]) / 1e6
    gaps = np.diff(ts)
    rate = (len(ts) - 1) / span if span > 0 else 0
    gap = float(gaps.max()) / 1000
    age = ((time.time_ns() // 1000 if now_us is None else now_us) - int(ts[-1])) / 1e6
    reasons = []
    if not 0 <= age <= 0.5:
        reasons.append('stale CSI or clock discontinuity')
    if span < minimum_seconds:
        reasons.append('insufficient observation time')
    if rate < MIN_CAPTURE_RATE:
        reasons.append('low CSI rate')
    if gap > maximum_gap_ms or np.any(gaps <= 0):
        reasons.append('CSI gap or non-increasing timestamp')
    return dict(ready=not reasons, reason=', '.join(reasons), rows_per_s=rate,
                max_gap_ms=gap, age_s=age, observed_s=span, latest_us=int(ts[-1]))

def health_deltas(first, last):
    return {
        'udp_receive_errors_delta': last['udp']['RcvbufErrors'] - first['udp']['RcvbufErrors'],
        **{key + '_delta': last[key] - first[key]
           for key in ('uhd_overflows', 'nic_rx_dropped', 'nic_rx_errors')
           if first.get(key) is not None and last.get(key) is not None}
    }

def inspect_receiver_health(path, minimum_seconds=20, *, now_ns=None):
    path = Path(path)
    if not path.is_file():
        return dict(ready=False, reason='waiting for receiver telemetry')
    try:
        rows = [json.loads(line) for line in complete_tail(path, int((minimum_seconds + 8) * 16000))]
    except ValueError:
        return dict(ready=False, reason='malformed receiver telemetry')
    if len(rows) < 2:
        return dict(ready=False, reason='waiting for receiver telemetry')
    last = rows[-1]
    end = last['monotonic_ns']
    earlier = [i for i, row in enumerate(rows) if row['monotonic_ns'] <= end - minimum_seconds * 1e9]
    if not earlier:
        return dict(ready=False, reason='waiting for sustained receiver telemetry')
    rows = rows[earlier[-1]:]
    first = rows[0]
    age = ((time.monotonic_ns() if now_ns is None else now_ns) - end) / 1e9
    issues = []
    if not 0 <= age <= 2.5 or any(not 0 < b['monotonic_ns'] - a['monotonic_ns'] <= 2.5e9
                                  for a,b in zip(rows, rows[1:])):
        issues.append('stale or interrupted health telemetry')
    deltas = health_deltas(first,last)
    issues.extend(k for k,v in deltas.items() if v != 0)
    if 'target_crc_valid_frames' in last and last['target_crc_valid_frames'] <= first['target_crc_valid_frames']:
        issues.append('target-frame counter stopped')
    for key in ('uhd_overflows', 'nic_rx_errors', 'nic_rx_dropped'):
        if last.get(key) is None:
            issues.append(key + ' telemetry unavailable')
    return dict(ready=not issues, reason=', '.join(issues), age_s=age, **deltas,
                temperature_c=last.get('temperature_c',{}),
                thermal_throttle_count_delta=last.get('thermal_throttle',{}).get('package_throttle_count',0)
                    - first.get('thermal_throttle',{}).get('package_throttle_count',0))

def _rows(path):
    with Path(path).open() as f:return list(csv.DictReader(f))

def assess_saved_run(phone_folder,csi_file):
    """Report whole-trial and clean-window coverage separately."""
    folder=Path(phone_folder);plan=json.loads((folder/'plan.json').read_text())
    meta=json.loads((folder/'phone/metadata.json').read_text())
    q=json.loads((folder/'phone/quality.json').read_text());labels=_rows(folder/'phone/labels.csv')
    events=[p for p in plan['phases'] if p['kind'] in ('perform','baseline')]
    actual={int(p['phase_index']):p for p in labels};streams={};issues=[]
    for name in ['accelerometer','gyroscope']:
        rows=_rows(folder/f'phone/{name}.csv')
        streams[name]=np.array([int(r['controller_time_est_ns']) for r in rows],dtype=np.int64)
        if q[name]['invalid_rows_or_order'] or q[name]['gaps_over_100ms']:issues.append(name+' has invalid rows or gaps above 100ms')
    csi_t=[];invalid=0;badrows=0
    with Path(csi_file).open() as f:
        reader=csv.reader(f);header=next(reader)
        for row in reader:
            try:
                if len(row)!=len(header):badrows+=1;continue
                t=int(row[1]);vals=[float(v) for v in row[3:]]
                invalid+=sum(not math.isfinite(v) for v in vals);csi_t.append(t*1000)
            except (ValueError,IndexError):badrows+=1
    streams['csi']=np.asarray(csi_t,dtype=np.int64)
    for name,t in streams.items():
        if len(t)<2 or np.any(np.diff(t)<=0):issues.append(name+' has missing/non-increasing timestamps')
    if badrows or invalid:issues.append('CSI has malformed/non-finite data')
    windows=[];decisions=[]
    for event in events:
        rec=actual.get(event['index']);complete=rec is not None and rec['phase_complete']=='true'
        lateness=None if rec is None else (int(rec['start_controller_est_ns'])-event['start_ns'])/1e6
        timing_ok=complete and abs(lateness)<=200
        def covered(start,end):
            for name,t in streams.items():
                if len(t)<2 or t[0]>start or t[-1]<end:return False
                a,b=np.searchsorted(t,[start,end]);near=t[max(0,a-1):min(len(t),b+1)]
                if len(near)<2 or np.diff(near).max()>100_000_000:return False
                if (b-a)/((end-start)/1e9)<(20 if name=='csi' else 45):return False
            return True
        full=timing_ok and covered(event['start_ns'],event['end_ns']);n=0
        if timing_ok:
            for start in range(event['start_ns'],event['end_ns']-2_000_000_000+1,500_000_000):
                end=start+2_000_000_000
                if covered(start,end):
                    n+=1;windows.append(dict(phase_index=event['index'],trial=event['trial'],label=event['label'],start_controller_ns=start,end_controller_ns=end))
            # A clean interval can fall between fixed 0.5s grid positions.
            # Search actual gap boundaries before declaring an event unusable.
            if not n:
                candidates={event['start_ns']}
                for t in streams.values():
                    for index in np.flatnonzero(np.diff(t)>100_000_000):
                        start=int(t[index+1])+1
                        if event['start_ns']<=start<=event['end_ns']-2_000_000_000:candidates.add(start)
                for start in sorted(candidates):
                    end=start+2_000_000_000
                    if covered(start,end):
                        n+=1;windows.append(dict(phase_index=event['index'],trial=event['trial'],label=event['label'],start_controller_ns=start,end_controller_ns=end))
                        break
        decisions.append(dict(trial=event['trial'],label=event['label'],complete=complete,start_error_ms=lateness,strict_full_trial_pass=bool(full),clean_2s_windows=n))
    if meta['status']!='complete':issues.append('Phone run is '+meta['status'])
    missing=[d['trial'] for d in decisions if not d['clean_2s_windows']]
    if missing:issues.append('No clean paired 2-second window for trials '+str(missing))
    result=dict(status='passed_window_checks' if not issues else 'review_required',issues=issues,
        events=len(events),completed_events=sum(d['complete'] for d in decisions),strict_full_trials=sum(d['strict_full_trial_pass'] for d in decisions),
        events_with_clean_2s_windows=sum(d['clean_2s_windows']>0 for d in decisions),clean_2s_windows=len(windows),
        phone_quality=q,decisions=decisions,label_provenance='scheduled cues; execution and physical latency not independently verified',
        criteria='Full event coverage or separately filtered two-second windows; max gap 100ms, IMU >=45Hz, CSI >=20 rows/s. Search fixed 0.5s starts and actual gap boundaries before rejection. Overlapping windows must be grouped before train/test splits.')
    receiver_dir = Path(csi_file).parent
    if (receiver_dir/'receiver_health.jsonl').exists():
        from receiver_report import capture_report
        result['receiver_report'] = capture_report(receiver_dir, events)
        if result['receiver_report']['issues']:
            result['status'] = 'review_required'
            issues.append('Receiver diagnostics flagged intervals; see receiver_report for affected trials.')
    (folder/'collection_quality.json').write_text(json.dumps(result,indent=2)+'\n')
    with (folder/'usable_windows.csv').open('w',newline='') as f:
        fields=['phase_index','trial','label','start_controller_ns','end_controller_ns'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(windows)
    return result
