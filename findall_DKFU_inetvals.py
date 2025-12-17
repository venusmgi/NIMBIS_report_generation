
#By Venus 7.13

import pyedflib
import pandas as pd
import numpy as np
import os
import glob
import datetime

import re
# test = pyedflib.EdfReader('Z:/uci_vmostaghimi/testing-root/18.cnh_zkramer/18-0001 (2017)/diagnosis/18-0001_DX_01.edf')






def Find_FU_DX_intervals (pathDX,pathFU):

    DX_EDF_names = os.listdir(pathDX)
    FU_EDF_names = os.listdir(pathFU)
    EDF_intervals = []
    if not os.path.exists(pathDX):
        return
    if not os.path.exists(pathFU):
        return
    for k,DX_name in enumerate(DX_EDF_names):
        full_path_DX = pathDX + DX_name
        DXEDF = pyedflib.EdfReader(full_path_DX)
        DX_start = DXEDF.getStartdatetime()
        DXEDF.close()
        for j, FU_name in enumerate(FU_EDF_names):
            full_pahth_FU = pathFU + FU_name
            FUEDF = pyedflib.EdfReader(full_pahth_FU)
            FU_start = FUEDF.getStartdatetime()
            interval = FU_start - DX_start
            interval_in_S = interval.total_seconds()
            interval_in_hours = float(divmod(interval_in_S, 60 * 60)[0])
            interval_in_days = float(divmod(interval_in_hours, 24)[0])
            FUEDF.close()

            EDF_intervals.append({"diagnosis EDF": DX_name,
                              "follow up EDF": FU_name,
                              "interval in days":interval_in_days})


        # Store the datetime in the dictionary with the file name as the key
        # Start_TD_DX[DX_names] = Start_TD




    return EDF_intervals

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

        FU_DX_intervals_all = pd.DataFrame(columns = ["diagnosis EDF","follow up EDF","interval in days"])
        for j,patientID in enumerate(patientIDs):
            pathDX = f'{site_directory}/{patientID}/{diagnosis_folder_name}/'
            pathFU = f'{site_directory}/{patientID}/{follow_up_folder_name}/'
            FU_DX_intervals = pd.DataFrame(Find_FU_DX_intervals(pathDX,pathFU))
            FU_DX_intervals_all = pd.concat([FU_DX_intervals_all, FU_DX_intervals], ignore_index=True)

        #now I want to summerize my info
        DX_EDFS = FU_DX_intervals_all.loc[:, 'diagnosis EDF']
        FU_EDFS = FU_DX_intervals_all.loc[:, 'follow up EDF']
        df2 = pd.DataFrame(FU_DX_intervals_all)
        #edf_name_pattern = r"(\d+)-(\d+)_(DX|FU)_(\d+)_?(\d*)\.edf"

        lst_edfnames = []
        # Create keys based on the DX and FU columns
        DX_regex  = df2['diagnosis EDF'].apply(extract_key)

        DX_regex_useful = DX_regex.apply(remove_dx) # removing "DX" from the regex
        df2['DX_key'] = DX_regex_useful
        FU_regex = df2['follow up EDF'].apply(extract_key)
        FU_regex_useful = FU_regex.apply(remove_fu)
        df2['FU_key'] = FU_regex_useful

        # Ensure that keys match
        # assert df2['DX_key'].equals(df2['FU_key']), "Mismatch between DX and FU keys"

        # Group by the extracted key and get the maximum interval
        aggregated_df = df2.groupby(['DX_key', 'FU_key'], as_index=False).agg(max_interval_in_days=('interval in days', 'max'))
        aggregated_df['DX EDF'] = aggregated_df['DX_key'].apply(lambda key: f"{key[0]}-{key[1]}_DX_{key[2]}.edf" if key else "No key")
        aggregated_df['FU EDF'] = aggregated_df['FU_key'].apply(lambda key: f"{key[0]}-{key[1]}_FU_{key[2]}.edf" if key else "No key")

        filtered_df = df2.loc[df2.groupby(['DX_key', 'FU_key'])['interval in days'].idxmax()]

        # Drop the helper columns
        df2.drop(columns=['DX_key', 'FU_key'], inplace=True)
        aggregated_df.drop(columns=['DX_key', 'FU_key'], inplace=True)



        df1 = pd.DataFrame(FU_DX_intervals_all)
        # df2 = pd.DataFrame(summerized_FU_DX_intervals_all)
        write_as_excel(df1, root_folder, 'all_FU_DX_intervals.xlsx', site_names[i])
        write_as_excel(aggregated_df, root_folder, 'summerized_all_FU_DX_intervals1.xlsx', site_names[i])
        write_as_excel(df2, root_folder, 'summerized_all_FU_DX_intervals2.xlsx', site_names[i])

# Define the regex pattern

def extract_key(edf_filename):
    edf_name_pattern = re.compile(r"(\d+)-(\d+)_(DX|FU)_(\d+)")
    match = edf_name_pattern.match(edf_filename)
    if match:
        return match.groups() #groups are like this 1: site_id, 2:patient_id, 3:recording_phase, 4:file_number, 5:clip_number
    else:
        return None
def remove_dx(tup):
    if not tup:
        return tuple()
    return tuple(x for x in tup if x != 'DX')

def remove_fu(tup):
    if not tup:
        return tuple()
    return tuple( x for x in tup if x != 'FU')
def make_dx(tup):
    return tuple(x for x in tup if x != 'DX')


Get_FU_DX_Interval()
