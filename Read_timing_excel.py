# By Venus
# 2.20.2024
import pandas as pd

# to Run this code fisrt make an excel file and put it in the root folder direcoty and put the name in Output_excel_sheetName


def Process_all_data(root_folder='Z:/uci_vmostaghimi/testing-root/additional EDFs',Input_excel_sheetName='FU_DX_timings.xlsx',
                     Output_excel_sheetName='PatientsEDF_duration_check.xlsx'):
    excel_file_path = f'{root_folder}/{Input_excel_sheetName}'
    excel_data = pd.read_excel(excel_file_path,
                               sheet_name=None)  # it reads it as a Dictionary which sheetnames are keys


    for site_name in excel_data.keys(): #sitenames is the dictationary key
        PatientsID_duration_check = pd.DataFrame()

        if site_name !='Sheet1':
            site_info = excel_data[site_name]
            site_info['PatientID_prefix'] = site_info['PatientID'].astype(str).str[:10]  #astype converts the patientIDs to strings and then .str allows to perform vectorwise operation on the patientID

            # Group by the new column and find the maximum duration within each group
            # PatientsID_duration_check = site_info.groupby('PatientID_prefix')['Duration in seconds'].max().reset_index()# Here we cannot name the column the way we want becase we are resetting the ordere
            test = site_info.groupby('PatientID_prefix')['Duration in seconds'].agg(['max', 'sum']).reset_index()
            PatientsID_duration_check['PatientID'] = test['PatientID_prefix']
            PatientsID_duration_check['Sum_Duration'] = test['sum']
            PatientsID_duration_check['Max_Duration']= test['max']

            PatientsID_duration_check['duration_max_above_120'] = test['max'] > 120

            write_as_excel(PatientsID_duration_check, root_folder, 'PatientsEDF_duration_check.xlsx', site_name, mode='a')
#

def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):
    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)


Process_all_data()

