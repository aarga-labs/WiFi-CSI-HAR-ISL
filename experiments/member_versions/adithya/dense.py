"""Continuous streams with per-sample labels, for window training and streaming eval.

Each kept take becomes: x [T, 52] at FS_D Hz (preprocessed), t_us, per-sample
state (-1 unknown, 0 idle, 1 routine, 2 sign) and fine (-1 or index into FINE),
plus an event table (GT intervals in sample indices).

Per-sample labels
  isolated trials    [GO, STOP] -> activity / sign
  gaps <= 7 s        signs/baseline files -> idle; actions files -> routine (transition reset)
  operator breaks    unknown
  baseline, empty    idle
  stories            keypress steps; outside steps unknown
"""
import pickle
import numpy as np
import pandas as pd
from data import kept_takes, load_csi, load_labels, CACHE
from preprocess import preprocess, FS
from windows import FINE

FS_D = 50.0                    # decimated rate for the CNN (signal is low-passed at 20 Hz)
DEC = int(FS / FS_D)
STATE = {"idle": 0, "activity": 1, "transition": 1, "sign": 2}


def _posture(r, part):
    if part != "scripts":
        return r.posture if isinstance(r.posture, str) else "standing"
    if r.label == "walk":
        return "moving"
    if r.script_id == "C-SEQ":
        return "standing" if r.context == "cleaning" else "mattress"
    return "seated"


def build_stream(take):
    t, amp = load_csi(take.csi_file)
    p = preprocess(t, amp)
    x = p["x"][::DEC].copy()
    tg = p["t"][::DEC]
    gap = p["gap"][::DEC]
    T = len(tg)
    state = np.full(T, -1, np.int8)
    fine = np.full(T, -1, np.int8)
    at = lambda us: int(np.clip(np.searchsorted(tg, us), 0, T))
    events = []
    if take.part == "empty":
        state[:] = 0
    else:
        lab = load_labels(take.label_file)
        ev = lab[lab.type.isin(["activity", "sign", "idle"])].reset_index(drop=True)
        ev["rep"] = ev.groupby("label").cumcount() + 1
        fine_idx = {c: i for i, c in enumerate(FINE)}
        for k, r in ev.iterrows():
            i0, i1 = at(r.t_start_us), at(r.t_end_us)
            if i1 <= i0:
                continue
            state[i0:i1] = STATE[r.type]
            fine[i0:i1] = fine_idx.get(r.label, -1)
            events.append({"i0": i0, "i1": i1, "type": r.type, "label": r.label,
                           "context": r.context, "intent": r.intent, "home_action": r.home_action,
                           "script": r.script_id, "run": r.run, "step": r.step,
                           "posture": _posture(r, take.part), "rep": r.rep})
            # inter-trial gap (not for stories: between steps there is no gap)
            if take.part != "scripts" and k + 1 < len(ev):
                g0, g1 = i1, at(ev.t_start_us[k + 1])
                if 0 < (g1 - g0) / FS_D <= 7.0:
                    state[g0:g1] = 1 if take.part == "actions" else 0
                    if take.part == "actions":
                        events.append({"i0": g0, "i1": g1, "type": "transition", "label": "transition",
                                       "context": None, "intent": "I0", "home_action": "none",
                                       "script": None, "run": None, "step": None, "posture": "moving",
                                       "rep": r.rep})   # same rep as the trial before it (calibration splits)
    state[gap] = -1
    return {"pid": take.pid, "part": take.part, "file": take.csi_file, "x": x.astype(np.float32),
            "t": tg, "state": state, "fine": fine, "events": pd.DataFrame(events)}


def load_streams():
    f = CACHE / "streams.pkl"
    if f.exists():
        return pickle.load(open(f, "rb"))
    S = [build_stream(tk) for tk in kept_takes().itertuples()]
    pickle.dump(S, open(f, "wb"))
    return S


if __name__ == "__main__":
    for s in load_streams():
        st = s["state"]
        print(f"{s['pid']:4s} {s['part']:15s} T={len(st):6d} unk={np.mean(st == -1):.2f} "
              f"idle={np.mean(st == 0):.2f} routine={np.mean(st == 1):.2f} sign={np.mean(st == 2):.2f} events={len(s['events'])}")
