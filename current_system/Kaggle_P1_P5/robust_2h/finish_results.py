"""Reporting, common evaluation, packaging. No fitting."""
from pathlib import Path
import hashlib
import json
import os
import sys
import time

os.environ['MPLBACKEND']='Agg'
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
import fyp_robust as R


def report(spec):
    C=R.C;out=Path(spec['out']);streams=joblib.load(spec['streams'])
    progress=spec['progress']
    def beat(phase):C.atomic_json(dict(time=time.time(),phase=phase),progress)
    completed=[];errors=[]
    for test in C.PIDS:
        beat('assembling untouched outer test '+test)
        try:
            if not (out/test/'complete.json').exists():R.score_outer(dict(spec,test=test),streams)
            completed.append(test)
        except AssertionError as exc:errors.append(str(exc));print('[INCOMPLETE]',exc,flush=True)
    if completed:
        beat('class-wise results and confusion matrices')
        C.summarize(out)
        reference=json.loads((Path(__file__).parent/'baseline_reference.json').read_text())
        data=pd.read_csv(out/'all_out_of_fold_predictions.csv')
        ids_hash=hashlib.sha256('\n'.join(sorted(data.id)).encode()).hexdigest()
        info=json.loads((out/'dataset_info.json').read_text())
        matched=len(completed)==5 and ids_hash==reference['event_ids_sha256'] and info['dataset']==reference['dataset']
        if matched:
            old=pd.DataFrame(reference['summary'])
            new=pd.read_csv(out/'summary.csv')
            comparison=old.merge(new,on=['split','type'],suffixes=('_baseline','_new'),validate='one_to_one')
            comparison['change_pp']=100*(comparison.mean_f1_new-comparison.mean_f1_baseline)
            comparison.to_csv(out/'comparison_with_balanced.csv',index=False)
            print('[SAME-EVENT COMPARISON]\n',comparison[['split','type','mean_f1_baseline','mean_f1_new','change_pp']].to_string(index=False),flush=True)
            fig,ax=plt.subplots(figsize=(11,5))
            g=comparison[comparison.split.isin(['isolated','stories_oracle_boundaries'])]
            x=np.arange(len(g));ax.bar(x-.19,g.mean_f1_baseline,.38,label='Previous balanced')
            ax.bar(x+.19,g.mean_f1_new,.38,label='New cross-fit ensemble')
            ax.set_xticks(x,[f'{a.replace("stories_oracle_boundaries","Story, known bounds")}\n{b}' for a,b in zip(g.split,g.type)])
            ax.set_ylim(0,1);ax.set_ylabel('Mean held-out macro F1');ax.set_title('Same dataset and test event IDs; training protocols differ')
            ax.legend();fig.tight_layout();fig.savefig(out/'figures/previous_vs_new.png',dpi=170);plt.close(fig)
        else:
            errors.append('Automatic baseline comparison withheld: dataset/event IDs or evaluation coverage differ.')
        # Learning curves show validation, rather than only training loss.
        fig,axes=plt.subplots(1,2,figsize=(13,5))
        for pid in completed:
            for p in (out/pid/'models').glob('val_*/history.csv'):
                d=pd.read_csv(p);label=pid+'/'+p.parent.name
                axes[0].plot(d.epoch,d.loss,alpha=.6,label=label)
                valid=d.validation_score.notna();axes[1].plot(d.loc[valid,'epoch'],d.loc[valid,'validation_score'],alpha=.7,label=label)
        axes[0].set_title('Optimization loss');axes[1].set_title('Validation selection score — no test data')
        for ax in axes:ax.set_xlabel('Epoch')
        axes[1].legend(ncol=2,fontsize=6);fig.tight_layout();fig.savefig(out/'figures/crossfit_learning_curves.png',dpi=170);plt.close(fig)
    status=dict(completed_test_participants=completed,evaluation_complete=len(completed)==5,
                all_five_model_ready=(out/'deployment_all5/model_card.json').exists(),errors=errors,
                elapsed_minutes=(time.time()-spec['started'])/60,
                evaluation='Updated benchmark informed by previous tests; not a fresh independent study.')
    if status['all_five_model_ready']:
        card=json.loads((out/'deployment_all5/model_card.json').read_text())
        status['final_selected_epoch_targets_completed']=card['selected_epoch_targets_completed']
    C.atomic_json(status,out/'run_completion.json')
    beat('exporting checkpoint archive')
    archive=C.archive_outputs(out)
    beat('report and archive complete')
    print('[FINISHED]',json.dumps(status,indent=2),flush=True)
    print('[ARCHIVE]',archive,flush=True)


if __name__=='__main__':report(json.loads(Path(sys.argv[2]).read_text()))
