"""LOSO training of the CNN and dense prediction over every held-out recording.

Configs
  iso      : train on isolated parts only (actions, signs, baseline, empty)
  iso+story: also train on the other participants' story recordings
Saves cache/dense_<config>_<pid>.pkl with predictions for each test stream.
"""
import sys
import time
import pickle
import numpy as np
from dense import load_streams
from cnn import Trainer, predict_stream
from data import CACHE

PIDS = ["P01", "P02", "P03"]
CONFIGS = {"iso": {"scripts"}, "iso+story": set(), "cal1": set(), "cal2": set()}   # parts excluded from training
SEEDS = [0, 1, 2]
CAL_PARTS = ("actions", "signs_standing", "signs_seated")
CAL_WEIGHT = 3.0


def split_calibration(s, k):
    """Calibration on the test participant: isolated trials with rep <= k (and the transition
    after them) go to training; they are masked out of the test stream."""
    if s["part"] not in CAL_PARTS or not len(s["events"]):
        return None, s
    ev = s["events"]
    cal = ev.rep <= k
    keep = np.zeros(len(s["state"]), bool)
    for e in ev[cal].itertuples():
        keep[e.i0:e.i1] = True
    tr = dict(s, state=np.where(keep, s["state"], -1), fine=np.where(keep, s["fine"], -1),
              events=ev[cal].reset_index(drop=True), weight=CAL_WEIGHT)
    te = dict(s, state=np.where(keep, -1, s["state"]), fine=np.where(keep, -1, s["fine"]),
              events=ev[~cal].reset_index(drop=True))
    return tr, te

if __name__ == "__main__":
    configs = sys.argv[1:] or list(CONFIGS)
    S = load_streams()
    for cfg in configs:
        for pid in PIDS:
            t0 = time.time()
            train = [s for s in S if s["pid"] != pid and s["part"] not in CONFIGS[cfg]]
            test = [s for s in S if s["pid"] == pid]
            if cfg.startswith("cal"):
                pairs = [split_calibration(s, int(cfg[3:])) for s in test]
                train += [a for a, _ in pairs if a is not None]
                test = [b for _, b in pairs]
            nets = [Trainer(train, seed=k).fit().net for k in SEEDS]
            out = []
            for s in test:
                c, ps, pf = predict_stream(nets, s["x"])
                out.append({k: s[k] for k in ("pid", "part", "file", "t", "state", "fine", "events")}
                           | {"centre": c, "ps": ps, "pf": pf})
            pickle.dump(out, open(CACHE / f"dense_{cfg}_{pid}.pkl", "wb"))
            print(f"{cfg} {pid}: trained {len(SEEDS)} nets on {len(train)} streams, {time.time() - t0:.0f}s", flush=True)
