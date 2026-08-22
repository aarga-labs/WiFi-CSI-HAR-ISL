# Three-Channel USRP Experiment (2 USRP N210, TX + RX)

## What this is

A **two-USRP, three-channel** WiFi CSI capture experiment, separate from (and
built on top of) the earlier single-USRP passive-sniffing project in
`USRP_lib/`. Instead of passively sniffing a real MacBook↔hotspot link on one
fixed channel, this setup runs **our own dedicated transmitter** on one USRP
and hops it — together with the receiver — across the three non-overlapping
2.4 GHz WiFi channels (**1, 6, 11**) every 100 ms.

```
Laptop A (transmitter)              Laptop B (receiver, this machine)
  packet_generator.py                       wifi_rx.py
        | TCP :52001                       (channel-hopping)
        v                                        |
  wifi_tx_multi_hop.py                            v
   (hops 1/6/11 every 100ms)          decodes 802.11 frames,
        |                             extracts 52-subcarrier CSI,
        v                             writes CSV (Packet,
   USRP N210 (TX) ==RF over the air==> USRP N210 (RX)   Timestamp_us, Channel,
   addr 192.168.10.9                  addr 192.168.10.7   SC0_Re, SC0_Im, ...)
        ^ ethernet                          ^ ethernet
        |                                   |
   Laptop A eth: 192.168.10.1/24      Laptop B eth: 192.168.10.1/24
```

Each USRP talks to its own laptop over a **direct point-to-point ethernet
cable**, so both laptops can safely use the same local IP (`192.168.10.1/24`)
— they're electrically separate links, not a shared LAN.

## Folder layout

- **`transmitter/`** — everything needed on the TX laptop. Self-contained:
  the pristine upstream `gr-ieee802-11` + `gr-foo` OOT module source, the
  hopping TX flowgraph, and the traffic generator. **This is the folder to
  zip and send to your friend.** Full instructions in
  [transmitter/TRANSMITTER.md](transmitter/TRANSMITTER.md).
- **`receiver/`** — stays on this laptop. Contains your teammates'
  channel-aware `gr-ieee802-11` (the `extract_csi` block now has a `Channel`
  column and a `set_channel()` call the hop loop drives) and the RX
  flowgraph. Full instructions in [receiver/RECEIVER.md](receiver/RECEIVER.md).

Both are trimmed copies (no `build/` artifacts, no stale experiment
leftovers) of what already exists elsewhere in this repo:
`gr-ieee802-11/` + `gr-foo/` at the repo root (TX side), and
`Three_Channel_Receiver/Team67_USRP_Receiver/gr-ieee802-11/` (RX side, the
one your teammates actually got building — the raw drop in
`Three_Channel_Receiver/` also contains an older ZMQ-based attempt and a
`USRP_HAR_Project/` wrapper script that are now dead ends; this folder only
carries forward the parts that are current).

## Two things to know before you run this

**1. The MAC filter your teammates left behind is wrong.** The transmitter
sends frames with a fixed, synthetic address — src `02:00:00:00:00:01`, dst
`02:00:00:00:00:02` (see `TRANSMITTER.md`). The old `har_receiver.py` wrapper
in `Three_Channel_Receiver/USRP_HAR_Project/` hardcodes
`CSI_TA=42:42:42:42:42:42`, which doesn't match — it would never see a
`(MATCH)`. Use the values in `RECEIVER.md` instead (or `CSI_TA=any
CSI_RA=any` for your very first test run).

**2. TX and RX hop independently — there's no shared clock.** Both sides
free-run their own "channel 1 → 6 → 11, 100 ms each" loop from whenever you
start them; nothing keeps them locked in phase. Start both processes within
a second or two of each other and expect the two to drift in and out of
alignment — you'll only catch packets on the ~⅓ of the cycle where both
sides happen to be on the same channel. Treat this as the first thing to
validate (does the rate gate in `RECEIVER.md` pass at all?), not something
that's guaranteed to work out of the box.

## Running it

1. Read `receiver/RECEIVER.md` and get this laptop's RX side built and
   verified first (you can do this alone, before your friend is involved —
   `uhd_find_devices` should find your RX USRP, and you should see decoded
   frames from *any* WiFi traffic once you set `CSI_TA=any CSI_RA=any`).
2. Zip `transmitter/` and send it to your friend. They read
   `TRANSMITTER.md` and build on their machine.
3. Wire up both USRPs, agree on a start time (call/chat), start the RX
   flowgraph first, then the TX flowgraph + packet generator.
4. Watch the RX console for `(MATCH)` and a `rows/s` figure — that's the
   same rate-gate idea from the single-USRP project, just noisier here
   because of the independent hopping.

## Git

This folder lives inside the `usrp-projects` git repo but hasn't been
committed yet (everything in the repo currently shows as untracked/staged).
Nothing here was auto-committed — say the word if you want it committed, or
just `zip -r transmitter.zip transmitter/` and hand that off without
touching git at all.
