
#By Venus 7.13

import pyedflib
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime,timedelta


##### write a fucntion that takes two efs and returns their interval differences in days, hours, and mitunes all ogether


##also, write another fucntion that checks if the edf within one folder has changed the name, and if so, check the interval and the lenght of edf and see if they match
def do_ranges_overlap( end1, start2):
    return  start2 <= end1


list_subfolders_with_paths = [f.path for f in os.scandir("Z:/uci_vmostaghimi/") if f.is_dir()]

Timing_all = pd.DataFrame(columns=["patientID", "Start DateTime","Finish DateTime","Overlap"])
Timing_one = pd.DataFrame(columns=["patientID", "Start DateTime","Finish DateTime","Overlap"])
# getStartdatetime(self)

for i in range(0,2):
    print(i)
    sheetnames = os.listdir("Z:/uci_vmostaghimi/")
    path1 = list_subfolders_with_paths[i]
    patinetID = []
    #checks that the listed contain of the desired path does not have a .xlsx file
    for f in os.listdir(path1 + '/'):
        if not (f.endswith('.xlsx')):
            patinetID.append(f)
    #loop through diagnosis and follow-up folder of each site
    for j in range(0, len(patinetID)):
        pathDX = path1 + '/' + patinetID[j] + '/diagnosis/'
        pathFU = path1 + '/' + patinetID[j] + '/follow up/'
        Timing_info_FU = []
        Timing_info_DX = []

        if bool(pathDX):
            DX_names = os.listdir(pathDX)
            FU_names = os.listdir(pathFU)
            # Start_TD_DX = {}
            # Start_TD_FU = {}
            # interval_in_minutes_F = np.full((1,len(DX_names)),np.nan)
            # Initialize a list to store results

            for k in range(0, len(DX_names)):
                full_path_DX = pathDX + DX_names[k]
                fDX = pyedflib.EdfReader(full_path_DX)
                if (k == 0):
                    previous_Finish_DX = datetime.now()
                    Start_DX = fDX.getStartdatetime()
                    Duration_DX_S = fDX.getFileDuration()
                    Duration_DX= timedelta (seconds = Duration_DX_S)
                    Finish_DX = Start_DX + Duration_DX
                else:
                    previous_Finish_DX= Finish_DX
                    Start_DX = fDX.getStartdatetime()
                    Duration_DX_S = fDX.getFileDuration()
                    Duration_DX= timedelta (seconds = Duration_DX_S)
                    Finish_DX = Start_DX + Duration_DX

                overlap=do_ranges_overlap(previous_Finish_DX,Start_DX)
                if (overlap):
                    flag = 1
                else:
                    flag = 0
                Timing_info_DX.append({"PatientID": DX_names[k],
                                       "Start DateTime": Start_DX,
                                       "Finish DateTime": Finish_DX,
                                       "Overlap":flag})
            #writing into df
            Timing_info_DX = pd.DataFrame(Timing_info_DX)
        if bool(pathFU):

            for k in range(0, len(FU_names)):
                full_path_FU = pathFU + FU_names[k]
                fFU = pyedflib.EdfReader(full_path_FU)

                if (k==0):
                    previous_Finish_FU =datetime.now()
                    Start_FU = fFU.getStartdatetime()
                    Duration_FU_S = fFU.getFileDuration()  # this gives the duration in seconds
                    Duration_FU = timedelta(seconds=Duration_FU_S)
                    Finish_FU = Start_FU + Duration_FU

                else:
                    previous_Finish_FU =  Finish_FU
                    Start_FU = fFU.getStartdatetime()
                    Duration_FU_S = fFU.getFileDuration() #this gives the duration in seconds
                    Duration_FU = timedelta(seconds = Duration_FU_S)
                    Finish_FU = Start_FU + Duration_FU

                    overlap=do_ranges_overlap(previous_Finish_FU,Start_FU)
                if (overlap):
                    flag = 1
                else:
                    flag = 0

                Timing_info_FU.append({"PatientID":FU_names[k],
                "Start DateTime": Start_FU,
                "Finish DateTime": Finish_FU,
                "Overlap":flag})
            # writing into df
            Timing_info_FU = pd.DataFrame(Timing_info_FU)

            Timing_one = pd.concat([Timing_info_DX, Timing_info_FU], axis=0)

        Timing_all =pd.concat([Timing_one,Timing_all], axis =0)

        df1 = pd.DataFrame(Timing_all)
        df1.append(Timing_all)

    with pd.ExcelWriter("Z:/uci_vmostaghimi/FU_DX_timings.xlsx",
                        mode='a', engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name=sheetnames[i], index=False)


