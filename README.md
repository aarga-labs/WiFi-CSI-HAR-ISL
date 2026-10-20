# FYP team consolidation

Private, evidence-backed archive of the work supplied by **Adhikkesh, Adithya Ajay, Amrith, Gowreesh and Rishiikesh**, consolidated on **20 October 2026**.

This repository includes earlier research, CASAS and SignFi experiments, ESP32 sensing and fall detection, passive/controlled USRP work, reviews and the current P1–P5 system. It preserves original source locations and existing Git histories. New import commits use the actual import date; the supported February–October development timeline is documented separately.

## Start here

1. [Consolidation and commit plan](docs/CONSOLIDATION_PLAN.md)
2. [Evidence-backed timeline](docs/TIMELINE.md)
3. [Contributions and attribution limits](docs/CONTRIBUTIONS.md)
4. [Review presentation catalogue](docs/REVIEW_CATALOGUE.md)
5. [Current full project context](current_system/Adhi_To_Amrith_Context.md)

## Repository map

| Directory | Contents |
|---|---|
| `research/` | Earlier dataset studies and literature |
| `docs/meetings/`, `docs/reviews/` | Dated meeting/supporting review material and October PDF export |
| `capture/esp32/` | ESPectre local changes/tools, standalone receiver and sender firmware |
| `experiments/casas/`, `experiments/signfi/` | Early public-benchmark implementations and notebook variants |
| `experiments/esp32_fall_detection/` | ESP32 CSI fall-detection work |
| `experiments/imu_fall_detection/` | Smartphone/wearable preprocessing, training/export scripts and ESP32 actuator |
| `experiments/passive_usrp/` | Amrith's passive-USRP source collection |
| `experiments/member_versions/` | Distinct member variants, with original internal layouts retained |
| `current_system/` | Intact current FYP source/evidence layout, including P1–P5 capture, training, results and presentation |
| `provenance/` | Full file manifest, duplicates/empty files, source roots, history, dependencies and checks |
| `tools/` | Read-only verification and checksum-verified asset download |

Preserving `current_system/` as a unit keeps its code/result references and evidence hashes valid. It is the current implementation; other directories are historical experiments with separate tasks and validation status.

## Verify after cloning

```bash
python3 tools/verify_repository.py
```

This uses Python's standard library, checks imported hashes/notebook JSON structures and recomputes current saved metrics. It does not train, infer, load models, install dependencies or operate hardware. Original-file rechecking on Adhikkesh's machine is optional: `python3 tools/verify_repository.py --check-originals`.

## Optional data, models and original history

Private release: <https://github.com/aarga-labs/FYP-Team-Consolidated/releases/tag/consolidation-2026-10-20>

```bash
python3 tools/fetch_assets.py --list
python3 tools/fetch_assets.py --asset legacy
python3 tools/fetch_assets.py --asset histories
```

Use your own GitHub CLI account with private-repository access. Downloads are verified and left unextracted in ignored `downloads/`. Legacy archive entries are namespaced by source collection; do not extract them over source or combine them with the current corpus. Original Git bundles preserve existing objects/refs rather than manufacturing old commits in the new main branch. Verify bundles with `git bundle verify FILE.bundle` before recovery into a separate directory.

Current P1–P5 raw/checkpoint ZIPs remain in the existing private FYP release; see [its asset manifest](current_system/handoff/ASSETS.json). Public benchmark data, SDKs and generated environments are not mirrored here; see [data boundaries](docs/DATA_AND_RESULTS.md) and [dependencies](docs/DEPENDENCIES.md).

Read [NOTICE.md](NOTICE.md) before redistribution. Keep research claims aligned with the current claim ledger. May/June exact milestones, original OPPORTUNITY evidence and some individual attribution remain unresolved; they are not filled with invented dates or results.
