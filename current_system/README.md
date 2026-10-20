# FYP: Wi-Fi CSI activity and sign-gesture recognition

Amrita Vishwa Vidyapeetham, B.Tech CSE final-year project. Team: Adhikkesh S K, Adithya Ajay, Amrith B, Gowreesh B, Rishiikesh S K. Guide: Ms. Nalinadevi K.

## Start here — Amrith / Claude handoff

**Read [Adhi_To_Amrith_Context.md](Adhi_To_Amrith_Context.md) first.** It is the integrated current context as of 19 October 2026, including the actual P1–P5 collection, retained Kaggle model, metrics, limitations, historical corrections and paper plan. `CLAUDE.md` points Claude Code to that handoff.

The guide's research-paper draft is due **25 October 2026**. The recommended near-term target is **IEEE PerCom 2027 WiP**, subject to guide acceptance of a WiP/workshop-proceedings publication and travel/budget. No paper has been submitted or accepted by a conference.

```bash
python3 paper/tools/verify_evidence.py
```

This verifies committed evidence and recomputes results using Python's standard library. It performs no model fitting or training and does not need raw CSI downloads.

| Path | Purpose |
|---|---|
| `paper/` | Paper workspace, curated evidence, claim ledger, venue rules and read-only verification |
| `handoff/` | Dataset/archive manifests, optional private release downloads and source provenance |
| `Kaggle_P1_P5/balanced_results_audit_20261017/` | **Retained completed benchmark**, all-five inference model and audited outputs |
| `Kaggle_P1_P5/balanced_2h/` | Executed balanced Kaggle notebook and source |
| `Kaggle_P1_P5/robust_2h/` | Newer proposed notebook; no verified execution/results supplied |
| `Model_Detect-Activity-and-Gestures/` | Earlier P1–P3 implementation/results, imported as normal files |
| `capture_snapshot/wifi_csi_capture/` | Actual capture source snapshot including P4/P5 extensions; provenance in `handoff/` |
| `pilot_tools/` | Earlier outer-repository recording-tool mirror |
| `Research_Paper.pdf` | Guide-accepted two-page abstract/introduction; old claims need correction, preserve original |
| `main.tex`, `current_impl/`, `presentation_current/` | Current Beamer presentation, figures, media, builders and previews |
| `Full_Context_7_Oct_26.md` | Detailed historical October 7 handoff; current status supersedes it |
| `Papers/`, `Latex/`, `ImagePi/`, `Reports/`, `Review/`, `others/` | Reference papers, older experiments and review artifacts |
| `SEM7_Rubrics_Instructions/` | Course rubrics supplied by the user |

## Current evidence

Five participants; 12 action and 14 sign labels. The retained collection has **2,050,030 raw CSI rows** in 25 selected recordings including empty-room QC; model recordings contain **2,010,899 rows** in 22 takes. Labels, rest/ready, trials and packet rows are different units.

Retained run: `FYP_BALANCED_2H_20261017_015419`. Mean held-out participant macro-F1: **50.2% isolated actions / 33.2% isolated signs**. Automatic stories: 121/208 signs detected, 39/208 correctly named. Current results do not establish reliable real-time home control. The exact metrics and scope are documented in the handoff and claim ledger.

## Historical data restriction

Do **not** use the old `DATA_COMBINED` / "Dataset 2" P2–P5 or its scores: the October handoff records fabricated timestamp-shifted copies of P1. The newer real Phase-1 collection is separate. Older proposals, 96% binary scores and macro-F1 0.71 are not current paper evidence.

## Storage and reproducibility

Normal Git includes sources, result/annotation CSVs, saved held-out probability arrays, plots, metadata and two small retained inference checkpoints. Rebuildable caches, optimizer/duplicate checkpoint archives and large raw data stay outside normal Git; the verified dataset/full-run bundles are distributed through the **private repository's handoff release**. See [handoff/README.md](handoff/README.md). Private chat dumps, virtual environments, discarded/fabricated datasets and local Git databases remain excluded. No raw source data was deleted.

The working `wifi_csi_capture/` and `usrp-projects/` repositories remain separate locally. The capture snapshot is available to a fresh clone without those nested checkouts. Some historical scripts contain Adhikkesh-specific absolute paths; use the portable paper verification/asset downloader or adapt paths before running them.
