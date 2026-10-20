#!/usr/bin/env python3
import os
import glob
import subprocess

def main():
    pilot_dir = "/home/rishiikesh/usrp-projects/data/pilot"
    csi_tools_dir = "/home/rishiikesh/usrp-projects/USRP_lib/csi_tools"
    segment_script = os.path.join(csi_tools_dir, "segment_windows.py")
    out_dir = os.path.join(pilot_dir, "windows")

    csv_files = glob.glob(os.path.join(pilot_dir, "*.csv"))
    print(f"Found {len(csv_files)} CSV files to segment.")

    for csv_file in csv_files:
        basename = os.path.basename(csv_file)
        # Parse action/noaction and subject from filename
        # Format: P01_action_<subject>_<date>_<take>.csv
        parts = basename.split("_")
        if len(parts) < 3:
            print(f"Skipping {basename}: invalid filename format")
            continue
        
        action = parts[1] # "action" or "noaction"
        subject = parts[2] # "amrith" or "rishiikesh"
        
        print(f"Segmenting {basename} (action={action}, subject={subject})...")
        cmd = [
            "python3", segment_script,
            csv_file,
            "--action", action,
            "--subject", subject,
            "--out-dir", out_dir
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(res.stdout.strip())
        else:
            print(f"Error segmenting {basename}:")
            print(res.stderr)

if __name__ == "__main__":
    main()
