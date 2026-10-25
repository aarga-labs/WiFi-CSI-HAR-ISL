# Data, results and access boundaries

## What this source checkout includes

The retained implementation is the completed BALANCED P01–P05 run. Code, aggregate class/fold metrics, analytical figures, training histories and model metadata describe its results. Known-boundary classification, mean participant macro-F1, pooled class recall and automatic story detection are distinct evaluation measures.

## Private material

Raw CSI examples, original participant annotations, event-level outputs, probability arrays, recording/session audits, participant video, animated presentation bundles, archive handoffs and internal context documents are excluded from the current tracked tree. Dataset and participant-media access links are not distributed. Local working copies remain on the owner's machine under ignore rules.

Aggregate checks run with `python3 tools/verify_repository.py`. Authorized local verification against retained private annotations/predictions uses `python3 tools/verify_repository.py --private-evidence`. A fresh source clone cannot independently reconstruct event-level scores without those private inputs.

An ordinary removal commit does not erase historical blobs. Keep this repository private until a separate history/privacy review and any necessary history cleanup have been completed. Ignore rules prevent future tracking; they do not hide earlier commits.

## Earlier experiments

Earlier ESP32, passive USRP, public SignFi/CASAS and IMU experiments remain distinct from the current CSI-only benchmark. Their inputs, splits and performance must not be combined with the five-person collection. Upstream datasets and code retain their own licences.

Models and legacy experiments are archived source/resources, not proof of validated real-world safety, linguistic performance or sensor fusion. No training, inference or hardware operation is needed for this privacy cleanup.
