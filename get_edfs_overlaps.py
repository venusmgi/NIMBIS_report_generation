#Renamed from Repetition_detection_V2.py to get_edfs_overlaps

"""
EEG Overlap Detector
Author: Venus
Date: 2023-09-20
Last Updated: 2025-12-17

Description:
This script detects temporal overlaps between EDF (European Data Format) recordings
within the same folder. Useful for identifying duplicate or concurrent recordings.

Prerequisites:
- An empty Excel file named "overlaps.xlsx" must exist in the root directory
- The script will create sheets for each site containing pairs of overlapping files

Folder Structure:
    testing_root/
    ├── site1/
    │   ├── patient1/
    │   │   ├── diagnosis/
    │   │   └── follow up/
    └── site2/
        └── ...

Output:
    overlaps.xlsx: Excel file with one sheet per site, listing pairs of overlapping EDFs

Requirements:
    pip install pyedflib pandas openpyxl
"""
import pyedflib
import pandas as pd
import os
from datetime import timedelta

"""
0. 1. 2, 3
A, B, C, D

        k   j
A   A   0   0   x
A   B   0   1
A   C   0   2
A   D   0   3

B   A   1   0
B   B   1   1   x
B   C   1   2
b   D   1   3

C   A   2   0
C   B   2   1   
C   C   2   2   x
C   D   2   3

D   A   2   0
D   B   2   1   
D   C   2   2
D   D   2   3   x

"""
def find_overlapping_edfs(folder_path):
    """
    Find all pairs of overlapping EDF files in a folder.

    Compares all pairs of EDF files to detect temporal overlaps in recording times.

    Args:
        folder_path (str): Path to folder containing EDF files

    Returns:
        pd.DataFrame: DataFrame with columns 'EDF1' and 'EDF2' containing
                      pairs of overlapping file names. Returns empty DataFrame
                      if folder doesn't exist or contains no overlaps.
    """
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Warning: Folder not found - {folder_path}")
        return pd.DataFrame(columns=["EDF1", "EDF2"])

    # Get all EDF files
    try:
        edf_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.edf')]
    except Exception as e:
        print(f"Error listing directory {folder_path}: {str(e)}")
        return pd.DataFrame(columns=["EDF1", "EDF2"])

    if not edf_files:
        print(f"Warning: No EDF files found in {folder_path}")
        return pd.DataFrame(columns=["EDF1", "EDF2"])

    overlapping_edfs = pd.DataFrame(columns=["EDF1", "EDF2"])

    # Collect overlapping pairs
    edf1_names = []
    edf2_names = []

    for i, edf_name1 in enumerate(edf_files):

        full_path1 = os.path.join(folder_path, edf_name1)
        for j, edf_name2 in enumerate(edf_files):
            if i >= j:
                continue
            full_path2 = os.path.join(folder_path, edf_name2)
            try:
                overlap = do_edfs_overlap(full_path1, full_path2)
            except Exception as e:
                print(f"    Error comparing {edf_name1} and {edf_name2}: {str(e)}")
                continue

            if overlap == 1:
                edf1_names.append(edf_name1)
                edf2_names.append(edf_name2)
    if edf1_names:
        overlapping_edfs = pd.DataFrame({"EDF1": edf1_names,
                                         "EDF2": edf2_names
                                         })
    return overlapping_edfs


def do_edfs_overlap(full_path_edf1, full_path_edf2):
    """
    Check if two EDF files have overlapping recording times.

    Args:
        full_path_edf1 (str): Full path to first EDF file
        full_path_edf2 (str): Full path to second EDF file

    Returns:
        bool: True if recordings overlap, False otherwise
    """
    # Read timing info from first EDF
    with pyedflib.EdfReader(full_path_edf1) as edf_reader1:
        start_edf1 = edf_reader1.getStartdatetime()
        duration_edf1_seconds = edf_reader1.getFileDuration()

    duration_edf1 = timedelta(seconds=duration_edf1_seconds)
    end_edf1 = start_edf1 + duration_edf1

    # Read timing info from second EDF
    with pyedflib.EdfReader(full_path_edf2) as edf_reader2:
        start_edf2 = edf_reader2.getStartdatetime()
        duration_edf2_seconds = edf_reader2.getFileDuration()

    duration_edf2 = timedelta(seconds=duration_edf2_seconds)
    end_edf2 = start_edf2 + duration_edf2

    # if end1 <= end2 and start2 >=end1:
    # Check for overlap
    # Overlap exists if one starts before the other ends
    # overlap = (start_edf1 <= start_edf2) and (start_edf2 <= end_edf1)
    overlap = (start_edf1 <= end_edf2) and (start_edf2 <= end_edf1)


    return overlap



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
        print(f"  ✓ No overlaps found for {sheet_name}")
        # Still write empty sheet to indicate folder was checked
        data_frame = pd.DataFrame(columns=["EDF1", "EDF2"])
    try:
        excel_path = os.path.join(folder_dir, excel_filename)
        with pd.ExcelWriter(excel_path, mode=mode, engine='openpyxl') as writer:
            data_frame.to_excel(writer, sheet_name=sheet_name, index=False, na_rep='')
    except Exception as e:
        print(f"Error writing to Excel file {excel_filename}, sheet {sheet_name}: {str(e)}")


def process_single_center_overlaps(center_dir, diagnosis_folder_name="diagnosis",
                                   follow_up_folder_name="follow up"):
    """
    Find all overlapping EDF files in a single center.

    Args:
        center_dir (str): Path to the center directory
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")

    Returns:
        pd.DataFrame: Combined overlap information for all patients
    """

    if not os.path.exists(center_dir):
        raise FileNotFoundError(f"Center directory not found: {center_dir}")

    center_name = os.path.basename(center_dir)
    print(f"\nProcessing Center: {center_name}")

    # Get all patient IDs (subdirectories only)
    patient_ids = [id for id in os.scandir(center_dir) if id.is_dir()]

    print(f"  Found {len(patient_ids)} patients")

    all_overlaps = []
    for patient_id in patient_ids:
        dx_path = os.path.join(center_dir, patient_id, diagnosis_folder_name)
        fu_path = os.path.join(center_dir, patient_id, follow_up_folder_name)

        overlaps_dx = find_overlapping_edfs(dx_path)
        overlaps_fu = find_overlapping_edfs(fu_path)

        if not overlaps_dx.empty:
            overlaps_dx.insert(0, 'Patient_ID', patient_id)
            all_overlaps.append(overlaps_dx)

        if not overlaps_fu.empty:
            overlaps_fu.insert(0, 'Patient_ID', patient_id)
            all_overlaps.append(overlaps_fu)

    if all_overlaps:
        combined_overlaps = pd.concat(all_overlaps, ignore_index=True)
        print(f"\n  Found {len(combined_overlaps)} total overlap(s) in {center_name}\n")
        return combined_overlaps
    else:
        print(f"\n  No overlaps found in {center_name}\n")
        return pd.DataFrame(columns=["Patient_ID", "EDF1", "EDF2"])


def process_all_centers_overlaps(root_folder, diagnosis_folder_name="diagnosis",
                                 follow_up_folder_name="follow up",
                                 excel_filename="overlaps.xlsx"):
    """
    Find overlapping EDFs in all centers.

    Args:
        root_folder (str): Path to root directory containing center folders
        diagnosis_folder_name (str): Name of diagnosis subfolder (default: "diagnosis")
        follow_up_folder_name (str): Name of follow-up subfolder (default: "follow up")
        excel_filename (str): Name of output Excel file (default: "overlaps.xlsx")

    Output Files (saved in root_folder):
        overlaps.xlsx: One sheet per center with overlapping EDF pairs
    """

    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Root folder not found: {root_folder}")

    # Get all center directories
    center_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    center_names = [os.path.basename(center_dir) for center_dir in center_directories]

    print(f"Found {len(center_names)} centers to process")

    # Process each center
    for center_idx, center_directory in enumerate(center_directories):
        center_name = center_names[center_idx]
        print(f"Processing Center {center_idx + 1}/{len(center_directories)}: {center_name}")

        center_overlaps = process_single_center_overlaps(
            center_directory,
            diagnosis_folder_name=diagnosis_folder_name,
            follow_up_folder_name=follow_up_folder_name
        )

        # Save to Excel (one sheet per center)
        write_dataframe_to_excel(
            center_overlaps,
            root_folder,
            excel_filename,
            center_name,
            mode='a'
        )


if __name__ == '__main__':
    # ========================================
    # CONFIGURATION
    # ========================================
    DIAGNOSIS_FOLDER = "diagnosis"
    FOLLOWUP_FOLDER = "follow up"
    EXCEL_FILENAME = "overlaps.xlsx"

    # MODE SELECTION
    # ------ Option 1: Process ALL Centers ------
    # Uncomment to process multiple centers:
    # process_all_centers_overlaps(
    #     root_folder="Z:/uci_vmostaghimi/testing-root/",
    #     diagnosis_folder_name=DIAGNOSIS_FOLDER,
    #     follow_up_folder_name=FOLLOWUP_FOLDER,
    #     excel_filename=EXCEL_FILENAME
    # )

    # ------ Option 2: Process SINGLE Center ------

    overlap_df = process_single_center_overlaps(
        center_dir='Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        diagnosis_folder_name=DIAGNOSIS_FOLDER,
        follow_up_folder_name=FOLLOWUP_FOLDER
    )

    write_dataframe_to_excel(
        overlap_df,
        folder_dir='Z:/uci_vmostaghimi/23.uconn_jmadan_new',
        excel_filename=EXCEL_FILENAME,
        sheet_name="23.uconn_jmadan",
        mode='w'
    )