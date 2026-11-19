# Current collection: one command per named run

This replaces the earlier pilot/manual two-command instructions.

## Load the corrected version once

Finish/save any active phone run using Stop and save now. Stop an older CSI receiver with Ctrl+C in its terminal. Stop the old controller with Ctrl+C in its own terminal. Existing files are retained.

Terminal 1:

```bash
cd Receiver_Phone
./START_WIFI.sh
```

Refresh the website with Ctrl+Shift+R. Connect the phone, mute its media volume, enable/test laptop sound, then choose Full-screen prompts. The website is a prompt monitor: there is no recording selector or Start button.

Terminal 2:

```bash
cd Receiver_Phone
source ./COMMANDS.sh P04 S01
```

## Run these individually, in this order

Wait for FINISHED before the next command. Each command starts its own CSI receiver, checks incoming packets, starts the phone with the shared event plan, waits for the verified transfer, then stops only its own CSI receiver.

| Run | Rishiikesh | Adhikkesh |
|---|---|---|
| Standing still, 120 seconds | `p04_stand_still` | `p05_stand_still` |
| Seated still, 120 seconds | `p04_sit_still` | `p05_sit_still` |
| Standing activities | `p04_activities_stand` | `p05_activities_stand` |
| Seated activities | `p04_activities_sit` | `p05_activities_sit` |
| Standing signs | `p04_sign_stand` | `p05_sign_stand` |
| Seated signs | `p04_sign_sit` | `p05_sign_sit` |
| Mixed activity + signs | `p04_mixed_activity` | `p05_mixed_activity` |

All named functions are loaded together, so the p05 commands automatically select P05. The sourced S01 setting applies to both people. For a later session, source COMMANDS.sh again with S02.

Do not separately run `csi ...`, `phone ...`, an old cue script, or another receiver while using these one-command runs. Keep Terminal 1, the phone connection, the website, and the stable TX terminal running. TX now uses `bash START_STABLE_TX.sh --gain 30` on Channel1, device .9, with normalized peak0.5 and no separate packet generator. RX is .7, RX2, gain12, with the calibrated notch in COLLECTION_SETUP.json. The phone starts only after a 20-second CSI check; follow the website when its scheduled cues begin.

## What appears in full screen

- Red: prepare for the named event, or rest. No scored movement label is assigned to ready/rest.
- Green and one beep: perform the displayed event. Two beeps: stop.
- Standing still contains only a short preparation and exactly 120 green seconds of stand_still. Seated still does the same for sit_still. No claps, forearm motion tasks, pilot classes, or extra short baseline phases.
- Activities and signs use the actual event order saved in each person's previous CSV labels, without a new shuffle. The new protocol file records the original path and hash.
- Standing activities: the same 12 classes, with 10 repetitions each except the earlier fall class's 5. Seated activities: the same 7 classes with 10 repetitions each. Signs: all 14 signs, 5 each in each posture. Their per-event durations match the earlier isolated definitions, including 4-second lightswitch, 5-second tvremote, 6-second other activities, and 4-second signs.
- Mixed activity replays that person's previous mixed-script event order, including the recorded story/run/posture metadata. It gives 10 seconds of red preparation before a different story, and ordinary preparation/rest between events. These are scheduled, buffered repetitions of the older scripts, not newly claimed spontaneous/interleaved recordings.
- The earlier label files had 60-second still intervals; the new stillness runs are deliberately 120 seconds each as requested now. Removed sync tasks and added buffers are recorded as the changed protocol, not presented as an identical timing replication.

Once started, the prompts advance automatically; do not click between events. Use Stop and save now for an early stop; partial runs remain partial. Ctrl+C in the one-command terminal requests a phone stop and stops the receiver it started, keeping the files.

## Saved files

Every attempt uses a new unique folder. The phone plan includes the paired CSI identity. The same plan and scheduled label times are saved alongside the CSI CSV. Phone originals and executed cue boundaries remain preserved in the uploaded archive. Actual CSI/phone clock alignment and performed movement boundaries still require review; one shared schedule does not certify perfect synchronization.

```text
data/recordings/P04/S01/PHONE_RUN_ID/
data/csi/P04/S01/CSI_RUN_ID/
data/run_logs/P04_BLOCK_TIMESTAMP_UNIQUE.log
```

Only one green event is a 120-second stillness interval; preparation/transfer add a little time to the full command. After FINISHED, both phone and CSI files are saved. A stopped/error run is reported as partial, never complete.


## Before the next run: receive buffers and automatic quality checks

Run `bash SETUP_RX_BUFFERS.sh` once and enter your Linux sudo password. This installs `/etc/sysctl.d/90-fyp-usrp.conf` with `net.core.rmem_max=50000000`, applies it now, and keeps it across restarts. Existing differing content at that specific config path is backed up. The agent could not apply the privileged change because sudo required a password. Named commands now refuse to open the receiver with the old small buffer setting.

Before starting the phone, the receiver checks at least 20 seconds of incoming packets and host health. See the thresholds below. Keep the phone app visible and use v1.1.

After transfer and receiver closure, the command checks both raw streams and the phone's executed cue times. It saves `collection_quality.json` and `usable_windows.csv` in that phone recording folder. Successful completion now explicitly means the included two-second windows passed the documented coverage checks. Whole-trial passes are counted separately. A partial run or an event with no clean window is reported as requiring review. Raw data are retained.

The driver may still print the odd-decimation advisory for the existing 20MHz Wi-Fi sample rate; no RF sample rate was changed or warning hidden. RF fading, host scheduling and physical sensor latency cannot be guaranteed away by these checks.

## Receiver qualification

Run `./BUILD_QUIET_RX.sh` when setting up the receiver or after updating the private C++ patch.
Run `./START_CSI_RX.sh --check` to verify the exact Python extensions and shared libraries.
With the stable transmitter running, `./START_CSI_RX.sh --pid P00 --session S98 --seconds 1220`
collects a no-participant rehearsal into a fresh folder and prints its summary. Each run writes
`bench_summary.json`, effective radio settings, actual socket buffers, per-second telemetry,
the original 107-column CSI CSV and a packet-indexed host monotonic timing file. The frame timestamps
measure receiver processing. The short synchronizer suppresses standard UHD time-tag propagation,
so assigning a radio arrival time from those CSV timestamps would introduce an unknown offset.

The participant start gate uses at least 20 seconds, 180 rows/s for the 200-probe/s setup, a 100 ms
maximum gap, fresh samples and telemetry, advancing target frames and zero new UHD overflows,
interface receive drops/errors and kernel UDP buffer errors. The 180 threshold is a collection
policy. Historical window salvage uses its original thresholds. During recording, interval warnings
preserve the cue schedule. The final report records overlapping trial IDs as review candidates.
UHD may report an overflow after the actual loss. The overlap refers to its reporting interval.
Packet gaps and the sample coverage assessment provide separate evidence.

The tested receiver laptop passed a 20-minute rehearsal on AC with the Dell
`performance` profile, all CPU cores available and the Intel P-state
maximum performance capped at 75%. The 75% cap is specific to this laptop
and its measured workload. [Bench results](diagnostics/2026-11-19_validation.md)

To reproduce that profile on the tested Dell, record the current values
before applying the temporary settings.

```bash
cat /sys/firmware/acpi/platform_profile
cat /sys/devices/system/cpu/intel_pstate/max_perf_pct
echo performance | sudo tee /sys/firmware/acpi/platform_profile
echo 75 | sudo tee /sys/devices/system/cpu/intel_pstate/max_perf_pct
./START_CSI_RX.sh --pid P00 --session S98 --seconds 1220
```

Restore the two saved values when capture work ends. On this machine they
were `balanced` and `100` before testing.

For a power-profile comparison, keep the laptop on AC, use the same radio settings and antenna
geometry, allow the CPU to return to a comparable starting temperature and run one rehearsal on
each Dell profile. Compare median and peak temperature, fan RPM, throttling, rate, gaps and loss
counters. Keep the Intel CPU governor fixed. Read the current firmware profile with
`cat /sys/firmware/acpi/platform_profile`. If authorized for the machine, select performance
with `echo performance | sudo tee /sys/firmware/acpi/platform_profile`, and restore the recorded
previous profile after the comparison. Queuing a performance preset does not prove better cooling.

On an idle radio, the Ettus UHD benchmark can separate Ethernet transport from Wi-Fi decoding.
Use the example supplied with the matching UHD release. With the Python benchmark, RX uses
`--args addr=192.168.10.7 --rx_rate 20e6 --duration 30`. On the Fedora TX host use
`--args addr=192.168.10.9 --tx_rate 20e6 --duration 30` while the normal TX process is stopped.
Record the summary and restart the stable transmitter. Follow a passing rehearsal with a short empty
room, still, walking and repeatable gesture pilot at recorded antenna positions before expanding
participant recruitment. Temperature or throughput alone cannot validate sensing performance.
