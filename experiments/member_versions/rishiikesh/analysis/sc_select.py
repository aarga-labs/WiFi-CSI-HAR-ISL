#!/usr/bin/env python3
"""Stage 2: score every subcarrier, rank per activity, and select a robust set.

Two different questions are answered with two different metrics, because they
behave very differently:

  1. "Which subcarriers separate activity X here?"  -> one-vs-rest separability
     (max over the 7 window features of 2|AUC-0.5|), computed per subject.
     This is reliable *within* a capture (split-half rho ~ 0.7-0.8) but does
     NOT transfer between subjects or rooms -- see the reliability block.

  2. "Which subcarriers actually respond to motion?" -> motion-SNR profile
     (band 0.5-25 Hz over the 30-38 Hz noise band), z-scored inside each capture
     so only the *shape* across frequency survives. This DOES transfer
     (rho 0.8-0.96 across subjects and across rooms) and is what the combined
     recommendation is built on.

Output: analysis/sc_scores.json
"""

import json
import os

import numpy as np
from scipy import stats
from sklearn.ensemble import RandomForestClassifier

OUT = "/home/rishiikesh/usrp-projects/analysis"
ACTS = ["walk", "mixed", "stand", "sit"]
ACTION = {"walk", "mixed"}
NSC = 52
SUBJECTS = ["amrith", "rishiikesh", "gowreesh"]
SUB_ENV = {"amrith": "A", "rishiikesh": "A", "gowreesh": "B"}
RNG = np.random.default_rng(0)

z = np.load(os.path.join(OUT, "sc_features.npz"), allow_pickle=True)
X = z["X"]                       # (nwin, nfeat, NSC)
FEATS = list(z["feats"])
act, sub, env, fidx = z["activity"], z["subject"], z["env"], z["file_idx"]
IM = FEATS.index("msnr")


def auc(pos, neg):
    """Mann-Whitney AUC, vectorised over the trailing axes."""
    n1, n2 = len(pos), len(neg)
    r = np.apply_along_axis(stats.rankdata, 0, np.concatenate([pos, neg], 0))
    return (r[:n1].sum(0) - n1 * (n1 + 1) / 2) / (n1 * n2)


def sep_scores(mask):
    """-> dict activity -> (NSC,) separability, and the winning feature name."""
    out, win = {}, {}
    for a in ACTS:
        pos, neg = X[mask & (act == a)], X[mask & (act != a)]
        s = 2 * np.abs(auc(pos, neg) - 0.5)          # (nfeat, NSC)
        out[a] = s.max(0)
        win[a] = [FEATS[i] for i in s.argmax(0)]
    return out, win


# ------------------------------------------------- 1. per-activity separability
sc_sub, winner = {}, {}
for s in SUBJECTS:
    sc_sub[s], winner[s] = sep_scores(sub == s)

scE = {
    "A": {a: np.mean([sc_sub["amrith"][a], sc_sub["rishiikesh"][a]], 0) for a in ACTS},
    "B": {a: sc_sub["gowreesh"][a] for a in ACTS},
}
sc_robust = {a: np.minimum(scE["A"][a], scE["B"][a]) for a in ACTS}
sc_mean = {a: 0.5 * (scE["A"][a] + scE["B"][a]) for a in ACTS}

# ------------------------------------------------------- 2. motion-SNR profile
# z-score inside each capture -> only the shape across frequency survives
msnr_cap, cap_key = [], []
for f in np.unique(fidx):
    m = fidx == f
    v = np.median(X[m][:, IM, :], 0)
    msnr_cap.append((v - v.mean()) / (v.std() + 1e-9))
    cap_key.append((sub[m][0], act[m][0], env[m][0]))
msnr_cap = np.stack(msnr_cap)

prof_act = {a: msnr_cap[[i for i, k in enumerate(cap_key) if k[1] == a]].mean(0)
            for a in ACTS}
prof_env = {e: msnr_cap[[i for i, k in enumerate(cap_key) if k[2] == e]].mean(0)
            for e in "AB"}
act_idx = [i for i, k in enumerate(cap_key) if k[1] in ACTION]
prof_motion = msnr_cap[act_idx].mean(0)          # the transferable profile
prof_motion_worst = msnr_cap[act_idx].min(0)     # worst-case over the 6 captures

# ------------------------------------------------------------- 3. reliability
def split_half(mask, n=10):
    rs = []
    for _ in range(n):
        p = RNG.random(len(mask)) < 0.5
        s1, _ = sep_scores(mask & p)
        s2, _ = sep_scores(mask & ~p)
        rs.append([stats.spearmanr(s1[a], s2[a]).statistic for a in ACTS])
    return np.array(rs)


rel = {}
sh = np.stack([split_half(sub == s) for s in SUBJECTS])       # (3, n, 4)
rel["split_half"] = {a: float(sh[:, :, i].mean()) for i, a in enumerate(ACTS)}
rel["split_half_sd"] = {a: float(sh[:, :, i].std()) for i, a in enumerate(ACTS)}
rel["cross_subject_sameroom"] = {
    a: float(stats.spearmanr(sc_sub["amrith"][a], sc_sub["rishiikesh"][a]).statistic)
    for a in ACTS}
rel["cross_env"] = {a: float(stats.spearmanr(scE["A"][a], scE["B"][a]).statistic)
                    for a in ACTS}

# same three tiers, for the motion-SNR profile instead
msnr_rel = {}
for a in ACTS:
    idx = {s: [i for i, k in enumerate(cap_key) if k[1] == a and k[0] == s]
           for s in SUBJECTS}
    msnr_rel[a] = {
        "cross_subject_sameroom": float(stats.spearmanr(
            msnr_cap[idx["amrith"][0]], msnr_cap[idx["rishiikesh"][0]]).statistic),
        "cross_env": float(np.mean([
            stats.spearmanr(msnr_cap[idx[s][0]],
                            msnr_cap[idx["gowreesh"][0]]).statistic
            for s in ["amrith", "rishiikesh"]]))}

# ---------------------------------------------- 4. redundancy / coherence band
sig = X[:, FEATS.index("sigma"), :].copy()
for f in np.unique(fidx):
    m = fidx == f
    sig[m] = (sig[m] - sig[m].mean(0)) / (sig[m].std(0) + 1e-9)
R = np.corrcoef(sig.T)
np.fill_diagonal(R, 1.0)

lag_corr = [float(np.mean([R[i, i + d] for i in range(NSC - d)]))
            for d in range(NSC)]
below = [d for d, v in enumerate(lag_corr) if v < 0.5]
coh_lag = below[0] if below else NSC
n_indep = NSC / coh_lag if coh_lag else NSC


def mrmr(relevance, R, k, lam=0.3):
    """Greedy max-relevance / min-redundancy; redundancy = worst pair so far."""
    r = (relevance - relevance.min()) / (np.ptp(relevance) + 1e-12)
    sel = [int(np.argmax(r))]
    while len(sel) < k:
        cand = [i for i in range(len(r)) if i not in sel]
        red = np.array([np.abs(R[i, sel]).max() for i in cand])
        sel.append(int(cand[int(np.argmax(r[cand] - lam * red))]))
    return sel


# combined recommendation: relevance = worst-case motion-SNR over the 6 action
# captures (so it must hold in BOTH rooms), spread by the redundancy penalty
ORDER = mrmr(prof_motion_worst, R, 20)
ORDER_ACT = {a: mrmr(sc_robust[a], R, 10) for a in ACTS}

# ------------------------------------------------------------- 5. validation
y = act
Xf = X.transpose(0, 2, 1)                       # (nwin, NSC, nfeat)


def loso_acc(sc_idx, seed=0):
    F = Xf[:, sc_idx, :].reshape(len(y), -1)
    accs = {}
    for s in SUBJECTS:
        te = sub == s
        clf = RandomForestClassifier(n_estimators=200, min_samples_leaf=2,
                                     random_state=seed, n_jobs=-1)
        clf.fit(F[~te], y[~te])
        accs[s] = float((clf.predict(F[te]) == y[te]).mean())
    accs["mean"] = float(np.mean([accs[s] for s in SUBJECTS]))
    return accs


def within_acc(sc_idx, seed=0, nfold=5):
    """Time-blocked CV inside each capture -- the stationary-channel case."""
    F = Xf[:, sc_idx, :].reshape(len(y), -1)
    accs = []
    for s in SUBJECTS:
        ms = sub == s
        blk = np.zeros(len(y), int)
        for f in np.unique(fidx[ms]):
            i = np.where(fidx == f)[0]
            blk[i] = (np.arange(len(i)) * nfold) // len(i)
        for k in range(nfold):
            te = ms & (blk == k)
            tr = ms & (blk != k)
            clf = RandomForestClassifier(n_estimators=200, min_samples_leaf=2,
                                         random_state=seed, n_jobs=-1)
            clf.fit(F[tr], y[tr])
            accs.append((clf.predict(F[te]) == y[te]).mean())
    return float(np.mean(accs))


KS = [1, 2, 4, 6, 8, 10, 12, 16, 20, 26, 52]
rank_msnr = list(np.argsort(-prof_motion_worst))
curve = {"k": KS, "selected": [], "within": [], "random_mean": [],
         "random_lo": [], "random_hi": [], "worst": [], "per_subject": {}}

for k in KS:
    selk = list(range(52)) if k == 52 else ORDER[:k]
    a = loso_acc(selk)
    curve["selected"].append(a["mean"])
    curve["within"].append(within_acc(selk))
    curve["per_subject"][k] = {s: a[s] for s in SUBJECTS}
    if k < 52:
        curve["worst"].append(loso_acc(list(rank_msnr[-k:]))["mean"])
        d = [loso_acc(list(RNG.choice(52, k, replace=False)), seed=i)["mean"]
             for i in range(10)]
        curve["random_mean"].append(float(np.mean(d)))
        curve["random_lo"].append(float(np.percentile(d, 10)))
        curve["random_hi"].append(float(np.percentile(d, 90)))
    else:
        for key in ("worst", "random_mean", "random_lo", "random_hi"):
            curve[key].append(a["mean"])
    print(f"k={k:3d} LOSO={a['mean']:.3f} within={curve['within'][-1]:.3f} "
          f"(am {a['amrith']:.2f} ri {a['rishiikesh']:.2f} go {a['gowreesh']:.2f}) "
          f"rand={curve['random_mean'][-1]:.3f} worst={curve['worst'][-1]:.3f}")

# selection-strategy comparison: does forcing spectral spread help? (no)
def spaced(rel, k, gap):
    sel = []
    for i in np.argsort(-rel):
        if all(abs(i - j) >= gap for j in sel):
            sel.append(int(i))
        if len(sel) == k:
            break
    return sel


strategies = {f"mrmr_lam{l}": (lambda k, l=l: mrmr(prof_motion_worst, R, k, l))
              for l in (0.0, 0.3, 0.6, 1.0, 1.5)}
strategies.update({f"spacing{g}": (lambda k, g=g: spaced(prof_motion_worst, k, g))
                   for g in (2, 3, 4, 5)})
strategies["uniform"] = lambda k: list(np.linspace(6, 45, k).round().astype(int))
strategy_cmp = {name: {k: loso_acc(fn(k))["mean"] for k in (6, 8, 12)}
                for name, fn in strategies.items()}

# confusion for the recommended set
K_REC = 12
F = Xf[:, ORDER[:K_REC], :].reshape(len(y), -1)
pred = np.empty_like(y)
for s in SUBJECTS:
    te = sub == s
    clf = RandomForestClassifier(n_estimators=400, min_samples_leaf=2,
                                 random_state=0, n_jobs=-1)
    clf.fit(F[~te], y[~te])
    pred[te] = clf.predict(F[te])
conf = [[int(((y == t) & (pred == p)).sum()) for p in ACTS] for t in ACTS]

# action vs no-action collapse (the binary task the pilot was built for)
bin_true = np.isin(y, list(ACTION))
bin_pred = np.isin(pred, list(ACTION))
bin_acc = float((bin_true == bin_pred).mean())

out = dict(
    acts=ACTS, feats=FEATS, nsc=NSC, subjects=SUBJECTS, sub_env=SUB_ENV,
    score_env={e: {a: scE[e][a].tolist() for a in ACTS} for e in "AB"},
    score_subject={s: {a: sc_sub[s][a].tolist() for a in ACTS} for s in SUBJECTS},
    score_robust={a: sc_robust[a].tolist() for a in ACTS},
    score_mean={a: sc_mean[a].tolist() for a in ACTS},
    winner_feature={s: {a: winner[s][a] for a in ACTS} for s in SUBJECTS},
    top_per_activity={a: [int(i) for i in np.argsort(-sc_robust[a])[:10]] for a in ACTS},
    top_per_activity_env={e: {a: [int(i) for i in np.argsort(-scE[e][a])[:10]]
                              for a in ACTS} for e in "AB"},
    mrmr_per_activity={a: [int(i) for i in ORDER_ACT[a]] for a in ACTS},
    msnr_cap=msnr_cap.tolist(),
    cap_key=[list(k) for k in cap_key],
    prof_act={a: prof_act[a].tolist() for a in ACTS},
    prof_env={e: prof_env[e].tolist() for e in "AB"},
    prof_motion=prof_motion.tolist(),
    prof_motion_worst=prof_motion_worst.tolist(),
    level=z["cap_level"].mean(0).tolist(),
    level_per_cap=z["cap_level"].tolist(),
    reliability=rel, msnr_reliability=msnr_rel,
    corr=R.tolist(), lag_corr=lag_corr, coh_lag=int(coh_lag),
    n_independent=float(n_indep),
    mrmr_order=[int(i) for i in ORDER],
    rank_msnr=[int(i) for i in rank_msnr],
    curve=curve, confusion=conf, k_recommended=K_REC, binary_acc=bin_acc,
    strategy_cmp=strategy_cmp,
)
with open(os.path.join(OUT, "sc_scores.json"), "w") as fh:
    json.dump(out, fh, indent=1)

print("\n--- reliability of the per-activity separability ranking (Spearman) ---")
for a in ACTS:
    print(f"  {a:6s} split-half {rel['split_half'][a]:+.2f}   "
          f"cross-subject(same room) {rel['cross_subject_sameroom'][a]:+.2f}   "
          f"cross-env {rel['cross_env'][a]:+.2f}")
print("--- same, for the motion-SNR profile ---")
for a in ACTS:
    print(f"  {a:6s} cross-subject(same room) "
          f"{msnr_rel[a]['cross_subject_sameroom']:+.2f}   "
          f"cross-env {msnr_rel[a]['cross_env']:+.2f}")
print(f"\ncoherence lag (corr<0.5): {coh_lag} subcarriers "
      f"-> ~{n_indep:.1f} independent looks across the band")
print("combined mRMR order:", ORDER)
print(f"binary action/no-action LOSO accuracy @k={K_REC}: {bin_acc:.3f}")
print("saved analysis/sc_scores.json")
