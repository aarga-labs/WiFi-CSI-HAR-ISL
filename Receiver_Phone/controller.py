#!/usr/bin/env python3
"""Local, authenticated Android research recorder controller (stdlib only)."""
import argparse
import csv
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import sqlite3
import statistics
import threading
import time
import urllib.parse
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from collection_blocks import BLOCKS, configure_block, named_phases

ROOT = Path(__file__).resolve().parent
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
ACTIONS = ['walk','sitstand','pickup','lightswitch','drink','answerphone','eat',
           'wipetable','tvremote','fall','chop_food','stir_pot']
SIGNS = ['HELLO','THANKYOU','LAMP','FAN','TELEVISION','COOK','WATER','HOT',
         'HUNGRY','TOILET','CALL','HELP','PAIN','ACCIDENT']
REQUIRED = {'accelerometer.csv','gyroscope.csv','labels.csv','clock_sync.csv','metadata.json'}
MAX_UPLOAD = 512 * 1024 * 1024

def compact(x):
    return json.dumps(x, separators=(',', ':'), ensure_ascii=True)

def atomic_json(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('x') as f:
        f.write(json.dumps(data, indent=2)); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def make_plan(req, now_ns):
    import random
    req = configure_block(req, ACTIONS, SIGNS)
    pid = req.get('pid', '')
    if pid not in ('P00', 'P04', 'P05'): raise ValueError('Choose P00, P04 or P05.')
    tag = req.get('session', 'S01')
    if not re.fullmatch(r'S\d{2}', tag): raise ValueError('Session must be S01, S02, etc.')
    if req.get('block'):
        phases,provenance=named_phases(req)
        start=now_ns+5_000_000_000;cursor=start
        for i,p in enumerate(phases):
            p.update(index=i,start_ns=cursor,end_ns=cursor+round(p['duration_s']*1e9));cursor=p['end_ns']
        arm=req.get('arm','right')
        if arm not in ('right','left'):raise ValueError('Choose left or right forearm.')
        sid=f"{pid}_{tag}_{req['block']}_{time.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(3)}"
        return dict(session_id=sid,pid=pid,session=tag,block=req['block'],block_title=req['block_title'],
            mode=req['mode'],posture=req['posture'],arm=arm,requested_hz=50,phone_position='forearm',
            start_ns=start,end_ns=cursor,phases=phases,created_ns=now_ns,seed=None,
            class_order=list(dict.fromkeys(p['label'] for p in phases if p['kind']=='perform')),
            label_provenance='scheduled cues; physical movement boundaries not independently verified',
            cue_protocol='named_runs_previous_collection_v2',collection_protocol_version=2,
            paired_csi_id=req.get('paired_csi_id',''),paired_csi_csv=req.get('paired_csi_csv',''),**provenance)
    mode = req.get('mode', 'pilot')
    if mode not in ('pilot','isolated','meal','tv','cleaning','baseline','ordinary','still'):
        raise ValueError('Unknown recording mode.')
    posture = req.get('posture', 'unspecified')
    if posture not in ('standing','seated','changing','unspecified'):
        raise ValueError('Unknown posture.')
    if mode == 'still' and req.get('block') not in ('stand_still','sit_still'):
        raise ValueError('Choose stand_still or sit_still for a stillness block.')
    still_label = 'Sit still' if posture == 'seated' else 'Stand still'
    arm = req.get('arm', 'right')
    if arm not in ('right','left'): raise ValueError('Choose left or right forearm.')
    seed = int(req.get('seed') or secrets.randbelow(2**31))
    rng = random.Random(seed)
    phases = []
    def add(kind, label, secs, state='', trial=0):
        phases.append(dict(kind=kind, label=label, duration_s=secs, state=state, trial=trial))
    def event(label, trial):
        state = 'sign' if label in SIGNS else 'activity'
        add('ready', label, 3, '', trial)
        add('perform', label, 4 if state == 'sign' else 6, state, trial)
        add('rest', 'Stay still', 2, '', trial)
    add('baseline', still_label, 5, 'idle')
    add('sync', 'Three separated forearm movements — timing check only', 6)
    if mode == 'pilot':
        for i, label in enumerate(['walk','sitstand','drink','WATER','HELLO','COOK'], 1): event(label,i)
    elif mode == 'isolated':
        classes = req.get('classes', [])
        if not isinstance(classes,list) or not classes or len(set(classes)) != len(classes):
            raise ValueError('Choose a non-empty list of unique classes.')
        if any(x not in ACTIONS+SIGNS for x in classes): raise ValueError('Unknown class.')
        reps = int(req.get('reps', 5))
        if not 1 <= reps <= 10: raise ValueError('Use 1–10 repetitions.')
        if 'fall' in classes and (not req.get('fall_confirmed') or reps > 2):
            raise ValueError('Fall is off by default; enable deliberately, with at most two repetitions.')
        trials = classes * reps; rng.shuffle(trials)
        for i,label in enumerate(trials,1): event(label,i)
    elif mode in ('meal','tv','cleaning'):
        sequences = {
            'meal':['eat','HOT','eat','drink','WATER','drink','COOK','stir_pot','HUNGRY','eat','THANKYOU'],
            'tv':['sitstand','HELLO','tvremote','TELEVISION','tvremote','HOT','answerphone','CALL','lightswitch','LAMP'],
            'cleaning':['wipetable','FAN','wipetable','pickup','HELP','pickup','HELLO','wipetable','THANKYOU']}
        # One continuous recording with explicit, unscored changeover buffers.
        add('ready', 'Mixed sequence starts next', 5)
        for i,label in enumerate(sequences[mode],1):
            add('perform',label,6,'sign' if label in SIGNS else 'activity',i)
    elif mode == 'still':
        add('ready', still_label, 3)
        add('baseline', still_label, 60, 'idle')
    elif mode == 'baseline':
        add('ready','Standing baseline',3); add('baseline','Stand still',60,'idle')
        add('ready','Sit down; this transition is not scored',6)
        add('baseline','Sit still',60,'idle')
    else:
        add('ordinary','Normal movement, no intentional signs; log the performed actions afterwards',300,'activity')
    add('sync','Three separated forearm movements — timing check only',6)
    add('baseline',still_label,5,'idle')
    # Separate STOP (two beeps) from the next GO (one beep). Do not silently
    # assign activity/idle training targets to these preparation intervals.
    event_kinds={'perform','baseline','ordinary','sync'}
    separated=[]
    for p in phases:
        if separated and separated[-1]['kind'] in event_kinds and p['kind'] in event_kinds:
            separated.append(dict(kind='ready',label=p['label'],duration_s=2,state='',trial=p['trial']))
        separated.append(p)
    phases=separated
    start = now_ns + 5_000_000_000
    cursor = start
    for i,p in enumerate(phases):
        p.update(index=i, start_ns=cursor, end_ns=cursor+int(p['duration_s']*1e9))
        cursor=p['end_ns']
    sid=f"{pid}_{tag}_{req.get('block') or mode}_{time.strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(3)}"
    return dict(session_id=sid,pid=pid,session=tag,mode=mode,arm=arm,seed=seed,
                requested_hz=50,phone_position='forearm',start_ns=start,end_ns=cursor,
                phases=phases,label_provenance='scheduled cues, not independently video-verified movement boundaries',
                class_order=ACTIONS+SIGNS,created_ns=now_ns,
                cue_protocol='red_buffer_green_event_one_start_two_stop',
                mixed_transition_buffer_s=2,block=req.get('block',''),
                block_title=req.get('block_title',''),posture=posture,
                paired_csi_id=req.get('paired_csi_id',''),paired_csi_csv=req.get('paired_csi_csv',''))

def inspect_archive(path, expected):
    """Validate every byte before extraction. No arbitrary ZIP paths are accepted."""
    with zipfile.ZipFile(path) as z:
        infos=z.infolist(); names=[i.filename for i in infos]
        if len(names)!=len(set(names)) or set(names)!=REQUIRED|{'manifest.json'}:
            raise ValueError('Unexpected or duplicate archive members.')
        if sum(i.file_size for i in infos)>MAX_UPLOAD: raise ValueError('Archive expands too much.')
        for i in infos:
            if '/' in i.filename or '\\' in i.filename or i.file_size>MAX_UPLOAD:
                raise ValueError('Unsafe archive member.')
            if i.filename.endswith('.json') and i.file_size>1_000_000:
                raise ValueError('Metadata member is too large.')
            if (i.external_attr>>16)&0o170000 == 0o120000: raise ValueError('Symlinks forbidden.')
        manifest=json.loads(z.read('manifest.json'))
        if set(manifest)!=REQUIRED: raise ValueError('Manifest file set does not match.')
        for name in REQUIRED:
            h=hashlib.sha256(); count=0
            with z.open(name) as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b);count+=len(b)
            entry=manifest[name]
            if entry.get('sha256')!=h.hexdigest() or entry.get('bytes')!=count:
                raise ValueError('Member checksum mismatch: '+name)
        meta=json.loads(z.read('metadata.json'))
        if meta.get('session_id')!=expected['session_id'] or meta.get('pid')!=expected['pid']:
            raise ValueError('Session identity mismatch.')
        if not meta.get('device_id') or meta.get('status') not in ('complete','stopped','interrupted','sensor_error'):
            raise ValueError('Invalid device metadata.')
    return meta

def quality(folder):
    out={'review_required':True,'notes':['Cue intervals are not independently verified movements.',
         'Clock RTT is a diagnostic, not a guarantee of physical synchronization.']}
    for name in ('accelerometer','gyroscope'):
        prev=None; deltas=[]; count=0; bad=0; gaps=0; first=None; last=None
        with (folder/(name+'.csv')).open() as f:
            for r in csv.DictReader(f):
                try:
                    ts=int(r['sensor_elapsed_ns']); vals=[float(r[k]) for k in ('x','y','z')]
                    if not all(__import__('math').isfinite(v) for v in vals):bad+=1
                    if prev is not None:
                        dt=(ts-prev)/1e6
                        if dt<=0:bad+=1
                        else:deltas.append(dt);gaps+=dt>100
                    if first is None:first=ts
                    last=ts;prev=ts;count+=1
                except (ValueError,KeyError):bad+=1
        med=statistics.median(deltas) if deltas else None
        out[name]=dict(rows=count,invalid_rows_or_order=bad,gaps_over_100ms=gaps,
                       median_hz=round(1000/med,2) if med else None,
                       max_gap_ms=round(max(deltas),2) if deltas else None,
                       duration_s=(last-first)/1e9 if first is not None else 0)
    return out

class Store:
    def __init__(self, folder):
        self.root=Path(folder).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        self.db=sqlite3.connect(self.root/'controller.sqlite3',check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('''PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS device(id TEXT PRIMARY KEY, seen REAL, data TEXT);
          CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, device TEXT, status TEXT, plan TEXT, archive_sha TEXT);
          CREATE TABLE IF NOT EXISTS commands(id TEXT PRIMARY KEY, device TEXT, session TEXT, body TEXT, state TEXT, result TEXT, created REAL);
        ''');self.db.commit()
        cfg=self.root/'pairing.json'
        if cfg.exists():self.token=json.loads(cfg.read_text())['token']
        else:
            self.token=secrets.token_urlsafe(32);atomic_json(cfg,{'token':self.token});cfg.chmod(0o600)
        self.anchor_wall=time.time_ns();self.anchor_mono=time.monotonic_ns()
        self.controller_id=uuid.uuid4().hex
    def now(self):return self.anchor_wall+time.monotonic_ns()-self.anchor_mono
    def path(self,sid):
        if not ID_RE.fullmatch(sid):raise ValueError('Invalid session ID.')
        with self.lock:r=self.db.execute('SELECT plan FROM sessions WHERE id=?',(sid,)).fetchone()
        if not r:raise ValueError('Session not found.')
        p=json.loads(r['plan']);return self.root/'recordings'/p['pid']/p['session']/sid
    def command(self,device,sid,kind,payload=None):
        cid=uuid.uuid4().hex
        body=dict(id=cid,kind=kind,session_id=sid,payload=payload or {},controller_id=self.controller_id)
        self.db.execute('INSERT INTO commands VALUES(?,?,?,?,?,?,?)',
            (cid,device,sid,compact(body),'queued',None,time.time()));self.db.commit()
        return body
    def snapshot(self):
        with self.lock:
            devices=[dict(id=r['id'],seen_s_ago=round(time.time()-r['seen'],1),**json.loads(r['data']))
                for r in self.db.execute('SELECT * FROM device ORDER BY seen DESC')]
            sessions=[dict(id=r['id'],device=r['device'],status=r['status'],plan=json.loads(r['plan']),
                           archive_sha=r['archive_sha']) for r in self.db.execute('SELECT * FROM sessions ORDER BY rowid DESC LIMIT 30')]
            cmds=[dict(r) for r in self.db.execute('SELECT id,session,state,result FROM commands ORDER BY created DESC LIMIT 10')]
        return dict(devices=devices,sessions=sessions,commands=cmds,now_ns=self.now(),
                    controller_id=self.controller_id,classes={'actions':ACTIONS,'signs':SIGNS},
                    collection_blocks=list(BLOCKS),paired_commands_version=2,
                    disk_free_bytes=shutil.disk_usage(self.root).free,
                    wall_clock_difference_ms=(time.time_ns()-self.now())/1e6)

class Handler(BaseHTTPRequestHandler):
    server_version='FYPCollector/1.0'
    def log_message(self,fmt,*args):pass  # No credentials or participant URLs in logs.
    @property
    def store(self):return self.server.store
    def send(self,data,status=200):
        raw=compact(data).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def authorized(self):
        return hmac.compare_digest(self.headers.get('X-Token',''),self.store.token)
    def body(self):
        n=int(self.headers.get('Content-Length','0'))
        if not 0<n<=1_000_000:raise ValueError('Invalid JSON request size.')
        d=json.loads(self.rfile.read(n))
        if not isinstance(d,dict):raise ValueError('Expected a JSON object.')
        return d
    def do_GET(self):
        try:
            url=urllib.parse.urlsplit(self.path);path=url.path
            if path in ('/','/app.js','/cues.js','/style.css'):
                file=ROOT/'web'/({'/':'index.html','/app.js':'app.js','/cues.js':'cues.js','/style.css':'style.css'}[path])
                raw=file.read_bytes();self.send_response(200)
                self.send_header('Content-Type',{'/':'text/html; charset=utf-8','/app.js':'text/javascript','/cues.js':'text/javascript','/style.css':'text/css'}[path])
                self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store')
                self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'")
                self.end_headers();self.wfile.write(raw);return
            if not self.authorized():self.send({'error':'Pairing token required.'},401);return
            if path=='/api/clock':
                receive=self.store.now();self.send(dict(receive_ns=receive,send_ns=self.store.now(),controller_id=self.store.controller_id));return
            if path=='/api/state':self.send(self.store.snapshot());return
            if path=='/api/command':
                device=urllib.parse.parse_qs(url.query).get('device',[''])[0]
                with self.store.lock:
                    r=self.store.db.execute("SELECT body FROM commands WHERE device=? AND state='queued' ORDER BY created LIMIT 1",(device,)).fetchone()
                self.send({'command':json.loads(r['body']) if r else None});return
            self.send({'error':'Not found'},404)
        except (ValueError,KeyError,json.JSONDecodeError) as e:self.send({'error':str(e)},400)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_POST(self):
        try:
            if not self.authorized():self.send({'error':'Pairing token required.'},401);return
            origin=self.headers.get('Origin')
            if origin and urllib.parse.urlsplit(origin).netloc != self.headers.get('Host'):
                self.send({'error':'Cross-origin request rejected.'},403);return
            if self.path=='/api/upload':self.upload();return
            d=self.body();s=self.store
            with s.lock:
                if self.path in ('/api/register','/api/heartbeat'):
                    device=d.get('device_id','')
                    if not ID_RE.fullmatch(device):raise ValueError('Invalid device ID.')
                    s.db.execute('INSERT OR REPLACE INTO device VALUES(?,?,?)',(device,time.time(),compact(d)));s.db.commit()
                    self.send({'ok':True,'controller_id':s.controller_id});return
                if self.path=='/api/session':
                    active=s.db.execute("SELECT id FROM sessions WHERE status IN ('queued','recording','stopping')").fetchone()
                    if active:raise ValueError('Finish the active session first. If the phone was interrupted, reconnect it to recover the recording.')
                    device=d.get('device_id');r=s.db.execute('SELECT * FROM device WHERE id=?',(device,)).fetchone()
                    if not r or time.time()-r['seen']>8:raise ValueError('Phone not connected. Open and connect the phone app.')
                    info=json.loads(r['data'])
                    if not info.get('accelerometer') or not info.get('gyroscope'):raise ValueError('Both accelerometer and gyroscope are required.')
                    if info.get('active_session'):raise ValueError('Phone is already recording.')
                    if info.get('clock_controller_id')!=s.controller_id or info.get('clock_age_ms',1e9)>15000:
                        raise ValueError('Waiting for a fresh phone clock measurement.')
                    if info.get('clock_rtt_ms',1e9)>200:raise ValueError('Connection delay too high; check USB or local Wi-Fi.')
                    if shutil.disk_usage(s.root).free<1_000_000_000:raise ValueError('Less than 1 GB free on laptop.')
                    plan=make_plan(d,s.now());sid=plan['session_id']
                    dest=s.root/'recordings'/plan['pid']/plan['session']/sid;dest.mkdir(parents=True,exist_ok=False)
                    atomic_json(dest/'plan.json',plan);atomic_json(dest/'flags.json',[])
                    with (dest/'planned_labels.csv').open('w',newline='') as f:
                        w=csv.DictWriter(f,fieldnames=list(plan['phases'][0]));w.writeheader();w.writerows(plan['phases'])
                    s.db.execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(sid,device,'queued',compact(plan),None));s.db.commit()
                    cmd=s.command(device,sid,'START',plan);self.send({'ok':True,'session_id':sid,'command_id':cmd['id']});return
                if self.path in ('/api/stop','/api/retry','/api/flag'):
                    sid=d.get('session_id','');r=s.db.execute('SELECT * FROM sessions WHERE id=?',(sid,)).fetchone()
                    if not r:raise ValueError('Session not found.')
                    if self.path=='/api/flag':
                        p=s.path(sid)/'flags.json';flags=json.loads(p.read_text())
                        flags.append(dict(time_ns=s.now(),trial=d.get('trial'),note=str(d.get('note',''))[:500]));atomic_json(p,flags)
                        self.send({'ok':True});return
                    if self.path=='/api/stop':
                        # Cancel an undelivered start rather than allowing a late start after stop.
                        s.db.execute("UPDATE commands SET state='cancelled' WHERE session=? AND state='queued' AND json_extract(body,'$.kind')='START'",(sid,))
                        s.db.execute("UPDATE sessions SET status='stopping' WHERE id=? AND status IN ('queued','recording')",(sid,));s.db.commit()
                    cmd=s.command(r['device'],sid,'STOP' if self.path=='/api/stop' else 'UPLOAD')
                    self.send({'ok':True,'command_id':cmd['id']});return
                if self.path=='/api/ack':
                    r=s.db.execute('SELECT * FROM commands WHERE id=? AND device=?',(d.get('id'),d.get('device_id'))).fetchone()
                    if not r:raise ValueError('Unknown command acknowledgement.')
                    s.db.execute('UPDATE commands SET state=?,result=? WHERE id=?',
                                 ('done' if d.get('ok') else 'error',compact(d),r['id']))
                    kind=json.loads(r['body'])['kind']
                    if kind=='START':
                        s.db.execute("UPDATE sessions SET status=? WHERE id=? AND status='queued'",('recording' if d.get('ok') else 'start_failed',r['session']))
                    if kind=='STOP' and d.get('ok') and d.get('result',{}).get('not_started'):
                        s.db.execute("UPDATE sessions SET status='cancelled' WHERE id=? AND status='stopping'",(r['session'],))
                    s.db.commit();self.send({'ok':True});return
                raise ValueError('Unknown operation.')
        except (ValueError,KeyError,json.JSONDecodeError,zipfile.BadZipFile) as e:self.send({'error':str(e)},400)
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:
            print('Controller request failed:',type(e).__name__,str(e),flush=True)
            try:self.send({'error':'Local operation failed. Original phone files are retained.'},500)
            except OSError:pass
    def upload(self):
        s=self.store;sid=self.headers.get('X-Session-ID','');want=self.headers.get('X-SHA256','')
        if not ID_RE.fullmatch(sid) or not re.fullmatch('[0-9a-f]{64}',want):raise ValueError('Invalid transfer identity.')
        n=int(self.headers.get('Content-Length','0'))
        if not 0<n<=MAX_UPLOAD:raise ValueError('Archive size is invalid.')
        with s.lock:
            r=s.db.execute('SELECT * FROM sessions WHERE id=?',(sid,)).fetchone()
            if not r:raise ValueError('Unknown session.')
            expected=json.loads(r['plan']);dest=s.path(sid)
        tmp=dest/('upload_'+uuid.uuid4().hex+'.part')
        try:
            h=hashlib.sha256();left=n
            with tmp.open('xb') as f:
                while left:
                    b=self.rfile.read(min(left,1024*1024))
                    if not b:raise ValueError('Interrupted upload; retry from phone.')
                    f.write(b);h.update(b);left-=len(b)
                f.flush();os.fsync(f.fileno())
            if h.hexdigest()!=want:raise ValueError('Transfer checksum mismatch.')
            meta=inspect_archive(tmp,expected)
            if meta['device_id']!=r['device']:raise ValueError('Wrong phone for this session.')
            with s.lock:
                current=s.db.execute('SELECT archive_sha FROM sessions WHERE id=?',(sid,)).fetchone()['archive_sha']
                if current:
                    if current!=want:raise ValueError('A different archive already exists; no overwrite allowed.')
                    self.send({'ok':True,'sha256':want,'already_received':True});return
                phone=dest/'phone';original=dest/'phone_original.zip'
                # Recover a power/process interruption between file commit and DB commit.
                # The already committed content is only reused if every manifest entry matches.
                if phone.exists():
                    with zipfile.ZipFile(tmp) as z:incoming=json.loads(z.read('manifest.json'))
                    if json.loads((phone/'manifest.json').read_text())!=incoming:
                        raise ValueError('A different partial recording already exists; originals retained for review.')
                    for name,entry in incoming.items():
                        if not (phone/name).is_file() or digest(phone/name)!=entry['sha256']:
                            raise ValueError('Existing partial files need review; no overwrite performed.')
                    report=quality(phone);atomic_json(phone/'quality.json',report)
                else:
                    stage=dest/('phone_'+uuid.uuid4().hex+'.tmp');stage.mkdir()
                    try:
                        with zipfile.ZipFile(tmp) as z:
                            for name in sorted(REQUIRED|{'manifest.json'}):
                                with z.open(name) as a,(stage/name).open('xb') as b:shutil.copyfileobj(a,b)
                        report=quality(stage);atomic_json(stage/'quality.json',report)
                        os.rename(stage,phone)
                    finally:
                        if stage.exists():shutil.rmtree(stage)
                if original.exists():
                    if digest(original)!=want:raise ValueError('A different original ZIP exists; no overwrite performed.')
                else:os.rename(tmp,original)
                receipt=dict(sha256=want,received_ns=s.now(),bytes=n,phone_status=meta['status'])
                atomic_json(dest/'transfer_receipt.json',receipt)
                s.db.execute('UPDATE sessions SET status=?,archive_sha=? WHERE id=?',
                    ('received_'+meta['status'],want,sid));s.db.commit()
            self.send({'ok':True,'sha256':want,'quality':report})
        finally:
            if tmp.exists():tmp.unlink()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host',default='127.0.0.1',help='USB default: 127.0.0.1. Local Wi-Fi: 0.0.0.0.')
    ap.add_argument('--port',type=int,default=8765)
    ap.add_argument('--data-dir',default=str(ROOT/'data'))
    args=ap.parse_args();store=Store(args.data_dir)
    try:server=ThreadingHTTPServer((args.host,args.port),Handler)
    except OSError as e:
        store.db.close()
        if e.errno==98:
            print(f'Port {args.port} is already in use. Re-run the launcher to reopen the existing collector.',flush=True)
            return 1
        raise
    server.store=store;server.daemon_threads=True
    link=f'http://127.0.0.1:{args.port}/#token={store.token}'
    atomic_json(store.root/'open_controller.json',{'url':link,'port':args.port})
    # The private local launch link contains the pairing secret. Never publish it.
    print('FYP Phone Collector — keep this terminal open.',flush=True)
    print('Open the desktop launcher or the private link in data/open_controller.json.',flush=True)
    print('Recordings:',store.root/'recordings',flush=True)
    if args.host=='0.0.0.0':print('Local Wi-Fi mode: use your laptop LAN address in the phone app. No port forwarding.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();store.db.close()

if __name__=='__main__':raise SystemExit(main())
