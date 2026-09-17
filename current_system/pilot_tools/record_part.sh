#!/usr/bin/env bash
#
# record_part.sh — record ONE part for ONE participant with a single command.
#
# It starts the receiver, checks that CSI rows are arriving, runs the cue /
# label script, then stops the receiver cleanly and prints a quality summary.
# The transmitter is NOT touched: leave it running all day.
#
#   export RX_GAIN=16                        # once per terminal (from gain_sweep.sh)
#   ./record_part.sh DAY empty               # 2 min empty room (start + end of each day)
#   ./record_part.sh P01 baseline
#   ./record_part.sh P01 actions
#   ./record_part.sh P01 signs_standing
#   ./record_part.sh P01 signs_seated
#   ./record_part.sh P01 scripts
#
# Extra arguments go straight to cue_session.py, e.g. a short pilot:
#   ./record_part.sh P00 actions --only lightswitch,drink --reps 3
#
# A mistake? Just record the same part again. At the end of every part the script
# asks "Keep this take?": answer r and the take is moved to $DATA/discarded/
# (Ctrl+C in the middle does the same automatically). Only kept takes stay in $DATA.
#
# Output (all in $DATA, default ~/usrp-projects/data/phase1):
#   <PID>_<part>_<date_time>.csv          CSI rows (one per decoded frame)
#   labels/labels_<PID>_<mode>_<...>.csv  ground-truth labels (same clock as the CSI)
#   logs/<PID>_<part>_<date_time>.rx.log  receiver warnings (overflows etc.)
#   session_log.csv                       one line per part: rows, rate, gain, files

set -uo pipefail

usage() { sed -n '3,23p' "$0"; exit 1; }
[ $# -ge 2 ] || usage
PID="$1"; PART="$2"; shift 2
case "$PART" in
    baseline|actions|signs_standing|signs_seated|scripts|empty) ;;
    *) echo "unknown part '$PART'"; usage ;;
esac
if [[ "$PID" == *_* ]]; then echo "participant id must not contain '_' (use P01, P02 ...)"; exit 1; fi

: "${RX_GAIN:?export RX_GAIN=<value from gain_sweep.sh> first, e.g. export RX_GAIN=18}"
export RX_GAIN

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO:-$HOME/adhikkesh/FYP/wifi_csi_capture}"
RX_EX="$REPO/receiver/gr-ieee802-11/examples"
DATA="${DATA:-$HOME/usrp-projects/data/phase1}"
EMPTY_SECS="${EMPTY_SECS:-120}"

[ -f "$RX_EX/wifi_rx.py" ] || { echo "wifi_rx.py not found in $RX_EX  (set REPO=/path/to/wifi_csi_capture)"; exit 1; }
mkdir -p "$DATA/logs" "$DATA/labels" "$DATA/discarded"

STAMP="$(date +%Y%m%d_%H%M%S)"
NAME="${PID}_${PART}_${STAMP}"
export CSI_TA=02:00:00:00:00:01
export CSI_RA=02:00:00:00:00:02
export CSI_OUT="$DATA/$NAME.csv"
LOG="$DATA/logs/$NAME.rx.log"
LBLDIR="$DATA/labels"
MARK="$DATA/logs/.$NAME.start"
touch "$MARK"
SLOG="$DATA/session_log.csv"
SLOG_HEAD="date,time,pid,part,rx_gain,rows,seconds,rows_per_s,gaps_over_100ms,max_gap_ms,mean_csi,overflow_msgs,csi_file,label_file,video_file,status"
if [ -f "$SLOG" ] && ! head -1 "$SLOG" | grep -q ",status$"; then sed -i '1s/$/,status/' "$SLOG"; fi
[ -f "$SLOG" ] || echo "$SLOG_HEAD" > "$SLOG"
# A copy of the session log is kept next to the repo (small file, easy to share/check).
COPY_DIR="${COPY_DIR:-$(dirname "$REPO")}"
copy_log() { cp -f "$SLOG" "$COPY_DIR/session_log_$(basename "$DATA").csv" 2>/dev/null || true; }

# Guard: the whole dataset should use ONE RX gain. Compare with the gain most kept takes used.
DS_GAIN=$(python3 - "$SLOG" <<'PYEOF'
import csv, sys, collections
try:
    rows = [r for r in csv.DictReader(open(sys.argv[1])) if r.get("status", "kept") in ("kept", "")]
except FileNotFoundError:
    rows = []
c = collections.Counter(r["rx_gain"] for r in rows if r.get("rx_gain"))
print(c.most_common(1)[0][0] if c else "")
PYEOF
)
if [ -n "$DS_GAIN" ] && [ "$DS_GAIN" != "$RX_GAIN" ]; then
    echo "!!! This dataset was recorded with RX_GAIN=$DS_GAIN, but this terminal has RX_GAIN=$RX_GAIN."
    echo "!!! Press Ctrl+C and run:  export RX_GAIN=$DS_GAIN   (or press Enter to continue anyway)"
    read -r _
fi

# Move everything this run wrote into discarded/ (a mistake, Ctrl+C, or no packets).
discard_take() {
    local why="$1" f
    for f in "$CSI_OUT" "$LOG"; do [ -f "$f" ] && mv -n "$f" "$DATA/discarded/"; done
    while IFS= read -r f; do mv -n "$f" "$DATA/discarded/"; done < <(find "$LBLDIR" -maxdepth 1 -name "labels_${PID}_*.csv" -newer "$MARK" 2>/dev/null)
    echo "$(date +%F),$(date +%T),$PID,$PART,$RX_GAIN,,,,,,,,$(basename "$CSI_OUT"),,$NAME.mp4,$why" >> "$SLOG"
    rm -f "$MARK"
    copy_log
    echo ">>> This take was moved to $DATA/discarded/ ($why). It is NOT part of the dataset."
    echo ">>> Camera person: delete this video (or rename it to ${NAME}_DISCARD.mp4)."
    echo ">>> To redo it, run the same command again:  ./record_part.sh $PID $PART"
}

echo "=============================================================="
echo " participant : $PID          part : $PART"
echo " RX gain     : $RX_GAIN dB"
echo " CSI file    : $CSI_OUT"
echo "=============================================================="
echo
echo ">>> Camera person: start the phone video now."
echo ">>> Video file name to use afterwards:  $NAME.mp4"
read -r -p ">>> Press Enter once the video is recording ... " _

# ---------------------------------------------------------------- receiver --
# stdout carries a metadata block per frame (hundreds of KB/s): discard it.
# stderr keeps the UHD warnings / overflow messages for the summary.
( cd "$RX_EX" && exec python3 wifi_rx.py ) > /dev/null 2> "$LOG" &
RXPID=$!

stop_rx() {
    if kill -0 "$RXPID" 2>/dev/null; then
        kill -INT "$RXPID" 2>/dev/null
        for _ in $(seq 1 20); do kill -0 "$RXPID" 2>/dev/null || break; sleep 0.5; done
        kill -0 "$RXPID" 2>/dev/null && kill -TERM "$RXPID" 2>/dev/null && sleep 2
        kill -0 "$RXPID" 2>/dev/null && kill -KILL "$RXPID" 2>/dev/null
    fi
    wait "$RXPID" 2>/dev/null
}
trap 'echo; echo "Interrupted - stopping the receiver"; stop_rx; discard_take aborted; exit 130' INT TERM

rows() { if [ -f "$CSI_OUT" ]; then echo $(( $(wc -l < "$CSI_OUT") - 1 )); else echo 0; fi; }

echo "Starting receiver, waiting for packets ..."
n=0; ok=0
for _ in $(seq 1 30); do
    sleep 1
    n=$(rows)
    if [ "$n" -ge 50 ]; then ok=1; break; fi
    kill -0 "$RXPID" 2>/dev/null || break
done
if [ "$ok" -ne 1 ]; then
    echo "!!! Only $n rows after 30 s. Check the transmitter is running (TX_CHANNEL=1, PPS=200)."
    echo "!!! Receiver messages: $LOG"
    stop_rx; discard_take no_packets; exit 1
fi
n1=$(rows); sleep 5; n2=$(rows)
RATE=$(( (n2 - n1) / 5 ))
echo "Receiver OK: about $RATE rows/s"
if [ "$RATE" -lt 60 ]; then
    echo "!!! WARNING: below 60 rows/s. Ctrl+C now to abort, or wait 5 s to continue anyway."
    sleep 5
fi
echo

# --------------------------------------------------------------------- cue --
cd "$HERE"
case "$PART" in
    baseline)       python3 cue_session.py baseline --pid "$PID" --outdir "$LBLDIR" "$@" ;;
    actions)        python3 cue_session.py actions  --pid "$PID" --reps 10 --ready 4 --outdir "$LBLDIR" "$@" ;;
    signs_standing) python3 cue_session.py signs    --pid "$PID" --posture standing --reps 5 --ready 3 --outdir "$LBLDIR" "$@" ;;
    signs_seated)   python3 cue_session.py signs    --pid "$PID" --posture seated   --reps 5 --ready 3 --outdir "$LBLDIR" "$@" ;;
    scripts)        python3 cue_session.py script   --pid "$PID" --runs 2 --outdir "$LBLDIR" "$@" ;;
    empty)
        echo ">>> Everyone LEAVE the room now. Recording ${EMPTY_SECS} s of empty room."
        for (( s=EMPTY_SECS; s>0; s-=10 )); do echo "    $s s left"; sleep 10; done
        echo ">>> Done - you can come back in." ;;
esac
CUE_RC=$?

stop_rx
trap - INT TERM
if [ "$CUE_RC" -eq 130 ]; then          # Ctrl+C during the cues
    discard_take aborted
    exit 130
fi

# ----------------------------------------------------------------- summary --
LBL="-"
if [ "$PART" != "empty" ]; then
    LBL="$(find "$LBLDIR" -maxdepth 1 -name "labels_${PID}_*.csv" -newer "$MARK" 2>/dev/null | head -1)"
    [ -n "$LBL" ] || LBL="-"
fi
OVF=$(grep -c "overflows occurred" "$LOG" 2>/dev/null || true)

SUMMARY=$(python3 - "$CSI_OUT" <<'PYEOF'
import csv, math, sys
try:
    rows = list(csv.reader(open(sys.argv[1])))[1:]
except FileNotFoundError:
    rows = []
rows = [r for r in rows if len(r) >= 107]
n = len(rows)
if n < 2:
    print(f"{n},0,0,0,0,-"); sys.exit()
ts = [int(r[1]) for r in rows]
dur = (ts[-1] - ts[0]) / 1e6
gaps = [(b - a) / 1e3 for a, b in zip(ts, ts[1:])]
amp = sum(math.hypot(float(r[3 + 2*k]), float(r[4 + 2*k])) for r in rows[::10] for k in range(52)) / (52 * len(rows[::10]))
print(f"{n},{dur:.1f},{n/dur:.1f},{sum(g > 100 for g in gaps)},{max(gaps):.0f},{amp:.3f}")
PYEOF
)
IFS=, read -r NROWS DUR RATEF GAPS MAXGAP AMP <<< "$SUMMARY"

echo
echo "=============================================================="
echo " DONE  $PID  $PART"
echo "   rows        : $NROWS in $DUR s  ->  $RATEF rows/s"
echo "   gaps >100ms : $GAPS   (longest $MAXGAP ms)"
echo "   overflow msgs: $OVF"
echo "   labels      : $LBL"
echo "=============================================================="
RI=${RATEF%.*}
if [ "${RI:-0}" -ge 80 ]; then
    echo " QUALITY OK"
else
    echo " !!! LOW RATE (< 80 rows/s). Re-record this part after checking the transmitter/gain."
fi
echo ">>> Camera person: stop the video now."
echo
read -r -p ">>> Keep this take?  [Enter = keep  /  r = retake (moves it to discarded/)]: " ANS
if [[ "$ANS" =~ ^[rR] ]]; then
    discard_take retake
else
    echo "$(date +%F),$(date +%T),$PID,$PART,$RX_GAIN,$NROWS,$DUR,$RATEF,$GAPS,$MAXGAP,$AMP,$OVF,$(basename "$CSI_OUT"),$(basename "$LBL"),$NAME.mp4,kept" >> "$SLOG"
    rm -f "$MARK"
    copy_log
    echo ">>> Kept. Camera person: rename the video to  $NAME.mp4"
fi
