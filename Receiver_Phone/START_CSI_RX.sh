#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
exec env -u LD_LIBRARY_PATH -u LD_PRELOAD -u PYTHONHOME -u PYTHONPATH \
  -u QT_QPA_PLATFORM_PLUGIN_PATH -u QT_PLUGIN_PATH -u QML2_IMPORT_PATH \
  /usr/bin/python3 start_csi_rx.py "$@"
