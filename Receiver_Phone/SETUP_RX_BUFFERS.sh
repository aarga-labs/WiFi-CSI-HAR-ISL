#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
target=/etc/sysctl.d/90-fyp-usrp.conf
if [[ -f "$target" ]] && ! cmp -s usrp-buffers.conf "$target"; then
    sudo cp -p "$target" "${target}.backup.$(date +%Y%m%d_%H%M%S)"
fi
sudo install -m 644 usrp-buffers.conf "$target"
sudo sysctl -p "$target"
echo 'Receive-buffer setting applied and saved for restart. Start your next named run.'
