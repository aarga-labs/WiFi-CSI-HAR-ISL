#!/usr/bin/env python3
"""
Load a captured CSI session into windowed arrays ready for training.

    from dataset import load_windows
    d = load_windows(channel=1)
    d.X          # (n_windows, 100, 52) float32 amplitude
    d.y          # (n_windows,) 'activity' | 'gesture'
    d.groups     # (n_windows,) instance id — NEVER split across train/test
    d.subjects   # (n_windows,) subject id — the LOSO fold key

Or as a command, to inspect a dataset before training on it:

    python3 dataset.py --channel 1 --summary

Three things this module exists to get right
--------------------------------------------

1. **Interval slicing.** capture.sh records a warm-up period before cueing the
   subject, and writes the exact GO/STOP microsecond timestamps to a .json
   sidecar. Only rows inside that interval are labelled data; everything else
   is the radio settling with nobody performing. We slice on the sidecar rather
   than guessing "drop the first second".

2. **Irregular sampling.** CSI arrives whenever a frame decodes, not on a
   clock, so windows contain varying sample counts (~130-150 at 70 Hz) while a
   CNN needs a fixed shape. Every window is resampled onto a uniform grid by
   interpolating against its real timestamps. This also makes captures at
   different achieved rates directly comparable — necessary for the per-channel
   comparison, where channel 6 may run slower than channel 1.

3. **Group leakage.** Windows overlap and neighbouring windows from one
   10-second recording are near-duplicates. Splitting them randomly puts
   near-copies on both sides and yields ~99% accuracy that measures nothing.
   Every window carries its instance id in `groups` and its subject in
   `subjects`, so the training script can split on either and never on rows.
"""

import argparse
import csv
import glob
import json
import os
from collections import Counter, namedtuple

import numpy as np


N_SUBCARRIERS = 52

# Sampling grid every window is resampled onto. Matches the existing HAR
# pipeline (RATE=50, WINDOW_SECONDS=2 -> 100 samples per window).
TARGET_RATE_HZ = 50
WINDOW_S = 2.0
WINDOW_SAMPLES = int(TARGET_RATE_HZ * WINDOW_S)  # 100
OVERLAP = 0.5

# A window must contain at least this fraction of TARGET_RATE_HZ * WINDOW_S
# real samples before it is worth interpolating. Below that we would be
# inventing most of the signal.
MIN_REAL_FRACTION = 0.6

# The coarse label each class maps to.
#
# `standstill` sits on the activity side: a person present and not
# communicating. It is also the hardest and most informative contrast against
# the gestures, because both have a stationary torso and differ only in hand
# motion — report that pair separately when evaluating.
# `empty` is a control (no person at all), excluded from the binary task by
# default; pass include_empty=True to make it a third class.
CLASS_GROUP = {
    "walk": "activity",
    "sitstand": "activity",
    "bend": "activity",
    "standstill": "activity",
    "hello": "gesture",
    "comehere": "gesture",
    "stop": "gesture",
    "thankyou": "gesture",
    "empty": "empty",
}

DEFAULT_ROOT = os.path.expanduser("~/usrp-projects/data/har")

Dataset = namedtuple(
    "Dataset", "X y groups subjects classes reps meta"
)


def _read_csv(path):
    """Return (timestamps_us, amplitude[T,52]). Uses pandas when available."""
    try:
        import pandas as pd
        try:
            df = pd.read_csv(path)
        except Exception:
            return None, None                       # empty/corrupt/not a CSV
        if "Timestamp_us" not in df.columns:
            return None, None
        re_cols = [f"SC{i}_Re" for i in range(N_SUBCARRIERS)]
        im_cols = [f"SC{i}_Im" for i in range(N_SUBCARRIERS)]
        if not set(re_cols + im_cols).issubset(df.columns):
            return None, None
        df = df.dropna(subset=["Timestamp_us"] + re_cols + im_cols)
        ts = df["Timestamp_us"].to_numpy(dtype=np.int64)
        re = df[re_cols].to_numpy(dtype=np.float32)
        im = df[im_cols].to_numpy(dtype=np.float32)
    except ImportError:
        ts_l, re_l, im_l = [], [], []
        try:
            with open(path, newline="") as f:
                r = csv.reader(f)
                hdr = next(r)                       # empty file -> StopIteration
                ti = hdr.index("Timestamp_us")      # wrong file -> ValueError
                ri = [hdr.index(f"SC{i}_Re") for i in range(N_SUBCARRIERS)]
                ii = [hdr.index(f"SC{i}_Im") for i in range(N_SUBCARRIERS)]
                need = max([ti] + ri + ii)
                for row in r:
                    if len(row) <= need:
                        continue                    # truncated row from a hard kill
                    try:
                        ts_l.append(int(row[ti]))
                        re_l.append([float(row[j]) for j in ri])
                        im_l.append([float(row[j]) for j in ii])
                    except ValueError:
                        continue                    # unparseable row, skip it
        except (StopIteration, ValueError, OSError):
            # Not a CSI capture, or unreadable. The caller records it as
            # skipped and carries on — one bad file must never stop a
            # collection run from being analysed.
            return None, None

        ts = np.asarray(ts_l, dtype=np.int64)
        re = np.asarray(re_l, dtype=np.float32)
        im = np.asarray(im_l, dtype=np.float32)

    if ts.size == 0:
        return None, None

    order = np.argsort(ts)
    ts, re, im = ts[order], re[order], im[order]
    amp = np.sqrt(re ** 2 + im ** 2).astype(np.float32)
    return ts, amp


def _slice_to_labelled_interval(path, ts, amp):
    """Trim to [go_us, stop_us] from the .json sidecar, when one exists."""
    meta_path = path[:-4] + ".json"
    if not os.path.exists(meta_path):
        return ts, amp, None

    try:
        with open(meta_path) as f:
            meta = json.load(f)
        go, stop = int(meta["go_us"]), int(meta["stop_us"])
    except (ValueError, KeyError, OSError):
        return ts, amp, None

    keep = (ts >= go) & (ts <= stop)
    return ts[keep], amp[keep], meta


def _window_instance(ts, amp):
    """Cut one instance into fixed-shape windows on a uniform time grid."""
    if ts.size < 2:
        return []

    step_us = int(WINDOW_S * (1.0 - OVERLAP) * 1_000_000)
    win_us = int(WINDOW_S * 1_000_000)
    min_real = int(MIN_REAL_FRACTION * TARGET_RATE_HZ * WINDOW_S)

    out = []
    start = ts[0]
    while start + win_us <= ts[-1]:
        end = start + win_us
        sel = (ts >= start) & (ts < end)
        n_real = int(sel.sum())

        if n_real >= min_real:
            t_real = ts[sel].astype(np.float64)
            a_real = amp[sel]
            # Uniform grid across the window; np.interp needs increasing x and
            # holds the end values flat outside the measured range, which is
            # the conservative choice at window edges.
            grid = np.linspace(start, end, WINDOW_SAMPLES, endpoint=False)
            w = np.empty((WINDOW_SAMPLES, amp.shape[1]), dtype=np.float32)
            for k in range(amp.shape[1]):
                w[:, k] = np.interp(grid, t_real, a_real[:, k])
            out.append(w)

        start += step_us

    return out


def parse_name(path):
    """<subject>_<class>_<rep>.csv -> (subject, class, rep), or None."""
    stem = os.path.basename(path)[:-4]
    parts = stem.split("_")
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]


def load_windows(channel=1, root=DEFAULT_ROOT, include_empty=False,
                 classes=None, subjects=None, verbose=True):
    """Load every instance for one channel into windowed arrays."""
    root = os.path.expanduser(root)
    pattern = os.path.join(root, f"ch{channel}", "*.csv")
    paths = sorted(glob.glob(pattern))

    if not paths:
        raise SystemExit(
            f"no captures found at {pattern}\n"
            f"Record some first: CSI_CHANNEL={channel} ./session.sh <subject>")

    X, y, groups, subjects_out, classes_out, reps_out = [], [], [], [], [], []
    skipped = []

    for p in paths:
        parsed = parse_name(p)
        if parsed is None:
            skipped.append((os.path.basename(p), "filename is not subject_class_rep"))
            continue
        subject, cls, rep = parsed

        if cls not in CLASS_GROUP:
            skipped.append((os.path.basename(p), f"unknown class '{cls}'"))
            continue
        group_label = CLASS_GROUP[cls]
        if group_label == "empty" and not include_empty:
            continue
        if classes is not None and cls not in classes:
            continue
        if subjects is not None and subject not in subjects:
            continue

        ts, amp = _read_csv(p)
        if ts is None or ts.size < 2:
            skipped.append((os.path.basename(p), "no usable rows"))
            continue

        ts, amp, _meta = _slice_to_labelled_interval(p, ts, amp)
        if ts.size < 2:
            skipped.append((os.path.basename(p), "no rows inside the GO/STOP interval"))
            continue

        windows = _window_instance(ts, amp)
        if not windows:
            skipped.append((os.path.basename(p),
                            f"no window reached {int(MIN_REAL_FRACTION*100)}% sample density"))
            continue

        instance_id = os.path.basename(p)[:-4]
        for w in windows:
            X.append(w)
            y.append(group_label)
            groups.append(instance_id)
            subjects_out.append(subject)
            classes_out.append(cls)
            reps_out.append(rep)

    if not X:
        raise SystemExit(f"every capture under {pattern} was skipped — nothing to train on.")

    d = Dataset(
        X=np.stack(X).astype(np.float32),
        y=np.asarray(y),
        groups=np.asarray(groups),
        subjects=np.asarray(subjects_out),
        classes=np.asarray(classes_out),
        reps=np.asarray(reps_out),
        meta={"channel": channel, "root": root, "skipped": skipped,
              "n_instances": len(set(groups))},
    )

    if verbose and skipped:
        print(f"  skipped {len(skipped)} file(s):")
        for name, why in skipped[:10]:
            print(f"    {name}: {why}")
        if len(skipped) > 10:
            print(f"    ... and {len(skipped)-10} more")

    return d


def summarise(d):
    """Print the report you should read before training on a dataset."""
    print()
    print("=" * 66)
    print(f" DATASET  channel {d.meta['channel']}")
    print("=" * 66)
    print(f"  windows        : {len(d.X)}")
    print(f"  instances      : {d.meta['n_instances']}")
    print(f"  window shape   : {d.X.shape[1:]}  "
          f"({WINDOW_S:g}s @ {TARGET_RATE_HZ} Hz, {int(OVERLAP*100)}% overlap)")
    print(f"  subjects       : {', '.join(sorted(set(map(str, d.subjects))))}")

    print()
    print("  binary label balance:")
    for lab, n in sorted(Counter(d.y).items()):
        print(f"    {lab:10s} {n:6d} windows  ({100*n/len(d.y):5.1f}%)")

    print()
    print("  per class (windows / instances):")
    inst_per_class = Counter()
    for cls, g in {(c, g) for c, g in zip(d.classes, d.groups)}:
        inst_per_class[cls] += 1
    for cls, n in sorted(Counter(d.classes).items()):
        print(f"    {cls:12s} {n:6d} / {inst_per_class[cls]:4d}   "
              f"-> {CLASS_GROUP.get(cls,'?')}")

    print()
    print("  per subject (windows / instances):")
    inst_per_subj = Counter()
    for s, g in {(s, g) for s, g in zip(d.subjects, d.groups)}:
        inst_per_subj[s] += 1
    for s, n in sorted(Counter(d.subjects).items()):
        print(f"    {s:12s} {n:6d} / {inst_per_subj[s]:4d}")

    # The checks worth failing loudly on.
    print()
    problems = []
    counts = Counter(d.y)
    if len(counts) < 2:
        problems.append("only one label present — nothing to classify")
    elif max(counts.values()) / max(min(counts.values()), 1) > 1.5:
        problems.append(f"label imbalance {dict(counts)} — record more of the smaller side")
    if len(set(d.subjects)) < 2:
        problems.append("only one subject — leave-one-subject-out is impossible; "
                        "results will not show generalisation")
    if d.meta["n_instances"] < 20:
        problems.append(f"only {d.meta['n_instances']} instances — too few to trust")

    if problems:
        print("  WARNINGS:")
        for p in problems:
            print(f"    ! {p}")
    else:
        print("  No structural problems found.")
    print("=" * 66)


def main():
    ap = argparse.ArgumentParser(description="Inspect a captured CSI dataset.")
    ap.add_argument("--channel", type=int, default=1)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--include-empty", action="store_true")
    ap.add_argument("--summary", action="store_true", help="(default action)")
    args = ap.parse_args()

    d = load_windows(channel=args.channel, root=args.root,
                     include_empty=args.include_empty)
    summarise(d)


if __name__ == "__main__":
    main()
