"""Multi-task 1D-CNN on [52 subcarriers x WIN] windows sampled from continuous streams.

Heads: state (idle / routine / sign) and fine (24 = 10 actions + 14 signs).
A window's label is the majority per-sample label of its central CENTER_S seconds.
"""
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from dense import FS_D
from windows import FINE

WIN_S = 4.0
CENTER_S = 2.0
WIN = int(WIN_S * FS_D)
CEN = int(CENTER_S * FS_D)
N_FINE = len(FINE)
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def window_labels(state, fine, starts, agree=0.6, win=WIN):
    """Majority label of the central part of each window; -1 when unclear."""
    c0 = starts + (win - CEN) // 2
    idx = c0[:, None] + np.arange(CEN)[None]
    st = state[idx].astype(int)
    fn = fine[idx].astype(int)
    ys, yf = np.full(len(starts), -1), np.full(len(starts), -1)
    for k in range(3):
        frac = (st == k).mean(1)
        ys[frac >= agree] = k
    for i in np.where(ys >= 1)[0]:
        v = fn[i][fn[i] >= 0]
        if len(v) >= agree * CEN:
            yf[i] = np.bincount(v).argmax()
    return ys, yf


class Res(nn.Module):
    def __init__(self, cin, cout, dil):
        super().__init__()
        self.c1 = nn.Conv1d(cin, cout, 7, padding=3 * dil, dilation=dil)
        self.b1 = nn.BatchNorm1d(cout)
        self.c2 = nn.Conv1d(cout, cout, 7, padding=3 * dil, dilation=dil)
        self.b2 = nn.BatchNorm1d(cout)
        self.sk = nn.Conv1d(cin, cout, 1) if cin != cout else nn.Identity()

    def forward(self, x):
        h = F.gelu(self.b1(self.c1(x)))
        return F.gelu(self.b2(self.c2(h)) + self.sk(x))


class Net(nn.Module):
    def __init__(self, cin=52, w=32, drop=0.3, win=WIN, inrep="raw"):
        super().__init__()
        self.win, self.inrep = win, inrep
        self.inorm = nn.BatchNorm1d(cin)
        self.body = nn.Sequential(
            nn.Conv1d(cin, w, 5, padding=2), nn.BatchNorm1d(w), nn.GELU(),
            Res(w, w, 1), nn.MaxPool1d(2),
            Res(w, w * 3 // 2, 2), nn.MaxPool1d(2),
            Res(w * 3 // 2, w * 2, 4), nn.MaxPool1d(2),
            Res(w * 2, w * 2, 8))
        self.drop = nn.Dropout(drop)
        self.state = nn.Linear(w * 4, 3)
        self.fine = nn.Linear(w * 4, N_FINE)

    def forward(self, x):
        if self.inrep == "env":            # sign-invariant log local energy per subcarrier
            x = torch.log(F.avg_pool1d(x * x, 9, 1, 4) + 1e-2)
        h = self.body(self.inorm(x))
        h = torch.cat([h.mean(2), h.amax(2)], 1)
        h = self.drop(h)
        return self.state(h), self.fine(h)


def augment(x):
    B, C, T = x.shape
    x = x * torch.empty(B, 1, 1, device=x.device).uniform_(0.6, 1.6)
    x = x * torch.where(torch.rand(B, 1, 1, device=x.device) < 0.5, -1.0, 1.0)
    x = x + torch.randn_like(x) * torch.empty(B, 1, 1, device=x.device).uniform_(0, 0.3)
    keep = (torch.rand(B, C, 1, device=x.device) > 0.1).float()
    return x * keep


class Trainer:
    def __init__(self, streams, seed=0, epochs=30, per_epoch=12000, bs=128, lr=2e-3,
                 win_s=WIN_S, inrep="raw", part_w=None):
        self.seed, self.epochs, self.per_epoch, self.bs, self.lr = seed, epochs, per_epoch, bs, lr
        self.win, self.inrep = int(win_s * FS_D), inrep
        part_w = part_w or {}
        X, S, SW = [], [], []
        for s in streams:
            starts = np.arange(0, len(s["x"]) - self.win, 5)
            ys, yf = window_labels(s["state"], s["fine"], starts, win=self.win)
            ok = ys >= 0
            X.append(torch.tensor(s["x"].T.copy()))
            for st, a, b in zip(starts[ok], ys[ok], yf[ok]):
                S.append((len(X) - 1, st, a, b))
                SW.append(s.get("weight", 1.0) * part_w.get(s["part"], 1.0))
        self.X = [x.to(DEV) for x in X]
        self.idx = np.array(S)
        ys = self.idx[:, 2]
        # balance states; inside routine/sign also balance fine classes
        w = np.zeros(len(ys))
        for k in range(3):
            m = ys == k
            if k == 0:
                w[m] = 1.0 / m.sum()
            else:
                fk = self.idx[m, 3]
                cnt = np.bincount(fk[fk >= 0], minlength=N_FINE)
                per = np.where(fk >= 0, 1.0 / np.maximum(cnt[np.maximum(fk, 0)], 1), 1.0 / m.sum())
                w[m] = per / per.sum()
        w = w * np.array(SW)          # e.g. up-weight calibration windows of the test participant
        self.w = w / w.sum()

    def batch(self, rows):
        xb = torch.stack([self.X[f][:, s:s + self.win] for f, s, _, _ in rows])
        return xb, torch.tensor(rows[:, 2], device=DEV), torch.tensor(rows[:, 3], device=DEV)

    def fit(self):
        torch.manual_seed(self.seed)
        g = np.random.default_rng(self.seed)
        net = Net(win=self.win, inrep=self.inrep).to(DEV)
        opt = torch.optim.AdamW(net.parameters(), lr=self.lr, weight_decay=0.05)
        steps = self.epochs * (self.per_epoch // self.bs)
        sch = torch.optim.lr_scheduler.OneCycleLR(opt, self.lr, total_steps=steps)
        net.train()
        for ep in range(self.epochs):
            pick = g.choice(len(self.idx), self.per_epoch, p=self.w)
            for i in range(0, self.per_epoch - self.bs + 1, self.bs):
                rows = self.idx[pick[i:i + self.bs]]
                # random sub-step jitter on top of the 0.1 s start grid
                rows = rows.copy()
                rows[:, 1] = np.clip(rows[:, 1] + g.integers(-2, 3, len(rows)), 0, None)
                rows[:, 1] = [min(s, self.X[f].shape[1] - self.win) for f, s in rows[:, :2]]
                xb, ys, yf = self.batch(rows)
                ls, lf = net(augment(xb))
                loss = F.cross_entropy(ls, ys, label_smoothing=0.1)
                m = yf >= 0
                if m.any():
                    loss = loss + F.cross_entropy(lf[m], yf[m], label_smoothing=0.1)
                opt.zero_grad()
                loss.backward()
                opt.step()
                sch.step()
        self.net = net.eval()
        return self


@torch.no_grad()
def predict_stream(nets, x, hop=10, bs=512):
    """Dense predictions every hop samples. Returns centre sample index, P(state), P(fine)."""
    xt = torch.tensor(x.T.copy(), device=DEV)
    win = nets[0].win
    starts = np.arange(0, xt.shape[1] - win, hop)
    ps, pf = 0, 0
    for net in nets:
        a, b = [], []
        for i in range(0, len(starts), bs):
            xb = torch.stack([xt[:, s:s + win] for s in starts[i:i + bs]])
            ls, lf = net(xb)
            a.append(ls.softmax(1).cpu()); b.append(lf.softmax(1).cpu())
        ps = ps + torch.cat(a).numpy() / len(nets)
        pf = pf + torch.cat(b).numpy() / len(nets)
    return starts + win // 2, ps, pf


@torch.no_grad()
def adapt_bn(net, xs, mode="all", n=6000, bs=256, seed=0):
    """AdaBN: re-estimate BatchNorm statistics on unlabelled data of the new participant.
    xs: list of [T, 52] streams of that participant. mode 'in' = input BN only, 'all' = every BN."""
    import copy
    net = copy.deepcopy(net).eval()
    bns = [net.inorm] if mode == "in" else [m for m in net.modules() if isinstance(m, nn.BatchNorm1d)]
    for m in bns:
        m.reset_running_stats()
        m.momentum = None                 # cumulative average
        m.train()
    g = np.random.default_rng(seed)
    X = [torch.tensor(x.T.copy(), device=DEV) for x in xs if len(x) > net.win]
    lens = np.array([x.shape[1] - net.win for x in X])
    f = g.choice(len(X), n, p=lens / lens.sum())
    for i in range(0, n, bs):
        xb = torch.stack([X[k][:, s:s + net.win] for k, s in
                          zip(f[i:i + bs], (g.random(len(f[i:i + bs])) * lens[f[i:i + bs]]).astype(int))])
        net(xb)
    return net.eval()
