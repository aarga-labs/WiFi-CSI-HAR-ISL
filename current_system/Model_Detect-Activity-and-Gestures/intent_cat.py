"""Intent-category accuracy (I1 device / I2 need / I3 alert / I4 interaction) for sign segments,
from the final-system predictions (cache/final_cal<k>_<pid>.pkl).

Two decoders from the sign head:
  argmax_sign : category of the most likely sign
  sum_prob    : sum sign probabilities per category, take the most likely category
Chance (uniform over 4) = 0.25; majority class (I3, 4 of 14 signs) = 0.29.
"""
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, balanced_accuracy_score
from stream_eval import segment_table, DEFAULT
from windows import SIGNS
from data import CACHE

PIDS = ["P01", "P02", "P03"]
CATS = ["I1", "I2", "I3", "I4"]
CAT_OF = np.array([DEFAULT[s][0] for s in SIGNS])


def run(cal_k):
    rows = []
    for pid in PIDS:
        f = CACHE / f"final_cal{cal_k}_{pid}.pkl"
        if not f.exists():
            continue
        seg = segment_table(pickle.load(open(f, "rb")))
        seg = seg[seg.type == "sign"]
        for r in seg.itertuples():
            p = r.pf_sign
            by_cat = {c: p[CAT_OF == c].sum() for c in CATS}
            rows.append({"pid": pid, "src": "story" if r.part == "scripts" else "isolated",
                         "posture": r.posture, "true": DEFAULT[r.label][0],
                         "argmax_sign": CAT_OF[p.argmax()], "sum_prob": max(by_cat, key=by_cat.get)})
    d = pd.DataFrame(rows)
    out = []
    for (src, pid), g in d.groupby(["src", "pid"]):
        for dec in ["argmax_sign", "sum_prob"]:
            out.append({"cal": cal_k, "src": src, "pid": pid, "decoder": dec, "acc": (g[dec] == g.true).mean(),
                        "bal_acc": balanced_accuracy_score(g.true, g[dec]),
                        "macroF1": f1_score(g.true, g[dec], average="macro", labels=CATS)})
    return pd.DataFrame(out)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    R = pd.concat([run(int(k)) for k in (sys.argv[1:] or ["0", "1"])])
    R.to_csv(CACHE.parent / "results_intent_category.csv", index=False)
    print(R.groupby(["cal", "src", "decoder"])[["acc", "bal_acc", "macroF1"]].mean().round(3).to_string())
