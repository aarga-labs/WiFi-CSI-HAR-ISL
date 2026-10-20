# Transmitter Setup (USRP N210 #1 — TX)

You have this folder because you're running the **transmitter** side of a
two-USRP WiFi CSI experiment. Your laptop sends synthetic 802.11 packets
through a USRP N210, hopping across WiFi channels 1, 6, and 11 every
100 ms, while a teammate's laptop on the other USRP receives and logs the
channel state.

Read this whole file once before touching anything — it's short.

---

## What's in this folder

```
transmitter/
├── TRANSMITTER.md          <- this file
├── gr-ieee802-11/          <- IEEE 802.11 a/g/p GNU Radio module (pristine upstream, unbuilt)
│   └── examples/
│       ├── wifi_tx_new.grc      <- the flowgraph, editable in GNU Radio Companion
│       ├── wifi_tx_multi_hop.py <- the flowgraph's generated Python, WITH channel hopping added
│       ├── wifi_phy_hier.grc    <- hierarchical PHY block the flowgraph depends on
│       └── packet_generator.py  <- feeds synthetic packets into the flowgraph over TCP
└── gr-foo/                 <- small helper OOT module (needed for one padding block)
```

You will **build both `gr-ieee802-11` and `gr-foo` from source** — they're
not prebuilt, on purpose, because build artifacts don't travel between
machines.

---

## Part 0 — Prerequisites

- **Ubuntu 22.04/24.04 or Fedora**, GNU Radio **3.10.x** with UHD and PyQt5
  (`gnuradio-companion`, `python3-uhd` / `uhd-host`, PyQt5 all installed and
  working — if `gnuradio-companion` already opens, you're set).
- Build tools: `cmake`, a C++ compiler, `git`.
- A USRP N210, connected to this laptop via a **direct gigabit ethernet
  cable** (no switch needed).

Quick sanity check once UHD is installed:
```bash
uhd_find_devices
```
This won't find anything useful until the network step below is done.

---

## Part 1 — Network setup (USRP ↔ laptop)

The flowgraph expects the USRP at **`192.168.10.9`**. Configure your
ethernet interface (the one physically connected to the USRP) to
`192.168.10.1/24`:

```bash
ip link                                    # find your interface name, e.g. eth0 / enp2s0
sudo ip addr add 192.168.10.1/24 dev <iface>
sudo ip link set <iface> up
```

Then confirm the USRP answers:
```bash
ping -c 3 192.168.10.9
uhd_find_devices                           # should list a device at addr=192.168.10.9
```

If your N210 is actually configured to a different IP (check the sticker /
ask whoever set it up), you'll need to either re-flash its EEPROM to `.9` to
match the flowgraph, or edit `dev_addr`/`addr=` in
`gr-ieee802-11/examples/wifi_tx_new.grc` (search for `192.168.10.9`) and
regenerate.

---

## Part 2 — Build gr-foo

```bash
cd gr-foo
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

---

## Part 3 — Build gr-ieee802-11

```bash
cd gr-ieee802-11
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
sudo ldconfig
```

Sanity check the Python bindings are importable:
```bash
python3 -c "import ieee802_11; print('ok')"
python3 -c "import foo; print('ok')"
```

---

## Part 4 — Generate the `wifi_phy_hier` hierarchical block

`wifi_tx_multi_hop.py` does `from wifi_phy_hier import wifi_phy_hier`. That
file isn't checked in — GNU Radio generates it from `wifi_phy_hier.grc` and
caches it under `~/.local/state/gnuradio/`, from where it's importable by
any flowgraph on this machine. Generate it once:

**Easiest — GUI:**
```bash
gnuradio-companion gr-ieee802-11/examples/wifi_tx_new.grc
```
Click **Generate** (the gear icon). This compiles both `wifi_tx_new.grc`
*and* its `wifi_phy_hier` dependency. Close the window once it's done (you
don't need to run it from here).

**Or — command line:**
```bash
cd gr-ieee802-11/examples
grcc wifi_phy_hier.grc -o ~/.local/state/gnuradio/
```

Verify it landed:
```bash
ls ~/.local/state/gnuradio/wifi_phy_hier.py
```

---

## Part 5 — Run the transmitter

Two terminals.

**Terminal A — the flowgraph:**
```bash
cd gr-ieee802-11/examples
python3 wifi_tx_multi_hop.py
```
A small Qt window opens. The console should start printing:
```
[HH:MM:SS.mmm] Hopped to Channel 1 (2412 MHz)
[HH:MM:SS.mmm] Hopped to Channel 6 (2437 MHz)
[HH:MM:SS.mmm] Hopped to Channel 11 (2462 MHz)
```
repeating every 300 ms (100 ms per channel). Leave this running.

**Terminal B — the traffic generator:**
```bash
cd gr-ieee802-11/examples
python3 packet_generator.py
```
This connects to the flowgraph over `TCP localhost:52001` and sends one
500-byte packet ~every 20 ms (50 packets/sec), each tagged
`SEQ=...;TS=...;LABEL=walking;`. You should see:
```
Connected
Sent packet 0
Sent packet 1
...
```
If it hangs on connect, Terminal A's flowgraph isn't up yet or already has
another client connected — check Terminal A first.

To label a different activity/run, edit the `LABEL` constant near the top
of `packet_generator.py` before starting it (it's a plain string, no need
to touch anything else).

---

## What the receiver needs from you

Tell your teammate running the receiver these exact values (already baked
into this flowgraph, in `ieee802_11_mac_0` inside `wifi_tx_new.grc`):

| | value |
|---|---|
| Transmitter address (`CSI_TA` on the RX side) | `02:00:00:00:00:01` |
| Receiver/destination address (`CSI_RA` on the RX side) | `02:00:00:00:00:02` |
| Channels | 1, 6, 11 (2412 / 2437 / 2462 MHz), 100 ms dwell each |
| `samp_rate` | 20e6 |
| `tx_gain` | 20 |

**Coordinate the start.** Neither side's hop loop is synced to the other —
they're two independent 100 ms-per-channel timers. Agree on a rough start
time over call/chat; start the receiver first, then this transmitter +
packet generator within a second or two. Expect the two hop sequences to
drift in and out of phase — that's a known limitation, not a sign something
is broken (see the top-level `README.md`).

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `uhd_find_devices` finds nothing | Network step (Part 1) not done, or wrong interface/cable |
| `ModuleNotFoundError: No module named 'ieee802_11'` or `'foo'` | Part 2/3 build or `sudo make install` skipped, or `sudo ldconfig` skipped |
| `ModuleNotFoundError: No module named 'wifi_phy_hier'` | Part 4 skipped — generate the hier block first |
| `packet_generator.py` hangs on `sock.connect` | Flowgraph (Terminal A) not running yet, wrong port, or another `packet_generator.py` already connected (the socket is single-client) |
| Qt window opens but nothing happens / no hop lines print | Wrong script — plain `wifi_tx.py` (if present) has no hopping; use `wifi_tx_multi_hop.py` |
| `uhd_usrp_sink` errors about address / no such device | USRP IP mismatch — re-check Part 1, or the actual N210 isn't at `.9` |
