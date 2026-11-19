#!/usr/bin/env python3
"""One named command starts CSI + phone and stops its own CSI after transfer."""
import argparse
import json
import math
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time

from collection_blocks import BLOCKS
from run_block import ROOT, api, process_alive
from stream_quality import ensure_receive_buffer,inspect_csi_tail,inspect_receiver_health,assess_saved_run

def stop_receiver(proc):
    if proc and proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        try:
            code=proc.wait(timeout=30)
            if code!=0:
                print('Receiver helper reported a shutdown problem; inspect its retained log.',flush=True)
                return False
        except subprocess.TimeoutExpired:
            print('CSI is still stopping. Its files are retained; check its log before another run.',flush=True)
            return False
    return True

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid',choices=['P04','P05'],required=True)
    parser.add_argument('--session',default='S01')
    parser.add_argument('--arm',choices=['right','left'],default='right')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--gain',type=float,default=12,help='RX gain in dB; keep fixed within a matched comparison session.')
    parser.add_argument('--block',choices=BLOCKS,required=True)
    args=parser.parse_args();proc=None;sid=None;token=None
    try:
        token=json.loads((ROOT/'data/pairing.json').read_text())['token']
        if not 0<=args.gain<=31.5:raise ValueError('RX gain must be between 0 and 31.5 dB.')
        state=api(args.port,token,'/api/state')
        if state.get('paired_commands_version')!=2:
            raise ValueError('Restart the old controller first: finish/save its run, Ctrl+C in its terminal, then ./START_WIFI.sh.')
        if any(s['status'] in ('queued','recording','stopping') for s in state['sessions']):
            raise ValueError('A phone recording is still active. Stop/save that run before starting another.')
        if len([d for d in state['devices'] if d['seen_s_ago']<8])!=1:
            raise ValueError('Connect one recording phone first.')
        device=next(d for d in state['devices'] if d['seen_s_ago']<8)
        if device.get('app_version')!='1.1':
            raise ValueError('Install the corrected APK v1.1 first: connect USB and run ./START_USB.sh --reinstall. Keep the phone app open.')
        if not device.get('screen_visible'):
            raise ValueError('Open FYP Phone Collector on the phone and leave it visible. It keeps the screen awake.')
        ensure_receive_buffer()
        for path in (ROOT/'data/csi').glob('*/*/*/metadata.json'):
            meta=json.loads(path.read_text())
            if meta.get('status') in ('running','stop_pending') and process_alive(meta.get('receiver_pid')):
                raise ValueError('An older CSI receiver is still running. Press Ctrl+C in that receiver terminal first.')
        logdir=ROOT/'data/run_logs';logdir.mkdir(parents=True,exist_ok=True)
        logfile=logdir/f'{args.pid}_{args.block}_{time.strftime("%Y%m%d_%H%M%S")}_{secrets.token_hex(3)}.log'
        print(f'{args.pid} / {args.session} / {args.block}\nStarting CSI; waiting for packets...',flush=True)
        print('Receiver log:',logfile,flush=True)
        with logfile.open('x') as log:
            proc=subprocess.Popen([str(ROOT/'START_CSI_RX.sh'),'--pid',args.pid,'--session',args.session,
                '--block',args.block,'--addr','192.168.10.7','--gain',str(args.gain)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        folder=None;previous=None;deadline=time.monotonic()+90;last_notice=0;last_probe={}
        print('Checking at least 20 seconds of stable CSI before starting the phone. No activity yet.',flush=True)
        while time.monotonic()<deadline:
            if proc.poll() is not None:raise ValueError('Receiver exited. Read its log: '+str(logfile))
            for path in (ROOT/'data/csi'/args.pid/args.session).glob('*/metadata.json'):
                try:meta=json.loads(path.read_text())
                except (OSError,ValueError):continue
                if meta.get('helper_pid')!=proc.pid:continue
                raw=Path(meta['csi_csv'])
                size=raw.stat().st_size if raw.exists() else 0
                if previous is not None and size>previous and previous>100:
                    probe=inspect_csi_tail(raw,minimum_seconds=20,maximum_gap_ms=100)
                    health=inspect_receiver_health(path.parent/'receiver_health.jsonl')
                    last_probe=dict(csi=probe,host=health)
                    if time.monotonic()-last_notice>=5:
                        print('CSI preflight:',json.dumps(last_probe),flush=True);last_notice=time.monotonic()
                    if probe['ready'] and health['ready']:
                        folder=path.parent
                        (folder/'preflight_quality.json').write_text(json.dumps(last_probe,indent=2)+'\n')
                        print(f"CSI readiness: {probe['observed_s']:.1f}s checked; {probe['rows_per_s']:.1f} rows/s; largest gap {probe['max_gap_ms']:.1f} ms; no new UDP receive errors",flush=True);break
                previous=size
            if folder:break
            time.sleep(.5)
        if folder is None:raise ValueError('CSI did not pass the sustained 20-second check. Phone was not started. Check TX burst mode/underflows and receiver load. Last measurements: '+json.dumps(last_probe)+'; log: '+str(logfile))
        last_check=time.monotonic()
        result=subprocess.run([sys.executable,str(ROOT/'run_block.py'),args.block,'--pid',args.pid,
            '--session',args.session,'--arm',args.arm,'--port',str(args.port),'--managed-csi'])
        if result.returncode:
            # A local sidecar error can happen after the server accepted START.
            current=api(args.port,token,'/api/state')
            active=next((s for s in current['sessions'] if s['plan'].get('paired_csi_csv')==str(folder/'csi.csv') and s['status'] in ('queued','recording','stopping')),None)
            if active:sid=active['id']
            raise ValueError('Phone setup did not finish. Inspect the dashboard; originals are retained.')
        link=json.loads(next(folder.glob('phone_plan_*.json')).read_text());sid=link['phone_session_id']
        print('\nRUNNING — follow only the website. No form selection or Start click needed.',flush=True)
        last=None;next_health_check=0
        while True:
            if proc.poll() is not None:
                raise ValueError('CSI receiver stopped before the phone finished. See '+str(logfile))
            if time.monotonic()>=next_health_check:
                check_time=time.monotonic()
                # Cover the handoff and the entire interval between polls, including delayed polls.
                elapsed=math.ceil(check_time-last_check)+2
                duration=min(max(3, elapsed), 60)
                last_check=check_time
                probe=inspect_csi_tail(folder/'csi.csv',minimum_seconds=duration,maximum_gap_ms=100)
                host=inspect_receiver_health(folder/'receiver_health.jsonl',minimum_seconds=duration)
                if elapsed>60:
                    host.update(ready=False,reason='monitoring interrupted for over one minute')
                observation=dict(epoch_ns=time.time_ns(),csi=probe,host=host)
                with (folder/'live_receiver_checks.jsonl').open('a') as checks:checks.write(json.dumps(observation)+'\n')
                if not probe['ready'] or not host['ready']:
                    print('CSI WARNING:',probe.get('reason',''),host.get('reason',''),flush=True)
                else:
                    print(f"CSI live: {probe['rows_per_s']:.1f} rows/s; largest recent gap {probe['max_gap_ms']:.1f} ms; no new receive drops",flush=True)
                next_health_check=time.monotonic()+10
            try:
                state=api(args.port,token,'/api/state')
                row=next(s for s in state['sessions'] if s['id']==sid)
                status=row['status']
                if status!=last:print('Phone:',status,flush=True);last=status
                if status.startswith('received_'):
                    receiver_stopped=stop_receiver(proc)
                    print('CSI saved:',folder/'csi.csv',flush=True)
                    if not receiver_stopped:
                        print('PHONE SAVED — CSI STOP PENDING. Wait for its receiver to exit before another run.',flush=True)
                        return 1
                    if status!='received_complete':
                        print('PARTIAL RUN SAVED — review before using',flush=True);return 1
                    print('Checking CSI and phone sample coverage...',flush=True)
                    try:
                        report=assess_saved_run(ROOT/'data/recordings'/args.pid/args.session/sid,folder/'csi.csv')
                    except Exception as audit_error:
                        print('FILES SAVED — quality check could not finish:',audit_error,flush=True);return 1
                    print(f"Quality: {report['events_with_clean_2s_windows']}/{report['events']} events have clean paired windows; {report['strict_full_trials']} pass whole-trial checks.",flush=True)
                    if report['status']!='passed_window_checks':
                        print('SAVED — QUALITY REVIEW REQUIRED:', '; '.join(report['issues']),flush=True);return 1
                    print('FINISHED — two-second window quality checks passed. Use usable_windows.csv for training.',flush=True)
                    return 0
                if status in ('start_failed','cancelled'):raise ValueError('Phone '+status)
            except (OSError,StopIteration):
                print('Controller connection interrupted. Keeping CSI running; reconnect to save.',flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nStopping this run and keeping its files...',flush=True)
        if sid and token:
            try:api(args.port,token,'/api/stop',{'session_id':sid});time.sleep(2)
            except Exception:print('Use STOP on the phone if it is still recording.',flush=True)
        stop_receiver(proc);return 130
    except Exception as e:
        print('Run could not finish:',e,flush=True)
        if sid and token:
            try:api(args.port,token,'/api/stop',{'session_id':sid});time.sleep(2)
            except Exception:print('Use STOP on the phone if it is still recording.',flush=True)
        stop_receiver(proc);return 1

if __name__=='__main__':raise SystemExit(main())
