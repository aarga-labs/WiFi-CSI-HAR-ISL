#!/usr/bin/env bash
#
# Check everything the receiver needs, before a subject is standing in the room.
#
#   ./preflight.sh
#
# Read-only: probes and reports, changes nothing. Run it at the start of every
# collection day, and any time a capture misbehaves.

set -uo pipefail

RX_ADDR="${RX_ADDR:-192.168.10.9}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PASS=0; WARN=0; FAIL=0

ok()   { echo "  [ OK ] $*"; PASS=$((PASS+1)); }
warn() { echo "  [WARN] $*"; WARN=$((WARN+1)); }
bad()  { echo "  [FAIL] $*"; FAIL=$((FAIL+1)); }

echo "=============================================================="
echo " RECEIVER PREFLIGHT"
echo "=============================================================="

echo
echo "1. Python and GNU Radio"
python3 -c "import gnuradio" 2>/dev/null \
    && ok "gnuradio imports" || bad "gnuradio does not import"
python3 -c "import ieee802_11" 2>/dev/null \
    && ok "ieee802_11 module imports" \
    || bad "ieee802_11 does not import — build it (RECEIVER.md Part 2)"

if python3 -c "import ieee802_11; assert hasattr(ieee802_11.extract_csi,'set_channel')" 2>/dev/null; then
    ok "extract_csi.set_channel present"
else
    bad "extract_csi has no set_channel — an old .so is installed; rebuild + sudo make install + sudo ldconfig"
fi

echo
echo "2. Installed CSI block"
SO=$(ls /usr/local/lib64/libgnuradio-ieee802_11.so 2>/dev/null \
     || ls /usr/local/lib/libgnuradio-ieee802_11.so 2>/dev/null | head -1)
if [[ -n "${SO:-}" && -f "$SO" ]]; then
    ok "found $SO"
    strings "$SO" | grep -q "CSI_TA" \
        && ok "env-var interface (CSI_TA) compiled in" \
        || bad "no CSI_TA in the .so — old block installed, rebuild"
    strings "$SO" | grep -q "address 2" \
        && ok "Data-frame TA/RA fallback compiled in" \
        || bad "no 'address 2' fallback — every Data frame will be dropped, rebuild"
    if strings "$SO" | grep -q "usrp-projects/data"; then
        ok "default output directory is \$HOME-anchored"
    else
        warn "could not confirm the default output dir; always set CSI_OUT (capture.sh does)"
    fi
else
    bad "libgnuradio-ieee802_11.so not found — run 'sudo make install && sudo ldconfig'"
fi

echo
echo "3. USRP at $RX_ADDR"
if command -v uhd_find_devices >/dev/null 2>&1; then
    FOUND=$(uhd_find_devices 2>/dev/null | grep -oE "addr: [0-9.]+" | awk '{print $2}' | sort -u)
    if [[ -z "$FOUND" ]]; then
        bad "uhd_find_devices found no USRPs at all — check cable and 'ip addr'"
    else
        echo "         USRPs answering: $(echo $FOUND | tr '\n' ' ')"
        if echo "$FOUND" | grep -qx "$RX_ADDR"; then
            ok "$RX_ADDR is present — matches the receiver default"
        else
            bad "$RX_ADDR NOT found. Either set RX_ADDR to one of the above, e.g."
            echo "         export RX_ADDR=$(echo "$FOUND" | head -1)"
        fi
    fi
else
    warn "uhd_find_devices not on PATH — cannot probe the radio"
fi

if ping -c 1 -W 2 "$RX_ADDR" >/dev/null 2>&1; then
    ok "$RX_ADDR responds to ping"
else
    warn "$RX_ADDR does not ping (some N210 configs still work; the probe above is authoritative)"
fi

echo
echo "4. Capture tooling"
[[ -x "$HERE/capture.sh" ]] && ok "capture.sh is executable" || bad "capture.sh not executable (chmod +x)"
[[ -x "$HERE/session.sh" ]] && ok "session.sh is executable" || bad "session.sh not executable (chmod +x)"
python3 "$HERE/qc.py" --help >/dev/null 2>&1 \
    && ok "qc.py runs" || bad "qc.py does not run"

echo
echo "5. Collection settings"
if [[ -n "${CSI_CHANNEL:-}" ]]; then
    case "$CSI_CHANNEL" in
        1|6|11) ok "CSI_CHANNEL=$CSI_CHANNEL (park the TX on the same channel)" ;;
        *) bad "CSI_CHANNEL='$CSI_CHANNEL' is not 1, 6 or 11" ;;
    esac
else
    warn "CSI_CHANNEL not set — set it before capturing, or the RX will hop (~2.4 Hz, unusable)"
fi
echo "         RX_GAIN=${RX_GAIN:-50} dB (raise for weak gesture signals, lower if saturated)"

AVAIL=$(df -Pm "$HOME" | awk 'NR==2{print $4}')
if [[ "${AVAIL:-0}" -gt 2000 ]]; then
    ok "disk space: ${AVAIL} MB free (a 10 s instance is ~1 MB)"
else
    warn "only ${AVAIL} MB free in \$HOME"
fi

echo
echo "=============================================================="
echo " $PASS passed, $WARN warnings, $FAIL failures"
if (( FAIL > 0 )); then
    echo " NOT READY — fix the failures above before collecting."
else
    echo " Receiver looks ready. Confirm on the TX laptop:"
    echo "   - wifi_tx_multi_hop.py prints PARKED on Channel ${CSI_CHANNEL:-<N>}"
    echo "   - packet_generator.py is running"
fi
echo "=============================================================="
exit $(( FAIL > 0 ? 1 : 0 ))
