# Animated collection clips in the existing presentation

## Upload to Overleaf

1. Extract FYP_Overleaf_Animated_Implementation.zip on your computer.
2. Open your existing Overleaf project. Replace main.tex, upload animate.sty beside it, and upload the complete current_impl folder with its media subfolder. Keep the original older images in the project.
3. Select main.tex as the main document. Use pdfLaTeX with TeX Live 2024 or newer, then Recompile. No shell escape or video conversion is needed in Overleaf.
4. Download the compiled PDF and open it in desktop Firefox 130 or newer, or desktop Adobe Acrobat Reader. The Overleaf preview and Chrome/Edge's built-in PDF viewers may show only the first frame.
5. Open numbered slide 23 to test the two collection clips; slide 24 contains the story clip. They loop automatically in supported viewers. Use the small play/pause/stop controls underneath if needed. Test playback on the actual presentation computer before the review.

Current_Implementation_Animated_Preview.pdf contains the eleven updated implementation slides only. It is ready to test separately. The matching preview .tex is also included if you want to compile only these slides. The full deck source is main.tex; older image assets must remain in your existing project.

## What changed

- Numbered slide 21 uses the supplied setup JPEG.
- Slide 22 lists the 12 actions and 14 signs.
- New slide 23 shows larger standing and seated collection animations side by side.
- Slide 24 includes the story-recording animation.
- Slides 25–26 show the data excerpt and per-class recording counts.
- Slides 32–36 retain the trained model and verified result graphs/tables.
- The full source contains 43 frames, including two unnumbered opening slides. The maroon theme and research-objective banners are retained.

The clip captions describe standing/seated/story collection. Exact gesture identities and timing have not been verified against the label files, so the captions do not infer an action or sign merely from the filenames.

## How the PDF animation works

Each original MP4 is converted to a multipage frame PDF. The animate package embeds all frames and playback controls into the final PDF. This preserves the original 25/3 frames per second, without slowing or speeding up the supplied clips:

| Source | Embedded frames | Duration |
|---|---:|---:|
| collection_action_pickup.mp4 | 25 | 3.00 s |
| collection_sign_cook_seated.mp4 | 31 | 3.72 s |
| collection_story_meal.mp4 | 30 | 3.60 s |

The files ending _frames.pdf are the animation inputs. Keep them in current_impl/media. The final downloaded presentation PDF is self-contained: it does not need external MP4 files alongside it. Original MP4s and poster JPEGs are also included as backups. The motion is silent.

The source uses:

```tex
\usepackage{animate}
\newcommand{\implclip}[2]{%
  \animategraphics[type=pdf,method=widget,autoplay,loop,autopause,
    controls={play,stop},buttonsize=0.17cm,
    width=\linewidth,height=#2,keepaspectratio,poster=first,label=#1]
    {8.333333}{current_impl/media/#1_frames}{}{}%
}
```

Example inside a column:

```tex
\implclip{collection_action_pickup}{3.20cm}
```

The supplied official animate.sty is version 2024/10/14 by Alexander Grahn, distributed under the LaTeX Project Public License. It is included to avoid an older package choosing a playback method incompatible with Firefox. Package documentation: https://ctan.org/pkg/animate

## Results retained

Retained collection: 2,050,030 raw rows / 25 recordings, including empty-room QC. Model input: 2,010,899 rows / 22 participant recordings; totals include rest/ready. The per-class table counts fully covered isolated intervals: 416,836 action rows and 222,570 sign rows.

The retained balanced model reports all-five held-out participant results: 311/628 actions correct (49.5%) and 171/490 signs correct (34.9%). Mean held-out macro F1 is 50.2% and 33.2%, respectively. Graphs show per-class recall and correct counts.

The threshold table is the separately labelled P1–P3 fixed-threshold sweep over 318 signs. Its matching protocol differs from the all-five automatic story assessment. Detection is distinct from correct naming. A score threshold is not calibrated certainty.

The final all-five deployment model has no separate independent test score. Seated/cooking isolated examples cover P4/P5. Cue-based labels have not yet been aligned against these video clips. No model was retrained or changed for the presentation.

## Verification

The eleven-slide preview compiled successfully with pdfLaTeX (TeX Live 2026), with no overfull text warnings. All pages were rendered and visually checked. The PDF contains three animation fields, 25/31/30 embedded frame widgets, and JavaScript playback actions. Interactive playback has not been exercised here; test the downloaded PDF in your presentation viewer. The complete source was checked in a separate local layout build, using labelled substitutes only for older images absent from this checkout; those substitutes are not present in the delivered main.tex.
