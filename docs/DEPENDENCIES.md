# Dependencies, attribution and runnable scope

The selected archive is organised source and evidence, not one unified application with a single runtime.

- **ESPectre**: upstream checkout is pinned in `provenance/upstream_dependencies.json`. Local CSI logging changes, two device configurations and two Python tools are selected under `capture/esp32/espectre/`. The full upstream build tree and ESP-IDF environments are excluded. Apply the saved patch to the matching upstream revision, configure local WiFi settings and follow upstream build instructions before a hardware test.
- **ESP32-CSI-Tool**: retain upstream attribution. The selected fall-detection firmware/scripts and local capture experiments are under `experiments/esp32_fall_detection/`. No flash/build/serial test was run. ESP-IDF version compatibility must be checked per experiment.
- **ESP32-WiFi-Sensing and Espressif esp-csi**: the inspected tracked files match their stored revisions after ignoring line endings/permissions. Their upstream commits are references, not claimed team-authored implementation.
- **CASAS / SignFi**: preserve upstream README, licence and code attribution. Original public datasets are external/rebuildable inputs. The current P1–P5 vocabulary is separate from the 276-class public SignFi benchmark.
- **USRP/GNU Radio**: the runnable source layout of the latest capture snapshot remains under `current_system/capture_snapshot/wifi_csi_capture/`. Historical receiver variants require their original GNU Radio/UHD and custom block versions. Upstream gr-ieee802-11/gr-foo/UHD trees are not additional team contributions.
- **Legacy ML**: requirements differ across TensorFlow/Keras, PyTorch and scientific-Python experiments. Read the relevant notebook and requirements file; do not install one combined set or assume modern packages reproduce an old run.

Private WiFi settings, virtual environments, generated builds and private permission documents remain outside the published source. A password in one selected actuator copy was replaced by `<CONFIGURE_LOCALLY>`; provenance/redactions.csv records the changed copy without exposing its original value.

Source syntax and notebook structure checks are recorded in provenance/validation.json and the adjacent audit CSVs. Those are not substitutes for hardware tests, model evaluation or training. Historical errors are preserved and labelled rather than silently corrected into a different experiment.
