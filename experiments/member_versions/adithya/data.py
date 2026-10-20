"""Loading kept Phase-1 takes: CSI amplitude (cached as .npz) and label CSVs.

The recorded data under phase1/ is only ever read, never written.
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
# dataset folder (CSI CSVs, labels/, session_log.csv); default: a phase1/ folder next to this repo
DATA = Path(os.environ.get("CSI_DATA", ROOT.parent / "phase1"))
CACHE = ROOT / "cache"
N_SC = 52

# session_log part name -> label-file mode name
PART2MODE = {"actions": "actions", "signs_standing": "signs", "signs_seated": "signs",
             "scripts": "script", "baseline": "baseline", "empty": "empty"}


def kept_takes():
    """One row per kept take: pid, part, rx_gain, csi_file, label_file (None for DAY empty)."""
    log = pd.read_csv(DATA / "session_log.csv")
    log = log[log.status == "kept"].copy()
    log["label_file"] = [f if isinstance(f, str) and f != "-" else None for f in log.label_file]
    # newest kept take wins if a part was re-recorded
    log = log.sort_values(["date", "time"]).drop_duplicates(["pid", "part"], keep="last")
    return log[["pid", "part", "rx_gain", "csi_file", "label_file"]].reset_index(drop=True)


def load_csi(csi_file):
    """Returns (t_us int64 [N], amp float32 [N, 52]). Amplitude only: no clock sync -> phase unusable."""
    CACHE.mkdir(exist_ok=True)
    cache = CACHE / (Path(csi_file).stem + ".npz")
    if cache.exists():
        z = np.load(cache)
        return z["t"], z["amp"]
    df = pd.read_csv(DATA / csi_file, engine="pyarrow")
    if (df.Channel != 1).any():
        raise ValueError(f"{csi_file}: non channel-1 rows")
    re = df[[f"SC{i}_Re" for i in range(N_SC)]].to_numpy(np.float32)
    im = df[[f"SC{i}_Im" for i in range(N_SC)]].to_numpy(np.float32)
    t = df.Timestamp_us.to_numpy(np.int64)
    amp = np.hypot(re, im)
    np.savez(cache, t=t, amp=amp)
    return t, amp


def load_labels(label_file):
    if not isinstance(label_file, str):  # pandas 3 turns None into NaN
        return None
    return pd.read_csv(DATA / "labels" / label_file)


if __name__ == "__main__":
    for r in kept_takes().itertuples():
        t, a = load_csi(r.csi_file)
        lab = load_labels(r.label_file)
        dur = (t[-1] - t[0]) / 1e6
        msg = f"{r.pid:4s} {r.part:15s} gain={r.rx_gain:2d} rows={len(t):7d} dur={dur:7.1f}s amp_med={np.median(a):.4f}"
        if lab is not None:
            ev = lab[lab.type.isin(["activity", "sign", "idle"])]
            covered = ((ev.t_start_us >= t[0]) & (ev.t_end_us <= t[-1])).sum()
            msg += f" events={len(ev)} covered={covered}"
        print(msg)
