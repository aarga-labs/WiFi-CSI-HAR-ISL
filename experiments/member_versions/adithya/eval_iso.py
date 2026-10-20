"""Isolated-trial evaluation: B0 scalar, B1 handcrafted+RF, B2 Rocket+ridge.

Splits
  LOSO   : train on the other participants (+ DAY empty), test on one.
  within : per participant, 5 folds by repetition number (held-out reps).
Also runs the leakage probes (should be near chance after static removal).
"""
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifierCV
from sklearn.metrics import f1_score, balanced_accuracy_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from windows import load_isolated, FINE, ACTIONS, SIGNS, LOOKALIKE
from features import handcrafted, motion_energy
from rocket import Rocket
from data import CACHE

PIDS = ["P01", "P02", "P03"]


def tasks(meta):
    iso = meta.part.isin(["actions", "signs_standing", "signs_seated", "baseline", "empty"])
    return {
        "state3": (iso, meta.state.values),
        "actions10": (meta.type == "activity", meta.fine.values),
        "signs14": (meta.type == "sign", meta.fine.values),
        "fine24": (meta.type.isin(["activity", "sign"]), meta.fine.values),
    }


def make_models():
    return {
        "B0_scalar": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
        "B1_feat_RF": lambda: RandomForestClassifier(500, class_weight="balanced", n_jobs=-1, random_state=0),
        "B2_rocket": lambda: make_pipeline(StandardScaler(), RidgeClassifierCV(np.logspace(-1, 4, 12), class_weight="balanced")),
    }


def folds(meta, mask, scheme):
    """Yields (name, train_idx, test_idx)."""
    idx = np.where(mask)[0]
    if scheme == "loso":
        for p in PIDS:
            te = idx[meta.pid.values[idx] == p]
            tr = idx[meta.pid.values[idx] != p]
            if len(te):
                yield p, tr, te
    else:  # within-subject, held-out repetitions
        rep = meta.rep.fillna(meta.trial).fillna(pd.Series(np.arange(len(meta)))).astype(int).values
        for p in PIDS:
            ip = idx[meta.pid.values[idx] == p]
            for k in range(5):
                te = ip[(rep[ip] - 1) % 5 == k]
                tr = ip[(rep[ip] - 1) % 5 != k]
                yield f"{p}/f{k}", tr, te


def run(X, meta, feats, scheme, task_names):
    rows, preds = [], {}
    T = tasks(meta)
    for tname in task_names:
        mask, y = T[tname]
        for mname, mk in make_models().items():
            yt_all, yp_all, pid_all = [], [], []
            for fname, tr, te in folds(meta, mask, scheme):
                if mname == "B2_rocket":
                    rk = Rocket(seed=0).fit(X[tr])
                    Ftr, Fte = rk.transform(X[tr]), rk.transform(X[te])
                else:
                    F = feats["scalar"] if mname == "B0_scalar" else feats["hand"]
                    Ftr, Fte = F[tr], F[te]
                m = mk().fit(Ftr, y[tr])
                yt_all.append(y[te]); yp_all.append(m.predict(Fte)); pid_all.append(meta.pid.values[te])
            yt, yp, pid = map(np.concatenate, (yt_all, yp_all, pid_all))
            per = [f1_score(yt[pid == p], yp[pid == p], average="macro") for p in PIDS if (pid == p).any()]
            rows.append({"scheme": scheme, "task": tname, "model": mname,
                         "macroF1_mean": np.mean(per), "macroF1_std": np.std(per),
                         "bal_acc": balanced_accuracy_score(yt, yp),
                         **{f"F1_{p}": v for p, v in zip([p for p in PIDS if (pid == p).any()], per)}})
            preds[(scheme, tname, mname)] = (yt, yp, pid)
            print(rows[-1], flush=True)
    return pd.DataFrame(rows), preds


def quiet_block(X, n=100):
    """Per window: per-subcarrier std of its quietest 1 s block (a noise-floor fingerprint)."""
    T = X.shape[2] // n * n
    b = X[:, :, :T].reshape(len(X), X.shape[1], -1, n)
    e = (b ** 2).mean((1, 3))
    i = e.argmin(1)
    q = b[np.arange(len(X)), :, i]
    return np.log(q.std(2) + 1e-9)


def probes(meta, X, level):
    """Can a window's file type (actions vs signs file) be told from things that are
    NOT the motion? static level (raw log-amp mean) and the quietest-second noise
    fingerprint. 0.5 = no leak. Uses trial windows of both files."""
    m = meta.type.isin(["activity", "sign"]).values
    y = (meta.part.values[m] == "actions").astype(int)
    pid = meta.pid.values[m]
    out = {}
    for name, F in [("static_level(no HP)", level[m]), ("quietest_1s_noise(HP+floor)", quiet_block(X[m]))]:
        accs = []
        for p in PIDS:
            tr, te = pid != p, pid == p
            clf = RandomForestClassifier(300, n_jobs=-1, random_state=0).fit(F[tr], y[tr])
            accs.append(balanced_accuracy_score(y[te], clf.predict(F[te])))
        out[name] = np.round(accs, 3).tolist()
    return out


def lookalike_report(yt, yp):
    """For each confuser pair: how often the action is called its look-alike sign, and vice versa."""
    rows = []
    for a, s in LOOKALIKE.items():
        ia, is_ = FINE.index(a), FINE.index(s)
        rows.append({"action": a, "sign": s,
                     "action->sign": np.mean(yp[yt == ia] == is_) if (yt == ia).any() else np.nan,
                     "sign->action": np.mean(yp[yt == is_] == ia) if (yt == is_).any() else np.nan})
    r = pd.DataFrame(rows)
    a_idx = [FINE.index(a) for a in ACTIONS]
    s_idx = [FINE.index(s) for s in SIGNS]
    any_sign = np.isin(yp[np.isin(yt, a_idx)], s_idx).mean()
    return r, any_sign


if __name__ == "__main__":
    X, meta = load_isolated()
    level = np.load(CACHE / "iso_level.npy")
    hand, names = handcrafted(X)
    feats = {"hand": hand, "scalar": motion_energy(X)[:, None]}
    print("probe (balanced acc per held-out pid; 0.5 = no leak):", probes(meta, X, level))

    all_tasks = ["state3", "actions10", "signs14", "fine24"]
    res_l, pred_l = run(X, meta, feats, "loso", all_tasks)
    res_w, pred_w = run(X, meta, feats, "within", ["actions10", "signs14", "fine24"])
    res = pd.concat([res_l, res_w])
    res.to_csv(CACHE.parent / "results_iso_baselines.csv", index=False)
    pd.set_option("display.width", 200)
    print(res.round(3).to_string(index=False))

    for m in ["B1_feat_RF", "B2_rocket"]:
        yt, yp, _ = pred_l[("loso", "fine24", m)]
        r, any_sign = lookalike_report(yt, yp)
        print(f"\n[{m}] LOSO fine24 look-alike confusion; actions predicted as ANY sign: {any_sign:.3f}")
        print(r.round(3).to_string(index=False))
        yt, yp, _ = pred_l[("loso", "state3", m)]
        print("state3 confusion (rows true idle/activity/sign):\n", confusion_matrix(yt, yp))
