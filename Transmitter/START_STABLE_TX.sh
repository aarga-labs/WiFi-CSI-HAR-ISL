#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
source ./ENV.sh
exec /usr/bin/python3 ./stable_tx.py "$@"
