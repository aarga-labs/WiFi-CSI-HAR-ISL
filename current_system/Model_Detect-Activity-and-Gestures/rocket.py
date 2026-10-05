"""MiniRocket-style random convolution features in torch (GPU), multivariate.

Kernels: length 9, weights from {-1, 2} (MiniRocket), random channel subsets,
exponential dilations. Biases are quantiles of the kernel's response on
training windows only, so nothing about the test subject is used when fitting.
Features per kernel: PPV (proportion of positive values) and mean of positive values.
"""
import numpy as np
import torch
import torch.nn.functional as F


class Rocket:
    def __init__(self, n_kernels=4000, max_ch=6, seed=0, device=None):
        self.n, self.max_ch, self.seed = n_kernels, max_ch, seed
        self.dev = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def fit(self, X):
        g = np.random.default_rng(self.seed)
        N, C, T = X.shape
        max_exp = np.log2((T - 1) / 8)
        self.kern = []                                   # (dilation, weight [k, C, 9])
        dil = np.floor(2 ** g.uniform(0, max_exp, self.n)).astype(int)
        for d in np.unique(dil):
            k = int((dil == d).sum())
            w = np.zeros((k, C, 9), np.float32)
            for j in range(k):
                pos = g.choice(9, 3, replace=False)
                base = -np.ones(9, np.float32)
                base[pos] = 2.0
                chans = g.choice(C, g.integers(1, self.max_ch + 1), replace=False)
                w[j, chans] = base
            self.kern.append((int(d), torch.tensor(w, device=self.dev)))
        # biases from responses on a few random training windows
        idx = g.choice(N, min(N, 64), replace=False)
        xs = torch.tensor(X[idx], device=self.dev)
        self.bias = []
        for d, w in self.kern:
            r = F.conv1d(xs, w, dilation=d, padding=4 * d)  # [n, k, T]
            q = torch.tensor(g.uniform(0.1, 0.9, w.shape[0]), device=self.dev, dtype=torch.float32)
            pick = torch.tensor(g.integers(0, len(idx), w.shape[0]), device=self.dev)
            resp = r[pick, torch.arange(w.shape[0], device=self.dev)]   # [k, T]
            srt = resp.sort(dim=1).values
            pos = (q * (srt.shape[1] - 1)).long()
            self.bias.append(srt[torch.arange(w.shape[0], device=self.dev), pos])
        return self

    @torch.no_grad()
    def transform(self, X, batch=128):
        out = []
        for i in range(0, len(X), batch):
            xb = torch.tensor(X[i:i + batch], device=self.dev)
            feats = []
            for (d, w), b in zip(self.kern, self.bias):
                r = F.conv1d(xb, w, dilation=d, padding=4 * d) - b[None, :, None]
                pos = (r > 0).float()
                feats += [pos.mean(2), (r * pos).sum(2) / (pos.sum(2) + 1)]
            out.append(torch.cat(feats, 1).cpu().numpy())
        return np.concatenate(out)
