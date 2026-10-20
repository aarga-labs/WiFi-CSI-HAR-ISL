#!/usr/bin/env python3
"""Stage 1: per-window, per-subcarrier feature extraction for the pilot captures.

Every capture is resampled onto a common uniform grid, de-spiked, converted to
dB amplitude, then cut into overlapping windows. For each (window, subcarrier)
we store a small set of *dynamics* features -- deliberately no absolute level,
so nothing can separate classes by per-capture gain alone.

Output: analysis/sc_features.npz (consumed by sc_select.py / sc_figures.py)
"""

import glob
import os

import numpy as np
import pandas as pd
from scipy import signal

PILOT = "/home/rishiikesh/usrp-projects/data/pilot"
OUT = "/home/rishiikesh/usrp-projects/analysis"

FS = 80.0            # common resample grid (Hz); all captures are 65-90 Hz
WIN_S = 2.0          # window length (s)
HOP_S = 1.0          # 50 % overlap
NSC = 52
FC = 2.462e9         # channel 11
C = 3e8
HZ_PER_MS = 2 * FC / C   # 16.41 Hz of Doppler per m/s radial speed

# analysis bands (Hz) on the dB-amplitude series
B_SLOW = (0.15, 0.5)   # posture sway / breathing
B_GAIT = (0.5, 4.0)    # torso + gait fundamental
B_LIMB = (4.0, 12.0)   # limb swing
B_FAST = (12.0, 25.0)  # fast limb / hand
B_NOISE = (30.0, 38.0) # above any human Doppler -> hardware + phase noise

ENV = {"amrith": "A", "rishiikesh": "A", "gowreesh": "B"}
FEATS = ["sigma", "roughness", "p_gait", "p_limb", "p_fast", "msnr", "centroid"]


def parse(path):
    # P01_<cls>_<subject>_<date>_<take>.csv
    p = os.path.basename(path)[:-4].split("_")
    cls, subject, take = p[1], p[2], p[4]
    # activity label: walk / mixed come from the action captures, sit / stand
    # from the noaction ones -- the take field already names the activity
    return dict(cls=cls, subject=subject, date=p[3], activity=take,
                env=ENV[subject])


def load_uniform(path):
    """CSV -> (dB amplitude on a uniform FS grid, gap fraction)."""
    df = pd.read_csv(path)
    cols = [f"SC{i}_Re" for i in range(NSC)] + [f"SC{i}_Im" for i in range(NSC)]
    df = df.dropna(subset=cols + ["Timestamp_us"])
    t = df["Timestamp_us"].to_numpy(np.int64)
    re = df[[f"SC{i}_Re" for i in range(NSC)]].to_numpy(float)
    im = df[[f"SC{i}_Im" for i in range(NSC)]].to_numpy(float)
    o = np.argsort(t)
    t, re, im = t[o], re[o], im[o]
    t = (t - t[0]) / 1e6

    amp = np.hypot(re, im)
    amp_db = 20 * np.log10(np.maximum(amp, 1e-12))

    # de-spike: replace samples >6 MAD from a 5-tap running median
    med = signal.medfilt(amp_db, kernel_size=(5, 1))
    resid = amp_db - med
    mad = np.median(np.abs(resid - np.median(resid, 0)), 0) + 1e-9
    spike = np.abs(resid) > 6 * 1.4826 * mad
    amp_db = np.where(spike, med, amp_db)

    grid = np.arange(0, t[-1], 1.0 / FS)
    out = np.empty((len(grid), NSC))
    for k in range(NSC):
        out[:, k] = np.interp(grid, t, amp_db[:, k])

    # fraction of grid time covered by an inter-arrival gap > 2 grid steps
    dt = np.diff(t)
    gap_frac = dt[dt > 2.0 / FS].sum() / t[-1]
    return out, grid, gap_frac, spike.mean()


def band_power(f, P, lo, hi):
    m = (f >= lo) & (f < hi)
    return P[m].sum(axis=0) if P.ndim > 1 else P[m].sum()


def window_features(x):
    """x: (nsamp, NSC) dB block -> (len(FEATS), NSC)."""
    xd = signal.detrend(x, axis=0, type="linear")
    n = len(xd)
    f, P = signal.welch(xd, fs=FS, nperseg=n, noverlap=0,
                        window="hann", axis=0, scaling="density")

    p_slow = band_power(f, P, *B_SLOW)
    p_gait = band_power(f, P, *B_GAIT)
    p_limb = band_power(f, P, *B_LIMB)
    p_fast = band_power(f, P, *B_FAST)
    p_noise = band_power(f, P, *B_NOISE)
    p_mot = p_gait + p_limb + p_fast

    m = (f >= B_GAIT[0]) & (f < B_FAST[1])
    centroid = (f[m, None] * P[m]).sum(0) / np.maximum(P[m].sum(0), 1e-30)

    eps = 1e-12
    return np.vstack([
        xd.std(0),                                       # sigma  (dB)
        np.median(np.abs(np.diff(xd, axis=0)), 0),       # roughness (dB/sample)
        10 * np.log10(p_gait + eps),
        10 * np.log10(p_limb + eps),
        10 * np.log10(p_fast + eps),
        10 * np.log10((p_mot + eps) / (p_noise + eps)),  # motion SNR (dB)
        centroid,                                        # Hz
    ]), dict(p_slow=p_slow, p_gait=p_gait, p_limb=p_limb, p_fast=p_fast,
             p_noise=p_noise)


def main():
    paths = sorted(glob.glob(os.path.join(PILOT, "P01_*.csv")))
    nwin = int(WIN_S * FS)
    nhop = int(HOP_S * FS)

    X, meta_act, meta_sub, meta_env, meta_file = [], [], [], [], []
    caps = []

    for fi, path in enumerate(paths):
        m = parse(path)
        xdb, grid, gap_frac, spike_frac = load_uniform(path)

        # capture-level view: level profile + full-record PSD
        level = np.median(xdb, 0)
        xd = signal.detrend(xdb, axis=0, type="linear")
        f, P = signal.welch(xd, fs=FS, nperseg=1024, noverlap=512,
                            window="hann", axis=0)
        cap = dict(**m, file=os.path.basename(path), n=len(xdb),
                   dur=grid[-1], gap_frac=gap_frac, spike_frac=spike_frac,
                   level=level, psd_f=f, psd=P,
                   sigma=xd.std(0),
                   msnr=10 * np.log10(
                       (band_power(f, P, B_GAIT[0], B_FAST[1]) + 1e-12) /
                       (band_power(f, P, *B_NOISE) + 1e-12)))
        caps.append(cap)

        for s in range(0, len(xdb) - nwin + 1, nhop):
            fv, _ = window_features(xdb[s:s + nwin])
            X.append(fv)
            meta_act.append(m["activity"])
            meta_sub.append(m["subject"])
            meta_env.append(m["env"])
            meta_file.append(fi)

        print(f"{os.path.basename(path):52s} env={m['env']} act={m['activity']:6s} "
              f"win={sum(1 for a in meta_file if a == fi):3d} "
              f"gap={gap_frac*100:4.1f}% spike={spike_frac*100:4.2f}%")

    X = np.stack(X)                      # (nwin, nfeat, NSC)
    np.savez_compressed(
        os.path.join(OUT, "sc_features.npz"),
        X=X, feats=np.array(FEATS),
        activity=np.array(meta_act), subject=np.array(meta_sub),
        env=np.array(meta_env), file_idx=np.array(meta_file),
        cap_level=np.stack([c["level"] for c in caps]),
        cap_sigma=np.stack([c["sigma"] for c in caps]),
        cap_msnr=np.stack([c["msnr"] for c in caps]),
        cap_psd=np.stack([c["psd"] for c in caps]),
        psd_f=caps[0]["psd_f"],
        cap_activity=np.array([c["activity"] for c in caps]),
        cap_subject=np.array([c["subject"] for c in caps]),
        cap_env=np.array([c["env"] for c in caps]),
        cap_gapfrac=np.array([c["gap_frac"] for c in caps]),
        cap_dur=np.array([c["dur"] for c in caps]),
        cap_file=np.array([c["file"] for c in caps]),
    )
    print(f"\nX = {X.shape}  (windows, features, subcarriers)")
    print("saved analysis/sc_features.npz")


if __name__ == "__main__":
    main()
