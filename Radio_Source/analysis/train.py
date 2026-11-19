#!/usr/bin/env python3
"""
Train and honestly evaluate Activity vs Gesture classification from WiFi CSI.

    python3 train.py --channel 1
    python3 train.py --channel 1 --model cnn          # needs torch
    python3 train.py --channel 1 --train-room A --test-room B

What this script refuses to do
------------------------------
It never splits windows at random. Windows overlap by 50%, so neighbouring
windows from one 10-second recording are near-duplicates; a random split puts
near-copies in both train and test and reports accuracy in the high nineties
that measures memorisation. Every split here is made on whole instances or
whole subjects.

What it reports, and why each one is there
------------------------------------------
  majority baseline   what you get by always guessing the larger class
  LOSO                train on N-1 subjects, test on the held-out one. This is
                      the headline number: it is the only one that answers
                      "does this work on a person it has never seen?"
  by-instance CV      train/test split on instances within the same subjects.
                      Always higher than LOSO. Quote it as an upper bound, not
                      as the result.
  shuffle control     the same pipeline with labels randomly reassigned per
                      instance. Must collapse to chance. If it does not, there
                      is leakage somewhere and every other number is void.
  per-class recall    which fine classes are actually being confused
  standstill vs gest. the pair that matters: both have a still torso and differ
                      only in hand motion, so this is where you find out
                      whether the system sees hands or just "big vs small
                      motion".
  instance-level      windows majority-voted per recording, which is how the
                      system would actually be used.
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import load_windows, summarise, CLASS_GROUP, DEFAULT_ROOT  # noqa: E402
from features import batch_features, rank_subcarriers                    # noqa: E402


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------

def confusion(y_true, y_pred, labels):
    idx = {l: i for i, l in enumerate(labels)}
    m = np.zeros((len(labels), len(labels)), dtype=int)
    for t, p in zip(y_true, y_pred):
        m[idx[t], idx[p]] += 1
    return m


def prf(y_true, y_pred, labels):
    """Per-label precision/recall/F1 plus macro-F1 and balanced accuracy."""
    cm = confusion(y_true, y_pred, labels)
    out, f1s, recs = {}, [], []
    for i, l in enumerate(labels):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        out[l] = {"precision": p, "recall": r, "f1": f, "support": int(cm[i].sum())}
        f1s.append(f); recs.append(r)
    return {
        "per_label": out,
        "macro_f1": float(np.mean(f1s)),
        "balanced_accuracy": float(np.mean(recs)),
        "accuracy": float(np.trace(cm) / max(cm.sum(), 1)),
        "confusion": cm.tolist(),
        "labels": list(labels),
    }


def majority_vote(preds):
    return Counter(preds).most_common(1)[0][0]


# --------------------------------------------------------------------------
# models
# --------------------------------------------------------------------------

def make_rf(seed=0):
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(
        n_estimators=300, min_samples_leaf=2, n_jobs=-1,
        class_weight="balanced", random_state=seed)


class RFModel:
    """Statistical + spectral features -> RandomForest."""
    name = "randomforest"

    def __init__(self, seed=0):
        self.seed = seed
        self.clf = None

    def fit(self, X, y):
        self.clf = make_rf(self.seed)
        self.clf.fit(batch_features(X), y)
        return self

    def predict(self, X):
        return self.clf.predict(batch_features(X))


class CNNModel:
    """Recurrence plots over the top-K subcarriers -> small 2D CNN.

    Mirrors the existing pipeline's representation (RP -> 2D CNN -> per
    subcarrier prediction -> majority vote) in a form that trains on CPU in
    minutes. Only used with --model cnn, and only if torch is installed.
    """
    name = "rp_cnn"

    def __init__(self, seed=0, top_k=6, epochs=8, rp_size=48):
        self.seed, self.top_k, self.epochs, self.rp_size = seed, top_k, epochs, rp_size
        self.subcarriers = None
        self.net = None
        self.labels = None

    def _images(self, X):
        from features import recurrence_plot
        n = len(X)
        out = np.empty((n, len(self.subcarriers), self.rp_size, self.rp_size),
                       dtype=np.float32)
        for i, w in enumerate(X):
            for j, sc in enumerate(self.subcarriers):
                out[i, j] = recurrence_plot(w[:, sc], size=self.rp_size)
        return out

    def fit(self, X, y):
        import torch, torch.nn as nn
        torch.manual_seed(self.seed)

        self.labels = sorted(set(y))
        self.subcarriers, _ = rank_subcarriers(X, y, top_k=self.top_k)

        imgs = self._images(X)
        yi = np.array([self.labels.index(v) for v in y])

        self.net = nn.Sequential(
            nn.Conv2d(len(self.subcarriers), 32, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(),
            nn.Dropout(0.3), nn.Linear(64, len(self.labels)),
        )
        opt = torch.optim.Adam(self.net.parameters(), lr=1e-3)
        lossf = nn.CrossEntropyLoss()

        xb_all = torch.from_numpy(imgs)
        yb_all = torch.from_numpy(yi).long()

        self.net.train()
        for _ in range(self.epochs):
            perm = torch.randperm(len(xb_all))
            for i in range(0, len(perm), 32):
                b = perm[i:i + 32]
                opt.zero_grad()
                loss = lossf(self.net(xb_all[b]), yb_all[b])
                loss.backward()
                opt.step()
        return self

    def predict(self, X):
        import torch
        self.net.eval()
        with torch.no_grad():
            logits = self.net(torch.from_numpy(self._images(X)))
            idx = logits.argmax(1).numpy()
        return np.array([self.labels[i] for i in idx])


def build_model(kind, seed):
    if kind == "rf":
        return RFModel(seed)
    if kind == "cnn":
        try:
            import torch  # noqa: F401
        except ImportError:
            raise SystemExit(
                "--model cnn needs torch:  pip install torch\n"
                "The randomforest baseline (--model rf) needs only scikit-learn "
                "and is a legitimate result on its own.")
        return CNNModel(seed)
    raise SystemExit(f"unknown model '{kind}'")


# --------------------------------------------------------------------------
# evaluation protocols
# --------------------------------------------------------------------------

def run_folds(d, folds, model_kind, seed, quiet=False):
    """Run a list of (name, train_mask, test_mask) and pool the predictions."""
    labels = sorted(set(d.y))
    all_true, all_pred, all_group, all_class = [], [], [], []
    per_fold = []

    for name, tr, te in folds:
        if tr.sum() == 0 or te.sum() == 0:
            continue
        if len(set(d.y[tr])) < 2:
            if not quiet:
                print(f"    fold {name}: skipped (training side has one class)")
            continue

        model = build_model(model_kind, seed).fit(d.X[tr], d.y[tr])
        pred = model.predict(d.X[te])

        acc = float((pred == d.y[te]).mean())
        per_fold.append({"fold": name, "accuracy": acc, "n_test": int(te.sum())})
        if not quiet:
            print(f"    fold {name:<12s} n={int(te.sum()):5d}  accuracy={acc:.3f}")

        all_true.append(d.y[te]); all_pred.append(pred)
        all_group.append(d.groups[te]); all_class.append(d.classes[te])

    if not per_fold:
        return None

    y_true = np.concatenate(all_true)
    y_pred = np.concatenate(all_pred)
    groups = np.concatenate(all_group)
    classes = np.concatenate(all_class)

    res = prf(y_true, y_pred, labels)
    res["per_fold"] = per_fold
    res["fold_mean"] = float(np.mean([f["accuracy"] for f in per_fold]))
    res["fold_std"] = float(np.std([f["accuracy"] for f in per_fold]))

    # Per fine class: how often was this class's window given the right
    # coarse label? Shows which classes carry the errors.
    per_class = {}
    for c in sorted(set(classes)):
        m = classes == c
        per_class[c] = {"n": int(m.sum()),
                        "recall": float((y_pred[m] == y_true[m]).mean())}
    res["per_fine_class"] = per_class

    # Instance-level: majority vote of every window in one recording.
    by_inst = defaultdict(list)
    truth = {}
    for g, t, p in zip(groups, y_true, y_pred):
        by_inst[g].append(p)
        truth[g] = t
    inst_true = [truth[g] for g in by_inst]
    inst_pred = [majority_vote(v) for g, v in by_inst.items()]
    res["instance_level"] = prf(np.array(inst_true), np.array(inst_pred), labels)
    res["instance_level"]["n_instances"] = len(by_inst)

    return res


def loso_folds(d):
    subs = sorted(set(d.subjects))
    return [(s, d.subjects != s, d.subjects == s) for s in subs]


def instance_folds(d, k=5, seed=0):
    """GroupKFold on instances: same subjects both sides, unseen recordings."""
    insts = np.array(sorted(set(d.groups)))
    rng = np.random.default_rng(seed)
    rng.shuffle(insts)
    chunks = np.array_split(insts, k)
    folds = []
    for i, ch in enumerate(chunks):
        te = np.isin(d.groups, ch)
        folds.append((f"k{i+1}", ~te, te))
    return folds


def shuffle_labels_by_instance(d, seed=0):
    """Reassign labels randomly per INSTANCE, preserving group structure."""
    rng = np.random.default_rng(seed)
    insts = sorted(set(d.groups))
    pool = []
    for g in insts:
        pool.append(d.y[d.groups == g][0])
    pool = np.array(pool)
    rng.shuffle(pool)
    mapping = dict(zip(insts, pool))
    return np.array([mapping[g] for g in d.groups])


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def print_confusion(res, title):
    labels = res["labels"]
    cm = np.array(res["confusion"])
    w = max(len(l) for l in labels) + 2
    print(f"\n  {title}")
    print("    " + " " * w + "".join(f"{l:>12s}" for l in labels) + "   <- predicted")
    for i, l in enumerate(labels):
        print("    " + f"{l:<{w}s}" + "".join(f"{v:12d}" for v in cm[i]))
    print(f"    accuracy {res['accuracy']:.3f}   macro-F1 {res['macro_f1']:.3f}   "
          f"balanced {res['balanced_accuracy']:.3f}")


def standstill_vs_gesture(d, model_kind, seed):
    """
    The contrast that decides whether hand motion is really being detected.

    Restricting to `standstill` and the gesture classes removes every cue that
    comes from whole-body locomotion. If accuracy here is near chance while the
    full binary task looks excellent, the classifier is separating "large
    motion" from "small motion" and would fail the moment a real user stood
    still without signing.
    """
    keep = (d.classes == "standstill") | (np.array([CLASS_GROUP.get(c) == "gesture"
                                                    for c in d.classes]))
    if keep.sum() == 0 or len(set(d.y[keep])) < 2:
        return None

    sub = d._replace(X=d.X[keep], y=d.y[keep], groups=d.groups[keep],
                     subjects=d.subjects[keep], classes=d.classes[keep],
                     reps=d.reps[keep])
    if len(set(sub.subjects)) < 2:
        return None
    return run_folds(sub, loso_folds(sub), model_kind, seed, quiet=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", type=int, default=1)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--model", choices=["rf", "cnn"], default="rf")
    ap.add_argument("--include-empty", action="store_true",
                    help="make 'empty' a third class instead of dropping it")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--skip-shuffle", action="store_true")
    ap.add_argument("--out", default=None, help="write results JSON here")
    args = ap.parse_args()

    d = load_windows(channel=args.channel, root=args.root,
                     include_empty=args.include_empty)
    summarise(d)

    results = {"channel": args.channel, "model": args.model,
               "n_windows": int(len(d.X)), "n_instances": d.meta["n_instances"],
               "subjects": sorted(set(map(str, d.subjects)))}

    counts = Counter(d.y)
    majority = max(counts.values()) / sum(counts.values())
    results["majority_baseline"] = majority

    print(f"\n  majority-class baseline: {majority:.3f}  "
          f"(always guessing '{counts.most_common(1)[0][0]}')")

    # ---- primary: leave one subject out
    print("\n" + "=" * 66)
    print(f" LEAVE-ONE-SUBJECT-OUT  (model={args.model})   <-- headline result")
    print("=" * 66)
    if len(set(d.subjects)) < 2:
        print("  Only one subject in this dataset — LOSO is impossible.")
        print("  Record a second subject before claiming this generalises.")
        results["loso"] = None
    else:
        loso = run_folds(d, loso_folds(d), args.model, args.seed)
        results["loso"] = loso
        if loso:
            print(f"\n    mean across subjects: {loso['fold_mean']:.3f} "
                  f"+/- {loso['fold_std']:.3f}")
            print_confusion(loso, "window-level confusion (pooled over folds)")
            print_confusion(loso["instance_level"],
                            f"instance-level after majority vote "
                            f"({loso['instance_level']['n_instances']} recordings)")
            print("\n  per fine class (recall of the correct coarse label):")
            for c, v in sorted(loso["per_fine_class"].items(),
                               key=lambda kv: kv[1]["recall"]):
                bar = "#" * int(v["recall"] * 30)
                print(f"    {c:<12s} n={v['n']:5d}  {v['recall']:.3f}  {bar}")

    # ---- upper bound: unseen recordings, same people
    print("\n" + "=" * 66)
    print(" BY-INSTANCE CROSS-VALIDATION   (upper bound, same subjects)")
    print("=" * 66)
    inst = run_folds(d, instance_folds(d, seed=args.seed), args.model, args.seed)
    results["by_instance"] = inst
    if inst:
        print(f"\n    mean: {inst['fold_mean']:.3f} +/- {inst['fold_std']:.3f}")

    # ---- the contrast that proves hands are visible
    print("\n" + "=" * 66)
    print(" STANDSTILL vs GESTURE   (still torso both sides — hands only)")
    print("=" * 66)
    svg = standstill_vs_gesture(d, args.model, args.seed)
    results["standstill_vs_gesture"] = svg
    if svg is None:
        print("  Not evaluable (needs 'standstill' plus gestures, 2+ subjects).")
    else:
        print(f"    LOSO accuracy: {svg['fold_mean']:.3f} +/- {svg['fold_std']:.3f}")
        if svg["fold_mean"] < 0.65:
            print("    ! Near chance. The full binary score is then mostly")
            print("      'moving vs not moving', NOT hand-gesture detection.")
            print("      Say so explicitly rather than leaving it to be found.")
        else:
            print("    Hand motion is separable from a still body. This is the")
            print("    number that makes the gesture claim defensible.")

    # ---- leakage control
    if not args.skip_shuffle:
        print("\n" + "=" * 66)
        print(" SHUFFLED-LABEL CONTROL   (must collapse to chance)")
        print("=" * 66)
        d_sh = d._replace(y=shuffle_labels_by_instance(d, args.seed))
        if len(set(d_sh.subjects)) >= 2:
            sh = run_folds(d_sh, loso_folds(d_sh), args.model, args.seed, quiet=True)
            results["shuffle_control"] = sh
            if sh:
                print(f"    accuracy with random labels: {sh['fold_mean']:.3f}")
                if sh["fold_mean"] > majority + 0.10:
                    print("    !!! ABOVE CHANCE — there is leakage. Do not trust")
                    print("    !!! any number above until this is explained.")
                else:
                    print("    At chance, as required. No leakage detected.")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2, default=float)
        print(f"\n  results written to {args.out}")


if __name__ == "__main__":
    main()
