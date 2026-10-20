import pandas as pd
import os

def process_and_merge(folder_path, label_value, output_name):
    print(f"Processing folder: {folder_path}...")
    
    # Define exact paths
    acc_file = os.path.join(folder_path, "Accelerometer.csv")
    gyro_file = os.path.join(folder_path, "Gyroscope.csv")
    
    # Read the CSV files
    try:
        df_acc = pd.read_csv(acc_file)
        df_gyro = pd.read_csv(gyro_file)
    except FileNotFoundError:
        print(f"Error: Missing required CSV files in {folder_path}")
        return

    # Rename columns to prevent overlapping and to fix the z, y, x order
    # Note: Using 'seconds_elapsed' to match your LibreOffice headers
    df_acc = df_acc.rename(columns={'z': 'acc_z', 'y': 'acc_y', 'x': 'acc_x'})
    df_gyro = df_gyro.rename(columns={'z': 'gyro_z', 'y': 'gyro_y', 'x': 'gyro_x'})

    # We only need the relevant columns
    df_acc = df_acc[['time', 'seconds_elapsed', 'acc_x', 'acc_y', 'acc_z']]
    df_gyro = df_gyro[['time', 'gyro_x', 'gyro_y', 'gyro_z']]

    # Crucial Step: Sort by time before merging (required by merge_asof)
    df_acc = df_acc.sort_values('time')
    df_gyro = df_gyro.sort_values('time')

    # Merge based on the closest timestamp
    # This aligns the gyroscope reading to the nearest millisecond of the accelerometer reading
    merged_df = pd.merge_asof(
        df_acc, 
        df_gyro, 
        on='time', 
        direction='nearest'
    )

    # Add the target Label (0 for ADL, 1 for Fall)
    merged_df['Label'] = label_value

    # Rearrange columns for a clean output
    final_columns = ['time', 'seconds_elapsed', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'Label']
    merged_df = merged_df[final_columns]

    # Save to a master file
    merged_df.to_csv(output_name, index=False)
    print(f"Success! Saved merged data to {output_name}\n")

# ==========================================
# RUN THE MERGE FOR BOTH FOLDERS
# ==========================================

# 1. Process ADL (Walking) -> Label 0
process_and_merge(
    folder_path="adl_walking_packet-2026-05-10_09-37-00", 
    label_value=0, 
    output_name="master_adl_walking.csv"
)

# 2. Process Falling -> Label 1
process_and_merge(
    folder_path="Falling-2026-05-10_12-00-00", 
    label_value=1, 
    output_name="master_falling.csv"
)