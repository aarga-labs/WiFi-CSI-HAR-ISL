#!/usr/bin/env python3
"""
Measure single-channel (parked) vs three-channel (hopping) CSI captures.

Every number quoted in THREE_CHANNEL_ANALYSIS.md comes from this script.
Run it to regenerate both the statistics and the figures:

    python3 doc/analyze_channels.py

Outputs:
    doc/channel_stats.json
    doc/figures/*.png
"""

import csv
import glob
import json
import os
import statistics
from collections import Counter

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = os.path.expanduser("~/usrp-projects/data")
HERE = os.path.dirname(os.path.abspath(__file__))
FIGS = os.path.join(HERE, "figures")
os.makedirs(FIGS, exist_ok=True)

# The existing HAR pipeline (Action_NoAction_imgfi.ipynb) hardcodes these.
# They define what a capture must deliver to be usable at all.
PIPELINE_RATE_HZ = 50
PIPELINE_WINDOW_S = 2
PIPELINE_SAMPLES_PER_WINDOW = PIPELINE_RATE_HZ * PIPELINE_WINDOW_S  # 100


def read_csv(path):
    """Return (timestamps_us, channels, amplitude[T,52])."""
    ts, ch, amp = [], [], []
    with open(path) as f:
        r = csv.reader(f)
        hdr = next(r)
        ti = hdr.index("Timestamp_us")
        ci = hdr.index("Channel") if "Channel" in hdr else None
        re_idx = [hdr.index(f"SC{i}_Re") for i in range(52)]
        im_idx = [hdr.index(f"SC{i}_Im") for i in range(52)]
        for row in r:
            if len(row) <= max(re_idx + im_idx):
                continue
            try:
                ts.append(int(row[ti]))
                re = np.array([float(row[i]) for i in re_idx])
                im = np.array([float(row[i]) for i in im_idx])
            except ValueError:
                continue
            amp.append(np.sqrt(re ** 2 + im ** 2))
            ch.append(row[ci] if ci is not None else None)
    return np.array(ts), ch, np.array(amp)


def describe(path, label):
    ts, ch, amp = read_csv(path)
    if len(ts) < 2:
        return None

    span = (ts[-1] - ts[0]) / 1e6
    gaps = np.diff(ts) / 1000.0  # ms

    # How many samples land in each consecutive 2 s wall-clock window?
    # This is the metric that decides whether the existing pipeline can run.
    edges = np.arange(ts[0], ts[-1], PIPELINE_WINDOW_S * 1_000_000)
    per_window = [int(((ts >= a) & (ts < a + PIPELINE_WINDOW_S * 1_000_000)).sum())
                  for a in edges]
    usable = sum(1 for n in per_window if n >= PIPELINE_SAMPLES_PER_WINDOW)

    return {
        "label": label,
        "file": os.path.basename(path),
        "rows": int(len(ts)),
        "duration_s": round(span, 1),
        "rate_hz": round(len(ts) / span, 2),
        "gap_ms_median": round(float(np.median(gaps)), 1),
        "gap_ms_p95": round(float(np.percentile(gaps, 95)), 1),
        "gap_ms_max": round(float(gaps.max()), 1),
        "channels": dict(Counter(c for c in ch if c)) or None,
        "windows_total": len(per_window),
        "windows_usable": usable,
        "windows_usable_pct": round(100 * usable / max(len(per_window), 1), 1),
        "samples_per_window_median": int(np.median(per_window)) if per_window else 0,
        "amp_mean": round(float(amp.mean()), 5),
        "motion_energy": round(float(amp.std(axis=0).mean()), 5),
    }


results = {"pipeline_requirement": {
    "rate_hz": PIPELINE_RATE_HZ,
    "window_s": PIPELINE_WINDOW_S,
    "samples_per_window": PIPELINE_SAMPLES_PER_WINDOW,
    "source": "Action_NoAction_imgfi.ipynb (RATE=50, WINDOW_SECONDS=2)",
}, "captures": []}

# --- single channel, parked (the July pilot that the working model was built on)
for p in sorted(glob.glob(f"{DATA}/pilot/P01_action_*walk*.csv"))[:2]:
    d = describe(p, "1-channel parked (pilot)")
    if d:
        results["captures"].append(d)

# --- three channel, hopping
for p in sorted(glob.glob(f"{DATA}/3ch_test_*.csv")):
    d = describe(p, "3-channel hopping")
    if d and d["rows"] > 50:
        results["captures"].append(d)

with open(os.path.join(HERE, "channel_stats.json"), "w") as f:
    json.dump(results, f, indent=2)

# ---------------------------------------------------------------- figures
one = next((c for c in results["captures"] if c["label"].startswith("1-channel")), None)
three = max((c for c in results["captures"] if c["label"].startswith("3-channel")),
            key=lambda c: c["rows"], default=None)

if one and three:
    # Fig 1 — sampling rate against what the pipeline needs
    fig, ax = plt.subplots(figsize=(7, 4.2))
    names = ["1-channel\n(parked)", "3-channel\n(hopping)"]
    vals = [one["rate_hz"], three["rate_hz"]]
    bars = ax.bar(names, vals, color=["#2a9d8f", "#e76f51"], width=0.55)
    ax.axhline(PIPELINE_RATE_HZ, ls="--", c="#264653", lw=1.6)
    ax.text(1.42, PIPELINE_RATE_HZ + 1.5, f"pipeline needs {PIPELINE_RATE_HZ} Hz",
            ha="right", fontsize=9, color="#264653")
    ax.axhline(36, ls=":", c="#6a4c93", lw=1.6)
    ax.text(1.42, 37.5, "Nyquist floor 36 Hz (18 Hz signal)",
            ha="right", fontsize=9, color="#6a4c93")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v} Hz",
                ha="center", fontweight="bold")
    ax.set_ylabel("CSI sampling rate (Hz)")
    ax.set_title("Achieved CSI rate vs what activity recognition requires")
    ax.set_ylim(0, max(vals) * 1.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{FIGS}/fig1_rate.png", dpi=150)
    plt.close(fig)

    # Fig 2 — gap distribution, log scale
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for path, lab, col in [
        (os.path.join(DATA, "pilot", one["file"]), "1-channel (parked)", "#2a9d8f"),
        (os.path.join(DATA, three["file"]), "3-channel (hopping)", "#e76f51"),
    ]:
        ts, _, _ = read_csv(path)
        g = np.diff(ts) / 1000.0
        g = g[g > 0]
        ax.hist(g, bins=np.logspace(0, 4, 60), alpha=0.65, label=lab, color=col)
    ax.set_xscale("log")
    ax.set_xlabel("gap between consecutive CSI samples (ms, log scale)")
    ax.set_ylabel("count")
    ax.axvline(20, ls="--", c="#264653", lw=1.4)
    ax.text(21, ax.get_ylim()[1] * 0.72, "20 ms\n(= 50 Hz)", fontsize=8, color="#264653")
    ax.set_title("Sample spacing: parked is tight and regular, hopping is not")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{FIGS}/fig2_gaps.png", dpi=150)
    plt.close(fig)

    # Fig 3 — CSI amplitude trace, first 5 subcarriers
    fig, axes = plt.subplots(2, 1, figsize=(7.5, 5.4), sharex=False)
    for ax, (path, lab, col) in zip(axes, [
        (os.path.join(DATA, "pilot", one["file"]), f"1-channel parked — {one['rate_hz']} Hz", "#2a9d8f"),
        (os.path.join(DATA, three["file"]), f"3-channel hopping — {three['rate_hz']} Hz", "#e76f51"),
    ]):
        ts, _, amp = read_csv(path)
        t = (ts - ts[0]) / 1e6
        keep = t <= 20
        for sc in range(5):
            ax.plot(t[keep], amp[keep, sc], lw=0.8, alpha=0.85)
        ax.set_title(f"{lab}   ({keep.sum()} samples in 20 s)", fontsize=10)
        ax.set_ylabel("|H|")
        ax.set_xlim(0, 20)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1].set_xlabel("time (s)")
    fig.suptitle("CSI amplitude, first 5 subcarriers, same 20-second span", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{FIGS}/fig3_traces.png", dpi=150)
    plt.close(fig)

    # Fig 4 — usable 2 s windows
    fig, ax = plt.subplots(figsize=(7, 4.2))
    names = ["1-channel\n(parked)", "3-channel\n(hopping)"]
    pct = [one["windows_usable_pct"], three["windows_usable_pct"]]
    bars = ax.bar(names, pct, color=["#2a9d8f", "#e76f51"], width=0.55)
    for b, v, c in zip(bars, pct, [one, three]):
        ax.text(b.get_x() + b.get_width() / 2, v + 2,
                f"{v}%\n({c['windows_usable']}/{c['windows_total']})",
                ha="center", fontweight="bold", fontsize=9)
    ax.set_ylabel("% of 2 s windows with ≥100 samples")
    ax.set_ylim(0, 115)
    ax.set_title("Windows the existing HAR pipeline can actually consume")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(f"{FIGS}/fig4_windows.png", dpi=150)
    plt.close(fig)

print(json.dumps(results, indent=2))
print(f"\nfigures -> {FIGS}")
