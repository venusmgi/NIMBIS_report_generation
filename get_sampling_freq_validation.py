# Renamed from Sampling_frequency_matching_header to get_sampling_freq_validation

"""
EEG Sampling Frequency Validator
Author: Venus
Date: 2023-12-11
Last Updated: 2025-12-17

Description:
This script validates EDF sampling frequencies by comparing the frequency stated
in the file header against the true frequency calculated from signal data points
and recording duration.

True Sampling Frequency = Signal Length (data points) / Recording Duration (seconds)

The script flags mismatches which could indicate corrupted files or header errors.

Directory Structure:
    root_folder/
    ├── site1/
    │   ├── patient1/
    │   │   ├── diagnosis/
    │   │   │   └── *.edf
    │   │   └── follow up/
    │   │       └── *.edf
    └── site2/
        └── ...

Output:
    FS_matching_DX.xlsx: Diagnosis sampling frequency validation (one sheet per site)
    FS_matching_FU.xlsx: Follow-up sampling frequency validation (one sheet per site)

Note:
    If you want to run process_all_centers_fs_validation, make sure you make two empty
    Excel spreadsheets with the exact same name as you input to the function, in the
    directory you want to save the Excel spreadsheet (in this scrip the root_folder)
"""

import pyedflib
import pandas as pd
import os


# deviding the datapoint numbers in a signal
# by the length of the signal in seconds to find the true sampling fre


def validate_sampling_frequencies(folder_path):
    """
        Validate sampling frequencies for all EDF files in a folder.

        Compares the stated sampling frequency in the file header against the
        true frequency calculated from signal length and recording duration.

        Args:
            folder_path (str): Path to folder containing EDF files

        Returns:
            pd.DataFrame: DataFrame with columns:
                - 'PatientID': Name of the EDF file
                - 'Header_Fs': Sampling frequency from file header (Hz)
                - 'Calculated_Fs': True frequency calculated from signal data (Hz)
                - 'Matching': 1 if frequencies match , 0 otherwise
            Returns empty DataFrame if folder doesn't exist or contains no EDF files.
        """

    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found - {folder_path}")
        return pd.DataFrame(columns=["PatientID", "Header_Fs", "Calculated_Fs", "Matching"])

    try:
        edf_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.edf')]
    except Exception as e:
        print(f"Error listing directory {folder_path}: {str(e)}")
        return pd.DataFrame(columns=["PatientID", "Header_Fs", "Calculated_Fs", "Matching"])

    if not edf_files:
        return pd.DataFrame(columns=["PatientID", "Header_Fs", "Calculated_Fs", "Matching"])

    # Collect validation data
    validation_data = []

    for edf_filename in edf_files:
        try:
            full_path = os.path.join(folder_path, edf_filename)

            # Read EDF file with context manager
            with pyedflib.EdfReader(full_path) as edf_reader:

                # Get header sampling frequency (from first channel),
                # since they cannot be different in each channel
                header_fs = edf_reader.getSampleFrequencies()[0]

                # Get recording duration
                duration_seconds = edf_reader.getFileDuration()

                # Read signal data to count samples
                signal = edf_reader.readSignal(0, start=0, n=None, digital=True) #read first channel
                signal_length = len(signal)

                if duration_seconds != 0:

                    calculated_fs = signal_length / duration_seconds
                    matching = 1 if calculated_fs == header_fs else 0
                    validation_data.append({"PatientID": edf_filename,
                                            "Header_Fs": header_fs,
                                            "Calculated_Fs": calculated_fs,
                                            "Matching": matching})
                else:
                    validation_data.append({"PatientID": edf_filename,
                                            "Header_Fs": None,
                                            "Calculated_Fs": None,
                                            "Matching": None})




        except Exception as e:
            print(f"    Error processing {edf_filename}: {str(e)}")
            continue

    if not validation_data:
        print(f"Warning: No valid sampling frequency data collected from {folder_path}")
        return pd.DataFrame(columns=["PatientID", "Header_Fs", "Calculated_Fs", "Matching"])

    validation_df = pd.DataFrame(validation_data)
    return validation_df


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
            data_frame.to_excel(writer, sheet_name=sheet_name, index=False, na_rep='')
    except Exception as e:
        print(f"Error writing to Excel file {excel_filename}, sheet {sheet_name}: {str(e)}")


def process_single_center_fs_validation(center_dir, diagnosis_folder_name="diagnosis",
                                        follow_up_folder_name="follow up"):
    """
    Validate sampling frequencies for all EDF files in a single center.

    Args:
        center_dir (str): Path to the center directory
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Returns:
        tuple: (dx_validation_df, fu_validation_df) - Validation results for DX and FU
    """

    if not os.path.exists(center_dir):
        raise FileNotFoundError(f"Center directory not found: {center_dir}")

    center_name = os.path.basename(center_dir)
    print(f"\nProcessing Center: {center_name}")

    # Get all patient IDs (subdirectories only)
    patient_ids = [id.name for id in os.scandir(center_dir) if id.is_dir()]
    print(f"  Found {len(patient_ids)} patients")

    # Collect validation data for all patients
    all_dx_validation = []
    all_fu_validation = []

    for patient_id in patient_ids:

        dx_path = os.path.join(center_dir, patient_id, diagnosis_folder_name)
        dx_validation = validate_sampling_frequencies(dx_path)

        fu_path = os.path.join(center_dir, patient_id, follow_up_folder_name)
        fu_validation = validate_sampling_frequencies(fu_path)

        if not dx_validation.empty:
            all_dx_validation.append(dx_validation)

        if not fu_validation.empty:
            all_fu_validation.append(fu_validation)

    # Combine all patients' data
    if all_dx_validation:
        combined_dx = pd.concat(all_dx_validation, ignore_index=True)
    else:
        combined_dx = pd.DataFrame(columns=["PatientID", "Header_Fs",
                                            "Calculated_Fs", "Matching"])
        print(f"\n  DX Summary: No files processed")

    if all_fu_validation:
        combined_fu = pd.concat(all_fu_validation, ignore_index=True)
    else:
        combined_fu = pd.DataFrame(columns=["PatientID", "Header_Fs",
                                            "Calculated_Fs", "Matching"])
        print(f"  FU Summary: No files processed\n")

    return combined_dx, combined_fu


def process_all_centers_fs_validation(root_folder, diagnosis_folder_name="diagnosis",
                                      follow_up_folder_name="follow up",
                                      dx_excel_filename  = 'FS_matching_DX.xlsx',
                                      fu_excel_filename  = 'FS_matching_FU.xlsx'):
    """
    Validate sampling frequencies for all centers.

    Args:
        root_folder (str): Path to root directory containing center folders
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Output Files (saved in root_folder):
        FS_matching_DX.xlsx: One sheet per center with DX validation results
        FS_matching_FU.xlsx: One sheet per center with FU validation results
    """

    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Root folder not found: {root_folder}")

    # Get all center directories
    center_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    center_names = [os.path.basename(center_dir) for center_dir in center_directories]

    # Process each center
    for center_idx, center_directory in enumerate(center_directories):
        center_name = center_names[center_idx]

        dx_validation, fu_validation = process_single_center_fs_validation(
            center_directory,
            diagnosis_folder_name=diagnosis_folder_name,
            follow_up_folder_name=follow_up_folder_name)
        # Save to Excel (separate files for DX and FU)
        write_dataframe_to_excel(
            dx_validation,
            root_folder,
            dx_excel_filename,
            center_name,
            mode='a'
        )

        write_dataframe_to_excel(
            fu_validation,
            root_folder,
            fu_excel_filename,
            center_name,
            mode='a'
        )


if __name__ == '__main__':
    # CONFIGURATION

    DIAGNOSIS_FOLDER = "diagnosis"
    FOLLOWUP_FOLDER = "follow up"
    DX_EXCEL_FILENAME = "FS_matching_DX.xlsx"
    FU_EXCEL_FILENAME ="FS_matching_FU.xlsx"


    # MODE SELECTION


    # ------ Option 1: Process ALL Centers ------
    # Uncomment to process multiple centers:
    # process_all_centers_fs_validation(
    #     root_folder="Z:/uci_vmostaghimi/testing-root/",
    #     diagnosis_folder_name=DIAGNOSIS_FOLDER,
    #     follow_up_folder_name=FOLLOWUP_FOLDER,
    #     dx_excel_filename =DX_EXCEL_FILENAME,
    #     fu_excel_filename=FU_EXCEL_FILENAME
    # )

    # ------ Option 2: Process SINGLE Center ------

    dx_df, fu_df = process_single_center_fs_validation(
        center_dir='Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        diagnosis_folder_name=DIAGNOSIS_FOLDER,
        follow_up_folder_name=FOLLOWUP_FOLDER,
    )

    # Save single center results
    write_dataframe_to_excel(
        dx_df,
        folder_dir='Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        excel_filename=DX_EXCEL_FILENAME,
        sheet_name="23.uconn_jmadan",
        mode='w'
    )

    write_dataframe_to_excel(
        fu_df,
        folder_dir='Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        excel_filename=FU_EXCEL_FILENAME,
        sheet_name="23.uconn_jmadan",
        mode='w'
    )

