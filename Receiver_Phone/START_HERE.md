# FYP Phone Collector

This is a local Android motion recorder and laptop controller for Group 067. It records the phone's accelerometer and gyroscope, shows scheduled collection prompts on the laptop, and transfers a checked archive into participant/session folders. It does not start a USRP flowgraph or train a model.

## Current workflow

Receiver update, 13 November: see [LINK_DIAGNOSIS.md](LINK_DIAGNOSIS.md) for measured gain/host checks, the private quiet receiver build, cooling guidance and existing P04 coverage. Current named commands retain RX gain 12 dB. The corrected TX uses START_STABLE_TX.sh --gain 30, normalized peak0.5, without the old packet generator; the receiver applies the calibrated narrow notch and checks20 seconds before starting the phone.

Read **[RUN_COMMANDS.md](RUN_COMMANDS.md)**. This replaces the earlier pilot and two-command workflow. Named commands such as `p04_stand_still` now start CSI and phone together, use one plan, and stop their own CSI receiver after verified phone transfer. Standing/seated stillness are separate 120-second events. Activity and sign orders/counts replay the actual earlier P04/P05 labels. There are no added forearm timing tasks or short baseline phases in named runs.

Start the controller, connect the phone, enable laptop sound and full-screen prompts. In a second terminal, source COMMANDS.sh and run the required named command. The website shows prompts and Stop/flag controls; its old selection form and Start button have been removed. Do not run the historical cue scheduler or a second CSI receiver alongside a named run.

## USB or Wi-Fi

### USB setup

Connect one phone using a data-capable USB cable. Enable developer options and USB debugging on the phone, and approve this computer on the unlocked phone. Run:

```bash
./START_USB.sh
```

The launcher installs the APK if missing, sets up the cable connection, and opens the dashboard. If the collector is already running, it reopens that instance without restarting it. An installed phone app is left unchanged. Phone address: `http://127.0.0.1:8765`.

Keep the original controller terminal open. Re-running the launcher does not create a second controller. To deliberately update an installed APK, finish and save all recordings, then use `./START_USB.sh --reinstall`. If another application occupies the port, it is left alone; use `./START_USB.sh --port 8766` and the matching port in the phone app.

USB avoids reliance on Wi-Fi but the cable can restrict movement. Choose a mounting/collection arrangement where it does not alter the performed gestures. Only use debugging on your trusted collection computer.

### Wireless collection

Connect laptop and phone to the same trusted local network. Run:

```bash
./START_WIFI.sh
```

The launcher displays the laptop's local network addresses. Enter `http://LAPTOP_LOCAL_ADDRESS:8765` in the phone app, using the same pairing key as the laptop dashboard. Open the controller locally on the laptop, not through a public tunnel. If the dashboard cannot connect, check the local firewall and network client-isolation settings without disabling unrelated protections.

Wi-Fi mode uses local HTTP with a random pairing key. It is **not transport-encrypted**. Use a trusted network and no port forwarding. Keep the key private. It permits session control and data upload, so do not share it outside the collection team. A 5 GHz local network, where available, avoids adding phone Wi-Fi traffic directly on the channel-1 CSI band; measure the actual radio environment rather than assuming no interference.

The application never uploads recordings to a cloud service. It does not request camera, microphone, location, contacts, or shared-storage access.

## During a recording

Follow only the displayed event. Red is preparation/rest; green and one beep means start; two beeps means stop. The phone media volume should be muted to prevent its separate GO tone. Prompts advance automatically. The website displays participant, session, posture, trial and story when applicable. Use Stop and save now or the phone's local stop button to keep a partial recording. Wait for FINISHED in the terminal before the next named command.

Cue labels describe scheduled tasks; they do not independently verify physical movement. Preparation/rest intervals have no scored class. The earlier datasets, new plans, and transfer archives are retained without overwrite.

## What is saved

The laptop creates a new, unique directory for every block:

```text
data/recordings/P04/S01/P04_S01_MODE_TIMESTAMP_UNIQUE_ID/
  plan.json                    # Intended phases, class order, seed and placement
  planned_labels.csv           # Laptop's intended cue schedule
  flags.json                   # Operator mistake/review notes
  phone_original.zip           # Exact, checked phone upload
  transfer_receipt.json         # Archive hash, size, arrival and phone status
  phone/
    accelerometer.csv          # All delivered raw acceleration events; gravity included
    gyroscope.csv              # All delivered raw rotation events; radians/second
    labels.csv                 # Phone-executed cue boundaries and completion flags
    clock_sync.csv             # Timing measurements and offset estimates
    metadata.json              # Hardware, app, units, participant and recording status
    manifest.json              # Hash and size for every original member
    quality.json               # Laptop's initial sampling/gap report
```

The server never overwrites a different recording. A retry of the same archive is accepted idempotently. Every archive member and the whole upload are checked against SHA-256 hashes before files are exposed as received.

The phone keeps raw files and its ZIP in app-private storage **after transfer**. The app's **Share a local backup** button can export an archive if needed. Do not uninstall the app or clear its storage before verifying and backing up your recordings; Android removes app-private data in those operations.

## Connection loss, interruptions and recovery

- Once received, the complete prompt schedule runs on the phone using its monotonic clock. A lost cable/Wi-Fi connection does not deliberately stop that block.
- The phone saves data locally, flushes approximately once per second, and requests a disk sync approximately every five seconds. A sudden power loss/process kill can still lose the most recent buffered events. This is not a zero-loss guarantee.
- Reconnect the phone/app/controller after an interruption. Completed, unacknowledged archives retry automatically.
- On app restart, a persisted unfinished recording is marked **interrupted** and packaged without inventing a missing final label interval.
- Files are not deleted after receipt. A failed upload is retried; an incomplete upload never replaces a good archive.
- A laptop restart may reset its monotonic-to-wall-clock anchor. Clock samples carry controller IDs to make that visible.
- If a recording is marked interrupted, stopped, or sensor_error, inspect it explicitly; do not include it as a completed block without documenting coverage/exclusions.

## Timing and CSI

### CSI in the current named commands

The one-command runner starts the preserved configurable receiver with RX .7, RX2, gain 12, Channel 1, and a unique output folder. It verifies incoming rows before starting the phone. It links the shared plan to that CSI file and stops only the receiver it started after phone transfer. The transmitter/packet generator remain running separately on the TX laptop. Original receiver source is unchanged.

Each sensor row contains the Android hardware-event timestamp, callback receipt time, a device-wall-time estimate, and a controller-time estimate. Raw monotonic timestamps are retained.

The phone periodically makes seven timing round trips and keeps the lowest-round-trip estimate. It logs the four exchange timestamps, mapping offset, RTT, and controller identity. The phone schedules its entire cue plan locally, and logs actual executed cue boundaries on the same monotonic clock as sensor events.

These measurements help align phone data with the laptop. They do **not** certify perfect clock synchronization, physical movement onset, audio output timing, or CSI/IMU sensor latency. Network asymmetry and hardware latency remain limitations. Compare timing checks on a real pilot before using the data for fusion.

The controller records its epoch anchor and displays any change in the laptop wall clock. CSI capture uses your existing receiver separately. Keep the receiver clock stable and preserve the CSI file and collection settings; no legacy capture code is changed by this project.

## Data-quality checklist before training

1. Confirm the correct person, session, phone forearm, mode, and class dictionary.
2. Check both sensor CSVs contain sensible, changing values and cover the intended phases.
3. Inspect actual rate, large gaps, invalid rows, and timestamp order in `quality.json`.
4. Check `labels.csv` phase completion; exclude or separately describe partial trials and operator flags.
5. Inspect timing evidence and any controller-clock change. RTT is not a measured synchronization-error bound.
6. Keep participant/session groups intact in train/validation/test splits. Do not split neighbouring overlapping windows randomly.
7. Preserve all raw files and receipts; write preprocessing output elsewhere.

“Received complete” describes phone completion and archive receipt. It does not claim the gesture was correct, synchronization was independently verified, or a model has been trained.

## Technical notes

- Android 8/API 26 or later, with a hardware accelerometer and gyroscope. Target API 35.
- Sensor request: 20,000 microseconds (~50 Hz), no batching requested. Actual delivered rate is recorded, not forced.
- User-started foreground service, visible notification, partial wake lock (up to six hours per connection), private local storage. Disconnect in the app when finished.
- Laptop controller: Python standard library; no package installation required. The bundled launchers use this computer's `/usr/bin/python3` and the downloaded official platform-tools path if adb is not on PATH.
- Pairing key: `data/pairing.json`; keep the `data` directory private. It also contains the local controller database and private browser launch link.
- Source: `android/src`, `controller.py`, and `web/`. Build with `python3 build_android.py` after providing the official SDK at the documented cache path or `--sdk`.
- APK update signing material is stored outside the project under `~/.local/share/fyp-phone-collector/`. Preserve it privately if rebuilding updates; do not publish it.
- The current APK is signed for local research installation, not distributed through Google Play.

The SDK tools used to build this application were downloaded from Google's Android repository. Relevant platform references: [sensor timestamps](https://developer.android.com/reference/android/hardware/SensorEvent#timestamp), [foreground services](https://developer.android.com/develop/background-work/services/fgs/service-types#special-use), and [Android Debug Bridge](https://developer.android.com/tools/adb).

## Updating the website cues

Finish and save any active block first. Stop the original controller terminal with Ctrl+C, run the same USB or Wi-Fi launcher again, and refresh the dashboard (Ctrl+Shift+R if cached). The website update does not need an APK reinstall. Test the laptop sound before the next P00 pilot.



Phone v1.1 update: see RECOVERY_AND_UPDATE.md. Install the updated APK in place, keep the app visible, then use p04_activities_stand_patch for the 45-trial makeup (455.5 seconds). Seventy original trials are recovered under recovery/P04_activities_standing_20261113_124340/. The dataset is not complete until makeup quality is checked.


## Before the next run: receive buffers and automatic quality checks

Run `bash SETUP_RX_BUFFERS.sh` once and enter your Linux sudo password. This installs `/etc/sysctl.d/90-fyp-usrp.conf` with `net.core.rmem_max=50000000`, applies it now, and keeps it across restarts. Existing differing content at that specific config path is backed up. The agent could not apply the privileged change because sudo required a password. Named commands now refuse to open the receiver with the old small buffer setting.

The receiver must show at least one second of recent incoming CSI averaging 50 rows/s or more, with no gap above 250ms, before the phone is started. This startup gate does not guarantee the RF link will remain unchanged during movement. The app still needs to stay visible, and v1.1 is required.

After transfer and receiver closure, the command checks both raw streams and the phone's executed cue times. It saves `collection_quality.json` and `usable_windows.csv` in that phone recording folder. Successful completion now explicitly means the included two-second windows passed the documented coverage checks. Whole-trial passes are counted separately. A partial run or an event with no clean window is reported as requiring review. Raw data are retained.

The driver may still print the odd-decimation advisory for the existing 20MHz Wi-Fi sample rate; no RF sample rate was changed or warning hidden. RF fading, host scheduling and physical sensor latency cannot be guaranteed away by these checks.

The next block after the completed standing activity collection is `p04_activities_sit`. Keep the transmitter and packet generator running, and use the existing website prompts.
