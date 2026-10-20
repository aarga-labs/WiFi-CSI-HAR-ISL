# Capture source snapshot

`wifi_csi_capture/` is a file snapshot of the separate local capture repository as inspected on 19 October 2026. It includes tracked source plus the P4/P5 working changes/additions; it is not a Git submodule and has no embedded Git database. `../handoff/capture_source_provenance.json` records the upstream URL, base commit, dirty status and file hashes.

For later collection, inspect `wifi_csi_capture/pilot_tools/protocol_p45.py`, `record_p45.sh`, `P04_P05_COMMANDS.md`, updated cue logic and actual transmitter/receiver runtime Python. The outer `../pilot_tools/` is an older mirror, not the complete later P4/P5 state.

This snapshot preserves the observed code, including upstream/vendor source and licence files. It does not prove that regenerating a GRC reproduces every runtime control. Some paths/dependencies are machine-specific. Do not start radios, overwrite captures, regenerate GRC outputs or install system software merely to write the paper.
