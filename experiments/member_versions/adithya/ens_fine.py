"""Nested check: does fusing CNN and ExtraTrees (handcrafted + per-participant normalisation)
improve fine recognition of isolated trials?

CNN predictions come from select_state.py (trained on single participants and pairs).
ExtraTrees is trained on exactly the same participants. Fusion = mean of class probabilities.
"""
import pickle
import itertools
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import f1_score
from windows import load_isolated, ACTIONS, SIGNS, FINE
from features import handcrafted
from select_fine import subj_norm
from stream_eval import segment_table
from data import CACHE

PIDS = ["P01", "P02", "P03"]
CNN_VARIANT = {"activity": "raw6", "sign": "raw4"}


def main():
    preds = pickle.load(open(CACHE / "select_state_preds.pkl", "rb"))
    X, meta = load_isolated()
    H, _ = handcrafted(X)
    Hs = subj_norm(H, meta.pid.values)
    rows = []
    for typ, names, key in [("activity", ACTIONS, "pf_act"), ("sign", SIGNS, "pf_sign")]:
        for ts in [(p,) for p in PIDS] + list(itertools.combinations(PIDS, 2)):
            tr = (meta.type == typ).values & meta.pid.isin(ts).values
            et = ExtraTreesClassifier(800, class_weight="balanced", n_jobs=-1, random_state=0).fit(Hs[tr], meta.label.values[tr])
            order = [list(et.classes_).index(c) for c in names]
            for p in [p for p in PIDS if p not in ts]:
                seg = segment_table(preds[(CNN_VARIANT[typ], ts, p)])
                seg = seg[(seg.part != "scripts") & (seg.type == typ)]
                te = (meta.type == typ).values & (meta.pid == p).values
                pe = et.predict_proba(Hs[te])[:, order]
                pe = pd.DataFrame({"file": meta.file.values[te], "rep": meta.rep.values[te].astype(int),
                                   "label": meta.label.values[te], "p_et": list(pe)})
                m = seg.merge(pe, on=["file", "rep", "label"])
                P_cnn, P_et = np.stack(m[key]), np.stack(m.p_et)
                y = m.label.values
                res = {}
                for name, P in [("cnn", P_cnn), ("et", P_et), ("fused", (P_cnn + P_et) / 2)]:
                    res[name] = f1_score(y, np.array(names)[P.argmax(1)], average="macro", labels=names)
                rows.append({"type": typ, "train": "+".join(ts), "n_train": len(ts), "scored": p, "n": len(m), **res})
                print(rows[-1], flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(CACHE.parent / "results_ens_fine.csv", index=False)
    print(R.groupby(["type", "n_train"])[["cnn", "et", "fused"]].mean().round(3))
    # nested choice among cnn / et / fused
    for typ in ["activity", "sign"]:
        sel = []
        for test in PIDS:
            others = [q for q in PIDS if q != test]
            inner = R[(R.type == typ) & (R.n_train == 1) & R.train.isin(others) & R.scored.isin(others)][["cnn", "et", "fused"]].mean()
            outer = R[(R.type == typ) & (R.n_train == 2) & (R.scored == test)].iloc[0]
            sel.append((test, inner.idxmax(), outer[inner.idxmax()], outer.cnn, outer.et, outer.fused))
        S = pd.DataFrame(sel, columns=["test", "selected", "outer_selected", "cnn", "et", "fused"])
        print(f"\n{typ}: nested"); print(S.round(3).to_string(index=False))
        print("  mean:", S[["outer_selected", "cnn", "et", "fused"]].mean().round(3).to_dict())


if __name__ == "__main__":
    main()
