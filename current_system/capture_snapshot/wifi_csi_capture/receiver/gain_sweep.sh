#!/usr/bin/env bash
#
# gain_sweep.sh — find the RX gain that gives the most CSI rows for the
# CURRENT room / antenna setup. Run it once whenever the setup changes.
#
#   ./gain_sweep.sh                 # 20 s per gain step
#   ./gain_sweep.sh 30              # 30 s per step
#   GAINS="10 15 20 25" ./gain_sweep.sh
#
# Before running: the transmitter must be running and parked
#   TX_CHANNEL=1 python3 wifi_tx_multi_hop.py      +   PPS=200 python3 packet_generator.py
# Keep the room as it will be during recording (nobody walking through the link).
#
# For every gain it records one CSV and prints:
#   rows/s   — CSI rows saved per second (higher = better; want 100+)
#   mean|H|  — average CSI amplitude (grows with gain; if rows/s drops while
#              this keeps rising, the receiver is overloaded = too much gain)
# Then it suggests the best gain. Use it as:  RX_GAIN=<best> python3 wifi_rx.py

set -uo pipefail

SECS="${1:-20}"
GAINS="${GAINS:-0 4 8 12 16 20 24 28 31.5}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EX="$HERE/gr-ieee802-11/examples"
OUT="$HOME/usrp-projects/data/gainsweep/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

export CSI_TA="${CSI_TA:-02:00:00:00:00:01}"
export CSI_RA="${CSI_RA:-02:00:00:00:00:02}"

echo "RX gain sweep: ${SECS}s per step, gains: $GAINS"
echo "Results: $OUT"
echo

{
printf "%-8s %-8s %-10s %-10s\n" "gain_dB" "rows" "rows/s" "mean|H|"
for g in $GAINS; do
    export CSI_OUT="$OUT/gain_${g}.csv"
    ( cd "$EX" && RX_GAIN="$g" timeout -s INT "$SECS" python3 wifi_rx.py > "$OUT/gain_${g}.log" 2>&1 )
    python3 - "$CSI_OUT" "$g" <<'PYEOF'
import csv, math, sys
path, g = sys.argv[1], sys.argv[2]
try:
    rows = list(csv.reader(open(path)))[1:]
except FileNotFoundError:
    rows = []
n = len(rows)
if n > 1:
    ts = [int(r[1]) for r in rows]
    dur = (ts[-1] - ts[0]) / 1e6 or 1.0
    amp = sum(math.hypot(float(r[3 + 2*k]), float(r[4 + 2*k]))
              for r in rows for k in range(52)) / (52 * n)
    print(f"{g:<8} {n:<8} {n/dur:<10.1f} {amp:<10.3f}")
else:
    print(f"{g:<8} {n:<8} {0.0:<10.1f} {'-':<10}")
PYEOF
done
} | tee "$OUT/summary.txt"

BEST=$(tail -n +2 "$OUT/summary.txt" | sort -k3 -g -r | head -1)
echo
echo "Best: gain $(echo "$BEST" | awk '{print $1}') dB  ->  $(echo "$BEST" | awk '{print $3}') rows/s"
echo "If two neighbouring gains are almost equal, pick the LOWER one (more headroom)."
echo "Record with:  RX_GAIN=$(echo "$BEST" | awk '{print $1}') python3 wifi_rx.py"
