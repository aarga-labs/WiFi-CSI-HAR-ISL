# Current presentation evidence and builders

The maroon Beamer source is `../main.tex`. Current graphs and animation inputs are under `../current_impl/`. Read `OVERLEAF_README.md` for upload and viewer instructions. The eleven-slide animated preview contains only the updated implementation portion, not the complete older presentation.

`build_assets.py` reads the retained saved predictions and committed `../paper/evidence/threshold_comparison_same_detection_rules.csv`; it does not train. Its checkout paths are portable. `update_deck.py` rebuilds from an older backup and can remove later animations; do not run it blindly. `add_video_animations.py` uses a saved pre-animation backup and has similar assumptions.

Count/sample/result CSVs are now versioned. Historical `verification.json` and ten-slide previews describe the pre-animation state; use `animated_verification.json` and `animated_frame_manifest.json` for the later 43-frame/eleven-current-slide version. Rendered contact sheets, extracted individual animation JPEGs and local diagnostic full-deck builds are rebuildable and ignored. Original input clips, frame PDFs and checked previews are retained.

The deck's "Interleaved Stories" wording is imprecise: the collection protocols use scripted SEQ stories. The paper must describe the actual protocol. Small differences between rounded slide training time and the exact run completion JSON should be resolved in favour of the measured metadata.
