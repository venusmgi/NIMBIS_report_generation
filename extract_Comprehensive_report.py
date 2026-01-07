
"""
EEG Comprehensive Report Generator
Author: Venus
Date: 2024-02-20
Last Updated: 2025-01-06

Description:
This script consolidates multiple EEG quality check reports into a single comprehensive report.
It reads various validation sheets (duration, sampling frequency, channel labels, intervals)
and merges them into one summary Excel file.

Input Excel Sheets Expected:
    - 'EDF Duration': Duration validation results
    - 'FU-DX interval': Follow-up to Diagnosis time intervals
    - 'fs-matching DX': Diagnosis sampling frequency validation
    - 'fs-matching FU': Follow-up sampling frequency validation
    - 'Channel Labels': Channel configuration validation

Output:
    comprehensive_report.xlsx: Single sheet with merged validation results

Note:
    This code cannot be used for multiple centers at the same time. It processes
    one center at a time.
"""



import os
import pandas as pd
from typing import Dict, List


# Constants
PATIENT_ID_PREFIX_LENGTH = 13  # First 13 characters identify the patient
MIN_SAMPLING_FREQUENCY_HZ = 200
MAX_SAMPLING_FREQUENCY_ERROR_PERCENT = 1.0

# Standard EEG channel names (10-20 system + reference)
ESSENTIAL_CHANNEL_NAMES = [
    'Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2',
    'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz', 'A1', 'A2'
]

# Channels required for valid montage (excludes reference electrodes)
MONTAGE_REQUIRED_CHANNELS = [
    'Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2',
    'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz'
]

# Marker for missing channels in reports
MISSING_CHANNEL_MARKER = '***'


def extract_patient_id_prefix(patient_id_series: pd.Series) -> pd.Series:
    """
    Extract patient ID prefix (first N characters) for grouping.

    Args:
        patient_id_series: Series containing patient IDs

    Returns:
        Series with patient ID prefixes
    """
    return patient_id_series.astype(str).str[:PATIENT_ID_PREFIX_LENGTH]

def validate_sampling_frequency_data(fs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate sampling frequency data and add validation flag.

    Args:
        fs_df: DataFrame with columns 'Header_Fs' and 'Calculated_Fs'

    Returns:
        DataFrame with added 'FS_check' column (1 = pass, 0 = fail)
    """
    fs_check_list = []

    for idx, _ in fs_df.iterrows():
        header_fs = fs_df.loc[idx, 'Header_Fs']
        calculated_fs = fs_df.loc[idx, 'Calculated_Fs']

        # Calculate percentage error
        if header_fs != 0:
            error_percent = abs((calculated_fs - header_fs) / header_fs * 100)
            is_valid = (error_percent <= MAX_SAMPLING_FREQUENCY_ERROR_PERCENT and
                        header_fs >= MIN_SAMPLING_FREQUENCY_HZ)
            fs_check_list.append(1 if is_valid else 0)
        else:
            fs_check_list.append(0)

    fs_df['FS_check'] = fs_check_list
    fs_df['PatientID_prefix'] = extract_patient_id_prefix(fs_df['PatientID'])

    # Group by patient - all EDFs must pass for patient to pass
    fs_check = (
        fs_df
        .groupby('PatientID_prefix', group_keys=True)['FS_check']
        .min()  # min() ensures ALL files pass
        .reset_index()
    )

    return fs_check


def process_duration_sheet(duration_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process EDF duration validation sheet.

    Args:
        duration_df: DataFrame from 'EDF Duration' sheet

    Returns:
        DataFrame grouped by patient with duration validation results
    """

    duration_df['PatientID_prefix'] = duration_df['PatientID']

    duration_df['Duration_check'] = (duration_df['duration_max_above_120'] * 1)

    # Group by patient - all EDFs must pass for patient to pass
    patient_duration_check = (
        duration_df
        .groupby('PatientID_prefix')['Duration_check']
        .min()
        .reset_index()
    )

    return patient_duration_check


def process_channel_labels_sheet(channel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process channel labels validation sheet.

    Args:
        channel_df: DataFrame from 'Channel Labels' sheet

    Returns:
        DataFrame grouped by patient with channel validation results
    """
    # Find missing channels (marked with '***') for each row
    missing_channels_per_row = []

    for _, row in channel_df.iterrows():
        missing_channels = channel_df.columns[row == MISSING_CHANNEL_MARKER].tolist()
        missing_channels_per_row.append(missing_channels)

    channel_df['missingChans'] = missing_channels_per_row
    channel_df['PatientID_prefix'] = extract_patient_id_prefix(channel_df['identifier'])

    # Group by patient
    grouped_missing_channels = (
        channel_df
        .groupby('PatientID_prefix')['missingChans']
        .apply(lambda x: x)
    )

    # Check if essential channels are missing
    essential_channels_check = pd.DataFrame({
        'PatientID_prefix': channel_df['PatientID_prefix'],
        'essential_channels_ok': ~grouped_missing_channels.isin(ESSENTIAL_CHANNEL_NAMES)
    })

    # Check if montage is valid
    montage_check = pd.DataFrame({
        'PatientID_prefix': channel_df['PatientID_prefix'],
        'montage_check': ~grouped_missing_channels.isin(MONTAGE_REQUIRED_CHANNELS)
    })

    # Merge and remove duplicates
    channel_validation = pd.merge(
        grouped_missing_channels,
        essential_channels_check,
        on='PatientID_prefix',
        how='outer'
    )

    montage_check_unique = montage_check.drop_duplicates(subset=['PatientID_prefix'])

    channel_validation = pd.merge(
        channel_validation,
        montage_check_unique,
        on='PatientID_prefix',
        how='outer'
    )

    channel_validation_unique = channel_validation.drop_duplicates(subset=['PatientID_prefix'])

    return channel_validation_unique


def generate_comprehensive_report(root_folder: str = 'D:/Users/vmostaghimi_choc/Desktop/site reports/10.CHOC',
                                  input_excel_filename: str = '10.CHOC_overall_report_input.xlsx',
                                  output_excel_filename: str = 'comprehensive_report.xlsx') -> None:
    """
    Generate comprehensive EEG quality validation report.

    Reads multiple validation sheets from an input Excel file and merges them
    into a single comprehensive report showing all quality checks per patient.

    Args:
        root_folder: Path to folder containing input Excel file
        input_excel_filename: Name of input Excel file with validation sheets
        output_excel_filename: Name of output Excel file for comprehensive report

    Raises:
        FileNotFoundError: If input Excel file doesn't exist
        ValueError: If required sheets are missing or data format is invalid
    """

    # Validate input file exists
    excel_file_path = os.path.join(root_folder, input_excel_filename)
    if not os.path.exists(excel_file_path):
        raise FileNotFoundError(f"Input Excel file not found: {excel_file_path}")

    # Read all sheets from Excel file
    try:
        excel_data = pd.read_excel(excel_file_path, sheet_name=None)
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {str(e)}")

    # Process each sheet
    sheet_results = {}

    for sheet_name, sheet_df in excel_data.items():
        print(f"  Processing sheet: {sheet_name}")

        if sheet_name == 'EDF Duration':
            sheet_results['duration'] = process_duration_sheet(sheet_df)

        elif sheet_name == 'FU-DX interval':
            sheet_results['interval'] = sheet_df.rename(columns={"patientID": "PatientID_prefix"})

        elif sheet_name == 'fs-matching DX':
            sheet_results['fs_dx'] = validate_sampling_frequency_data(sheet_df)

        elif sheet_name == 'fs-matching FU':
            sheet_results['fs_fu'] = validate_sampling_frequency_data(sheet_df)

        elif sheet_name == 'Channel Labels':
            sheet_results['channels'] = process_channel_labels_sheet(sheet_df)

    # Validate required sheets are present
    required_sheets = ['duration', 'fs_dx', 'fs_fu', 'channels']
    missing_sheets = [s for s in required_sheets if s not in sheet_results]
    if missing_sheets:
        raise ValueError(f"Missing required sheets: {missing_sheets}")

    # Merge sampling frequency checks (DX and FU)
    fs_merged = pd.merge(
        sheet_results['fs_dx'],
        sheet_results['fs_fu'],
        on='PatientID_prefix',
        how='outer',
        suffixes=('_DX', '_FU')
    )

    # Combine DX and FU FS checks into single column
    fs_merged['FS_check'] = fs_merged['FS_check_DX'].combine_first(fs_merged['FS_check_FU'])
    fs_merged = fs_merged.drop(['FS_check_DX', 'FS_check_FU'], axis=1)

    # Merge all validation results
    print(f"\nMerging all validation results...")
    comprehensive_report = (
        sheet_results['duration']
        .merge(sheet_results['channels'], on='PatientID_prefix')
        .merge(fs_merged, on='PatientID_prefix')
    )

    # Rename for clarity
    comprehensive_report = comprehensive_report.rename(columns={'PatientID_prefix': 'PatientID'})

    # Write output
    try:
        write_dataframe_to_excel(
            comprehensive_report,
            root_folder,
            output_excel_filename,
            'comprehensive_report',
            mode='w'  # Overwrite mode for fresh report
        )

    except Exception as e:
        raise IOError(f"Error writing output file: {str(e)}")


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


if __name__ == '__main__':


    ROOT_FOLDER = 'Z:/uci_vmostaghimi/23.uconn_jmadan_new'
    INPUT_EXCEL = '23.uconn_jmadan_new_overall_report_input.xlsx'
    OUTPUT_EXCEL = 'comprehensive_report.xlsx'
    generate_comprehensive_report(
        root_folder=ROOT_FOLDER,
        input_excel_filename=INPUT_EXCEL,
        output_excel_filename=OUTPUT_EXCEL
    )
