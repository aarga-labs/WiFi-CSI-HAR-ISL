# NOTICE

This project includes code derived from and built on top of
**gr-ieee802.11**, an IEEE 802.11 a/g/p transceiver implementation for
GNU Radio.

## Upstream project

- **Project:** gr-ieee802.11
- **Author:** Bastian Bloessl <bloessl@ccs-labs.org>
- **Repository:** https://github.com/bastibl/gr-ieee802-11
- **License:** GNU General Public License v3.0 (GPL-3.0)
- **Project page:** https://www.wime-project.net

## 1. Files modified from upstream

| File in this repo | Derived from | Description of changes |
|---|---|---|
| `gnuradio/wifi_rx.grc` | `examples/wifi_rx.grc` | Modified the receive flowgraph to route decoded frames through a new `WiFi Extract CSI` block (see below) for per-subcarrier CSI capture. |
| `gnuradio/wifi_rx.py` | Auto-generated Python from `wifi_rx.grc` | Regenerated/modified to instantiate and wire up the new CSI extraction block alongside the standard receive chain. |

Both files retain the original copyright notice from gr-ieee802.11 and
carry modification notices with dates, as required by Section 5 of
GPL-3.0.

## 2. New block added to the gr-ieee802.11 module

`WiFi Extract CSI` (`ieee802_11.extract_csi`) is a new GNU Radio block
written for this project and added into the gr-ieee802.11 module
structure, so it can access decoded-frame PDUs the same way the module's
other blocks do. It extracts the 52-subcarrier complex channel estimate
from each decoded WiFi frame for use in activity detection.

| File in this repo | Status | Notes |
|---|---|---|
| `gnuradio/extract_csi_block/extract_csi_impl.cc` | New, original | C++ implementation of the CSI extraction block |
| `gnuradio/extract_csi_block/extract_csi_impl.h` | New, original | Private implementation header |

> **Note:** the public block header (`extract_csi.h`) and the GRC block
> definition (`extract_csi.block.yml`) are not redistributed here. To build the
> block, place the two files above into the corresponding `lib/` directory of a
> gr-ieee802.11 checkout and add the matching public header and `.block.yml`
> following that module's existing blocks as a template.

Because this block is integrated into and built as part of the
gr-ieee802.11 module (using its build system and internal APIs) rather
than distributed as an independent program, it is released under the
same license as the module it extends — GPL-3.0.

## License

All files listed above — modified and new — are distributed under the
**GNU General Public License v3.0**. See [`LICENSE`](./LICENSE) for the
full text. Other original content in this repository (data collection
scripts, deep learning notebooks, and documentation) is also released
under GPL-3.0 for consistency, unless stated otherwise in an individual
file.

## Additional dependencies

This project also depends on the following upstream/third-party
components, which are **not redistributed** in this repository and must
be installed separately:

- [GNU Radio](https://www.gnuradio.org/) — GPL-3.0
- [gr-ieee802.11](https://github.com/bastibl/gr-ieee802-11) — GPL-3.0
- [gr-foo](https://github.com/bastibl/gr-foo) (dependency of gr-ieee802.11)
- [UHD](https://github.com/EttusResearch/uhd) (Ettus Research USRP Hardware Driver)

Users must install these according to the instructions in their
respective repositories before using the files in this project.

## Disclaimer

This is a research/academic project. The modified and added files are
provided "as is", without warranty of any kind, consistent with
Sections 15 and 16 of the GPL-3.0 license.