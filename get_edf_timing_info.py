
#By Venus 7.13

# This script processes EDF (European Data Format) files by reading their headers to extract timing information.
# The directory structure is organized as follows:
# - A main folder contains subfolders for each site.
# - Each site folder contains subfolders for each patient.
# - Each patient folder includes a "diagnosis" folder and a "follow up" folder, both containing EDF files.

# The script reads the EDF headers to obtain the start time, end time, and duration of each EDF file.
# It flags files with a duration shorter than 2 minutes.

# Prerequisites:
# - An Excel file named "FU_DX_timings.xlsx" must exist in the root directory.
# - The script saves the extracted information for each site in a separate sheet within this Excel file.
# - Each sheet is named after the corresponding site, and the EDF information is organized by EDF file name.

# Folder Structure:
# testing_root/
# ├── site1/
# │   ├── patient1/
# │   │   ├── diagnosis/
# │   │   └── follow up/
# │   └── patient2/
# │       ├── diagnosis/
# │       └── follow up/
# └── site2/
#     ├── patient1/
#     │   ├── diagnosis/
#     │   └── follow up/
import pyedflib
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
# import Chann_Fs_find

def   Find_duration_end_start(path_edf):
    """
        Reads EDF headers and collects timing information.

        Parameters:
            path_edf (str): Path to the EDF files.

        Returns:
            pd.DataFrame: DataFrame containing timing information of EDF files.
        """
    
    timing_info_edf = []
    edf_names = os.listdir(path_edf)
    if not (path_edf):
        return timing_info_edf 

    for k, edf_name in enumerate(edf_names):
        full_path_edf = path_edf + edf_name
        my_edf = pyedflib.EdfReader(full_path_edf)
        start_edf = my_edf.getStartdatetime()
        duration_seconds = my_edf.getFileDuration()
        duration = timedelta(seconds=duration_seconds)
        end_edf = start_edf + duration
        my_edf.close()

        # Overlap = any(element == 1 for element in overlap_list)
        flag = 1 if duration_seconds < 120 else 0
        timing_info_edf .append({"PatientID": edf_name,
                                 "Start DateTime": start_edf,
                                 "Finish DateTime": end_edf,
                                 "Duration in seconds": duration_seconds,
                                  # "Overlap": Overlap,
                                 "Duration < 120 s": flag})
        # writing into df
    timing_info_edf = pd.DataFrame(timing_info_edf)
    return timing_info_edf 

# To Do:
# write a fucntion that takes two efs and returns their interval differences in days, hours, and mitunes all ogether

# also, write another fucntion that checks if the edf within one folder has changed the name, and if so,
# check the interval and the lenght of edf and see if they match
# def do_ranges_overlap( start1,end1, start2,end2):
#
#     #if end1 <= end2 and start2 >=end1:
#     if start1 <= start2 and start2 <= end1:
#         overlap =1
#         # save edf name and add a counter when you call this function
#     else:
#         overlap = 0
#
#     return  overlap

def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):

    """
    Writes a DataFrame to an Excel file.

    Parameters:
        data_frame (pd.DataFrame): The DataFrame to write.
        folder_dir (str): The directory to save the Excel file.
        excel_file_name (str): The name of the Excel file.
        sheet_name (str): The name of the sheet in the Excel file.
    """

    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)



def Process_all_data (root_folder="Z:/uci_vmostaghimi/testing-root", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    """
    Processes all EDF files in the specified directory structure and writes timing information to an Excel file.

    Parameters:
        root_folder (str): The root directory containing site folders.
        diagnosis_folder_name (str): The name of the diagnosis folder.
        follow_up_folder_name (str): The name of the follow-up folder.
    """

    timing_one = pd.DataFrame(columns=["patientID", "Start DateTime", "Finish DateTime","Duration in seconds","Short Duration"])

    site_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]

    # for i, site_directory in enumerate(site_directories):
    for i, site_directory in enumerate(site_directories):
        timing_all = pd.DataFrame(
            columns=["PatientID", "Start DateTime", "Finish DateTime", "Duration in seconds","Duration < 120 s"])

        timing_one = pd.DataFrame(
            columns=["PatientID", "Start DateTime", "Finish DateTime", "Duration in seconds","Duration < 120 s"])

        print(site_directories[i])
        site_names = os.listdir(root_folder) ###probably need to remove the excel files

        #TO DO
        #make the excluding excels another function
        patientIDs = []
        # checks that the listed contain of the desired path does not have a .xlsx file
        for f in os.listdir(site_directories[i] + '/'):
            if not (f.endswith('.xlsx')):
                patientIDs.append(f)

        for j, patientID in enumerate(patientIDs):
            path_dx = f'{site_directories[i]}/{patientID}/{diagnosis_folder_name}/'
            path_fu = f'{site_directories[i]}/{patientID}/{follow_up_folder_name}/'
            timing_info_DX = Find_duration_end_start(path_dx)
            timing_info_FU = Find_duration_end_start(path_fu)
            timing_one = pd.concat([timing_info_DX, timing_info_FU], axis=0)
            timing_all = pd.concat([timing_one, timing_all], axis=0)

        write_as_excel(timing_all, root_folder, 'FU_DX_timings.xlsx', site_names[i], mode='a')


Process_all_data()

