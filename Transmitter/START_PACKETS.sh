#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
export PPS=200
export PAYLOAD_SIZE=100
export LABEL=paired_collection
echo 'Start only after the TX window says PARKED on Channel 1. Keep this terminal open.'
exec /usr/bin/python3 source/gr-ieee802-11/examples/packet_generator.py
