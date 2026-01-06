
# Renamed from Read_timing_excel.py to get_patient_eeg_length_summary.py
"""
EEG Duration Validation Checker
Author: Venus
Date: 2024-02-20
Last Updated: 2025-01-06

Description:
This script processes EEG duration data from multiple sites and validates
whether each patient has sufficient recording length.

For each patient:
- Calculates total duration (sum of all EDF files)
- Finds maximum single EDF duration
- Flags if maximum duration exceeds minimum threshold (120 seconds)

Input:
    Excel file with multiple sheets (one per site)
    each sheet has to have a name corresponding to the site you want the name
    Each sheet should have columns: PatientID, Duration in seconds

Output:
    Excel file with one sheet per site containing:
    - PatientID: Patient identifier
    - Sum_Duration: Total duration across all EDFs (seconds)
    - Max_Duration: Duration of longest single EDF (seconds)
    - duration_max_above_120: Boolean flag for quality check

Note:
    to Run this code first make an Excel file and put it in the root folder directory
     and put the name you chose for that file in output_excel_filename
"""
import os
import pandas as pd
from typing import List


def validate_patient_durations(root_folder='Z:/uci_vmostaghimi/testing-root/additional EDFs',
                     input_excel_filename='FU_DX_timings.xlsx',
                     output_excel_filename='PatientsEDF_duration_check.xlsx',
                     min_duration_seconds=120) -> None:
    """
    Validate EDF duration requirements for all patients across multiple sites.

    Reads an Excel file with duration data from multiple sites (one sheet per site),
    groups by patient, calculates duration statistics, and flags patients with
    insufficient recording lengths.

    Args:
        root_folder: Path to folder containing input Excel file
        input_excel_filename: Name of input Excel file with duration data
        output_excel_filename: Name of output Excel file for validation results
        min_duration_seconds: Minimum required duration for single EDF (default: 120 seconds)

    Raises:
        FileNotFoundError: If input Excel file doesn't exist
        ValueError: If required columns are missing or data format is invalid
    """

    # Sheet names to skip (template/placeholder sheets)
    skip_sheet_names = ['sheet1', 'sheet', 'template', 'readme', 'instructions']
    patient_id_prefix_length = 10  # Number of characters for patient identifier

    excel_file_path = os.path.join(root_folder, input_excel_filename)
    if not os.path.exists(excel_file_path):
        raise FileNotFoundError(f"Input Excel file not found: {excel_file_path}")

    # Read all sheets from Excel file
    try:
        excel_data = pd.read_excel(excel_file_path, sheet_name=None)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")

    print(f"Found {len(excel_data)} sheets to process\n")

    skipped_sites = 0
    processed_sites = 0

    for site_name, site_data in excel_data.items():#sitenames is the dictionary key
        if site_name.lower() in skip_sheet_names:
            continue

        try:
            # Validate required columns exist
            required_columns = ['PatientID', 'Duration in seconds']
            missing_columns = [col for col in required_columns if col not in site_data.columns]
            if missing_columns:
                print(f"Warning: Missing columns {missing_columns}, skipping site")
                skipped_sites += 1
                continue

            # Extract patient ID prefix for grouping
            # astype converts the patientIDs to strings and then .str allows to perform
            # vectorwise operation on the patientID
            site_data['PatientID_prefix'] = site_data['PatientID'].astype(str).str[:patient_id_prefix_length]

            # Group by the new column and find the maximum duration within each group
            # Calculate duration statistics per patient
            duration_stats = (
                site_data
                .groupby('PatientID_prefix')['Duration in seconds']
                .agg(['max', 'sum'])
                .reset_index()
            )

            # Create validation report
            validation_report = pd.DataFrame({
                'PatientID': duration_stats['PatientID_prefix'],
                'Sum_Duration': duration_stats['sum'],
                'Max_Duration': duration_stats['max'],
                'duration_max_above_120': duration_stats['max'] > min_duration_seconds
            })
            write_dataframe_to_excel(validation_report, root_folder, output_excel_filename, site_name, mode='a')
            processed_sites +=1
        except Exception as e:
            print(f"couldn't read info from {site_name}: {str(e)}")
            continue
    # Summary
    print(f"   Sites skipped: {skipped_sites}")
    print(f"   Sites processed: {processed_sites}")
#
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


if __name__ == '__main__':

    ROOT_FOLDER = 'Z:/uci_vmostaghimi/23.uconn_jmadan_new'
    INPUT_EXCEL = 'FU_DX_timings.xlsx'
    OUTPUT_EXCEL = 'PatientsEDF_duration_check.xlsx'


    validate_patient_durations(
        root_folder=ROOT_FOLDER,
        input_excel_filename=INPUT_EXCEL,
        output_excel_filename=OUTPUT_EXCEL)



