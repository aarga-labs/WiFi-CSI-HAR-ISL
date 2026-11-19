#!/usr/bin/env python3
"""
Turn CSI amplitude windows into feature vectors, and into recurrence plots.

Two representations, for two purposes:

* `window_features()` -> a compact statistical + spectral vector, for the
  classical baseline. Runs in seconds on a laptop with no GPU, and is the
  control that tells you whether a deep model is earning its complexity.

* `recurrence_plot()` -> the 2D image representation the existing HAR pipeline
  (Action_NoAction_imgfi.ipynb) feeds to ResNet-18.

The spectral features matter more than they might look. Whole-body motion puts
its energy low (gait is ~1-2 Hz); hand gestures are faster and sparser. Band
energies are therefore close to the physical difference between the two
classes, which is why the baseline is a genuine contender and not a straw man.
"""

import numpy as np

TARGET_RATE_HZ = 50

# Bands chosen against what the July analysis found in this rig's own data:
# all class-discriminative energy sits below 18 Hz.
BANDS = [(0.0, 2.0), (2.0, 5.0), (5.0, 10.0), (10.0, 18.0)]


def window_features(w, rate_hz=TARGET_RATE_HZ):
    """(T, S) amplitude window -> 1D feature vector."""
    w = np.asarray(w, dtype=np.float64)
    T, S = w.shape

    mean = w.mean(axis=0)
    std = w.std(axis=0)
    rng = np.percentile(w, 90, axis=0) - np.percentile(w, 10, axis=0)
    # Mean absolute first difference: how fast the channel is changing.
    vel = np.abs(np.diff(w, axis=0)).mean(axis=0)

    # Per-subcarrier band energy of the de-meaned signal.
    centred = w - mean
    spec = np.abs(np.fft.rfft(centred, axis=0)) ** 2
    freqs = np.fft.rfftfreq(T, d=1.0 / rate_hz)
    total = spec.sum(axis=0) + 1e-12

    band_feats = []
    for lo, hi in BANDS:
        sel = (freqs >= lo) & (freqs < hi)
        band_feats.append(spec[sel].sum(axis=0) / total)   # normalised share

    return np.concatenate([mean, std, rng, vel] + band_feats).astype(np.float32)


def batch_features(X, rate_hz=TARGET_RATE_HZ):
    """(N, T, S) -> (N, F)."""
    return np.stack([window_features(w, rate_hz) for w in X])


def feature_names(n_sub=52):
    names = []
    for tag in ("mean", "std", "p90p10", "vel"):
        names += [f"{tag}_sc{i}" for i in range(n_sub)]
    for lo, hi in BANDS:
        names += [f"band{lo:g}-{hi:g}Hz_sc{i}" for i in range(n_sub)]
    return names


def recurrence_plot(series, size=64, threshold=None):
    """
    1D series -> (size, size) recurrence plot in [0, 1].

    Downsamples to `size` points first, so the output is a fixed shape
    regardless of window length, then takes pairwise absolute distances.
    With no threshold this is an unthresholded (continuous) recurrence plot,
    which keeps more information than a binary one and is what the existing
    pipeline uses.
    """
    s = np.asarray(series, dtype=np.float64).ravel()
    if s.size != size:
        s = np.interp(np.linspace(0, s.size - 1, size), np.arange(s.size), s)

    d = np.abs(s[:, None] - s[None, :])
    m = d.max()
    if m > 0:
        d = d / m
    if threshold is not None:
        d = (d < threshold).astype(np.float32)
    return d.astype(np.float32)


def rank_subcarriers(X, y, top_k=6):
    """
    Rank subcarriers by how well their temporal variance separates the classes.

    Fisher-style score: between-class separation of the per-window temporal
    std, over within-class spread. Cheap, and it reproduces the "optimal
    subcarrier selection" idea already in the slides without needing a model.
    Returns indices, best first.
    """
    labels = np.unique(y)
    if labels.size != 2:
        raise ValueError("rank_subcarriers expects two classes")

    v = X.std(axis=1)                      # (N, S) temporal std per subcarrier
    a, b = v[y == labels[0]], v[y == labels[1]]
    num = (a.mean(axis=0) - b.mean(axis=0)) ** 2
    den = a.var(axis=0) + b.var(axis=0) + 1e-12
    score = num / den
    return np.argsort(score)[::-1][:top_k], score
