# Research-paper workspace

Read `../Adhi_To_Amrith_Context.md`, then `CLAIM_LEDGER.md` and `PERCOM_WIP_RULES.md`. The accepted `../Research_Paper.pdf` is a historical two-page abstract/introduction, not the final current manuscript. `../main.tex` is the presentation; put a new IEEE article under `paper/manuscript/` when authoring starts.

## Before drafting

```bash
python3 paper/tools/verify_evidence.py
```

Run from the repository root. Standard-library only, read-only, no training, no raw-data requirement. It checks all 34 saved fold metric rows, pooled identity counts, summary means, dataset/annotation integrity, story counts, model references and committed evidence hashes. Recomputed results do not replace an independent new test session.

## Evidence

`evidence/` contains exact copies of the retained balanced run's key tables, all 22 annotation CSVs, the selected session log, capture audits, class raw-row counts, threshold sweep, comparison-method notes and actual CSV excerpts. `SOURCE_MAP.json` maps them to original source locations. `evidence_manifest.json` lists SHA256 for those copies; do not modify results in place to make a paper claim fit.

The complete per-fold outputs/probability arrays remain under `../Kaggle_P1_P5/balanced_results_audit_20261017/run/FYP_BALANCED_2H_20261017_015419/results/`. The original P1–P3 source/results are under `../Model_Detect-Activity-and-Gestures/`. Both are available without downloading full checkpoint archives.

## Draft shape

1. Introduction + focused related work.
2. Actual hardware, collection/labels and model.
3. Split, baselines, preliminary results and continuous recognition.
4. Error analysis, limitations, ongoing work and conclusion.
5. Acknowledgment as applicable and references, all within the four-page WiP limit.

One setup/pipeline figure, one results figure and one compact table is a proposed layout, not a conference rule. Explain metric denominators. Do not describe sequential SEQ stories as arbitrary interleaving, fixed-rule context mapping as learned intent, or a causal filter inside centered-window inference as real-time recognition.

## Figure sources

Use `../current_impl/*.pdf` / PNG for existing static presentation figures, with scope labels intact. `../presentation_current/build_assets.py` now resolves paths relative to the repository and uses the committed threshold table. Its output figures are for slides and may need a more compact paper layout. PDF animations/video are presentation artifacts, not the paper's results figures.

## External assets

Raw CSI and full optimizer/model archives: `../handoff/ASSETS.json` and `../handoff/fetch_assets.py`. They are unnecessary for writing a factually grounded first draft from the saved results. Download only if re-evaluation needs them. Real training belongs on Kaggle, not the laptop.

## Status

No new research manuscript or additional experiment was created as part of this handoff. Guide approval of WiP eligibility, final author order, actual video/sign validation, ethics documentation, funding and any new data collection remain to confirm with the team. Do not replace missing facts with boilerplate.
