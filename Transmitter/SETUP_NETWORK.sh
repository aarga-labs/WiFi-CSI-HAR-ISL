#!/usr/bin/env bash
set -euo pipefail
ip -br link
FYP_TX_IFACE="${1:-}"
if [[ -z "$FYP_TX_IFACE" ]]; then
    read -r -p 'Type the Ethernet interface connected directly to the TX USRP: ' FYP_TX_IFACE
fi
if [[ ! "$FYP_TX_IFACE" =~ ^[[:alnum:]_.:-]+$ || ! -e "/sys/class/net/$FYP_TX_IFACE/device" || -d "/sys/class/net/$FYP_TX_IFACE/wireless" ]]; then
    echo 'Choose a physical Ethernet interface from the list, not Wi-Fi or a bridge.' >&2
    exit 1
fi
sudo ip link set "$FYP_TX_IFACE" up
sudo ip address replace 192.168.10.1/24 dev "$FYP_TX_IFACE"
FYP_TX_ADDRESS="${TX_ADDR:-192.168.10.9}"
ping -c 3 "$FYP_TX_ADDRESS"
uhd_find_devices --args="addr=$FYP_TX_ADDRESS"
echo 'Check that UHD lists the intended TX N210. Next: bash START_TX.sh'
