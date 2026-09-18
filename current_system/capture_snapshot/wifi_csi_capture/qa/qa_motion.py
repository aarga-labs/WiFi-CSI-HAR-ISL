import sys, os, json
import numpy as np, pandas as pd
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.expanduser("~/mnt/adhikkesh--adhikkesh--FYP/pilot_tools"))
from plot_pilot import load_csi, to_grid, motion_energy, FS
D = os.path.expanduser("~/mnt/usrp-projects/data/phase1")
csi, lbl = sys.argv[1], sys.argv[2]
t, amp = load_csi(os.path.join(D, csi)); g_t, g = to_grid(t, amp); e, _ = motion_energy(g)
lab = pd.read_csv(os.path.join(D, "labels", lbl))
seg = lab[lab.type.isin(["activity", "sign"]) & lab.t_start_us.between(t[0], t[-1]) & lab.t_end_us.between(t[0], t[-1])]
idx = lambda us: int((us - t[0]) / 1e6 * FS)
out = []
for r in seg.itertuples():
    a, b = idx(r.t_start_us), idx(r.t_end_us)
    pre = e[max(a - int(1.5 * FS), 0):max(a - int(0.3 * FS), 1)]
    w = e[a:b]
    if len(w) < 10 or np.all(np.isnan(w)) or len(pre) == 0: continue
    base = np.nanmedian(pre); peak = np.nanmax(w)
    if np.isnan(base) or np.isnan(peak): continue
    act = np.where(w > base + 0.3 * (peak - base))[0]
    if len(act) == 0: continue
    on, off = act[0] / FS, act[-1] / FS
    tail = np.nanmean(e[b - int(0.4 * FS):b]); still_moving = tail > base + 0.5 * (peak - base)
    out.append(dict(label=r.label, trial=r.trial, ratio=peak / base, onset=on, active=off - on, moving_at_stop=bool(still_moving)))
df = pd.DataFrame(out)
summ = df.groupby("label").agg(n=("label", "size"), peak_over_pre=("ratio", "median"), onset_s=("onset", "median"), active_s=("active", "median"), active_max=("active", "max"), moving_at_stop=("moving_at_stop", "sum"))
print("##", csi, "| trials", len(df), "| peak/pre median", round(df.ratio.median(), 2), "| weak (<1.5x):", int((df.ratio < 1.5).sum()), "| moving at STOP:", int(df.moving_at_stop.sum()))
print(summ.round(2).to_string())
weak = df[df.ratio < 1.5]
if len(weak): print("weak trials:", weak[["label", "trial", "ratio"]].round(2).values.tolist())
