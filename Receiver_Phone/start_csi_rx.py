#!/usr/bin/env python3
"""Run the preserved configurable CSI receiver into a new, protected recording."""
import argparse
import ast
import hashlib
import fcntl
import shutil
import platform
import importlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import time
import threading
from collection_blocks import BLOCKS
from capture_paths import RECEIVER_EXAMPLES
from stream_quality import ensure_receive_buffer

ROOT=Path(__file__).resolve().parent
RECEIVER=RECEIVER_EXAMPLES/'wifi_rx.py'
CAPTURE=ROOT/'capture_receiver.py'

def drain_shutdown_output(child, logfile):
    """Keep the receiver's stdout pipe flowing while its threads stop."""
    def drain():
        with logfile.open('a') as log:
            for line in child.stdout:
                log.write(line)
            log.flush()
    thread=threading.Thread(target=drain,daemon=True)
    thread.start()
    return thread

def clean_environment():
    env=os.environ.copy()
    for name in ('LD_LIBRARY_PATH','LD_PRELOAD','PYTHONHOME','PYTHONPATH',
                 'QT_QPA_PLATFORM_PLUGIN_PATH','QT_PLUGIN_PATH','QML2_IMPORT_PATH'):
        env.pop(name,None)
    env['PYTHONUNBUFFERED']='1'
    private=ROOT/'rx_runtime'
    if (private/'ready.json').is_file():
        env['PYTHONPATH']=str(private/'install/python')
        env['LD_LIBRARY_PATH']=str(private/'install/lib')+':'+str(private/'install/lib64')
    return env

def check_software():
    if not RECEIVER.is_file():raise RuntimeError('Preserved receiver source is missing: '+str(RECEIVER))
    ast.parse(RECEIVER.read_text())
    ast.parse(CAPTURE.read_text())
    runtime_dir = ROOT / 'rx_runtime'
    receipt_error = 'Private RX build is missing or outdated. Run ./BUILD_QUIET_RX.sh.'
    try:
        receipt = json.loads((runtime_dir / 'ready.json').read_text())
        hashes = receipt['sha256']
        if receipt['capture_io_version'] != 1 or hashes['capture-io.patch'] != hashlib.sha256(
                (runtime_dir / 'capture-io.patch').read_bytes()).hexdigest():
            raise ValueError(receipt_error)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(receipt_error) from exc
    for name in ('gnuradio.gr','gnuradio.uhd','gnuradio.qtgui','PyQt5.Qt','ieee802_11'):
        importlib.import_module(name)
    module=importlib.import_module('ieee802_11')
    private = (runtime_dir / 'install').resolve()
    if not Path(module.__file__).resolve().is_relative_to(private):
        raise RuntimeError('Capture requires the private RX runtime. Run BUILD_QUIET_RX.sh.')
    if not hasattr(module.extract_csi,'set_channel'):
        raise RuntimeError('Installed CSI block lacks the required channel setter.')

    sys.path.insert(0,str(RECEIVER.parent))
    importlib.import_module('wifi_rx')
    from gnuradio import gr
    libraries = {Path(line.split()[-1]) for line in Path('/proc/self/maps').read_text().splitlines()
                 if '/' in line and ('libgnuradio-ieee802_11.so' in line or 'ieee802_11_python.' in line)}
    if not libraries or any(not item.resolve().is_relative_to(private) for item in libraries):
        raise RuntimeError('Capture loaded an unexpected CSI shared library.')
    if any(hashes.get(str(item.resolve().relative_to(runtime_dir.resolve()))) !=
           hashlib.sha256(item.read_bytes()).hexdigest() for item in libraries):
        raise RuntimeError(receipt_error)
    sources = [ROOT/'receiver_report.py', RECEIVER, CAPTURE, ROOT/'capture_paths.py', ROOT/'stream_quality.py', ROOT/'run_paired.py',
               ROOT/'start_csi_rx.py', ROOT/'rx_runtime/capture-io.patch', ROOT/'COLLECTION_SETUP.json']
    ref=subprocess.run(['git','-C',str(RECEIVER.parent),'rev-parse','HEAD'],text=True,capture_output=True)
    return dict(base_flowgraph_revision=ref.stdout.strip() or None, python=sys.version, kernel=platform.release(), gnuradio=gr.version(),
                uhd=subprocess.check_output(['uhd_config_info','--version'],text=True).strip(),
                module=module.__file__, sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [*sources,*sorted(libraries)]})


def direct_interface(address):
    target=ipaddress.IPv4Address(address)
    rows=json.loads(subprocess.check_output(['ip','-j','-4','address','show'],text=True))
    for row in rows:
        if row['ifname']=='lo':continue
        for a in row.get('addr_info',[]):
            net=ipaddress.IPv4Network(f"{a['local']}/{a['prefixlen']}",strict=False)
            if target in net:
                if 'LOWER_UP' not in row.get('flags',[]):
                    raise RuntimeError('Interface '+row['ifname']+' has no cable link. Check the USRP power and Ethernet cable.')
                return row['ifname']
    raise RuntimeError('No local interface is configured for USRP '+address+'. Connect RX Ethernet and configure its private subnet first. This helper changes no network settings.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pid',choices=['P00','P04','P05'],default='P00')
    ap.add_argument('--session',default='S01')
    ap.add_argument('--block',choices=BLOCKS,help='Name of the matching phone block; no independent cue schedule is run.')
    ap.add_argument('--addr',default=os.environ.get('RX_ADDR','192.168.10.7'))
    ap.add_argument('--gain',type=float,default=12)
    ap.add_argument('--seconds',type=int,help='Timed P00 hardware rehearsal, without a phone.')
    ap.add_argument('--check',action='store_true',help='Check software only, without opening hardware or creating data.')
    args=ap.parse_args()
    if args.seconds is not None and (args.seconds<1 or args.pid!='P00'):
        ap.error('--seconds requires P00 and a positive duration')
    if not re.fullmatch('S[0-9]{2}',args.session):ap.error('Session must be S01, S02, etc.')
    try:
        ipaddress.IPv4Address(args.addr)
        if not 0<=args.gain<=31.5:raise ValueError('Use an SBX receive gain from 0 to 31.5 dB.')
        environment=clean_environment()
        command=[sys.executable, '-c', 'import json,start_csi_rx as r; print(json.dumps(r.check_software()))']
        checked=subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True)
        if checked.returncode:
            raise RuntimeError(checked.stderr.strip() or checked.stdout.strip())
        runtime=json.loads(checked.stdout.splitlines()[-1])
        if args.check:
            print(json.dumps(runtime,indent=2));return 0
        ensure_receive_buffer()
        interface=direct_interface(args.addr)
        lockdir=ROOT/'data'
        lockdir.mkdir(parents=True,exist_ok=True)
        lease=(lockdir/f'rx_{args.addr}.lock').open('a')
        try:
            fcntl.flock(lease,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another collector owns this receiver.')
        speed=int((Path('/sys/class/net')/interface/'speed').read_text())
        if speed<1000:
            raise RuntimeError(f'{interface} negotiated only {speed} Mbit/s.')
        ping=subprocess.run(['ping','-n','-c','1','-W','2',args.addr],capture_output=True,text=True)
        if ping.returncode:raise RuntimeError('USRP '+args.addr+' did not answer. Check its address, power, and direct Ethernet connection.')
    except Exception as e:
        print('Receiver not started:',e);return 1
    sid=f'{args.pid}_{args.session}_CSI_{args.block or "capture"}_{time.strftime("%Y%m%d_%H%M%S")}_{secrets.token_hex(3)}'
    dest=ROOT/'data/csi'/args.pid/args.session/sid;dest.mkdir(parents=True,exist_ok=False)
    out=dest/'csi.csv';env=clean_environment()
    env.update(CSI_CHANNEL='1',RX_ADDR=args.addr,RX_GAIN=str(args.gain),
               CSI_TA='02:00:00:00:00:01',CSI_RA='02:00:00:00:00:02',CSI_OUT=str(out))
    env.update(CSI_INTERFACE=interface, CSI_TIMING_OUT=str(dest/'host_timing.csv'),
               CSI_DISABLE_PLOT_MESSAGES='1',QT_QPA_PLATFORM='offscreen')
    meta=dict(runtime=runtime, link_mbps=speed, disk_free_bytes=shutil.disk_usage(dest).free,
              allowed_cpus=sorted(os.sched_getaffinity(0)),
              timing_source='CSV host wall clock; host_timing.csv Linux monotonic processing time per packet',
              diagnostic_seconds=args.seconds, pid=args.pid,session=args.session,recording_id=sid,receiver_source=str(RECEIVER),
              block=args.block or '',helper_pid=os.getpid(),
              rx_address=args.addr,interface=interface,channel=1,frequency_hz=2412000000,
              rx_gain_db=args.gain,rx_port='RX2',csi_csv=str(out),started_epoch_us=time.time_ns()//1000,
              receiver_runtime='verified private RX build',
              receiver_entrypoint=str(CAPTURE),live_plots_enabled=False,
              phone_link='run_block.py links the matching phone plan. Receiver runs continuously; no independent cues.',
              status='starting')
    setup=ROOT/'COLLECTION_SETUP.json'
    if setup.is_file():meta['collection_setup']=json.loads(setup.read_text())
    def save():
        temp=dest/'metadata.json.tmp';temp.write_text(json.dumps(meta,indent=2)+'\n');temp.replace(dest/'metadata.json')
    save();print('CSI output:',out,flush=True)
    print('CSI receiver started for '+(args.block or 'manual capture')+'. The paired command controls its own phone run and shutdown.',flush=True)
    child=None
    try:
        with (dest/'receiver.log').open('x') as log:
            command=['/usr/bin/python3',str(CAPTURE)]
            if args.seconds:
                command.extend(['--seconds',str(args.seconds)])
            child=subprocess.Popen(command,cwd=ROOT,pass_fds=(lease.fileno(),),
                  env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',start_new_session=True)
            meta['status']='running';meta['receiver_pid']=child.pid;save()
            for line in child.stdout:
                sys.stdout.write(line);sys.stdout.flush();log.write(line);log.flush()
            code=child.wait();meta['status']='exited' if code==0 else 'receiver_error';meta['exit_code']=code
    except KeyboardInterrupt:
        print('\nStopping CSI receiver cleanly...',flush=True)
        if child and child.poll() is None:
            # The main reader stopped at Ctrl+C. Leaving its pipe undrained can
            # block GNU Radio's logging threads and prevent tb.wait() completing.
            drainer=drain_shutdown_output(child,dest/'receiver.log')
            child.send_signal(signal.SIGINT)
            try:child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                print('Receiver is slow to close; terminating only this owned receiver process.',flush=True)
                meta['shutdown_note']='SIGINT timed out after 15s; SIGTERM sent to this receiver only'
                child.terminate()
                try:child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print('Receiver still has not exited; retaining files and reporting stop pending.');meta['status']='stop_pending';save();return 1
            drainer.join(timeout=2)
        meta['status']='stopped' if child and child.returncode==0 else 'receiver_error'
    finally:
        meta['ended_epoch_us']=time.time_ns()//1000;meta['csv_bytes']=out.stat().st_size if out.exists() else 0;save()
    if args.seconds and meta['status']=='exited':
        from receiver_report import capture_report
        report=capture_report(dest)
        (dest/'bench_summary.json').write_text(json.dumps(report,indent=2))
        print(json.dumps({k:v for k,v in report.items() if k!='issues'}),flush=True)
        if report['issues']:
            print('Review required:',dest/'bench_summary.json',flush=True)
            return 1
    print('Saved CSI:',out,flush=True)
    return 0 if meta['status'] in ('stopped','exited') else 1

if __name__=='__main__':raise SystemExit(main())
