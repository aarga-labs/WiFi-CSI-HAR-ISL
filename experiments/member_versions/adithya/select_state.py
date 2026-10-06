"""Nested-LOSO selection of CNN variants (mainly for the sign detector on stories).

Each variant is trained on every single participant and on every pair (2 seeds), and
predicts the participants it did not see. Selection for outer test participant P uses only
the inner scores (train on one of the other two, score on the remaining one).

Metrics per (variant, train set, scored participant):
  story_auc   : story steps, sign vs action, mean P(sign) over the step  (selection metric)
  act_f1/sign_f1 : isolated trials, within-type fine macro-F1
"""
import itertools
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score
from dense import load_streams
from cnn import Trainer, predict_stream
from stream_eval import segment_table
from windows import ACTIONS, SIGNS
from data import CACHE

PIDS = ["P01", "P02", "P03"]
VARIANTS = {
    "raw4": dict(win_s=4.0, inrep="raw"),
    "raw4_story3": dict(win_s=4.0, inrep="raw", part_w={"scripts": 3.0}),
    "env4": dict(win_s=4.0, inrep="env"),
    "env4_story3": dict(win_s=4.0, inrep="env", part_w={"scripts": 3.0}),
    "raw3": dict(win_s=3.0, inrep="raw"),
    "raw6": dict(win_s=6.0, inrep="raw"),
}
SEEDS = [0, 1]


def metrics(D):
    seg = segment_table(D)
    st = seg[seg.part == "scripts"]
    iso = seg[seg.part != "scripts"]
    a, s = iso[iso.type == "activity"], iso[iso.type == "sign"]
    return {"story_auc": roc_auc_score(st.type == "sign", st.p_sign),
            "story_auc_seated": roc_auc_score(st[st.posture == "seated"].type == "sign", st[st.posture == "seated"].p_sign),
            "act_f1": f1_score(a.label, a.within_type_pred, average="macro", labels=ACTIONS),
            "sign_f1": f1_score(s.label, s.within_type_pred, average="macro", labels=SIGNS)}


def run_all():
    S = load_streams()
    rows, preds = [], {}
    train_sets = [(p,) for p in PIDS] + list(itertools.combinations(PIDS, 2))
    for vname, kw in VARIANTS.items():
        for ts in train_sets:
            train = [s for s in S if s["pid"] in ts or s["pid"] == "DAY"]
            nets = [Trainer(train, seed=k, **kw).fit().net for k in SEEDS]
            for p in [p for p in PIDS if p not in ts]:
                D = []
                for s in [s for s in S if s["pid"] == p]:
                    c, ps, pf = predict_stream(nets, s["x"])
                    D.append({k: s[k] for k in ("pid", "part", "file", "t", "state", "fine", "events")}
                             | {"centre": c, "ps": ps, "pf": pf})
                preds[(vname, ts, p)] = D
                rows.append({"variant": vname, "train": "+".join(ts), "n_train": len(ts), "scored": p, **metrics(D)})
                print(rows[-1], flush=True)
    pickle.dump(preds, open(CACHE / "select_state_preds.pkl", "wb"))
    return pd.DataFrame(rows)


def nested(R, metric):
    out = []
    for test in PIDS:
        others = [p for p in PIDS if p != test]
        inner = R[(R.n_train == 1) & R.train.isin(others) & R.scored.isin(others)]
        inner_score = inner.groupby("variant")[metric].mean()
        best = inner_score.idxmax()
        outer = R[(R.n_train == 2) & (R.scored == test)].set_index("variant")
        out.append({"test": test, "metric": metric, "selected": best, "inner": inner_score[best],
                    "outer_selected": outer.loc[best, metric], "outer_raw4": outer.loc["raw4", metric],
                    "outer_oracle": outer[metric].max(), "oracle_variant": outer[metric].idxmax()})
    return pd.DataFrame(out)


if __name__ == "__main__":
    R = run_all()
    R.to_csv(CACHE.parent / "results_select_state.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.groupby(["n_train", "variant"])[["story_auc", "story_auc_seated", "act_f1", "sign_f1"]].mean().round(3).to_string())
    for m in ["story_auc", "act_f1", "sign_f1"]:
        N = nested(R, m)
        print(f"\nnested selection on {m}:")
        print(N.round(3).to_string(index=False))
        print("  mean outer (selected):", round(N.outer_selected.mean(), 3), " baseline raw4:", round(N.outer_raw4.mean(), 3))
