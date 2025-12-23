# renamed from Chann_Fs_find.py to get_channel_labels_and_sampling_frequency

"""
EEG Metadata Extraction Tool
Author: Venus Mostaghimi
Date: 2023-06-27
Last Updated: 2025-12-17

Description:
This script extracts metadata (channel labels and sampling frequencies) from EDF
(European Data Format) EEG recordings organized in a hierarchical folder structure:
- Root folder contains multiple center directories (20 centers)
- Each center contains patient ID folders
- Each patient folder has 'diagnosis' and 'follow up' subdirectories
- Each subdirectory contains .EDF EEG recording files

The script outputs Excel files per center containing:
- Channel labels for diagnosis and follow-up recordings
- Sampling frequencies for diagnosis and follow-up recordings
Each patient's data is stored in a separate sheet.

Output:
    Excel files are automatically created in each center directory.
    No need to pre-create files - they will be generated automatically.

Important:
    1. To be able to run this script, you need to make 4 empty Excel sheets,
    with the following names:
    f'{center_name}_SF_FU'
    f'{center_name}_SF_DX'
    f'{center_name}_channels_DX'
    f'{center_name}_channels_FU'

    so for example for a center with name "10.CHOC" you should have these 4 empty
    Excel sheets ready in the center directory:
    10.CHOC_SF_FU
    10.CHOC_SF_DX
    10.CHOC_channels_DX
    10.CHOC_channels_FU


    2. If you run the script multiple times on the same center, delete the
    existing Excel files first to avoid duplicate sheet errors.

Usage:
    # Process single center
    process_single_center(center_dir="path/to/center/")

    # Process all centers
    process_multiple_centers(root_folder="path/to/root/")
"""

import pyedflib
import pandas as pd
import os
# Requires: openpyxl (used by pandas ExcelWriter)

def extract_metadata_from_edf_folder(folder_path):
    """
    Extract channel labels and sampling frequencies from all EDF files in a folder.

    Args:
        folder_path (str): Path to the folder containing EDF files

    Returns:
        tuple: (signal_labels_df, sampling_frequency_df)
            - signal_labels_df: DataFrame with channel labels from each EDF file
            - sampling_frequency_df: DataFrame with sampling frequencies from each EDF file
            Returns empty DataFrames if folder doesn't exist or contains no valid files
    """
    # Initialize empty DataFrames
    signal_labels_dict = {}
    sampling_frequency_dict = {}

    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found - {folder_path}")
        return pd.DataFrame(), pd.DataFrame()

    # Get all EDF files in the folder
    edf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.edf')]

    if not edf_files:
        print(f"Warning: No EDF files found in {folder_path}")
        return pd.DataFrame(), pd.DataFrame()

    # Process each EDF file

    for edf_filename in edf_files:
        try:
            full_path = os.path.join(folder_path, edf_filename)
            # full_path = folder_path + edf_filename

            # Open and read sampling frequency and channel labels in each EDF file
            with pyedflib.EdfReader(full_path) as edf_reader:
                signal_labels = edf_reader.getSignalLabels()
                sampling_frequencies = edf_reader.getSampleFrequencies()

            # Store data in dictionaries
            signal_labels_dict[edf_filename] = signal_labels
            sampling_frequency_dict[edf_filename] = sampling_frequencies

        except Exception as e:
            print(f"Error reading {edf_filename}: {str(e)}")
            continue

    # Convert dictionaries to DataFrames, using the pd.DataFrame.from_dict,
    # orient='index' and then .transpose, because sometimes, we have various
    # length of channels and just using p.DataFrame will raise an error
    signal_labels_df = pd.DataFrame.from_dict(signal_labels_dict, orient='index').transpose()
    sampling_frequencies_df = pd.DataFrame.from_dict(sampling_frequency_dict, orient='index').transpose()
    return signal_labels_df, sampling_frequencies_df
#


def write_dataframe_to_excel(data_frame, output_dir, excel_filename, sheet_name, mode='a'):
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
        return  # Exit early to avoid writing empty data

    try:
        excel_path = os.path.join(output_dir, excel_filename)
        with pd.ExcelWriter(excel_path, mode=mode, engine='openpyxl') as writer:
            data_frame.to_excel(writer, sheet_name=sheet_name, index=False, na_rep='')

    except Exception as e:
        print(f"Error writing to Excel file {excel_filename}, sheet {sheet_name}: {str(e)}")

# r"c:\ta" -> c:\ta
# "c:\ta" -> c:    a

def process_single_center (center_dir,  diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):

    """
    Process all patients in a single center directory.

    Args:
        center_dir (str): Path to the center directory
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Output Files (saved in center_dir):
        - {center_name}_channels_DX.xlsx: Diagnosis channel labels
        - {center_name}_channels_FU.xlsx: Follow-up channel labels
        - {center_name}_SF_DX.xlsx: Diagnosis sampling frequencies
        - {center_name}_SF_FU.xlsx: Follow-up sampling frequencies
    """

    if not os.path.exists(center_dir):
        raise FileNotFoundError(f"Center directory not found: {center_dir}")

    center_name = os.path.basename(center_dir)
    print(f"Processing Center: {center_name}")

    # Get all patient IDs (subdirectories only, exclude any other file such as excel or .mat files
    patient_ids = [id for id in os.listdir(center_dir) if os.path.isdir(os.path.join(center_dir, id))]
    # patient_ids = os.listdir(center_dir + '/')

    # Process each patient
    for patient_id in patient_ids:
        print(f"    Processing Patient: {patient_id}")

        # Extract metadata from diagnosis folder
        dx_path = os.path.join(center_dir, patient_id, diagnosis_folder_name)
        # dx_path = f'{center_dir}/{patient_ids[j]}/{diagnosis_folder_name}/'
        signal_labels_dx, sampling_freq_dx = extract_metadata_from_edf_folder(dx_path)

        # Extract metadata from follow up folder
        fu_path = os.path.join(center_dir, patient_id, follow_up_folder_name)
        # fu_path = f'{center_dir}/{patient_ids[j]}/{follow_up_folder_name}/'
        signal_labels_fu, sampling_freq_fu = extract_metadata_from_edf_folder(fu_path)

        # Save patient data to Excel (each patient gets own sheet)
        sheet_name = patient_id
        write_dataframe_to_excel(signal_labels_dx, center_dir, f'{center_name}_channels_DX.xlsx', sheet_name, mode='a')
        write_dataframe_to_excel(signal_labels_fu, center_dir, f'{center_name}_channels_FU.xlsx', sheet_name, mode='a')
        write_dataframe_to_excel(sampling_freq_dx, center_dir, f'{center_name}_SF_DX.xlsx', sheet_name, mode='a')
        write_dataframe_to_excel(sampling_freq_fu, center_dir, f'{center_name}_SF_FU.xlsx', sheet_name, mode='a')


def process_multiple_centers(root_folder="Z:/uci_vmostaghimi/testing-root/", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    """
    Process all EEG files across multiple centers and patients, extracting metadata.

    This function:
    1. Iterates through all center directories in the root folder
    2. For each center, processes all patient directories
    3. For each patient, extracts metadata from diagnosis and follow-up EDF files
    4. Saves results to Excel files (one per center and data type)

    Args:
        root_folder (str): Path to root directory containing center folders
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Output Files (per center):
        - {center_name}_channels_DX.xlsx: Diagnosis channel labels
        - {center_name}_channels_FU.xlsx: Follow-up channel labels
        - {center_name}_SF_DX.xlsx: Diagnosis sampling frequencies
        - {center_name}_SF_FU.xlsx: Follow-up sampling frequencies
    """
    # Validate root folder exists
    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Root folder not found: {root_folder}")

    # Get all center directories
    center_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    center_names = [os.path.basename(center_dir) for center_dir in center_directories]
    print(f"Found {len(center_names)} center to process\n")

    # Process each center
    for center_idx, center_dir in enumerate(center_directories):
        center_name = center_names[center_idx]
        process_single_center(center_dir,  diagnosis_folder_name, follow_up_folder_name)
        print(f"  ✓ Completed {center_name}\n")
    print("All centers processed successfully!")

if __name__ == "__main__":
    # CONFIGURATION
    DIAGNOSIS_FOLDER = "diagnosis"
    FOLLOWUP_FOLDER = "follow up"


    # # ------ Option 1: Process ALL Centers ------
    # Uncomment to process multiple centers:
    # ROOT_FOLDER = "Z:/uci_vmostaghimi/testing-root/"
    # process_multiple_centers(
    #     root_folder=ROOT_FOLDER,
    #     diagnosis_folder_name=DIAGNOSIS_FOLDER,
    #     follow_up_folder_name=FOLLOWUP_FOLDER
    # )

    # ------ Option 2: Process SINGLE Center ------
    process_single_center(
        center_dir= r'Z:\uci_vmostaghimi\23.uconn_jmadan_new',
        diagnosis_folder_name=DIAGNOSIS_FOLDER,
        follow_up_folder_name=FOLLOWUP_FOLDER
    )
