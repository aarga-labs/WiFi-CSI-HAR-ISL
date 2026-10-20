## What this repo is

A WiFi **CSI (Channel State Information) human-activity-recognition** project built on a USRP N210. The USRP passively sniffs 802.11 frames on a link between a MacBook and an Android hotspot; a person moving between them perturbs the channel, and the per-packet channel estimate (52 complex subcarriers) becomes the sensing signal. Captured CSI is turned into images and fed to a small CNN (the "ImgFi" pipeline) to classify 7 activities: `walk`, `squat`, `bend`, `drink`, `nod`, `noaction` (person still), `empty` (nobody).

Not a git repository. Three numbered guides at the root are the authoritative operator docs — read them before touching capture or training:
- [1_DATA_CAPTURE_GUIDE.md](1_DATA_CAPTURE_GUIDE.md) — end-to-end collection, the verification gates, session workflow.
- [2_TRAINING_GUIDE.md](2_TRAINING_GUIDE.md) — the CSV→model pipeline with the reasoning behind each step.
- [3_COMMANDS_CHEATSHEET.md](3_COMMANDS_CHEATSHEET.md) — every command, grouped by machine.

## Layout: two vendored trees + a thin project layer

The project's own work is small and lives in three places; everything else is upstream code cloned in.

- **`csi_tools/`** — the project's Python pipeline (data collection + ImgFi training). This and the modified `extract_csi` block are the only original code.
- **`gnuradio/gr-ieee802-11/`** — a clone of Bastian Bloessl's `gr-ieee802-11` OOT module. **One block is modified**: `lib/extract_csi_impl.{cc,h}` (see below). Treat the rest as upstream — don't refactor it.
- **`usrp/uhd/`** — a full clone of Ettus UHD (the USRP driver). Vendored reference only; the project does not build or modify it. Ignore unless a hardware/driver question specifically requires it.
- **`gnuradio/extract_csi_impl.{cc,h}`** (root of `gnuradio/`) — the **pristine upstream** version of the block (streams CSI out + tags, no CSV). Kept as a backup/reference. The *active* block is the modified copy under `gr-ieee802-11/lib/`; don't confuse the two.

## The one modified block: `extract_csi`

`gnuradio/gr-ieee802-11/lib/extract_csi_impl.cc` is the heart of the project. Upstream's version streams CSI vectors downstream; this version instead consumes the decoded-frame PDU, **filters by MAC, and writes a CSV directly**. Its `work()` is a no-op stub — all logic is in `handle_pdu`.

**It is configured entirely by environment variables — never recompile to change a MAC or output path:**

| Var | Meaning | `unset`/default |
|---|---|---|
| `CSI_TA` | accept only frames FROM this MAC (MacBook), or `any` | falls back to a hardcoded default MAC |
| `CSI_RA` | accept only frames TO this MAC (hotspot BSSID), or `any` | hardcoded default |
| `CSI_OUT` | output CSV path (appends, never overwrites) | timestamped `~/usrp-projects/data/csi_YYYYmmdd_HHMMSS.csv` |

CSV columns: `Packet, Timestamp_us, SC0_Re, SC0_Im, … SC51_Re, SC51_Im`. `Timestamp_us` is wall-clock microseconds from the same clock `session_logger.py` uses, which is how reps are later cut out. The block prints each distinct `seen TA=.. RA=..` pair once and a `(MATCH)`/`(no match)` tag — the primary way to catch a rotated MAC live.

## Build / run

**Rebuild + install after any C++ change to the block:**
```bash
cd ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/build
make -j$(nproc)
sudo make install && sudo ldconfig
```
`sudo` is interactive — the user must run the install step themselves; don't assume it can be done non-interactively.

**Run a capture** (the flowgraph that drives the USRP is the generated `wifi_rx.py`):
```bash
export CSI_TA=<macbook-mac> CSI_RA=<hotspot-bssid> CSI_OUT=<path.csv>   # env, then:
python3 ~/usrp-projects/USRP_lib/gnuradio/gr-ieee802-11/examples/wifi_rx.py
```
USRP is at `addr=192.168.10.7` (Fedora side `eno1` = `192.168.10.1/24`), `samp_rate=20e6`, source `gain=50`, `freq=2462000000` (channel 11). After editing `wifi_rx.grc` in GNU Radio Companion, regenerate with `grcc wifi_rx.grc -o .`.

## The ImgFi pipeline (`csi_tools/`)

Ordered stages, each a standalone script:

1. **`session_logger.py`** — run alongside the flowgraph; ENTER marks rep start/end, writing `<name>_labels.csv` (+ `_meta.json`) with `t_start_us`/`t_end_us`. `--continuous` for walk/noaction/empty (single take).
2. **`segment_windows.py`** — CSV → per-window amplitude matrices (`52 × 200`, .npy). Computes `|H|=hypot(Re,Im)` (**amplitude only — raw phase is unusable**, the USRP isn't synced to the transmitter) and resamples each 2 s window onto a uniform 100 Hz grid. Two modes: `--labels` (discrete reps) or `--action/--subject` (auto-chunk continuous takes).
3. **`make_images.py`** — each subcarrier's series → one **RT (recurrence) image** `RT[i,j]=|xᵢ−xⱼ|`, 224×224 grayscale PNG. One image *per subcarrier* → the dataset is ×52 larger; ImgFi's best-performing (and cheapest) of its 5 conversion methods.
4. **`train_imgfi.py`** — 3-conv-layer CNN. Reports **per-image** (diagnostic) and **per-window** (52-image majority vote — the real accuracy) numbers.
5. **`check_capture.py`** — QA a capture: rows/s, gaps, NaN/zero/constant columns, and an amplitude-vs-time PNG for the "wiggle test".

**Critical rule enforced by `train_imgfi.py`: splits are by SUBJECT (`--test-subject`) or filename substring (`--test-match`), NEVER random.** All 52 images of one window come from the same 2 seconds; a random shuffle leaks near-duplicates across train/test and produces a meaningless ~99%. The script refuses to run without one of those flags. Validation is likewise split by window, not image.

## Environment gotchas (not visible in the code)

- **MACs rotate.** Both the MacBook (`CSI_TA`) and the Android hotspot BSSID (`CSI_RA`) use randomized MACs. Re-verify every session; if the console shows your devices under `(no match)`, a MAC rotated — update the env vars and restart.
- **Hotspot channel drifts** (1/6/11). `freq` in the flowgraph must match the live channel (ch 11 → `2462000000`). Check every session.
- **The rate gate is the make-or-break check.** Target ~100 rows/s, gate ≥50. If low with a `(MATCH)`, the likely cause is the MacBook sending **802.11n (HT) frames, which gr-ieee802-11 cannot decode** (legacy OFDM only) — see the HT troubleshooting in [1_DATA_CAPTURE_GUIDE.md](1_DATA_CAPTURE_GUIDE.md).
- **`torchvision` is intentionally NOT installed** — `train_imgfi.py` uses only `torch`, `numpy`, and `PIL` on purpose. Don't add a torchvision dependency. A CUDA GPU is available (`train_imgfi.py` auto-selects `cuda`).
- Data (CSVs, .npy, images, models) lives outside this repo under `~/usrp-projects/data/`.

See also the persistent project memory (`csi-har-project`) for current state and the approved collection plan.
