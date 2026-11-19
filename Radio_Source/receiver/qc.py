#!/usr/bin/env python3
"""
Quality-check one capture CSV, immediately after recording it.

    python3 qc.py <csv> [--expect-channel N] [--min-rate HZ] [--window-s S]

Exits 0 if the capture is usable, 1 if it is not. capture.sh calls this after
every instance so a bad recording is caught while the subject is still standing
in the room, not on the last day when the dataset is being assembled.

Deliberately stdlib-only: numpy/pandas are not needed to count rows and
timestamps, and the capture loop must never fail because of a missing package.

The decisive metric is `usable windows`, not the average rate. A capture can
average 50 Hz and still be useless if the packets arrive in bursts separated by
one-second holes, because every 2 s window then falls short of the 100 samples
the HAR pipeline needs. Averages hide that; window counting does not.
"""

import argparse
import csv
import os
import statistics
import sys


# Matches the HAR pipeline's hardcoded requirement (RATE=50, WINDOW_SECONDS=2).
PIPELINE_RATE_HZ = 50
PIPELINE_WINDOW_S = 2.0
PIPELINE_SAMPLES_PER_WINDOW = int(PIPELINE_RATE_HZ * PIPELINE_WINDOW_S)  # 100


def read_capture(path):
    """Return (timestamps_us sorted, channel values) using only the stdlib."""
    ts, ch = [], []

    with open(path, newline="") as f:
        reader = csv.reader(f)

        try:
            header = next(reader)
        except StopIteration:
            return [], []

        try:
            ti = header.index("Timestamp_us")
        except ValueError:
            raise SystemExit(f"{path}: no Timestamp_us column — not a CSI capture?")

        ci = header.index("Channel") if "Channel" in header else None

        for row in reader:
            if len(row) <= ti:
                continue  # truncated final row from a hard kill
            try:
                ts.append(int(row[ti]))
            except ValueError:
                continue
            if ci is not None and len(row) > ci:
                ch.append(row[ci])

    ts.sort()
    return ts, ch


def analyse(ts, window_s=PIPELINE_WINDOW_S):
    """Compute the statistics that decide whether this capture is usable."""
    span_s = (ts[-1] - ts[0]) / 1e6
    if span_s <= 0:
        return None

    gaps_ms = [(b - a) / 1000.0 for a, b in zip(ts, ts[1:])]
    gaps_sorted = sorted(gaps_ms)

    def pct(p):
        if not gaps_sorted:
            return 0.0
        idx = min(int(p / 100.0 * len(gaps_sorted)), len(gaps_sorted) - 1)
        return gaps_sorted[idx]

    # Count samples in each consecutive wall-clock window.
    #
    # Only FULL windows count. A capture spanning 10.03 s contains five whole
    # 2 s windows plus a 0.03 s remainder — and that remainder is not a window
    # the pipeline could ever form, so scoring it as a failed one would mark
    # every healthy instance down for the crime of not being an exact multiple
    # of the window length.
    win_us = int(window_s * 1_000_000)
    per_window, start, i = [], ts[0], 0
    while start + win_us <= ts[-1]:
        end = start + win_us
        n = 0
        while i + n < len(ts) and ts[i + n] < end:
            n += 1
        per_window.append(n)
        i += n
        start = end

    usable = sum(1 for n in per_window if n >= PIPELINE_SAMPLES_PER_WINDOW)

    return {
        "rows": len(ts),
        "span_s": span_s,
        "rate_hz": len(ts) / span_s,
        "gap_median_ms": statistics.median(gaps_ms) if gaps_ms else 0.0,
        "gap_p95_ms": pct(95),
        "gap_max_ms": max(gaps_ms) if gaps_ms else 0.0,
        "windows_total": len(per_window),
        "windows_usable": usable,
        "windows_usable_pct": 100.0 * usable / max(len(per_window), 1),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--expect-channel", type=int, default=None,
                    help="fail if any row reports a different channel")
    ap.add_argument("--min-rate", type=float, default=40.0,
                    help="minimum acceptable mean rate in Hz (default 40)")
    ap.add_argument("--min-usable-pct", type=float, default=70.0,
                    help="minimum %% of 2s windows with >=100 samples (default 70)")
    ap.add_argument("--window-s", type=float, default=PIPELINE_WINDOW_S)
    ap.add_argument("--from-us", type=int, default=None,
                    help="ignore rows before this epoch-microsecond timestamp "
                         "(capture.sh passes the GO cue, so warm-up rows "
                         "recorded before the subject started are excluded)")
    ap.add_argument("--to-us", type=int, default=None,
                    help="ignore rows after this epoch-microsecond timestamp")
    ap.add_argument("--quiet", action="store_true",
                    help="print only on failure")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        print(f"!!! FAIL  no such file: {args.csv}", file=sys.stderr)
        return 1

    ts, ch = read_capture(args.csv)

    # Restrict to the interval the subject was actually performing the
    # activity. Without this the flowgraph warm-up rows drag the measured
    # rate and gap statistics away from what the labelled data really is.
    if args.from_us is not None or args.to_us is not None:
        lo = args.from_us if args.from_us is not None else float("-inf")
        hi = args.to_us if args.to_us is not None else float("inf")
        paired = [(t, c) for t, c in zip(ts, ch + [None] * (len(ts) - len(ch)))
                  if lo <= t <= hi]
        ts = [t for t, _ in paired]
        ch = [c for _, c in paired if c is not None]

    if len(ts) < 2:
        print(f"!!! FAIL  {os.path.basename(args.csv)}: {len(ts)} rows — "
              f"nothing was captured.", file=sys.stderr)
        print("          Check: is packet_generator.py running? Do TX_CHANNEL "
              "and CSI_CHANNEL match?", file=sys.stderr)
        return 1

    st = analyse(ts, args.window_s)
    if st is None:
        print(f"!!! FAIL  {os.path.basename(args.csv)}: zero time span.",
              file=sys.stderr)
        return 1

    problems = []

    if st["rate_hz"] < args.min_rate:
        problems.append(
            f"rate {st['rate_hz']:.1f} Hz is below the {args.min_rate:.0f} Hz minimum")

    if st["windows_total"] == 0:
        # Capture shorter than one window: the rate check above is the only
        # meaningful gate, so say so rather than reporting a bogus 0%.
        pass
    elif st["windows_usable_pct"] < args.min_usable_pct:
        problems.append(
            f"only {st['windows_usable_pct']:.0f}% of {args.window_s:g}s windows reach "
            f"{PIPELINE_SAMPLES_PER_WINDOW} samples "
            f"({st['windows_usable']}/{st['windows_total']})")

    # A single long hole mid-recording means the subject performed part of the
    # activity into a dead link. That instance is unlabelled data, not data.
    if st["gap_max_ms"] > 1000.0:
        problems.append(f"largest gap {st['gap_max_ms']/1000:.1f} s — link dropped "
                        f"mid-recording")

    channels = sorted(set(c for c in ch if c))
    if args.expect_channel is not None and channels:
        unexpected = [c for c in channels if c != str(args.expect_channel)]
        if unexpected:
            problems.append(
                f"rows labelled channel {unexpected} but expected "
                f"{args.expect_channel} — is the receiver actually parked?")

    summary = (
        f"{st['rows']:5d} rows  {st['rate_hz']:5.1f} Hz  "
        f"{st['span_s']:5.1f} s  "
        f"gap med {st['gap_median_ms']:5.1f} / p95 {st['gap_p95_ms']:6.1f} / "
        f"max {st['gap_max_ms']:7.1f} ms  "
        f"usable {st['windows_usable']}/{st['windows_total']} "
        f"({st['windows_usable_pct']:.0f}%)"
    )

    if problems:
        print(f"!!! FAIL  {summary}", file=sys.stderr)
        for p in problems:
            print(f"!!!       - {p}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"    OK    {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
