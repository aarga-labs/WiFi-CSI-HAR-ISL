#!/usr/bin/env bash
#
# Capture one labelled activity instance to its own CSV.
#
#   ./capture.sh <subject> <activity> <rep> [seconds]
#
# e.g.  ./capture.sh rishi walk 03
#
# Writes to  ~/usrp-projects/data/har/ch<CSI_CHANNEL>/<subject>_<activity>_<rep>.csv
# so the label lives in the filename and needs no separate bookkeeping.
#
# Requires CSI_CHANNEL to be set to 1, 6 or 11 (the parked channel). The
# transmitter must be parked on the same channel with TX_CHANNEL.

set -euo pipefail

SUBJECT="${1:?usage: capture.sh <subject> <activity> <rep> [seconds]}"
ACTIVITY="${2:?usage: capture.sh <subject> <activity> <rep> [seconds]}"
REP="${3:?usage: capture.sh <subject> <activity> <rep> [seconds]}"
SECONDS_PER_INSTANCE="${4:-10}"

: "${CSI_CHANNEL:?set CSI_CHANNEL to 1, 6 or 11 first (and park the TX to match)}"

case "$CSI_CHANNEL" in
    1|6|11) ;;
    *) echo "CSI_CHANNEL must be 1, 6 or 11 — got '$CSI_CHANNEL'" >&2; exit 1 ;;
esac

# The filename is the label, and loaders split it on '_' into exactly three
# fields. An underscore inside a name silently mislabels the instance, so use
# 'sitstand', never 'sit_stand'.
if [[ "$SUBJECT" == *_* || "$ACTIVITY" == *_* ]]; then
    echo "no underscores in subject or activity name (got '${SUBJECT}_${ACTIVITY}')" >&2
    echo "use e.g. 'sitstand' instead of 'sit_stand'." >&2
    exit 1
fi

EXAMPLES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/gr-ieee802-11/examples" && pwd)"
OUT_DIR="$HOME/usrp-projects/data/har/ch${CSI_CHANNEL}"
mkdir -p "$OUT_DIR"

OUT="$OUT_DIR/${SUBJECT}_${ACTIVITY}_${REP}.csv"

if [[ -e "$OUT" ]]; then
    echo "refusing to overwrite existing $OUT" >&2
    echo "delete it first if you really meant to re-record this instance." >&2
    exit 1
fi

export CSI_TA=02:00:00:00:00:01
export CSI_RA=02:00:00:00:00:02
export CSI_OUT="$OUT"

echo "=============================================================="
echo " channel   : $CSI_CHANNEL   (TX must be parked here too)"
echo " subject   : $SUBJECT"
echo " activity  : $ACTIVITY   rep $REP"
echo " duration  : ${SECONDS_PER_INSTANCE}s"
echo " output    : $OUT"
echo "=============================================================="
echo
echo "Get into position. Recording starts in 3 seconds..."
sleep 3
echo ">>> GO — perform '$ACTIVITY' continuously for ${SECONDS_PER_INSTANCE}s <<<"

# -s INT so the flowgraph takes the same clean-shutdown path as Ctrl+C:
# sig_handler stops the top block, and extract_csi's destructor flushes
# and closes the CSV. A plain SIGTERM would skip that.
timeout -s INT "$SECONDS_PER_INSTANCE" \
    python3 "$EXAMPLES_DIR/wifi_rx.py" || true

echo
if [[ -f "$OUT" ]]; then
    ROWS=$(( $(wc -l < "$OUT") - 1 ))
    RATE=$(awk -v r="$ROWS" -v s="$SECONDS_PER_INSTANCE" 'BEGIN{printf "%.1f", r/s}')
    echo "--- $ROWS rows  (~${RATE} Hz)  ->  $OUT"

    # Below ~20 Hz there is not enough temporal detail to resolve human
    # motion, so flag it now rather than after a whole session is recorded.
    if (( ROWS < SECONDS_PER_INSTANCE * 20 )); then
        echo "!!! WARNING: under 20 Hz — do not build a dataset on this."
        echo "!!! Check that TX_CHANNEL matches CSI_CHANNEL, packet_generator.py"
        echo "!!! is running, and PPS is 200."
    fi
else
    echo "!!! No CSV produced — is the flowgraph starting at all?"
    exit 1
fi
