from pathlib import Path
import datetime
import json
import re
import shutil

ROOT=Path('/home/adhikkesh/adhikkesh/FYP')
HERE=Path(__file__).parent
MAIN=ROOT/'main.tex'
BACKUP=HERE/'main_before_current_implementation.tex'
if not BACKUP.exists():shutil.copy2(MAIN,BACKUP)
text=BACKUP.read_text()
# Beamer preloads xcolor; pass the table option at class load time.
text=text.replace(r'\documentclass[aspectratio=169,11pt]{beamer}',
                  r'\documentclass[aspectratio=169,11pt,xcolor=table]{beamer}',1)
text=text.replace(r'\raggedcolumns','')

helpers=r'''
% Current collection photographs are optional until uploaded to Overleaf.
% Put these four PNGs next to main.tex; missing photographs render as labelled boxes.
\newcommand{\implphoto}[3]{%
  \IfFileExists{#1}{%
    \includegraphics[width=\linewidth,height=#2,keepaspectratio]{#1}%
  }{%
    \fcolorbox{AmritaMaroon}{LightGray}{%
      \parbox[c][#2][c]{0.92\linewidth}{\centering\scriptsize
        \textbf{#3}\\[4pt]\texttt{\detokenize{#1}}}%
    }%
  }%
}
\newcommand{\implnote}[1]{{\scriptsize\color{AmritaDark}#1\par}}
'''
text=text.replace(r'\begin{document}',helpers+'\n'+r'\begin{document}',1)

collection_overview=r'''
\begin{frame}{21. Current Dataset: Collection and Coverage}
\roone
\begin{columns}[T,onlytextwidth]
\column{0.56\textwidth}
{\small\textbf{\color{AmritaMaroon}5 people \quad 25 kept recordings \quad 2,050,030 raw rows}}
\vspace{0.13cm}

\scriptsize
\renewcommand{\arraystretch}{1.32}
\begin{tabular}{@{}lrr@{}}
\toprule
\textbf{Recording block} & \textbf{Files} & \textbf{CSI rows}\\
\midrule
Actions: main block & 5 & 844,426\\
Actions: seated & 2 & 173,297\\
Signs: standing & 5 & 457,408\\
Signs: seated & 2 & 127,209\\
Interleaved stories & 5 & 354,465\\
Still-person baselines & 3 & 54,094\\
Empty-room checks & 3 & 39,131\\
\midrule
\textbf{Total collected} & \textbf{25} & \textbf{2,050,030}\\
\bottomrule
\end{tabular}
\vspace{0.15cm}

\implnote{Model input: \textbf{22 files / 2,010,899 rows}.
Recording totals include rest/ready; empty-room files are QC only.}
\column{0.41\textwidth}
\centering
\implphoto{collection_setup.png}{2.45cm}{Room, transmitter and receiver}
\vspace{0.16cm}

\raggedright\footnotesize
\textbf{\color{AmritaMaroon}Collection conditions}\\[3pt]
Two USRP N210s; Channel 1, 2412 MHz.\\[3pt]
Same room and antenna positions.\\[3pt]
One active participant at a time.\\[3pt]
P4/P5 add seated blocks and cooking actions.
\end{columns}
\end{frame}
'''

vocabulary=r'''
\begin{frame}{22. Current Dataset: Actions and Signs}
\roone
\begin{columns}[T,onlytextwidth]
\column{0.49\textwidth}
\centering
\implphoto{collection_action_pickup.png}{1.50cm}{Isolated action: pick up an object}
\vspace{0.12cm}

\raggedright
{\small\textbf{\color{AmritaMaroon}12 action labels}}\\[5pt]
\footnotesize
\renewcommand{\arraystretch}{1.16}
\begin{tabular}{@{}ll@{}}
Walk & Sit--stand\\
Pick up & Light switch\\
Drink & Answer phone\\
Eat & Wipe table\\
TV remote & Fall\\
Chop food & Stir pot
\end{tabular}
\vspace{0.14cm}

\implnote{628 isolated trials. P4/P5 add chop/stir and seven seated action types.}
\column{0.49\textwidth}
\centering
\implphoto{collection_sign_cook_seated.png}{1.50cm}{Seated sign: COOK}
\vspace{0.12cm}

\raggedright
{\small\textbf{\color{AmritaMaroon}14 sign labels}}\\[5pt]
\footnotesize
\renewcommand{\arraystretch}{1.16}
\begin{tabular}{@{}ll@{}}
HELLO & THANKYOU\\
LAMP & FAN\\
TELEVISION & COOK\\
WATER & HOT\\
HUNGRY & TOILET\\
CALL & HELP\\
PAIN & ACCIDENT
\end{tabular}
\vspace{0.12cm}

\implnote{490 trials: 350 standing (P1--P5) + 140 seated (P4/P5).}
\end{columns}
\end{frame}
'''

stories=r'''
\begin{frame}{23. Current Dataset: Interleaved Stories}
\roonefour
\begin{columns}[T,onlytextwidth]
\column{0.62\textwidth}
\scriptsize
\renewcommand{\arraystretch}{1.35}
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{1.35cm}>{\raggedright\arraybackslash}p{6.9cm}@{}}
\toprule
\textbf{Template} & \textbf{Recorded sequence / context}\\
\midrule
M-SEQ: meal & Walk, light switch, sit--stand, eat/drink; HELLO, HUNGRY, COOK, HOT, WATER, THANKYOU. P4/P5 add chop/stir.\\
T-SEQ: TV & Walk, sit--stand, TV remote, phone; HELLO, TELEVISION, HOT, LAMP, CALL, TOILET; stand and walk out.\\
C-SEQ: clean / fall & Walk, wipe, pick up; FAN, HELP; walk and fall; HELP, PAIN, ACCIDENT, CALL on the mattress.\\
S-SEQ: seated & Wipe, chop, stir, eat, drink; HELLO, HUNGRY, COOK, HOT, WATER, HELP, THANKYOU. P4/P5 only.\\
\bottomrule
\end{tabular}
\vspace{0.14cm}

\implnote{Each available template was repeated twice per person:
\textbf{34 runs / 416 labelled steps} = 208 actions + 208 signs.}
\column{0.35\textwidth}
\centering
\implphoto{collection_story_meal.png}{2.50cm}{Meal story: sign after an action}
\vspace{0.12cm}

\raggedright\footnotesize
\textbf{\color{AmritaMaroon}Why stories matter}\\[4pt]
Actions and signs share one recording.\\[4pt]
HOT during a meal and HOT while watching TV have different intended responses.
\end{columns}
\end{frame}
'''

schema=r'''
\begin{frame}{24. Current Dataset: CSI Rows and Annotations}
\roone
\begin{center}
\includegraphics[width=0.97\linewidth,height=4.55cm,keepaspectratio]{current_impl/dataset_excerpt.pdf}
\end{center}
\vspace{-0.08cm}
\implnote{Actual CSV excerpt, selected columns. Raw rows contain packet/time/channel and complex CSI;
the separate label file supplies participant, type, label, posture and time boundaries.
Labels come from the collection cues/key presses; video alignment is not yet verified.}
\end{frame}
'''

# Keep the individual class row counts editable in LaTeX rather than rasterizing them.
import pandas as pd
rowcounts=pd.read_csv(HERE/'isolated_raw_rows_by_class.csv')
names={'walk':'Walk','sitstand':'Sit--stand','pickup':'Pick up','lightswitch':'Light switch','drink':'Drink',
       'answerphone':'Answer phone','eat':'Eat','wipetable':'Wipe table','tvremote':'TV remote','fall':'Fall',
       'chop_food':'Chop food','stir_pot':'Stir pot'}
tables=[]
for typ,heading in [('activity','Actions'),('sign','Signs')]:
    rows=rowcounts[rowcounts.type.eq(typ)]
    body='\n'.join(f'{names.get(r.label,r.label)} & {r.trials:,} & {r.raw_rows:,}\\\\' for r in rows.itertuples())
    tables.append(r'{\small\textbf{\color{AmritaMaroon}'+heading+r'}}\\[4pt]'+'\n'+
        r'\fontsize{7}{8.1}\selectfont\renewcommand{\arraystretch}{0.94}'+'\n'+r'\begin{tabular}{@{}lrr@{}}\toprule'+
        '\n'+r'\textbf{Class} & \textbf{Trials} & \textbf{Raw rows}\\\midrule'+'\n'+body+'\n'+
        f'\\midrule\\textbf{{Total}} & \\textbf{{{rows.trials.sum():,}}} & \\textbf{{{rows.raw_rows.sum():,}}}\\\\\n'+r'\bottomrule\end{tabular}')
class_rows=r'''
\begin{frame}{25. Current Dataset: Recording Rows per Class}
\roone
\begin{columns}[T,onlytextwidth]
\column{0.49\textwidth}
'''+tables[0]+r'''
\column{0.49\textwidth}
'''+tables[1]+r'''
\end{columns}
\vspace{0.10cm}
\implnote{Raw packets inside fully covered isolated label intervals; rest/ready and story steps excluded.
Partial P2 trials excluded. Chop/stir: P4/P5 only.}
\end{frame}
'''

model=r'''
\begin{frame}{31. Current Model: Training and Evaluation}
\roone
\begin{center}
\begin{tikzpicture}[
 box/.style={draw=AmritaMaroon,rounded corners=5pt,align=center,minimum height=1.25cm,text width=2.65cm,font=\scriptsize,inner sep=5pt},
 arr/.style={-{Latex},thick}]
\node[box,fill=LightBlue] (raw) {\textbf{CSI + time labels}\\52 complex subcarriers\\Magnitude input};
\node[box,fill=LightGreen,right=0.25cm of raw] (prep) {\textbf{Preprocessing}\\Log magnitude\\0.3--18 Hz; 50 Hz output};
\node[box,fill=LightOrange,right=0.25cm of prep] (cnn) {\textbf{Residual 1D CNNs}\\4 s / 6 s windows\\State + class heads};
\node[box,fill=LightPink,right=0.25cm of cnn] (out) {\textbf{Predictions}\\Idle / activity / sign\\12 actions + 14 signs};
\draw[arr](raw)--(prep);\draw[arr](prep)--(cnn);\draw[arr](cnn)--(out);
\end{tikzpicture}
\end{center}
\vspace{0.12cm}
\begin{columns}[T,onlytextwidth]
\column{0.54\textwidth}
\footnotesize
\textbf{\color{AmritaMaroon}Five held-out-person tests}
\begin{itemize}\setlength{\itemsep}{3pt}
\item Initial fit: 3 people; validation: 1 other person.
\item Choose detector/action/sign roles on validation.
\item Refit selected networks on 4 people, two seeds.
\item Test only on the fifth person; repeat for all five.
\end{itemize}
\column{0.43\textwidth}
\footnotesize
\textbf{\color{AmritaMaroon}All-five deployment model}\\[5pt]
Two normalized four-second CNNs, one per seed, trained on all five people.\\[5pt]
Scales, masks and class order saved.\\[5pt]
Kaggle T4 $\times$2: \textbf{41.4 minutes}.
\end{columns}
\vspace{0.13cm}
\implnote{Scores come from held-out folds; the all-five refit has no independent score.
Inference is offline. ExtraTrees applies only to isolated action fusion (final weight: zero).}
\end{frame}
'''

action_results=r'''
\begin{frame}{32. Current Results: Action Recognition}
\roone
{\footnotesize\textbf{\color{AmritaMaroon}311/628 correct (49.5\% accuracy)}
\hfill Mean held-out macro F1: \textbf{50.2\%}}
\begin{center}
\includegraphics[width=\linewidth,height=4.45cm,keepaspectratio]{current_impl/action_class_performance.pdf}
\end{center}
\vspace{-0.08cm}
\implnote{P1--P5 isolated trials, known boundaries/type; bars show per-class recall.
\textbf{Strongest:} walk/pick up. \textbf{Weakest:} TV remote/chop/phone.
Chop/stir cover P4/P5 only.}
\end{frame}
'''

sign_results=r'''
\begin{frame}{33. Current Results: Sign Recognition}
\roone
{\footnotesize\textbf{\color{AmritaMaroon}171/490 correct (34.9\% accuracy)}
\hfill Mean held-out macro F1: \textbf{33.2\%}}
\begin{center}
\includegraphics[width=\linewidth,height=4.45cm,keepaspectratio]{current_impl/sign_class_performance.pdf}
\end{center}
\vspace{-0.08cm}
\implnote{P1--P5: 350 standing + 140 seated trials; 35 per sign; known boundaries/type.
\textbf{Stronger:} COOK/HUNGRY/PAIN. \textbf{Weakest:} THANKYOU/WATER/TOILET.
Isolated seated signs cover P4/P5 only.}
\end{frame}
'''

threshold=r'''
\begin{frame}{34. Current Results: Detection Threshold}
\roonefour
\begin{columns}[T,onlytextwidth]
\column{0.54\textwidth}
\footnotesize
\renewcommand{\arraystretch}{1.25}
\begin{tabular}{@{}lrr@{}}
\toprule
\textbf{Setting} & \textbf{Signs caught} & \textbf{False / hour}\\
\midrule
$\tau=0.3$: sensitive & 71.4\% & 27.5\\
$\tau=0.5$: middle & 68.9\% & 14.6\\
$\tau=0.7$: strict & 54.7\% & 10.5\\
\bottomrule
\end{tabular}
\vspace{0.25cm}

\footnotesize
Raise $\tau$ to reduce false triggers; fewer signs are caught.\\[5pt]
``Caught'' means detected, not correctly named.\\[5pt]
$\tau$ is a score cutoff, not calibrated certainty.
\column{0.43\textwidth}
\includegraphics[width=\linewidth,height=4.25cm,keepaspectratio]{current_impl/threshold_tradeoff.pdf}
\end{columns}
\vspace{0.16cm}
\implnote{Fixed-threshold sweep: P1--P3, isolated + stories, 318 signs; mean over three people.
One-second smoothing/minimum run, one-second gap merge and $\pm$1 s matching.
Rates cover routine movement only (about 58 measured minutes), excluding idle/unknown periods.}
\end{frame}
'''

story_results=r'''
\begin{frame}{35. Current Results: Continuous Story Recognition}
\roonefour
\begin{columns}[T,onlytextwidth]
\column{0.72\textwidth}
\includegraphics[width=\linewidth,height=4.55cm,keepaspectratio]{current_impl/story_recognition.pdf}
\column{0.25\textwidth}
\footnotesize
\textbf{\color{AmritaMaroon}Automatic story inference}\\[5pt]
No true sign boundaries or type are supplied.\\[6pt]
\textbf{58.2\%} of signs detected.\\[5pt]
\textbf{18.8\%} correctly named.\\[5pt]
\textbf{15.4\%} correct full intent.\\[7pt]
Continuous identity is the main remaining limitation.
\end{columns}
\vspace{0.13cm}
\implnote{All five people; validation-selected thresholds per fold; one-to-one IoU $\geq0.10$ matching.
This differs from the fixed-threshold sweep. There were 50 false triggers during 20.3 minutes of measured story routine activity.}
\end{frame}
'''

def replace_frame(source,number,replacement):
    pattern=r'\\begin\{frame\}(?:\[[^\]]*\])?\{'+str(number)+r'\.[\s\S]*?\\end\{frame\}'
    result,n=re.subn(pattern,lambda _:replacement.strip(),source,count=1)
    assert n==1,number
    return result

text=replace_frame(text,21,collection_overview)
text=replace_frame(text,22,vocabulary+'\n'+stories+'\n'+schema+'\n'+class_rows)
anchor=r'\begin{frame}{28. MOOC / Course Selection}'
assert anchor in text
text=text.replace(anchor,'\n'.join([model,action_results,sign_results,threshold,story_results])+'\n'+anchor)

# Historical binary scores remain clearly separate from the verified multiclass experiment.
text=text.replace('24. Model Architecture \\& Methodology','24. Earlier Pilot: Binary Action Model')
text=text.replace('25. Model Performance \\& Results','25. Earlier Pilot: Action vs. No-Action Results')
text=text.replace('26. Model 2 Architecture \\& Methodology (Activity vs Gesture)','26. Earlier Pilot: Activity vs. Gesture Model')
text=text.replace('27. Model 2 Performance \\& Results','27. Earlier Pilot: Activity vs. Gesture Results')
text=text.replace('Sequential hopping across Channels 1, 6 and 11','Current collection: fixed Channel 1 (2412 MHz)')
text=text.replace('$\\approx$100 ms dwell per channel','Hopping retained as an optional hardware capability')
text=text.replace('The current CNN pipeline evaluates pre-segmented 2-second temporal windows; it cannot yet dynamically segment or classify continuous, overlapping multi-person activities in real-time.',
                  'The current CSI model uses centered 4--6 second windows for offline inference. Continuous sign naming and false-trigger control remain weak; overlapping multi-person recognition has not been evaluated.')
text=text.replace('More labeled data from different environments, people, and gestures is required.',
                  'Five people were recorded in one room; isolated seated and cooking examples cover only P4/P5. A fresh session or person is needed to confirm generalization, and cue-based labels still need video verification.')

# Keep the two existing slides whose wording was updated within their old layout.
hardware=re.search(r'\\begin\{frame\}\{13\.[\s\S]*?\\end\{frame\}',text).group(0)
hardware=hardware.replace(r'\vspace{0.65cm}',r'\vspace{0.40cm}').replace(r'\vspace{0.5cm}',r'\vspace{0.20cm}')
text=replace_frame(text,13,hardware)
limits=re.search(r'\\begin\{frame\}\{29\. Limitations\}[\s\S]*?\\end\{frame\}',text).group(0)
limits=limits.replace(r'\vspace{0.35cm}',r'\vspace{0.12cm}')
limits=limits.replace('    align=left,','    align=left,\n    font=\\small,',1)
limits=limits.replace('Isolated Window Classification','Continuous Recognition')
text=replace_frame(text,29,limits)

# Re-number all numbered frame titles to preserve the original deck's convention.
counter=[0]
def number_title(m):
    counter[0]+=1
    return m.group(1)+str(counter[0])+'. '
text=re.sub(r'(\\begin\{frame\}(?:\[[^\]]*\])?\{)\d+\.\s*',number_title,text)
assert counter[0]==40,counter
MAIN.write_bytes(text.replace('\n','\r\n').encode())

# Standalone current-implementation preview uses the exact original preamble.
preamble=text.split(r'\begin{document}')[0]+r'\graphicspath{{../}{./}}'+'\n'
all_frames=re.findall(r'\\begin\{frame\}(?:\[[^\]]*\])?(?:\{[^\n]*\})?[\s\S]*?\\end\{frame\}',text)
current=[f for f in all_frames if re.search(r'\\begin\{frame\}(?:\[[^\]]*\])?\{\d+\. Current (?:Dataset|Model|Results):',f)]
assert len(current)==10,len(current)
(HERE/'current_implementation_preview.tex').write_text(preamble+r'\begin{document}'+'\n'+'\n'.join(current)+'\n'+r'\end{document}')
(HERE/'frame_manifest.json').write_text(json.dumps(dict(total_frames=len(all_frames),current_frames=len(current),
 current_titles=[re.search(r'\\begin\{frame\}[^\n]*',f).group(0) for f in current]),indent=2))
print('Updated',MAIN,'frames',len(all_frames),'current implementation frames',len(current))
