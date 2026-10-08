"""P01-P05 CSI experiments. No training is performed on import.
Residual baseline inspired by ../Model_Detect-Activity-and-Gestures/cnn.py.
New split, quality, normalization, selection, multiscale and checkpoint pipeline.
"""
from pathlib import Path
import os, json, hashlib, random, shutil, zipfile, time, gc, platform
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfilt, sosfilt_zi, welch
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import f1_score, classification_report, confusion_matrix, roc_auc_score
import joblib
import torch
from torch import nn
from torch.nn import functional as F

VERSION = 'p1p5-fast-2h-v1'
PIDS = ['P01','P02','P03','P04','P05']
ACTIONS = ['walk','sitstand','pickup','lightswitch','drink','answerphone','eat','wipetable','tvremote','fall','chop_food','stir_pot']
SIGNS = ['HELLO','THANKYOU','LAMP','FAN','TELEVISION','COOK','WATER','HOT','HUNGRY','TOILET','CALL','HELP','PAIN','ACCIDENT']
FINE = ACTIONS + SIGNS
STATES = ['idle','activity','sign']
FS = 50
MAX_WIN = 6*FS
HOP = 10  # 0.2 seconds
CANDIDATES = [{'name':'residual4','kind':'residual','seconds':4},
              {'name':'multiscale4','kind':'multiscale','seconds':4}]
SESSION_DEADLINE = None

class SessionBudgetReached(RuntimeError):
    pass

DEFAULTS = dict(epochs=28, patience=4, min_epochs=8, steps_per_epoch=32,
                batch_size=256, lr=0.001, weight_decay=0.01, seed=17, tree_estimators=300)
VALIDATION_PID = {'P01':'P04','P02':'P05','P03':'P01','P04':'P02','P05':'P03'}

PROGRESS_PATH = None
CURRENT_JOB = ''

def progress(phase):
    if PROGRESS_PATH is not None:
        atomic_json(dict(time=time.time(), job=CURRENT_JOB, phase=phase), PROGRESS_PATH)




def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()


def atomic_json(obj,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)))
    os.replace(tmp,path)


def verify_data(root):
    root=Path(root)
    manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['participants']==PIDS, 'This notebook requires all five real participants.'
    for name,info in manifest['files'].items():
        f=(root/name).resolve()
        assert f.is_relative_to(root.resolve()),name
        assert f.is_file() and f.stat().st_size==info['bytes'],f'Missing/incomplete: {name}'
        assert sha256(f)==info['sha256'],f'Hash mismatch: {name}'
    return sha256(root/'manifest.json')


def extract_verified(archive, destination, expected_sha=''):
    archive=Path(archive); destination=Path(destination)
    if expected_sha: assert sha256(archive)==expected_sha, 'ZIP SHA256 mismatch: download again.'
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None,'Corrupt ZIP: download again.'
        base=destination.resolve()
        for member in z.infolist():
            p=(base/member.filename).resolve()
            assert p.is_relative_to(base),'Unsafe ZIP path'
            assert (member.external_attr>>16)&0o170000 != 0o120000,'Symlink in ZIP'
        z.extractall(destination)
    root=destination/'phase1'
    verify_data(root)
    return root


def resolve_csi(root,name):
    p=Path(root)/Path(name).name
    if not p.exists(): p=Path(str(p)+'.gz')
    assert p.exists(),p
    return p


def raw_to_stream(path):
    # No whole-recording fitted mean, PCA or noise-floor normalization.
    df=pd.read_csv(path)
    expected=['Packet','Timestamp_us','Channel']+[q for c in range(52) for q in (f'SC{c}_Re',f'SC{c}_Im')]
    assert list(df.columns)==expected,f'Unexpected CSI schema: {path}'
    t=df.Timestamp_us.to_numpy(np.int64)
    assert len(t)>100 and (np.diff(t)>0).all(),f'Invalid timestamps: {path}'
    assert df.Channel.eq(1).all(),f'Wrong channel: {path}'
    v=df.iloc[:,3:].to_numpy(np.float32)
    assert np.isfinite(v).all(),f'Nonfinite CSI: {path}'
    a=np.hypot(v[:,::2],v[:,1::2]); x=np.log(np.maximum(a,1e-6))
    rel=(t-t[0])/1e6
    grid=np.arange(0,rel[-1],0.01)
    # Resample at 100 Hz before low-pass and decimation to 50 Hz.
    xg=np.stack([np.interp(grid,rel,x[:,c]) for c in range(52)],axis=1)
    idx=np.clip(np.searchsorted(rel,grid),1,len(rel)-1)
    gap=rel[idx]-rel[idx-1]
    valid=gap<=0.100
    severe=gap>0.250
    sos=butter(2,[0.3,18.0],btype='bandpass',fs=100,output='sos')
    # Reset filter state following a severe gap. Mark warmup as unavailable.
    cuts=np.r_[0,np.flatnonzero(severe[:-1] & ~severe[1:])+1,len(grid)]
    hp=np.zeros_like(xg)
    for a0,b0 in zip(cuts[:-1],cuts[1:]):
        if b0<=a0: continue
        zi=sosfilt_zi(sos)[:,:,None]*xg[a0][None,None,:]
        hp[a0:b0],_=sosfilt(sos,xg[a0:b0],axis=0,zi=zi)
        valid[a0:min(a0+300,b0)]=False
    return dict(t=t[0]+np.round(grid[::2]*1e6).astype(np.int64),
                x=hp[::2].astype(np.float32), valid=valid[::2],
                severe=severe[::2], raw_first=int(t[0]),raw_last=int(t[-1]),
                rows=len(t), raw_rate=len(t)/rel[-1], max_gap_ms=float(np.diff(rel).max()*1000))


def infer_posture(r,part):
    if isinstance(r.get('posture'),str) and r['posture']: return r['posture'],'recorded'
    # Do not invent original story postures. Explicitly report unknown.
    if part=='signs_standing': return 'standing','part_name'
    return 'unknown','unrecorded'


def prepare(root,work):
    root=Path(root); work=Path(work); work.mkdir(parents=True,exist_ok=True)
    fingerprint=verify_data(root)
    log=pd.read_csv(root/'session_log.csv')
    log=log[log.status.eq('kept') & log.pid.isin(PIDS)].sort_values(['date','time']).drop_duplicates(['pid','part'],keep='last')
    assert set(log.pid)==set(PIDS)
    cache=work/'cache'; cache.mkdir(exist_ok=True)
    streams=[]; audit=[]; events=[]
    for take in log.itertuples():
        src=resolve_csi(root,take.csi_file)
        cp=cache/(src.name.replace('.csv','').replace('.gz','')+'.npz')
        # Source and preprocessing version fingerprint; never trust stale caches.
        key=hashlib.sha256((fingerprint+VERSION+take.csi_file).encode()).hexdigest()
        if cp.exists():
            with np.load(cp,allow_pickle=False) as z:
                cached={k:z[k] for k in z.files}
            s=cached if str(cached.pop('key'))==key else raw_to_stream(src)
        else: s=raw_to_stream(src)
        np.savez(cp,**s,key=key)
        s.update(pid=take.pid,part=take.part,file=take.csi_file,date=take.date,rx_gain=float(take.rx_gain))
        lab=pd.read_csv(root/'labels'/Path(take.label_file).name).fillna('')
        assert (lab.pid==take.pid).all()
        n=len(s['t']); s['state']=np.full(n,-1,np.int64); s['fine']=np.full(n,-1,np.int64)
        s['event']=np.full(n,-1,np.int64); s['events']=[]
        ev=lab[lab.type.isin(['activity','sign','idle'])].sort_values('t_start_us')
        last_end=None
        for ordinal,(_,r) in enumerate(ev.iterrows()):
            a,b=int(r.t_start_us),int(r.t_end_us)
            assert b>a,'Nonpositive label duration'
            assert last_end is None or a>=last_end,'Overlapping ground-truth labels'
            last_end=b
            posture,posture_source=infer_posture(r,take.part)
            e=dict(id=f'{take.csi_file}:{ordinal}',pid=take.pid,part=take.part,file=take.csi_file,
                   label=r.label,type=r.type,posture=posture,posture_source=posture_source,
                   trial=r.trial,script=r.script_id,run=r.run,step=r.step,
                   context=r.context,intent=r.intent,home_action=r.home_action,
                   t_start_us=a,t_end_us=b,date=take.date,
                   i0=int(np.searchsorted(s['t'],a)),i1=int(np.searchsorted(s['t'],b)),
                   covered=a>=s['raw_first'] and b<=s['raw_last'])
            if not e['covered']:
                e.update(eligible=False,reason='label_outside_recorded_CSI',quality_fraction=0.)
                events.append(e); continue
            i,j=e['i0'],e['i1']; assert j>i
            typ=STATES.index(r.type); fine=FINE.index(r.label) if r.label in FINE else -1
            assert r.type=='idle' or fine>=0,f'Unknown fine label {r.label}'
            quality=float(s['valid'][i:j].mean())
            e.update(eligible=True,reason='',quality_fraction=quality,
                     severe_gap=bool(s['severe'][i:j].any()))
            s['state'][i:j]=typ; s['fine'][i:j]=fine; s['event'][i:j]=len(s['events'])
            s['events'].append(e); events.append(e)
        # Protocol-defined short inter-trial gaps; no inferred labels in long breaks or stories.
        if take.part!='scripts':
            es=s['events']
            for a,b in zip(es[:-1],es[1:]):
                i,j=a['i1'],b['i0']
                if 0<(j-i)/FS<=7:
                    s['state'][i:j]=1 if take.part in ['actions','actions_seated'] else 0
        s['state'][~s['valid']]=-1; s['fine'][~s['valid']]=-1
        audit.append(dict(pid=take.pid,part=take.part,rows=int(s['rows']),rate=float(s['raw_rate']),
                          max_gap_ms=float(s['max_gap_ms']),events=len(s['events']),
                          usable_fraction=float(s['valid'].mean())))
        streams.append(s)
        print('Prepared',take.pid,take.part,round(float(s['raw_rate']),1),'rows/s',flush=True)
    pd.DataFrame(audit).to_csv(work/'recording_audit.csv',index=False)
    pd.DataFrame(events).to_csv(work/'event_coverage.csv',index=False)
    atomic_json(dict(version=VERSION,dataset=fingerprint,fs=FS,classes=FINE,
                     empty_references='QC only, excluded from training to avoid shared-day leakage'),work/'dataset_info.json')
    return streams,fingerprint


def fit_scale(streams):
    # Equal stream contribution; only training participants enter this function.
    stats=[]
    for s in streams:
        v=s['x'][s['valid'] & (s['state']>=0)][::5]
        if len(v): stats.append(np.mean(v.astype(np.float64)**2,axis=0))
    assert stats
    return np.maximum(np.sqrt(np.mean(stats,axis=0)),1e-4).astype(np.float32)


def window_ok(s,c):
    a,b=c-MAX_WIN//2,c+MAX_WIN//2
    return a>=0 and b<=len(s['x']) and not s['severe'][a:b].any() and s['valid'][a:b].mean()>=0.95


def examples(streams):
    rows=[]
    for si,s in enumerate(streams):
        for c in range(MAX_WIN//2,len(s['x'])-MAX_WIN//2+1,HOP):
            if not window_ok(s,c): continue
            a,b=c-FS,c+FS
            v=s['state'][a:b]; vals=np.bincount(v[v>=0],minlength=3)
            if vals.max()<0.8*(b-a): continue
            st=int(vals.argmax()); fv=s['fine'][a:b]
            fine=-1
            if st!=0:
                good=fv[fv>=0]
                if len(good)>=0.8*(b-a):
                    counts=np.bincount(good,minlength=len(FINE))
                    if counts.max()>=0.8*(b-a): fine=int(counts.argmax())
            rows.append((si,c,st,fine))
    assert rows,'No valid training windows'
    return np.asarray(rows,np.int64)


class WindowDataset(torch.utils.data.Dataset):
    def __init__(self,streams,rows,scale,seconds):
        self.streams,self.rows,self.scale,self.width=streams,rows,scale,int(seconds*FS)
    def __len__(self): return len(self.rows)
    def __getitem__(self,i):
        si,c,st,fi=self.rows[i]; half=self.width//2
        x=(self.streams[si]['x'][c-half:c+half]/self.scale).T.copy()
        return torch.from_numpy(np.clip(x,-20,20)),int(st),int(fi)


def sampling_weights(streams,rows):
    # Equal states; then equal fine classes; then equal participants within each class.
    keys=[(int(st),int(fi),streams[si]['pid']) for si,c,st,fi in rows]
    counts=pd.Series(keys).value_counts().to_dict()
    classes={st:set(fi for a,fi,p in keys if a==st) for st in range(3)}
    people={(st,fi):set(p for a,b,p in keys if (a,b)==(st,fi)) for st,fi,p in set(keys)}
    return torch.tensor([1/(counts[k]*len(classes[k[0]])*len(people[k[:2]])) for k in keys],dtype=torch.double)


class ResBlock(nn.Module):
    def __init__(self,cin,cout,dilation):
        super().__init__()
        self.body=nn.Sequential(nn.Conv1d(cin,cout,7,padding=3*dilation,dilation=dilation),
            nn.BatchNorm1d(cout),nn.GELU(),nn.Conv1d(cout,cout,7,padding=3*dilation,dilation=dilation),nn.BatchNorm1d(cout))
        self.skip=nn.Conv1d(cin,cout,1) if cin!=cout else nn.Identity()
    def forward(self,x): return F.gelu(self.body(x)+self.skip(x))


class MultiBlock(nn.Module):
    def __init__(self,cin,cout=96):
        super().__init__()
        self.reduce=nn.Conv1d(cin,24,1,bias=False)
        self.branches=nn.ModuleList([nn.Conv1d(24,24,k,padding=k//2,bias=False) for k in [9,19,39]])
        self.pool=nn.Sequential(nn.MaxPool1d(3,stride=1,padding=1),nn.Conv1d(cin,24,1,bias=False))
        self.norm=nn.GroupNorm(8,cout)
        self.skip=nn.Conv1d(cin,cout,1) if cin!=cout else nn.Identity()
        self.se=nn.Sequential(nn.AdaptiveAvgPool1d(1),nn.Conv1d(cout,16,1),nn.GELU(),nn.Conv1d(16,cout,1),nn.Sigmoid())
    def forward(self,x):
        z=self.reduce(x)
        h=self.norm(torch.cat([b(z) for b in self.branches]+[self.pool(x)],dim=1))
        return F.gelu(h*self.se(h)+self.skip(x))


class CSIModel(nn.Module):
    def __init__(self,arch):
        super().__init__(); self.arch=dict(arch)
        if arch['kind']=='residual':
            self.body=nn.Sequential(nn.BatchNorm1d(52),nn.Conv1d(52,32,5,padding=2),nn.BatchNorm1d(32),nn.GELU(),
                ResBlock(32,32,1),nn.MaxPool1d(2),ResBlock(32,48,2),nn.MaxPool1d(2),
                ResBlock(48,64,4),nn.MaxPool1d(2),ResBlock(64,64,8)); width=64
        else:
            self.body=nn.Sequential(MultiBlock(52),nn.AvgPool1d(2),MultiBlock(96),nn.AvgPool1d(2),MultiBlock(96)); width=96
        self.drop=nn.Dropout(0.3); self.state=nn.Linear(width*2,3); self.fine=nn.Linear(width*2,len(FINE))
    def forward(self,x):
        h=self.body(x); h=self.drop(torch.cat([h.mean(-1),h.amax(-1)],dim=1))
        return self.state(h),self.fine(h)


def augment(x):
    b,c,t=x.shape
    scale=torch.empty(b,1,1,device=x.device).uniform_(0.8,1.25)
    noise=torch.randn_like(x)*torch.empty(b,1,1,device=x.device).uniform_(0,0.08)
    keep=(torch.rand(b,c,1,device=x.device)>0.05)
    return (x*scale+noise)*keep


def require_kaggle_gpu():
    assert Path('/kaggle/working').is_dir(),'Training is restricted to Kaggle, as requested.'
    assert torch.cuda.is_available(),'Enable a GPU in Kaggle Settings before running training.'


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)


def checkpoint_save(payload,path):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp')
    with open(tmp,'wb') as f:
        torch.save(payload,f); f.flush(); os.fsync(f.fileno())
    if path.exists(): shutil.copy2(path,path.with_suffix('.previous.pt'))
    os.replace(tmp,path)


def trusted_load(path):
    # Only use checkpoints generated by this notebook / your own saved outputs.
    try: return torch.load(path,map_location='cpu',weights_only=False)
    except Exception:
        prev=Path(path).with_suffix('.previous.pt')
        if not prev.exists(): raise
        print('Recovering previous checkpoint:',prev)
        return torch.load(prev,map_location='cpu',weights_only=False)


def unwrapped(model): return model.module if isinstance(model,nn.DataParallel) else model


def predict(model,streams,scale,arch,batch=256,device=None):
    device=device or next(model.parameters()).device
    model.eval(); result=[]
    width=int(arch['seconds']*FS); half=width//2
    for s in streams:
        centers=np.arange(MAX_WIN//2,len(s['x'])-MAX_WIN//2+1,HOP)
        valid=np.array([window_ok(s,int(c)) for c in centers])
        ps=np.full((len(centers),3),np.nan,np.float32)
        pf=np.full((len(centers),len(FINE)),np.nan,np.float32)
        good=np.flatnonzero(valid)
        with torch.inference_mode():
            for start in range(0,len(good),batch):
                ix=good[start:start+batch]
                x=np.stack([(s['x'][c-half:c+half]/scale).T for c in centers[ix]])
                xt=torch.from_numpy(np.clip(x,-20,20)).to(device,non_blocking=True)
                with torch.autocast('cuda',dtype=torch.float16,enabled=str(device).startswith('cuda')):
                    a,b=model(xt)
                ps[ix]=a.float().softmax(-1).cpu().numpy(); pf[ix]=b.float().softmax(-1).cpu().numpy()
        result.append(dict(stream=s,centers=centers,ps=ps,pf=pf,valid=valid))
    return result


def segment_table(preds):
    rows=[]
    for p in preds:
        s=p['stream']; c=p['centers']
        for e in s['events']:
            if e['type'] not in ['activity','sign']: continue
            m=(c>=e['i0'])&(c<e['i1'])&p['valid']
            if m.any():
                ps=p['ps'][m].mean(0); pf=p['pf'][m].mean(0)
                start,end=(0,len(ACTIONS)) if e['type']=='activity' else (len(ACTIONS),len(FINE))
                pred=FINE[start+pf[start:end].argmax()]
                state=int(ps.argmax())
                # Explicit branch is clearer than relying on true event type for end-to-end identity.
                if state==1: hier=ACTIONS[pf[:len(ACTIONS)].argmax()]
                elif state==2: hier=SIGNS[pf[len(ACTIONS):].argmax()]
                else: hier='idle'
                action_prob=pf[:len(ACTIONS)]; action_prob=action_prob/(action_prob.sum()+1e-12)
            else:
                pred=hier='unavailable'; ps=np.array([np.nan]*3); action_prob=np.zeros(len(ACTIONS))
            rows.append(dict(**e,pred=pred,cnn_pred=pred,hier_pred=hier,p_sign=float(ps[2]),
                             pred_state='unavailable' if not m.any() else STATES[int(ps.argmax())],
                             scored_windows=int(m.sum()),action_prob=action_prob))
    return pd.DataFrame(rows)


def macro(frame,labels,pred='pred'):
    if frame.empty: return float('nan')
    labels=[c for c in labels if c in set(frame.label)]
    return float(f1_score(frame.label,frame[pred],labels=labels,average='macro',zero_division=0))


def validation_score(preds):
    d=segment_table(preds)
    scores=[]
    for story in [False,True]:
        for typ,labels in [('activity',ACTIONS),('sign',SIGNS)]:
            g=d[(d.part.eq('scripts')==story)&d.type.eq(typ)]
            if len(g): scores.append(macro(g,labels))
    g=d[d.part.eq('scripts')]
    if len(g): scores.append(float(f1_score(g.type,g.pred_state,labels=['activity','sign'],average='macro',zero_division=0)))
    return float(np.mean(scores))



# -------- Action baseline and held-out selection --------
def action_features(streams,scale):
    feats=[]; ids=[]; labels=[]
    for s in streams:
        if s['part'] not in ['actions','actions_seated']: continue
        for e in s['events']:
            if e['type']!='activity': continue
            c=(e['i0']+e['i1'])//2
            if not window_ok(s,c): continue
            x=(s['x'][c-2*FS:c+2*FS]/scale).T
            power=x*x; env=power.mean(0).reshape(20,-1).mean(1); env=env/(env.sum()+1e-9)
            freq,psd=welch(x,fs=FS,nperseg=100,axis=1)
            bands=np.stack([psd[:,(freq>=a)&(freq<b)].sum(1) for a,b in [(0.3,1),(1,2),(2,4),(4,8),(8,18)]])
            bands=bands/(bands.sum(0,keepdims=True)+1e-9)
            f=np.concatenate([np.log(power.mean(1)+1e-9),np.mean(np.abs(np.diff(x,axis=1)),axis=1),
                np.quantile(x,0.9,axis=1)-np.quantile(x,0.1,axis=1),env,bands.mean(1),bands.std(1)])
            feats.append(f); ids.append(e['id']); labels.append(e['label'])
    return np.asarray(feats,np.float32),ids,np.asarray(labels)


def train_tree(train_streams,scale,path):
    require_kaggle_gpu()  # Also disallow CPU classifier training on the laptop.
    x,_,y=action_features(train_streams,scale)
    clf=ExtraTreesClassifier(n_estimators=300,min_samples_leaf=2,max_features=0.7,class_weight='balanced',random_state=17,n_jobs=2)
    clf.fit(x,y)
    tmp=Path(path).with_suffix('.tmp'); joblib.dump(clf,tmp); os.replace(tmp,path)
    return clf


def tree_predictions(clf,streams,scale):
    x,ids,y=action_features(streams,scale)
    if not len(x): return {}
    out=np.zeros((len(x),len(ACTIONS)),np.float32)
    out[:,[ACTIONS.index(c) for c in clf.classes_]]=clf.predict_proba(x)
    return dict(zip(ids,out))


def fuse_table(frame,tree_probs,weight):
    frame=frame.copy()
    frame['tree_pred']='unavailable'
    for i,r in frame.iterrows():
        if r['id'] not in tree_probs: continue
        pe=tree_probs[r['id']]
        frame.at[i,'tree_pred']=ACTIONS[int(pe.argmax())]
        if r['scored_windows']:
            prob=(1-weight)*r.action_prob+weight*pe
            frame.at[i,'pred']=ACTIONS[int(prob.argmax())]
    return frame


DEFAULT_INTENT={'HELLO':('I4','wake_system'),'THANKYOU':('I4','confirm_close'),
 'LAMP':('I1','toggle_light'),'FAN':('I1','toggle_fan'),'TELEVISION':('I1','toggle_tv'),
 'COOK':('I1','cooking_mode'),'WATER':('I2','bring_water_reminder'),'HOT':('I2','cool_room'),
 'HUNGRY':('I2','food_request'),'TOILET':('I2','toilet_assist'),'CALL':('I3','call_caregiver'),
 'HELP':('I3','notify_caregiver'),'PAIN':('I3','health_alert'),'ACCIDENT':('I3','emergency_alert')}
ANCHOR={'eat':'meal','drink':'meal','chop_food':'meal','stir_pot':'meal',
        'tvremote':'tv','answerphone':'tv','wipetable':'cleaning','pickup':'cleaning','fall':'after_fall'}


def intent(sign,context):
    if sign=='HOT' and context=='meal': return ('I3','kitchen_hazard_alert')
    if sign=='HELP' and context=='after_fall': return ('I3','emergency_alert')
    return DEFAULT_INTENT.get(sign,('unknown','unknown'))


def true_runs(mask):
    edges=np.diff(np.r_[False,mask,False].astype(int))
    return list(zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)))


def commands(p,tau):
    # Offline centered windows; 1-second trailing probability average.
    ps=p['ps']; valid=p['valid']; n=len(ps)
    raw=np.nan_to_num(ps[:,2]); kernel=np.ones(5)
    den=np.convolve(valid.astype(float),kernel,'full')[:n]
    sm=np.convolve(raw,kernel,'full')[:n]/np.maximum(den,1)
    mask=(sm>=tau)&valid&(den>=5)
    # Consecutive signs in a story can have no idle gap. Split only when a
    # different predicted identity persists for at least one second.
    identities=np.nan_to_num(p['pf'][:,len(ACTIONS):]).argmax(1)
    intervals=[]
    for a,b in true_runs(mask):
        start=a; active=int(identities[a]); pending=None; since=a
        for j in range(a+1,b):
            label=int(identities[j])
            if label==active: pending=None
            elif label!=pending: pending=label; since=j
            elif j-since+1>=5:
                intervals.append((start,since)); start=since; active=label; pending=None
        intervals.append((start,b))
    out=[]
    for a,b in intervals:
        if (b-a)*HOP/FS<1.: continue
        prob=np.nanmean(p['pf'][a:b,len(ACTIONS):],axis=0)
        label=SIGNS[int(prob.argmax())]
        i0=int(p['centers'][a]-HOP//2); i1=int(p['centers'][b-1]+HOP//2)
        # Context uses only predicted prior activity frames, never true context.
        recent=(p['centers']<i0)&(p['centers']>=i0-120*FS)&valid
        good=np.flatnonzero(recent & (np.nan_to_num(ps[:,1])>=0.6))
        ctx='isolated'
        for j in good:
            action=ACTIONS[int(p['pf'][j,:len(ACTIONS)].argmax())]
            if action in ANCHOR: ctx=ANCHOR[action]
        cat,home=intent(label,ctx)
        out.append(dict(i0=i0,i1=i1,label=label,context=ctx,intent=cat,home_action=home))
    return out


def event_metrics(preds,tau):
    totals=dict(n_true=0,n_pred=0,detected=0,identified=0,intent_correct=0,false_on_routine=0,routine_seconds=0.)
    allcommands=[]
    for p in preds:
        s=p['stream']
        if s['part']!='scripts': continue
        gt=[e for e in s['events'] if e['type']=='sign']
        cmds=commands(p,tau); totals['n_true']+=len(gt); totals['n_pred']+=len(cmds)
        # Match detection without using sign identity, one-to-one, highest IoU first.
        pairs=[]
        for i,c in enumerate(cmds):
            for j,e in enumerate(gt):
                inter=max(0,min(c['i1'],e['i1'])-max(c['i0'],e['i0']))
                union=max(c['i1'],e['i1'])-min(c['i0'],e['i0'])
                if inter and inter/union>=0.10: pairs.append((inter/union,i,j))
        used_c=set(); used_e=set()
        for _,i,j in sorted(pairs,reverse=True):
            if i in used_c or j in used_e: continue
            used_c.add(i); used_e.add(j); totals['detected']+=1
            correct=cmds[i]['label']==gt[j]['label']; totals['identified']+=int(correct)
            totals['intent_correct']+=int(correct and cmds[i]['intent']==gt[j]['intent'] and cmds[i]['home_action']==gt[j]['home_action'])
        # Denominator only measured routine time with model coverage, not all story wall time.
        covered=np.zeros(len(s['state']),bool)
        for c,v in zip(p['centers'],p['valid']):
            if v: covered[max(0,c-HOP//2):min(len(covered),c+HOP//2)]=True
        routine=(s['state']==1)&covered
        totals['routine_seconds']+=float(routine.sum()/FS)
        for i,c in enumerate(cmds):
            midpoint=(c['i0']+c['i1'])//2
            if i not in used_c and 0<=midpoint<len(routine) and routine[midpoint]: totals['false_on_routine']+=1
            allcommands.append(dict(pid=s['pid'],file=s['file'],matched=i in used_c,**c))
    for key,count in [('detection',totals['detected']),('identity',totals['identified'])]:
        precision=count/max(totals['n_pred'],1); recall=count/max(totals['n_true'],1)
        totals[key+'_precision']=precision; totals[key+'_recall']=recall
        totals[key+'_f1']=2*precision*recall/max(precision+recall,1e-12)
    totals['intent_e2e']=totals['intent_correct']/max(totals['n_true'],1)
    totals['false_commands_per_routine_hour']=totals['false_on_routine']/max(totals['routine_seconds']/3600,1e-12)
    totals['tau']=float(tau)
    return totals,allcommands


def choose_tau(inner_predictions):
    rows=[]
    for tau in np.arange(0.2,0.901,0.05):
        rr=[event_metrics(p,float(tau))[0] for p in inner_predictions]
        rows.append(dict(tau=float(tau),identity_f1=float(np.mean([r['identity_f1'] for r in rr])),
                         detection_f1=float(np.mean([r['detection_f1'] for r in rr]))))
    # Identity first; detection breaks ties; then prefer a higher threshold.
    selected=max(rows,key=lambda r:(r['identity_f1'],r['detection_f1'],r['tau']))
    return selected['tau'],rows


def average_predictions(all_preds):
    result=[]
    for pos in range(len(all_preds[0])):
        p=all_preds[0][pos].copy()
        # NaNs at invalid frames are intentional; average only valid frames.
        for key in ['ps','pf']:
            p[key]=np.stack([a[pos][key] for a in all_preds]).mean(0)
        result.append(p)
    return result


def save_predictions(preds,path):
    arrays={}
    for i,p in enumerate(preds):
        for key in ['centers','ps','pf','valid']: arrays[f'{i}_{key}']=p[key]
        arrays[f'{i}_file']=np.array(p['stream']['file'])
    np.savez_compressed(path,**arrays)


def release(net):
    net.cpu(); torch.cuda.empty_cache(); gc.collect()


def report_fold(table,preds,tau,folder):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    table.drop(columns=['action_prob']).to_csv(folder/'segments.csv',index=False)
    metrics=[]; perclass=[]
    # Common 10 actions /14 signs; expanded results show actual support, never fictitious zeros.
    slices=[('isolated',table[table.part.ne('scripts')]),('stories_oracle_boundaries',table[table.part.eq('scripts')]),
            ('isolated_seated',table[table.part.isin(['actions_seated','signs_seated'])]),
            ('isolated_original_parts',table[table.part.isin(['actions','signs_standing'])])]
    for split,d in slices:
        for typ,names in [('activity',ACTIONS),('sign',SIGNS)]:
            g=d[d.type.eq(typ)]
            if g.empty: continue
            supported=[n for n in names if n in set(g.label)]
            values=dict(split=split,type=typ,n=len(g),supported_classes=len(supported),
                        macro_f1=macro(g,supported),accuracy=float((g.label==g.pred).mean()),
                        cnn_macro_f1=macro(g,supported,'cnn_pred'),
                        unavailable=int(g.scored_windows.eq(0).sum()))
            if typ=='activity': values['common10_macro_f1']=macro(g[g.label.isin(ACTIONS[:10])],ACTIONS[:10])
            metrics.append(values)
            rep=classification_report(g.label,g.pred,labels=supported,output_dict=True,zero_division=0)
            for label in supported: perclass.append(dict(split=split,type=typ,label=label,**rep[label]))
    ev,cmd=event_metrics(preds,tau)
    atomic_json(ev,folder/'story_events.json'); pd.DataFrame(cmd).to_csv(folder/'predicted_commands.csv',index=False)
    pd.DataFrame(metrics).to_csv(folder/'metrics.csv',index=False)
    pd.DataFrame(perclass).to_csv(folder/'per_class.csv',index=False)
    st=table[table.part.eq('scripts')]; good=st.p_sign.notna()
    atomic_json(dict(story_auc=roc_auc_score(st.loc[good,'type'].eq('sign'),st.loc[good,'p_sign']) if st.loc[good,'type'].nunique()==2 else None,
                     story_hierarchical_accuracy=float(st.label.eq(st.hier_pred).mean()),
                     story_oracle_boundary_note='Fine identity uses known event boundaries/type; event detection and intent metrics do not.',
                     missing_prediction_policy='Fully covered labels without usable windows remain as unavailable and count as misses.'),folder/'context.json')








def archive_outputs(out,only_fold=None):
    out=Path(out); base=out.parent
    name=f'FYP_{only_fold}_checkpoint_bundle' if only_fold else 'FYP_all_checkpoints_and_results'
    dest=base/(name+'.zip'); tmp=dest.with_suffix('.zip.part')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in out.rglob('*'):
            if not p.is_file() or 'cache' in p.parts or p.suffix in ['.tmp','.part']: continue
            rel=p.relative_to(out)
            if only_fold and len(rel.parts)>1 and rel.parts[0] not in [only_fold]: continue
            if only_fold and len(rel.parts)==1 and rel.name not in ['fyp_pipeline.py','dataset_info.json','environment.json','recording_audit.csv','event_coverage.csv']: continue
            z.write(p,Path('results')/rel)
    tmp.replace(dest)
    atomic_json(dict(sha256=sha256(dest),bytes=dest.stat().st_size),dest.with_suffix('.zip.json'))
    return dest




def summarize(out):
    import matplotlib.pyplot as plt
    out=Path(out); frames=[]; metrics=[]; events=[]
    for pid in PIDS:
        if not (out/pid/'complete.json').exists(): continue
        d=pd.read_csv(out/pid/'segments.csv'); frames.append(d)
        m=pd.read_csv(out/pid/'metrics.csv'); m['pid']=pid; metrics.append(m)
        ev=json.loads((out/pid/'story_events.json').read_text()); ev['pid']=pid; events.append(ev)
    if not frames: print('No completed folds yet.'); return
    d=pd.concat(frames,ignore_index=True); m=pd.concat(metrics,ignore_index=True); ev=pd.DataFrame(events)
    d.to_csv(out/'all_out_of_fold_predictions.csv',index=False); m.to_csv(out/'fold_metrics.csv',index=False); ev.to_csv(out/'story_metrics.csv',index=False)
    figures=out/'figures'; figures.mkdir(exist_ok=True)
    fig,ax=plt.subplots(figsize=(10,5))
    for pid in PIDS:
        for path in sorted((out/pid/'models').glob('seed_*/history.csv')):
            h=pd.read_csv(path)
            ax.plot(h.epoch,h.loss,label=f'{pid} {path.parent.name}',alpha=0.7)
    ax.set_title('Final fold training losses'); ax.set_xlabel('Epoch'); ax.set_ylabel('Loss')
    ax.legend(fontsize=7,ncol=3); fig.tight_layout(); fig.savefig(figures/'training_curves.png',dpi=160); plt.show(); plt.close(fig)
    for typ,names in [('activity',ACTIONS),('sign',SIGNS)]:
        for source,mask in [('isolated',d.part.ne('scripts')),('stories_oracle',d.part.eq('scripts'))]:
            g=d[mask & d.type.eq(typ)]
            if g.empty: continue
            report=classification_report(g.label,g.pred,labels=names,output_dict=True,zero_division=0)
            per=pd.DataFrame([dict(label=n,**report[n]) for n in names]); per.to_csv(out/f'{source}_{typ}_per_class.csv',index=False)
            fig,ax=plt.subplots(figsize=(11,5)); values=per['f1-score'].to_numpy()
            ax.bar(names,values,color=['#187b62' if v>=0.6 else '#ca8a32' for v in values]); ax.set_ylim(0,1)
            ax.set_ylabel('F1'); ax.set_title(f'{source.replace("_"," ")} — {typ}; pooled held-out predictions')
            ax.tick_params(axis='x',rotation=55); fig.tight_layout(); fig.savefig(figures/f'{source}_{typ}_f1.png',dpi=160); plt.show(); plt.close(fig)
            # Rectangular confusion includes idle / unavailable instead of silently dropping missed examples.
            pred_labels=names+['idle','unavailable']+[n for n in FINE if n not in names]
            cm=np.array([[(g.label.eq(a)&g.pred.eq(b)).sum() for b in pred_labels] for a in names])
            used=cm.sum(0)>0; cm=cm[:,used]; cols=np.array(pred_labels)[used]
            norm=cm/np.maximum(cm.sum(1,keepdims=True),1)
            fig,ax=plt.subplots(figsize=(11,8)); im=ax.imshow(norm,vmin=0,vmax=1,cmap='Blues')
            ax.set_xticks(range(len(cols)),cols,rotation=70); ax.set_yticks(range(len(names)),names)
            ax.set_xlabel('Predicted'); ax.set_ylabel('True'); ax.set_title(f'{source} {typ}: row-normalized confusion')
            fig.colorbar(im,ax=ax); fig.tight_layout(); fig.savefig(figures/f'{source}_{typ}_confusion.png',dpi=160); plt.show(); plt.close(fig)
    # Participant, posture, common-vs-expanded evidence remain visible.
    pp=[]
    for (pid,part,posture,typ),g in d.groupby(['pid','part','posture','type'],dropna=False):
        pp.append(dict(pid=pid,part=part,posture=posture,type=typ,n=len(g),macro_f1=macro(g,ACTIONS if typ=='activity' else SIGNS)))
    pd.DataFrame(pp).to_csv(out/'posture_participant_metrics.csv',index=False)
    summary=m.groupby(['split','type']).agg(mean_f1=('macro_f1','mean'),sd_f1=('macro_f1','std'),participants=('pid','nunique'),events=('n','sum')).reset_index()
    summary.to_csv(out/'summary.csv',index=False)
    fig,ax=plt.subplots(figsize=(9,5))
    iso=m[m.split.eq('isolated')].pivot(index='pid',columns='type',values='macro_f1'); iso.plot.bar(ax=ax,ylim=(0,1))
    ax.set_title('Unseen-participant performance'); ax.set_ylabel('Macro F1'); fig.tight_layout(); fig.savefig(figures/'participant_f1.png',dpi=160); plt.show(); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5)); ev.set_index('pid')[['detection_recall','identity_recall','intent_e2e']].plot.bar(ax=ax,ylim=(0,1))
    ax.set_title('Stories: detection, correct sign, correct intent'); fig.tight_layout(); fig.savefig(figures/'story_end_to_end.png',dpi=160); plt.show(); plt.close(fig)
    print(summary.to_string(index=False)); print(ev[['pid','n_true','detection_f1','identity_f1','intent_e2e','false_commands_per_routine_hour']].to_string(index=False))
    print('Completed participants:',sorted(d.pid.unique()),'of',PIDS)
    if len(frames)<5: print('PARTIAL EVALUATION — finish the remaining folds before reporting a five-person result.')
    return summary


def load_deployment(folder,device='cuda'):
    folder=Path(folder); card=json.loads((folder/'model_card.json').read_text()); nets=[]; scale=None
    for path in sorted(folder.glob('seed_*/best.pt')):
        ck=trusted_load(path); net=CSIModel(ck['arch']).to(device); net.load_state_dict(ck['model']); net.eval()
        nets.append(net); scale=ck['scale']
    assert nets,'No saved model weights'
    return nets,scale,card


def predict_unlabelled_csv(csv_path,model_folder,device='cuda'):
    nets,scale,card=load_deployment(model_folder,device)
    s=raw_to_stream(csv_path); s.update(file=Path(csv_path).name,pid='new',part='inference',events=[])
    pred=average_predictions([predict(n,[s],scale,card['arch'],device=device) for n in nets])[0]
    # Unlabelled continuous inference uses CNNs, not oracle-boundary ExtraTrees fusion.
    rows=[]
    for c,ps,pf,valid in zip(pred['centers'],pred['ps'],pred['pf'],pred['valid']):
        if not valid: label=state='unavailable'; confidence=0.
        else:
            state=STATES[int(ps.argmax())]
            labels=ACTIONS if state=='activity' else SIGNS
            f=pf[:len(ACTIONS)] if state=='activity' else pf[len(ACTIONS):]
            label='idle' if state=='idle' else labels[int(f.argmax())]
            confidence=float(ps.max())
        rows.append(dict(timestamp_us=int(s['t'][c]),state=state,label=label,state_confidence=confidence))
    return pd.DataFrame(rows),pd.DataFrame(commands(pred,card['tau']))

# Fast path: no DataLoader workers, no DataParallel. Each process owns one GPU.
def gpu_bank(streams,scale):
    offsets=np.cumsum([0]+[len(s['x']) for s in streams[:-1]])
    flat=np.concatenate([np.clip(s['x']/scale,-20,20) for s in streams],axis=0).T.copy()
    bank=torch.from_numpy(flat).cuda()
    rows=examples(streams)
    centers=rows[:,1]+offsets[rows[:,0]]
    return bank,torch.as_tensor(centers,device='cuda'),torch.as_tensor(rows[:,2:],device='cuda'),sampling_weights(streams,rows).float().cuda()


def fit_fast(tr,va,arch,cfg,folder,fingerprint,epochs=None,deadline=None):
    global CURRENT_JOB
    require_kaggle_gpu(); torch.set_num_threads(2); seed_all(cfg['seed'])
    torch.backends.cudnn.benchmark=True; torch.set_float32_matmul_precision('high')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    CURRENT_JOB=str(folder.relative_to(folder.parents[3])) if len(folder.parents)>3 else str(folder)
    progress('building GPU sample bank')
    scale=fit_scale(tr);bank,centers,targets,weights=gpu_bank(tr,scale)
    net=CSIModel(arch).cuda()
    optimizer=torch.optim.AdamW(net.parameters(),lr=cfg['lr'],weight_decay=cfg['weight_decay'])
    total=int(epochs or cfg['epochs'])
    scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=total,eta_min=1e-5)
    scaler=torch.amp.GradScaler('cuda'); width=int(arch['seconds']*FS)
    times=torch.arange(width,device='cuda')-width//2
    best=-1.;best_epoch=1;best_weights=None;bad=0;history=[]
    print(f'[JOB] {folder}: {total} epochs maximum, {cfg["steps_per_epoch"]} batches/epoch',flush=True)
    for epoch in range(total):
        if deadline is not None and time.time()>=deadline:
            if best_weights is None: raise SessionBudgetReached('No epoch completed before time budget.')
            break
        started=time.time();net.train();losses=[];progress(f'epoch {epoch+1} training')
        picks=torch.multinomial(weights,cfg['steps_per_epoch']*cfg['batch_size'],replacement=True).reshape(cfg['steps_per_epoch'],cfg['batch_size'])
        for step,ix in enumerate(picks):
            if step%8==0:
                progress(f'epoch {epoch+1}, batch {step+1}/{cfg["steps_per_epoch"]}')
                if deadline is not None and time.time()>=deadline:
                    raise SessionBudgetReached('GPU training budget reached between batches.')
            idx=centers[ix,None]+times[None,:]
            x=bank[:,idx].permute(1,0,2).contiguous();ys=targets[ix,0];yf=targets[ix,1]
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                st,fi=net(augment(x));loss=F.cross_entropy(st,ys,label_smoothing=0.03)
                has=yf>=0
                if has.any():loss=loss+F.cross_entropy(fi[has],yf[has],label_smoothing=0.05)
            if not torch.isfinite(loss):raise RuntimeError('Nonfinite loss; previous checkpoint is retained.')
            scaler.scale(loss).backward();scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(net.parameters(),1.)
            scaler.step(optimizer);scaler.update();losses.append(float(loss.detach()))
        scheduler.step()
        # Validate every two epochs, plus the last; no repeated full-stream check each epoch.
        score=None
        if va and ((epoch+1)%2==0 or epoch+1==total):
            progress(f'epoch {epoch+1} validation')
            score=validation_score(predict(net,va,scale,arch,cfg['batch_size']))
        improved=(not va) or (score is not None and score>best+1e-4)
        if improved:
            best=score if score is not None else 0.;best_epoch=epoch+1;bad=0
            best_weights={k:v.detach().cpu().clone() for k,v in net.state_dict().items()}
        elif score is not None:bad+=1
        history.append(dict(epoch=epoch+1,loss=float(np.mean(losses)),validation_score=score,seconds=time.time()-started))
        payload=dict(version=VERSION,arch=arch,classes=FINE,states=STATES,scale=scale,dataset=fingerprint,
            epoch=epoch+1,config=cfg,model={k:v.detach().cpu() for k,v in net.state_dict().items()},optimizer=optimizer.state_dict(),
            rng_python=random.getstate(),rng_numpy=np.random.get_state(),rng_torch=torch.get_rng_state(),rng_cuda=torch.cuda.get_rng_state_all(),
            scheduler=scheduler.state_dict(),scaler=scaler.state_dict(),train_participants=sorted({s['pid'] for s in tr}),
            validation_participants=sorted({s['pid'] for s in va}),history=history)
        progress(f'epoch {epoch+1} saving')
        checkpoint_save(payload,folder/'last.pt')
        if improved:
            checkpoint_save(dict(model=best_weights,arch=arch,classes=FINE,states=STATES,scale=scale,dataset=fingerprint,epoch=best_epoch),folder/'best.pt')
        pd.DataFrame(history).to_csv(folder/'history.csv',index=False)
        print(f'[EPOCH] {folder.name}/{arch["name"]} {epoch+1}/{total} loss={np.mean(losses):.4f} val={score} elapsed={time.time()-started:.1f}s',flush=True)
        progress(f'epoch {epoch+1} completed')
        if va and epoch+1>=cfg['min_epochs'] and bad>=cfg['patience']:break
    if best_weights is None:raise SessionBudgetReached('No validated model completed within the budget.')
    net.load_state_dict(best_weights)
    del bank,centers,targets,weights,optimizer,scheduler,scaler,picks
    torch.cuda.empty_cache()
    return net,scale,best_epoch,history


def fast_fold(streams,test,cfg,out,fingerprint,deadline):
    global CURRENT_JOB
    require_kaggle_gpu();out=Path(out);fold=out/test;fold.mkdir(parents=True,exist_ok=True)
    val=VALIDATION_PID[test]
    tr=[s for s in streams if s['pid'] not in [test,val]]
    va=[s for s in streams if s['pid']==val]
    refit=[s for s in streams if s['pid']!=test]
    te=[s for s in streams if s['pid']==test]
    assert not {test,val}&{s['pid'] for s in tr}
    rows=[];choices=[]
    for arch in CANDIDATES:
        net,scale,ep,_=fit_fast(tr,va,arch,cfg,fold/'selection'/arch['name'],fingerprint,deadline=deadline)
        progress('scoring validation participant')
        pred=predict(net,va,scale,arch,cfg['batch_size']);score=validation_score(pred)
        rows.append(dict(candidate=arch['name'],validation_pid=val,score=score,best_epoch=ep))
        choices.append((score,arch,ep,pred,segment_table(pred),scale))
        release(net);del net
    pd.DataFrame(rows).to_csv(fold/'validation_selection.csv',index=False)
    _,arch,ep,vpred,vd,scale=max(choices,key=lambda r:r[0])
    tau,tau_rows=choose_tau([vpred]);pd.DataFrame(tau_rows).to_csv(fold/'validation_thresholds.csv',index=False)
    progress('fitting validation action tree')
    tree=train_tree(tr,scale,fold/'selection_action_tree.joblib');tp=tree_predictions(tree,va,scale)
    fusion=[]
    for weight in [0.,0.5,1.]:
        g=fuse_table(vd,tp,weight);g=g[g.type.eq('activity')&g.part.ne('scripts')]
        fusion.append(dict(weight=weight,score=macro(g,ACTIONS)))
    weight=max(fusion,key=lambda r:r['score'])['weight']
    choice=dict(arch=arch,epochs=ep,tau=tau,action_tree_weight=weight,validation_pid=val,
                training_pids=[p for p in PIDS if p!=test],test_pid=test,validation_fusion=fusion,
                protocol='One fixed validation person within training people; single-seed refit. No full nested search.')
    atomic_json(choice,fold/'selection.json')
    net,scale,_,_=fit_fast(refit,[],arch,cfg,fold/'models'/f'seed_{cfg["seed"]}',fingerprint,epochs=ep,deadline=deadline)
    progress('predicting unseen test participant')
    pred=predict(net,te,scale,arch,cfg['batch_size']);d=segment_table(pred)
    release(net);del net
    progress('fitting final action tree')
    tree=train_tree(refit,scale,fold/'action_tree.joblib')
    d=fuse_table(d,tree_predictions(tree,te,scale),weight)
    save_predictions(pred,fold/'frame_predictions.npz');report_fold(d,pred,tau,fold)
    atomic_json(dict(test=test,version=VERSION,protocol='fast fixed-validation LOSO'),fold/'complete.json')
    print('[FOLD COMPLETE]',test,choice,flush=True);progress('fold completed')


def fast_final(streams,cfg,out,fingerprint,deadline):
    require_kaggle_gpu();out=Path(out)
    completed=[p for p in PIDS if (out/p/'complete.json').exists()]
    choices=[json.loads((out/p/'selection.json').read_text()) for p in completed]
    if choices:
        names=[c['arch']['name'] for c in choices]
        name=max([a['name'] for a in CANDIDATES],key=lambda x:names.count(x))
        relevant=[c for c in choices if c['arch']['name']==name]
        arch=next(a for a in CANDIDATES if a['name']==name)
        epochs=max(4,int(np.median([c['epochs'] for c in relevant])))
        tau=float(np.median([c['tau'] for c in relevant]))
        weight=float(pd.Series([c['action_tree_weight'] for c in choices]).mode().iloc[0])
    else:
        arch=CANDIDATES[0];epochs=12;tau=0.6;weight=0.
    final=out/'deployment_all5';final.mkdir(exist_ok=True)
    net,scale,_,_=fit_fast(streams,[],arch,cfg,final/f'seed_{cfg["seed"]}',fingerprint,epochs=epochs,deadline=deadline)
    release(net);del net
    progress('fitting all-five action tree')
    train_tree(streams,scale,final/'action_tree.joblib')
    atomic_json(dict(arch=arch,epochs=epochs,tau=tau,action_tree_weight=weight,classes=FINE,fs=FS,
        training_participants=PIDS,dataset=fingerprint,completed_evaluation_folds=completed,
        evaluation_status='complete' if len(completed)==5 else 'PARTIAL; do not report a five-fold mean',
        validation='All-five deployment refit has no independent accuracy score.',
        inference='Offline centered windows; continuous CNN inference; tree fusion only for isolated windows.'),final/'model_card.json')
    shutil.copy2(__file__,final/'fyp_fast.py');progress('deployment refit completed')
    print('[ALL-FIVE MODEL SAVED]',final,flush=True)


def fast_worker(spec_path):
    import joblib
    global PROGRESS_PATH,CURRENT_JOB
    spec=json.loads(Path(spec_path).read_text());PROGRESS_PATH=Path(spec['progress']);CURRENT_JOB=spec['pid']
    torch.set_num_threads(2)
    require_kaggle_gpu();progress('loading preprocessed data')
    streams=joblib.load(spec['streams'])
    try:
        if spec['pid']=='FINAL':fast_final(streams,spec['cfg'],spec['out'],spec['fingerprint'],spec['deadline'])
        else:fast_fold(streams,spec['pid'],spec['cfg'],spec['out'],spec['fingerprint'],spec['deadline'])
    except SessionBudgetReached as exc:
        print('[TIME BUDGET]',exc,flush=True);progress('time budget reached');return 75
    return 0


if __name__=='__main__':
    import sys
    if len(sys.argv)==3 and sys.argv[1]=='--worker':sys.exit(fast_worker(sys.argv[2]))
