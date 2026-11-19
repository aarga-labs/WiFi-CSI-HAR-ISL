#!/usr/bin/env python3
"""Start the local controller, optionally install/connect the phone using USB."""
import argparse,json,os,socket,subprocess,sys,time,webbrowser
import urllib.request
import urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def controller_state(port,data):
    """Recognize our authenticated controller; never terminate a port owner."""
    with socket.socket() as sock:
        sock.settimeout(.5)
        if sock.connect_ex(('127.0.0.1',port))!=0:return 'free',None
    try:
        token=json.loads((Path(data)/'pairing.json').read_text())['token']
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/clock',headers={'X-Token':token})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req,timeout=2) as r:reply=json.loads(r.read(10000))
        if not isinstance(reply.get('controller_id'),str) or not isinstance(reply.get('receive_ns'),int):
            return 'other',None
        return 'collector',f'http://127.0.0.1:{port}/#token={token}'
    except (OSError,ValueError,KeyError,TypeError,urllib.error.URLError):return 'other',None

def open_existing(port,data):
    state,link=controller_state(port,data)
    if state=='collector':
        webbrowser.open(link)
        print(f'Collector is already running on port {port}. Opened its dashboard.')
        print('The existing controller and its recordings were left running. Keep its original terminal open.')
        return True
    return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wifi',action='store_true');ap.add_argument('--install',action='store_true',help='Install the app only if missing.');ap.add_argument('--reinstall',action='store_true',help='Explicitly update the installed APK; finish recording first.');ap.add_argument('--port',type=int,default=8765);args=ap.parse_args()
    if not 1<=args.port<=65535:ap.error('Port must be between 1 and 65535.')
    data=ROOT/'data';data.mkdir(exist_ok=True)
    state,_=controller_state(args.port,data)
    if state=='other':
        print(f'Port {args.port} belongs to another service or collector with a different key. Nothing was stopped.')
        print(f'Try this launcher with --port {args.port+1}, and enter that port in the phone app.');return 1
    adb_candidates=[Path.home()/'.cache/fyp_android_sdk/unpacked/platform-tools/platform-tools/adb',ROOT/'tools/adb']
    import shutil
    adb=shutil.which('adb') or next((str(p) for p in adb_candidates if p.is_file()),None)
    if not args.wifi:
        if not adb:
            print('Android platform-tools (adb) is required for USB. Use Wi-Fi mode or install platform-tools.');return 1
        output=subprocess.check_output([adb,'devices'],text=True);rows=[l.split() for l in output.splitlines()[1:] if l.strip()]
        if len(rows)!=1 or rows[0][1]!='device':
            print('Connect ONE phone by USB. Enable USB debugging and approve this computer on the unlocked phone.\n'+output);return 1
        if args.install or args.reinstall:
            installed=subprocess.run([adb,'shell','pm','path','org.aarga.fypcollector'],capture_output=True,text=True,check=False)
            if 'package:' not in installed.stdout:
                subprocess.run([adb,'install','-r',str(ROOT/'FYP_Phone_Collector.apk')],check=True)
            elif args.reinstall:
                # Updating an app stops its process. Refuse an update during a known active session.
                if state=='collector':
                    token=json.loads((data/'pairing.json').read_text())['token']
                    request=urllib.request.Request(f'http://127.0.0.1:{args.port}/api/state',headers={'X-Token':token})
                    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=3) as r:current=json.load(r)
                    if any(s['status'] in ('queued','recording','stopping') for s in current['sessions']):
                        print('Finish and save the active recording before updating the app.');return 1
                subprocess.run([adb,'install','-r',str(ROOT/'FYP_Phone_Collector.apk')],check=True)
            else:print('Phone app is already installed; leaving it unchanged.')
        subprocess.run([adb,'reverse',f'tcp:{args.port}',f'tcp:{args.port}'],check=True)
    if open_existing(args.port,data):return 0
    proc=subprocess.Popen([sys.executable,str(ROOT/'controller.py'),'--host','0.0.0.0' if args.wifi else '127.0.0.1','--port',str(args.port)])
    try:
        launch=data/'open_controller.json'
        start=time.time()
        while time.time()-start<8:
            if proc.poll() is not None:
                if open_existing(args.port,data):return 0
                print('Controller could not start. Check the message above. No existing service was stopped.');return 1
            if launch.exists() and launch.stat().st_mtime>start-0.2:break
            time.sleep(.15)
        if controller_state(args.port,data)[0]!='collector':
            print('Controller did not become ready. No existing recording was changed.');return 1
        link=json.loads(launch.read_text())['url'];webbrowser.open(link)
        print('\nController is open in your browser. Keep this terminal open. Ctrl+C ends the laptop controller.')
        print('Phone files are retained if the controller stops. Reopen to retry transfer.')
        if args.wifi:
            try:
                ips=subprocess.check_output(['hostname','-I'],text=True).strip();print('Laptop local addresses:',ips)
            except Exception:print('Find your laptop LAN address in network settings.')
            print('Enter http://YOUR_LAPTOP_LOCAL_ADDRESS:'+str(args.port)+' in the phone app. Use a trusted network; local HTTP is not encrypted.')
        proc.wait()
    except KeyboardInterrupt:pass
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
    return 0
if __name__=='__main__':sys.exit(main())
