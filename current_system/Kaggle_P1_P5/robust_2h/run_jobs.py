"""Process supervision for bounded Kaggle runs. This module never trains on import."""
from pathlib import Path
import os,sys,json,time,signal,subprocess,collections


def stop(proc):
    if proc.poll() is not None:return
    os.killpg(proc.pid,signal.SIGTERM)
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=5)


def launch(spec,script):
    path=Path(spec['spec_path']);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(spec,indent=2));log=path.with_suffix('.log')
    env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(spec['gpu']),PYTHONUNBUFFERED='1',
             OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
    file=open(log,'w')
    proc=subprocess.Popen([sys.executable,'-u',str(script),'--worker',str(path)],stdout=file,
        stderr=subprocess.STDOUT,env=env,start_new_session=True)
    return dict(spec=spec,proc=proc,file=file,log=log,pos=0,started=time.time(),notice=time.time())


def drain(job):
    with open(job['log']) as f:
        f.seek(job['pos']);s=f.read();job['pos']=f.tell()
    if s:
        for line in s.splitlines():print(f'[{job["spec"]["pid"]}] {line}',flush=True)


def run_jobs(specs,script,max_parallel=2,stall_seconds=300,poll_seconds=2):
    pending=collections.deque(specs);active=[];results=[];free=list(range(max_parallel))
    try:
        while pending or active:
            while pending and free:
                spec=dict(pending.popleft())
                if time.time()>=spec['deadline']:
                    results.append(dict(pid=spec['pid'],status='not_started_time_budget'));continue
                gpu=free.pop(0);spec['gpu']=gpu
                if spec.get('max_job_seconds'):
                    spec['deadline']=min(spec['deadline'],time.time()+spec['max_job_seconds'])
                print('[START]',spec['pid'],'GPU',gpu,flush=True)
                active.append(launch(spec,script))
            for job in list(active):
                drain(job);spec=job['spec'];now=time.time();rc=job['proc'].poll();reason=None
                last=job['started'];phase='worker startup'
                progress=Path(spec['progress'])
                if progress.exists():
                    try:
                        data=json.loads(progress.read_text());last=data['time'];phase=data['phase']
                    except (OSError,ValueError,KeyError):pass
                if rc is None and now>=spec['deadline']:
                    reason='time_budget_reached';stop(job['proc']);rc=job['proc'].returncode
                elif rc is None and now-last>=stall_seconds:
                    reason='stalled_no_progress';stop(job['proc']);rc=job['proc'].returncode
                if rc is not None:
                    drain(job);job['file'].close();active.remove(job);free.append(spec['gpu']);free.sort()
                    result=dict(pid=spec['pid'],status=reason or ('complete' if rc==0 else 'failed_or_paused'),
                        exit_code=rc,seconds=round(now-job['started'],1),last_phase=phase,log=str(job['log']))
                    results.append(result)
                    Path(spec['spec_path']).with_suffix('.status.json').write_text(json.dumps(result,indent=2))
                    print('[END]',result,flush=True)
                elif now-job['notice']>=60:
                    print('[STATUS]',spec['pid'],phase,'seconds since progress:',int(now-last),flush=True)
                    job['notice']=now
            if pending or active:time.sleep(poll_seconds)
    finally:
        for job in active:
            stop(job['proc']);drain(job);job['file'].close()
    return results
