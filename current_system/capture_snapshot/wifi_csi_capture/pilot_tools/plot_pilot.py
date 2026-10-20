#!/usr/bin/env python3
"""
plot_pilot.py - quality check + figures from one CSI CSV and its label file(s).

  python3 plot_pilot.py --csi P00_part2_actions.csv --labels labels_P00_actions_*.csv --out figs/

Makes, in --out:
  <name>_qc.png          packets per second over the recording, with label bands
  <name>_trials.png      isolated trials: motion energy of every repetition, per class
  <name>_<script>_r<k>.png   scripts: CSI heatmap + motion energy + ground-truth bands
  <name>_trials.csv      per-trial packets, rate and motion energy
and prints a QC summary plus the one-number test (can mean motion energy alone
tell a sign from a routine action?  If AUC is close to 1.0, the task is too easy).

Needs numpy, pandas, matplotlib.  Runs on any laptop (not only the RX one).
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Colour by what the segment IS (fixed order, reference palette):
TYPE_COLOR = {"activity": "#2a78d6", "sign": "#eb6834", "idle": "#9a9994", "sync": "#52514e"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
FS = 100.0            # analysis grid (Hz) - CSI is resampled onto it using Timestamp_us
MAX_GAP_S = 0.25      # grid points inside a longer packet gap are left empty


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


# ------------------------------------------------------------------ load ---
def load_csi(path):
    df = pd.read_csv(path, on_bad_lines="skip")
    df = df.dropna()
    re = df[[f"SC{k}_Re" for k in range(52)]].to_numpy(float)
    im = df[[f"SC{k}_Im" for k in range(52)]].to_numpy(float)
    amp = np.hypot(re, im)
    t_us = df["Timestamp_us"].to_numpy(np.int64)
    order = np.argsort(t_us, kind="stable")
    return t_us[order], amp[order]


def load_labels(paths):
    frames = [pd.read_csv(p) for p in paths]
    lab = pd.concat(frames, ignore_index=True)
    bad_trials = set(lab.loc[lab.label == "BAD_TRIAL", "trial"].astype(str))
    bad_runs = set(zip(lab.loc[lab.label == "BAD_RUN", "script_id"], lab.loc[lab.label == "BAD_RUN", "run"]))
    lab = lab[~lab.label.isin(["BAD_TRIAL", "BAD_RUN"])].copy()
    lab["excluded"] = [
        (str(r.trial) in bad_trials and r.mode != "script") or ((r.script_id, r.run) in bad_runs)
        for r in lab.itertuples()]
    return lab


# ------------------------------------------------------------- features ---
def to_grid(t_us, amp):
    """Resample amplitude onto a uniform grid; blank out long packet gaps."""
    t = (t_us - t_us[0]) / 1e6
    grid = np.arange(0, t[-1], 1 / FS)
    out = np.empty((len(grid), amp.shape[1]))
    for k in range(amp.shape[1]):
        out[:, k] = np.interp(grid, t, amp[:, k])
    idx = np.searchsorted(t, grid)
    idx = np.clip(idx, 1, len(t) - 1)
    gap = (t[idx] - t[idx - 1]) > MAX_GAP_S
    out[gap] = np.nan
    return grid, out


def motion_energy(g_amp, win_s=0.5):
    """Mean over subcarriers of the rolling std of median-normalised amplitude."""
    z = g_amp / np.nanmedian(g_amp, axis=0) - 1.0       # removes the static per-subcarrier arch
    s = pd.DataFrame(z).rolling(int(win_s * FS), center=True, min_periods=5).std()
    return s.mean(axis=1).to_numpy(), z


def auc(pos, neg):
    """Mann-Whitney AUC without sklearn."""
    x = np.r_[pos, neg]
    r = pd.Series(x).rank().to_numpy()
    n1, n0 = len(pos), len(neg)
    return (r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else np.nan


# ---------------------------------------------------------------- plots ---
def plot_qc(name, t_us, lab, t0_us, out):
    t = (t_us - t0_us) / 1e6
    secs = np.floor(t).astype(int)
    counts = np.bincount(secs)
    gaps = np.diff(t)
    dur = t[-1] - t[0]
    summary = (f"{len(t)} packets in {dur:.1f} s  ->  {len(t)/dur:.1f} Hz average | "
               f"median gap {np.median(gaps)*1e3:.1f} ms | gaps >100 ms: {(gaps > 0.1).sum()} | "
               f"longest gap {gaps.max()*1e3:.0f} ms")
    fig, ax = plt.subplots(figsize=(11, 2.8))
    add_bands(ax, lab, t0_us, alpha=0.18)
    ax.plot(np.arange(len(counts)), counts, color=INK, lw=1.2)
    ax.set_xlabel("time (s)", color=INK2, fontsize=9)
    ax.set_ylabel("packets / s", color=INK2, fontsize=9)
    ax.set_title(f"{name}: CSI rate   ({summary})", fontsize=9, color=INK, loc="left")
    style(ax)
    add_legend(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"{name}_qc.png"), dpi=150)
    plt.close(fig)
    return summary


def add_bands(ax, lab, t0_us, alpha=0.22, text=False):
    for r in lab.itertuples():
        if r.type == "sync" or pd.isna(r.t_start_us) or r.excluded:
            continue
        a, b = (r.t_start_us - t0_us) / 1e6, (r.t_end_us - t0_us) / 1e6
        ax.axvspan(a, b, color=TYPE_COLOR.get(r.type, "#cccccc"), alpha=alpha, lw=0)
        if text:
            ax.text((a + b) / 2, 1.01, r.label, transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=7, color=INK2, rotation=60)


def add_legend(ax):
    handles = [Patch(color=TYPE_COLOR[k], alpha=0.5, label=k) for k in ("activity", "sign", "idle")]
    ax.legend(handles=handles, loc="upper right", fontsize=7, frameon=False, ncol=3)


def plot_trials(name, lab, grid_t, energy, t0_us, out):
    iso = lab[(lab["mode"] != "script") & (lab.type.isin(["activity", "sign", "idle"])) & ~lab.excluded]
    if iso.empty:
        return None
    rows, per_trial = [], []
    classes = list(dict.fromkeys(iso.label))
    ncol = 4
    nrow = int(np.ceil(len(classes) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.2 * ncol, 2.1 * nrow), sharey=True, squeeze=False)
    ymax = 0
    for ax, cls in zip(axes.flat, classes):
        sub = iso[iso.label == cls]
        col = TYPE_COLOR.get(sub.type.iloc[0], INK)
        curves = []
        for r in sub.itertuples():
            a = (r.t_start_us - t0_us) / 1e6
            b = (r.t_end_us - t0_us) / 1e6
            i0, i1 = int((a - 2) * FS), int((b + 2) * FS)
            if i0 < 0 or i1 > len(energy):
                continue
            seg = energy[i0:i1]
            x = np.arange(len(seg)) / FS - 2
            ax.plot(x, seg, color=col, lw=0.8, alpha=0.35)
            curves.append(seg)
            inside = energy[int(a * FS):int(b * FS)]
            per_trial.append(dict(label=cls, type=r.type, trial=r.trial, posture=r.posture,
                                  mean_energy=np.nanmean(inside)))
        if curves:
            L = min(map(len, curves))
            m = np.nanmean([c[:L] for c in curves], axis=0)
            ax.plot(np.arange(L) / FS - 2, m, color=col, lw=2)
            ymax = max(ymax, np.nanpercentile(np.concatenate(curves), 99))
            dur = (sub.t_end_us - sub.t_start_us).median() / 1e6
            ax.axvspan(0, dur, color=GRID, alpha=0.5, lw=0)
        ax.set_title(f"{cls}  (n={len(curves)})", fontsize=9, color=INK, loc="left")
        style(ax)
    for ax in axes.flat[len(classes):]:
        ax.axis("off")
    for ax in axes.flat[:len(classes)]:
        ax.set_ylim(0, ymax * 1.05 if ymax > 0 else 1)
    fig.suptitle(f"{name}: motion energy per repetition (grey = GO..STOP window; "
                 f"blue = routine action, orange = ISL sign)", fontsize=9, color=INK, x=0.01, ha="left")
    fig.supxlabel("seconds from GO", fontsize=8, color=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(out, f"{name}_trials.png"), dpi=150)
    plt.close(fig)
    df = pd.DataFrame(per_trial)
    df.to_csv(os.path.join(out, f"{name}_trials.csv"), index=False)
    return df


def plot_scripts(name, lab, grid_t, z, energy, t0_us, out):
    scr = lab[(lab["mode"] == "script") & ~lab.excluded]
    made = []
    for (sid, run), g in scr.groupby(["script_id", "run"]):
        g = g.sort_values("step")
        a = (g.t_start_us.min() - t0_us) / 1e6 - 3
        b = (g.t_end_us.max() - t0_us) / 1e6 + 3
        i0, i1 = max(int(a * FS), 0), min(int(b * FS), len(energy))
        if i1 - i0 < FS:
            continue
        x = grid_t[i0:i1]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 5), sharex=True,
                                       gridspec_kw=dict(height_ratios=[1.3, 1]))
        zz = z[i0:i1].T
        lim = np.nanpercentile(np.abs(zz), 98)
        ax1.imshow(np.abs(zz), aspect="auto", origin="lower", cmap="Blues", vmin=0, vmax=lim,
                   extent=[x[0], x[-1], 0, 52], interpolation="nearest")
        ax1.set_ylabel("subcarrier", fontsize=8, color=INK2)
        ax1.set_title(f"{name}: {sid} run {int(run)}  |amplitude change| per subcarrier "
                      f"(top) and motion energy with ground truth (bottom)", fontsize=9, color=INK, loc="left")
        ax1.tick_params(colors=INK2, labelsize=8)
        add_bands(ax2, g, t0_us, text=True)
        ax2.plot(x, energy[i0:i1], color=INK, lw=1)
        ax2.set_xlabel("time (s)", fontsize=8, color=INK2)
        ax2.set_ylabel("motion energy", fontsize=8, color=INK2)
        style(ax2)
        add_legend(ax2)
        fig.tight_layout()
        p = os.path.join(out, f"{name}_{sid}_r{int(run)}.png")
        fig.savefig(p, dpi=150)
        plt.close(fig)
        made.append(p)
    return made


# ----------------------------------------------------------------- main ---
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csi", required=True)
    ap.add_argument("--labels", nargs="+", required=True, help="label CSV(s); globs allowed")
    ap.add_argument("--out", default="figs")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    paths = sorted({p for pat in args.labels for p in glob.glob(pat)})
    name = os.path.splitext(os.path.basename(args.csi))[0]

    t_us, amp = load_csi(args.csi)
    lab = load_labels(paths)
    t0 = t_us[0]
    lab = lab[(lab.t_end_us.isna()) | ((lab.t_end_us > t0) & (lab.t_start_us.fillna(t0) < t_us[-1]))]

    print("QC  :", plot_qc(name, t_us, lab, t0, args.out))
    grid_t, g_amp = to_grid(t_us, amp)
    energy, z = motion_energy(g_amp)

    df = plot_trials(name, lab, grid_t, energy, t0, args.out)
    if df is not None and not df.empty:
        print("\nPer class (mean motion energy inside GO..STOP):")
        print(df.groupby(["type", "label"]).mean_energy.agg(["count", "mean", "std"]).round(4).to_string())
        s, a = df[df.type == "sign"].mean_energy.dropna(), df[df.type == "activity"].mean_energy.dropna()
        if len(s) and len(a):
            v = auc(a.to_numpy(), s.to_numpy())
            print(f"\nOne-number test, sign vs routine (AUC of mean motion energy): {v:.2f}  "
                  f"(1.0 or 0.0 = trivially separable, 0.5 = the scalar is useless)")
    for p in plot_scripts(name, lab, grid_t, z, energy, t0, args.out):
        print("figure:", p)
    print(f"\nFigures in {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
