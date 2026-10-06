"""Nested-LOSO model selection for fine recognition on isolated trials (10 actions, 14 signs).

Outer fold: hold out one participant for testing.
Inner: on the two training participants, train on one and validate on the other (both ways).
The candidate with the best inner score is retrained on both and tested once on the outer
participant. Only that number is an unbiased estimate; inner scores are for selection only.

Candidates = representation x feature extractor x subject normalisation.
Subject normalisation ("subj") z-scores features with statistics of ALL windows of the same
participant (no labels; in deployment = a few minutes of unlabelled data from the new user).
"""
import sys
import itertools
import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import RidgeClassifierCV, LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from windows import load_isolated, FINE, ACTIONS, SIGNS
from features import handcrafted
from rocket import Rocket
from data import CACHE

PIDS = ["P01", "P02", "P03"]


# ------------------------------------------------------------ representations
def rep_raw(X):
    return X[:, :, ::2]


def rep_pca(X, k=8):
    out = np.empty((len(X), k, X.shape[2]), np.float32)
    for i, x in enumerate(X):
        xc = x - x.mean(1, keepdims=True)
        u, s, vt = np.linalg.svd(xc, full_matrices=False)
        sg = np.sign(u[:, :k].sum(0))                 # fix the PCA sign ambiguity
        sg[sg == 0] = 1
        out[i] = (vt[:k] * s[:k, None]) * sg[:, None]
    return out[:, :, ::2]


def rep_env(X):
    e = uniform_filter1d(X ** 2, size=20, axis=2)       # 0.2 s local energy per subcarrier
    return np.log(e + 1e-3)[:, :, ::2].astype(np.float32)


def rep_diff(X):
    return np.diff(X, axis=2)[:, :, ::2].astype(np.float32)


REPS = {"raw": rep_raw, "pca": rep_pca, "env": rep_env, "diff": rep_diff}


# ------------------------------------------------------------ feature sets (computed once, all windows)
def build_features(X, reps, seed=0):
    """Rocket kernels are fitted once on a fixed random subset of windows of all participants.
    Bias quantiles come from unlabelled windows only, so this is label-free (transductive at worst)."""
    F = {}
    H, _ = handcrafted(X)
    F["hand"] = H
    for r in reps:
        R = REPS[r](X)
        rk = Rocket(n_kernels=4000, seed=seed).fit(R)
        F[f"rocket_{r}"] = rk.transform(R)
        print("features", r, F[f"rocket_{r}"].shape, flush=True)
    return F


def subj_norm(F, pid):
    out = F.copy()
    for p in np.unique(pid):
        m = pid == p
        mu, sd = F[m].mean(0), F[m].std(0) + 1e-6
        out[m] = (F[m] - mu) / sd
    return out


CLFS = {
    "ridge": lambda: make_pipeline(StandardScaler(), RidgeClassifierCV(np.logspace(-1, 5, 13), class_weight="balanced")),
    "logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=3000, class_weight="balanced")),
    "rf": lambda: RandomForestClassifier(500, class_weight="balanced", n_jobs=-1, random_state=0),
    "et": lambda: ExtraTreesClassifier(800, class_weight="balanced", n_jobs=-1, random_state=0),
}


def candidates(F):
    for feat in F:
        for norm in ["none", "subj"]:
            clfs = ["rf", "et"] if feat == "hand" else ["ridge", "logreg"]
            for c in clfs:
                yield feat, norm, c


def score(Fn, y, tr, te, labels, clf):
    m = CLFS[clf]().fit(Fn[tr], y[tr])
    return f1_score(y[te], m.predict(Fn[te]), average="macro", labels=labels), m


def run(task, F, meta, cal_k=0):
    typ = "activity" if task == "actions10" else "sign"
    names = ACTIONS if task == "actions10" else SIGNS
    labels = [FINE.index(c) for c in names]
    pid_all = meta.pid.values
    y = meta.fine.values
    sel = (meta.type == typ).values
    rep = meta.rep.fillna(0).astype(int).values
    Fs = {k: {"none": v, "subj": subj_norm(v, pid_all)} for k, v in F.items()}
    cands = list(candidates(F))
    rows = []
    for test in PIDS:
        train_p = [p for p in PIDS if p != test]
        cal = lambda p: sel & (pid_all == p) & (rep <= cal_k) if cal_k else np.zeros(len(sel), bool)
        inner = []
        for feat, norm, clf in cands:
            Fn = Fs[feat][norm]
            sc = []
            for a, b in [(0, 1), (1, 0)]:
                tr = (sel & (pid_all == train_p[a])) | cal(train_p[b])
                te = sel & (pid_all == train_p[b]) & ~cal(train_p[b])
                sc.append(score(Fn, y, tr, te, labels, clf)[0])
            inner.append(((feat, norm, clf), np.mean(sc)))
        inner.sort(key=lambda t: -t[1])
        best, best_inner = inner[0]
        tr = (sel & np.isin(pid_all, train_p)) | cal(test)
        te = sel & (pid_all == test) & ~cal(test)
        outer = {c: score(Fs[c[0]][c[1]], y, tr, te, labels, c[2])[0] for c, _ in inner}
        rows.append({"task": task, "cal": cal_k, "test": test, "selected": "/".join(best),
                     "inner": best_inner, "outer_selected": outer[best],
                     "outer_oracle_best": max(outer.values()),
                     "oracle_cfg": "/".join(max(outer, key=outer.get))})
        print(rows[-1], flush=True)
        print("   inner top5:", [("/".join(c), round(s, 3)) for c, s in inner[:5]], flush=True)
        # keep every candidate's outer score for the record (not used for selection)
        for c, s in inner:
            rows.append({"task": task, "cal": cal_k, "test": test, "candidate": "/".join(c),
                         "inner_c": s, "outer_c": outer[c]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    X, meta = load_isolated()
    F = build_features(X, list(REPS))
    out = []
    for cal_k in [0, 1]:
        for task in ["actions10", "signs14"]:
            out.append(run(task, F, meta, cal_k))
    R = pd.concat(out)
    R.to_csv(CACHE.parent / "results_select_fine.csv", index=False)
    S = R[R.selected.notna()]
    pd.set_option("display.width", 250)
    print(S.groupby(["task", "cal"])[["inner", "outer_selected", "outer_oracle_best"]].mean().round(3))
    C = R[R.candidate.notna()].groupby(["task", "cal", "candidate"])[["inner_c", "outer_c"]].mean()
    print(C.sort_values("inner_c", ascending=False).groupby(level=[0, 1]).head(6).round(3).to_string())
