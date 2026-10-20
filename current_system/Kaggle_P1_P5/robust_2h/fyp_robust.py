"""Fixed P1–P5 experiment. Import, preprocessing and inference never fit a model.

Real fitting requires Kaggle + CUDA. The shared module preserves the previous
dataset, coverage policy, event matching, class order and reporting definitions.
"""
from pathlib import Path
import copy
import gc
import json
import math
import os
import shutil
import sys
import time

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.nn import functional as F
import fyp_common as C

VERSION = 'p1p5-shape-spectrum-crossfit-v1'
ARCH = dict(name='shape_spectrum4', seconds=4, kind='shape_spectrum')
CFG = dict(batch_size=256, lr=8e-4, weight_decay=0.02, seed=17,
           contrastive_weight=0.08, ema_decay=0.995, validate_seconds=25,
           fit_seconds=540, checkpoint_seconds=50, restart_epochs=60,
           final_seeds=[137,271])
PIDS, ACTIONS, SIGNS, FINE = C.PIDS, C.ACTIONS, C.SIGNS, C.FINE
PROGRESS = None


def inner_plan(out,work,streams,fingerprint,cfg,deadline):
    out,work=Path(out),Path(work);jobs=[]
    for ti,test in enumerate(PIDS):
        for vi,val in enumerate(PIDS):
            if val==test:continue
            name=test+'__val_'+val
            jobs.append(dict(pid=name,job='inner',test=test,val=val,seed=17+ti*100+vi*13,
                folder=str(out/test/'models'/('val_'+val)),out=str(out),streams=str(streams),
                fingerprint=fingerprint,cfg=dict(cfg),deadline=deadline,max_job_seconds=11*60,
                spec_path=str(work/(name+'.json')),progress=str(work/(name+'.progress.json'))))
    return jobs


def progress(phase):
    if PROGRESS:
        C.atomic_json(dict(time=time.time(), phase=phase), PROGRESS)


class Block(nn.Module):
    def __init__(self, cin, cout, dilation=1):
        super().__init__()
        self.reduce=nn.Conv1d(cin,24,1,bias=False)
        self.branches=nn.ModuleList([nn.Conv1d(24,24,k,padding=(k//2)*dilation,
                                              dilation=dilation,bias=False) for k in [7,15,31]])
        self.pool=nn.Sequential(nn.AvgPool1d(3,1,1),nn.Conv1d(cin,24,1,bias=False))
        self.norm=nn.GroupNorm(8,96)
        self.skip=nn.Conv1d(cin,cout,1,bias=False) if cin!=cout else nn.Identity()
        self.se=nn.Sequential(nn.AdaptiveAvgPool1d(1),nn.Conv1d(cout,16,1),
                              nn.GELU(),nn.Conv1d(16,cout,1),nn.Sigmoid())
    def forward(self,x):
        z=self.reduce(x)
        h=self.norm(torch.cat([branch(z) for branch in self.branches]+[self.pool(x)],1))
        return F.gelu(h*self.se(h)+self.skip(x))


class ShapeSpectrumCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.temporal=nn.Sequential(Block(52,96),nn.AvgPool1d(2),Block(96,96),
                                     nn.AvgPool1d(2),Block(96,96,dilation=2))
        self.attention=nn.Sequential(nn.Conv1d(96,32,1),nn.Tanh(),nn.Conv1d(32,1,1))
        self.spectral=nn.Sequential(nn.Linear(52*4,64),nn.LayerNorm(64),nn.GELU(),nn.Dropout(.2))
        self.embedding=nn.Sequential(nn.Linear(96*3+64+2,192),nn.LayerNorm(192),nn.GELU(),nn.Dropout(.35))
        self.detector=nn.Linear(192,3)
        self.action=nn.Linear(192,len(ACTIONS));self.sign=nn.Linear(192,len(SIGNS))
        self.project=nn.Sequential(nn.Linear(192,128),nn.GELU(),nn.Linear(128,64))
        freq=torch.fft.rfftfreq(200,d=1/C.FS)
        self.register_buffer('bands',torch.stack([(freq>=lo)&(freq<hi) for lo,hi in [(0.5,2),(2,5),(5,10),(10,18.01)]]))

    def forward(self,x,with_embedding=False):
        # Spectral calculations stay in FP32 under mixed precision.
        with torch.autocast(device_type=x.device.type,enabled=False):
            xf=x.float();energy=xf.square().mean((1,2)).clamp_min(1e-5)
            velocity=(xf[:,:,1:]-xf[:,:,:-1]).square().mean((1,2)).clamp_min(1e-5)
            shape=(xf/energy.sqrt()[:,None,None]).clamp(-20,20)
            spectrum=torch.fft.rfft(shape,dim=-1).abs().square()/shape.shape[-1]
            bands=torch.stack([spectrum[:,:,mask].mean(-1) for mask in self.bands],-1)
            bands=torch.log1p(bands).flatten(1)
        h=self.temporal(shape)
        w=self.attention(h).float().softmax(-1)
        mean=(h*w).sum(-1)
        std=((h.float()-mean[:,:,None]).square()*w).sum(-1).clamp_min(1e-5).sqrt()
        z=self.embedding(torch.cat([mean,std,h.amax(-1),self.spectral(bands),
                                    energy.log()[:,None],velocity.log()[:,None]],1))
        st=self.detector(z)
        # Each identity head has its own normalized distribution. The common
        # reporting adapter's 26-way softmax gives each type half the mass.
        fi=torch.cat([F.log_softmax(self.action(z).float(),1),F.log_softmax(self.sign(z).float(),1)],1)
        return (st,fi,self.project(z)) if with_embedding else (st,fi)


def balanced_weights(streams,rows):
    """Equal state, fine class, person, source/posture, then event contribution."""
    keys=[]
    for si,c,st,fi in rows:
        s=streams[si];eid=int(s['event'][c])
        posture=s['events'][eid]['posture'] if eid>=0 else 'transition'
        # Per-event balancing avoids a six-second repetition outweighing a
        # four-second one. Unknown original postures remain unknown.
        keys.append((int(st),int(fi),s['pid'],s['part'],posture,int(si),eid))
    prefix_counts={}
    for level in range(1,8):
        prefix_counts[level]={}
        for key in set(keys):
            parent=key[:level-1]
            prefix_counts[level].setdefault(parent,set()).add(key[:level])
    counts=pd.Series(keys).value_counts().to_dict()
    weights=[]
    for key in keys:
        probability=1.
        for level in range(1,8): probability/=len(prefix_counts[level][key[:level-1]])
        weights.append(probability/counts[key])
    return torch.tensor(weights,dtype=torch.float32)


def make_bank(streams,device='cuda'):
    scale=C.fit_scale(streams)
    rows=C.examples(streams)
    offsets=np.cumsum([0]+[len(s['x']) for s in streams[:-1]])
    bank=torch.as_tensor(np.concatenate([np.clip(s['x']/scale,-20,20) for s in streams]).T.copy(),device=device)
    center=torch.as_tensor(rows[:,1]+offsets[rows[:,0]],device=device)
    targets=torch.as_tensor(rows[:,2:],device=device)
    pids=torch.as_tensor([PIDS.index(streams[si]['pid']) for si in rows[:,0]],device=device)
    weights=balanced_weights(streams,rows).to(device)
    return bank,center,targets,pids,weights,scale


def augment(x):
    rms=x.square().mean((1,2),keepdim=True).sqrt().clamp_min(1e-3)
    gain=torch.empty(len(x),1,1,device=x.device).uniform_(.75,1.35)
    channel=torch.empty(len(x),52,1,device=x.device).uniform_(.9,1.1)
    sign=torch.where(torch.rand(len(x),1,1,device=x.device)<.5,-1.,1.)
    noise=torch.randn_like(x)*rms*torch.empty(len(x),1,1,device=x.device).uniform_(0,.025)
    keep=(torch.rand(len(x),52,1,device=x.device)>.04)
    return (x*gain*channel*sign+noise)*keep


def cross_person_contrastive(z,labels,people,temperature=.15):
    """Same fine label in another TRAINING person supplies positive pairs."""
    keep=labels>=0
    z=F.normalize(z[keep].float(),dim=1);y=labels[keep];p=people[keep]
    if len(z)<2:return z.sum()*0
    logits=z@z.T/temperature
    eye=torch.eye(len(z),device=z.device,dtype=torch.bool)
    positive=(y[:,None]==y[None,:])&(p[:,None]!=p[None,:])&~eye
    good=positive.any(1)
    if not good.any():return z.sum()*0
    logits=logits-logits.max(1,keepdim=True).values.detach()
    logprob=logits-torch.logsumexp(logits.masked_fill(eye,-torch.inf),1,keepdim=True)
    # masked_fill avoids 0 * inf on diagonal for very small synthetic batches.
    sums=logprob.masked_fill(~positive,0).sum(1)
    return -(sums[good]/positive.sum(1)[good]).mean()


def objective(st,fi,z,ys,yf,people,contrastive_weight=.08):
    loss=.6*F.cross_entropy(st.float(),ys,label_smoothing=.02)
    a=(ys==1)&(yf>=0);s=(ys==2)&(yf>=0)
    if a.any():loss=loss+F.cross_entropy(fi[a,:12],yf[a],label_smoothing=.03)
    if s.any():loss=loss+F.cross_entropy(fi[s,12:],yf[s]-12,label_smoothing=.03)
    return loss+contrastive_weight*cross_person_contrastive(z,yf,people)


def validation_score(predictions):
    table=C.segment_table(predictions);scores=[]
    # Fixed before this run: story sign identity receives the largest weight.
    for story,typ,names,weight in [(False,'activity',ACTIONS,.15),(False,'sign',SIGNS,.15),
                                   (True,'activity',ACTIONS,.2),(True,'sign',SIGNS,.35)]:
        g=table[table.type.eq(typ)&(table.part.eq('scripts')==story)]
        if len(g):scores.append((C.macro(g,names),weight))
    g=table[table.part.eq('scripts')]
    if len(g):scores.append((C.f1_score(g.type,g.pred_state,labels=['activity','sign'],average='macro',zero_division=0),.15))
    return float(sum(s*w for s,w in scores)/sum(w for s,w in scores))


def update_ema(ema,net,decay):
    with torch.no_grad():
        for a,b in zip(ema.parameters(),net.parameters()):a.lerp_(b,1-decay)
        for a,b in zip(ema.buffers(),net.buffers()):a.copy_(b)


def fit(tr,va,cfg,folder,fingerprint,deadline,epochs=None):
    C.require_kaggle_gpu();torch.set_num_threads(2);C.seed_all(cfg['seed'])
    torch.backends.cudnn.benchmark=True
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    progress('building GPU bank; training participants '+','.join(sorted({s['pid'] for s in tr})))
    bank,centers,targets,people,weights,scale=make_bank(tr)
    net=ShapeSpectrumCNN().cuda();ema=copy.deepcopy(net).eval()
    opt=torch.optim.AdamW(net.parameters(),lr=cfg['lr'],weight_decay=cfg['weight_decay'])
    scheduler=torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(opt,T_0=cfg['restart_epochs'],T_mult=2,eta_min=1e-5)
    scaler=torch.amp.GradScaler('cuda')
    steps=max(32,math.ceil(len(centers)/cfg['batch_size']))
    positions=torch.arange(200,device='cuda')-100
    start=time.time();fit_end=min(deadline,start+cfg['fit_seconds'])
    best=-math.inf;best_epoch=0;best_steps=0;epoch=0;updates=0;history=[];full_epochs=0
    last_validation=0.;last_checkpoint=0.;best_state=None
    print('[FIT]',folder,'participants',sorted({s['pid'] for s in tr}),
          'validation',sorted({s['pid'] for s in va}),'seconds',round(fit_end-start),
          'batches_per_epoch',steps,'target_epochs',epochs,flush=True)

    def payload():
        return dict(version=VERSION,arch=ARCH,classes=FINE,states=C.STATES,scale=scale,dataset=fingerprint,
                    epoch=epoch,updates=updates,steps_per_epoch=steps,config=cfg,
                    model={k:v.detach().cpu().clone() for k,v in ema.state_dict().items()},
                    train_model={k:v.detach().cpu().clone() for k,v in net.state_dict().items()},
                    optimizer=opt.state_dict(),scheduler=scheduler.state_dict(),scaler=scaler.state_dict(),
                    rng_python=C.random.getstate(),rng_numpy=np.random.get_state(),rng_torch=torch.get_rng_state(),
                    rng_cuda=torch.cuda.get_rng_state_all(),train_participants=sorted({s['pid'] for s in tr}),
                    validation_participants=sorted({s['pid'] for s in va}),history=history)

    while time.time()<fit_end and (epochs is None or epoch<epochs):
        ep_start=time.time();net.train();loss_sum=0.;count=0
        picks=torch.multinomial(weights,steps*cfg['batch_size'],replacement=True).reshape(steps,cfg['batch_size'])
        for step,ix in enumerate(picks):
            if step%8==0:
                progress(f'training epoch {epoch+1}, batch {step+1}/{steps}; updates {updates}')
                if time.time()>=fit_end:break
            x=bank[:,centers[ix,None]+positions].permute(1,0,2).contiguous()
            opt.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):
                st,fi,z=net(augment(x),with_embedding=True)
                loss=objective(st,fi,z,targets[ix,0],targets[ix,1],people[ix],cfg['contrastive_weight'])
            if not torch.isfinite(loss):raise RuntimeError('Nonfinite loss; last atomic checkpoint remains available.')
            scaler.scale(loss).backward();scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(net.parameters(),1.)
            old_scale=scaler.get_scale();scaler.step(opt);scaler.update()
            if scaler.get_scale()>=old_scale:
                update_ema(ema,net,cfg['ema_decay']);updates+=1
            scheduler.step(epoch+(step+1)/steps)
            loss_sum+=float(loss.detach());count+=1
        if not count:break
        epoch+=1;full_epochs+=int(count==steps);score=None
        need_val=bool(va) and (best_state is None or time.time()-last_validation>=cfg['validate_seconds'] or time.time()>=fit_end)
        if need_val:
            progress(f'validation at epoch {epoch}; test person remains excluded')
            score=validation_score(C.predict(ema,va,scale,ARCH,cfg['batch_size']))
            last_validation=time.time()
        improved=not va or (score is not None and score>best+1e-5)
        if improved:
            best=score if score is not None else 0.;best_epoch=epoch;best_steps=updates
            best_state={k:v.detach().cpu().clone() for k,v in ema.state_dict().items()}
            C.checkpoint_save(dict(version=VERSION,arch=ARCH,classes=FINE,states=C.STATES,scale=scale,
                dataset=fingerprint,epoch=epoch,updates=updates,model=best_state,validation_score=score,
                train_participants=sorted({s['pid'] for s in tr}),validation_participants=sorted({s['pid'] for s in va})),folder/'best.pt')
        history.append(dict(epoch=epoch,loss=loss_sum/count,validation_score=score,seconds=time.time()-ep_start,
                            updates=updates,steps=count,full_epoch=count==steps,
                            draws=count*cfg['batch_size'],lr=opt.param_groups[0]['lr']))
        if improved or time.time()-last_checkpoint>=cfg['checkpoint_seconds'] or time.time()>=fit_end or epoch==epochs:
            progress(f'saving checkpoint epoch {epoch}')
            C.checkpoint_save(payload(),folder/'last.pt');last_checkpoint=time.time()
            pd.DataFrame(history).to_csv(folder/'history.csv',index=False)
        print(f'[EPOCH] {folder.name} epoch={epoch} loss={loss_sum/count:.4f} val={score} updates={updates} elapsed={time.time()-start:.1f}s',flush=True)
    if best_state is None:raise RuntimeError('No model completed validation before the budget.')
    if updates==0:raise RuntimeError('No finite optimizer update completed; refusing to publish random weights.')
    C.checkpoint_save(payload(),folder/'last.pt');pd.DataFrame(history).to_csv(folder/'history.csv',index=False)
    info=dict(best_epoch=best_epoch,best_updates=best_steps,epochs_completed=epoch,updates=updates,
              steps_per_epoch=steps,training_seconds=time.time()-start,requested_epochs=epochs,
              full_epochs_completed=full_epochs,target_completed=epochs is None or full_epochs>=epochs,validation_score=best,
              train_participants=sorted({s['pid'] for s in tr}),validation_participants=sorted({s['pid'] for s in va}))
    C.atomic_json(info,folder/'fit_info.json')
    ema.load_state_dict(best_state)
    del bank,centers,targets,people,weights,net,opt,scheduler,scaler
    torch.cuda.empty_cache();gc.collect()
    return ema,scale,info


def packed_predictions(predictions,path):
    # Store frame predictions only. The common stream cache supplies true labels
    # for evaluation, rather than copying raw recordings into every artifact.
    C.save_predictions(predictions,path)


def restore_predictions(path,streams):
    found={s['file']:s for s in streams};result=[]
    with np.load(path,allow_pickle=False) as z:
        for i in range(len([k for k in z.files if k.endswith('_file')])):
            result.append(dict(stream=found[str(z[f'{i}_file'])],
                               **{key:z[f'{i}_{key}'] for key in ['centers','ps','pf','valid']}))
    return result


def inner_worker(streams,spec):
    test,val=spec['test'],spec['val']
    assert test!=val and test in PIDS and val in PIDS
    tr=[s for s in streams if s['pid'] not in [test,val]]
    va=[s for s in streams if s['pid']==val];te=[s for s in streams if s['pid']==test]
    assert len({s['pid'] for s in tr})==3
    cfg=dict(spec['cfg'],seed=spec['seed']);folder=Path(spec['folder'])
    # Reserve time for inference and final atomic writes before supervisor cap.
    net,scale,info=fit(tr,va,cfg,folder,spec['fingerprint'],spec['deadline']-75)
    progress('saving validation predictions')
    packed_predictions(C.predict(net,va,scale,ARCH,cfg['batch_size']),folder/'validation_frames.npz')
    progress('saving untouched outer test predictions')
    packed_predictions(C.predict(net,te,scale,ARCH,cfg['batch_size']),folder/'test_frames.npz')
    C.atomic_json(dict(test=test,validation=val,seed=cfg['seed'],arch=ARCH,dataset=spec['fingerprint'],
                       training_participants=sorted({s['pid'] for s in tr}),**info),folder/'complete.json')
    C.release(net);print('[MEMBER COMPLETE]',test,val,flush=True)


_ORIGINAL_COMMANDS=C.commands
def commands(p,tau):
    # Keep original smoothing, boundary handling and matching; reject ambiguous
    # predicted sign intervals without changing the coverage denominator.
    minimum=p.get('sign_confidence',0.)
    all_commands=_ORIGINAL_COMMANDS(p,tau)
    if minimum<=0:return all_commands
    selected=[]
    for command in all_commands:
        m=(p['centers']>=command['i0'])&(p['centers']<command['i1'])&p['valid']
        if not m.any():continue
        probabilities=p['pf'][m,12:].mean(0)
        probabilities=probabilities/max(float(probabilities.sum()),1e-12)
        if probabilities.max()>=minimum:selected.append(command)
    return selected
C.commands=commands


def choose_operating_point(validation_sets):
    rows=[]
    for tau in np.arange(.3,.901,.1):
        for confidence in [0.,.2,.35,.5]:
            individual=[]
            for predictions in validation_sets:
                for p in predictions:p['sign_confidence']=confidence
                r,_=C.event_metrics(predictions,float(tau))
                precision=r['identity_precision'];recall=r['identity_recall']
                r['identity_f0_5']=1.25*precision*recall/max(.25*precision+recall,1e-12)
                individual.append(r)
            rows.append(dict(tau=float(tau),confidence=confidence,
                **{key:float(np.mean([r[key] for r in individual])) for key in
                   ['identity_f0_5','identity_f1','detection_f1','false_commands_per_routine_hour']}))
    # Precision receives extra weight. Selection never examines test labels.
    best=max(rows,key=lambda r:(r['identity_f0_5'],r['identity_f1'],
                               -r['false_commands_per_routine_hour'],r['detection_f1'],r['tau'],r['confidence']))
    return best,rows


def score_outer(spec,streams):
    out=Path(spec['out']);test=spec['test'];fold=out/test
    members=[fold/'models'/('val_'+val) for val in PIDS if val!=test]
    assert all((m/'complete.json').exists() for m in members),f'{test}: missing inner member; no partial ensemble score is published.'
    for member in members:
        meta=json.loads((member/'complete.json').read_text());val=member.name.removeprefix('val_')
        assert meta['test']==test and meta['validation']==val
        expected=set(PIDS)-{test,val}
        assert set(meta['train_participants'])==expected and set(meta['validation_participants'])=={val}
        if 'fingerprint' in spec:assert meta['dataset']==spec['fingerprint']
    validation_sets=[restore_predictions(m/'validation_frames.npz',streams) for m in members]
    operating,grid=choose_operating_point(validation_sets)
    pd.DataFrame(grid).to_csv(fold/'validation_operating_points.csv',index=False)
    predictions=C.average_predictions([restore_predictions(m/'test_frames.npz',streams) for m in members])
    for p in predictions:p['sign_confidence']=operating['confidence']
    C.atomic_json(dict(test=test,operating_point=operating,members=[str(m.relative_to(out)) for m in members],
        selection='Four cross-fitted validation people; correct-identity F0.5 objective; no outer test labels.'),fold/'selection.json')
    C.save_predictions(predictions,fold/'frame_predictions.npz')
    C.report_fold(C.segment_table(predictions),predictions,operating['tau'],fold)
    C.atomic_json(dict(test=test,version=VERSION,members=4,training='Each member trains on 3 of the 4 other people.'),fold/'complete.json')
    print('[OUTER TEST COMPLETE]',test,flush=True)


def final_worker(streams,spec):
    cfg=dict(spec['cfg'],seed=spec['seed'],fit_seconds=spec['final_seconds'])
    net,scale,info=fit(streams,[],cfg,spec['folder'],spec['fingerprint'],spec['deadline']-25,epochs=spec['epochs'])
    C.atomic_json(info,Path(spec['folder'])/'complete.json');C.release(net)
    print('[FINAL SEED COMPLETE]',spec['seed'],info,flush=True)


def package_deployment(out,fingerprint,cfg):
    out=Path(out);final=out/'deployment_all5'
    checkpoints=[final/'models'/f'seed_{seed}'/'best.pt' for seed in cfg['final_seeds']]
    assert all(p.exists() and (p.parent/'complete.json').exists() for p in checkpoints),'All-five models are incomplete.'
    selections=[json.loads((out/pid/'selection.json').read_text()) for pid in PIDS]
    infos=[json.loads((p.parent/'fit_info.json').read_text()) for p in checkpoints]
    card=dict(version=VERSION,architecture=ARCH,classes=FINE,states=C.STATES,fs=C.FS,dataset=fingerprint,
        models=[str(p.relative_to(final)) for p in checkpoints],training_participants=PIDS,
        tau=float(np.median([s['operating_point']['tau'] for s in selections])),
        sign_confidence=float(np.median([s['operating_point']['confidence'] for s in selections])),
        final_fit_info=infos,selected_epoch_targets_completed=all(x['target_completed'] for x in infos),
        evaluation='Five outer test ensembles of four cross-fit models. Final two-seed all-five refit has no independent score.',
        label_protocol='Cue/key-press labels; video alignment unverified. No test-person calibration.',
        inference='Offline centered four-second windows; 50 Hz; CSI magnitude only; conditional action/sign heads.',
        threshold_note='Final median cross-fit operating points; calibration drift in final ensemble is unverified.')
    C.atomic_json(card,final/'model_card.json')
    for name in ['fyp_robust.py','fyp_common.py']:shutil.copy2(Path(__file__).parent/name,final/name)
    (final/'README.md').write_text('''# All-five CSI model

Install torch, numpy, pandas, scipy, scikit-learn and joblib. Keep this folder structure intact.
Inference: add this directory to sys.path, import fyp_robust, then call
`frames, commands = fyp_robust.predict_unlabelled_csv("new_csi.csv", model_folder, device="cuda")`.
Use `device="cpu"` for slower inference. The input must use the original 107-column CSI schema.
The final all-five model has no independent test score; see model_card.json and the outer held-out results.
''')
    import zipfile
    path=out.parent/'FYP_Improved_All5_Model.zip';tmp=path.with_suffix('.zip.part')
    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in final.rglob('*'):
            if p.is_file() and p.name not in ['last.pt','last.previous.pt','best.previous.pt','history.csv']:
                z.write(p,Path('FYP_Improved_All5_Model')/p.relative_to(final))
    os.replace(tmp,path);C.atomic_json(dict(sha256=C.sha256(path),bytes=path.stat().st_size),path.with_suffix('.zip.json'))
    return card


def load_deployment(folder,device='cuda'):
    folder=Path(folder);card=json.loads((folder/'model_card.json').read_text());models=[]
    assert card['classes']==FINE
    for relative in card['models']:
        ck=C.trusted_load(folder/relative)
        assert ck['classes']==FINE
        net=ShapeSpectrumCNN().to(device);net.load_state_dict(ck['model']);net.eval()
        models.append((net,ck['scale']))
    return models,card


def predict_unlabelled_csv(csv_path,model_folder,device='cuda'):
    models,card=load_deployment(model_folder,device)
    stream=C.raw_to_stream(csv_path);stream.update(file=Path(csv_path).name,pid='new',part='inference',events=[])
    p=C.average_predictions([C.predict(net,[stream],scale,ARCH,device=device) for net,scale in models])[0]
    p['sign_confidence']=card['sign_confidence'];rows=[]
    for center,st,fi,valid in zip(p['centers'],p['ps'],p['pf'],p['valid']):
        state=C.STATES[int(st.argmax())] if valid else 'unavailable'
        label='idle' if state=='idle' else (ACTIONS[fi[:12].argmax()] if state=='activity' else
                                          SIGNS[fi[12:].argmax()] if state=='sign' else 'unavailable')
        rows.append(dict(timestamp_us=int(stream['t'][center]),state=state,label=label))
    return pd.DataFrame(rows),pd.DataFrame(commands(p,card['tau']))


def worker(path):
    global PROGRESS
    spec=json.loads(Path(path).read_text());PROGRESS=spec['progress']
    C.require_kaggle_gpu();progress('loading preprocessed streams')
    streams=joblib.load(spec['streams'])
    if spec['job']=='inner':inner_worker(streams,spec)
    elif spec['job']=='final':final_worker(streams,spec)
    else:raise ValueError(spec['job'])


if __name__=='__main__':worker(sys.argv[2])
