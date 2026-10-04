"""Final system, evaluated with LOSO (zero-shot and 1-rep calibration).

Components (each chosen by nested LOSO, see select_state.py / ens_fine.py / select_adapt.py)
  detector + action head : CNN, 6 s window ("raw6"), 3 seeds
  action identity        : mean of CNN raw6 probabilities and ExtraTrees (handcrafted,
                           per-participant feature normalisation) on isolated trials
  sign identity          : CNN, 4 s window ("raw4"), 3 seeds
  threshold tau          : chosen on inner folds (train on one training participant, score the
                           other) from select_state predictions, maximising event F1
  intent                 : intent_of(sign, context), context from predicted actions (stream_eval)
"""
import sys
import pickle
import itertools
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import f1_score, roc_auc_score
from dense import load_streams
from cnn import Trainer, predict_stream, adapt_bn
from run_cnn import split_calibration
from select_state import VARIANTS
from select_fine import subj_norm
from stream_eval import segment_table, stream_metrics, A_IDX, S_IDX, TAUS
from windows import load_isolated, ACTIONS, SIGNS
from features import handcrafted
from data import CACHE

PIDS = ["P01", "P02", "P03"]
SEEDS = [0, 1, 2]
ADABN = {"det": "none", "sign": "none"}       # set from select_adapt.py results
TAU_GRID = np.round(np.arange(0.3, 0.95, 0.05), 2)


def inner_tau(test):
    """tau maximising event F1 on inner folds, from select_state predictions (raw6, 1-person training)."""
    preds = pickle.load(open(CACHE / "select_state_preds.pkl", "rb"))
    others = [p for p in PIDS if p != test]
    best, best_f = None, -1
    for tau in TAU_GRID:
        f = np.mean([stream_metrics(preds[("raw6", (a,), b)], tau)[0]["event_F1"]
                     for a, b in itertools.permutations(others, 2)])
        if f > best_f:
            best, best_f = tau, f
    return best, best_f


def predict(nets, streams, mode):
    if mode != "none":
        nets = [adapt_bn(n, [s["x"] for s in streams], mode) for n in nets]
    return [predict_stream(nets, s["x"]) for s in streams]


def run(cal_k):
    S = load_streams()
    X, meta = load_isolated()
    Hs = subj_norm(handcrafted(X)[0], meta.pid.values)
    rep = meta.rep.fillna(0).astype(int).values
    out, segs = [], []
    for test in PIDS:
        train = [s for s in S if s["pid"] != test]
        tests = [s for s in S if s["pid"] == test]
        if cal_k:
            pairs = [split_calibration(s, cal_k) for s in tests]
            train += [a for a, _ in pairs if a is not None]
            tests = [b for _, b in pairs]
        det = [Trainer(train, seed=k, **VARIANTS["raw6"]).fit().net for k in SEEDS]
        sgn = [Trainer(train, seed=k, **VARIANTS["raw4"]).fit().net for k in SEEDS]
        P6 = predict(det, tests, ADABN["det"])
        P4 = predict(sgn, tests, ADABN["sign"])
        D = []
        for s, (c6, ps6, pf6), (c4, ps4, pf4) in zip(tests, P6, P4):
            # align the 4 s sign-head frames to the 6 s detector frames (nearest centre)
            j = np.clip(np.searchsorted(c4, c6), 0, len(c4) - 1)
            pf = np.zeros_like(pf6)
            pf[:, A_IDX] = pf6[:, A_IDX] / pf6[:, A_IDX].sum(1, keepdims=True)
            pf[:, S_IDX] = pf4[j][:, S_IDX] / pf4[j][:, S_IDX].sum(1, keepdims=True)
            D.append({k: s[k] for k in ("pid", "part", "file", "t", "state", "fine", "events")}
                     | {"centre": c6, "ps": ps6, "pf": pf})
        # ExtraTrees for action identity on isolated trials (+ calibration reps of the test participant)
        is_act = (meta.type == "activity").values
        cal = is_act & (meta.pid == test).values & (rep <= cal_k) if cal_k else np.zeros(len(meta), bool)
        tr = (is_act & (meta.pid != test).values) | cal
        et = ExtraTreesClassifier(800, class_weight="balanced", n_jobs=-1, random_state=0).fit(Hs[tr], meta.label.values[tr])
        te = is_act & (meta.pid == test).values & ~cal
        order = [list(et.classes_).index(c) for c in ACTIONS]
        pe = pd.DataFrame({"file": meta.file.values[te], "rep": rep[te].astype(float), "label": meta.label.values[te],
                           "p_et": list(et.predict_proba(Hs[te])[:, order])})
        seg = segment_table(D)
        seg["rep"] = seg.rep.astype(float)
        seg = seg.merge(pe, on=["file", "rep", "label"], how="left")
        fused = [(a + b) / 2 if isinstance(b, np.ndarray) else a for a, b in zip(seg.pf_act, seg.p_et)]
        seg["act_pred_fused"] = [ACTIONS[int(np.argmax(f))] for f in fused]
        segs.append(seg)
        tau, f_in = inner_tau(test)
        for t in sorted(set(TAUS) | {tau}):
            r, it = stream_metrics(D, t)
            out.append({"cal": cal_k, "test": test, "tau_inner": tau, **r,
                        "intent_e2e": it.e2e.mean(), "intent_cat": it.e2e_cat.mean(),
                        "story_detected": it.detected.mean()})
        pickle.dump(D, open(CACHE / f"final_cal{cal_k}_{test}.pkl", "wb"))
        print(f"cal{cal_k} {test} done, inner tau={tau}", flush=True)
    return pd.concat(segs), pd.DataFrame(out)


def summarise(seg, st, cal_k):
    iso = seg[seg.part != "scripts"]
    a, s = iso[iso.type == "activity"], iso[iso.type == "sign"]
    story = seg[seg.part == "scripts"]
    res = {"cal": cal_k}
    per = lambda d, col, labels: np.mean([f1_score(g.label, g[col], average="macro", labels=labels) for _, g in d.groupby("pid")])
    res["action_F1_cnn"] = per(a, "within_type_pred", ACTIONS)
    res["action_F1_fused"] = per(a, "act_pred_fused", ACTIONS)
    res["sign_F1"] = per(s, "within_type_pred", SIGNS)
    res["story_AUC_sign_vs_action"] = np.mean([roc_auc_score(g.type == "sign", g.p_sign) for _, g in story.groupby("pid")])
    res["story_sign_F1"] = per(story[story.type == "sign"], "within_type_pred", SIGNS)
    op = st[st.tau == st.tau_inner]
    for k in ["tau", "sign_recall", "precision", "event_F1", "sign_id_acc|det", "FC/h_routine", "intent_e2e", "intent_cat", "story_detected"]:
        res[f"op_{k}"] = op[k].mean()
    return res


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    summary = []
    for cal_k in [int(a) for a in sys.argv[1:]] or [0, 1]:
        seg, st = run(cal_k)
        seg.drop(columns=["pf_act", "pf_sign", "p_et"]).to_csv(CACHE.parent / f"results_final_segments_cal{cal_k}.csv", index=False)
        st.to_csv(CACHE.parent / f"results_final_stream_cal{cal_k}.csv", index=False)
        summary.append(summarise(seg, st, cal_k))
        print(st.groupby("tau")[["sign_recall", "precision", "event_F1", "sign_id_acc|det", "FC/h_routine"]].mean().round(3).to_string())
    S = pd.DataFrame(summary).T
    S.to_csv(CACHE.parent / "results_final_summary.csv")
    print(S.round(3).to_string())
