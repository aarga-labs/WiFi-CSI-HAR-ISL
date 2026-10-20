"""End-to-end result assembly with synthetic predictions and random weights.

No fit function is called. No optimizer is constructed or updated.
"""
from pathlib import Path
import json
import tempfile
import time
import zipfile
import joblib
import numpy as np
import pandas as pd
import torch
import fyp_robust as R
import finish_results

torch.set_num_threads(2)
C=R.C
streams=[]
for pid in R.PIDS:
    for part in ['actions','signs_standing','scripts']:
        typelist=['activity','sign'] if part=='scripts' else ['activity' if part=='actions' else 'sign']
        events=[];state=np.full(800,-1,dtype=np.int64)
        for i,typ in enumerate(typelist):
            a=100+i*200;b=a+200;state[a:b]=C.STATES.index(typ)
            label='walk' if typ=='activity' else 'HELLO'
            events.append(dict(id=f'{pid}_{part}:{i}',pid=pid,part=part,file=f'{pid}_{part}.csv',
                               label=label,type=typ,posture='standing',i0=a,i1=b,
                               intent='I0',home_action='none',covered=True))
        streams.append(dict(pid=pid,part=part,file=f'{pid}_{part}.csv',state=state,events=events))

def predictions(pid):
    result=[]
    for stream in streams:
        if stream['pid']!=pid:continue
        centers=[];states=[];fine=[]
        for e in stream['events']:
            for center in range(e['i0']+50,e['i1'],100):
                st=np.zeros(3,np.float32);st[C.STATES.index(e['type'])]=1
                fi=np.zeros(26,np.float32);fi[0]=.5;fi[12]=.5
                centers.append(center);states.append(st);fine.append(fi)
        result.append(dict(stream=stream,centers=np.array(centers),ps=np.array(states),pf=np.array(fine),valid=np.ones(len(centers),bool)))
    return result

with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp);out=work/'results';out.mkdir();progress=work/'progress.json'
    joblib.dump(streams,work/'streams.joblib')
    (out/'dataset_info.json').write_text(json.dumps(dict(dataset='synthetic-fixture')))
    for test in R.PIDS:
        for val in R.PIDS:
            if test==val:continue
            folder=out/test/'models'/('val_'+val);folder.mkdir(parents=True)
            R.packed_predictions(predictions(val),folder/'validation_frames.npz')
            R.packed_predictions(predictions(test),folder/'test_frames.npz')
            C.atomic_json(dict(test=test,validation=val,train_participants=sorted(set(R.PIDS)-{test,val}),
                               validation_participants=[val],dataset='synthetic-fixture'),folder/'complete.json')
            pd.DataFrame([dict(epoch=1,loss=1.,validation_score=.4)]).to_csv(folder/'history.csv',index=False)
        R.score_outer(dict(out=str(out),test=test),streams)
        assert (out/test/'complete.json').exists()
        selection=json.loads((out/test/'selection.json').read_text())
        assert len(selection['members'])==4
        assert pd.read_csv(out/test/'metrics.csv').macro_f1.eq(1).all()
    # Package two randomly initialized fixture networks; verify structure and
    # provenance. This validates packaging, not accuracy or model fitting.
    model=R.ShapeSpectrumCNN().eval()
    for seed in R.CFG['final_seeds']:
        folder=out/'deployment_all5/models'/f'seed_{seed}';folder.mkdir(parents=True)
        C.checkpoint_save(dict(classes=R.FINE,scale=np.ones(52,dtype=np.float32),model=model.state_dict()),folder/'best.pt')
        info=dict(target_completed=True,train_participants=R.PIDS,requested_epochs=2)
        C.atomic_json(info,folder/'fit_info.json');C.atomic_json(info,folder/'complete.json')
    card=R.package_deployment(out,'synthetic-fixture',R.CFG)
    loaded,_=R.load_deployment(out/'deployment_all5','cpu')
    assert len(loaded)==2 and card['selected_epoch_targets_completed']
    package=work/'FYP_Improved_All5_Model.zip'
    with zipfile.ZipFile(package) as z:
        assert z.testzip() is None and len([n for n in z.namelist() if n.endswith('best.pt')])==2
        assert not any('last.pt' in n for n in z.namelist())
    finish_results.report(dict(out=str(out),streams=str(work/'streams.joblib'),progress=str(progress),started=time.time()))
    status=json.loads((out/'run_completion.json').read_text())
    assert status['evaluation_complete'] and status['all_five_model_ready']
    assert status['final_selected_epoch_targets_completed']
    assert not (out/'comparison_with_balanced.csv').exists(),'A different dataset must not get a baseline comparison.'
    assert len(pd.read_csv(out/'all_out_of_fold_predictions.csv'))==20
    assert len(list((out/'figures').glob('*.png')))>=10
    with zipfile.ZipFile(work/'FYP_all_checkpoints_and_results.zip') as z:assert z.testzip() is None
    print('PASS: five complete four-member ensembles, saved metrics, conditional identity, model ZIP reload, report figures, CRC checks and refusal of mismatched baseline comparison. Zero fits.')
