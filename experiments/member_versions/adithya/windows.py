"""Fixed-length windows from the isolated parts (actions, signs, baseline, empty).

Every window is WIN_S long whatever its class, so trial duration (4-6 s actions,
4 s signs) cannot leak the label. Trial windows start PRE_S before the GO cue.
Idle windows come from the still gaps between trials *in the same files*, plus
baseline and empty-room recordings.
"""
import numpy as np
import pandas as pd
from data import kept_takes, load_csi, load_labels, CACHE
from preprocess import preprocess, idx_at, FS

WIN_S = 5.0
PRE_S = 0.5
WIN = int(WIN_S * FS)
MAX_GAP_FRAC = 0.10
LEVEL = []
# routine = actions + the reset/transition motion between action trials (no command)
STATE = {"idle": 0, "activity": 1, "transition": 1, "sign": 2}

ACTIONS = ["walk", "sitstand", "pickup", "lightswitch", "drink",
           "answerphone", "eat", "wipetable", "tvremote", "fall"]
SIGNS = ["HELLO", "THANKYOU", "LAMP", "FAN", "TELEVISION", "COOK", "WATER",
         "HOT", "HUNGRY", "TOILET", "CALL", "HELP", "PAIN", "ACCIDENT"]
FINE = ACTIONS + SIGNS                     # 24 fine classes (idle handled by the state head)
LOOKALIKE = {"sitstand": "PAIN", "pickup": "HELP", "lightswitch": "LAMP", "drink": "WATER",
             "answerphone": "CALL", "eat": "HOT", "wipetable": "FAN", "tvremote": "TELEVISION",
             "fall": "ACCIDENT"}


def _cut(p, t0_us, rows, X, meta, info):
    i0 = idx_at(p["t"], t0_us)
    if i0 < 0 or i0 + WIN > len(p["t"]):
        return False                       # not covered by CSI (e.g. P02 truncation)
    gap = p["gap"][i0:i0 + WIN].mean()
    if gap > MAX_GAP_FRAC:
        return False
    X.append(p["x"][i0:i0 + WIN].T.copy())
    LEVEL.append(p["logamp"][i0:i0 + WIN].mean(0))   # static level, only for the leakage probe
    meta.append({**info, "gap_frac": gap, "t0_us": t0_us})
    return True


def build_isolated():
    X, meta = [], []
    for take in kept_takes().itertuples():
        if take.part == "scripts":
            continue
        t, amp = load_csi(take.csi_file)
        p = preprocess(t, amp)
        base = {"pid": take.pid, "part": take.part, "file": take.csi_file, "rx_gain": take.rx_gain}

        if take.part == "empty":           # whole take, skip 3 s at each end
            s = p["t"][0] + 3e6
            while s + WIN_S * 1e6 < p["t"][-1] - 3e6:
                _cut(p, s, None, X, meta, {**base, "label": "empty", "type": "idle", "posture": "none"})
                s += WIN_S * 1e6
            continue

        lab = load_labels(take.label_file)
        ev = lab[lab.type.isin(["activity", "sign", "idle"])].reset_index(drop=True)
        ev["rep"] = ev.groupby("label").cumcount() + 1

        if take.part == "baseline":        # 60 s still segments -> non-overlapping windows
            for e in ev.itertuples():
                s = e.t_start_us + 1e6
                while s + WIN_S * 1e6 <= e.t_end_us - 1e6:
                    _cut(p, s, None, X, meta, {**base, "label": e.label, "type": "idle", "posture": e.posture})
                    s += WIN_S * 1e6
            continue

        for k, e in enumerate(ev.itertuples()):
            _cut(p, e.t_start_us - PRE_S * 1e6, None, X, meta,
                 {**base, "label": e.label, "type": e.type, "posture": e.posture,
                  "trial": e.trial, "rep": e.rep})
            # gap between this STOP and the next GO (skips the operator breaks).
            # Signs: participants freeze -> idle. Actions: they reset props/position
            # for the next trial (walk back, sit down, get up off the mattress) -> transition.
            if k + 1 < len(ev):
                gap_s = (ev.t_start_us[k + 1] - e.t_end_us) / 1e6
                if WIN_S <= gap_s <= WIN_S + 2.0:
                    s = e.t_end_us + (gap_s - WIN_S) / 2 * 1e6
                    typ = "transition" if take.part == "actions" else "idle"
                    _cut(p, s, None, X, meta, {**base, "label": "between", "type": typ,
                                                "posture": e.posture, "trial": e.trial})
        print(f"{take.pid} {take.part}: {sum(m['file'] == take.csi_file for m in meta)} windows")

    X = np.stack(X).astype(np.float32)
    meta = pd.DataFrame(meta)
    meta["state"] = meta.type.map(STATE)
    meta["fine"] = meta.label.map({c: i for i, c in enumerate(FINE)}).fillna(-1).astype(int)
    np.save(CACHE / "iso_X.npy", X)
    np.save(CACHE / "iso_level.npy", np.stack(LEVEL).astype(np.float32))
    meta.to_csv(CACHE / "iso_meta.csv", index=False)
    return X, meta


def load_isolated():
    if not (CACHE / "iso_X.npy").exists():
        return build_isolated()
    return np.load(CACHE / "iso_X.npy"), pd.read_csv(CACHE / "iso_meta.csv")


if __name__ == "__main__":
    X, meta = build_isolated()
    print(X.shape)
    print(meta.groupby(["pid", "part", "type"]).size().unstack(fill_value=0))
    print("max gap frac", meta.gap_frac.max())
