
# renamed from Get_StartEndTime.py to get_edf_timing_info
"""
EEG Recording Timing Analyzer
Author: Venus
Date: 2024-07-13
Last Updated: 2025-12-18

Description:
This script processes EDF (European Data Format) files by reading their headers to
extract timing information including start time, duration, and end time. It flags
recordings shorter than 2 minutes for quality control.

Multiple center directory structure:
    root_folder/
    ├── center1/
    │   ├── patient1/
    │   │   ├── diagnosis/
    │   │   │   └── *.edf
    │   │   └── follow up/
    │   │       └── *.edf
    │   └── patient2/
    │       ├── diagnosis/
    │       └── follow up/
    └── site2/
        └── ...

Output:
    FU_DX_timings.xlsx: Excel file with one sheet per site containing timing
                        information for all EDF files

Usage:
    # Process single center
    process_single_center_timing(center_dir="path/to/center/")

    # Process all centers
    process_all_centers_timing(root_folder="path/to/root/")

Requirements:
    pip install pyedflib pandas openpyxl
"""


import pyedflib
import pandas as pd
import os

from datetime import timedelta

def   extract_edf_timing_info(folder_path, min_duration_seconds=120):
    """
        Extract timing information from all EDF files in a folder.

        Reads EDF headers to collect start time, end time, and duration.
        Flags files shorter than the specified minimum duration.

        Args:
            folder_path (str): Path to folder containing EDF files
            min_duration_seconds (int): Minimum acceptable duration in seconds (default: 120)

        Returns:
            pd.DataFrame: DataFrame with columns:
                - 'EDF_Filename': Name of the EDF file
                - 'Start_DateTime': Recording start datetime
                - 'End_DateTime': Recording end datetime
                - 'Duration_Seconds': Recording duration in seconds
                - 'Short_Duration_Flag': 1 if duration < min_duration_seconds, else 0
            Returns empty DataFrame if folder doesn't exist or contains no EDF files
        """
    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found - {folder_path}")
        return pd.DataFrame()

    # Get all EDF files
    try:
        edf_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.edf')]
    except Exception as e:
        print(f"Error listing directory {folder_path}: {str(e)}")
        return pd.DataFrame()

    if not edf_files:
        print(f"Warning: No EDF files found in {folder_path}")
        return pd.DataFrame()

    timing_data = []

    for edf_filename in edf_files:
        try:
            full_path = os.path.join(folder_path, edf_filename)

            # Read edf timing information

            with pyedflib.EdfReader(full_path) as edf_reader:
                start_datetime = edf_reader.getStartdatetime()
                duration_seconds = edf_reader.getFileDuration()

            # Calculate end time
            duration = timedelta(seconds=duration_seconds)
            end_datetime = start_datetime + duration

            flag = 1 if duration_seconds < min_duration_seconds else 0
            timing_data.append({"PatientID": edf_filename,
                                     "Start DateTime": start_datetime,
                                     "Finish DateTime": end_datetime,
                                     "Duration in seconds": duration_seconds,
                                     "Duration < 120 s": flag})
        except Exception as e:
            print(f"Error reading {edf_filename}: {str(e)}")
            continue
    if not timing_data:
        print(f"Warning: No valid EDF timing data collected from {folder_path}")
        return pd.DataFrame()
    # writing into df
    timing_data_df = pd.DataFrame(timing_data)
    return timing_data_df


def write_dataframe_to_excel(data_frame, folder_dir, excel_filename, sheet_name, mode='a'):
    """
    Write a DataFrame to an Excel file as a new sheet.

    Args:
        data_frame (pd.DataFrame): Data to write
        folder_dir (str): Directory where Excel file should be saved
        excel_filename (str): Name of the Excel file
        sheet_name (str): Name of the sheet to create
        mode (str): Write mode - 'a' for append (default), 'w' for overwrite
    """

    if data_frame.empty:
        print(f"Warning: Empty DataFrame, skipping write for sheet '{sheet_name}'")
        return
    excel_path = os.path.join(folder_dir, excel_filename)
    try:
        with pd.ExcelWriter(excel_path, mode=mode, engine='openpyxl') as writer:
            data_frame.to_excel(writer, sheet_name=sheet_name, na_rep='', index=False )
    except Exception as e:
        print(f"Error writing to Excel file {excel_filename}, sheet {sheet_name}: {str(e)}")


def process_single_center_timing(center_dir, diagnosis_folder_name="diagnosis",
                                 follow_up_folder_name="follow up",
                                 min_duration_seconds=120):
    """
    Process all EDF files in a single center and extract timing information.

    Args:
        center_dir (str): Path to the center directory
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")
        min_duration_seconds (int): Minimum duration threshold in seconds (default: 120)

    Returns:
        pd.DataFrame: Combined timing information for all patients in the center
    """
    if not os.path.exists(center_dir):
        raise FileNotFoundError(f"Center directory not found: {center_dir}")

    center_name = os.path.basename(center_dir)
    print(f"\nProcessing Center: {center_name}")

    # Get all patient IDs (subdirectories only)
    patient_ids = [d for d in os.listdir(center_dir)
                   if os.path.isdir(os.path.join(center_dir, d))]

    print(f"Found {len(patient_ids)} patients")
    all_timing = []
    for patient_id in patient_ids:
        print(f"Processing Patient: {patient_id}")
        dx_path = os.path.join(center_dir, patient_id, diagnosis_folder_name)
        timing_dx = extract_edf_timing_info(dx_path, min_duration_seconds)

        fu_path = os.path.join(center_dir, patient_id, follow_up_folder_name)
        timing_fu = extract_edf_timing_info(fu_path, min_duration_seconds)

        timing_one = pd.concat([timing_dx, timing_fu], axis=0)
        all_timing.append(timing_one)
    if all_timing:
        combined_timing = pd.concat(all_timing, ignore_index=True)
        return combined_timing
    else:
        return pd.DataFrame()



def process_all_centers_timing(root_folder, diagnosis_folder_name="diagnosis",
                               follow_up_folder_name="follow up",
                               excel_filename="FU_DX_timings.xlsx",
                               min_duration_seconds=120):
    """
    Process all centers and extract timing information from all EDF files.

    Args:
        root_folder (str): Path to root directory containing center folders
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")
        min_duration_seconds (int): Minimum duration threshold in seconds (default: 120)

    Output Files (saved in root_folder):
        FU_DX_timings.xlsx: One sheet per center with timing information
    """

    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Root folder not found: {root_folder}")

    # Get all center directories
    center_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    center_names = [os.path.basename(center_dir) for center_dir in center_directories]

    print(f"\n{'=' * 60}")
    print(f"Found {len(center_names)} centers to process")
    print(f"{'=' * 60}\n")

    # Process each center
    for center_idx, center_directory in enumerate(center_directories):
        center_name = center_names[center_idx]
        print(f"Processing Center {center_idx + 1}/{len(center_directories)}: {center_name}")

        center_timing = process_single_center_timing(
            center_directory,
            diagnosis_folder_name=diagnosis_folder_name,
            follow_up_folder_name=follow_up_folder_name,
            min_duration_seconds=min_duration_seconds
        )

        # Save to Excel (one sheet per center)
        write_dataframe_to_excel(
            center_timing,
            root_folder,
            excel_filename,
            center_name,
            mode='a'
        )



if __name__ == '__main__':

    # CONFIGURATION
    DIAGNOSIS_FOLDER = "diagnosis"
    FOLLOWUP_FOLDER = "follow up"
    EXCEL_FILENAME = "FU_DX_timings.xlsx"
    MIN_DURATION_SECONDS = 120  # Flag files shorter than 2 minutes


    # ------ Option 1: Process ALL Centers ------
    # Uncomment to process multiple centers:
    # process_all_centers_timing(
    #     root_folder="Z:/uci_vmostaghimi/testing-root/",
    #     diagnosis_folder_name=DIAGNOSIS_FOLDER,
    #     follow_up_folder_name=FOLLOWUP_FOLDER,
    #     excel_filename=EXCEL_FILENAME,
    #     min_duration_seconds=MIN_DURATION_SECONDS
    # )

    # ------ Option 2: Process SINGLE Center ------
    timing_info_df = process_single_center_timing(
        center_dir= 'Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        diagnosis_folder_name=DIAGNOSIS_FOLDER,
        follow_up_folder_name=FOLLOWUP_FOLDER,
        min_duration_seconds=MIN_DURATION_SECONDS
    )

    write_dataframe_to_excel(
        timing_info_df,
        folder_dir='Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        excel_filename=EXCEL_FILENAME,
        sheet_name="23.uconn_jmadan",
        mode='w')




