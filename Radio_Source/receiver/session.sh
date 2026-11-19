#!/usr/bin/env bash
#
# Record a full labelled session for one subject: every class, every rep, in
# randomised order, with resume and a summary.
#
#   ./session.sh <subject> [reps] [seconds]
#
#   e.g.  ./session.sh rishi 20 10
#
# Randomised order matters. Recording all 20 walks and then all 20 waves lets
# the model learn clock-time drift — room temperature, antenna creep, your own
# fatigue — instead of the activity, and that shows up as accuracy which
# collapses on anyone else's data. Interleaving the classes spreads any drift
# evenly across all of them.
#
# Safe to re-run: instances already on disk are skipped, so a session
# interrupted halfway resumes where it stopped.
#
# Environment:
#   CSI_CHANNEL   1|6|11  (required) channel both radios are parked on
#   CLASSES       space-separated class list (default: the 9 below)
#   SEED          RNG seed for the order (default: random; recorded either way)
#   BREAK_EVERY   pause for input after this many instances (default 30)
#   ROOM          free-text room label, stored in every sidecar
#   plus everything capture.sh accepts (RX_GAIN, MIN_RATE, ...)

set -uo pipefail

SUBJECT="${1:?usage: session.sh <subject> [reps] [seconds]}"
REPS="${2:-20}"
DURATION="${3:-10}"

: "${CSI_CHANNEL:?set CSI_CHANNEL to 1, 6 or 11 first (and park the TX to match)}"

# Four whole-body activities, four hand gestures, one empty-room control.
# Keep gesture and activity counts balanced — an unbalanced binary task lets a
# model score well by leaning on the majority class.
DEFAULT_CLASSES="walk sitstand bend standstill hello comehere stop thankyou empty"
CLASSES="${CLASSES:-$DEFAULT_CLASSES}"

BREAK_EVERY="${BREAK_EVERY:-30}"
SEED="${SEED:-$RANDOM}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="$HOME/usrp-projects/data/har/ch${CSI_CHANNEL}"
mkdir -p "$OUT_DIR"
SESSION_LOG="$OUT_DIR/session_${SUBJECT}_$(date +%Y%m%d_%H%M%S).log"

# Build every (class, rep) pair, then shuffle deterministically from SEED so
# the exact order can be reproduced and reported.
mapfile -t PLAN < <(
    for c in $CLASSES; do
        for r in $(seq -w 1 "$REPS"); do
            echo "$c $r"
        done
    done | shuf --random-source=<(yes "$SEED")
)

TOTAL=${#PLAN[@]}

echo "=============================================================="
echo " SESSION  subject=$SUBJECT  channel=$CSI_CHANNEL  room=${ROOM:-unspecified}"
echo " classes  : $CLASSES"
echo " plan     : $REPS reps x $(echo $CLASSES | wc -w) classes = $TOTAL instances"
echo " duration : ${DURATION}s each  (~$(( TOTAL * (DURATION + 8) / 60 )) min total)"
echo " order    : randomised, seed=$SEED"
echo " log      : $SESSION_LOG"
echo "=============================================================="
echo
echo "Before you start, confirm all of these:"
echo "  [ ] TX laptop: wifi_tx_multi_hop.py says PARKED on Channel $CSI_CHANNEL"
echo "  [ ] TX laptop: packet_generator.py is running"
echo "  [ ] Antennas taped in place and NOT moved since the last session"
echo "  [ ] Door closed, nobody else moving in the room"
echo "  [ ] 'empty' reps: you must leave the room while they record"
echo
read -r -p "Press Enter to begin, Ctrl+C to abort... "

OK=0; SKIP=0; FAIL=0; N=0
FAILED_LIST=()

trap 'echo; echo "Session interrupted at $N/$TOTAL."; exit 130' INT

for entry in "${PLAN[@]}"; do
    read -r CLASS REP <<< "$entry"
    N=$(( N + 1 ))

    echo
    echo "--------------------------------------------------------------"
    echo " [$N/$TOTAL]  $SUBJECT / $CLASS / rep $REP   (ok=$OK skip=$SKIP fail=$FAIL)"
    echo "--------------------------------------------------------------"

    if [[ "$CLASS" == "empty" ]]; then
        echo " *** LEAVE THE ROOM NOW — this rep records an empty room ***"
    fi

    ROOM="${ROOM:-unspecified}" "$HERE/capture.sh" "$SUBJECT" "$CLASS" "$REP" "$DURATION"
    rc=$?

    case "$rc" in
        0) OK=$(( OK + 1 ));   echo "$(date -Is) OK   $CLASS $REP" >> "$SESSION_LOG" ;;
        2) SKIP=$(( SKIP + 1 )); echo "$(date -Is) SKIP $CLASS $REP (already recorded)" >> "$SESSION_LOG" ;;
        *) FAIL=$(( FAIL + 1 )); FAILED_LIST+=("$CLASS $REP")
           echo "$(date -Is) FAIL $CLASS $REP" >> "$SESSION_LOG" ;;
    esac

    # Stop early if the link has clearly died, rather than burning through the
    # rest of the plan producing unusable files.
    if [[ "$FAIL" -ge 5 && "$OK" -eq 0 ]]; then
        echo
        echo "!!! 5 failures and no successes — stopping." >&2
        echo "!!! Fix the link before continuing; re-run this script to resume." >&2
        break
    fi

    if (( N % BREAK_EVERY == 0 && N < TOTAL )); then
        echo
        read -r -p ">>> Break. $N/$TOTAL done. Press Enter to continue... "
    fi
done

echo
echo "=============================================================="
echo " SESSION COMPLETE  $SUBJECT  channel $CSI_CHANNEL"
echo "   recorded : $OK"
echo "   skipped  : $SKIP (already existed)"
echo "   failed   : $FAIL"
echo "=============================================================="

if (( FAIL > 0 )); then
    echo
    echo "Failed instances (delete the .csv, then re-run this script to retry):"
    printf '   %s\n' "${FAILED_LIST[@]}"
fi

echo
echo "Per-class counts now on disk:"
ls "$OUT_DIR"/*.csv 2>/dev/null \
    | xargs -n1 basename 2>/dev/null \
    | sed 's/_[0-9]*\.csv$//' \
    | sort | uniq -c | sed 's/^/   /'
