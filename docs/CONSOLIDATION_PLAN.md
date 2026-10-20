# Consolidation and commit plan

All six requested stages are carried out in this separate repository. The source FYP, SEM6 and member folders are preserved. This plan groups imports by implementation responsibility; it does not manufacture February–October Git activity.

## Stages

1. Gather all five collections, including Gowreesh; record source roots and identify gaps.
2. Inventory relevant files, exact duplicates, empty placeholders, dependencies and external data. Record source/destination hashes and any credential redaction.
3. Copy selected files into a separate staged repository; preserve the current system as a unit and keep distinct historical variants.
4. Verify imported/original hashes, inspect notebook state and syntax, recompute current results, run capture protocol tests and check archive CRC/security patterns. Do not train or operate hardware.
5. Save the exact file-level commit plan below and in provenance/commit_plan.json.
6. Execute the groups as real new commits on main, publish a private repo/release, then verify from a fresh clone. Original histories are preserved separately as original Git bundles.

## Planned import groups

| Order | Commit title | Files | Historical evidence scope |
|---:|---|---:|---|
| 1 | Document transparent consolidation, provenance and verification | 60 | Research / cross-cutting |
| 2 | Import early dataset studies and supporting literature | 11 | Before February / February–March |
| 3 | Preserve CASAS preprocessing and temporal-model experiment source | 10 | Reported by February |
| 4 | Preserve distinct SignFi benchmark notebooks and analysis | 22 | March–April discussion evidence |
| 5 | Import ESPectre local logging changes and visualisation tools | 9 | April demo recorded in meeting notes |
| 6 | Import standalone ESP32 CSI receiver and serial collection tools | 7 | Exact completion month unresolved |
| 7 | Import nonempty ESP32 CSI sender firmware | 4 | Exact completion month unresolved |
| 8 | Preserve ESP32 CSI fall-detection scripts and supplied notebook | 59 | Historical prototype; exact month unresolved |
| 9 | Import IMU fall-model preparation and ESP32 alarm actuator | 9 | Separate historical modality; exact month unresolved |
| 10 | Preserve passive-USRP activity project and attribution notices | 17 | July original history |
| 11 | Import Gowreesh distinct training and inference notebook variants | 4 | Supplied October; original run dates unresolved |
| 12 | Preserve Adithya collection notebook and pipeline variants | 103 | Mixed historical work; source provenance only |
| 13 | Preserve historical USRP receiver and multi-hop variants | 13 | August original history |
| 14 | Preserve original three-channel experiment documentation | 9 | August–September original history |
| 15 | Import pilot and subcarrier analysis source and figures | 45 | July–August analysis |
| 16 | Preserve distinct Rishiikesh review and supporting project files | 52 | Mixed historical work |
| 17 | Import current project context and historical review records | 28 | Current handoff with earlier review evidence |
| 18 | Preserve controlled two-USRP experiment snapshot | 476 | August–September development history |
| 19 | Import current capture source snapshot and recording protocol | 491 | September–October capture system |
| 20 | Preserve P1-P3 baseline source and saved result tables | 47 | October original baseline history |
| 21 | Import Kaggle training runners and notebook versions | 56 | October; run status distinguished in current context |
| 22 | Preserve earlier FAST run diagnostics and outputs | 160 | Earlier completed October run |
| 23 | Import retained BALANCED run and saved held-out evidence | 184 | Completed October P1-P5 run |
| 24 | Import threshold comparison and model-audit utilities | 2 | October evaluation |
| 25 | Import current evidence ledger, annotations and metric verifier | 65 | October audited P1-P5 evidence |
| 26 | Import current implementation presentation, figures and collection excerpts | 49 | October presentation source/export |
| 27 | Preserve original handoff manifests and private-asset recovery instructions | 13 | October handoff |
| 28 | Preserve remaining current-layout legacy experiments and references | 50 | Historical source layout preserved |

The final delivery follow-up records actual remote commit and private-release checks. See provenance/commit_execution.json for resulting commit IDs. Exact monthly completion remains unresolved for May/June and some prototypes; no empty month is padded with artificial commits.

## Deliberate exclusions and remaining evidence gaps

- SDKs, environments, build products, private chat exports, private permission documents and rejected fabricated DATA_COMBINED copies are outside the published import.
- Public benchmark datasets/rebuildable arrays remain external inputs with recorded source paths/hashes; they are not team-collected data.
- Empty files remain listed, not promoted into functioning code/data. Exact duplicates point to a canonical selected copy.
- The OPPORTUNITY result in the March review still needs its original implementation and split evidence.
- Individual authorship cannot be inferred from copied folder names, generic Ubuntu User commits or notebook execution counters.
- Legacy Python 2 utilities and one historical fall-detection script fail Python 3 parsing; these findings are preserved, not silently repaired. Hardware and legacy model performance were not revalidated.
