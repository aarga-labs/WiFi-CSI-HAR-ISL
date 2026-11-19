# FYP transmitter laptop — Fedora

## Current collection command

Use **`bash START_STABLE_TX.sh --gain 30`**. See [STABLE_TX_NOTES.md](STABLE_TX_NOTES.md) for the measured repair, waveform headroom and receiver calibration.

Copy `FYP_TX_Setup_Capture_Update.zip` to the new laptop's Downloads folder. It contains the two source modules (`gr-foo`, `gr-ieee802-11`), the transmit flowgraph, packet generator, and setup scripts.

## 1. Extract

```bash
cd ~/Downloads
unzip FYP_TX_Setup_Capture_Update.zip
cd FYP_TX_Setup_Capture_Update
```

If `unzip` is missing, run `sudo dnf install -y unzip` first. Extract into a fresh folder; do not merge this source bundle with a build copied from another machine.

## 2. Install dependencies — once

```bash
bash INSTALL_FEDORA.sh
```

This installs Fedora packages using `dnf`, including GNU Radio 3.10, GNU Radio development files, UHD/tools/host firmware files, compilers, Qt5, and Python bindings dependencies. It does not flash or reprogram the USRP. Internet and sudo are needed for package installation.

## 3. Build both modules — once on this laptop

```bash
bash BUILD.sh
```

Wait for **BUILD PASSED**. This builds `gr-foo`, builds `gr-ieee802-11`, generates the PHY hierarchy, then checks the imports. It installs built modules into **this folder's `install/`**, without sudo or global module replacement. Defaults to two compiler jobs. Build outputs are specific to the new laptop's installed Python/GNU Radio; rebuild there rather than copying built binaries from the receiver laptop.

## 4. Connect the TX USRP and configure Ethernet

Connect the powered TX N210 directly to the laptop using gigabit Ethernet. Keep Wi-Fi available separately if needed. Attach the TX antenna to the USRP's **TX/RX** connector.

```bash
bash SETUP_NETWORK.sh
```

The script lists interfaces and asks which physical Ethernet interface is connected to the USRP. Type that interface name, e.g. `enp2s0`, and press Enter. It assigns `192.168.10.1/24` to that interface, pings the TX address, and runs UHD discovery. Do not select Wi-Fi or a bridge. The receiver laptop's interface name may differ from this laptop's.

This kit defaults to **TX `192.168.10.9`**, matching the earlier physical TX code; the user confirmed **RX `192.168.10.7`**. Verify `.9` replies and UHD identifies the TX N210. Changing laptops does not change the USRP device address. If TX is at a different verified address, set `TX_ADDR` explicitly for both network setup and transmitter launch; no source edits are required.

The two laptops may each use `192.168.10.1` because their direct USRP Ethernet links are separate. Do not connect both of those interfaces to the same shared LAN with duplicate host addresses.

## 5. Start the transmitter

From this folder run `bash START_STABLE_TX.sh --gain 30`. Keep this terminal open through all blocks.
The transmitter supplies 200 probes/s and records requested and actual radio settings in `logs/`.
An available UHD asynchronous message port is sampled for diagnostics. Keep the terminal output too.
Ctrl+C closes the transmitter and writes its final status. Use the same command after restarting.
The phone cue scheduler and receiver run on the other laptop.

## Validation and limitations

The bundle's sources and scripts were checked locally with GNU Radio 3.10. Fedora package names were checked against the official Fedora package listings. The Fedora package install and physical TX operation must still be run and verified on the new laptop. A successful local build does not establish radio packet reception or CSI/phone timing alignment.

If any step fails, stop at that step and share the final error lines. Do not proceed to participant collection until the receiver shows incoming saved CSI packets and the paired pilot has been reviewed.

Sources: https://packages.fedoraproject.org/pkgs/gnuradio/ , https://packages.fedoraproject.org/pkgs/uhd/ , https://wiki.gnuradio.org/index.php/OutOfTreeModules
