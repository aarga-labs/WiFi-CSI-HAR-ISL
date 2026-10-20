"""CSI amplitude -> uniform 100 Hz, despiked, log, high-passed (static level removed).

Static removal matters: every sign comes from a signs file and every action from an
actions file, and the static per-subcarrier level differs per file (gain, posture, day).
High-passing removes that level so models must use motion, not file identity.
"""
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import butter, sosfiltfilt

FS = 100.0          # target rate (Hz); raw is 85-131 rows/s, irregular
GAP_S = 0.10        # grid points farther than this from a real packet are gaps
HP_HZ = 0.3         # high-pass cut-off for static removal
LP_HZ = 20.0        # low-pass cut-off (body/hand motion is well below this)


def despike(amp, k=7, n_mad=5.0):
    """Clip decode glitches: values > n_mad robust sigmas from a running median."""
    med = median_filter(amp, size=(k, 1), mode="nearest")
    dev = amp - med
    mad = np.median(np.abs(dev), axis=0, keepdims=True) * 1.4826 + 1e-12
    return np.where(np.abs(dev) > n_mad * mad, med, amp)


def resample(t_us, x, fs=FS):
    """Linear interpolation onto a uniform grid. Returns grid times (us), data, gap mask."""
    t = (t_us - t_us[0]) / 1e6
    grid = np.arange(0.0, t[-1], 1.0 / fs)
    out = np.empty((len(grid), x.shape[1]), np.float32)
    for c in range(x.shape[1]):
        out[:, c] = np.interp(grid, t, x[:, c])
    # distance from each grid point to its nearest real packet
    idx = np.clip(np.searchsorted(t, grid), 1, len(t) - 1)
    near = np.minimum(np.abs(t[idx] - grid), np.abs(t[idx - 1] - grid))
    return t_us[0] + (grid * 1e6).astype(np.int64), out, near > GAP_S


def preprocess(t_us, amp):
    """Returns dict with grid times, high-passed log-amplitude [T, 52], raw log-amp, gap mask."""
    x = np.log(despike(amp) + 1e-4)
    tg, xg, gap = resample(t_us, x)
    sos_bp = butter(2, [HP_HZ, LP_HZ], btype="band", fs=FS, output="sos")
    hp = sosfiltfilt(sos_bp, xg, axis=0).astype(np.float32)
    floor = noise_floor(hp)
    return {"t": tg, "x": hp / np.sqrt(floor), "logamp": xg, "gap": gap, "floor": floor}


def noise_floor(hp, pct=5):
    """Label-free per-recording noise level: low percentile of 1 s block energy.
    Dividing by it equalises SNR differences between files (e.g. P01 actions at RX gain 16)."""
    n = int(FS)
    e = (hp[:len(hp) // n * n] ** 2).mean(1).reshape(-1, n).mean(1)
    return float(np.percentile(e, pct))


def idx_at(t_grid, t_us):
    return int(np.searchsorted(t_grid, t_us))
