#!/usr/bin/env python3
"""Sanity-check a CSI capture CSV produced by extract_csi.

Reports rows/s (the make-or-break number), timestamp gaps, NaN/zero/constant
columns, and saves an amplitude-vs-time plot so you can eyeball whether
motion is visible in the CSI at all (the "wiggle test").

Usage:
    python3 check_capture.py ~/usrp-projects/data/csi_20260716_101502.csv
    python3 check_capture.py capture.csv --min-rate 50 --subcarriers 0,13,26,39,51
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", help="CSI CSV from extract_csi")
    p.add_argument("--min-rate", type=float, default=50.0,
                   help="rows/s gate (default 50; target is ~100)")
    p.add_argument("--subcarriers", default="0,13,26,39,51",
                   help="comma-separated subcarrier indices to plot")
    p.add_argument("--plot-out", default=None,
                   help="output PNG (default: <capture>_check.png)")
    args = p.parse_args()

    df = pd.read_csv(args.capture)
    n = len(df)
    print("File: %s" % args.capture)
    print("Rows: %d" % n)
    if n == 0:
        print("FAIL: empty capture - no packets matched the TA/RA filter.")
        print("      Watch the flowgraph console for 'seen TA=.. RA=..' lines")
        print("      and fix CSI_TA / CSI_RA.")
        sys.exit(1)

    sc_cols = [c for c in df.columns if c.startswith("SC")]
    n_sc = len(sc_cols) // 2
    re = df[[f"SC{i}_Re" for i in range(n_sc)]].to_numpy(float)
    im = df[[f"SC{i}_Im" for i in range(n_sc)]].to_numpy(float)
    amp = np.hypot(re, im)  # rows x n_sc

    # ---------- data validity ----------
    n_nan = int(np.isnan(amp).sum())
    zero_rows = int((amp.sum(axis=1) == 0).sum())
    const_sc = [i for i in range(n_sc) if np.ptp(amp[:, i]) == 0]
    print("Subcarriers: %d" % n_sc)
    print("NaN values: %d%s" % (n_nan, "  <-- BAD" if n_nan else ""))
    print("All-zero rows: %d%s" % (zero_rows, "  <-- BAD" if zero_rows else ""))
    print("Constant subcarriers: %s" % (const_sc if const_sc else "none"))

    # ---------- rate ----------
    have_ts = "Timestamp_us" in df.columns
    ok_rate = None
    if not have_ts:
        print("No Timestamp_us column (old CSV format) - cannot measure rate.")
        print("Rebuild gr-ieee802-11 with the updated extract_csi block.")
    elif n >= 2:
        t = df["Timestamp_us"].to_numpy(np.int64)
        dur = (t[-1] - t[0]) / 1e6
        mean_rate = (n - 1) / dur if dur > 0 else float("inf")
        gaps_ms = np.diff(t) / 1e3

        sec = ((t - t[0]) // 1_000_000).astype(int)
        per_sec = np.bincount(sec)

        print("Duration: %.1f s" % dur)
        print("Mean rate: %.1f rows/s" % mean_rate)
        print("Per-second rate: min %d / median %d / max %d"
              % (per_sec.min(), int(np.median(per_sec)), per_sec.max()))
        print("Largest gap: %.0f ms" % gaps_ms.max())
        ok_rate = mean_rate >= args.min_rate
        print("RATE GATE (>= %.0f rows/s): %s"
              % (args.min_rate, "PASS" if ok_rate else "FAIL"))
        if not ok_rate:
            print("  -> is `sudo ping -i 0.01 <gateway>` running on the MacBook?")
            print("  -> try CSI_TA=any CSI_RA=any to see if the filter is the problem")
            print("  -> if still low, frames are likely 802.11n (HT) which")
            print("     gr-ieee802-11 cannot decode; see plan Part C.4")

    # ---------- plot ----------
    scs = [int(s) for s in args.subcarriers.split(",") if s.strip() != ""]
    scs = [s for s in scs if 0 <= s < n_sc]
    x = (df["Timestamp_us"].to_numpy(np.int64) - df["Timestamp_us"].iloc[0]) / 1e6 \
        if have_ts else np.arange(n)
    xlabel = "time (s)" if have_ts else "packet index"

    n_panels = 2 if have_ts else 1
    fig, axes = plt.subplots(n_panels, 1, figsize=(12, 4 * n_panels), squeeze=False)

    ax = axes[0][0]
    for s in scs:
        ax.plot(x, amp[:, s], lw=0.8, label="SC%d" % s)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("|H| amplitude")
    ax.set_title("CSI amplitude - a person moving must be visible by eye here")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)

    if have_ts:
        ax2 = axes[1][0]
        ax2.bar(np.arange(len(per_sec)), per_sec, width=1.0)
        ax2.axhline(args.min_rate, color="red", ls="--", label="gate %.0f/s" % args.min_rate)
        ax2.set_xlabel("second")
        ax2.set_ylabel("rows/s")
        ax2.set_title("CSI sample rate over time")
        ax2.legend()
        ax2.grid(alpha=0.3)

    out = args.plot_out or os.path.splitext(args.capture)[0] + "_check.png"
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print("Plot -> %s" % out)

    sys.exit(0 if (ok_rate is not False and not n_nan and not zero_rows) else 1)


if __name__ == "__main__":
    main()
