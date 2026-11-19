#!/usr/bin/env python3
"""
Day-1 go/no-go: can this rig see hand motion at all?

    python3 pilot_check.py --channel 1

Run it after recording a handful of pilot instances. It answers two questions,
in increasing order of difficulty:

  1. Does a walking person change the channel more than an empty room?
     If this fails, the link is broken or the geometry is wrong. Nothing else
     matters until it passes.

  2. Does a hand gesture change the channel more than a person standing still?
     This is the real question for Activity-vs-Gesture, and the one that can
     fail even when everything else looks fine — a hand perturbs the channel
     far less than a whole body. If this fails, raise RX_GAIN, move the
     antennas closer (~2 m), and make sure the hands cross the direct path.

The statistic is per-window temporal standard deviation of CSI amplitude,
averaged over subcarriers: how much the channel moves during the window.
Motion raises it, a still room does not. Reported both as a ratio and as
Cohen's d, because a ratio alone hides how much the two distributions overlap.
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import load_windows, CLASS_GROUP, DEFAULT_ROOT  # noqa: E402


def motion_energy(X):
    """(N, T, S) -> (N,) mean over subcarriers of the temporal std."""
    return X.std(axis=1).mean(axis=1)


def cohens_d(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2.0)
    if pooled == 0:
        return float("nan")
    return float((a.mean() - b.mean()) / pooled)


def verdict(name, a, b, ratio_target, d_target):
    """Compare two groups and print a pass/fail line."""
    if len(a) == 0 or len(b) == 0:
        print(f"  {name}: SKIPPED — need both classes recorded")
        return None

    ratio = a.mean() / b.mean() if b.mean() > 0 else float("inf")
    d = cohens_d(a, b)
    # bool() is load-bearing: numpy comparisons yield numpy.bool_, and
    # `numpy.bool_(False) is False` is itself False, so the identity checks in
    # main() would silently miss every failure and report GO regardless.
    passed = bool(ratio >= ratio_target and (np.isnan(d) or d >= d_target))

    print(f"  {name}")
    print(f"      motion energy  {a.mean():.5f}  vs  {b.mean():.5f}")
    print(f"      ratio          {ratio:5.2f}x   (want >= {ratio_target}x)")
    print(f"      Cohen's d      {d:5.2f}     (want >= {d_target})")
    print(f"      -> {'PASS' if passed else 'FAIL'}")
    return passed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--channel", type=int, default=1)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--subject", default=None, help="restrict to one subject")
    args = ap.parse_args()

    subjects = [args.subject] if args.subject else None
    d = load_windows(channel=args.channel, root=args.root,
                     include_empty=True, subjects=subjects, verbose=True)

    e = motion_energy(d.X)

    print()
    print("=" * 62)
    print(f" PILOT CHECK  channel {args.channel}")
    print("=" * 62)
    print("  per class (higher motion energy = more channel disturbance):")
    print(f"    {'class':<12s} {'windows':>8s} {'motion energy':>15s}  {'group':>9s}")
    for c in sorted(set(d.classes)):
        m = d.classes == c
        print(f"    {c:<12s} {m.sum():8d} {e[m].mean():15.5f}  "
              f"{CLASS_GROUP.get(c,'?'):>9s}")

    def grab(*names):
        m = np.isin(d.classes, list(names))
        return e[m]

    gestures = [c for c in set(d.classes) if CLASS_GROUP.get(c) == "gesture"]

    print()
    print("  TEST 1 — is the link sensitive to motion at all?")
    t1 = verdict("walk vs empty", grab("walk"), grab("empty"), 2.0, 1.0)

    print()
    print("  TEST 2 — can it see HANDS? (the one that decides the project)")
    t2 = verdict("gesture vs standstill", grab(*gestures), grab("standstill"),
                 1.3, 0.5) if gestures else None

    print()
    print("=" * 62)
    if t1 is False:
        print(" NO-GO. The link is not seeing motion.")
        print("   - check RX_GAIN (try 40 and 55), antenna orientation")
        print("   - confirm the subject crosses the direct TX-RX path")
        print("   - re-run receiver/preflight.sh")
    elif t2 is False:
        print(" PARTIAL. Whole-body motion is visible; hand motion is not.")
        print("   - raise RX_GAIN, shorten TX-RX to ~2 m")
        print("   - hands must cross the direct path, body still")
        print("   - if it still fails, fall back to large-amplitude gestures")
        print("     (two-arm wave, big beckon, arm raise) and say so in the report")
    elif t2 is None:
        print(" TEST 1 passed. Record some gesture instances and re-run.")
    else:
        print(" GO. Both tests pass — proceed to the full session.")
    print("=" * 62)


if __name__ == "__main__":
    main()
