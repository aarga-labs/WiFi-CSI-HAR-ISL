# Comparative analysis — our CSI pilot vs published WiFi sensing datasets

Answers the question *"did we collect our data correctly?"* by measuring the pilot
capture and comparing it against three published datasets (ARIL, UT-HAR, Widar 3.0).

**Deliverable: [`comparative_analysis.pdf`](comparative_analysis.pdf)** (19 slides, 16:9).

## Headline findings

| | Finding |
|---|---|
| ✅ | **Sampling rate is sufficient** — all class-discriminative energy lies below **18 Hz**; our worst-case Nyquist is 25.7 Hz. The 15× rate deficit vs UT-HAR costs nothing measurable *on this task*. |
| ✅ | **Signal is strong** — `action` carries **4.2×** the motion energy of `noaction` (Fisher ratio 3.85). |
| ✅ | **Our evaluation is the strictest** of the four datasets — leave-one-subject-out, vs ARIL's every-5th-sample and UT-HAR's random split. |
| ✅ | **Front-end matches ARIL** spec-for-spec (USRP N210, 52 subcarriers, SISO, amplitude-only). |
| ⚠️ | **The task is near-trivial** — one scalar + one threshold scores **99.1%**. Our 98.4% deep model does *not* beat that baseline. |
| ⚠️ | **13% of windows silently dropped** — `segment_all_pilot.py` used the default `--rate 100` on 66 Hz data. Fixable with `--rate 50`, no recapture. |
| ⚠️ | **~4 effective dimensions, not 52** — subcarriers are highly correlated during motion, undercutting ImgFi's "×52 free data" claim. |
| ❌ | **Scale/diversity** — 322 samples vs 1,394 / 4,477 / 258,000; 2 subjects, 1 room, 1 day. |

## Files

| File | What |
|---|---|
| `comparative_analysis.tex` / `.pdf` | The deck (build: `pdflatex comparative_analysis.tex`, run twice) |
| `analyze_pilot.py` | Measures every pilot statistic → `pilot_stats.json` |
| `make_figures.py` | Builds all 10 figures → `figures/*.pdf` |
| `pilot_stats.json` | Machine-readable results (rates, jitter, correlation, effective rank, separability, window yield) |

## Rebuild

```bash
cd ~/usrp-projects/analysis
python3 analyze_pilot.py     # -> pilot_stats.json
python3 make_figures.py      # -> figures/*.pdf
pdflatex comparative_analysis.tex && pdflatex comparative_analysis.tex
```

Requires `numpy pandas scipy matplotlib` and a LaTeX install with `beamer`.

## Scope limitation (stated on the last slide too)

Reference datasets are compared on **published specifications only** — we did not
download and re-analyse their raw CSI, so their signal-level statistics (jitter,
effective rank, spectral ratio) are not measured here. Every number describing
*our* pilot is measured directly from `data/pilot/`.
