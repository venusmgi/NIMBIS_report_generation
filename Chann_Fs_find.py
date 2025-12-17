#By Venus 6.27

import pyedflib
import pandas as pd
import numpy as np
import os
import sys
import csv
import openpyxl

#[signal_labels_DX, sampling_frequency_DX] = function recover_metadata_from_diagnosis_folder(pathDX)


def recover_metadata_from_diagnosis_folder(pathDX):
    signal_labels_DX = pd.DataFrame()
    sampling_frequency_DX = pd.DataFrame()
    if not os.path.exists(pathDX):
        return signal_labels_DX, sampling_frequency_DX
    DX_names = os.listdir(pathDX)
    for k, Dx_name in enumerate(DX_names):
        full_path_DX = pathDX+Dx_name
        fDX = pyedflib.EdfReader(full_path_DX)
        signal_labels = pd.DataFrame(fDX.getSignalLabels())
        sampling_frequency = pd.DataFrame(fDX.getSampleFrequencies())





        #it said instead of insert use pd.concat(index =1).....
        signal_labels_DX.insert(k, Dx_name, signal_labels)
        sampling_frequency_DX.insert(k,Dx_name,sampling_frequency)
    # TODO: Check is a simpler implementation can be made
    # my_data = dict()
    # my_data.setdefault(DX_names[k], list())
    # my_data[DX_names[k]].append(signal_labels)
    # my_data = []
    # my_data.append((DX_names[k], signal_labels))
    return signal_labels_DX, sampling_frequency_DX
#


def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):
    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)

#r"c:\ta" -> c:\ta
# "c:\ta" -> c:    a
def process_files(root_folder="Z:/uci_vmostaghimi/testing-root/", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    site_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]

    for i, site_dir in enumerate(site_directories):
    # for  dir_names in range(1,2):
    #     dir_name= list_subfolders_with_paths[dir_names]
        site_names = os.listdir(root_folder)
        patientIDs = os.listdir(site_dir + '/')
        print(site_names[i])
        for j, patientID in enumerate(patientIDs):
            pathDX = f'{site_dir}/{patientIDs[j]}/{diagnosis_folder_name}/'
            signal_labels_DX, sampling_frequency_DX = recover_metadata_from_diagnosis_folder(pathDX)

            pathFU = f'{site_dir}/{patientIDs[j]}/{follow_up_folder_name}/'
            signal_labels_FU, sampling_frequency_FU = recover_metadata_from_diagnosis_folder(pathFU)

            # Save the iteration's data in a new sheet
            sheet_name = patientIDs[j]
            write_as_excel(signal_labels_DX, site_dir, site_names[i]+'_channels_DX.xlsx', sheet_name, mode='a')
            write_as_excel(signal_labels_FU, site_dir, site_names[i]+'_channels_FU.xlsx', sheet_name, mode='a')
            write_as_excel(sampling_frequency_DX, site_dir, site_names[i]+'_SF_DX.xlsx', sheet_name, mode='a')
            write_as_excel(sampling_frequency_FU, site_dir, site_names[i]+'_SF_FU.xlsx', sheet_name, mode='a')

if __name__ == "__main__":
    # I will avoid global variables:
    process_files(root_folder="Z:/uci_vmostaghimi/testing-root/", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up")
