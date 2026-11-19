# Wi-Fi CSI Activity & Sign-Gesture Recognition

The capture pipeline for Wi-Fi CSI and phone inertial measurements.

| Directory | Contents |
| --- | --- |
| [Receiver_Phone](Receiver_Phone) | CSI receiver, Android app, browser controller, paired recording scripts and quality checks |
| [Transmitter](Transmitter) | GNU Radio transmitter source, Linux setup scripts and the stable Wi-Fi probe |
| [Radio_Source](Radio_Source) | GNU Radio flowgraphs and the source used to build the receiver |
| [Documentation](Documentation) | Recording procedure and participant guide |

## Start the pipeline

Use the Linux system Python and compatible GNU Radio, UHD and GNU Radio development libraries. Build each radio runtime on its own laptop.

1. In `Transmitter`, run `bash BUILD.sh` and `bash START_STABLE_TX.sh --gain 30`. The [Fedora guide](Transmitter/README_FEDORA.md) covers dependencies and Ethernet setup. Use the `Transmitter` directory in this checkout.
2. In `Receiver_Phone`, run `./BUILD_QUIET_RX.sh` and `./START_CSI_RX.sh --check`. The check verifies the GNU Radio runtime without opening hardware.
3. Launch `./START_WIFI.sh` or `./START_USB.sh`. Run the [paired recording commands](Receiver_Phone/RUN_COMMANDS.md) from `Receiver_Phone`.

The controller creates local session files when first launched. Existing participant recordings, calibration traces and the source labels used by historical audits are kept in the private project workspace.
