#!/usr/bin/env python3
"""Train the ImgFi CNN on RT images produced by make_images.py.

Splits are by SUBJECT (leave-one-subject-out) or by filename substring -
never by randomly shuffling images. All 52 subcarrier images of one window
always land in the same split, otherwise accuracy is fake (leakage).

Usage:
    # train on 2 subjects, test on the third:
    python3 train_imgfi.py dataset/ --test-subject gowreesh

    # or hold out a whole day/session by filename substring:
    python3 train_imgfi.py dataset/ --test-match 20260717

Filenames are expected to contain _<subject>_ (as produced by the
segment_windows.py -> make_images.py pipeline).

Reports per-image accuracy AND per-window accuracy (majority vote over the
52 subcarrier images of a window) - the per-window number is the one that
matters for the application.
"""

import argparse
import os
import re
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


def window_id(fname):
    """Strip the _scNN suffix: all subcarrier images of a window share this."""
    return re.sub(r"_sc\d+\.png$", "", fname)


class CsiImages(Dataset):
    def __init__(self, items, classes, size):
        self.items = items  # list of (path, class_idx)
        self.classes = classes
        self.size = size

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, y = self.items[i]
        img = Image.open(path).convert("L")
        if img.size != (self.size, self.size):
            img = img.resize((self.size, self.size), Image.BILINEAR)
        x = torch.from_numpy(np.asarray(img, np.float32) / 255.0).unsqueeze(0)
        return x, y, i


class ImgFiCNN(nn.Module):
    """3 conv layers (ImgFi Fig. 5, 3-layer variant: >99.5% with RT input)."""

    def __init__(self, n_classes, channels=(64, 128, 256)):
        super().__init__()
        layers, in_ch = [], 1
        for ch in channels:
            layers += [nn.Conv2d(in_ch, ch, 3, padding=1),
                       nn.BatchNorm2d(ch),
                       nn.ReLU(inplace=True),
                       nn.MaxPool2d(2)]
            in_ch = ch
        self.features = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(in_ch, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, n_classes),
        )

    def forward(self, x):
        return self.classifier(self.pool(self.features(x)))


def scan_dataset(root):
    items = []
    classes = sorted(d for d in os.listdir(root)
                     if os.path.isdir(os.path.join(root, d)))
    for ci, c in enumerate(classes):
        for f in sorted(os.listdir(os.path.join(root, c))):
            if f.endswith(".png"):
                items.append((os.path.join(root, c, f), ci))
    return items, classes


def evaluate(model, loader, device, n_classes, paths):
    model.eval()
    correct = total = 0
    conf = np.zeros((n_classes, n_classes), int)
    votes = defaultdict(Counter)
    truth = {}
    with torch.no_grad():
        for x, y, idx in loader:
            pred = model(x.to(device)).argmax(1).cpu()
            correct += (pred == y).sum().item()
            total += len(y)
            for yi, pi, ii in zip(y.tolist(), pred.tolist(), idx.tolist()):
                conf[yi][pi] += 1
                wid = window_id(os.path.basename(paths[ii]))
                votes[wid][pi] += 1
                truth[wid] = yi
    img_acc = correct / max(total, 1)
    win_ok = sum(1 for w, c in votes.items()
                 if c.most_common(1)[0][0] == truth[w])
    win_acc = win_ok / max(len(votes), 1)
    return img_acc, win_acc, conf


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dataset")
    p.add_argument("--test-subject", help="subject held out for testing (LOSO)")
    p.add_argument("--test-match", help="filename substring held out for testing")
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--size", type=int, default=224)
    p.add_argument("--val-frac", type=float, default=0.15,
                   help="fraction of train WINDOWS used for validation")
    p.add_argument("--out", default="imgfi_model.pt")
    args = p.parse_args()

    if not args.test_subject and not args.test_match:
        p.error("need --test-subject or --test-match (random splits are not allowed"
                " - they leak subcarrier images across splits)")

    items, classes = scan_dataset(args.dataset)
    if not items:
        raise SystemExit("no PNGs found under %s" % args.dataset)
    key = ("_%s_" % args.test_subject.lower()) if args.test_subject \
        else args.test_match.lower()
    test = [it for it in items if key in os.path.basename(it[0]).lower()]
    train_all = [it for it in items if key not in os.path.basename(it[0]).lower()]
    if not test or not train_all:
        raise SystemExit("split produced empty set (test=%d train=%d) - check the "
                         "subject/match string" % (len(test), len(train_all)))

    # validation split BY WINDOW, never by image
    wids = sorted({window_id(os.path.basename(p_)) for p_, _ in train_all})
    rng = np.random.default_rng(0)
    val_wids = set(rng.choice(wids, max(1, int(len(wids) * args.val_frac)),
                              replace=False))
    train = [it for it in train_all
             if window_id(os.path.basename(it[0])) not in val_wids]
    val = [it for it in train_all
           if window_id(os.path.basename(it[0])) in val_wids]

    print("Classes:", classes)
    print("Images: train=%d val=%d test=%d" % (len(train), len(val), len(test)))

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Device:", device)

    def mk(items_, shuffle):
        ds = CsiImages(items_, classes, args.size)
        return ds, DataLoader(ds, batch_size=args.batch, shuffle=shuffle,
                              num_workers=2)

    _, train_loader = mk(train, True)
    val_ds, val_loader = mk(val, False)
    test_ds, test_loader = mk(test, False)

    model = ImgFiCNN(len(classes)).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.ExponentialLR(opt, gamma=0.8)
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

        val_img, val_win, _ = evaluate(model, val_loader, device, len(classes),
                                       [p_ for p_, _ in val_ds.items])
        print("epoch %2d  loss %.4f  train_acc %.3f  val_img %.3f  val_win %.3f"
              % (epoch, tot_loss / seen, correct / seen, val_img, val_win))
        if val_win >= best_val:
            best_val = val_win
            torch.save({"model": model.state_dict(), "classes": classes}, args.out)

    model.load_state_dict(torch.load(args.out)["model"])
    img_acc, win_acc, conf = evaluate(model, test_loader, device, len(classes),
                                      [p_ for p_, _ in test_ds.items])
    print("\nTEST  per-image acc %.3f   per-window acc %.3f" % (img_acc, win_acc))
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
