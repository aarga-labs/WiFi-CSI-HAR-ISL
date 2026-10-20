from pathlib import Path
import re,json
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'presentation_current'
backup=HERE/'main_before_animations.tex'
if not backup.exists(): backup.write_bytes((ROOT/'main.tex').read_bytes())
text=backup.read_text()
text=text.replace(r'\usepackage{graphicx}',r'\usepackage{graphicx}'+'\n'+r'\usepackage{animate}',1)
a=text.index('% Current collection photographs are optional')
b=text.index(r'\newcommand{\implnote}',a)
text=text[:a]+r'''% Self-contained PDF animations; each page of the frame PDF is one frame.
% The supplied media are preconverted, so Overleaf needs no shell escape.
\newcommand{\implclip}[2]{%
  \animategraphics[type=pdf,method=widget,autoplay,loop,autopause,
    controls={play,stop},buttonsize=0.17cm,
    width=\linewidth,height=#2,keepaspectratio,poster=first,label=#1]
    {8.333333}{current_impl/media/#1_frames}{}{}%
}
'''+text[b:]
text=text.replace(r'\implphoto{collection_setup.png}{2.45cm}{Room, transmitter and receiver}',r'\includegraphics[width=\linewidth,height=2.45cm,keepaspectratio]{current_impl/media/collection_setup.jpeg}')
for stem,label in [('collection_action_pickup','Isolated action: pick up an object'),('collection_sign_cook_seated','Seated sign: COOK')]:
    old=r'\centering'+'\n'+r'\implphoto{'+stem+r'.png}{1.50cm}{'+label+'}\n'+r'\vspace{0.12cm}'+'\n\n'
    assert old in text,stem
    text=text.replace(old,'',1)
text=text.replace(r'\implphoto{collection_story_meal.png}{2.50cm}{Meal story: sign after an action}',r'\implclip{collection_story_meal}{2.30cm}'+'\n'+r'\par\vspace{0.10cm}{\scriptsize Story recording excerpt\par}')
new=r'''
\begin{frame}{23. Current Dataset: Recording Demonstration}
\roone
\begin{columns}[T,onlytextwidth]
\column{0.485\textwidth}
\centering
{\small\textbf{\color{AmritaMaroon}Standing collection excerpt}}\par
\vspace{0.16cm}
\implclip{collection_action_pickup}{3.20cm}\par
\vspace{0.15cm}
{\footnotesize Standing participant within the collection area.\par}
\column{0.485\textwidth}
\centering
{\small\textbf{\color{AmritaMaroon}Seated collection excerpt}}\par
\vspace{0.16cm}
\implclip{collection_sign_cook_seated}{3.20cm}\par
\vspace{0.15cm}
{\footnotesize Seated posture and hand movement during recording.\par}
\end{columns}
\vspace{0.18cm}
\implnote{Short excerpts from the recorded collection videos. The label files define the action/sign classes and time intervals.}
\end{frame}

'''
anchor=r'\begin{frame}{23. Current Dataset: Interleaved Stories}'
assert anchor in text
text=text.replace(anchor,new+anchor,1)
counter=[0]
def renumber(m):
    counter[0]+=1
    return m.group(1)+str(counter[0])+'. '
text=re.sub(r'(\\begin\{frame\}(?:\[[^\]]*\])?\{)\d+\.\s*',renumber,text)
assert counter[0]==41
(ROOT/'main.tex').write_bytes(text.replace('\n','\r\n').encode())
frames=re.findall(r'\\begin\{frame\}(?:\[[^\]]*\])?(?:\{[^\n]*\})?[\s\S]*?\\end\{frame\}',text)
current=[f for f in frames if re.search(r'\\begin\{frame\}(?:\[[^\]]*\])?\{\d+\. Current (?:Dataset|Model|Results):',f)]
assert len(current)==11
preamble=text.split(r'\begin{document}')[0]
preview=preamble+r'\begin{document}'+'\n'+'\n'.join(current)+'\n'+r'\end{document}'
(ROOT/'current_implementation_animated_preview.tex').write_text(preview)
(HERE/'animated_frame_manifest.json').write_text(json.dumps(dict(total_frames=len(frames),current_frames=len(current),current_titles=[re.search(r'\\begin\{frame\}[^\n]*',f).group(0) for f in current]),indent=2))
print('Updated main.tex:',len(frames),'total frames;',len(current),'current slides; 3 animations')
