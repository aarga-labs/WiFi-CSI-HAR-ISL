# Adhi → Amrith research-paper handoff (19 October 2026)

Start with `Adhi_To_Amrith_Context.md` on `main`, then `paper/README.md`, the claim ledger and the read-only evidence verifier. The guide's draft is due 25 October; PerCom 2027 WiP is the recommended, not yet guide-confirmed, target.

This private release supplies the large verified real Phase-1 dataset, the retained BALANCED full checkpoint/result archive, the earlier FAST full archive and a compact all-five inference bundle. `handoff/ASSETS.json` on main contains expected sizes and SHA256 hashes and `handoff/fetch_assets.py` downloads/verifies them using the collaborator's own GitHub authentication.

A normal pull contains all paper evidence, source, annotations, saved probability arrays, plots and two small retained inference checkpoints. Raw CSI/full optimizer archives are optional downloads. No training ran during handoff preparation. The retained all-five refit has no independent test score; current continuous recognition remains weak. Do not use fabricated DATA_COMBINED or old pilot scores in the new paper.

The repository/release remain private. Full phone videos, private chat exports, virtual environments, rebuildable caches and unrelated old backups are not publication assets. Both full-run ZIPs contain a `results/` root: extract them into separate directories, never over one another.
