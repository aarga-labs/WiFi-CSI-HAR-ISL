# Current transmitter method — 13 November 2026

After BUILD.sh has built the private modules, use `bash START_STABLE_TX.sh --gain 30`. Keep this one terminal open. Stop the old START_TX.sh and START_PACKETS.sh processes first; the continuous transmitter does not use the packet generator. The source and UHD sink continuously supply every sample at20 MHz, including zeros between standard Wi-Fi probes, giving200 probes/s.

The probe is encoded once using the existing PHY/MAC/padding. The complete waveform is peak-normalized to0.5 before UHD conversion. Channel1, TX/RX and transmitter .9 are retained. The active probe repeats its MAC sequence and has no meaningful payload timestamp. CSI timestamps continue to come from the receiver. Logs record settings under logs/.

The inherited0.8 multiplier produced components outside normalized +/-1; do not copy its unnormalized output into UHD. The old burst-tag/debug/dummy-receive patches are retained as repair history, but physical underflows remained; they are not the active collection method.

No GNU Radio or C++ rebuild is needed when replacing only stable_tx.py or the launch script. `bash START_STABLE_TX.sh --build-only` validates the encoded waveform and headroom without opening a radio. For this .7/.9 radio pair the receiver also uses a calibrated narrow frontend notch at2441.40625 Hz to reject a strong near-centre unwanted tone; details and evidence are in the receiver collector's LINK_DIAGNOSIS.md. Recheck calibration if radio clocks/frequency change.

The full corrected setup was observed for70.20seconds:199.47CSIrows/s,largestgap12.171ms,no gaps>100ms,no new UDP receive errors, clean receiver shutdown. This is not a permanent zero-loss guarantee. Physical test was on the operator's Fedora TX laptop, with receiver-side verification. Old participant data are retained under their original collection regime.
