#!/usr/bin/env python3
"""Train the Hybrid CNN-GRU with Attention Model on raw CSI amplitude windows.

Splits are by SUBJECT (leave-one-subject-out) or by filename substring.
Each window is processed as a whole 1D time-series matrix (52 x 200),
making training and inference 52x faster than the 2D majority voting pipeline.

Usage:
    python3 train_hybrid.py /home/rishiikesh/usrp-projects/data/pilot/windows --test-subject amrith
"""

import argparse
import os
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


class CsiAmplitudeDataset(Dataset):
    def __init__(self, items, classes, train_std):
        self.items = items  # list of (path, class_idx)
        self.classes = classes
        self.train_std = train_std
        
    def __len__(self):
        return len(self.items)
        
    def __getitem__(self, i):
        path, y = self.items[i]
        window = np.load(path).astype(np.float32)
        
        # Detrend: subtract the temporal mean of each subcarrier
        window = window - window.mean(axis=1, keepdims=True)
        
        # Scale: divide by training set detrended standard deviation
        window = window / self.train_std
        
        return torch.tensor(window), torch.tensor(y), i


class SpatialTemporalAttentionModel(nn.Module):
    def __init__(self, num_classes=2, num_subcarriers=52, cnn_channels=64, gru_hidden=128):
        super().__init__()
        # Extract features across subcarriers at each timestep
        self.feature_extractor = nn.Sequential(
            nn.Conv1d(in_channels=num_subcarriers, out_channels=cnn_channels, kernel_size=5, padding=2),
            nn.BatchNorm1d(cnn_channels),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=2),  # downsamples time to 100
            
            nn.Conv1d(cnn_channels, cnn_channels * 2, kernel_size=5, padding=2),
            nn.BatchNorm1d(cnn_channels * 2),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=2)   # downsamples time to 50
        )
        
        # GRU for sequential modeling (sequence length = 50, features = cnn_channels * 2)
        self.gru = nn.GRU(
            input_size=cnn_channels * 2,
            hidden_size=gru_hidden,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )
        
        # Self-Attention Layer over time steps
        self.attention_query = nn.Linear(gru_hidden * 2, 1)
        
        # Classifier
        self.classifier = nn.Sequential(
            nn.Linear(gru_hidden * 2, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # x shape: (batch, 52, 200)
        features = self.feature_extractor(x)  # shape: (batch, 128, 50)
        features = features.transpose(1, 2)   # shape: (batch, 50, 128)
        
        out, _ = self.gru(features)           # shape: (batch, 50, 256)
        
        # Attention Mechanism
        attn_weights = torch.softmax(self.attention_query(out), dim=1) # shape: (batch, 50, 1)
        context = torch.sum(out * attn_weights, dim=1)                 # shape: (batch, 256)
        
        return self.classifier(context)


def scan_dataset(root):
    items = []
    classes = sorted(d for d in os.listdir(root)
                     if os.path.isdir(os.path.join(root, d)))
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if f.endswith(".npy"):
                items.append((os.path.join(root, c, f), ci))
    return items, classes


def evaluate(model, loader, device, n_classes, paths):
    model.eval()
    correct = total = 0
    conf = np.zeros((n_classes, n_classes), int)
    with torch.no_grad():
        for x, y, idx in loader:
            x = x.to(device)
            pred = model(x).argmax(1).cpu()
            correct += (pred == y).sum().item()
            total += len(y)
            for yi, pi in zip(y.tolist(), pred.tolist()):
                conf[yi][pi] += 1
    acc = correct / max(total, 1)
    return acc, conf


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dataset")
    p.add_argument("--test-subject", help="subject held out for testing (LOSO)")
    p.add_argument("--test-match", help="filename substring held out for testing")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--val-frac", type=float, default=0.15,
                   help="fraction of train windows used for validation")
    p.add_argument("--out", default="hybrid_model.pt")
    args = p.parse_args()

    if not args.test_subject and not args.test_match:
        p.error("need --test-subject or --test-match")

    items, classes = scan_dataset(args.dataset)
    if not items:
        raise SystemExit("no .npy files found under %s" % args.dataset)
        
    key = ("_%s_" % args.test_subject.lower()) if args.test_subject \
        else args.test_match.lower()
        
    test = [it for it in items if key in os.path.basename(it[0]).lower()]
    train_all = [it for it in items if key not in os.path.basename(it[0]).lower()]
    
    if not test or not train_all:
        raise SystemExit("split produced empty set (test=%d train=%d) - check the "
                         "subject/match string" % (len(test), len(train_all)))

    # validation split by window
    wids = sorted({os.path.basename(p_) for p_, _ in train_all})
    rng = np.random.default_rng(0)
    val_wids = set(rng.choice(wids, max(1, int(len(wids) * args.val_frac)),
                               replace=False))
    train = [it for it in train_all
             if os.path.basename(it[0]) not in val_wids]
    val = [it for it in train_all
           if os.path.basename(it[0]) in val_wids]

    print("Classes:", classes)
    print("Windows: train=%d val=%d test=%d" % (len(train), len(val), len(test)))

    # Compute training set std of detrended data per subcarrier
    train_vals = []
    for path, _ in train:
        w = np.load(path)
        w_detrend = w - w.mean(axis=1, keepdims=True)
        train_vals.append(w_detrend)
    train_vals = np.concatenate(train_vals, axis=1) # shape: (52, num_windows * 200)
    train_std = (train_vals.std(axis=1, keepdims=True) + 1e-8).astype(np.float32)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device:", device)

    def mk(items_, shuffle):
        ds = CsiAmplitudeDataset(items_, classes, train_std)
        return ds, DataLoader(ds, batch_size=args.batch, shuffle=shuffle,
                              num_workers=2)

    _, train_loader = mk(train, True)
    val_ds, val_loader = mk(val, False)
    test_ds, test_loader = mk(test, False)

    model = SpatialTemporalAttentionModel(len(classes)).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.85)
    loss_fn = nn.CrossEntropyLoss()

    best_val = 0.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        tot_loss = correct = seen = 0
        for x, y, _ in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            out = model(x)
            loss = loss_fn(out, y)
            loss.backward()
            opt.step()
            tot_loss += loss.item() * len(y)
            correct += (out.argmax(1) == y).sum().item()
            seen += len(y)
        sched.step()

        val_acc, _ = evaluate(model, val_loader, device, len(classes),
                                [p_ for p_, _ in val_ds.items])
        print("epoch %2d  loss %.4f  train_acc %.3f  val_acc %.3f"
              % (epoch, tot_loss / seen, correct / seen, val_acc))
        if val_acc >= best_val:
            best_val = val_acc
            torch.save({"model": model.state_dict(), "classes": classes}, args.out)

    model.load_state_dict(torch.load(args.out)["model"])
    test_acc, conf = evaluate(model, test_loader, device, len(classes),
                                [p_ for p_, _ in test_ds.items])
    print("\nTEST per-window acc %.3f" % test_acc)
    print("Confusion matrix (rows=true, cols=pred):")
    w = max(len(c) for c in classes) + 1
    print(" " * w + "".join(c[:6].rjust(7) for c in classes))
    for i, c in enumerate(classes):
        print(c.ljust(w) + "".join(str(conf[i][j]).rjust(7)
                                   for j in range(len(classes))))
    np.savetxt(os.path.splitext(args.out)[0] + "_confusion.csv", conf,
               fmt="%d", delimiter=",",
               header=",".join(classes), comments="")
    print("Model -> %s" % args.out)


if __name__ == "__main__":
    main()
