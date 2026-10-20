"""Compare saved out-of-fold predictions. No model training or fitting."""
from pathlib import Path
import hashlib
import json
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

ROOT = Path('/home/adhikkesh/adhikkesh/FYP')
FRIEND = ROOT / 'Model_Detect-Activity-and-Gestures'
OURS = ROOT / 'Kaggle_P1_P5/balanced_results_audit_20261017/run/FYP_BALANCED_2H_20261017_015419/results'
OUT = Path(__file__).resolve().parent
DOWNLOAD = Path('/home/adhikkesh/Downloads/FYP_Kaggle_P1_P5/Friend_vs_Our_Results')
DOWNLOAD.mkdir(parents=True, exist_ok=True)

friend = pd.read_csv(FRIEND / 'results_final_segments_cal0.csv')
ours_all = pd.read_csv(OURS / 'all_out_of_fold_predictions.csv')
ours = ours_all[ours_all.pid.isin(friend.pid.unique())].sort_values(['file', 't_start_us']).copy()
# Friend's dense.py numbers repetitions within each label, in recording order.
ours['rep'] = ours.groupby(['file', 'label']).cumcount() + 1
keys = ['pid', 'part', 'file', 'label', 'type', 'rep']
joined = friend.merge(ours, on=keys, suffixes=('_friend', '_ours'),
                      how='outer', indicator=True, validate='one_to_one')
unmatched = joined[joined._merge.ne('both')][keys + ['_merge']]
unmatched.to_csv(OUT / 'unmatched_events.csv', index=False)
assert len(joined[joined._merge.eq('both')]) == 684
assert len(unmatched) == 1 and unmatched.iloc[0].pid == 'P02'
assert unmatched.iloc[0].label == 'lightswitch'
matched = joined[joined._merge.eq('both')].copy()
matched.to_csv(OUT / 'matched_predictions.csv', index=False)
labels = {typ: sorted(friend.loc[(friend.type.eq(typ)) & friend.part.ne('scripts'), 'label'].unique())
          for typ in ('activity', 'sign')}

def friend_pred(part, typ):
    return 'act_pred_fused' if part != 'scripts' and typ == 'activity' else 'within_type_pred'

rows = []
for (pid, part, typ), g in matched.groupby(['pid', 'part', 'type']):
    p = friend_pred(part, typ)
    a = f1_score(g.label, g[p], labels=labels[typ], average='macro', zero_division=0)
    b = f1_score(g.label, g.pred, labels=labels[typ], average='macro', zero_division=0)
    rows.append(dict(pid=pid, part=part, type=typ, events=len(g), friend_f1=a,
                     our_f1=b, change_pp=100*(b-a)))
per_pid = pd.DataFrame(rows)
per_pid.to_csv(OUT / 'participant_comparison.csv', index=False)
means = per_pid.groupby(['part', 'type'])[['friend_f1', 'our_f1', 'change_pp']].mean().reset_index()
means.to_csv(OUT / 'matched_macro_f1.csv', index=False)

aucs = []
for pid, g in matched[matched.part.eq('scripts')].groupby('pid'):
    aucs.append(dict(pid=pid, friend_auc=roc_auc_score(g.type.eq('sign'), g.p_sign_friend),
                     our_auc=roc_auc_score(g.type.eq('sign'), g.p_sign_ours)))
auc = pd.DataFrame(aucs)
auc.to_csv(OUT / 'story_auc_comparison.csv', index=False)

classes = []
for typ, part in [('activity', 'actions'), ('sign', 'signs_standing')]:
    g = matched[matched.part.eq(part)]
    a = f1_score(g.label, g[friend_pred(part, typ)], labels=labels[typ], average=None, zero_division=0)
    b = f1_score(g.label, g.pred, labels=labels[typ], average=None, zero_division=0)
    for name, x, y in zip(labels[typ], a, b):
        classes.append(dict(type=typ, label=name, events=int(g.label.eq(name).sum()),
                            friend_f1=x, our_f1=y, change_pp=100*(y-x)))
classes = pd.DataFrame(classes)
classes.to_csv(OUT / 'matched_class_comparison.csv', index=False)

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(1, 2, figsize=(13, 5.6))
plot_rows = [('actions', 'activity', 'Isolated actions'), ('signs_standing', 'sign', 'Isolated signs'),
             ('scripts', 'activity', 'Story actions*'), ('scripts', 'sign', 'Story signs*')]
x = np.arange(4)
a, b = [], []
for part, typ, _ in plot_rows:
    r = means[(means.part == part) & (means.type == typ)].iloc[0]
    a.append(100*r.friend_f1); b.append(100*r.our_f1)
ax = axes[0]
bars1=ax.bar(x-.19, a, .38, label="Friend: P1–P3 training pool", color='#8a9dad')
bars2=ax.bar(x+.19, b, .38, label='Ours: P1–P5 training pool', color='#087f8c')
ax.bar_label(bars1, fmt='%.1f', padding=3, fontsize=9)
ax.bar_label(bars2, fmt='%.1f', padding=3, fontsize=9)
ax.set_xticks(x, [r[2].replace(' ', '\n', 1) for r in plot_rows]);ax.set_ylim(0, 100)
ax.set_ylabel('Mean held-out participant macro F1 (%)')
ax.set_title('Same P1–P3 test events and class lists')
ax.legend(loc='upper left', fontsize=8)
ax=axes[1]
isolated=per_pid[per_pid.part.isin(['actions','signs_standing'])]
for typ, marker, color in [('activity','o','#a35b00'), ('sign','s','#087f8c')]:
    g=isolated[isolated.type.eq(typ)].sort_values('pid')
    ax.plot(g.pid,100*g.friend_f1,ls='--',marker=marker,color=color,label=f'Friend {typ}')
    ax.plot(g.pid,100*g.our_f1,ls='-',marker=marker,color=color,label=f'Our {typ}')
ax.set_ylim(0,100);ax.set_ylabel('Isolated macro F1 (%)');ax.set_title('Gains on each original participant')
ax.legend(fontsize=9)
fig.suptitle('Friend’s final zero-shot system vs balanced Kaggle run',fontweight='bold')
fig.text(.02,.02,'*Story identity uses true event boundaries and type. Training data and methods differ; this is not a controlled architecture test.',fontsize=9)
fig.tight_layout(rect=[0,.065,1,.93]);fig.savefig(OUT/'friend_vs_ours.png',dpi=180);plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(13,7.7))
for ax,typ,title in zip(axes,['activity','sign'],['Original 10 actions','Original 14 signs']):
    g=classes[classes.type.eq(typ)].sort_values('our_f1')
    y=np.arange(len(g));ax.barh(y-.18,100*g.friend_f1,.36,color='#8a9dad',label='Friend')
    ax.barh(y+.18,100*g.our_f1,.36,color='#087f8c',label='Ours')
    ax.set_yticks(y,g.label);ax.set_xlim(0,105);ax.set_xlabel('Pooled class F1 (%)');ax.set_title(title)
    for i,v in enumerate(g.our_f1):ax.text(100*v+1,i+.18,f'{100*v:.1f}',va='center',fontsize=8)
    ax.legend(loc='lower right',fontsize=9)
fig.suptitle('Class results on shared P1–P3 isolated test events',fontweight='bold')
fig.text(.02,.015,'Pooled class scores differ from the headline mean-over-participants metric. Each system is scored from saved held-out predictions.',fontsize=9)
fig.tight_layout(rect=[0,.04,1,.94]);fig.savefig(OUT/'matched_class_results.png',dpi=180);plt.close(fig)

summary = pd.read_csv(FRIEND/'results_final_summary.csv',index_col=0)
assert np.isclose(per_pid[(per_pid.part=='signs_standing')].friend_f1.mean(),summary.loc['sign_F1','0'])
assert np.isclose(per_pid[(per_pid.part=='scripts')&(per_pid.type=='sign')].friend_f1.mean(),summary.loc['story_sign_F1','0'])
assert np.isclose(auc.friend_auc.mean(),summary.loc['story_AUC_sign_vs_action','0'])
report = '''# Friend’s results compared with our balanced run

Our run improves isolated recognition on the original participants. Continuous stories remain a limitation, and several story measures are lower. There is no evidence that our model is better at every task.

## Matched original test recordings

Both columns below use the same 684 P1–P3 events and the same 10-action/14-sign class lists. Values are macro F1 averaged equally across held-out participants. Each scored participant was excluded from that system’s training. Story identity is evaluated with the true event boundaries and type supplied.

| Metric | Friend’s final zero-shot | Our balanced run | Change |
|---|---:|---:|---:|
'''
for part,typ,label in plot_rows:
    r=means[(means.part==part)&(means.type==typ)].iloc[0]
    report += f'| {label.replace("*", "")} F1 | {100*r.friend_f1:.1f}% | {100*r.our_f1:.1f}% | {r.change_pp:+.1f} points |\n'
report+=f'| Story sign-versus-action AUC | {100*auc.friend_auc.mean():.1f}% | {100*auc.our_auc.mean():.1f}% | {100*(auc.our_auc.mean()-auc.friend_auc.mean()):+.1f} points |\n'
report+='''
F1 is not accuracy. AUC measures separation of signs from actions across thresholds; it does not measure correct sign identity or successful commands.

The friend’s published action F1 is 48.8%. It becomes 48.6% when restricting both systems to shared events. Their output includes one extra P02 lightswitch event (repetition 9) whose full labelled interval is not covered by the recording. Our preparation excludes that partial interval. No predictions were changed for this comparison.

The friend trained on two other people for each P1–P3 test. Our run trained on four other people, adding P4/P5 and their seated/cooking examples. Architecture, preprocessing, validation and training also differ. These figures compare the saved systems on shared test data; they cannot isolate which change caused a gain. With only three matched test people, small differences are uncertain.

![Matched result comparison](IMAGE_MAIN)

## Isolated results for each original participant

| Participant | Friend action F1 | Our action F1 | Friend sign F1 | Our sign F1 |
|---|---:|---:|---:|---:|
'''
for pid,g in per_pid[per_pid.part.isin(['actions','signs_standing'])].groupby('pid'):
    act=g[g.type.eq('activity')].iloc[0];sign=g[g.type.eq('sign')].iloc[0]
    report+=f'| {pid} | {100*act.friend_f1:.1f}% | {100*act.our_f1:.1f}% | {100*sign.friend_f1:.1f}% | {100*sign.our_f1:.1f}% |\n'
report+='''
## Which classes improved

These class F1 values pool the matched original participants, rather than averaging their individual class F1 scores.

| Class | Friend | Ours | Interpretation |
|---|---:|---:|---|
'''
for name, note in [('wipetable','Large gain'),('pickup','Large gain'),('sitstand','Gain'),('COOK','Large gain'),('FAN','Large gain'),('HELLO','Gain'),('eat','Lower'),('tvremote','Lower and still weak'),('TOILET','Lower'),('WATER','Lower'),('THANKYOU','Neither system recognizes these isolated examples correctly')]:
    r=classes[classes.label.eq(name)].iloc[0]
    report+=f'| {name} | {100*r.friend_f1:.1f}% | {100*r.our_f1:.1f}% | {note} |\n'
report+='''
![All matched class scores](IMAGE_CLASSES)

THANKYOU has 0% F1 for both systems on these original isolated examples. That is a reason to inspect the recorded movement, signal and annotation boundaries. The saved predictions alone cannot establish the cause.

## Full five-person results

Our full held-out P1–P5 results are 50.2% isolated action F1, 33.2% isolated sign F1, 52.4% story action F1 and 24.7% story sign F1 with known story boundaries/type. Those are a wider evaluation: they include P4/P5, seated recordings and two extra action classes. They should not replace the matched table when comparing the original participants.

Isolated seated action/sign F1 is only 19.4%/20.0%, evaluated on P4/P5. The friend has no equivalent isolated seated test set. Chopping and stirring likewise have no matching old classes.

## Calibration is a separate experiment

The friend’s final one-repetition calibration system scores 53.4% action F1 and 29.8% sign F1. It uses a labelled example from the test person per class and excludes those examples from evaluation. Our reported run uses no test-person calibration. These protocols and test sets differ, so the calibrated numbers are not an equal comparison.

The 38% calibrated sign F1 in the friend’s earlier table comes from an earlier CNN experiment. Their saved final-system sign F1 is 29.8%. Keep the experiment names and protocols attached to every figure instead of combining the best numbers from different runs.

## Continuous commands need separate treatment

The friend’s reported 78.3% streaming event F1 combines isolated and story sign detections and does not require correct sign identity. It uses one-second matching tolerance. Our story metrics use stories only, identity-aware scoring and one-to-one overlap matching. Their false-command rate also includes routine time outside stories. Directly comparing those exported streaming F1 or hourly false-command numbers would be misleading.

On the 108 original story sign steps, the friend reports 25.9% detected and 2.8% correct full intent. Our counts are 52 detected (48.1%) and 9 correct full intents (8.3%). These are descriptive because detection matching and context implementations differ. A common re-evaluation of continuous outputs is needed for a defensible improvement claim.

Across all five participants, our system detects 121 of 208 story signs, correctly identifies 39 and produces 32 correct full intents (15.4% end-to-end success). It produces 50 false commands over 20.3 minutes of measured story routine time. Continuous operation is therefore still weak despite better isolated F1.

## What to do next

Keep both baselines. The next experiment should address continuous sign identity, seated performance and false commands. Audit THANKYOU, WATER, TOILET and TV remote examples and boundaries first. Evaluate personal calibration as a separately named protocol, or test changes on a fresh session after validation-based selection. More epochs alone have not been shown to solve these failures.

Use the same stream matching, threshold-selection objective and routine-time denominator for both pipelines before presenting a streaming comparison. A controlled experiment using the same folds, preprocessing and data would be required to attribute improvement to an architecture.

## Evidence

- Friend: `results_final_segments_cal0.csv`, `results_final_summary.csv`, `results_final_stream_cal0.csv`, `final_system.py`, `dense.py`, `RESULTS.md` in `Model_Detect-Activity-and-Gestures`.
- Ours: `all_out_of_fold_predictions.csv`, `summary.csv`, `fold_metrics.csv` and `story_metrics.csv` in `FYP_BALANCED_2H_20261017_015419/results`.
- `participant_comparison.csv`, `matched_class_comparison.csv`, `matched_predictions.csv` and `unmatched_events.csv` preserve the matched comparison. `comparison_manifest.json` records input hashes.

This comparison only reads saved outputs and computes metrics/plots. No training ran on the laptop.
'''
report=report.replace('IMAGE_MAIN',str(DOWNLOAD/'friend_vs_ours.png')).replace('IMAGE_CLASSES',str(DOWNLOAD/'matched_class_results.png'))
(OUT/'Friend_vs_Our_Results.md').write_text(report)
inputs=[FRIEND/'results_final_segments_cal0.csv',FRIEND/'results_final_summary.csv',OURS/'all_out_of_fold_predictions.csv',OURS/'story_metrics.csv']
manifest=dict(matched_events=len(matched),unmatched_events=len(unmatched),
              comparison='Zero-shot saved out-of-fold predictions; matched P1–P3 test events; training pools differ',
              inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              mean_story_auc=auc[['friend_auc','our_auc']].mean().to_dict())
(OUT/'comparison_manifest.json').write_text(json.dumps(manifest,indent=2))
for p in OUT.iterdir():
    if p.is_file() and p.suffix in ('.csv','.md','.png','.json'):
        shutil.copy2(p,DOWNLOAD/p.name)
print(means.to_string(index=False))
print('AUC:',auc[['friend_auc','our_auc']].mean().to_dict())
print('Saved:',DOWNLOAD)
