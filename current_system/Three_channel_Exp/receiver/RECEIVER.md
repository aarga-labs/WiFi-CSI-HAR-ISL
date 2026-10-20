# Receiver Setup (USRP N210 #2 — RX)

This is the receiving side of the two-USRP, three-channel WiFi CSI
experiment. This laptop's USRP hops across channels 1, 6, 11 (100 ms each,
in sync with — well, *alongside*, see the warning below — the transmitter),
decodes 802.11 frames from the dedicated transmitter, and logs each frame's
52-subcarrier channel estimate plus which channel it was seen on to a CSV.

This is your teammates' `Team67_USRP_Receiver/gr-ieee802-11` work, copied
out clean (no `build/`, no dead ZMQ-era leftovers) — same idea as the
single-USRP `extract_csi` block you already know from `USRP_lib/`, extended
with a `Channel` column and a live `set_channel()` call the hop loop drives.

---

## What's in this folder

```
receiver/
├── RECEIVER.md          <- this file
└── gr-ieee802-11/       <- modified IEEE 802.11 module (unbuilt — build it here)
    └── examples/
        ├── wifi_rx.grc  <- the flowgraph, editable in GNU Radio Companion
        └── wifi_rx.py   <- generated Python + the channel-hop loop in main()
```

The interesting file is `gr-ieee802-11/lib/extract_csi_impl.cc` — same
environment-variable interface as the single-USRP project (`CSI_TA`,
`CSI_RA`, `CSI_OUT` — no recompiling to change a MAC or output path), plus:
- a `Channel` column in the CSV (which of 1/6/11 the packet was decoded on)
- `set_channel(chan)`, called by `wifi_rx.py`'s hop loop every 100 ms

Note that the hop loop lives in `wifi_rx.py`'s `main()`, **not** in the
`wifi_rx` class and **not** in the `.grc` — regenerating the flowgraph from
`wifi_rx.grc` in GNU Radio Companion will overwrite `wifi_rx.py` and silently
delete the hop loop. If you ever regenerate, re-add it (see
`CHANNELS`/`DWELL_TIME` and `hop_channels()` near the bottom of the file).

CSV columns: `Packet, Timestamp_us, Channel, SC0_Re, SC0_Im, … SC51_Re, SC51_Im`.

---

## ⚠ Before you start: fix the MAC filter

The transmitter (see `transmitter/TRANSMITTER.md`) sends frames with a
**fixed synthetic address**, not a rotating MacBook MAC:

| | value |
|---|---|
| `CSI_TA` (transmitter address) | `02:00:00:00:00:01` |
| `CSI_RA` (receiver/destination address) | `02:00:00:00:00:02` |

**Do not use `Three_Channel_Receiver/USRP_HAR_Project/har_receiver.py`** —
it hardcodes `CSI_TA=42:42:42:42:42:42`, which does not match the
transmitter above and would silently see zero `(MATCH)` lines forever. Run
`wifi_rx.py` directly instead.

Historical note, in case you find an older copy of this file: `har_receiver.py`
used to be the *only* thing that hopped the receiver — `wifi_rx.py` had no hop
loop, so "just run `wifi_rx.py` instead" left the RX parked on 2412 MHz with a
`Channel` column stuck at `1`. The loop now lives in `wifi_rx.py` itself, so
the wrapper really is redundant, but that was not true before 2026-08-13.

For your very first test — before the transmitter is even involved —
running with `CSI_TA=any CSI_RA=any` will show you every decoded frame's
real `TA`/`RA` on the console, which is the fastest way to confirm the
whole chain works before narrowing the filter.

---

## Part 0 — Prerequisites

Already satisfied on this machine (GNU Radio 3.10.11, UHD tooling present —
same environment the single-USRP project uses). If setting up fresh,
mirror `transmitter/TRANSMITTER.md` Part 0.

---

## Part 1 — Network setup

Same pattern as the single-USRP project: this laptop's ethernet interface
at `192.168.10.1/24`, USRP RX at `192.168.10.7`.

```bash
nmcli device status                                # confirm your ethernet iface is connected
ip addr show eno1                                  # expect 192.168.10.1/24 (adjust iface name if different)
sudo ip addr add 192.168.10.1/24 dev eno1           # if missing
ping -c 3 192.168.10.7
uhd_find_devices                                    # should list addr=192.168.10.7
```

This is a separate physical link from the transmitter's `192.168.10.9` —
both laptops using `192.168.10.1/24` locally is fine, they're not on a
shared network.

---

## Part 2 — Build

```bash
cd gr-ieee802-11
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Verify the channel-aware block is what actually got installed:
```bash
strings /usr/local/lib64/libgnuradio-ieee802_11.so | grep "CSI_TA"     # should print CSI_TA
strings /usr/local/lib64/libgnuradio-ieee802_11.so | grep "address 2"  # the Data-frame TA fallback
python3 -c "import ieee802_11; print(hasattr(ieee802_11.extract_csi, 'set_channel'))"   # True
```

If you edit `lib/extract_csi_impl.cc`, you must re-run `make && sudo make
install && sudo ldconfig` from `build/` — the flowgraph loads the *installed*
`.so`, not the one in your build tree. Editing `wifi_rx.py` needs no rebuild.

---

## Part 3 — Run a capture

**Terminal A:**
```bash
export CSI_TA=any
export CSI_RA=any
unset CSI_OUT
cd gr-ieee802-11/examples
python3 wifi_rx.py
```

You should see, within a few seconds of the transmitter starting (timestamps
and filenames will be your own — the shapes below are what matter):
```
extract_csi: TA filter = any, RA filter = any
extract_csi: writing to /home/rishiikesh/usrp-projects/data/csi_20260813_001234.csv
[00:12:34.567] Hopped to Channel 1 (2412 MHz)
[00:12:34.667] Hopped to Channel 6 (2437 MHz)
[00:12:34.767] Hopped to Channel 11 (2462 MHz)
extract_csi: seen TA=02:00:00:00:00:01 RA=02:00:00:00:00:02 (MATCH)
```

The three `Hopped to Channel` lines repeat every 300 ms and are your proof the
RX is actually retuning. If you never see them, the hop loop is missing from
`wifi_rx.py` (see the note in "What's in this folder") and every CSV row will
be labelled `Channel 1` no matter where the packet really came from.

Interleaved with the above you'll also see a `========== Metadata ==========`
block per decoded frame, printed by `parse_mac`. That block is *upstream* of
`extract_csi` — seeing it means the PHY decoded a frame, **not** that the frame
reached the CSV. Only the `extract_csi:` lines speak for the CSV.

The `saved N packets (~XX rows/s)` line only prints once every 100 rows, so on
a slow link you may legitimately never see it even while rows are landing.
Trust `wc -l` on the CSV (Part 4) over that line.

Once you've confirmed `TA=02:00:00:00:00:01 RA=02:00:00:00:00:02` is what
shows up, lock the filter in and name your output file:

```bash
export CSI_TA=02:00:00:00:00:01
export CSI_RA=02:00:00:00:00:02
export CSI_OUT=~/usrp-projects/data/3ch_test_$(date +%Y%m%d_%H%M%S).csv
cd gr-ieee802-11/examples
python3 wifi_rx.py
```

Ctrl+C to stop. It prints a final `total saved packets: N` line.

**Note on the default `CSI_OUT` path:** if you leave `CSI_OUT` unset, the
block falls back to a path hardcoded at compile time
(`/home/rishiikesh/usrp-projects/data/csi_<timestamp>.csv` — see
`DEFAULT_DIR` in `extract_csi_impl.cc`). That's fine on this machine; if
this code ever runs under a different user/home directory, **always set
`CSI_OUT` explicitly** rather than relying on that fallback.

---

## Part 4 — Sanity-check the CSV

```bash
wc -l ~/usrp-projects/data/3ch_test_*.csv
head -2 ~/usrp-projects/data/3ch_test_*.csv | cut -d, -f1-8      # header + first row, first few columns
watch -n 1 'wc -l ~/usrp-projects/data/3ch_test_*.csv'           # watch it grow live

# Are all three channels actually represented? This is the check that catches
# a receiver that isn't really hopping — a run that only ever reports
# "Channel 1" is parked, not hopping, no matter what the console says.
tail -n +2 ~/usrp-projects/data/3ch_test_*.csv | cut -d, -f3 | sort | uniq -c
```

A healthy run shows all of `1`, `6`, and `11` in that last command, in roughly
(not exactly) comparable numbers.

Expect the **overall** rate to be noticeably lower than the single-channel
project's ~100 rows/s target, and lumpy rather than smooth — each packet
only lands in the CSV when TX and RX both happen to be dwelling on the same
channel at the same moment, and the two hop loops aren't synchronized (see
the top-level `README.md`). A trickle of matched packets across all three
`Channel` values is a legitimate "it's working" result for a first pass;
zero matched packets for more than ~30s while the transmitter is confirmed
running is the actual failure signal.

Roughly what to expect: two free-running 3-channel loops share a channel about
**⅓** of the time *on average*, drifting anywhere between 0 % and 100 % as their
phase slips — which is why the rate is lumpy rather than steady. Note that
hopping the RX buys nothing here: a *parked* RX also sees a hopping TX exactly ⅓
of the time. Hopping the RX only adds retune cost and splits the rows across
three channels.

The dominant loss is **per-hop settling**, not alignment. Measured over a 784 s
hopping capture: a productive 100 ms dwell delivered a mean of **1.8 packets**,
against the ~5 that a 50 pkt/s transmitter should fit into it — so roughly
**60 ms of every 100 ms dwell is consumed by retune plus OFDM re-sync**, on each
side independently. 56 % of productive dwells yielded a single packet.

That fixed ~60 ms cost is per *hop*, not per second, which sets the direction of
every tuning decision:

- **Shortening `DWELL_TIME` makes it worse, fast.** At 50 ms the dwell is shorter
  than the settling time and essentially nothing gets through.
- **Lengthening it helps**, because the fixed cost is amortised over a longer
  productive window. 0.5 s is a reasonable next try; 1 s better still.
- **Parking both sides on one channel removes the cost entirely** and is the only
  option that reaches the ~50 Hz activity recognition needs. See
  `DATA_COLLECTION.md`.

`DWELL_TIME` is set in `wifi_rx.py` here and in `wifi_tx_multi_hop.py` on the
transmitter — change both, and agree the value with whoever runs the TX.

---

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| No `seen TA=...` lines at all | Transmitter not running, wrong channel/frequency alignment, or USRP RX not receiving — check `uhd_fft --args="addr=192.168.10.7" -f 2.412e9 -s 20e6` for signal |
| `seen TA=...` lines appear but never with `02:00:00:00:00:01` | You're seeing ambient WiFi, not this experiment's transmitter — confirm the transmitter's console is actually printing "Hopped to Channel" lines |
| Console shows the right TA/RA but rate is near zero | Expected to some degree — see the hop-sync note above. If it's *literally* zero for a sustained period, double-check both sides' `DWELL_TIME` (100 ms) and channel order (1, 6, 11) match — they should, unless someone edited one script |
| `strings ... | grep CSI_TA` prints nothing | Old block still installed — rebuild (Part 2) and make sure `sudo make install && sudo ldconfig` both ran |
| CSV empty but flowgraph runs | Check the `extract_csi: writing to ...` line for the actual path in use — `CSI_OUT` set in a different terminal doesn't apply here. `export` only affects the shell you typed it in; a new tab does not inherit it |
| `Metadata` blocks print, but no `extract_csi: seen TA=` line ever appears, and the CSV stays at 1 line | `extract_csi` is dropping frames before the filter. It needs TA/RA out of the frame metadata; `parse_mac` only publishes `ta`/`ra` keys for **Control** frames, while our transmitter sends **Data** frames (which carry `address 2` = TA and `address 1` = RA instead). `extract_csi_impl.cc` must fall back to those — it does as of 2026-08-13; if you restored an older copy, that fallback is what's missing |
| Console shows `(MATCH)` but `wc -l` still says 1 | Buffering, not data loss. Rows are flushed to disk as they're written as of 2026-08-13; older builds flushed only every 100 rows, so a slow link left everything sitting in the buffer until Ctrl+C |
| Every CSV row says `Channel 1` | The RX isn't hopping — no `Hopped to Channel` lines. `d_current_channel` initialises to `1` and only changes when `set_channel()` is called, so a missing hop loop shows up as a column of `1`s rather than an error |
| `Odd decimation`, `No GPSDO`, `thread priority` warnings | Harmless, ignore (same as the single-USRP project) |
| `pdu_to_tagged_stream(4) ... no handler registered. Message discarded.` | Harmless — an unconnected debug/scope port in the flowgraph, unrelated to the CSI path |

---

## Changelog — 2026-08-13

Three bugs kept this receiver from ever writing a usable CSV. All three were
on the RX side; the transmitter was correct throughout. Recorded here because
each one failed *silently* — no error, no warning, just an empty or wrong CSV.

1. **`extract_csi` dropped every Data frame.** It required `ta`/`ra` keys in
   the frame metadata, but `parse_mac` only sets those for Control frames;
   Data frames (what we transmit) carry `address 2`/`address 1` instead. The
   handler returned early, before even its own "seen TA=" log line, so the
   symptom was a header-only CSV and total console silence from the block.
   Fixed in `lib/extract_csi_impl.cc` by falling back to the `address N` keys.

2. **Rows sat unflushed.** The CSV was flushed only every 100 rows. At this
   experiment's low match rate that meant minutes of captured data invisible
   on disk (recoverable only via the destructor's flush on Ctrl+C). Now
   flushed per row.

3. **The receiver never hopped.** `wifi_rx.py` had no hop loop — earlier
   revisions of this document asserted three times that it did. The RX sat on
   2412 MHz for every run, and because `d_current_channel` initialises to `1`,
   the `Channel` column read a plausible-looking `1` instead of failing
   loudly. The loop (adapted from `har_receiver.py`, which had the only
   working copy) now lives in `wifi_rx.py`'s `main()`.

Items 1 and 2 require a rebuild + `sudo make install` (Part 2). Item 3 is
pure Python. Verified: `(MATCH)` lines appear and rows reach the CSV. The
end-to-end three-channel rate has not yet been characterised — see the
`DWELL_TIME` note in Part 4.
