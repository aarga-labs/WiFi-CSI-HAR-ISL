#!/usr/bin/env bash
#
# Capture one labelled activity or gesture instance to its own CSV.
#
#   ./capture.sh <subject> <class> <rep> [seconds]
#
#   e.g.  ./capture.sh rishi walk 03
#         ./capture.sh rishi hello 03 10
#
# Writes to  ~/usrp-projects/data/har/ch<CSI_CHANNEL>/<subject>_<class>_<rep>.csv
# plus a matching .json sidecar holding the exact interval the subject was
# performing, so the label lives with the data and needs no bookkeeping.
#
# Requires CSI_CHANNEL to be set to 1, 6 or 11 (the parked channel). The
# transmitter must be parked on the same channel with TX_CHANNEL.
#
# Environment:
#   CSI_CHANNEL      1|6|11  (required) channel both radios are parked on
#   RX_GAIN          receiver gain in dB (default 50, see wifi_rx.py)
#   RX_ADDR          receiver USRP address (default 192.168.10.9)
#   LINKUP_TIMEOUT   seconds to wait for the link before giving up (default 30)
#   MIN_RATE         Hz below which the instance is rejected (default 40)
#   CAPTURE_BEEP     command to run as the GO cue (default: terminal bell)

set -euo pipefail

SUBJECT="${1:?usage: capture.sh <subject> <class> <rep> [seconds]}"
ACTIVITY="${2:?usage: capture.sh <subject> <class> <rep> [seconds]}"
REP="${3:?usage: capture.sh <subject> <class> <rep> [seconds]}"
SECONDS_PER_INSTANCE="${4:-10}"

: "${CSI_CHANNEL:?set CSI_CHANNEL to 1, 6 or 11 first (and park the TX to match)}"

LINKUP_TIMEOUT="${LINKUP_TIMEOUT:-30}"
LINKUP_ROWS="${LINKUP_ROWS:-10}"
MIN_RATE="${MIN_RATE:-40}"
RX_GAIN="${RX_GAIN:-50}"

case "$CSI_CHANNEL" in
    1|6|11) ;;
    *) echo "CSI_CHANNEL must be 1, 6 or 11 — got '$CSI_CHANNEL'" >&2; exit 1 ;;
esac

# The filename is the label, and loaders split it on '_' into exactly three
# fields. An underscore inside a name silently mislabels the instance, so use
# 'sitstand', never 'sit_stand'.
if [[ "$SUBJECT" == *_* || "$ACTIVITY" == *_* ]]; then
    echo "no underscores in subject or class name (got '${SUBJECT}_${ACTIVITY}')" >&2
    echo "use e.g. 'sitstand' instead of 'sit_stand'." >&2
    exit 1
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXAMPLES_DIR="$HERE/gr-ieee802-11/examples"
OUT_DIR="$HOME/usrp-projects/data/har/ch${CSI_CHANNEL}"
mkdir -p "$OUT_DIR"

OUT="$OUT_DIR/${SUBJECT}_${ACTIVITY}_${REP}.csv"
META="${OUT%.csv}.json"
LOG="${OUT%.csv}.log"

if [[ -e "$OUT" ]]; then
    echo "refusing to overwrite existing $OUT" >&2
    echo "delete it first if you really meant to re-record this instance." >&2
    exit 2      # distinct from 1 so session.sh can treat it as "already done"
fi

export CSI_TA=02:00:00:00:00:01
export CSI_RA=02:00:00:00:00:02
export CSI_OUT="$OUT"
export CSI_CHANNEL RX_GAIN
[[ -n "${RX_ADDR:-}" ]] && export RX_ADDR

echo "=============================================================="
echo " channel   : $CSI_CHANNEL   (TX must be parked here too)"
echo " subject   : $SUBJECT"
echo " class     : $ACTIVITY   rep $REP"
echo " duration  : ${SECONDS_PER_INSTANCE}s"
echo " rx gain   : ${RX_GAIN} dB"
echo " output    : $OUT"
echo "=============================================================="

FLOWGRAPH_PID=""

cleanup() {
    if [[ -n "$FLOWGRAPH_PID" ]] && kill -0 "$FLOWGRAPH_PID" 2>/dev/null; then
        # SIGINT so wifi_rx.py takes its clean-shutdown path: sig_handler stops
        # the top block and extract_csi's destructor flushes and closes the CSV.
        # A plain SIGTERM would skip that and truncate the tail of the capture.
        kill -INT "$FLOWGRAPH_PID" 2>/dev/null || true
        for _ in $(seq 1 50); do
            kill -0 "$FLOWGRAPH_PID" 2>/dev/null || break
            sleep 0.1
        done
        kill -KILL "$FLOWGRAPH_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

rows_now() {
    if [[ -f "$OUT" ]]; then
        local n
        n=$(wc -l < "$OUT" 2>/dev/null || echo 1)
        echo $(( n > 0 ? n - 1 : 0 ))
    else
        echo 0
    fi
}

# ---------------------------------------------------------------------------
# Start the radio FIRST and wait until it is actually decoding frames.
#
# This ordering is the whole point. The previous version printed "GO", then
# started the flowgraph — but bringing up the USRP and acquiring OFDM sync
# takes several seconds, so the subject performed the first part of every
# activity into a radio that was not yet recording, and the CSV captured the
# tail (often including them stopping). Every instance was skewed the same way,
# which is worse than random noise: it is a systematic bias the model would
# happily learn.
# ---------------------------------------------------------------------------
echo
echo "Starting receiver, waiting for the link to come up..."

python3 "$EXAMPLES_DIR/wifi_rx.py" > "$LOG" 2>&1 &
FLOWGRAPH_PID=$!

LINKED=0
for _ in $(seq 1 $(( LINKUP_TIMEOUT * 10 )) ); do
    if ! kill -0 "$FLOWGRAPH_PID" 2>/dev/null; then
        echo
        echo "!!! The receiver exited during startup. Last lines of $LOG:" >&2
        tail -n 15 "$LOG" >&2
        exit 1
    fi
    if [[ "$(rows_now)" -ge "$LINKUP_ROWS" ]]; then
        LINKED=1
        break
    fi
    sleep 0.1
done

if [[ "$LINKED" -ne 1 ]]; then
    echo
    echo "!!! No CSI after ${LINKUP_TIMEOUT}s — not recording." >&2
    echo "!!! Check, in this order:" >&2
    echo "!!!   1. Is packet_generator.py running on the TX laptop?" >&2
    echo "!!!   2. Does TX_CHANNEL match CSI_CHANNEL=${CSI_CHANNEL}?" >&2
    echo "!!!   3. Does the TX console say PARKED on Channel ${CSI_CHANNEL}?" >&2
    echo "!!!   4. Last lines of $LOG:" >&2
    tail -n 15 "$LOG" >&2
    rm -f "$OUT"
    exit 1
fi

# ---------------------------------------------------------------------------
# The link is live. Cue the subject and record the exact interval.
# ---------------------------------------------------------------------------
echo "Link up. Get into position."
sleep 2

if [[ -n "${CAPTURE_BEEP:-}" ]]; then
    eval "$CAPTURE_BEEP" >/dev/null 2>&1 || true
else
    printf '\a'; sleep 0.15; printf '\a'
fi

GO_US=$(date +%s%6N)
echo
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
echo ">>> GO — perform '$ACTIVITY' continuously for ${SECONDS_PER_INSTANCE}s"
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

sleep "$SECONDS_PER_INSTANCE"

STOP_US=$(date +%s%6N)
printf '\a'
echo "<<< STOP"

cleanup
FLOWGRAPH_PID=""

# ---------------------------------------------------------------------------
# Provenance sidecar. go_us/stop_us bound the interval the subject was actually
# performing; the loader slices on them, so warm-up rows never reach training
# and no fixed "drop the first N seconds" guess is needed.
# ---------------------------------------------------------------------------
cat > "$META" <<JSON_EOF
{
  "subject": "$SUBJECT",
  "class": "$ACTIVITY",
  "rep": "$REP",
  "channel": $CSI_CHANNEL,
  "duration_s": $SECONDS_PER_INSTANCE,
  "go_us": $GO_US,
  "stop_us": $STOP_US,
  "rx_gain_db": $RX_GAIN,
  "rx_addr": "${RX_ADDR:-192.168.10.9}",
  "csi_ta": "$CSI_TA",
  "csi_ra": "$CSI_RA",
  "room": "${ROOM:-unspecified}",
  "notes": "${NOTES:-}",
  "recorded_at": "$(date -Is)"
}
JSON_EOF

echo
if [[ ! -f "$OUT" ]]; then
    echo "!!! No CSV produced — is the flowgraph starting at all? See $LOG" >&2
    exit 1
fi

# Judge only the labelled interval, not the warm-up.
if python3 "$HERE/qc.py" "$OUT" \
        --expect-channel "$CSI_CHANNEL" \
        --min-rate "$MIN_RATE" \
        --from-us "$GO_US" --to-us "$STOP_US"; then
    rm -f "$LOG"     # keep logs only for instances that failed
    echo "    -> $OUT"
    exit 0
else
    echo "!!!       instance kept at $OUT — inspect, then delete and re-record." >&2
    echo "!!!       flowgraph log: $LOG" >&2
    exit 1
fi
