"""Correct-count and threshold comparison from saved predictions. No fitting."""
from pathlib import Path
import hashlib
import json
import sys

import joblib
import numpy as np
import pandas as pd

BASE=Path('/home/adhikkesh/adhikkesh/FYP')
FRIEND=BASE/'Model_Detect-Activity-and-Gestures'
RUN=BASE/'Kaggle_P1_P5/balanced_results_audit_20261017/run/FYP_BALANCED_2H_20261017_015419'
HERE=Path(__file__).parent
OUT=Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/For_Mam_Comparison')
OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(FRIEND))
import stream_eval as E
sys.path.insert(0,str(BASE/'Kaggle_P1_P5/balanced_2h'))
import fyp_fast as C

friend=pd.read_csv(FRIEND/'results_final_segments_cal0.csv')
ours_all=pd.read_csv(RUN/'results/all_out_of_fold_predictions.csv')
ours=ours_all[ours_all.pid.isin(['P01','P02','P03'])].sort_values(['file','t_start_us']).copy()
ours['rep']=ours.groupby(['file','label']).cumcount()+1
keys=['pid','part','file','label','type','rep']
matched=friend.merge(ours,on=keys,suffixes=('_friend','_ours'),validate='one_to_one')
assert len(matched)==684
rows=[]
for typ in ['activity','sign']:
    d=matched[matched.type.eq(typ)&matched.part.ne('scripts')]
    pred='act_pred_fused' if typ=='activity' else 'within_type_pred'
    for label,g in d.groupby('label'):
        wrong=g[g.pred.ne(label)].pred.value_counts()
        mistakes=sorted(wrong.items(),key=lambda x:(-x[1],x[0]))[:2]
        rows.append(dict(type=typ,label=label,n=len(g),friend_correct=int(g.label.eq(g[pred]).sum()),
                         ours_correct=int(g.label.eq(g.pred).sum()),friend_recall=float(g.label.eq(g[pred]).mean()),
                         ours_recall=float(g.label.eq(g.pred).mean()),
                         ours_common_confusions=', '.join(f'{name} ({count})' for name,count in mistakes) or '—'))
counts=pd.DataFrame(rows)
counts.to_csv(OUT/'correctly_named_by_class.csv',index=False)
assert counts[counts.type.eq('activity')].friend_correct.sum()==131
assert counts[counts.type.eq('activity')].ours_correct.sum()==144
assert counts[counts.type.eq('sign')].friend_correct.sum()==49
assert counts[counts.type.eq('sign')].ours_correct.sum()==77

# Use the friend's exact detect/runs/stream_metrics implementations, imported
# read-only. Map the saved 26-class output order; their original order had 24.
E.ACTIONS=C.ACTIONS;E.SIGNS=C.SIGNS;E.FINE=C.FINE
E.A_IDX=list(range(12));E.S_IDX=list(range(12,26))
streams=joblib.load(RUN/'cache/prepared_streams.joblib')
byfile={s['file']:s for s in streams}
D=[]
for pid in ['P01','P02','P03']:
    with np.load(RUN/'results'/pid/'frame_predictions.npz',allow_pickle=False) as z:
        for i in range(len([k for k in z.files if k.endswith('_file')])):
            s=byfile[str(z[f'{i}_file'])];centers=z[f'{i}_centers'];valid=z[f'{i}_valid']
            coverage=np.zeros(len(s['state']),bool)
            for center,ok in zip(centers,valid):
                if ok:coverage[max(0,center-5):min(len(coverage),center+5)]=True
            state=s['state'].copy();state[~coverage]=-1
            # Invalid frames are unscored, not imputed sign probabilities.
            # Retain all fully covered sign labels, including missed ones.
            D.append(dict(pid=pid,part=s['part'],file=s['file'],centre=centers,
                          ps=np.nan_to_num(z[f'{i}_ps']),pf=np.nan_to_num(z[f'{i}_pf']),
                          state=state,events=pd.DataFrame(s['events'])))

oldstream=pd.read_csv(FRIEND/'results_final_stream_cal0.csv')
thresholds=[];details=[];source_rows=[]
for tau in [.3,.5,.7]:
    individual=[]
    for pid in ['P01','P02','P03']:
        metric,_=E.stream_metrics([d for d in D if d['pid']==pid],tau)
        individual.append(metric);details.append(dict(pid=pid,**metric))
    f=oldstream[np.isclose(oldstream.tau,tau)]
    assert len(f)==3 and all(r['n_sign']==106 for r in individual)
    thresholds.append(dict(tau=tau,friend_detection_recall=float(f.sign_recall.mean()),
        ours_detection_recall=float(np.mean([r['sign_recall'] for r in individual])),
        friend_false_per_routine_hour=float(f['FC/h_routine'].mean()),
        ours_false_per_routine_hour=float(np.mean([r['FC/h_routine'] for r in individual])),
        friend_n_sign=int(f.n_sign.sum()),ours_n_sign=sum(r['n_sign'] for r in individual),
        friend_routine_hours=float(f.routine_h.sum()),ours_routine_hours=sum(r['routine_h'] for r in individual)))
    for source in ['isolated','story']:
        subset=[d for d in D if (d['part']=='scripts')==(source=='story')]
        metric,_=E.stream_metrics(subset,tau);source_rows.append(dict(source=source,**metric))
pd.DataFrame(thresholds).to_csv(OUT/'threshold_comparison_same_detection_rules.csv',index=False)
pd.DataFrame(details).to_csv(OUT/'our_threshold_details_by_person.csv',index=False)
pd.DataFrame(source_rows).to_csv(OUT/'our_threshold_details_by_source.csv',index=False)

manifest=dict(our_run=RUN.name,our_new_improved_notebook_results_available=False,
    matched_events=len(matched),participants=['P01','P02','P03'],
    classification='Known type and event boundaries. Per-class recall and pooled accuracy, not macro F1.',
    threshold='Friend final zero-shot exported means; ours recomputed using identical friend detect/match functions. Both average three participants.',
    detection_rules='50 Hz, 0.2 s frame hop, centered 1 s smoothing, 1 s minimum run, merge gaps <=1 s, match tolerance +/-1 s; no identity requirement for detection.',
    scope='Thresholds combine isolated and story sources: 318 true signs. Routine-hour rates exclude idle and unknown; not all wrong reactions.',
    coverage_difference='Our quality-masked/unavailable frames remain unavailable; routine time differs slightly (0.96544 h vs 0.96816 h).',
    screenshot_note='Action/sign screenshots reproduce friend final zero-shot predictions before excluding one partial P02 lightswitch. Threshold screenshot does not match final CSV; its run/scope are unverified.',
    inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [FRIEND/'results_final_segments_cal0.csv',FRIEND/'results_final_stream_cal0.csv',FRIEND/'stream_eval.py',RUN/'results/all_out_of_fold_predictions.csv']})
(OUT/'comparison_method.json').write_text(json.dumps(manifest,indent=2))

names=dict(walk='walk',sitstand='sit–stand',fall='fall',pickup='pick up',eat='eat',drink='drink',
           answerphone='answer phone',wipetable='wipe table',lightswitch='light switch',tvremote='TV remote')
order_actions=['walk','sitstand','fall','pickup','eat','drink','answerphone','wipetable','lightswitch','tvremote']
order_signs=['LAMP','HUNGRY','HELP','COOK','HOT','PAIN','FAN','WATER','ACCIDENT','TOILET','CALL','HELLO','THANKYOU','TELEVISION']
text='''# Correctly named actions and signs

Compared on identical original P1–P3 isolated events, using our completed balanced run. The newer improved notebook has no verified results here. Each person was excluded from their model’s training. Our model learned from four other people; the friend’s model learned from two. These are per-class correct-count percentages (recall), not F1. Event boundaries and action/sign type are supplied.

'''
for typ,order in [('activity',order_actions),('sign',order_signs)]:
    text+=f'## {"Actions" if typ=="activity" else "Signs"}\n\n| Class | Friend | Ours | Our common mistakes |\n|---|---:|---:|---|\n'
    for label in order:
        r=counts[counts.label.eq(label)].iloc[0]
        text+=f'| {names.get(label,label)} | {r.friend_correct}/{r.n} ({100*r.friend_recall:.1f}%) | {r.ours_correct}/{r.n} ({100*r.ours_recall:.1f}%) | {r.ours_common_confusions} |\n'
    g=counts[counts.type.eq(typ)];n=g.n.sum()
    text+=f'| **Overall** | **{g.friend_correct.sum()}/{n} ({100*g.friend_correct.sum()/n:.1f}%)** | **{g.ours_correct.sum()}/{n} ({100*g.ours_correct.sum()/n:.1f}%)** | |\n\n'
text+='''One partial P02 light-switch interval is excluded from both columns. The screenshot includes it: 7/29 and 132/259 actions overall. Matched values are 6/28 and 131/258. Common mistakes list up to two most frequent wrong labels; ties may have other equally frequent labels.

## Signs caught and wrong reactions at fixed thresholds

The screenshot’s approximate 9/10, 8/10 and 6–7/10 values cannot be verified against the saved final CSV. Use the verified final table below instead. Our saved probabilities were re-evaluated with the friend’s own detector and matching code. Both include isolated recordings and stories (318 true signs); values average the three people equally. Quality masks/coverage still differ slightly. This is a retrospective threshold sweep, not a newly selected deployment threshold.

| Threshold | Friend: signs caught | Ours: signs caught | Friend: false reactions / routine hour | Ours: false reactions / routine hour |
|---|---:|---:|---:|---:|
'''
for r in thresholds:
    text+=f'| {r["tau"]:.1f} | {100*r["friend_detection_recall"]:.1f}% | {100*r["ours_detection_recall"]:.1f}% | {r["friend_false_per_routine_hour"]:.1f} | {r["ours_false_per_routine_hour"]:.1f} |\n'
text+='''
“Caught” means detected as a sign; it does not mean the correct sign was named. A threshold is a model-score cutoff, not verified percentage certainty. The hourly rate counts unmatched detections during labelled routine movement, excludes idle/unknown periods and incorrect names during actual signs, and is extrapolated from about 58 measured routine minutes. It is not a count of every wrong home reaction.

## What to say

On the same original participant recordings, correctly named actions improved from about 51% to 56%, and correctly named signs improved from 23% to 37%. The strongest gains are wiping the table, pickup, sit–stand, COOK and HELLO. THANKYOU and several small movements remain weak. At the same detector thresholds, the updated model catches slightly more signs but also produces more false triggers. Continuous use still needs improvement.

The complete P1–P5 isolated dataset, including new seated/cooking examples, has 311/628 correctly named actions (49.5%) and 171/490 correctly named signs (34.9%). Those are a different, broader test set than the matched comparison above.

All calculations use saved predictions. No model was fitted.
'''
(OUT/'Comparison_For_Mam.md').write_text(text)
print(counts.to_string(index=False));print(pd.DataFrame(thresholds).to_string(index=False));print(OUT)
