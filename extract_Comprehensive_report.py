# By Venus
# 2.20.2024
import pandas as pd


# to Run this code fisrt make an excel file and put it in the root folder direcoty and put the name in Output_excel_sheetName
def Process_all_data(root_folder='D:/Users/vmostaghimi_choc/Desktop/site reports/10.CHOC',
                     Input_excel_sheetName='10.CHOC_overall_report_input.xlsx',
                     Output_excel_sheetName='Overal_report.xlsx'):
    excel_file_path = f'{root_folder}/{Input_excel_sheetName}'
    excel_data = pd.read_excel(excel_file_path,
                               sheet_name=None)  # it reads it as a Dictionary which sheetnames are keys
    comprehensive_report = pd.DataFrame(
        columns=['PatientID_DX', 'montage_DX', 'Duration_DX', 'Having_21_channs_DX', 'missing_channs_DX', 'fs_DX_OK',
                 'PatientID_FU', 'montage_FU', 'Duration_FU', 'Having_21_channs_FU', 'missing_channs_FU', 'fs_FU_OK'])

    channel_name_list = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T3', 'T4', 'T5',
                         'T6', 'Fz', 'Cz', 'Pz', 'A1', 'A2']

    montage_check_chann_list = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T3', 'T4',
                                'T5','T6', 'Fz', 'Cz', 'Pz']

    missing_channel_marker = ['***']

    for sheet_name in excel_data.keys():  # sheet is the dictationary key

        if sheet_name == 'EDF Duration':  # duration in per edf
            Total_duration_sheet_info = excel_data[sheet_name]
            Total_duration_sheet_info['PatientID_prefix'] = Total_duration_sheet_info['PatientID'].astype(str).str[
                                                            :13]  # astype converts the patientIDs to strings and then .str allows to perform vectorwise operation on the patientID
            Total_duration_sheet_info['Duration_check'] = (Total_duration_sheet_info['duration_max_above_120']) * 1
            abst = (Total_duration_sheet_info['duration_max_above_120']) * 1
            # Group by the new column and find the maximum duration within each group
            # PatientsID_duration_check = site_info.groupby('PatientID_prefix')['Duration in seconds'].max().reset_index()# Here we cannot name the column the way we want becase we are resetting the ordere
            Patient_Duration_check = Total_duration_sheet_info.groupby('PatientID_prefix')['Duration_check'].agg(
                'min').reset_index()
            # PatientsID_duration_check['PatientID'] = test['PatientID_prefix']
            # PatientsID_duration_check['Sum_Duration'] = test['Duration_check']

        elif sheet_name == 'FU-DX interval':
            FU_DX_interval = excel_data[sheet_name]
            FU_DX_interval = FU_DX_interval.rename(columns={"patientID": "PatientID_prefix"})


        elif sheet_name == 'fs-macthing DX':
            Fs_DX_sheet_info = excel_data[sheet_name]
            fs_Dx_check_all = []
            for k, edfnames in enumerate(Fs_DX_sheet_info['PatientID']):

                percentage_of_error = (Fs_DX_sheet_info.loc[k, 'True fs'] - Fs_DX_sheet_info.loc[k, 'File fs']) / \
                                      Fs_DX_sheet_info.loc[k, 'File fs'] * 100
                if (percentage_of_error <= 1) & (Fs_DX_sheet_info.loc[k, 'File fs'] >= 200):
                    fs_Dx_check = 1
                    fs_Dx_check_all.append(fs_Dx_check)
                else:
                    fs_Dx_check = 0
                    fs_Dx_check_all.append(fs_Dx_check)
            Fs_DX_sheet_info['FS_DX_check'] = fs_Dx_check_all
            Fs_DX_sheet_info['PatientID_prefix'] = Fs_DX_sheet_info['PatientID'].astype(str).str[:13]
            Fs_DX_check = Fs_DX_sheet_info.groupby(by='PatientID_prefix', group_keys=True)['FS_DX_check'].agg(
                'min').reset_index()

        elif sheet_name == 'fs-matching FU':
            Fs_FU_sheet_info = excel_data[sheet_name]
            fs_FU_check_all = []
            for k, edfnames in enumerate(Fs_FU_sheet_info['PatientID']):

                percentage_of_error = (Fs_FU_sheet_info.loc[k, 'True fs'] - Fs_FU_sheet_info.loc[k, 'File fs']) / \
                                      Fs_FU_sheet_info.loc[k, 'File fs'] * 100
                if (percentage_of_error <= 1) & (Fs_FU_sheet_info.loc[k, 'File fs'] >= 200):
                    fs_Fu_check = 1
                    fs_FU_check_all.append(fs_Fu_check)
                else:
                    fs_Fu_check = 0
                    fs_FU_check_all.append(fs_Fu_check)
            Fs_FU_sheet_info['FS_FU_check'] = fs_FU_check_all
            Fs_FU_sheet_info['PatientID_prefix'] = Fs_FU_sheet_info['PatientID'].astype(str).str[:13]
            Fs_FU_check = Fs_FU_sheet_info.groupby(by='PatientID_prefix', group_keys=True)['FS_FU_check'].agg(
                'min').reset_index()


        elif sheet_name == 'Channel Labels':
            Chann_label_sheet_info = excel_data[sheet_name]

            # sheet_info['missingChans'] = sheet_info.apply(lambda row: sheet_info.columns[row.isna()].tolist(), axis=1)
            empty_columns_per_row = []

            for _, row in Chann_label_sheet_info.iterrows():  # itterrows gives label of a dataframe or tuple of label, since I have it saved it as tuple, it gives tuple of labels
                empty_columns = Chann_label_sheet_info.columns[
                    row.isin(missing_channel_marker)].tolist()  # sheet_info.columns gives the name of each column in the first row, now row.isna, defines which columns in that row are empty
                empty_columns_per_row.append(empty_columns)
            Chann_label_sheet_info['missingChans'] = empty_columns_per_row

            essential_channs = []

            for rows in Chann_label_sheet_info['missingChans']:
                if not(rows):
                    essential_channs.append('TRUE')
                else:
                    ChansMissing = pd.DataFrame(rows)
                    mytest = ~ChansMissing.isin(channel_name_list).any().any()
                    essential_channs.append(mytest)

            Chann_label_sheet_info['Having_21_channels'] = ~Chann_label_sheet_info['missingChans'].isin(
                channel_name_list)

            Chann_label_sheet_info['PatientID_prefix'] = Chann_label_sheet_info['identifier'].astype('string').str[:13]
            Missing_channels = Chann_label_sheet_info.groupby(by='PatientID_prefix', group_keys=True)[
                'missingChans'].apply(lambda x: x)  # when you want to group based on just the name, make sure to make the GroupKeys true and do apply (lambda x:x)

            Essential_channs_exist = pd.merge(Chann_label_sheet_info['PatientID_prefix'],
                                              ~Missing_channels.isin(channel_name_list), on='PatientID_prefix')




            montage_check = pd.merge(Chann_label_sheet_info['PatientID_prefix'],
                                     ~Missing_channels.isin(montage_check_chann_list),on='PatientID_prefix')
            montage_check_unique = montage_check.drop_duplicates(subset = ['PatientID_prefix'])
            montage_check_unique = montage_check_unique.rename(columns={"missingChans": "montage_check"})

            Chann_check = pd.merge(Missing_channels, Essential_channs_exist, on='PatientID_prefix', how='outer')
            Chann_check = pd.merge(Chann_check,montage_check_unique,on='PatientID_prefix', how='outer')
            Chann_check_unique = Chann_check.drop_duplicates(subset=['PatientID_prefix'])



    FS_check_new = pd.merge(Fs_FU_check, Fs_DX_check, on='PatientID_prefix', how='outer')

    # Combine '_x' and '_y' columns into a new column 'Info'
    FS_check_new['FS_check'] = FS_check_new['FS_FU_check'].combine_first(FS_check_new['FS_DX_check'])

    # Drop the original '_x' and '_y' columns
    FS_check_new.drop(['FS_FU_check', 'FS_DX_check'], axis=1, inplace=True)


    Merged_info_all = pd.merge(Patient_Duration_check, Chann_check_unique,on='PatientID_prefix').merge(FS_check_new,on='PatientID_prefix')
    Merged_info_all = Merged_info_all.rename(columns ={'PatientID_prefix':'PatientID'})
   # Merged_info_all['Having_21_channels'] = essential_channs

    # Merged_info_FU = pd.merge(Patient_Duration_check, Chann_check_unique, on='PatientID_prefix').merge(Fs_FU_check,
    #                                                                                             on='PatientID_prefix')
    # testing = pd.merge(Merged_info_FU, FU_DX_interval, on='PatientID_prefix')

    # Merged_info_DX = pd.merge(Patient_Duration_check, Chann_check_unique, on='PatientID_prefix').merge(Fs_DX_check,
    #                                                                                             on='PatientID_prefix')

    # comprehensive_report["PatientID_DX"] = Merged_info_DX['PatientID_prefix']
    # comprehensive_report["montage_DX"] = Merged_info_DX['montage_check']
    # comprehensive_report["Duration_DX"] = Merged_info_DX['Duration_check']
    # comprehensive_report["Having_21_channs_DX"] = Merged_info_DX['missingChans_y']
    # comprehensive_report["missing_channs_DX"] = Merged_info_DX['missingChans_x']
    # comprehensive_report["fs_DX_OK"] = Merged_info_DX['FS_DX_check']
    #
    # comprehensive_report["PatientID_FU"] = Merged_info_FU['PatientID_prefix']
    # comprehensive_report["montage_FU"] = Merged_info_FU['montage_check']
    # comprehensive_report["Duration_FU"] = Merged_info_FU['Duration_check']
    # comprehensive_report["Having_21_channs_FU"] = Merged_info_FU['missingChans_y']
    # comprehensive_report["missing_channs_FU"] = Merged_info_FU['missingChans_x']
    # comprehensive_report["fs_FU_OK"] = Merged_info_FU['FS_FU_check']

    # write_as_excel(comprehensive_report, root_folder, 'comprehensive_report.xlsx', 'comprehensive_report', mode='a')
    write_as_excel(Merged_info_all, root_folder, 'comprehensive_report.xlsx', 'comprehensive_report', mode='a')


#

def write_as_excel(data_frame, folder_dir, excel_file_name, sheet_name, mode='a'):
    with pd.ExcelWriter(f"{folder_dir}/{excel_file_name}", mode=mode, engine='openpyxl') as writer:
        data_frame.to_excel(writer, sheet_name=sheet_name, index=False)


Process_all_data()
