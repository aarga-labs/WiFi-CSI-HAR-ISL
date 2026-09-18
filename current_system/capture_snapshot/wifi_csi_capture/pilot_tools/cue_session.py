#!/usr/bin/env python3
"""
cue_session.py - cue the participant and write ground-truth labels.

Run it ON THE RX LAPTOP, in a second terminal, while wifi_rx.py is recording.
extract_csi stamps every CSV row with this laptop's system clock (microseconds),
and this script stamps every label with the same clock, so the two line up
without any further syncing.  Nothing in wifi_csi_capture/ is modified.

Modes
  baseline  stand_still / sit_still, one long trial each
  actions   randomised isolated routine actions (beep -> GO -> STOP)
  signs     randomised isolated ISL signs; use --posture standing|seated
  script    sequential stories (M-SEQ, T-SEQ, C-SEQ); the operator presses Enter at
            every transition, and the video is used later only to fix errors
  test      show the coloured cue screens and play the beeps (do this first)

Cues: the word is shown in big letters on a coloured full-screen terminal
(yellow = get ready, green = GO, red = STOP, blue = clap) plus beeps
(GO = one high beep, STOP = two low beeps). No voice.

Examples
  python3 cue_session.py baseline --pid P01
  python3 cue_session.py actions  --pid P01 --reps 10
  python3 cue_session.py signs    --pid P01 --posture standing --reps 5
  python3 cue_session.py script   --pid P01 --runs 2
  python3 cue_session.py actions  --pid P00 --only lightswitch,drink --reps 5   # pilot
  python3 cue_session.py test                       # check the screen + beeps first

Output: <outdir>/labels_<pid>_<mode>_<YYYYmmdd_HHMMSS>.csv, one row per trial/step,
flushed after every row (Ctrl+C never loses what was already logged).
"""
import argparse
import csv
import json
import os
import random
import shutil
import subprocess
import sys
import time
from datetime import datetime

import protocol as P

FIELDS = ["pid", "mode", "posture", "trial", "label", "type", "intent", "home_action",
          "context", "script_id", "run", "step", "t_start_us", "t_end_us", "source", "note"]


def now_us():
    return time.time_ns() // 1000


# ---------------------------------------------------------------- cues -----
# Cues are SHOWN on the laptop screen in big colour-coded letters (cue_display.py)
# plus two beeps: GO = one high beep, STOP = two low beeps. No voice.
# Sound goes to the laptop speaker or a WIRED speaker, never Bluetooth (2.4 GHz).
import cue_display as D

_PLAYER = shutil.which("paplay") or shutil.which("pw-play") or shutil.which("aplay")

# What the screen SHOWS for each label (labels themselves never change).
SHOWN = {
    "stand_still": "STAND STILL", "sit_still": "SIT STILL",
    "walk": "WALK", "sitstand": "STAND UP\nSIT DOWN", "pickup": "PICK UP",
    "lightswitch": "LIGHT SWITCH", "drink": "DRINK", "answerphone": "ANSWER PHONE",
    "eat": "EAT", "wipetable": "WIPE TABLE", "tvremote": "TV REMOTE", "fall": "FALL",
    "THANKYOU": "THANK YOU",
}


def shown(label, typ=""):
    """Screen text for a label; signs get 'SIGN' on its own first line."""
    words = SHOWN.get(label, label.replace("_", " ").upper())
    return f"SIGN:\n{words}" if typ == "sign" else words


def _tone(path, parts, rate=44100, vol=0.7):
    """Write a 16-bit mono WAV made of (freq_Hz, seconds) parts; freq 0 = silence."""
    import math, struct, wave
    frames = bytearray()
    for freq, secs in parts:
        n = int(rate * secs)
        fade = max(1, int(rate * 0.01))
        for i in range(n):
            env = min(1.0, i / fade, (n - i) / fade)
            v = vol * env * math.sin(2 * math.pi * freq * i / rate) if freq else 0.0
            frames += struct.pack("<h", int(v * 32767))
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(bytes(frames))


_SOUND_DIR = os.path.join(os.path.expanduser("~"), ".cache", "cue_session")
_GO = os.path.join(_SOUND_DIR, "go.wav")      # one high beep
_STOP = os.path.join(_SOUND_DIR, "stop.wav")  # two lower beeps
try:
    os.makedirs(_SOUND_DIR, exist_ok=True)
    if not os.path.exists(_GO):
        _tone(_GO, [(1000, 0.30)])
    if not os.path.exists(_STOP):
        _tone(_STOP, [(600, 0.15), (0, 0.08), (600, 0.15)])
except OSError:
    _GO = _STOP = None


def beep(kind="go"):
    """GO = one high beep, STOP = two lower beeps."""
    path = _GO if kind == "go" else _STOP
    if _PLAYER and path and os.path.exists(path):
        subprocess.Popen([_PLAYER, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        sys.stdout.write("\a")
        sys.stdout.flush()


def screen_test():
    """Check screen + beeps before a session: python3 cue_session.py test"""
    print(f"beep player: {_PLAYER or 'NOT FOUND  (install: sudo pacman -S libpulse)'}")
    input("Make this terminal full screen and zoom in (Ctrl+Shift+=), then press Enter ... ")
    D.show("ready", shown("drink", "activity"), "get ready", "TEST  -  yellow = get ready")
    time.sleep(2.5)
    beep("go")
    D.show("go", shown("drink", "activity"), "GO  (one high beep)", "TEST  -  green = GO")
    time.sleep(2.5)
    beep("stop")
    D.show("stop", "STOP", "freeze  (two low beeps)", "TEST  -  red = STOP")
    time.sleep(2.5)
    D.show("ready", shown("WATER", "sign"), "get ready", "TEST  -  signs show SIGN on the first line")
    time.sleep(2.5)
    D.show("clap", "CLAP 3 TIMES", "operator: Enter on the 3rd clap", "TEST  -  blue = claps")
    time.sleep(2.5)
    D.plain()
    print("If the word was hard to read from X, zoom in more or turn the screen toward X.")
    print("If you heard no beeps, raise the volume or plug in a WIRED speaker.")


def banner(text):
    print("\n" + "=" * 60 + f"\n  {text}\n" + "=" * 60, flush=True)


# ---------------------------------------------------------------- writer ---
class LabelWriter:
    def __init__(self, outdir, pid, mode, protocol_version=None):
        os.makedirs(outdir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(outdir, f"labels_{pid}_{mode}_{stamp}.csv")
        self.protocol_version = protocol_version
        self.fh = open(self.path, "w", newline="")
        self.w = csv.DictWriter(self.fh, fieldnames=FIELDS)
        self.w.writeheader()
        self.fh.flush()

    def row(self, **kw):
        if self.protocol_version:
            kw["note"] = "; ".join(filter(None, [
                f"protocol={self.protocol_version}", kw.get("note", "")]))
        self.w.writerow({k: kw.get(k, "") for k in FIELDS})
        self.fh.flush()

    def close(self):
        self.fh.close()


def sync_mark(lw, pid, mode, note, top=""):
    """Clap marker: aligns the video (and the phone IMU) to the CSI clock."""
    D.show("clap", "CLAP 3 TIMES", f"operator: press Enter on the 3rd clap ({note})", top)
    input(f">>> Participant CLAPS 3 times ({note}).  Press Enter ON THE THIRD CLAP ... ")
    t = now_us()
    lw.row(pid=pid, mode=mode, label="clap_x3", type="sync", t_start_us=t, t_end_us=t,
           source="keypress", note=note)
    print(f"    sync logged at {t}")


# ---------------------------------------------------------------- isolated -
def run_isolated(args, lw, trials):
    """trials: list of (label, type, dur, intent, action).  Randomised order."""
    rng = random.Random(args.seed)
    rng.shuffle(trials)
    n = len(trials)
    print(f"{n} trials, seed={args.seed}, ready={args.ready}s rest={args.rest}s")
    top = f"{args.pid}  -  {args.mode} {args.posture if args.mode in ('signs', 'actions') else ''}".strip()
    sync_mark(lw, args.pid, args.mode, "start", top)
    bad = []
    for i, (label, typ, dur, intent, action) in enumerate(trials, 1):
        if args.break_every and i > 1 and (i - 1) % args.break_every == 0:
            D.show("info", "BREAK", f"{i-1} of {n} done  -  operator: type bad trial numbers below, or Enter", top)
            ans = input(f"--- break after {i-1}/{n}. Type bad trial numbers to flag "
                        f"(e.g. '3 7'), or just Enter to continue: ").strip()
            bad += [x for x in ans.split() if x.isdigit()]
        head = f"{top}   -   trial {i} of {n}"
        instruction = getattr(P, "ACTION_INSTRUCTIONS", {}).get(label, "")
        ready_text = "get ready  -  go to the start position and freeze"
        if args.protocol == "p45":
            posture = "seated" if label == "sit_still" else args.posture
            ready_text = f"{posture.upper()} - get ready, then freeze"
            if label == "sitstand":
                ready_text = "START SEATED - stand up then sit down on GO"
            if instruction:
                ready_text += " - " + instruction
        D.show("ready", shown(label, typ), ready_text, head)
        time.sleep(args.ready)                      # participant gets ready, stays still
        beep("go")
        t0 = now_us()
        D.show("go", shown(label, typ), f"GO  -  {dur:g} s", head)
        time.sleep(dur)
        beep("stop")
        t1 = now_us()
        D.show("stop", "STOP", "freeze", head)
        posture = args.posture
        if args.protocol == "p45":
            posture = ("seated" if label == "sit_still" else
                       "transition" if label in ("sitstand", "fall") else
                       "moving" if label == "walk" else args.posture)
        lw.row(pid=args.pid, mode=args.mode, posture=posture, trial=i, label=label,
               type=typ, intent=intent, home_action=action, context="isolated",
               t_start_us=t0, t_end_us=t1, source="cue")
        time.sleep(args.rest)
    D.show("info", "DONE", "operator: type bad trial numbers below, or Enter", top)
    ans = input("Done. Flag any bad trial numbers (e.g. '3 7') or Enter: ").strip()
    bad += [x for x in ans.split() if x.isdigit()]
    for b in bad:
        lw.row(pid=args.pid, mode=args.mode, trial=b, label="BAD_TRIAL", type="flag",
               source="operator", note="exclude this trial")
    sync_mark(lw, args.pid, args.mode, "end", top)
    D.plain()


def build_trials(args):
    trials = []
    if args.mode == "baseline":
        for label, secs in P.BASELINES.items():
            trials.append((label, "idle", secs, "I0", "none"))
    elif args.mode == "actions":
        actions = P.SEATED_ACTIONS if args.protocol == "p45" and args.posture == "seated" else P.ACTIONS
        for label, (dur, reps, _, _) in actions.items():
            if args.only and label not in args.only:
                continue
            r = args.reps if args.reps else reps
            if label == "fall":
                r = min(r, 5)                       # safety: never more than 5 falls
            trials += [(label, "activity", dur, "I0", "none")] * r
    elif args.mode == "signs":
        for label, (dur, cat, action, _) in P.SIGNS.items():
            if args.only and label not in args.only:
                continue
            trials += [(label, "sign", dur, cat, action)] * (args.reps or 5)
    return trials


# ---------------------------------------------------------------- scripts --
def run_scripts(args, lw):
    names = args.only or list(P.SCRIPTS.keys())
    order = [(s, r) for r in range(1, args.runs + 1) for s in names]
    random.Random(args.seed).shuffle(order)
    print("Script order:", ", ".join(f"{s}#{r}" for s, r in order))
    for k, (sid, run) in enumerate(order, 1):
        steps = P.SCRIPTS[sid]
        postures = P.script_postures(sid) if args.protocol == "p45" else [""] * len(steps)
        D.plain()
        banner(f"SCRIPT {k}/{len(order)}:  {sid}  run {run}")
        for j, (label, typ, ctx) in enumerate(steps):
            print(f"   {j:2d}. {label:12s} {typ:8s} {ctx} {postures[j]}")
        if args.protocol == "p45":
            print("Start posture:", P.SCRIPT_START_POSTURE.get(sid, "standing"))
        input("\nOperator: read the steps to the participant. Press Enter to begin ... ")
        head = f"{args.pid}  -  {sid}  run {run}   ({k} of {len(order)})"
        texts, sat = [], (args.protocol == "p45" and P.SCRIPT_START_POSTURE.get(sid) == "seated")
        for label, typ, ctx in steps:
            if label == "sitstand":
                texts.append("STAND UP" if sat else "SIT DOWN")
                sat = not sat
            elif typ == "sync":
                texts.append("CLAP 3 TIMES")
            else:
                texts.append(shown(label, typ))
        t_prev = None
        for j, (label, typ, ctx) in enumerate(steps):
            nxt = steps[j + 1][0] if j + 1 < len(steps) else "END"
            nxt_text = texts[j + 1].replace("\n", " ") if j + 1 < len(steps) else "END"
            if typ == "sync":
                D.show("clap", "CLAP 3 TIMES", "operator: press Enter on the 3rd clap", f"{head}   -   step {j}")
                input(f"  [{j}] CLAP x3 now - press Enter on the third clap ")
                t = now_us()
                lw.row(pid=args.pid, mode="script", label=label, type=typ, script_id=sid,
                       run=run, step=j, t_start_us=t, t_end_us=t, source="keypress", posture=postures[j])
                t_prev = t
                continue
            sub = f"next: {nxt_text}"
            if postures[j]:
                sub = f"{postures[j].upper()} - {sub}"
            D.show("go", texts[j], sub, f"{head}   -   step {j}")
            input(f"  [{j}] NOW: {label:12s} ({typ})   next: {nxt:12s}  -> Enter when it ENDS ")
            t = now_us()
            cat, action = P.intent_of(label, typ, ctx)
            lw.row(pid=args.pid, mode="script", label=label, type=typ, intent=cat,
                   home_action=action, context=ctx, script_id=sid, run=run, step=j,
                   t_start_us=t_prev, t_end_us=t, source="keypress", posture=postures[j])
            t_prev = t
        D.plain()
        ok = input("  Script OK? [Enter = yes / n = redo later]: ").strip().lower()
        if ok == "n":
            lw.row(pid=args.pid, mode="script", label="BAD_RUN", type="flag", script_id=sid,
                   run=run, source="operator", note="exclude this run")


# ---------------------------------------------------------------- main -----
def main():
    global P
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["baseline", "actions", "signs", "script", "test"])
    ap.add_argument("--pid", help="participant id, e.g. P01 (P00 = pilot)")
    ap.add_argument("--posture", default="standing", choices=["standing", "seated"])
    ap.add_argument("--protocol", choices=["original", "p45"], default="original",
                    help="p45 adds two cooking actions, seated actions and a seated story")
    ap.add_argument("--plan", action="store_true", help="print the selected plan; no cues, labels or receiver")
    ap.add_argument("--reps", type=int, default=0, help="override repetitions per class")
    ap.add_argument("--runs", type=int, default=2, help="runs per script (script mode)")
    ap.add_argument("--only", default="", help="comma list of classes/scripts to include")
    ap.add_argument("--ready", type=float, default=2.5, help="seconds to get ready before GO")
    ap.add_argument("--rest", type=float, default=2.0, help="seconds of stillness after STOP")
    ap.add_argument("--break-every", type=int, default=20)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--plain", action="store_true", help="no big coloured screen, plain text only")
    ap.add_argument("--no-speech", dest="speak", action="store_false", help=argparse.SUPPRESS)  # old option, ignored
    ap.add_argument("--outdir", default=os.path.expanduser("~/usrp-projects/data/labels"))
    args = ap.parse_args()
    if args.protocol == "p45":
        import protocol_p45
        P = protocol_p45
    if args.plain:
        D.enabled = False
    if args.mode == "test":
        screen_test()
        return
    if not args.pid:
        ap.error("--pid is required, e.g. --pid P01")
    args.only = [x.strip() for x in args.only.split(",") if x.strip()]
    if args.reps < 0 or args.runs < 1 or args.ready < 0 or args.rest < 0 or args.break_every < 0:
        ap.error("reps/ready/rest/break-every must be nonnegative; runs must be positive")
    available = (P.SCRIPTS if args.mode == "script" else P.SIGNS if args.mode == "signs" else
                 P.SEATED_ACTIONS if args.protocol == "p45" and args.mode == "actions" and args.posture == "seated" else
                 P.ACTIONS if args.mode == "actions" else P.BASELINES)
    unknown = set(args.only) - set(available)
    if unknown:
        ap.error("unknown/unsupported labels for this part: " + ", ".join(sorted(unknown)))
    if args.protocol == "original" and args.mode == "actions" and args.posture == "seated":
        ap.error("seated actions require --protocol p45")
    if args.plan:
        result = {"protocol": getattr(P, "VERSION", "original"), "mode": args.mode, "posture": args.posture}
        if args.mode == "script":
            result.update(runs=args.runs, scripts={name: [
                {"label": label, "type": typ, "context": ctx,
                 "posture": P.script_postures(name)[j] if args.protocol == "p45" else ""}
                for j, (label, typ, ctx) in enumerate(P.SCRIPTS[name])]
                for name in (args.only or P.SCRIPTS)})
        else:
            trials = build_trials(args)
            result.update(trials=len(trials), classes={
                label: {"reps": sum(t[0] == label for t in trials), "duration_s": dur}
                for label, _, dur, _, _ in trials})
        print(json.dumps(result, indent=2))
        return
    if args.seed is None:
        args.seed = random.randrange(1_000_000)

    label_mode = args.mode
    if args.protocol == "p45":
        label_mode = f"{args.mode}_{args.posture}" if args.mode in ("actions", "signs") else args.mode
    lw = LabelWriter(args.outdir, args.pid, label_mode, getattr(P, "VERSION", None))
    print(f"Labels -> {lw.path}")
    print("Check: wifi_rx.py must already be running and saving rows in the other terminal.")
    try:
        if args.mode == "script":
            run_scripts(args, lw)
        else:
            trials = build_trials(args)
            if not trials:
                sys.exit("No trials selected - check --only names against protocol.py")
            run_isolated(args, lw, trials)
    except KeyboardInterrupt:
        interrupted = True
        print("\nStopped (Ctrl+C).")
    else:
        interrupted = False
    finally:
        D.plain() if D.enabled else None
        lw.close()
        print(f"Labels saved: {lw.path}")
    if interrupted:
        sys.exit(130)          # record_part.sh treats this as an aborted take


if __name__ == "__main__":
    main()
