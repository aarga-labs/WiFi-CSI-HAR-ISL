"""Supervise Kaggle training in a fresh process; no training on import.
Original model/data/selection code is retained for checkpoint compatibility.
Runtime recovery changes: one GPU, no loader subprocesses, one held-out fold/run,
and an external progress timeout. Exact prior stall cause is unknown.
"""
from pathlib import Path
import os, sys, json, time, signal, subprocess, shutil, hashlib, traceback

ORIGINAL_SHA='5182a7dd650182b1a87a2a297bb8fa941e2a62564c157a9978a90d6a7a0f4f21'


def worker(spec_path):
    import numpy as np
    import torch, joblib
    import fyp_pipeline as fyp
    spec=json.loads(Path(spec_path).read_text())
    fyp.require_kaggle_gpu()
    assert fyp.sha256(fyp.__file__)==ORIGINAL_SHA,'Unexpected original engine; do not mix versions.'
    torch.set_num_threads(2)
    if torch.cuda.is_available(): torch.cuda.set_device(0)
    streams=joblib.load(spec['streams'])  # only this notebook's locally generated cache
    cfg=spec['cfg']; out=Path(spec['out']); pid=spec['pid']; progress=Path(spec['progress'])
    current={'phase':'starting','job':pid}
    def tick(phase,job=None):
        current['phase']=phase
        if job is not None: current['job']=str(job)
        fyp.atomic_json(dict(time=time.time(),**current),progress)
        print('[RECOVERY]',current['job'],phase,flush=True)
    # Keep source/data/optimizer signatures unchanged. These execution settings
    # do not enter the original per-model training signature.
    base_train=fyp.train
    def safe_train(tr,va,arch,cfg,folder,fingerprint,seed,epochs=None):
        tick('training started',Path(folder).relative_to(out))
        actual=dict(cfg,workers=0,multi_gpu=False)
        result=base_train(tr,va,arch,actual,folder,fingerprint,seed,epochs)
        tick('training finished',Path(folder).relative_to(out))
        return result
    fyp.train=safe_train
    base_save=fyp.checkpoint_save
    def progress_save(payload,path):
        base_save(payload,path)
        if Path(path).name=='last.pt':
            tick('saved epoch '+str(payload['epoch']),Path(path).parent.relative_to(out))
    fyp.checkpoint_save=progress_save
    base_predict=fyp.predict
    def progress_predict(*args,**kwargs):
        tick('prediction started')
        result=base_predict(*args,**kwargs)
        tick('prediction finished')
        return result
    fyp.predict=progress_predict
    base_load=fyp.trusted_load
    def compatible_load(path):
        ck=base_load(path)
        # Original run recorded RNG states for two GPUs; this process exposes one.
        if isinstance(ck,dict) and 'rng_cuda' in ck:
            ck=dict(ck); states=ck['rng_cuda']
            ck['rng_cuda']=states[:torch.cuda.device_count()]
        return ck
    fyp.trusted_load=compatible_load
    tick('starting fold',pid)
    fyp.SESSION_DEADLINE=spec['deadline']
    fyp.atomic_json(dict(single_gpu=True,workers=0,original_source_sha256=ORIGINAL_SHA,
        note='Execution settings changed for stall diagnosis; exact numerical replay is not promised.'),out/('recovery_runtime_'+pid+'.json'))
    try:
        if spec.get('mode')=='smoke':
            tr=[s for s in streams if s['pid'] in ['P01','P02','P03']]
            va=[s for s in streams if s['pid']=='P04']
            c=dict(cfg,epochs=2,min_epochs=1,patience=2,steps_per_epoch=2)
            model,*_=fyp.train(tr,va,fyp.CANDIDATES[0],c,out/'smoke',spec['fingerprint'],17)
            fyp.release(model)
            tick('smoke completed')
        elif spec.get('mode')=='final':
            fyp.final_train(streams,cfg,out,spec['fingerprint'])
            tick('all-five deployment refit completed')
        else:
            fyp.run_fold(streams,pid,cfg,out,spec['fingerprint'])
            tick('fold completed',pid)
    except fyp.SessionBudgetReached as exc:
        tick('session budget reached',pid); print(exc,flush=True)
        return 75
    except BaseException:
        traceback.print_exc(); tick('worker failed',pid)
        return 1
    return 0


def _stop_process(proc):
    if proc.poll() is not None:return
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)


def supervise(spec_path,stall_seconds=900,poll_seconds=5,hard_grace_seconds=120):
    """Parent has no CUDA workload; can stop a worker even if CUDA blocks."""
    spec_path=Path(spec_path); spec=json.loads(spec_path.read_text())
    log=spec_path.with_suffix('.log'); progress=Path(spec['progress'])
    if progress.exists():progress.unlink()  # run-local heartbeat only, never a model
    env=dict(os.environ,PYTHONUNBUFFERED='1',CUDA_VISIBLE_DEVICES=str(spec.get('gpu',0)),
             OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    began=time.time(); position=0; status=None; last_notice=began
    with open(log,'w') as output:
        proc=subprocess.Popen([sys.executable,'-u',str(Path(__file__).resolve()),'--worker',str(spec_path)],
            stdout=output,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        try:
            while True:
                with open(log) as inp:
                    inp.seek(position); content=inp.read();position=inp.tell()
                if content:print(content,end='',flush=True)
                rc=proc.poll()
                if rc is not None:
                    status={'exit_code':rc,'reason':'finished' if rc==0 else 'worker paused or failed'};break
                now=time.time(); last=began; phase='loading worker'
                if progress.exists():
                    try:
                        data=json.loads(progress.read_text());last=data['time'];phase=data['phase']
                    except (OSError,ValueError,KeyError):pass
                if now-last>stall_seconds:
                    _stop_process(proc)
                    status={'exit_code':124,'reason':'no completed phase/checkpoint for '+str(stall_seconds)+' seconds','last_phase':phase};break
                if now>spec['deadline']+hard_grace_seconds:
                    _stop_process(proc)
                    status={'exit_code':124,'reason':'session deadline exceeded during a blocked phase','last_phase':phase};break
                if now-last_notice>=60:
                    print(f'[SUPERVISOR] {spec["pid"]}: {phase}; {int(now-last)}s since progress',flush=True)
                    last_notice=now
                time.sleep(poll_seconds)
        finally:
            _stop_process(proc)
    with open(log) as inp:
        inp.seek(position);rest=inp.read()
    if rest:print(rest,end='',flush=True)
    status.update(log=str(log),elapsed_seconds=round(time.time()-began,1))
    spec_path.with_suffix('.status.json').write_text(json.dumps(status,indent=2))
    return status


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':sys.exit(worker(sys.argv[2]))
    raise SystemExit('Import this module from the recovery notebook.')
