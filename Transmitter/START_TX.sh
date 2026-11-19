#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
source ./ENV.sh
if [[ ! -f build/BUILD_OK.json ]]; then
    echo 'Build first: bash BUILD.sh' >&2
    exit 1
fi
/usr/bin/python3 ./check_setup.py
export TX_ADDR="${TX_ADDR:-192.168.10.9}"
export TX_CHANNEL=1
export TX_GAIN=15
ping -c 1 -W 2 "$TX_ADDR"
echo "TX USRP $TX_ADDR | Channel 1 (2412 MHz) | gain 15 dB | keep this open"
cd source/gr-ieee802-11/examples
exec /usr/bin/python3 wifi_tx_multi_hop.py
