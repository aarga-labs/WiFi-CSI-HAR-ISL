"""E5: train on isolated trials of the other participants, run a sliding window over
the held-out participant's story recording, compare with the keypress step labels.

Stories put signs and actions in the SAME file, so this is the test that cannot be
passed by telling recording files apart.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifierCV
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from data import kept_takes, load_csi, load_labels
from preprocess import preprocess, FS
from windows import load_isolated, WIN, FINE, SIGNS, ACTIONS
from features import handcrafted
from rocket import Rocket

HOP = int(0.5 * FS)
PIDS = ["P01", "P02", "P03"]


def story_windows(pid):
    take = kept_takes().query("pid == @pid and part == 'scripts'").iloc[0]
    t, amp = load_csi(take.csi_file)
    p = preprocess(t, amp)
    lab = load_labels(take.label_file)
    steps = lab[lab.type.isin(["activity", "sign"])]
    starts = np.arange(0, len(p["t"]) - WIN, HOP)
    X = np.stack([p["x"][s:s + WIN].T for s in starts]).astype(np.float32)
    rows = []
    for s in starts:
        a, b = p["t"][s], p["t"][s + WIN - 1]
        ov = (np.minimum(steps.t_end_us, b) - np.maximum(steps.t_start_us, a)).clip(lower=0)
        # label = step overlapping the window most; needs >= 2 s overlap to count
        if ov.max() >= 2e6:
            st = steps.loc[ov.idxmax()]
            rows.append({"t0": a, "label": st.label, "type": st.type, "script": st.script_id,
                         "run": st.run, "context": st.context, "step": st.step})
        else:
            rows.append({"t0": a, "label": None, "type": None})
    return X, pd.DataFrame(rows), steps


def fit_models(X, meta):
    m = meta.part.isin(["actions", "signs_standing", "signs_seated", "baseline", "empty"]).values
    rk = Rocket(seed=0).fit(X[m])
    Fr = rk.transform(X[m])
    state = make_pipeline(StandardScaler(), RidgeClassifierCV(np.logspace(-1, 4, 12), class_weight="balanced")).fit(Fr, meta.state.values[m])
    H, _ = handcrafted(X[m])
    rf = RandomForestClassifier(500, class_weight="balanced", n_jobs=-1, random_state=0).fit(H, meta.state.values[m])
    fm = (meta.fine.values >= 0) & m
    fine = make_pipeline(StandardScaler(), RidgeClassifierCV(np.logspace(-1, 4, 12), class_weight="balanced")).fit(rk.transform(X[fm]), meta.fine.values[fm])
    return rk, state, rf, fine


def evaluate(pid, X, meta):
    tr = (meta.pid != pid).values
    rk, state, rf, fine = fit_models(X[tr], meta[tr].reset_index(drop=True))
    Xs, ws, steps = story_windows(pid)
    Fr = rk.transform(Xs)
    dec = state.decision_function(Fr)                     # [n, 3] idle / routine / sign
    H, _ = handcrafted(Xs)
    p_rf = rf.predict_proba(H)
    ws["pred_rocket"] = dec.argmax(1)
    ws["sign_score_rocket"] = dec[:, 2] - np.maximum(dec[:, 0], dec[:, 1])
    ws["pred_rf"] = p_rf.argmax(1)
    ws["sign_score_rf"] = p_rf[:, 2]
    ws["fine_pred"] = [FINE[i] for i in fine.predict(Fr)]
    ws["pid"] = pid
    return ws


def summarise(ws):
    L = ws[ws.type.notna()].copy()
    y = (L.type == "sign").astype(int).values
    out = {"pid": ws.pid.iloc[0], "n_win": len(L), "sign_frac": y.mean()}
    for m in ["rocket", "rf"]:
        out[f"AUC_sign_{m}"] = roc_auc_score(y, L[f"sign_score_{m}"])
        pred_sign = (L[f"pred_{m}"] == 2).astype(int).values
        out[f"F1_sign_{m}"] = f1_score(y, pred_sign)
        out[f"act->sign_{m}"] = pred_sign[y == 0].mean()     # window-level false-command proxy
        out[f"sign_recall_{m}"] = pred_sign[y == 1].mean()
    # fine label accuracy on story windows (fine head ignores state)
    out["fine_acc_signs"] = (L.fine_pred[L.type == "sign"] == L.label[L.type == "sign"]).mean()
    out["fine_acc_actions"] = (L.fine_pred[L.type == "activity"] == L.label[L.type == "activity"]).mean()
    return out


if __name__ == "__main__":
    X, meta = load_isolated()
    allw, rows = [], []
    for pid in PIDS:
        ws = evaluate(pid, X, meta)
        allw.append(ws)
        rows.append(summarise(ws))
        print(rows[-1], flush=True)
    res = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(res.round(3).to_string(index=False))
    W = pd.concat(allw)
    W.to_csv("cache/story_windows_pred.csv", index=False)
    L = W[W.type.notna()]
    for m in ["rocket", "rf"]:
        print(f"\n{m}: story windows, rows = true activity/sign, cols = pred idle/routine/sign")
        print(pd.crosstab(L.type, L[f"pred_{m}"]))
    print("\nper-label sign-prediction rate (rocket):")
    print(L.groupby("label").apply(lambda d: (d.pred_rocket == 2).mean(), include_groups=False).round(2).sort_values().to_string())
