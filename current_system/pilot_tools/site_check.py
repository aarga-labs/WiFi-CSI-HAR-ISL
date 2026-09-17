#!/usr/bin/env python3
"""
site_check.py - is this place quiet enough to record in?  (20-minute test)

Measures two things at a candidate recording place:
  1. the noise floor: CSI motion energy of the EMPTY place while someone walks
     around OUTSIDE it (passers-by, trees, wind leak in through open sides)
  2. the signal: motion energy of real ISL signs recorded at the same place
and compares them.

  ./record_part.sh SITE empty                       # a teammate walks outside the open side
  ./record_part.sh P00 signs_standing --reps 3
  python3 site_check.py --empty  ~/usrp-projects/data/phase1/SITE_empty_*.csv \\
                        --signs  ~/usrp-projects/data/phase1/P00_signs_standing_*.csv \\
                        --labels ~/usrp-projects/data/phase1/labels/labels_P00_signs_*.csv

The limits used for the verdict are rules of thumb, not published thresholds.
"""
import argparse
import glob

import numpy as np
import pandas as pd

from plot_pilot import FS, load_csi, load_labels, to_grid, motion_energy

SKIP_START_S, SKIP_END_S = 15, 5      # people are still leaving / coming back


def one(pattern):
    hits = sorted(glob.glob(pattern))
    if not hits:
        raise SystemExit(f"no file matches {pattern}")
    return hits[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--empty", required=True, help="CSI csv of the empty place (glob ok, newest used)")
    ap.add_argument("--signs", help="CSI csv of a signs part at the same place")
    ap.add_argument("--labels", nargs="+", help="label csv(s) of that signs part")
    a = ap.parse_args()

    # ---- noise floor -------------------------------------------------------
    path = one(a.empty)
    t_us, amp = load_csi(path)
    dur = (t_us[-1] - t_us[0]) / 1e6
    _, g = to_grid(t_us, amp)
    e, _ = motion_energy(g)
    e = e[int(SKIP_START_S * FS):len(e) - int(SKIP_END_S * FS)]
    e = e[~np.isnan(e)]
    if len(e) < 30 * FS:
        raise SystemExit("empty recording too short (need at least ~50 s)")
    print(f"empty place : {path}")
    print(f"  {len(t_us)} rows in {dur:.0f} s = {len(t_us) / dur:.0f} rows/s")
    print(f"  motion energy  median {np.median(e):.4f}   95th pct {np.percentile(e, 95):.4f}   "
          f"max {e.max():.4f}")

    if not (a.signs and a.labels):
        print("\nGive --signs and --labels for the full verdict.")
        return

    # ---- signal ------------------------------------------------------------
    t2, amp2 = load_csi(one(a.signs))
    _, g2 = to_grid(t2, amp2)
    e2, _ = motion_energy(g2)
    lab = load_labels(sorted({p for pat in a.labels for p in glob.glob(pat)}))
    tr = lab[(lab.type == "sign") & ~lab.excluded & lab.t_end_us.notna()]
    tr = tr[(tr.t_start_us > t2[0]) & (tr.t_end_us < t2[-1])]
    means = []
    for r in tr.itertuples():
        i0, i1 = int((r.t_start_us - t2[0]) / 1e6 * FS), int((r.t_end_us - t2[0]) / 1e6 * FS)
        means.append(np.nanmean(e2[i0:i1]))
    means = np.array([m for m in means if np.isfinite(m)])
    if len(means) < 5:
        raise SystemExit("fewer than 5 usable sign trials - check the files belong together")
    sign_dur = float((tr.t_end_us - tr.t_start_us).median() / 1e6)
    weak = np.percentile(means, 25)
    print(f"\nsigns       : {len(means)} trials, typical length {sign_dur:.1f} s")
    print(f"  motion energy  median {np.median(means):.4f}   weakest quarter below {weak:.4f}")

    # ---- compare -----------------------------------------------------------
    # How often does the EMPTY place, averaged over one sign length, look at
    # least as strong as a weak sign?  That is time a model could mistake for a command.
    w = max(int(sign_dur * FS), 1)
    e_win = pd.Series(e).rolling(w, min_periods=w // 2).mean().dropna().to_numpy()
    leak = float((e_win >= weak).mean() * 100)
    ratio = weak / np.percentile(e, 95)

    print(f"\n  weak sign / loud empty moment      : {ratio:.1f}x")
    print(f"  empty time that looks like a sign  : {leak:.1f} %")
    if ratio >= 3 and leak <= 1:
        verdict = "GOOD - record here."
    elif ratio >= 1.5 and leak <= 5:
        verdict = ("USABLE - record here, but keep people and moving things away from the open "
                   "side, and record only in calm, dry weather.")
    else:
        verdict = ("NOT GOOD - outside movement is as strong as the signs. Move to a closed room, "
                   "or move the TX/RX further from the open side and test again.")
    print(f"\nVERDICT: {verdict}")


if __name__ == "__main__":
    main()
