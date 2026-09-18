import sys, os, json, glob
import numpy as np, pandas as pd
sys.path.insert(0, os.path.expanduser("~/mnt/adhikkesh--adhikkesh--FYP/pilot_tools"))
sys.dont_write_bytecode = True
from plot_pilot import to_grid, motion_energy, FS
D = os.path.expanduser("~/mnt/usrp-projects/data/phase1")
csi, lbl = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "-")
p = os.path.join(D, csi)
with open(p) as f:
    nlines = sum(1 for _ in f) - 1
df = pd.read_csv(p, on_bad_lines="skip")
res = {"file": csi, "lines": nlines, "rows": len(df), "nan_rows": int(df.isna().any(axis=1).sum())}
df = df.dropna()
t = df["Timestamp_us"].to_numpy(np.int64)
d = np.diff(t)
res["ts_backwards"] = int((d < 0).sum()); res["ts_dupes"] = int((d == 0).sum())
res["channels"] = sorted(df["Channel"].unique().tolist())
t = np.sort(t); d = np.diff(t) / 1e3
dur = (t[-1] - t[0]) / 1e6
res.update(dur_s=round(dur, 1), rate=round(len(t) / dur, 1), gaps100=int((d > 100).sum()), gaps250=int((d > 250).sum()), maxgap_ms=round(float(d.max()), 0))
secs = np.floor((t - t[0]) / 1e6).astype(int); cnt = np.bincount(secs)[:-1]
w10 = np.convolve(cnt, np.ones(10) / 10, "valid") if len(cnt) >= 10 else cnt
res["min_10s_rate"] = round(float(w10.min()), 1)
re = df[[f"SC{k}_Re" for k in range(52)]].to_numpy(float); im = df[[f"SC{k}_Im" for k in range(52)]].to_numpy(float)
amp = np.hypot(re, im)[np.argsort(df["Timestamp_us"].to_numpy(np.int64), kind="stable")]
ma = amp.mean(1); med = np.median(ma)
res["amp_median"] = round(float(med), 4); res["amp_outlier_rows"] = int(((ma < 0.2 * med) | (ma > 5 * med)).sum())
g_t, g = to_grid(t, amp); e, _ = motion_energy(g)
res["energy_median_all"] = round(float(np.nanmedian(e)), 4)
if lbl != "-":
    lab = pd.read_csv(os.path.join(D, "labels", lbl))
    res["label_rows"] = len(lab)
    flags = lab[lab.label.isin(["BAD_TRIAL", "BAD_RUN"])]
    res["flags"] = flags[["label", "trial", "script_id", "run"]].astype(str).values.tolist()
    sync = lab[lab.type == "sync"]; res["claps"] = len(sync)
    seg = lab[lab.type.isin(["activity", "sign", "idle"]) & lab.t_start_us.notna() & lab.t_end_us.notna()].copy()
    seg["inside"] = (seg.t_start_us >= t[0]) & (seg.t_end_us <= t[-1])
    res["segments"] = len(seg); res["segments_outside_csi"] = int((~seg.inside).sum())
    def win(a, b):
        i0, i1 = np.searchsorted(t, [a, b]); return i0, i1
    rows, egy, mg = [], [], []
    for r in seg.itertuples():
        i0, i1 = win(r.t_start_us, r.t_end_us); rows.append(i1 - i0)
        tt = t[max(i0 - 1, 0):i1 + 1]; mg.append(float(np.diff(tt).max() / 1e3) if len(tt) > 1 else 9e9)
        j0, j1 = int((r.t_start_us - t[0]) / 1e6 * FS), int((r.t_end_us - t[0]) / 1e6 * FS)
        egy.append(float(np.nanmean(e[max(j0, 0):max(j1, 1)])) if j1 > j0 else np.nan)
    seg["rows"], seg["energy"], seg["maxgap"] = rows, egy, mg
    seg["dur"] = (seg.t_end_us - seg.t_start_us) / 1e6
    res["seg_rows_min"] = int(seg.rows.min()); res["seg_gap_over_250ms"] = int((seg.maxgap > 250).sum())
    res["seg_gap_list"] = seg.loc[seg.maxgap > 250, ["label", "trial", "script_id", "run", "step", "maxgap"]].astype(str).values.tolist()
    # rest = time between labelled segments, inside the clapped region (isolated parts only)
    if (lab["mode"] != "script").all() and len(sync) >= 2:
        s0, s1 = sync.t_start_us.min(), sync.t_start_us.max()
        mask = np.zeros(len(e), bool)
        a = int((s0 - t[0]) / 1e6 * FS); b = int((s1 - t[0]) / 1e6 * FS); mask[max(a,0):b] = True
        for r in seg.itertuples():
            j0, j1 = int((r.t_start_us - t[0]) / 1e6 * FS - 0.5*FS), int((r.t_end_us - t[0]) / 1e6 * FS + 0.5*FS)
            mask[max(j0, 0):max(j1, 0)] = False
        rest = e[mask]; rest = rest[~np.isnan(rest)]
        if len(rest):
            res["rest_energy_median"] = round(float(np.median(rest)), 4); p95 = float(np.percentile(rest, 95))
            res["rest_energy_p95"] = round(p95, 4)
            act = seg[seg.type != "idle"]
            res["trials_below_rest_p95"] = act.loc[act.energy < p95, ["label", "trial", "energy"]].round(4).astype(str).values.tolist()
    per = seg.groupby("label").agg(n=("label", "size"), rows_med=("rows", "median"), dur_med=("dur", "median"), energy_med=("energy", "median"))
    res["per_class"] = {k: [int(v.n), int(v.rows_med), round(float(v.dur_med), 2), round(float(v.energy_med), 4)] for k, v in per.iterrows()}
    if (lab["mode"] == "script").any():
        sc = seg.groupby(["script_id", "run"]).size()
        res["script_runs"] = {f"{a}#{b}": int(n) for (a, b), n in sc.items()}
print(json.dumps(res))
