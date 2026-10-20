#!/usr/bin/env python3
"""Quantitative characterisation of the pilot CSI capture.

Writes a JSON of every measured statistic (consumed by the LaTeX deck) and the
per-file numbers used in the comparative analysis. No claims here are
hand-typed: everything is measured from the 8 capture CSVs and the 322 windows.
"""

import glob
import json
import os

import numpy as np
import pandas as pd

PILOT = "/home/rishiikesh/usrp-projects/data/pilot"
OUT = "/home/rishiikesh/usrp-projects/analysis"
os.makedirs(OUT, exist_ok=True)

C = 3e8
FC = 2.462e9  # channel 11


def load_capture(path):
    df = pd.read_csv(path)
    n_sc = sum(1 for c in df.columns if c.endswith("_Re"))
    cols = [f"SC{i}_Re" for i in range(n_sc)] + [f"SC{i}_Im" for i in range(n_sc)]
    # exactly one truncated trailing row per file (Ctrl+C mid-write) -> drop it
    n_before = len(df)
    df = df.dropna(subset=cols + ["Timestamp_us"])
    n_dropped = n_before - len(df)
    t = df["Timestamp_us"].to_numpy(np.int64)
    re = df[[f"SC{i}_Re" for i in range(n_sc)]].to_numpy(float)
    im = df[[f"SC{i}_Im" for i in range(n_sc)]].to_numpy(float)
    amp = np.hypot(re, im)
    o = np.argsort(t)
    return t[o], amp[o], n_sc, n_dropped


def parse(fn):
    # P01_<class>_<subject>_<date>_<take>.csv
    p = os.path.basename(fn)[:-4].split("_")
    return {"cls": p[1], "subject": p[2], "date": p[3], "take": p[4]}


results = {"files": [], "meta": {"fc_hz": FC}}

for path in sorted(glob.glob(os.path.join(PILOT, "P01_*.csv"))):
    meta = parse(path)
    t, amp, n_sc, n_dropped = load_capture(path)
    n = len(t)
    dur = (t[-1] - t[0]) / 1e6
    rate = (n - 1) / dur

    # inter-arrival jitter
    gaps_ms = np.diff(t) / 1e3
    # per-second instantaneous rate
    sec = ((t - t[0]) // 1_000_000).astype(int)
    per_sec = np.bincount(sec)
    per_sec = per_sec[:-1] if len(per_sec) > 1 else per_sec  # drop partial last

    # amplitude statistics
    amp_mean = float(amp.mean())
    amp_std = float(amp.std())

    # motion energy: std over time of each subcarrier, after removing its mean
    detr = amp - amp.mean(axis=0, keepdims=True)
    sc_temporal_std = detr.std(axis=0)          # (52,)
    motion_energy = float(sc_temporal_std.mean())
    # normalised (coefficient of variation) - comparable across gain settings
    cv = float((sc_temporal_std / (amp.mean(axis=0) + 1e-12)).mean())

    # subcarrier-to-subcarrier correlation (spatial redundancy)
    cc = np.corrcoef(detr.T)
    iu = np.triu_indices(n_sc, k=1)
    mean_abs_corr = float(np.abs(cc[iu]).mean())

    # effective rank of the 52-subcarrier covariance (how many independent views).
    # SVD on the centred matrix is numerically safer than eigvalsh on the cov.
    sv = np.linalg.svd(detr - detr.mean(axis=0, keepdims=True),
                       compute_uv=False)
    ev = np.clip(sv ** 2, 1e-18, None)
    p_ = ev / ev.sum()
    eff_rank = float(np.exp(-(p_ * np.log(p_)).sum()))

    results["files"].append({
        **meta,
        "file": os.path.basename(path),
        "rows": int(n),
        "duration_s": round(dur, 1),
        "rate_hz": round(rate, 1),
        "rate_per_sec_min": int(per_sec.min()),
        "rate_per_sec_med": float(np.median(per_sec)),
        "rate_per_sec_max": int(per_sec.max()),
        "gap_ms_med": round(float(np.median(gaps_ms)), 2),
        "gap_ms_p99": round(float(np.percentile(gaps_ms, 99)), 2),
        "gap_ms_max": round(float(gaps_ms.max()), 1),
        "nyquist_hz": round(rate / 2, 1),
        "max_speed_unaliased_ms": round((rate / 2) * C / (2 * FC), 2),
        "n_subcarriers": int(n_sc),
        "amp_mean": amp_mean,
        "amp_std": amp_std,
        "motion_energy": motion_energy,
        "cv": cv,
        "mean_abs_sc_corr": mean_abs_corr,
        "eff_rank": eff_rank,
        "truncated_rows_dropped": int(n_dropped),
        "zero_rows": int((amp.sum(axis=1) == 0).sum()),
    })

# ---------- window-level analysis ----------
wins = {"action": [], "noaction": []}
win_meta = {"action": [], "noaction": []}
for cls in ("action", "noaction"):
    for f in sorted(glob.glob(os.path.join(PILOT, "windows", cls, "*.npy"))):
        wins[cls].append(np.load(f))
        b = os.path.basename(f)
        win_meta[cls].append({
            "subject": "amrith" if "_amrith_" in b else "rishiikesh",
            "take": next(k for k in ("walk", "mixed", "stand", "sit") if k in b),
        })

results["windows"] = {}
for cls in wins:
    W = np.stack(wins[cls])                    # (N, 52, 200)
    detr = W - W.mean(axis=2, keepdims=True)
    per_win_energy = detr.std(axis=2).mean(axis=1)   # (N,)
    results["windows"][cls] = {
        "n": int(W.shape[0]),
        "shape": list(W.shape[1:]),
        "energy_mean": float(per_win_energy.mean()),
        "energy_std": float(per_win_energy.std()),
        "energy_median": float(np.median(per_win_energy)),
    }

# separability of the single best hand-crafted feature (motion energy)
ea = np.stack([ (w - w.mean(axis=1, keepdims=True)).std(axis=1).mean() for w in wins["action"] ])
en = np.stack([ (w - w.mean(axis=1, keepdims=True)).std(axis=1).mean() for w in wins["noaction"] ])
fisher = (ea.mean() - en.mean()) ** 2 / (ea.var() + en.var())
# threshold accuracy of that one feature
allv = np.concatenate([ea, en])
ths = np.linspace(allv.min(), allv.max(), 2000)
best = max(((ea > th).sum() + (en <= th).sum()) / (len(ea) + len(en)) for th in ths)
results["separability"] = {
    "fisher_ratio": float(fisher),
    "single_feature_best_acc": float(best),
    "action_energy_mean": float(ea.mean()),
    "noaction_energy_mean": float(en.mean()),
    "energy_ratio": float(ea.mean() / en.mean()),
}

# per-take breakdown of motion energy
per_take = {}
for cls in wins:
    for w, m in zip(wins[cls], win_meta[cls]):
        e = (w - w.mean(axis=1, keepdims=True)).std(axis=1).mean()
        per_take.setdefault(m["take"], []).append(float(e))
results["per_take_energy"] = {k: {"n": len(v), "mean": float(np.mean(v)),
                                  "std": float(np.std(v))}
                              for k, v in sorted(per_take.items())}

# window yield: how many windows were possible vs saved (the --rate 100 cost)
tot_dur = sum(f["duration_s"] for f in results["files"])
results["yield"] = {
    "total_capture_s": round(tot_dur, 1),
    "windows_possible_2s": int(sum(f["duration_s"] // 2 for f in results["files"])),
    "windows_saved": int(sum(results["windows"][c]["n"] for c in results["windows"])),
}
results["yield"]["dropped"] = (results["yield"]["windows_possible_2s"]
                               - results["yield"]["windows_saved"])
results["yield"]["dropped_pct"] = round(
    100 * results["yield"]["dropped"] / results["yield"]["windows_possible_2s"], 1)

with open(os.path.join(OUT, "pilot_stats.json"), "w") as fh:
    json.dump(results, fh, indent=2)

# ---------- console summary ----------
print("=== per-file ===")
for f in results["files"]:
    print("%-46s %5.1f Hz  nyq %4.1f Hz  vmax %.2f m/s  CV %.4f  effrank %.1f"
          % (f["file"], f["rate_hz"], f["nyquist_hz"],
             f["max_speed_unaliased_ms"], f["cv"], f["eff_rank"]))

print("\n=== rate summary ===")
r = [f["rate_hz"] for f in results["files"]]
print("mean %.1f  min %.1f  max %.1f Hz" % (np.mean(r), min(r), max(r)))

print("\n=== windows ===")
for c, v in results["windows"].items():
    print("%-9s n=%3d  energy %.4f +/- %.4f" % (c, v["n"], v["energy_mean"], v["energy_std"]))

print("\n=== separability (motion energy alone) ===")
s = results["separability"]
print("action/noaction energy ratio %.2fx   Fisher %.2f   1-feature acc %.3f"
      % (s["energy_ratio"], s["fisher_ratio"], s["single_feature_best_acc"]))

print("\n=== per-take energy ===")
for k, v in results["per_take_energy"].items():
    print("%-7s n=%3d  %.4f +/- %.4f" % (k, v["n"], v["mean"], v["std"]))

print("\n=== window yield ===")
y = results["yield"]
print("capture %.0f s -> %d possible, %d saved, %d dropped (%.1f%%)"
      % (y["total_capture_s"], y["windows_possible_2s"], y["windows_saved"],
         y["dropped"], y["dropped_pct"]))
print("\n-> %s" % os.path.join(OUT, "pilot_stats.json"))
