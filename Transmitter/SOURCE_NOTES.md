# Bundle provenance

Source copied from `FYP_Main/Three_channel_Exp/transmitter/gr-foo` and `gr-ieee802-11` on the receiver workspace. The original directories were left unchanged.

Text files with CRLF line endings were normalized to LF in the bundle only. The stored GNU Radio binding header hashes matched the LF versions; normalization fixes the otherwise-failing header hash check without bypassing it or changing the public API.

Legacy TRANSMITTER.md is deliberately omitted because its hardcoded address, gain and hopping instructions differ from the current physical setup. Use README_FEDORA.md and the launch scripts supplied here. The source flowgraph is preserved; START_TX.sh explicitly supplies TX address `.9`, parked Channel 1 and gain 15 through its supported environment settings.

Builds are private under install/; launch scripts add those paths only to their own process environment. The ZIP excludes build/, install/, generated/, logs, Python caches and machine-specific binaries. Source licenses remain with the respective modules.
