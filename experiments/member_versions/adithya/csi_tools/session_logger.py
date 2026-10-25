#!/usr/bin/env python3
"""Mark rep start/end times during a CSI capture session.

Run this next to the running wifi_rx flowgraph. It records wall-clock
timestamps (microseconds, same clock as the Timestamp_us column written
by extract_csi) so reps can be cut out of the capture CSV later.

Usage (discrete actions, e.g. squat):
    python3 session_logger.py --action squat --subject amrith --name S01_squat_amrith_20260716

    ENTER      -> start rep
    ENTER      -> end rep
    u + ENTER  -> undo last completed rep
    q + ENTER  -> finish session

Usage (continuous classes: walk / noaction / empty):
    python3 session_logger.py --action walk --subject amrith --continuous
    (ENTER starts the take, ENTER ends it; it is auto-chunked later)
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime

DEFAULT_OUT_DIR = os.path.expanduser("~/usrp-projects/data")


def now_us():
    return int(time.time() * 1e6)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--action", required=True,
                   help="class label: walk|squat|bend|drink|nod|noaction|empty")
    p.add_argument("--subject", required=True, help="who performs (e.g. amrith)")
    p.add_argument("--name", default=None,
                   help="session name; labels file = <name>_labels.csv "
                        "(default: <action>_<subject>_<timestamp>)")
    p.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    p.add_argument("--continuous", action="store_true",
                   help="single start/end take (walk/noaction/empty)")
    p.add_argument("--channel", default="", help="WiFi channel, for the metadata file")
    p.add_argument("--notes", default="", help="free-form notes, for the metadata file")
    args = p.parse_args()

    name = args.name or "%s_%s_%s" % (
        args.action, args.subject, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(args.out_dir, exist_ok=True)
    labels_path = os.path.join(args.out_dir, name + "_labels.csv")
    meta_path = os.path.join(args.out_dir, name + "_meta.json")

    if os.path.exists(labels_path):
        raise SystemExit("Refusing to overwrite existing %s" % labels_path)

    reps = []  # (rep, t_start_us, t_end_us)

    print("Session:", name)
    print("Labels ->", labels_path)
    print("ENTER=start/end rep, u=undo last rep, q=finish\n")

    try:
        rep = 1
        while True:
            cmd = input("[rep %d] ENTER to START (q=finish, u=undo): " % rep).strip().lower()
            if cmd == "q":
                break
            if cmd == "u":
                if reps:
                    dropped = reps.pop()
                    rep -= 1
                    print("  undid rep %d" % dropped[0])
                else:
                    print("  nothing to undo")
                continue

            t_start = now_us()
            print("  >>> GO (action now)")
            input("[rep %d] ENTER to END: " % rep)
            t_end = now_us()
            dur = (t_end - t_start) / 1e6
            reps.append((rep, t_start, t_end))
            print("  rep %d saved (%.1f s)%s" % (
                rep, dur,
                "  [WARNING: outside 1.5-4 s, consider redoing]"
                if not args.continuous and not (1.5 <= dur <= 4.0) else ""))
            rep += 1

            if args.continuous:
                break
    except KeyboardInterrupt:
        print("\ninterrupted - saving what we have")

    with open(labels_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subject", "action", "rep", "t_start_us", "t_end_us"])
        for r, ts, te in reps:
            w.writerow([args.subject, args.action, r, ts, te])

    with open(meta_path, "w") as f:
        json.dump({
            "session": name,
            "subject": args.subject,
            "action": args.action,
            "continuous": args.continuous,
            "channel": args.channel,
            "csi_ta": os.environ.get("CSI_TA", ""),
            "csi_ra": os.environ.get("CSI_RA", ""),
            "csi_out": os.environ.get("CSI_OUT", ""),
            "date": datetime.now().isoformat(timespec="seconds"),
            "n_reps": len(reps),
            "notes": args.notes,
        }, f, indent=2)

    print("\nSaved %d reps -> %s" % (len(reps), labels_path))
    print("Metadata -> %s" % meta_path)


if __name__ == "__main__":
    main()
