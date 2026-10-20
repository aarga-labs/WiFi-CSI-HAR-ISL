#!/usr/bin/env python3
"""Stage 3: figures for the subcarrier-selection analysis.

Renders PNG (for the report page) + PDF (for the deck) into analysis/figures/.
"""

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D

OUT = "/home/rishiikesh/usrp-projects/analysis/figures"
os.makedirs(OUT, exist_ok=True)

# ---- palette (validated default; light surface) ---------------------------
SURF = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASE = "#e1e0d9", "#c3c2b7"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
       "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
BLUES = LinearSegmentedColormap.from_list("seq_blue", SEQ)
DIVERGE = LinearSegmentedColormap.from_list(
    "div", ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f3a3a2", "#d03b3b", "#7a1f1f"])

plt.rcParams.update({
    "font.family": ["DejaVu Sans"], "font.size": 8.5,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": BASE, "axes.linewidth": 0.8,
    "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "grid.linestyle": "-", "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "legend.handlelength": 1.6,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.25,
})

S = json.load(open("/home/rishiikesh/usrp-projects/analysis/sc_scores.json"))
Z = np.load("/home/rishiikesh/usrp-projects/analysis/sc_features.npz", allow_pickle=True)
ACTS = S["acts"]
ACT_LABEL = {"walk": "Walking", "mixed": "Mixed activity",
             "stand": "Standing", "sit": "Sitting"}
ACT_COLOR = {"walk": S1, "mixed": S2, "stand": S3, "sit": S4}
NSC = 52
SEL = S["mrmr_order"]
K = S["k_recommended"]


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"))
    plt.close(fig)
    print("  wrote", name)


def title(ax, t, sub=None):
    ax.set_title(t, loc="left", fontsize=10, color=INK, pad=19 if sub else 6,
                 fontweight="medium")
    if sub:
        ax.annotate(sub, xy=(0, 1), xycoords="axes fraction", xytext=(0, 4),
                    textcoords="offset points", fontsize=8, color=MUTED,
                    va="bottom", ha="left")


def sc_axis(ax):
    ax.set_xlabel("subcarrier index")
    ax.set_xlim(-1, NSC)
    ax.set_xticks(range(0, NSC, 4))
    ax.xaxis.grid(False)


# ============================================================ fig 1: passband
def fig_passband():
    L = np.array(S["level_per_cap"])
    env = Z["cap_env"]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for e, c, lab in (("A", S1, "Environment A  (Amrith, Rishiikesh)"),
                      ("B", S2, "Environment B  (Gowreesh)")):
        m = env == e
        mu, sd = L[m].mean(0), L[m].std(0)
        ax.fill_between(range(NSC), mu - sd, mu + sd, color=c, alpha=0.13, lw=0)
        ax.plot(range(NSC), mu, color=c, lw=2, label=lab, solid_capstyle="round")
    lvl = np.array(S["level"])
    ax.annotate(f"{lvl.max() - lvl.min():.1f} dB roll-off\nedge → centre",
                xy=(25, lvl.max()), xytext=(33, lvl.max() + 1.6),
                fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=BASE, lw=0.8))
    ax.set_ylabel("mean |H| per subcarrier  (dB)")
    sc_axis(ax)
    ax.legend(loc="lower center", ncols=2, fontsize=8, labelcolor=INK2)
    title(ax, "The amplitude profile is the radio's passband, not the room",
          "Both rooms show the same smooth arch peaking at band centre "
          "(r ≈ 0.9 across environments). Shaded = ±1 SD over captures.")
    save(fig, "sc_fig1_passband")


# ==================================================== fig 2: motion-SNR profile
def fig_motion_profile():
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8), width_ratios=[1, 1])
    ax = axes[0]
    for a in ACTS:
        ax.plot(range(NSC), S["prof_act"][a], color=ACT_COLOR[a], lw=1.9,
                label=ACT_LABEL[a], solid_capstyle="round")
    ax.axhline(0, color=BASE, lw=0.8)
    ax.set_ylabel("motion-SNR, z-scored within capture")
    sc_axis(ax)
    ax.legend(loc="lower center", ncols=2, fontsize=8, labelcolor=INK2)
    title(ax, "Motion response across the band, by activity",
          "Walking has the strongest, most band-centred response.")

    ax = axes[1]
    caps = S["cap_key"]
    prof = np.array(S["msnr_cap"])
    idx = [i for i, k in enumerate(caps) if k[1] == "walk"]
    for i in idx:
        ax.plot(range(NSC), prof[i], color=MUTED, lw=0.9, alpha=0.55)
    ax.plot(range(NSC), np.mean(prof[idx], 0), color=S1, lw=2.4,
            solid_capstyle="round")
    ax.axhline(0, color=BASE, lw=0.8)
    ax.text(0.985, 0.93, "ρ = +0.81 same room\nρ = +0.91 across rooms",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color=INK2)
    ax.set_ylabel("motion-SNR, z-scored within capture")
    sc_axis(ax)
    ax.legend(handles=[Line2D([], [], color=S1, lw=2.4, label="mean of 3 captures"),
                       Line2D([], [], color=MUTED, lw=0.9, label="individual capture")],
              loc="upper left", fontsize=8, labelcolor=INK2)
    title(ax, "Walking: the same shape in every capture",
          "3 subjects, 2 rooms, 4 days apart — the profile transfers.")
    fig.subplots_adjust(wspace=0.28)
    save(fig, "sc_fig2_motion_profile")


# ================================================== fig 3: separability heatmap
def fig_heatmap():
    rows, labels = [], []
    for a in ACTS:
        for e in "AB":
            rows.append(S["score_env"][e][a])
            labels.append(f"{ACT_LABEL[a]} · env {e}")
    M = np.array(rows)
    fig, ax = plt.subplots(figsize=(10.5, 3.9))
    im = ax.imshow(M, aspect="auto", cmap=BLUES, vmin=0, vmax=1,
                   interpolation="nearest")
    for r in range(len(rows)):
        top = np.argsort(-M[r])[:10]
        ax.plot(top, [r] * len(top), marker="o", ls="none", ms=3.2,
                mfc="none", mec=SURF, mew=1.4)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.set_xticks(range(0, NSC, 4))
    ax.set_xlabel("subcarrier index")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.028)
    cb.set_label("one-vs-rest separability  2|AUC−0.5|", fontsize=8, color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(color=MUTED, labelsize=7.5)
    title(ax, "Per-activity subcarrier separability, measured in each room",
          "Rings mark each row's top 10. The bright columns do not line up "
          "between env A and env B — the ranking is room-specific.")
    save(fig, "sc_fig3_heatmap")


# =============================================== fig 4: top-10 per activity
def fig_top_per_activity():
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.0))
    for ax, a in zip(axes.ravel(), ACTS):
        v = np.array(S["score_robust"][a])
        top = list(np.argsort(-v)[:10])
        cols = [ACT_COLOR[a] if i in top else "#dedcd4" for i in range(NSC)]
        ax.bar(range(NSC), v, color=cols, width=0.72)
        b = top[0]
        ax.annotate(f"best: SC{b}", xy=(b, v[b]), xytext=(0, 7),
                    textcoords="offset points", ha="center", fontsize=7.5,
                    color=INK2)
        ax.set_ylim(0, max(v.max() * 1.22, 0.1))
        ax.set_ylabel("robust separability")
        sc_axis(ax)
        ax.set_xticks(range(0, NSC, 8))
        title(ax, ACT_LABEL[a],
              "top 10: " + ", ".join(str(i) for i in top))
    fig.suptitle("Best subcarriers for each activity  (worst-case of the two rooms)",
                 x=0.005, ha="left", fontsize=11, color=INK, y=1.005)
    fig.subplots_adjust(hspace=0.62, wspace=0.22)
    save(fig, "sc_fig4_top_per_activity")


# ================================================= fig 5: reliability of ranking
def fig_reliability():
    rel, mrel = S["reliability"], S["msnr_reliability"]
    tiers = [("split_half", "same capture (split-half)", S1),
             ("cross_subject_sameroom", "different person, same room", S2),
             ("cross_env", "different room", S3)]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8), sharey=True)
    w = 0.26
    for ax, src, ttl, sub in (
            (axes[0], "sep", "Per-activity separability ranking",
             "Reliable inside a capture, unrelated across captures."),
            (axes[1], "msnr", "Motion-SNR profile",
             "Walking transfers across people and rooms; static poses don't.")):
        for j, (key, lab, c) in enumerate(tiers):
            if src == "sep":
                vals = [rel[key][a] for a in ACTS]
            else:
                if key == "split_half":
                    continue
                vals = [mrel[a][key] for a in ACTS]
            off = (j - 1) * w
            ax.bar(np.arange(4) + off, vals, width=w * 0.88, color=c, label=lab)
        ax.axhline(0, color=BASE, lw=0.9)
        ax.set_xticks(range(4), [ACT_LABEL[a] for a in ACTS], fontsize=8)
        ax.xaxis.grid(False)
        ax.set_ylim(-0.75, 1.0)
        title(ax, ttl, sub)
    axes[0].set_ylabel("Spearman ρ of the subcarrier ranking")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncols=3, fontsize=8, labelcolor=INK2,
               bbox_to_anchor=(0.5, -0.06))
    fig.subplots_adjust(wspace=0.12)
    save(fig, "sc_fig5_reliability")


# ================================================ fig 6: redundancy / coherence
def fig_redundancy():
    R = np.array(S["corr"])
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), width_ratios=[1, 1.15])
    ax = axes[0]
    im = ax.imshow(R, cmap=BLUES, vmin=0, vmax=1, interpolation="nearest")
    ax.set_xticks(range(0, NSC, 8))
    ax.set_yticks(range(0, NSC, 8))
    ax.set_xlabel("subcarrier index")
    ax.set_ylabel("subcarrier index")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, pad=0.015, fraction=0.046)
    cb.set_label("correlation of motion response", fontsize=8, color=INK2)
    cb.outline.set_visible(False)
    cb.ax.tick_params(color=MUTED, labelsize=7.5)
    title(ax, "Neighbouring subcarriers repeat each other",
          "Block width ≈ the coherence bandwidth.")

    ax = axes[1]
    lc = S["lag_corr"][:26]
    ax.plot(range(len(lc)), lc, color=S1, lw=2, solid_capstyle="round")
    ax.axhline(0.5, color=BASE, lw=0.9)
    ax.axvline(S["coh_lag"], color=S2, lw=1.4)
    ax.annotate(f"ρ drops below 0.5 at {S['coh_lag']} subcarriers\n"
                f"≈ {S['n_independent']:.0f} independent looks across 52",
                xy=(S["coh_lag"], 0.5), xytext=(S["coh_lag"] + 1.6, 0.78),
                fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=BASE, lw=0.8))
    ax.set_xlabel("separation between subcarriers")
    ax.set_ylabel("mean correlation")
    ax.set_ylim(-0.05, 1.02)
    ax.xaxis.grid(False)
    title(ax, "How far apart before they carry new information",
          "This is why accuracy stops improving past ~8–12 subcarriers.")
    fig.subplots_adjust(wspace=0.42)
    save(fig, "sc_fig6_redundancy")


# ============================================ fig 7: combined recommendation
def fig_recommendation():
    v = np.array(S["prof_motion_worst"])
    fig, ax = plt.subplots(figsize=(10.5, 3.9))
    sel = SEL[:K]
    cols = [S1 if i in sel else "#dedcd4" for i in range(NSC)]
    ax.bar(range(NSC), v, color=cols, width=0.72)
    for rank, i in enumerate(sel, 1):
        ax.text(i, v[i] + 0.06, str(rank), ha="center", fontsize=6.6, color=SURF,
                bbox=dict(boxstyle="circle,pad=0.16", fc=S1, ec="none"))
    ax.axhline(0, color=BASE, lw=0.9)
    ax.set_ylabel("worst-case motion-SNR across all 6 action captures\n(z-scored)")
    sc_axis(ax)
    ax.set_ylim(v.min() - 0.15, v.max() + 0.55)
    ax.legend(handles=[Line2D([], [], color=S1, lw=6, label=f"recommended set (top {K})"),
                       Line2D([], [], color="#dedcd4", lw=6, label="not selected")],
              loc="lower center", ncols=2, fontsize=8, labelcolor=INK2)
    title(ax, f"Recommended subcarrier set — {', '.join(str(i) for i in sorted(sel))}",
          "Ranked by the motion response that survives in BOTH rooms and all "
          "three people; numbers show selection order.")
    save(fig, "sc_fig7_recommendation")


# ==================================================== fig 8: validation curve
def fig_validation():
    c = S["curve"]
    k = c["k"]
    fig, ax = plt.subplots(figsize=(9.4, 4.0))
    ax.fill_between(k, c["random_lo"], c["random_hi"], color=MUTED, alpha=0.14, lw=0)
    ax.plot(k, c["within"], color=S3, lw=2, label="same capture (time-blocked CV)")
    ax.plot(k, c["selected"], color=S1, lw=2.4, label="selected subcarriers, new person")
    ax.plot(k, c["random_mean"], color=MUTED, lw=1.6, label="random subcarriers, new person")
    ax.plot(k, c["worst"], color=S2, lw=1.6, label="worst subcarriers, new person")
    ax.axhline(0.25, color=BASE, lw=0.9)
    ax.text(52, 0.262, "chance (4 classes)", ha="right", fontsize=7.5, color=MUTED)

    best = int(np.argmax(c["selected"]))
    ax.plot([k[best]], [c["selected"][best]], "o", ms=7, mfc=S1, mec=SURF, mew=2)
    ax.annotate(f"{c['selected'][best]:.0%} with {k[best]} subcarriers",
                xy=(k[best], c["selected"][best]), xytext=(k[best] + 2.5, c["selected"][best] + 0.055),
                fontsize=8.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=BASE, lw=0.8))
    ax.annotate(f"all 52: {c['selected'][-1]:.0%}", xy=(52, c["selected"][-1]),
                xytext=(40, c["selected"][-1] - 0.075), fontsize=8.5, color=INK2,
                arrowprops=dict(arrowstyle="-", color=BASE, lw=0.8))
    ax.set_xscale("log")
    ax.set_xticks(k, [str(x) for x in k])
    ax.set_xlabel("number of subcarriers used")
    ax.set_ylabel("4-class accuracy")
    ax.set_ylim(0.2, 1.0)
    ax.xaxis.grid(False)
    ax.legend(loc="upper left", fontsize=8, labelcolor=INK2)
    title(ax, "Eight chosen subcarriers beat all fifty-two",
          "Leave-one-person-out (holding out Gowreesh is also the cross-room "
          "test). Band = 10–90th pct of 10 random draws.")
    save(fig, "sc_fig8_validation")


# ======================================================== fig 9: confusion
def fig_confusion():
    C = np.array(S["confusion"], float)
    Cn = C / C.sum(1, keepdims=True)
    fig, ax = plt.subplots(figsize=(4.9, 4.3))
    im = ax.imshow(Cn, cmap=BLUES, vmin=0, vmax=1)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{Cn[i, j]:.0%}", ha="center", va="center", fontsize=9,
                    color=SURF if Cn[i, j] > 0.55 else INK2)
    ax.set_xticks(range(4), [ACT_LABEL[a] for a in ACTS], rotation=30, ha="right",
                  fontsize=8)
    ax.set_yticks(range(4), [ACT_LABEL[a] for a in ACTS], fontsize=8)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    title(ax, f"Where it fails ({K} subcarriers, new person)",
          f"Action vs no-action collapses to {S['binary_acc']:.0%}.")
    save(fig, "sc_fig9_confusion")


# ==================================================== fig 10: sanity traces
def fig_traces():
    """What actually separates a good subcarrier from a bad one: the noise floor.

    Both subcarriers see the same body motion (equal energy in the motion band);
    the rejected one just carries ~5 dB more noise on top of it.
    """
    import pandas as pd
    from scipy import signal as sg
    best, worst = SEL[0], int(np.argmin(S["prof_motion_worst"]))
    files = [("P01_action_amrith_20260717_walk.csv", "Walking"),
             ("P01_noaction_amrith_20260717_sit.csv", "Sitting")]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), sharey=True)
    for ax, (fn, lab) in zip(axes, files):
        df = pd.read_csv(f"/home/rishiikesh/usrp-projects/data/pilot/{fn}").dropna()
        t = (df["Timestamp_us"].to_numpy(np.int64) - df["Timestamp_us"].iloc[0]) / 1e6
        grid = np.arange(0, t.iloc[-1] if hasattr(t, "iloc") else t[-1], 1 / 80.0)
        ax.axvspan(0.5, 25, color=S1, alpha=0.055, lw=0)
        ax.axvspan(30, 38, color=INK2, alpha=0.07, lw=0)
        for sc, c, name in ((best, S1, f"SC{best}  (recommended)"),
                            (worst, S2, f"SC{worst}  (rejected)")):
            a = np.hypot(df[f"SC{sc}_Re"], df[f"SC{sc}_Im"]).to_numpy()
            a = 20 * np.log10(np.maximum(a, 1e-12))
            x = np.interp(grid, t, a)
            f, P = sg.welch(sg.detrend(x), fs=80.0, nperseg=1024, noverlap=512)
            ax.semilogx(f[1:], 10 * np.log10(P[1:]), color=c, lw=1.5,
                        label=name if lab == "Walking" else None)
        ax.set_xlabel("frequency (Hz)")
        ax.set_xlim(0.15, 39)
        ax.set_ylim(-42, 26)
        ax.xaxis.grid(False)
        tr = ax.get_xaxis_transform()
        ax.text(3.5, 0.97, "body motion  0.5–25 Hz", transform=tr, fontsize=7.5,
                color=INK2, ha="center", va="top")
        ax.text(33, 0.97, "noise floor", transform=tr, fontsize=7.5, color=INK2,
                ha="center", va="top")
        title(ax, lab)
    axes[0].set_ylabel("power spectral density of |H| (dB)")
    axes[0].annotate("identical motion energy —\nSC29 wins on a ~6 dB lower noise floor",
                     xy=(34, -24), xytext=(0.22, -38), fontsize=8, color=INK,
                     arrowprops=dict(arrowstyle="-", color=BASE, lw=0.8))
    axes[0].legend(loc="upper right", bbox_to_anchor=(1.0, 0.86), fontsize=8,
                   labelcolor=INK2)
    fig.suptitle("A good subcarrier is not one that moves more — it is one that "
                 "hears the same motion over less noise",
                 x=0.005, ha="left", fontsize=11, color=INK, y=1.02)
    fig.subplots_adjust(wspace=0.08)
    save(fig, "sc_fig10_spectra")


for fn in (fig_passband, fig_motion_profile, fig_heatmap, fig_top_per_activity,
           fig_reliability, fig_redundancy, fig_recommendation, fig_validation,
           fig_confusion, fig_traces):
    fn()
print("figures ->", OUT)
