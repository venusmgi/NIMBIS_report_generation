
#By Venus 7.13

import pyedflib
import pandas as pd
import numpy as np
import os
import glob
import datetime
# test = pyedflib.EdfReader('Z:/uci_vmostaghimi/testing-root/18.cnh_zkramer/18-0001 (2017)/diagnosis/18-0001_DX_01.edf')


def Find_start_DateTime (pathEDF):
    EDF_names = os.listdir(pathEDF)
    if not os.path.exists(pathEDF):
        return
    for k,EDF_name in enumerate(EDF_names):
        full_path_EDF = pathEDF + EDF_name
        fEDF = pyedflib.EdfReader(full_path_EDF)
        # Store the datetime in the dictionary with the file name as the key
        # Start_TD_DX[DX_names] = Start_TD
        if (k == 0):
            Start_EDF = fEDF.getStartdatetime()

        else:
            if (Start_EDF == fEDF.getStartdatetime()):
                print('discrepencies in edf', EDF_name)
    return Start_EDF

def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):
    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)
root_folder="Z:/uci_vmostaghimi/testing-root/"
def Get_FU_DX_Interval(root_folder="Z:/uci_vmostaghimi/testing-root/", diagnosis_folder_name = "diagnosis", follow_up_folder_name = "follow up"):
    site_directories = [f.path for f in os.scandir(root_folder) if f.is_dir()]
    FU_DX_intervals = pd.DataFrame(columns=["patientID", "interval"])
    # getStartdatetime(self)

    for i, site_directory in enumerate(site_directories):
        print(i)
        site_names = os.listdir(root_folder)
        patientIDs = []
        #checks that the listed contain of the desired path does not have a .xlsx file
        for f in os.listdir(site_directory + '/'):
            if not (f.endswith('.xlsx')):
                patientIDs.append(f)

        for j,patientID in enumerate(patientIDs):
            pathDX = f'{site_directory}/{patientID}/{diagnosis_folder_name}/'
            pathFU = f'{site_directory}/{patientID}/{follow_up_folder_name}/'

            Start_DX = Find_start_DateTime(pathDX)
            Start_FU= Find_start_DateTime(pathFU)

            interval = Start_FU - Start_DX
            interval_in_S = interval.total_seconds()
            interval_in_hours = float(divmod(interval_in_S, 60*60)[0])
            interval_in_days = float(divmod(interval_in_hours, 24)[0])




            FU_DX_intervals.loc[j] = patientIDs[j], interval_in_days
        df1 = pd.DataFrame(FU_DX_intervals)
        write_as_excel(df1, root_folder, 'FU_DX_intervals.xlsx', site_names[i])


Get_FU_DX_Interval()

root_folder="Z:/uci_vmostaghimi/testing-root/"
diagnosis_folder_name = "diagnosis"
follow_up_folder_name = "follow up"