# CSI collection repair — verified 13 November 2026

The final calibrated setup passed a 70.20-second receiver check: **199.47 CSI rows/s**, **12.171 ms maximum gap**, **zero gaps above 100 ms**, **zero new UDP receive errors**, clean shutdown. The final 20-second readiness check also passed. This is a measured link check, not a guarantee against every future movement/environment change.

## Confirmed faults and evidence

1. The original Fedora transmitter repeatedly underflowed (`U`) and printed two complete packet dumps per packet. It treated intermittent packets as a continuous stream and ran an unnecessary unthrottled receive chain on dummy zeros. A burst-tag/debug correction and limiting the dummy receive branch reduced avoidable work, but physical underflows remained. The active replacement encodes a standard probe once and continuously streams a zero-filled 100,000-sample period, producing a nominal 200 probes/s at 20 MHz. The operator observed no new underflows after starting it.
2. The inherited TX multiplier of 0.8 did not ensure sample headroom: I reached 2.44068 and Q 2.00984, with 560/3921 active samples outside normalized +/-1. The first continuous implementation carried over this bug. The active waveform is now scaled to a maximum complex magnitude of 0.5 before UHD conversion. A hardware-free clipped-waveform replay decoded 10/20 probes; normalized replay decoded 20/20. The waveform is a fixed probe; its MAC sequence repeats and its payload is not a packet clock.
3. A strong narrow component near +2441 Hz in actual RF samples disrupted synchronization. Merely increasing gain made the CPU fall behind; buffer drops returned. On the same 5,000,000-sample (250 ms) normalized RF capture, the original decoder path yielded 0 CRC-valid target frames, while a narrow notch at 2441.40625 Hz yielded 49. Both replay paths consumed the full capture. This isolates a receiver frontend mitigation on identical input; it does not conclusively identify the physical origin of the unwanted tone.
4. Host load contributed risk: two runaway Satty processes were closed with operator authorization; a spinning swaync notification service was stopped after restart failed to clear its CPU spin. CPU performance governor and a 50,000,000-byte receive buffer are verified. CPU temperatures still reached approximately 98–100 C with new thermal-throttle events during the successful link check. Hardware cooling is not declared repaired.

## Active configuration

- TX USRP .9, TX/RX, channel1 /2412 MHz, 20 MHz, RF gain30, normalized complex-envelope peak0.5, 200 repeated probes/s.
- RX USRP .7, RX2, channel1 /2412 MHz, 20 MHz, RF gain12.
- Receiver live plot branches disconnected; original synchronization/equalization/decode/CSV path retained, with the explicitly added frontend notch before its three raw-IQ branches.
- Notch: H(z)=(1-exp(j*w0)*z^-1)/(1-0.9995*exp(j*w0)*z^-1), w0=2*pi*2441.40625/20e6. Its roughly 1.6 kHz characteristic width lies near the unused centre carrier, far from the closest active Wi-Fi subcarriers. This is a calibrated frontend change, not merely logging cleanup. Record it in preprocessing/evaluation descriptions.
- The filter is calibrated for this current radio/clock/frequency pair. Recheck after replacing/restarting radios or changing frequency; do not assume its centre is universal. Future metadata embeds COLLECTION_SETUP.json.

## Commands and safeguards

On the TX laptop, open the transmitter folder and run `bash START_STABLE_TX.sh --gain 30`. Keep it running.

Receiver laptop, inside FYP_Phone_Collector: source COMMANDS.sh and use the same named commands. Before phone START, run_paired now checks at least20 seconds of sustained CSI, >=50rows/s, max gap100ms, and no new receiver UDP errors. On failure it stops its own receiver before asking a participant to perform anything. During a block it logs live_receiver_checks.jsonl every10 seconds; degraded intervals are flagged without altering the shared schedule. After transfer it evaluates actual samples and exports usable_windows.csv. Keep following website cues.

The receiver helper automatically uses capture_receiver.py and the private quiet module. The original FYP_Main source/global installation is preserved. No phone APK reinstall or controller restart is required for these command-line receiver changes. Temporary local file-transfer servers are stopped after successful downloads.

## Limits and existing recordings

Original participant CSVs, phone uploads and final standing dataset have not been rewritten. Earlier gain15, unnormalized/legacy captures and the corrected gain30 fixed-probe/notched captures are different collection regimes. Preserve that distinction in training manifests; do not silently present them as identical calibration conditions. Existing quality-filtered windows remain the proposed usable subset; future fixes do not reconstruct missing old CSI samples. Group original trials/sessions before splitting overlapping windows.

The strict 100ms gap criterion is a conservative analysis policy, not a universal hardware-failure boundary. Current saved seated signs retain all70 phone trials and paired windows from60 under that policy. A full block repeat is not implied by the prior screening result.

Startup advisories about odd interpolation/decimation or TX scheduling/socket recommendations can remain. They were not suppressed. Ongoing U/underflow, loss of sustained throughput, or new receive errors require checking; the current successful link test is the evidence supporting continuation.

Broad DC blockers and other diagnostic filters were evaluated offline but are not deployed. The active filter is only the explicitly calibrated narrow notch above. Synthetic noiseless IIR tests can expose filter ring-down triggering the existing correlator; realistic tone+noise tests and identical-input RF replay were used for deployment evidence.

## Evidence

- Final report: quality_reviews/latest_link_verification.json; physical raw diagnostics in data/csi/P00/S99/P00_S99_CSI_capture_20261113_175637_d1d26b (P00, not participant training data).
- Same-input RF replay: build/test_normalized_raw_baseline.log and build/test_normalized_raw_notch.log; raw recording in the directory named by build/raw_normalized_folder.txt, captured without kernel UDP drops.
- Waveform tests: build/test_probe_clipped.log, build/test_probe_normalized.log; realistic narrow-tone/noise replay build/test_tone_notch.log.
- Regression suite: build/final_capture_checks.log, 40 tests passed.
- Prior gain/load diagnostics are retained in diagnostics/. They must not be interpreted as proof that the first short gain test fixed the full collection pipeline.

References: https://files.ettus.com/manual/page_general.html (underflows) and https://files.ettus.com/manual/structuhd_1_1stream__args__t.html (floating-point fullscale).

To restore desktop notifications when collection is over: `systemctl --user start swaync.service`. Its earlier high CPU spin may return; do not start it solely to remove a warning while collecting.

## Preflight JSON correction

The first mixed-run attempt at18:06 stopped before phone START because the early, short-stream readiness comparison returned numpy.bool, which JSON cannot serialize. The whole readiness expression is now converted to native bool; the fix covers early false, low-rate false and ready true. The exact failed file and successful sustained capture both serialize correctly, and41 tests passed. The failed attempt receiver stopped cleanly; no mixed phone session was created. No RF settings changed for this correction.

## Receiver-to-phone handoff correction

The18:09 mixed attempt passed20.6seconds of CSI at198.4rows/s, maximumgap15ms, zero new UDP errors, but run_block rejected the process because process_alive still recognized only wifi_rx.py. Recognition now accepts the actual Python script argument for both wifi_rx.py and capture_receiver.py, including interpreter flags, while rejecting names merely present in unrelated arguments. A real temporary capture_receiver.py process, growing synthetic CSV, HTTP controller and simulated phone completed the full mixed-plan handoff; shared plan and label parity were checked. All43 regression tests passed. Neither failed attempt started a physical mixed phone session; both receivers stopped cleanly. No radio settings changed for this correction.
