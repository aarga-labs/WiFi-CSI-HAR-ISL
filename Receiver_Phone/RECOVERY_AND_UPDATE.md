# Phone v1.1 and P04 recovery

1. Finish/save any recording first. Connect the Samsung to the laptop by USB using a data cable, enable USB debugging if needed, and run from this folder:

```bash
./START_USB.sh --reinstall
```

This uses an in-place signed update (`adb install -r`). Do not uninstall or clear app storage. Existing phone files remain in app-private storage. If USB debugging is unavailable, copy FYP_Phone_Collector.apk to the phone and install it over the existing app using the same signing identity.

2. Open the phone app and confirm its opening text says **Version 1.1**. Keep the app visible during recording. The app keeps its window awake, and acquires a fresh CPU wake lock for the duration of every recording. Use unrestricted battery mode. You can disconnect USB and use the existing trusted Wi-Fi address after connecting the app.

3. Version 1.1 stops and preserves a `sensor_error` partial run if a measured sensor gap exceeds 100 ms, sensor delivery stalls for over one second, or a phone cue callback runs more than 200 ms late. It cancels remaining cue callbacks when stopping. It will not silently continue a badly delayed phase schedule and report it complete. Raw data are retained for review.

4. The current local controller has to load the additional makeup block; restart it only when no recording is active. Refresh the website, enable/test laptop sound, and reload commands:

```bash
source ./COMMANDS.sh P04 S01
p04_activities_stand_patch
```

The command starts both modalities and records only 45 selected replacement trials, about 7 minutes 36 seconds of scheduled recording. Wait for FINISHED without clicking Stop. The receiver may need extra time to close and transfer may take additional time.

5. Original useful data were recovered into `recovery/P04_activities_standing_20261113_124340/`. The three `_recovered.csv` files contain 70 retained trials. No raw sample or original recording file was modified. The derived manifest records file hashes, criteria and original trial IDs. The makeup data must be audited before adding replacements and declaring all 115 trials complete.

The operator confirmed following the laptop website prompts throughout the original run. Consequently the recovery uses the laptop's intended schedule and phone hardware timestamps mapped to the controller clock, not the delayed phone cue callbacks. Movement execution and physical timing alignment are not independently calibrated by this recovery.

Keep the phone app visible even with the CPU wake-lock protection. Device restrictions, process kills and hardware failures cannot be guaranteed away; these guards turn detected failures into explicit partial runs. Physical M35 behavior must be checked after updating. Emulator tests are development evidence, not participant data.
