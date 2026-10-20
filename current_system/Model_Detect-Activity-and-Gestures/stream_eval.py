"""Evaluation from dense LOSO predictions (cache/dense_<cfg>_<pid>.pkl).

1. Segment-level (oracle segmentation): each GT trial / story step is classified by
   averaging the window predictions centred inside it.
2. Streaming commands: smoothed P(sign) > tau for >= MIN_RUN_S -> one command event.
   Sign recall vs false commands per hour of routine activity (FC/h), swept over tau.
3. Intent on stories: f(predicted sign, context inferred from recent predicted actions).
"""
import sys
import pickle
import numpy as np
import pandas as pd
from dense import FS_D
from windows import FINE, ACTIONS, SIGNS
from data import CACHE

PIDS = ["P01", "P02", "P03"]
HOP_S = 10 / FS_D
A_IDX = [FINE.index(a) for a in ACTIONS]
S_IDX = [FINE.index(s) for s in SIGNS]
SMOOTH = 5                 # frames (1 s) moving average on P(sign)
MIN_RUN_S = 1.0
MERGE_S = 1.0
MATCH_TOL_S = 1.0
CTX_WINDOW_S = 120.0
TAUS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

# (sign, context) -> (intent, home_action); defaults are the isolated entries
DEFAULT = {"HELLO": ("I4", "wake_system"), "THANKYOU": ("I4", "confirm_close"),
           "LAMP": ("I1", "toggle_light"), "FAN": ("I1", "toggle_fan"), "TELEVISION": ("I1", "toggle_tv"),
           "COOK": ("I1", "cooking_mode"), "WATER": ("I2", "bring_water_reminder"), "HOT": ("I2", "cool_room"),
           "HUNGRY": ("I2", "food_request"), "TOILET": ("I2", "toilet_assist"), "CALL": ("I3", "call_caregiver"),
           "HELP": ("I3", "notify_caregiver"), "PAIN": ("I3", "health_alert"), "ACCIDENT": ("I3", "emergency_alert")}
CONTEXT_INTENT = {("HOT", "meal"): ("I3", "kitchen_hazard_alert"), ("HOT", "tv"): ("I2", "cool_room"),
                  ("HELP", "cleaning"): ("I3", "notify_caregiver"), ("HELP", "after_fall"): ("I3", "emergency_alert")}
ANCHOR = {"eat": "meal", "drink": "meal", "tvremote": "tv", "answerphone": "tv",
          "wipetable": "cleaning", "pickup": "cleaning", "fall": "after_fall"}


def intent_of(sign, ctx):
    return CONTEXT_INTENT.get((sign, ctx), DEFAULT[sign])


def frames_in(c, i0, i1, margin=int(1.0 * FS_D)):
    m = (c >= i0 + margin) & (c <= i1 - margin)
    if not m.any():
        m = np.zeros(len(c), bool)
        m[np.argmin(np.abs(c - (i0 + i1) / 2))] = True
    return m


# ---------------------------------------------------------------- 1. segments
def segment_table(D):
    rows = []
    for s in D:
        if not len(s["events"]):
            continue
        for e in s["events"].itertuples():
            if e.type not in ("activity", "sign"):
                continue
            m = frames_in(s["centre"], e.i0, e.i1)
            ps, pf = s["ps"][m].mean(0), s["pf"][m].mean(0)
            pred_sign = ps[2] > ps[1]
            within = SIGNS[pf[S_IDX].argmax()] if e.type == "sign" else ACTIONS[pf[A_IDX].argmax()]
            hier = SIGNS[pf[S_IDX].argmax()] if pred_sign else ACTIONS[pf[A_IDX].argmax()]
            rows.append({"pid": s["pid"], "part": s["part"], "file": s["file"], "rep": getattr(e, "rep", None),
                         "pf_act": pf[A_IDX] / pf[A_IDX].sum(), "pf_sign": pf[S_IDX] / pf[S_IDX].sum(),
                         "type": e.type, "label": e.label,
                         "posture": e.posture, "p_sign": ps[2], "pred_is_sign": pred_sign,
                         "within_type_pred": within, "hier_pred": hier})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 2. streaming
def runs(mask, min_len, merge):
    """Contiguous True runs as (start, end) frame indices, short gaps merged."""
    r, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            r.append([i, j])
            i = j
        else:
            i += 1
    out = []
    for a, b in r:
        if out and a - out[-1][1] <= merge:
            out[-1][1] = b
        else:
            out.append([a, b])
    return [(a, b) for a, b in out if b - a >= min_len]


def detect(s, tau):
    p = np.convolve(s["ps"][:, 2], np.ones(SMOOTH) / SMOOTH, mode="same")
    ev = []
    for a, b in runs(p > tau, int(MIN_RUN_S / HOP_S), int(MERGE_S / HOP_S)):
        pf = s["pf"][a:b].mean(0)
        ev.append({"f0": a, "f1": b, "i0": s["centre"][a], "i1": s["centre"][b - 1],
                   "sign": SIGNS[pf[S_IDX].argmax()]})
    return ev


def action_events(s):
    """Predicted routine-action events (for context): runs where routine is the argmax state."""
    is_r = s["ps"].argmax(1) == 1
    ev = []
    for a, b in runs(is_r, int(1.0 / HOP_S), int(0.5 / HOP_S)):
        pf = s["pf"][a:b].mean(0)
        ev.append({"i1": s["centre"][b - 1], "action": ACTIONS[pf[A_IDX].argmax()]})
    return ev


def infer_context(acts, t_idx):
    """Context at sample t_idx from predicted actions in the previous CTX_WINDOW_S.
    A fall in the window wins (after_fall); otherwise the most recent anchor action."""
    lo = t_idx - CTX_WINDOW_S * FS_D
    recent = [a for a in acts if lo <= a["i1"] <= t_idx and a["action"] in ANCHOR]
    if any(a["action"] == "fall" for a in recent):
        return "after_fall"
    return ANCHOR[recent[-1]["action"]] if recent else "isolated"


def stream_metrics(D, tau):
    n_gt = n_hit = n_id = 0
    fc = {"routine": 0, "idle": 0, "unknown": 0}
    dur = {"routine": 0.0, "idle": 0.0}
    intents = []
    for s in D:
        st = s["state"]
        dur["routine"] += (st == 1).sum() / FS_D / 3600
        dur["idle"] += (st == 0).sum() / FS_D / 3600
        gts = s["events"][s["events"].type == "sign"] if len(s["events"]) else pd.DataFrame()
        det = detect(s, tau)
        used = set()
        tol = MATCH_TOL_S * FS_D
        acts = action_events(s) if s["part"] == "scripts" else []
        for g in gts.itertuples():
            hit = [k for k, d in enumerate(det) if k not in used and d["i0"] <= g.i1 + tol and d["i1"] >= g.i0 - tol]
            n_gt += 1
            pred = None
            if hit:
                used.add(hit[0])
                n_hit += 1
                pred = det[hit[0]]["sign"]
                n_id += pred == g.label
            if s["part"] == "scripts":
                ctx_pred = infer_context(acts, g.i0)
                gt_int = (g.intent, g.home_action)
                intents.append({
                    "pid": s["pid"], "label": g.label, "context": g.context, "posture": g.posture,
                    "detected": bool(hit), "pred_sign": pred, "ctx_pred": ctx_pred,
                    "e2e": pred is not None and intent_of(pred, ctx_pred) == gt_int,
                    "e2e_cat": pred is not None and intent_of(pred, ctx_pred)[0] == gt_int[0],
                    "oracle_ctx": pred is not None and intent_of(pred, g.context) == gt_int,
                    "no_ctx": pred is not None and DEFAULT[pred] == gt_int,
                    "oracle_sign_pred_ctx": intent_of(g.label, ctx_pred) == gt_int,
                    "oracle_sign_no_ctx": DEFAULT[g.label] == gt_int})
        for k, d in enumerate(det):
            if k in used:
                continue
            # a second detection on an already-matched sign is a duplicate, not a false command
            if len(gts) and any(d["i0"] <= g.i1 + tol and d["i1"] >= g.i0 - tol for g in gts.itertuples()):
                continue
            c = int((d["i0"] + d["i1"]) / 2)
            lab = st[min(c, len(st) - 1)]
            fc["routine" if lab == 1 else "idle" if lab == 0 else "unknown"] += 1
    n_false = fc["routine"] + fc["idle"]
    prec = n_hit / max(n_hit + n_false, 1)
    rec = n_hit / max(n_gt, 1)
    return {"tau": tau, "sign_recall": rec, "precision": prec, "event_F1": 2 * prec * rec / max(prec + rec, 1e-9),
            "sign_id_acc|det": n_id / max(n_hit, 1),
            "FC_routine": fc["routine"], "FC/h_routine": fc["routine"] / max(dur["routine"], 1e-9),
            "FC/h_idle": fc["idle"] / max(dur["idle"], 1e-9), "FC_unknown": fc["unknown"],
            "routine_h": dur["routine"], "n_sign": n_gt}, pd.DataFrame(intents)


def load(cfg):
    D = []
    for pid in PIDS:
        f = CACHE / f"dense_{cfg}_{pid}.pkl"
        if f.exists():
            D += pickle.load(open(f, "rb"))
    return D


def report(cfg):
    D = load(cfg)
    print(f"\n==================== {cfg}  ({sorted({s['pid'] for s in D})})")
    seg = segment_table(D)
    seg["src"] = np.where(seg.part == "scripts", "story", "isolated")
    seg["ok_type"] = seg.pred_is_sign == (seg.type == "sign")
    seg["ok_within"] = seg.within_type_pred == seg.label
    seg["ok_hier"] = seg.hier_pred == seg.label
    print("\n[segments] accuracy (oracle segmentation)")
    print(seg.groupby(["src", "type", "posture"])[["ok_type", "ok_within", "ok_hier"]].mean().round(3)
          .join(seg.groupby(["src", "type", "posture"]).size().rename("n")).to_string())
    print("\n[segments] per participant (isolated): sign-vs-action acc / within-type fine acc")
    iso = seg[seg.src == "isolated"]
    print(iso.groupby(["pid", "type"])[["ok_type", "ok_within"]].mean().round(3).unstack().to_string())
    from sklearn.metrics import f1_score
    for typ, labels in [("activity", ACTIONS), ("sign", SIGNS)]:
        d = iso[iso.type == typ]
        f1 = [f1_score(g.label, g.within_type_pred, average="macro", labels=labels) for _, g in d.groupby("pid")]
        print(f"  isolated {typ} within-type macro-F1 per pid: {np.round(f1, 3)} mean {np.mean(f1):.3f}")

    print("\n[stream] commands: all held-out recordings of each participant pooled")
    rows, intents = [], None
    for tau in TAUS:
        r, it = stream_metrics(D, tau)
        rows.append(r)
        if tau == 0.5:
            intents = it
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    for tau in (0.5, 0.7):
        per = []
        for pid in PIDS:
            r, _ = stream_metrics([s for s in D if s["pid"] == pid], tau)
            per.append({"pid": pid, **r})
        print(f"\n[stream] per participant at tau={tau}")
        print(pd.DataFrame(per).round(3).to_string(index=False))

    print("\n[intent] story sign steps, tau=0.5 (undetected sign counts as wrong)")
    cols = ["detected", "e2e", "e2e_cat", "oracle_ctx", "no_ctx", "oracle_sign_pred_ctx", "oracle_sign_no_ctx"]
    print(intents[cols].mean().round(3).to_string())
    print("context-sensitive signs only (HOT, HELP):")
    cs = intents[intents.label.isin(["HOT", "HELP"])]
    print(cs.groupby("context")[["ctx_pred"]].agg(lambda v: v.value_counts().to_dict()).to_string())
    print(cs[["oracle_sign_pred_ctx", "oracle_sign_no_ctx"]].mean().round(3).to_string())
    print("by posture:")
    print(intents.groupby("posture")[["detected", "e2e"]].mean().round(3).to_string())
    return seg, pd.DataFrame(rows), intents


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    for cfg in sys.argv[1:] or ["iso", "iso+story"]:
        seg, st, it = report(cfg)
        seg.to_csv(CACHE.parent / f"results_segments_{cfg}.csv", index=False)
        st.to_csv(CACHE.parent / f"results_stream_{cfg}.csv", index=False)
        it.to_csv(CACHE.parent / f"results_intent_{cfg}.csv", index=False)
