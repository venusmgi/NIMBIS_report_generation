# renamed from FUDXInterval.py to get_FU_DX_interval.py

"""
EEG Diagnosis-FollowUp Interval Calculator
Author: Venus
Date: 2023-07-13
Last Updated: 2025-12-17

Description:
This script calculates the time interval (in days) between the first diagnosis (DX)
and first follow-up (FU) EEG recording for each patient by reading the start datetime
from EDF file headers.

For each patient:
- Reads the start datetime from the first DX EDF file
- Reads the start datetime from the first FU EDF file
- Calculates the interval in days
- Validates that all EDF files in each folder have the same start datetime

Folder Structure:
    testing_root/
    ├── site1/
    │   ├── patient1/
    │   │   ├── diagnosis/
    │   │   └── follow up/
    └── site2/
        └── ...

Output:
    FU_DX_intervals.xlsx: Excel file with one sheet per center containing
                          patient IDs and their DX-FU intervals in days

Usage:
    # Process single center
    calculate_intervals_single_center(center_dir="path/to/center/")

    # Process all centers
    calculate_intervals_multiple_centers(root_folder="path/to/root/")

Note:
    If you want to run calculate_intervals_multiple_centers, make sure you make an empty
    Excel spreadsheet with the exact same name as you input to the function, in the
    directory you want to save the Excel spreadsheet (in this scrip the root_folder)
"""

import os
import pyedflib
import pandas as pd


def get_first_edf_start_datetime(folder_path):
    """
    Extract start datetime from the first EDF file in a folder.

    Also validates that all EDF files in the folder have the same start datetime,
    printing a warning if discrepancies are found.

    Args:
        folder_path (str): Path to folder containing EDF files

    Returns:
        datetime or None: Start datetime of the first EDF file, or None if:
            - Folder doesn't exist
            - No EDF files found
            - Error reading files
    """

    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found - {folder_path}")
        return None

    # Get all EDF files in the folder
    try:
        edf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.edf')]
    except Exception as e:
        print(f"Error listing directory {folder_path}: {str(e)}")
        return None

    if not edf_files:
        print(f"Warning: No EDF files found in {folder_path}")
        return None

    # Read first EDF file's start datetime

    first_edf_datetime = None
    for edf_index, edf_filename in enumerate(edf_files):
        try:
            full_path = os.path.join(folder_path, edf_filename)
            # full_path = folder_path + edf_filename
            with pyedflib.EdfReader(full_path) as edf_reader:
                current_datetime = edf_reader.getStartdatetime()

            # Store the first file's datetime
            if edf_index == 0:
                first_edf_datetime = current_datetime

            # Validate subsequent files have the same datetime
            else:
                if first_edf_datetime != current_datetime:  # Add "if"!
                    print(f"  Warning: Datetime discrepancy in {edf_filename}")
                    print(f"    Expected: {first_edf_datetime}")
                    print(f"    Found: {current_datetime}")

        except Exception as e:
            print(f"Error handling {edf_filename}: {str(e)}")
            continue
    return first_edf_datetime

def write_dataframe_to_excel(data_frame, folder_dir, excel_filename, sheet_name, mode='a'):
    """
    Write a DataFrame to an Excel file as a new sheet.

    Args:
        data_frame (pd.DataFrame): Data to write
        output_dir (str): Directory where Excel file should be saved
        excel_filename (str): Name of the Excel file
        sheet_name (str): Name of the sheet to create
        mode (str): Write mode - 'a' for append (default), 'w' for overwrite
    """

    if data_frame.empty:
        print(f"Warning: Empty DataFrame, skipping write for sheet '{sheet_name}'")
        return
    try:
        excel_path = os.path.join(folder_dir, excel_filename)
        with pd.ExcelWriter(excel_path, mode=mode, engine='openpyxl') as writer:
            data_frame.to_excel(writer, sheet_name=sheet_name, index=False, na_rep='')
    except Exception as e:
        print(f"Error writing to Excel file {excel_filename}, sheet {sheet_name}: {str(e)}")

def calculate_intervals_single_center(center_dir, diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    """
    Calculate DX-FU intervals for all patients in a single center.

    Args:
        center_dir (str): Path to the center directory
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Returns:
        pd.DataFrame: DataFrame with columns 'patientID' and 'interval_days'
    """
    if not os.path.exists(center_dir):
        raise FileNotFoundError(f"Center directory not found: {center_dir}")

    center_name = os.path.basename(center_dir)
    print(f"\nProcessing Center: {center_name}")

    # Get all patient IDs (subdirectories only, exclude any other file such as excel or .mat files
    patient_ids = [id for id in os.listdir(center_dir) if os.path.isdir(os.path.join(center_dir, id))]

    print(f"  Found {len(patient_ids)} patients")

    # Collect interval data
    intervals_data = []

    for patient_id in patient_ids:
        print(f"Processing Patient: {patient_id}")

        # Build paths to DX and FU folders
        dx_folder_path = os.path.join(center_dir, patient_id, diagnosis_folder_name)
        fu_folder_path = os.path.join(center_dir, patient_id, follow_up_folder_name)

        # Get start datetimes
        dx_start = get_first_edf_start_datetime(dx_folder_path)
        fu_start = get_first_edf_start_datetime(fu_folder_path)

        # Calculate interval if both datetimes are valid
        if dx_start is None or fu_start is None:
            print(f"      Skipping {patient_id} - missing DX or FU data")
            intervals_data.append({'patientID': patient_id,
                                   'interval_days': None,
                                   'status': 'Missing data'})
            continue

        # Calculate interval
        try:
            interval = fu_start - dx_start
            interval_seconds = interval.total_seconds()
            interval_hours = interval_seconds/ 3600
            interval_days = interval_hours/24

            intervals_data.append({
                'patientID': patient_id,
                'interval_days': round(interval_days),
                'status': 'Success'
            })
        except Exception as e:
            print(f"Error calculating interval: {str(e)}")
            intervals_data.append({
                'patientID': patient_id,
               'interval_days': None,
                'status':  f'Error: {str(e)}'
            })
    intervals_df = pd.DataFrame(intervals_data)
    return intervals_df

def calculate_intervals_multiple_centers(root_folder,
                                         diagnosis_folder_name="diagnosis",
                                         follow_up_folder_name="follow up",
                                         excel_filename="FU_DX_intervals_new.xlsx"):
    """
    Calculate DX-FU intervals for all centers in root folder.

    Args:
        root_folder (str): Path to root directory containing center folders
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Output Files (saved in root_folder):
        FU_DX_intervals.xlsx: One sheet per center with patient intervals
    """

    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Root folder not found: {root_folder}")

    # Get all center directories
    center_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    center_names = [os.path.basename(center_dir) for center_dir in center_directories]

    print(f"\nFound {len(center_names)} centers to process\n")

    # process each center
    for center_idx, center_directory in enumerate(center_directories):

        center_name = center_names[center_idx]
        print(f"Processing Center {center_idx + 1}/{len(center_directories)}: {center_name}")
        center_intervals = calculate_intervals_single_center(center_directory, diagnosis_folder_name=diagnosis_folder_name,
                                          follow_up_folder_name=follow_up_folder_name)

        # Save to Excel (one sheet per center)
        write_dataframe_to_excel(
            center_intervals,
            root_folder,
            excel_filename,
            center_name,
            mode='a'
        )


if __name__ == "__main__":

    # CONFIGURATION
    DIAGNOSIS_FOLDER = "diagnosis"
    FOLLOWUP_FOLDER = "follow up"
    EXCEL_FILENAME = "FU_DX_intervals_new.xlsx"

    # ------ Option 1: Process ALL Centers ------
    # Uncomment to process multiple centers:
    ROOT_FOLDER = "Z:/uci_vmostaghimi/testing-root/"
    calculate_intervals_multiple_centers(
        root_folder=ROOT_FOLDER,
        diagnosis_folder_name=DIAGNOSIS_FOLDER,
        follow_up_folder_name=FOLLOWUP_FOLDER,
        excel_filename=EXCEL_FILENAME
    )

    # ------ Option 2: Process SINGLE Center ------

    # result_df = calculate_intervals_single_center(
    #     center_dir="Z:/uci_vmostaghimi/23.uconn_jmadan_new",
    #     diagnosis_folder_name=DIAGNOSIS_FOLDER,
    #     follow_up_folder_name=FOLLOWUP_FOLDER
    # )
    #
    # # Save single center results
    # write_dataframe_to_excel(
    #     result_df,
    #     "Z:/uci_vmostaghimi/23.uconn_jmadan_new",
    #     EXCEL_FILENAME,
    #     "23.uconn_jmadan",
    #     mode='w'
    # )