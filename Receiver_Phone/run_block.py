#!/usr/bin/env python3
"""Start a named phone block after its matching CSI receiver is recording."""
import argparse
import csv
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

from collection_blocks import BLOCKS
from controller import make_plan

ROOT = Path(__file__).resolve().parent

def api(port, token, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=body,
        headers={'X-Token':token, 'Content-Type':'application/json'})
    # Local controller only; never send the pairing key to a configured proxy.
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=10) as response:
        return json.load(response)

def process_alive(pid):
    try:
        if int(pid)<=0:return False
        args=[part.decode(errors='replace') for part in Path(f'/proc/{int(pid)}/cmdline').read_bytes().split(b'\0') if part]
        if not args or not Path(args[0]).name.startswith('python'):return False
        index=1
        while index<len(args):
            arg=args[index]
            if arg in ('-c','-m'):return False
            if arg=='--':index+=1;break
            if arg in ('-W','-X'):index+=2;continue
            if arg.startswith('-'):index+=1;continue
            break
        return index<len(args) and Path(args[index]).name in ('wifi_rx.py','capture_receiver.py')
    except (ValueError, OSError, TypeError):
        return False

def find_csi(root, pid, session, block):
    matches = []
    for path in (root/'data/csi'/pid/session).glob('*/metadata.json'):
        try:
            meta = json.loads(path.read_text())
            if meta.get('block') != block or meta.get('status') != 'running':
                continue
            if not process_alive(meta.get('receiver_pid')):
                continue
            raw = Path(meta['csi_csv'])
            if not raw.is_file() or raw.stat().st_size < 100:
                continue
            size = raw.stat().st_size
            time.sleep(.6)
            if raw.stat().st_size <= size:
                continue
            matches.append((path.parent, meta))
        except (ValueError, OSError, KeyError):
            continue
    if len(matches) != 1:
        raise ValueError(f'Found {len(matches)} matching CSI recordings receiving rows. '
            f'First run ./START_CSI_RX.sh --pid {pid} --session {session} --block {block}; '
            'wait for incoming packets. Stop an older receiver before starting another.')
    return matches[0]

def describe(plan):
    events = [p for p in plan['phases'] if p['kind']=='perform']
    print(f"Block: {plan['block_title']} | {plan['pid']} {plan['session']} | forearm: {plan['arm']}")
    print('Posture:', plan['posture'], '| order:',plan.get('order_source','saved plan'))
    print('Event order:', ' -> '.join(p['label'] for p in events) if events else '120 seconds of '+('seated' if plan['posture']=='seated' else 'standing')+' stillness')
    print(f"Scheduled block: {(plan['end_ns']-plan['start_ns'])/1e9:.0f} seconds including preparation/rest. No added timing tasks.")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('block',choices=BLOCKS)
    p.add_argument('--pid',choices=['P00','P04','P05'],required=True)
    p.add_argument('--session',default='S01')
    p.add_argument('--arm',choices=['right','left'],default='right')
    p.add_argument('--reps',type=int,default=5)
    p.add_argument('--seed',type=int,default=401)
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--managed-csi',action='store_true',help=argparse.SUPPRESS)
    p.add_argument('--preview',action='store_true',help='Print the planned order only; no server, radio, or phone is started.')
    args=p.parse_args()
    req=dict(block=args.block,pid=args.pid,session=args.session,arm=args.arm,reps=args.reps,seed=args.seed)
    try:
        preview=make_plan(req,time.time_ns())
        if args.preview:
            describe(preview);print('PREVIEW ONLY — nothing recorded.');return 0
        token=json.loads((ROOT/'data/pairing.json').read_text())['token']
        state=api(args.port,token,'/api/state')
        if state.get('paired_commands_version') != 2 or args.block not in state.get('collection_blocks',[]):
            raise ValueError('The controller is an older version. Finish and save any active block, '
                'stop its original terminal with Ctrl+C, then run ./START_WIFI.sh and refresh the website.')
        if any(s['status'] in ('queued','recording','stopping') for s in state['sessions']):
            raise ValueError('Finish and save the current phone block first.')
        devices=[d for d in state['devices'] if d['seen_s_ago']<8]
        if len(devices)!=1:
            raise ValueError('Connect exactly one recording phone, then try again.')
        folder,meta=find_csi(ROOT,args.pid,args.session,args.block)
        req.update(device_id=devices[0]['id'],paired_csi_id=meta['recording_id'],paired_csi_csv=meta['csi_csv'])
        result=api(args.port,token,'/api/session',req)
        sid=result['session_id']
        # The server-created plan is the shared order. No second randomization.
        plan_path=ROOT/'data/recordings'/args.pid/args.session/sid/'plan.json'
        plan=json.loads(plan_path.read_text())
        link=folder/('phone_plan_'+sid+'.json')
        with link.open('x') as f:
            json.dump(dict(phone_session_id=sid,phone_plan=str(plan_path),csi_csv=meta['csi_csv'],plan=plan),f,indent=2)
        labels=folder/('planned_labels_'+sid+'.csv')
        with labels.open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['phase_index','trial','kind','label','state','posture','t_start_us','t_end_us','source'])
            w.writeheader()
            for phase in plan['phases']:
                w.writerow(dict(phase_index=phase['index'],trial=phase['trial'],kind=phase['kind'],
                    label=phase['label'],state=phase['state'],posture=phase.get('posture',plan['posture']),
                    t_start_us=phase['start_ns']//1000,t_end_us=phase['end_ns']//1000,source='scheduled_cue_not_verified_movement'))
        describe(plan)
        print('Queued on phone. Follow the WEBSITE prompts, with laptop sound enabled.')
        print('CSI and phone use this ONE schedule; do not run the old cue_session.py.')
        print('CSI:',meta['csi_csv']);print('Shared labels:',labels)
        print('Phone folder:',plan_path.parent)
        if args.managed_csi:
            print('This named command will stop its CSI receiver and check both recordings automatically. Wait for its final result.')
        else:
            print('After received complete: Ctrl+C in the CSI terminal, then start the next block.')
        return 0
    except urllib.error.HTTPError as e:
        try:message=json.loads(e.read()).get('error',str(e))
        except (ValueError,OSError):message=str(e)
        print('Not started:',message,file=sys.stderr);return 1
    except (ValueError,OSError,KeyError) as e:
        print('Could not finish block setup:',e,file=sys.stderr)
        print('Check the dashboard before retrying; any accepted phone recording is retained.',file=sys.stderr)
        return 1

if __name__=='__main__':raise SystemExit(main())
