# 3 — Commands Cheat Sheet

Every command needed during capture and processing, grouped by machine.

---

## MacBook (transmitter)

### WiFi MAC address of the MacBook (→ `CSI_TA`)
```bash
ifconfig en0 | grep ether
```

### Hotspot BSSID (→ `CSI_RA`) + current channel, signal, rate
Hold **Option (⌥)** and click the Wi-Fi icon in the menu bar — the connected
network section shows BSSID, Channel, RSSI, Tx Rate.

Terminal alternative (macOS 14+, needs sudo):
```bash
sudo wdutil info | grep -E "BSSID|Channel|RSSI|Tx Rate"
```

### Stop the Mac from rotating its MAC (do once)
System Settings → Wi-Fi → *(hotspot network)* → Details → **Private Wi-Fi Address → OFF**
(then re-check the MAC — it changes once after switching this off).

### Find the hotspot's gateway IP (the phone)
```bash
netstat -nr | grep default        # first line, e.g. 172.20.10.1
```

### Traffic generation — ping at ~100 packets/second (needs sudo)
```bash
sudo ping -i 0.01 172.20.10.1
```
- `-i 0.01` = 10 ms interval ≈ 100 pkt/s (intervals < 0.2 s require sudo on macOS)
- `-i 0.005` ≈ 200 pkt/s if you need more headroom
- add `-s 200` to change payload size (sometimes changes the WiFi rate used)

### Traffic generation — iperf3 UDP (steadier stream; fallback if ping decode rate is low)
Phone side: install an iperf3 server app (e.g. "PingTools"/"iPerf3" from Play Store), start server.
```bash
brew install iperf3                       # once
iperf3 -u -c <phone-ip> -b 2M -l 200 -t 600
```
- `-u` UDP, `-b 2M` bandwidth, `-l 200` datagram size, `-t 600` run 10 min
- packets/s = bandwidth / size → 2 Mbit/s ÷ 200 B ≈ 1250 pkt/s (plenty)

### Check ping is actually flowing
```bash
ping -c 5 172.20.10.1                     # quick reachability sanity check
```

---

## Android phone (access point)

- Hotspot on, **2.4 GHz band** (Settings → Hotspot → sometimes under "AP Band" / "Speed & compatibility": choose 2.4 GHz).
- BSSID + channel: easiest read from the **MacBook** (Option-click Wi-Fi, above), or install a
  WiFi analyzer app on a second phone connected to nothing.
- Channel cannot be pinned on most stock Androids — it may hop when the hotspot restarts.
  **Therefore: check channel at every session start** and keep the hotspot running all session.
- Keep the phone plugged into a charger (battery saver can throttle the hotspot).

### Channel → frequency table (2.4 GHz)
| Channel | `freq` in wifi_rx |
|---|---|
| 1 | `2412000000` |
| 6 | `2437000000` |
| 11 | `2462000000` |

---

## Fedora laptop (receiver)

### USRP alive?
```bash
uhd_find_devices                                   # expects addr=192.168.10.7
ping -c 3 192.168.10.7
```

### Ethernet interface config (if the link is dead after reboot)
```bash
nmcli device status                                # eno1 should be connected
ip addr show eno1                                  # expects 192.168.10.1/24
sudo ip addr add 192.168.10.1/24 dev eno1          # if missing
```

### Live spectrum check (gain/saturation, is the hotspot visible?)
```bash
uhd_fft --args="addr=192.168.10.7" -f 2.462e9 -s 20e6
```

### Run a capture
```bash
export CSI_TA=42:23:9e:d9:54:24                    # today's verified MacBook MAC
export CSI_RA=e2:63:84:5b:14:29                    # today's verified hotspot BSSID
export CSI_OUT=~/usrp-projects/data/S03_squat_amrith_20260716.csv   # or leave unset
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
```
Debug filters off: `export CSI_TA=any CSI_RA=any` (accept every decoded frame).

### Rep marking (second terminal, while flowgraph runs)
```bash
cd ~/usrp-projects/USRP_lib/csi_tools
python3 session_logger.py --action squat --subject amrith --name S03_squat_amrith_20260716 --channel 11
python3 session_logger.py --action walk  --subject amrith --continuous --name S07_walk_amrith_20260716
```

### Watch the CSV grow live (rough rows/s by eye)
```bash
watch -n 1 'wc -l ~/usrp-projects/data/S03_squat_amrith_20260716.csv'
```

### After every session — sanity check
```bash
python3 ~/usrp-projects/USRP_lib/csi_tools/check_capture.py ~/usrp-projects/data/S03_squat_amrith_20260716.csv
# opens nothing; look at the printed PASS/FAIL and the saved *_check.png plot
```

### Quick CSV peeks
```bash
wc -l file.csv                                     # row count
head -2 file.csv | cut -d, -f1-6                   # header + first row, first columns
tail -1 file.csv | cut -d, -f1,2                   # last packet index + timestamp
```

### Processing & training (details in 2_TRAINING_GUIDE.md)
```bash
cd ~/usrp-projects/USRP_lib/csi_tools
python3 segment_windows.py <capture.csv> --labels <labels.csv> --out-dir ~/usrp-projects/data/windows
python3 segment_windows.py <capture.csv> --action walk --subject amrith --out-dir ~/usrp-projects/data/windows
python3 make_images.py ~/usrp-projects/data/windows --out ~/usrp-projects/data/dataset
python3 train_imgfi.py ~/usrp-projects/data/dataset --test-subject gowreesh
```

### Windows-per-class count (balance check)
```bash
for d in ~/usrp-projects/data/windows/*/; do echo "$d: $(ls "$d" | wc -l)"; done
```

### Rebuild gr-ieee802-11 after any C++ change
```bash
cd ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/build
make -j$(nproc)
sudo make install && sudo ldconfig
```

### Regenerate wifi_rx.py after editing the .grc in Companion
```bash
cd ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples
grcc wifi_rx.grc -o .
```

### Backup the data after each collection day (do it!)
```bash
tar czf ~/csi_backup_$(date +%Y%m%d).tar.gz ~/usrp-projects/data/*.csv ~/usrp-projects/data/*.json
# then copy to a USB stick / Google Drive
```

---

## Console messages decoder (flowgraph terminal)

| Message | Meaning |
|---|---|
| `extract_csi: TA filter = ..., RA filter = ...` | Config the block actually loaded — verify it's today's values |
| `extract_csi: writing to <path>` | The file being written — verify it's your session file |
| `seen TA=.. RA=.. (MATCH)` | Your link decoded and saved ✓ |
| `seen TA=.. RA=.. (no match)` | Other WiFi traffic (printed once per pair). If YOUR devices appear here, a MAC rotated |
| `saved N packets (~X rows/s)` | Live rate — keep an eye on it all session (want ≥ 50) |
| `total saved packets: N` | Printed at shutdown — write it on the log sheet |
| `Unable to set thread priority`, `No GPSDO`, `Odd decimation` | Harmless, ignore |
