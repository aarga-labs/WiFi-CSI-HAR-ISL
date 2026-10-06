"""Handcrafted motion features (B0 scalar, B1 vector) for windows x [N, 52, T]."""
import numpy as np
from scipy.signal import welch
from scipy.stats import kurtosis
from preprocess import FS

BANDS = [(0.3, 1), (1, 2), (2, 4), (4, 8), (8, 16)]
N_ENV = 20


def motion_energy(X):
    """B0: one scalar per window = log mean squared high-passed amplitude."""
    return np.log(np.mean(X ** 2, axis=(1, 2)) + 1e-12)


def _one(x):
    C, T = x.shape
    f = {}
    sc_std = x.std(axis=1)
    f["log_e"] = np.log(np.mean(x ** 2) + 1e-12)
    f["log_sc_std_max"] = np.log(sc_std.max() + 1e-9)
    f["sc_std_cv"] = sc_std.std() / (sc_std.mean() + 1e-9)
    f["log_vel"] = np.log(np.mean(np.abs(np.diff(x, axis=1))) + 1e-12)

    # energy envelope over time: shape is normalised, so it is level-free
    env = (x ** 2).mean(0).reshape(N_ENV, -1).mean(1)
    p = env / (env.sum() + 1e-12)
    for i, v in enumerate(p):
        f[f"env{i}"] = v
    tt = np.arange(N_ENV)
    f["env_peak"] = env.argmax() / N_ENV
    f["env_centroid"] = (p * tt).sum() / N_ENV
    f["env_spread"] = np.sqrt((p * (tt - (p * tt).sum()) ** 2).sum()) / N_ENV
    f["env_dur50"] = (env > 0.5 * env.max()).mean()
    f["env_dur20"] = (env > 0.2 * env.max()).mean()

    # per-window PCA across subcarriers
    xc = x - x.mean(1, keepdims=True)
    u, s, vt = np.linalg.svd(xc, full_matrices=False)
    ev = s ** 2 / (s ** 2).sum()
    f["pc1_ratio"], f["pc2_ratio"], f["pc3_ratio"] = ev[:3]
    corr = np.corrcoef(x)
    f["sc_corr_mean"] = np.nanmean(corr[np.triu_indices(C, 1)])
    for k in range(3):
        pc = vt[k] * s[k]
        fr, psd = welch(pc, fs=FS, nperseg=128)
        tot = psd[(fr >= 0.3) & (fr <= 16)].sum() + 1e-12
        for lo, hi in BANDS:
            f[f"pc{k}_b{lo}-{hi}"] = psd[(fr >= lo) & (fr < hi)].sum() / tot
        f[f"pc{k}_fcent"] = (fr * psd).sum() / (psd.sum() + 1e-12)
        f[f"pc{k}_kurt"] = kurtosis(pc)
        f[f"pc{k}_zcr"] = np.mean(np.abs(np.diff(np.sign(pc)))) / 2
        # subcarrier loading shape: how spread the motion is across the band
        load = np.abs(u[:, k])
        f[f"pc{k}_load_cent"] = (load * np.arange(C)).sum() / (load.sum() * C)
    return f


def handcrafted(X):
    rows = [_one(x) for x in X]
    names = list(rows[0])
    return np.array([[r[n] for n in names] for r in rows], np.float32), names
