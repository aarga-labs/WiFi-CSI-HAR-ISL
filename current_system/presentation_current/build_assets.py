"""Build presentation figures from recorded rows and saved held-out predictions.
No classifier fitting or training is performed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).parent
ASSETS=ROOT/'current_impl';ASSETS.mkdir(exist_ok=True)
RESULTS=ROOT/'Kaggle_P1_P5/balanced_results_audit_20261017/run/FYP_BALANCED_2H_20261017_015419/results'
d=pd.read_csv(RESULTS/'all_out_of_fold_predictions.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'text.color':'#242424',
                     'axes.labelcolor':'#242424','axes.spines.top':False,'axes.spines.right':False,
                     'axes.titleweight':'bold','axes.titlecolor':'#5F0023','savefig.facecolor':'white'})
NAMES={'walk':'Walk','sitstand':'Sit–stand','pickup':'Pick up','lightswitch':'Light switch',
       'drink':'Drink','answerphone':'Answer phone','eat':'Eat','wipetable':'Wipe table',
       'tvremote':'TV remote','fall':'Fall','chop_food':'Chop food','stir_pot':'Stir pot'}

def save(fig,name):
    fig.savefig(ASSETS/(name+'.pdf'),bbox_inches='tight',pad_inches=.12)
    fig.savefig(ASSETS/(name+'.png'),dpi=210,bbox_inches='tight',pad_inches=.12)
    plt.close(fig)

rows=[]
for typ,name in [('activity','action_class_performance'),('sign','sign_class_performance')]:
    g=d[d.part.ne('scripts')&d.type.eq(typ)]
    stats=[]
    for label,x in g.groupby('label'):
        wrong=x[x.label.ne(x.pred)].pred.value_counts()
        stats.append(dict(label=label,correct=int(x.label.eq(x.pred).sum()),n=len(x),
                          recall=float(x.label.eq(x.pred).mean()),
                          common_mistake=str(wrong.index[0]) if len(wrong) else 'none'))
    p=pd.DataFrame(stats).sort_values(['recall','label']);p.to_csv(HERE/(name+'.csv'),index=False)
    rows+=p.assign(type=typ).to_dict('records')
    fig,axes=plt.subplots(1,2,figsize=(12,3.7))
    fig.subplots_adjust(left=.115,right=.99,bottom=.24,top=.98,wspace=.67)
    ordered=p.iloc[::-1];midpoint=(len(ordered)+1)//2
    for ax,g in zip(axes,[ordered.iloc[:midpoint],ordered.iloc[midpoint:]]):
        color=['#36805B' if v>=.7 else '#D89439' if v>=.4 else '#A50037' for v in g.recall]
        ax.barh(np.arange(len(g)),100*g.recall,color=color,height=.64)
        ax.set_yticks(np.arange(len(g)),[NAMES.get(n,n) for n in g.label],fontsize=17)
        ax.invert_yaxis();ax.set_xlim(0,150);ax.set_xticks([0,50,100]);ax.tick_params(axis='x',labelsize=14)
        ax.set_xlabel('Correctly named (%)',fontsize=15)
        ax.xaxis.grid(True,alpha=.15);ax.set_axisbelow(True);ax.spines['left'].set_visible(False)
        for y,r in enumerate(g.itertuples()):
            ax.text(100*r.recall+2,y,f'{100*r.recall:.0f}% ({r.correct}/{r.n})',va='center',fontsize=16)
    fig.legend(handles=[Patch(color='#36805B',label='70% or more'),Patch(color='#D89439',label='40–69%'),
                        Patch(color='#A50037',label='Below 40%')],loc='lower center',bbox_to_anchor=(.51,-.025),
               frameon=False,ncol=3,fontsize=13)
    save(fig,name)

pd.DataFrame(rows).to_csv(HERE/'all_class_performance.csv',index=False)

# Actual raw CSV and annotation excerpts. This is a rendered data view, not a
# photograph or fabricated desktop screenshot.
raw=pd.read_csv(HERE/'actual_CSI_sample.csv')
label=pd.read_csv(HERE/'actual_label_sample.csv')
fig=plt.figure(figsize=(14,5.25));fig.patch.set_facecolor('white')
fig.text(.015,.96,'Raw CSI file: one row per decoded packet',fontsize=16,weight='bold',color='#5F0023')
fig.text(.015,.90,'P04_signs_seated_20261016_174235.csv  |  107 columns: 3 metadata + 52 × (Re, Im)',fontsize=11.5)
ax=fig.add_axes([.015,.54,.97,.30]);ax.axis('off')
cols=['Packet','Timestamp_us','Channel','SC0_Re','SC0_Im','SC1_Re','SC1_Im']
values=[]
for r in raw.itertuples(index=False):
    values.append([str(int(getattr(r,c))) if c in cols[:3] else f'{getattr(r,c):.6f}' for c in cols]+['…'])
table=ax.table(cellText=values,colLabels=cols+['…'],cellLoc='center',loc='center',
               colWidths=[.08,.21,.075,.13,.13,.13,.13,.04])
table.auto_set_font_size(False);table.set_fontsize(11);table.scale(1,1.65)
for (i,j),cell in table.get_celld().items():
    cell.set_edgecolor('#dedede')
    cell.set_facecolor('#A50037' if i==0 else '#f8f8f8' if i%2 else 'white')
    if i==0:cell.set_text_props(color='white',weight='bold')
fig.text(.015,.46,'Separate label file: join each packet to its annotated time interval',fontsize=15,weight='bold',color='#5F0023')
ax=fig.add_axes([.015,.12,.97,.27]);ax.axis('off')
labelcols=['pid','type','label','posture','t_start_us','t_end_us']
values=[[str(int(getattr(r,c))) if c.startswith('t_') else str(getattr(r,c)) for c in labelcols] for r in label.itertuples(index=False)]
t=ax.table(cellText=values,colLabels=labelcols,cellLoc='center',loc='center',colWidths=[.07,.09,.14,.12,.28,.28])
t.auto_set_font_size(False);t.set_fontsize(11);t.scale(1,1.65)
for (i,j),cell in t.get_celld().items():
    cell.set_edgecolor('#dedede');cell.set_facecolor('#5F0023' if i==0 else '#edf6ef' if i%2 else 'white')
    if i==0:cell.set_text_props(color='white',weight='bold')
fig.text(.015,.035,'Selected columns shown. Values are copied from the actual recording and label CSVs; other subcarrier columns are omitted.',fontsize=10.5,color='#555555')
save(fig,'dataset_excerpt')

thresholds=pd.read_csv(ROOT/'paper/evidence/threshold_comparison_same_detection_rules.csv')
fig,ax=plt.subplots(figsize=(5.5,4))
ax.plot(thresholds.ours_false_per_routine_hour,100*thresholds.ours_detection_recall,'o-',color='#A50037',lw=2,ms=8)
for r in thresholds.itertuples():ax.annotate(f'τ = {r.tau:.1f}',(r.ours_false_per_routine_hour,100*r.ours_detection_recall),xytext=(6,6),textcoords='offset points',fontsize=12)
ax.set(xlim=(0,34),ylim=(40,85),xlabel='False triggers / routine hour',ylabel='Signs detected (%)')
ax.grid(alpha=.15);fig.tight_layout();save(fig,'threshold_tradeoff')

story=pd.read_csv(RESULTS/'story_metrics.csv');counts=[int(story.n_true.sum()),int(story.detected.sum()),int(story.identified.sum()),int(story.intent_correct.sum())]
assert counts==[208,121,39,32]
fig,ax=plt.subplots(figsize=(9.8,4.6));fig.subplots_adjust(left=.29,right=.95,bottom=.15,top=.96)
ax.barh([3,2,1,0],counts,color=['#9d9d9d','#D89439','#A50037','#5F0023'],height=.60)
ax.set_yticks([3,2,1,0],['True story signs','Detected as a sign','Correct sign name','Correct full intent'],fontsize=13)
ax.set_xlim(0,245);ax.set_xticks([0,50,100,150,200]);ax.set_xlabel('Number of story signs (out of 208)')
ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.spines['left'].set_visible(False)
for y,value in zip([3,2,1,0],counts):ax.text(value+3,y,f'{value}  ({100*value/208:.1f}%)',va='center',fontsize=13)
save(fig,'story_recognition')

# Complete collection manifest summary, machine readable for slide insertion.
info=json.loads((HERE/'verified_dataset_counts.json').read_text())
perf={}
for typ in ['activity','sign']:
    g=d[d.type.eq(typ)&d.part.ne('scripts')]
    perf[typ]=dict(correct=int(g.label.eq(g.pred).sum()),n=len(g),accuracy=float(g.label.eq(g.pred).mean()))
info['performance']=perf
info['story_counts']=counts
(HERE/'slide_data.json').write_text(json.dumps(info,indent=2))
print('Assets:',[p.name for p in ASSETS.iterdir()]);print(json.dumps(perf,indent=2))
