#!/usr/bin/env python3
"""Convert CSI amplitude windows (.npy) into RT images for the ImgFi CNN.

RT = recurrence plot with epsilon=0 (non-binarized), ImgFi's best method:
    RT[i, j] = |x_i - x_j|
computed per subcarrier, min-max normalized per image, resized to
--size x --size, and saved as grayscale PNG:

    dataset/<action>/<window_stem>_sc<k>.png

Usage:
    python3 make_images.py windows/ --out dataset/
"""

import argparse
import os

import numpy as np
from PIL import Image


def rt_image(x, size):
    m = np.abs(x[:, None] - x[None, :])
    ptp = m.max() - m.min()
    if ptp > 0:
        m = (m - m.min()) / ptp
    else:
        m = np.zeros_like(m)
    img = Image.fromarray((m * 255).astype(np.uint8), mode="L")
    if img.size != (size, size):
        img = img.resize((size, size), Image.BILINEAR)
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("windows_dir", help="output of segment_windows.py")
    p.add_argument("--out", default="dataset")
    p.add_argument("--size", type=int, default=224)
    args = p.parse_args()

    n_img = n_win = 0
    for action in sorted(os.listdir(args.windows_dir)):
        adir = os.path.join(args.windows_dir, action)
        if not os.path.isdir(adir):
            continue
        odir = os.path.join(args.out, action)
        os.makedirs(odir, exist_ok=True)
        for fname in sorted(os.listdir(adir)):
            if not fname.endswith(".npy"):
                continue
            stem = fname[:-4]
            w = np.load(os.path.join(adir, fname))  # (n_sc, n_samples)
            for k in range(w.shape[0]):
                out = os.path.join(odir, "%s_sc%02d.png" % (stem, k))
                if os.path.exists(out):
                    continue
                rt_image(w[k], args.size).save(out)
                n_img += 1
            n_win += 1

    print("Converted %d windows -> %d images under %s/" % (n_win, n_img, args.out))


if __name__ == "__main__":
    main()
