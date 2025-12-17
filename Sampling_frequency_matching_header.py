#By Venus 12.11

import pyedflib
import pandas as pd
import numpy as np
import os
import sys
import csv
import openpyxl

# deviding the datapoint numbers in a signal
# by the length of the signal in seconds to find the true samling fre


def Find_true_and_file_Fs (pathEDF):
    FS_macthing_DX = []
    EDF_names = os.listdir(pathEDF)
    if not (pathEDF):
        return FS_macthing_DX
    for k, EDF_name1 in enumerate(EDF_names):
        full_path_EDF1 = pathEDF + EDF_name1
        EDF1 = pyedflib.EdfReader(full_path_EDF1)
        sampling_frequency = EDF1.getSampleFrequencies()[0]
        duration = EDF1.getFileDuration()
        signal = EDF1.readSignal(0, start=0, n=None, digital=True)
        if duration != 0:
            True_Fs = len(signal) / duration
        else:
            True_Fs = 'Nan'
        if True_Fs == sampling_frequency:
            Matching = 1
        else:
            Matching = 0
        FS_macthing_DX.append({"PatientID": EDF_name1,
                                   "File fs": sampling_frequency,
                                    "Tue fs": True_Fs,
                                    "Matching": Matching})
        sampling_frequrncy_matching = pd.DataFrame(FS_macthing_DX)
    return sampling_frequrncy_matching


def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):
    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)

def process_files(root_folder="Z:/uci_vmostaghimi/testing-root/", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    site_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    FS_macthing_DX = pd.DataFrame(columns=["PatientID","File fs", "Tue fs", "Matching"])
    FS_macthing_FU = pd.DataFrame(columns=["PatientID","File fs", "Tue fs", "Matching"])

    for i, site_dir in enumerate(site_directories):
    # for  dir_names in range(1,2):
    #     dir_name= list_subfolders_with_paths[dir_names]
        site_names = os.listdir(root_folder)
        patientIDs = os.listdir(site_dir + '/')
        FS_macthing_DX = pd.DataFrame(columns=["PatientID", "File fs", "True fs", "Matching"])
        FS_macthing_FU = pd.DataFrame(columns=["PatientID", "File fs", "True fs", "Matching"])

        FS_macthing_DX_all = pd.DataFrame(columns=["PatientID", "File fs", "True fs", "Matching"])
        FS_macthing_FU_all = pd.DataFrame(columns=["PatientID", "File fs", "True fs", "Matching"])

        print(site_names[i])
        for j, patientID in enumerate(patientIDs):
            pathDX = f'{site_dir}/{patientIDs[j]}/{diagnosis_folder_name}/'
            FS_macthing_DX = Find_true_and_file_Fs(pathDX)
            FS_macthing_DX_all = pd.concat([FS_macthing_DX, FS_macthing_DX_all], axis=0)

            pathFU = f'{site_dir}/{patientIDs[j]}/{follow_up_folder_name}/'
            FS_macthing_FU = Find_true_and_file_Fs(pathFU)
            FS_macthing_FU_all = pd.concat([FS_macthing_FU, FS_macthing_FU_all], axis=0)

        write_as_excel(FS_macthing_DX_all, root_folder, 'FS_macthing_DX_all.xlsx', site_names[i], mode='a')
        write_as_excel(FS_macthing_FU_all, root_folder, 'FS_macthing_FU_all.xlsx', site_names[i], mode='a')

process_files()


