#!/usr/bin/env python3
"""Generate every figure used in the comparative-analysis deck.

All pilot numbers are measured from the capture CSVs / windows.
All reference-dataset numbers are published specifications (see refs in deck).
"""

import glob
import json
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy import signal

PILOT = "/home/rishiikesh/usrp-projects/data/pilot"
OUT = "/home/rishiikesh/usrp-projects/analysis/figures"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "font.size": 9, "axes.grid": True, "grid.alpha": 0.25,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 130, "savefig.bbox": "tight",
})

C_ACT, C_NOA = "#c0392b", "#2471a3"
C_OURS, C_REF = "#c0392b", "#7f8c8d"

FC = 2.462e9
C = 3e8
HZ_PER_MS = 2 * FC / C          # Doppler Hz per m/s of radial speed  = 16.41

S = json.load(open("/home/rishiikesh/usrp-projects/analysis/pilot_stats.json"))
FILES = S["files"]


def load_amp(path):
    df = pd.read_csv(path)
    n_sc = sum(1 for c in df.columns if c.endswith("_Re"))
    cols = [f"SC{i}_Re" for i in range(n_sc)] + [f"SC{i}_Im" for i in range(n_sc)]
    df = df.dropna(subset=cols + ["Timestamp_us"])
    t = df["Timestamp_us"].to_numpy(np.int64)
    re = df[[f"SC{i}_Re" for i in range(n_sc)]].to_numpy(float)
    im = df[[f"SC{i}_Im" for i in range(n_sc)]].to_numpy(float)
    o = np.argsort(t)
    return (t[o] - t[o][0]) / 1e6, np.hypot(re, im)[o]


def load_windows():
    W, meta = {}, {}
    for cls in ("action", "noaction"):
        arr, mt = [], []
        for f in sorted(glob.glob(os.path.join(PILOT, "windows", cls, "*.npy"))):
            arr.append(np.load(f))
            b = os.path.basename(f)
            mt.append({"subject": "amrith" if "_amrith_" in b else "rishiikesh",
                       "take": next(k for k in ("walk", "mixed", "stand", "sit")
                                    if k in b)})
        W[cls], meta[cls] = np.stack(arr), mt
    return W, meta


WIN, WMETA = load_windows()


# ---------------------------------------------------------------- fig 1
def fig_rate_vs_datasets():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.4),
                                 gridspec_kw={"width_ratios": [1.15, 1]})

    names = [f"{f['subject'][:4]}\n{f['take']}" for f in FILES]
    rates = [f["rate_hz"] for f in FILES]
    cols = [C_ACT if f["cls"] == "action" else C_NOA for f in FILES]
    a1.bar(range(len(rates)), rates, color=cols)
    a1.axhline(100, ls="--", c="k", lw=1)
    a1.text(len(rates) - .4, 102, "pipeline assumes 100 Hz", ha="right", fontsize=7.5)
    a1.axhline(50, ls=":", c="#e67e22", lw=1.4)
    a1.text(-.4, 44, "project gate 50 Hz", fontsize=7.5, color="#e67e22")
    a1.set_xticks(range(len(rates)))
    a1.set_xticklabels(names, fontsize=6.8)
    a1.set_ylabel("packet rate (Hz)")
    a1.set_title("(a) Our 8 captures: 51.5 – 77.6 Hz (mean 66.4)", fontsize=9.5)
    a1.set_ylim(0, 115)
    a1.legend(handles=[Patch(color=C_ACT, label="action"),
                       Patch(color=C_NOA, label="noaction")],
              fontsize=7.5, loc="lower right")

    ds = ["Ours\n(pilot)", "SignFi", "NTU-Fi", "UT-HAR", "Widar 3.0"]
    dr = [66.4, 200, 500, 1000, 1000]
    dc = [C_OURS] + [C_REF] * 4
    a2.bar(ds, dr, color=dc)
    a2.set_yscale("log")
    a2.set_ylabel("packet rate (Hz, log)")
    a2.set_title("(b) vs published datasets — 15× below UT-HAR/Widar", fontsize=9.5)
    for i, v in enumerate(dr):
        a2.text(i, v * 1.15, f"{v:g}", ha="center", fontsize=7.5)
    a2.set_ylim(30, 3000)
    fig.savefig(f"{OUT}/fig1_rate.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 2
def fig_rate_stability():
    fig, axes = plt.subplots(2, 4, figsize=(11, 4.2), sharey=True)
    for ax, f in zip(axes.ravel(), FILES):
        t, amp = load_amp(os.path.join(PILOT, f["file"]))
        sec = t.astype(int)
        ps = np.bincount(sec)[:-1]
        col = C_ACT if f["cls"] == "action" else C_NOA
        ax.bar(np.arange(len(ps)), ps, width=1, color=col, alpha=.85)
        ax.axhline(50, ls=":", c="#e67e22", lw=1.2)
        ax.set_title(f"{f['subject'][:4]} {f['take']}  ({f['rate_hz']:.0f} Hz)",
                     fontsize=8)
        ax.set_xlabel("second", fontsize=7.5)
        ax.tick_params(labelsize=7)
    axes[0, 0].set_ylabel("packets/s")
    axes[1, 0].set_ylabel("packets/s")
    fig.suptitle("Instantaneous capture rate — dips below the 50 Hz gate are the "
                 "windows that get dropped", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig2_rate_stability.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 3
def fig_amplitude_traces():
    picks = [("P01_action_rishiikesh_20260717_walk.csv", "action — walk"),
             ("P01_action_rishiikesh_20260717_mixed.csv", "action — mixed"),
             ("P01_noaction_rishiikesh_20260717_stand.csv", "noaction — stand"),
             ("P01_noaction_rishiikesh_20260717_sit.csv", "noaction — sit")]
    fig, axes = plt.subplots(4, 1, figsize=(9.6, 6), sharex=True)
    for ax, (fn, title) in zip(axes, picks):
        t, amp = load_amp(os.path.join(PILOT, fn))
        m = t <= 30
        col = C_ACT if "noaction" not in title else C_NOA
        for sc in (0, 13, 26, 39, 51):
            ax.plot(t[m], amp[m, sc], lw=.55, alpha=.8)
        ax.set_title(title, fontsize=8.5, loc="left", color=col)
        ax.set_ylabel("|H|", fontsize=8)
    axes[-1].set_xlabel("time (s)  — first 30 s of each take")
    fig.suptitle("Raw CSI amplitude, 5 of 52 subcarriers — the class difference is "
                 "visible by eye", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig3_traces.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 4
def fig_motion_energy():
    def eng(W):
        return (W - W.mean(axis=2, keepdims=True)).std(axis=2).mean(axis=1)
    ea, en = eng(WIN["action"]), eng(WIN["noaction"])

    per_take = {}
    for cls in WIN:
        e = eng(WIN[cls])
        for v, m in zip(e, WMETA[cls]):
            per_take.setdefault(m["take"], []).append(v)

    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11, 3.3))

    bins = np.linspace(0, max(ea.max(), en.max()) * 1.05, 45)
    a1.hist(en, bins=bins, color=C_NOA, alpha=.8, label=f"noaction (n={len(en)})")
    a1.hist(ea, bins=bins, color=C_ACT, alpha=.75, label=f"action (n={len(ea)})")
    a1.set_xlabel("per-window motion energy")
    a1.set_ylabel("windows")
    a1.set_title("(a) Near-separable by one scalar", fontsize=9.5)
    a1.legend(fontsize=7.5)

    order = ["walk", "mixed", "stand", "sit"]
    data = [per_take[k] for k in order]
    bp = a2.boxplot(data, labels=order, patch_artist=True, widths=.6)
    for patch, k in zip(bp["boxes"], order):
        patch.set_facecolor(C_ACT if k in ("walk", "mixed") else C_NOA)
        patch.set_alpha(.8)
    a2.set_ylabel("motion energy")
    a2.set_title("(b) By take type", fontsize=9.5)

    # threshold sweep -> single-feature accuracy
    allv = np.concatenate([ea, en])
    ths = np.linspace(allv.min(), allv.max(), 800)
    acc = [((ea > t).sum() + (en <= t).sum()) / (len(ea) + len(en)) for t in ths]
    a3.plot(ths, acc, c="k", lw=1.4)
    bi = int(np.argmax(acc))
    a3.plot(ths[bi], acc[bi], "o", c=C_ACT)
    a3.annotate(f"best {acc[bi]*100:.1f}%", (ths[bi], acc[bi]),
                textcoords="offset points", xytext=(8, -12), fontsize=8, color=C_ACT)
    a3.axhline(.5, ls=":", c="grey")
    a3.set_xlabel("threshold on motion energy")
    a3.set_ylabel("accuracy")
    a3.set_title("(c) 1 feature + 1 threshold = 99.1%", fontsize=9.5)
    a3.set_ylim(.4, 1.03)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig4_energy.pdf")
    plt.close(fig)
    return acc[bi]


# ---------------------------------------------------------------- fig 5
def fig_doppler():
    """The central technical result: where the discriminative band actually is,
    and whether our sampling rate covers it."""
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11.4, 3.4))

    sp = {}
    for cls, col in (("action", C_ACT), ("noaction", C_NOA)):
        d = WIN[cls] - WIN[cls].mean(axis=2, keepdims=True)
        f, P = signal.welch(d, fs=100.0, nperseg=128, axis=2)
        sp[cls] = P.mean(axis=(0, 1))
        a1.semilogy(f, sp[cls], color=col, lw=1.6, label=cls)

    nyq_med = np.median([x["nyquist_hz"] for x in FILES])
    nyq_min = min(x["nyquist_hz"] for x in FILES)

    a1.axvspan(nyq_min, 50, color="grey", alpha=.15)
    a1.axvline(nyq_min, color="k", ls=":", lw=1.2)
    a1.set_xlabel("frequency (Hz)")
    a1.set_ylabel("PSD of amplitude")
    a1.set_title("(a) Motion spectrum, both classes", fontsize=9.5)
    a1.legend(fontsize=8, loc="upper right")
    a1.set_xlim(0, 50)

    # ---- ratio: where does class information actually live?
    ratio = sp["action"] / sp["noaction"]
    cross = f[np.argmax(ratio <= 1.05)]
    a2.plot(f, ratio, c="k", lw=1.6)
    a2.axhline(1, ls=":", c="grey")
    a2.axvspan(0, cross, color="#27ae60", alpha=.16)
    a2.axvline(nyq_min, c="#c0392b", ls=":", lw=1.5)
    a2.axvline(nyq_med, c="#c0392b", ls="--", lw=1.5)
    a2.annotate(f"all class information\nis below {cross:.0f} Hz",
                xy=(cross, 1), xytext=(cross + 4, 12), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", lw=.9))
    a2.text(nyq_min + .6, 45, f"worst Nyquist\n{nyq_min:.0f} Hz",
            fontsize=7, color="#c0392b")
    a2.text(nyq_med + .6, 22, f"median\n{nyq_med:.0f} Hz",
            fontsize=7, color="#c0392b")
    a2.set_yscale("log")
    a2.set_xlim(0, 50)
    a2.set_xlabel("frequency (Hz)")
    a2.set_ylabel("PSD ratio  action / noaction")
    a2.set_title(f"(b) Usable band ends at {cross:.0f} Hz — we sample enough",
                 fontsize=9.5)

    # ---- what speeds that corresponds to
    speeds = np.array([0.5, 1.0, 1.5, 2.0, 3.0, 4.0])
    dopp = speeds * HZ_PER_MS
    labels = ["slow limb 0.5", "walk torso 1.0", "brisk 1.5",
              "fast limb 2.0", "fast hand 3.0", "very fast 4.0"]
    colors = [("#27ae60" if d <= nyq_min else
               "#e67e22" if d <= nyq_med else "#c0392b") for d in dopp]
    a3.barh(range(len(speeds)), dopp, color=colors, alpha=.9)
    a3.axvline(nyq_min, c="k", ls=":", lw=1.3)
    a3.axvline(nyq_med, c="k", ls="--", lw=1.3)
    a3.text(nyq_min - 1, -1.15, f"worst {nyq_min:.0f}", fontsize=6.8, ha="right")
    a3.text(nyq_med + 1, -1.15, f"median {nyq_med:.0f}", fontsize=6.8)
    a3.set_yticks(range(len(speeds)))
    a3.set_yticklabels(labels, fontsize=7.5)
    a3.set_xlabel("Doppler shift (Hz) at 2.462 GHz")
    a3.set_ylim(-1.6, len(speeds) - .3)
    a3.set_title("(c) Radial speeds captured unaliased", fontsize=9.5)
    a3.legend(handles=[Patch(color="#27ae60", label="safe, every capture"),
                       Patch(color="#e67e22", label="safe at median rate"),
                       Patch(color="#c0392b", label="aliased")],
              fontsize=6.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig5_doppler.pdf")
    plt.close(fig)
    return float(cross)


# ---------------------------------------------------------------- fig 6
def fig_redundancy():
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11, 3.3))
    for ax, fn, title in (
            (a1, "P01_action_rishiikesh_20260717_walk.csv", "action — walk"),
            (a2, "P01_noaction_rishiikesh_20260717_stand.csv", "noaction — stand")):
        _, amp = load_amp(os.path.join(PILOT, fn))
        d = amp - amp.mean(axis=0, keepdims=True)
        cc = np.corrcoef(d.T)
        im = ax.imshow(cc, vmin=-1, vmax=1, cmap="RdBu_r")
        ax.set_title(f"{title}\nsubcarrier correlation", fontsize=8.5)
        ax.set_xlabel("subcarrier"); ax.set_ylabel("subcarrier")
        ax.grid(False)
        plt.colorbar(im, ax=ax, fraction=.046)

    er_a = [f["eff_rank"] for f in FILES if f["cls"] == "action"]
    er_n = [f["eff_rank"] for f in FILES if f["cls"] == "noaction"]
    a3.bar(["action\ntakes", "noaction\ntakes"], [np.mean(er_a), np.mean(er_n)],
           yerr=[np.std(er_a), np.std(er_n)], color=[C_ACT, C_NOA], capsize=5)
    a3.axhline(52, ls="--", c="k", lw=1.2)
    a3.text(.5, 48, "52 subcarriers recorded", ha="center", fontsize=7.5)
    a3.set_ylabel("effective rank")
    a3.set_title("(c) Only ~4 independent views\nduring motion, not 52",
                 fontsize=9.5)
    a3.set_ylim(0, 58)
    for i, v in enumerate([np.mean(er_a), np.mean(er_n)]):
        a3.text(i, v + 2, f"{v:.1f}", ha="center", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig6_redundancy.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 7
def fig_window_heatmaps():
    fig, axes = plt.subplots(1, 4, figsize=(11, 2.9))
    picks = [("action", "walk"), ("action", "mixed"),
             ("noaction", "stand"), ("noaction", "sit")]
    for ax, (cls, take) in zip(axes, picks):
        idx = next(i for i, m in enumerate(WMETA[cls]) if m["take"] == take)
        w = WIN[cls][idx]
        d = w - w.mean(axis=1, keepdims=True)
        v = np.abs(d).max() * .8
        im = ax.imshow(d, aspect="auto", cmap="RdBu_r", vmin=-v, vmax=v,
                       extent=[0, 2, 52, 0])
        ax.set_title(f"{cls} — {take}", fontsize=8.5,
                     color=C_ACT if cls == "action" else C_NOA)
        ax.set_xlabel("time (s)", fontsize=8)
        ax.grid(False)
        plt.colorbar(im, ax=ax, fraction=.046)
    axes[0].set_ylabel("subcarrier")
    fig.suptitle("One 2 s window (52 × 200), mean-removed — the model's actual input",
                 fontsize=9.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig7_windows.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 8
def fig_scale_comparison():
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11, 3.2))

    ds = ["Ours", "ARIL", "UT-HAR", "Widar 3.0"]
    cols = [C_OURS, C_REF, C_REF, C_REF]

    samples = [322, 1394, 4477, 258000]
    a1.bar(ds, samples, color=cols)
    a1.set_yscale("log")
    a1.set_ylabel("labelled samples (log)")
    a1.set_title("(a) Dataset size", fontsize=9.5)
    for i, v in enumerate(samples):
        a1.text(i, v * 1.3, f"{v:,}", ha="center", fontsize=7.2)
    a1.set_ylim(100, 2e6)
    a1.tick_params(labelsize=7.5)

    subj = [2, 1, 6, 16]
    a2.bar(ds, subj, color=cols)
    a2.set_ylabel("subjects")
    a2.set_title("(b) Subject diversity", fontsize=9.5)
    for i, v in enumerate(subj):
        a2.text(i, v + .3, str(v), ha="center", fontsize=8)
    a2.tick_params(labelsize=7.5)

    streams = [52, 52, 90, 540]
    a3.bar(ds, streams, color=cols)
    a3.set_yscale("log")
    a3.set_ylabel("CSI streams (sc × ant, log)")
    a3.set_title("(c) Spatial richness", fontsize=9.5)
    for i, v in enumerate(streams):
        a3.text(i, v * 1.18, str(v), ha="center", fontsize=8)
    a3.set_ylim(20, 2000)
    a3.tick_params(labelsize=7.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig8_scale.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 9
def fig_confusion():
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))
    for ax, who in zip(axes, ["amrith", "rishiikesh"]):
        m = np.loadtxt(f"{PILOT}/hybrid_model_test-{who}_confusion.csv",
                       delimiter=",", skiprows=1, dtype=int)
        acc = np.trace(m) / m.sum()
        ax.imshow(m / m.sum(axis=1, keepdims=True), cmap="Blues", vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(m[i, j]), ha="center", va="center",
                        color="white" if i == j else "black", fontsize=12)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["action", "noaction"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["action", "noaction"], fontsize=8)
        ax.set_xlabel("predicted", fontsize=8); ax.set_ylabel("true", fontsize=8)
        ax.set_title(f"test = {who}  ({acc*100:.1f}%, n={m.sum()})", fontsize=9)
        ax.grid(False)
    fig.suptitle("Leave-one-subject-out, per-window (CNN-GRU-Attention)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig9_confusion.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- fig 10
def fig_yield_gaps():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 3.2))

    y = S["yield"]
    a1.bar(["possible\n(2 s windows)", "actually saved"],
           [y["windows_possible_2s"], y["windows_saved"]],
           color=["#bdc3c7", C_OURS])
    a1.set_ylabel("windows")
    a1.set_title(f"(a) {y['dropped']} windows lost ({y['dropped_pct']}%)\n"
                 "— default --rate 100 on 66 Hz data", fontsize=9.5)
    for i, v in enumerate([y["windows_possible_2s"], y["windows_saved"]]):
        a1.text(i, v + 6, str(v), ha="center", fontsize=9)

    gaps = []
    for f in FILES:
        t, _ = load_amp(os.path.join(PILOT, f["file"]))
        gaps.append(np.diff(t) * 1e3)
    g = np.concatenate(gaps)
    a2.hist(g, bins=np.logspace(0, np.log10(g.max()), 60), color=C_OURS, alpha=.85)
    a2.set_xscale("log"); a2.set_yscale("log")
    a2.axvline(np.median(g), c="k", ls="--", lw=1.2)
    a2.text(np.median(g) * 1.15, a2.get_ylim()[1] * .3,
            f"median {np.median(g):.0f} ms", fontsize=7.5)
    a2.axvline(1000 / 100, c="#27ae60", ls=":", lw=1.4)
    a2.set_xlabel("inter-packet gap (ms, log)")
    a2.set_ylabel("count (log)")
    a2.set_title(f"(b) Timing jitter — worst gap {g.max():.0f} ms\n"
                 "(= 23% of a 2 s window interpolated)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig10_yield.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_rate_vs_datasets();      print("fig1 rate")
    fig_rate_stability();        print("fig2 stability")
    fig_amplitude_traces();      print("fig3 traces")
    acc = fig_motion_energy();   print(f"fig4 energy (1-feature acc {acc:.3f})")
    cr = fig_doppler();          print(f"fig5 doppler (crossover {cr:.1f} Hz)")
    fig_redundancy();            print("fig6 redundancy")
    fig_window_heatmaps();       print("fig7 windows")
    fig_scale_comparison();      print("fig8 scale")
    fig_confusion();             print("fig9 confusion")
    fig_yield_gaps();            print("fig10 yield")
    print("\nfigures ->", OUT)
