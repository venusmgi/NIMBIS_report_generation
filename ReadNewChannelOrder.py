#By Venus 2.12.2024

import pandas as pd
import numpy as np
from io import StringIO
from itertools import chain

file_path = 'Z:/uci_vmostaghimi/to mat edfs/11.bch_ngupta/channel_mapping.csv'
df = pd.read_csv(file_path)
# any(pd.DataFrame(df).isin(1).all(axis=1))

# Create a list to store non-duplicated rows
reordered_channels = []

# Iterate over every third row in the original DataFrame
# df.iloc[2::3].iterrows() selects every third row starting from the third row of df

for index, row in df.iloc[2::3].iterrows():
    reordered_channels.append(row.tolist())  #tolist() converts pd to list
#
all_reordered_channels = pd.DataFrame(reordered_channels, columns=df.columns)

#finding the indecies the edf file names that are duplicated and
# just keeping the last duplication
duplicated_edfs_idx =all_reordered_channels['chanInfo1'].duplicated(keep='last')
reordered_edf_idx_repeated = all_reordered_channels.loc[duplicated_edfs_idx].index


#making a list of the row indecies edfnames that are duplicated and the next two rows
idx_tobe_deleted_from_csv = []
for i,idx in enumerate(reordered_edf_idx_repeated):
    current_idx =list(range(idx, idx + 3))
    idx_tobe_deleted_from_csv.append(current_idx)

flatten_idx_tobe_deleted_from_csv = list(chain.from_iterable(idx_tobe_deleted_from_csv))

#removing the 3 rows that are related to the repeaded edfs
df_cleaned = df.drop(flatten_idx_tobe_deleted_from_csv)

#just keeping the new order of the edf channels
df_cleaned_newchanorder = df_cleaned.iloc[2::3,:]

grouped_counts = df_cleaned.groupby(df_cleaned_newchanorder.iloc[:, 1:].apply(tuple, axis=1)).size()


# Filter groups where there are more than one EDF with the same channel order
duplicated_channel_orders = grouped_counts[grouped_counts > 1]

# Get the corresponding EDFs
duplicated_edfs = df_cleaned[df_cleaned.iloc[:, 1:].apply(tuple, axis=1).isin(duplicated_channel_orders.index)]

duplicated_edfs2 = df_cleaned[df_cleaned.iloc[:, 1:].apply(tuple, axis=1).isin(grouped_counts.index)]

