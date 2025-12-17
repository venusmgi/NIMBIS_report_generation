#By Venus 9.20

# To make this function work you need to have an empty excel file in the root folder, names overlaps
# then it will put the names of two edf files that have overlap in each site, under the site sheet
import pyedflib
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime,timedelta
# import Chann_Fs_find

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
def   Find_Overlapping_EDFs(pathEDF):
    overlapping_EDFS = pd.DataFrame(columns=["EDF1","EDF2"])
    first_edf_name_files = []
    second_edf_name_files = []

    EDF_names = os.listdir(pathEDF)
    # if not (pathEDF):
    #     return overlapping_EDFS
    for k, EDF_name1 in enumerate(EDF_names):
        full_path_EDF1 = pathEDF + EDF_name1
        for j, EDF_name2 in enumerate(EDF_names):
            if k >= j:
                continue
            full_path_EDF2 = pathEDF + EDF_name2
            overlap = DO_EDFs_overlap(full_path_EDF1, full_path_EDF2)
            if overlap == 1:
                first_edf_name_files.append(EDF_name1)
                second_edf_name_files.append(EDF_name2)

                #edf1 = pd.DataFrame({'EDF1': [EDF_name1]})  # Provide an index and column name
                #edf2 = pd.DataFrame({'EDF2': [EDF_name2]})  # Provide an index and column name
                #overlapping_EDFS = pd.concat([edf1, edf2], axis=1)


        #overlapping_EDFS = pd.concat([overlapping_EDFS])
    """
    overlapping_EDFS = pd.DataFrame.from_dict({
        "EDF1": first_edf_name_files,
        "EDF2": second_edf_name_files,
    })
    """
    overlapping_EDFS = pd.DataFrame.from_dict(dict(
        EDF1=first_edf_name_files,
        EDF2=second_edf_name_files,
    ))
    return overlapping_EDFS


def DO_EDFs_overlap(full_pathEDF1, full_pathEDF2):
    EDF1 = pyedflib.EdfReader(full_pathEDF1)
    Start_EDF1 = EDF1.getStartdatetime()
    Duration_EDF1_S = EDF1.getFileDuration()
    Duration_EDF1 = timedelta(seconds=Duration_EDF1_S)
    End_EDF1 = Start_EDF1 + Duration_EDF1

    EDF2 = pyedflib.EdfReader(full_pathEDF2)
    Start_EDF2 = EDF2.getStartdatetime()
    Duration_EDF2_S = EDF2.getFileDuration()
    Duration_EDF2 = timedelta(seconds=Duration_EDF2_S)
    End_EDF2 = Start_EDF2 + Duration_EDF2

    # if end1 <= end2 and start2 >=end1:
    if Start_EDF1 <= Start_EDF2 and Start_EDF2 <= End_EDF1:
        overlap = 1
        # save edf name and add a counter when you call this function
    else:
        overlap = 0

    return overlap



def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):
    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)


def Process_all_data (root_folder="Z:/uci_vmostaghimi/testing-root/", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    Timing_one = pd.DataFrame(columns=["EDF1","EDF2"])

    site_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]

    # for i, site_directory in enumerate(site_directories):
    for i, site_directory in enumerate(site_directories):
        Timing_all = pd.DataFrame(
            columns=["EDF1","EDF2"])

        Timing_one = pd.DataFrame(
            columns=["EDF1","EDF2"])

        print(site_directories[i])
        site_names = os.listdir(root_folder) ###probably need to remove the excel files
        #TODO:
        #make the excluding excels another function
        patientIDs = []
        # checks that the listed contain of the desired path does not have a .xlsx file
        for f in os.listdir(site_directories[i] + '/'):
            if not (f.endswith('.xlsx')):
                patientIDs.append(f)

        for j, patientID in enumerate(patientIDs):
            pathDX = f'{site_directories[i]}/{patientID}/{diagnosis_folder_name}/'
            pathFU = f'{site_directories[i]}/{patientID}/{follow_up_folder_name}/'
            Timing_info_DX = Find_Overlapping_EDFs(pathDX)
            Timing_info_FU = Find_Overlapping_EDFs(pathFU)
            Timing_one = pd.concat([Timing_info_DX, Timing_info_FU], axis=0)
            Timing_all = pd.concat([Timing_one, Timing_all], axis=0)

        write_as_excel(Timing_all, root_folder, 'overlaps.xlsx', site_names[i], mode='a')

Process_all_data ()