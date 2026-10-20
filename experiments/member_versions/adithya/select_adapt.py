"""Nested-LOSO check of AdaBN test-time adaptation (no labels from the new participant).

Same scheme as select_state.py: train on each single participant and each pair (2 seeds),
predict the unseen participants with adaptation mode none / in / all.
Usage: python select_adapt.py <variant name from select_state.VARIANTS>
"""
import sys
import itertools
import pandas as pd
from dense import load_streams
from cnn import Trainer, predict_stream, adapt_bn
from select_state import VARIANTS, SEEDS, PIDS, metrics, nested
from data import CACHE

MODES = ["none", "in", "all"]

if __name__ == "__main__":
    vname = sys.argv[1] if len(sys.argv) > 1 else "raw4"
    S = load_streams()
    rows = []
    for ts in [(p,) for p in PIDS] + list(itertools.combinations(PIDS, 2)):
        train = [s for s in S if s["pid"] in ts or s["pid"] == "DAY"]
        nets = [Trainer(train, seed=k, **VARIANTS[vname]).fit().net for k in SEEDS]
        for p in [p for p in PIDS if p not in ts]:
            test = [s for s in S if s["pid"] == p]
            for mode in MODES:
                ad = nets if mode == "none" else [adapt_bn(n, [s["x"] for s in test], mode) for n in nets]
                D = []
                for s in test:
                    c, ps, pf = predict_stream(ad, s["x"])
                    D.append({k: s[k] for k in ("pid", "part", "file", "t", "state", "fine", "events")}
                             | {"centre": c, "ps": ps, "pf": pf})
                rows.append({"variant": mode, "train": "+".join(ts), "n_train": len(ts), "scored": p, **metrics(D)})
                print(rows[-1], flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(CACHE.parent / f"results_select_adapt_{vname}.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.groupby(["n_train", "variant"])[["story_auc", "story_auc_seated", "act_f1", "sign_f1"]].mean().round(3).to_string())
    for m in ["story_auc", "act_f1", "sign_f1"]:
        R2 = R.copy()
        N = nested(R2.assign(variant=R2.variant.replace({"none": "raw4"})), m)
        print(f"\nnested on {m}:"); print(N.round(3).to_string(index=False))
