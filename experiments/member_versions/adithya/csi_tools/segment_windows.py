#!/usr/bin/env python3
"""Cut a CSI capture into fixed windows of amplitude (52 x rate*window).

Two modes:

1) Labeled reps (discrete actions - squat/bend/drink/nod), using the labels
   CSV written by session_logger.py. Each rep becomes one window centered
   inside its [t_start, t_end] interval:

    python3 segment_windows.py capture.csv --labels S01_squat_amrith_labels.csv

2) Auto-chunk (continuous classes - walk/noaction/empty): the whole capture
   is split into consecutive windows:

    python3 segment_windows.py capture.csv --action walk --subject amrith

Each window is resampled onto a uniform time grid (linear interpolation per
subcarrier) and saved as float32 .npy of shape (n_subcarriers, n_samples)
under <out-dir>/<action>/.
"""

import argparse
import os

import numpy as np
import pandas as pd


def load_capture(path):
    df = pd.read_csv(path)
    if "Timestamp_us" not in df.columns:
        raise SystemExit("Capture has no Timestamp_us column - recapture with "
                         "the updated extract_csi block.")
    n_sc = sum(1 for c in df.columns if c.endswith("_Re"))
    t = df["Timestamp_us"].to_numpy(np.int64)
    re = df[[f"SC{i}_Re" for i in range(n_sc)]].to_numpy(float)
    im = df[[f"SC{i}_Im" for i in range(n_sc)]].to_numpy(float)
    amp = np.hypot(re, im)
    order = np.argsort(t)
    return t[order], amp[order]


def extract_window(t, amp, t0_us, t1_us, n_samples, min_fill):
    """Resample amplitude rows within [t0,t1] onto a uniform n_samples grid."""
    mask = (t >= t0_us) & (t <= t1_us)
    n_have = int(mask.sum())
    expected = n_samples  # grid density == target rate
    if n_have < max(4, int(min_fill * expected)):
        return None, n_have
    ts, as_ = t[mask], amp[mask]
    grid = np.linspace(t0_us, t1_us, n_samples)
    out = np.empty((amp.shape[1], n_samples), np.float32)
    for k in range(amp.shape[1]):
        out[k] = np.interp(grid, ts, as_[:, k])
    return out, n_have


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("capture")
    p.add_argument("--labels", help="labels CSV from session_logger.py")
    p.add_argument("--action", help="class label (auto-chunk mode)")
    p.add_argument("--subject", help="subject (auto-chunk mode)")
    p.add_argument("--rate", type=float, default=100.0, help="target Hz (default 100)")
    p.add_argument("--window", type=float, default=2.0, help="window seconds (default 2)")
    p.add_argument("--step", type=float, default=None,
                   help="auto-chunk step seconds (default = window, no overlap)")
    p.add_argument("--min-fill", type=float, default=0.5,
                   help="min fraction of expected packets in a window (default 0.5)")
    p.add_argument("--out-dir", default="windows")
    args = p.parse_args()

    if not args.labels and not (args.action and args.subject):
        p.error("need --labels, or --action + --subject for auto-chunk mode")

    t, amp = load_capture(args.capture)
    n_samples = int(round(args.rate * args.window))
    stem = os.path.splitext(os.path.basename(args.capture))[0]
    win_us = int(args.window * 1e6)

    saved = skipped = 0

    def save(action, subject, rep, w):
        d = os.path.join(args.out_dir, action)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "%s_%s_%s_rep%03d.npy" % (stem, action, subject, rep))
        np.save(path, w)

    if args.labels:
        labels = pd.read_csv(args.labels)
        for _, row in labels.iterrows():
            mid = (int(row.t_start_us) + int(row.t_end_us)) // 2
            w, n_have = extract_window(t, amp, mid - win_us // 2, mid + win_us // 2,
                                       n_samples, args.min_fill)
            if w is None:
                print("SKIP rep %d: only %d packets in window" % (row.rep, n_have))
                skipped += 1
                continue
            save(row.action, row.subject, int(row.rep), w)
            saved += 1
    else:
        step_us = int((args.step or args.window) * 1e6)
        rep = 1
        t0 = int(t[0])
        while t0 + win_us <= t[-1]:
            w, n_have = extract_window(t, amp, t0, t0 + win_us, n_samples, args.min_fill)
            if w is None:
                skipped += 1
            else:
                save(args.action, args.subject, rep, w)
                saved += 1
                rep += 1
            t0 += step_us

    print("Saved %d windows (%d skipped) -> %s/" % (saved, skipped, args.out_dir))
    if skipped > saved:
        print("WARNING: more skipped than saved - capture rate is too low or "
              "gaps too large; check with check_capture.py")


if __name__ == "__main__":
    main()
