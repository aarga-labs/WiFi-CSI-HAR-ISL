# Private data and checkpoint delivery

The repository is private (`aarga-labs/FYP`). A normal `git pull` supplies the paper context, source, result tables, annotations, saved held-out probability arrays, figures and the retained pair of small all-five inference checkpoints. Writing the paper does not require downloading the raw recordings.

Large artifacts are attached to the private release:

**https://github.com/aarga-labs/FYP/releases/tag/handoff-2026-10-19**

`ASSETS.json` records exact bytes, SHA256, purpose and archive top-level directories. Release assets use descriptive unique filenames; the two full-run archives originally shared the filename `FYP_all_checkpoints_and_results.zip`. They were renamed for distribution without changing their contents.

Delivery verification is recorded in `handoff/DELIVERY.json`; source/evidence checks are in `handoff/VALIDATION.json`.

## Download when needed

Install/authenticate GitHub CLI with **your own account that can access the private repository**. Do not copy Adhikkesh's token or make the release public to bypass access controls.

```bash
python3 handoff/fetch_assets.py --list
python3 handoff/fetch_assets.py --asset dataset
python3 handoff/fetch_assets.py --asset balanced_checkpoints
```

`--all` downloads all four assets, about 1.26 GB total. Downloads go into ignored `handoff/assets/`. Existing valid files are reused; changed/incomplete files are rejected instead of silently overwritten. The helper verifies hashes and does not extract or execute code.

| Asset key | Contents / restoration |
|---|---|
| `dataset` | Verified selected real CSI archive. Extraction to a new directory creates `phase1/`, containing the per-file `manifest.json`, selected CSVs, labels, logs and audits. Excludes fabricated/discarded data and full videos. |
| `balanced_checkpoints` | Full retained balanced result/checkpoint archive. Extraction creates `results/`; includes optimizer/best/last states and supporting saved artifacts. Restore to a separate directory so an existing run is never overwritten. |
| `fast_checkpoints` | Full earlier FAST-run archive, also rooted at `results/`. Extract separately from the balanced archive; never overlay them. |
| `balanced_inference` | Compact retained all-five package rooted at `Balanced_All5_Model/`. Useful for portable inference; no new independent score. |

The raw dataset hash is `74259c5718d512ffa9cd3bdf63f150badcd6887e0cd2b35f780602e6e13a165c`. The archived `manifest.json` hash/fingerprint is `f01651df3c4b758f3cbec5dd742669b4f0605a9f11c24162aecd662949dede62`. These are different objects/hashes.

Do not blindly unpickle downloaded checkpoint/joblib files from untrusted sources. These particular artifacts are tied to the saved project checksums. No classifier fitting or GPU training is part of recovering them. Any new real training remains a Kaggle task explicitly requested by the team.

## Provenance

- `manifest.json`, `upload_verification.json`, `.sha256`: exact verified data packaging metadata, copied without changing its bytes. Absolute `archive` paths in historical reports are Adhikkesh-specific provenance only.
- `capture_source_provenance.json`: snapshot source URL/base commit/dirty state and hashes for actual capture code, including P4/P5 additions. The separate live capture repository was not reset, committed or pushed by this handoff.
- `friend_source_provenance.json`: original P1–P3 model repository URL/commit/status. Its working source is imported as normal outer-repository files; the local Git database is preserved under ignored `_backup_git/`.
- `../paper/evidence_manifest.json`: committed evidence/model hashes used by the portable verifier.

## What is intentionally outside normal Git

Full raw CSI and large checkpoint ZIPs (release assets); generated preprocessing caches (rebuildable); previous/last/optimizer checkpoint duplicates (in the full archives); virtual environments/build products; private chat exports; rejected fabricated data; discarded captures; older unrelated large backup ZIPs; local nested Git databases. None of those were deleted from Adhikkesh's machine.

No complete phone-video dataset is included. Three short excerpts and a setup photo are in `../current_impl/media/`. Do not infer full video annotation or language validation from their presence.

The initial release and pushed branch are verified at delivery. On later updates, compare actual remote asset metadata and local hashes again rather than assuming a stale release is current.
