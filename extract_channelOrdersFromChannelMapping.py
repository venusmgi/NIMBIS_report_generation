import sys
import pprint
from typing import Collection, Tuple

# This function removes what "-REF" and "EEG-", from the channel names
def preprocess_channel_names(name: str) -> str:
    name = name.replace("EEG", "")
    name = name.replace("Org", "")
    name = name.replace("Ref", "")
    name = name.replace("CZ", "Cz")
    name = name.replace("FZ", "Fz")
    name = name.replace("PZ", "Pz")
    return name

channel_name_list = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T3', 'T4', 'T5',
                         'T6', 'Fz', 'Cz', 'Pz','A1','A2','Eye1','Eye2','EKG1','EKG2','EMG1','EMG2']
# This function reads the csv files, line by line, and removes the spaces in the channel names and removes the empty cells in the re-ordered channels
def read_information_in_triplets(filename: str) -> dict:
    def _print_records(triplet_info):
        print(f"Dataset:")
        for key, dict_values in triplet_info.items():
            print(f"* {key}")
            for category, channels in dict_values.items():
                print(f"   {category}: {channels}")
    triplet_result = dict()
    with open(filename, "rt") as f:
        line = f.readline() # header, so we can ignore it
        counter = 0
        while line != "":
            line = f.readline()
            if line == "":
                # It reached the end of the file, so exit
                break
                #removing the spaces in the names
            cells = [s.strip() for s in line.split(",")] # TODO: this will break if the name has a comma\
            print(cells)


            # We only update the "key" with original file names
            # (not the reorder or the new)
            if counter % 3 == 0:
                filename_cell = cells[0]
            channels_cell = cells[1:] #rest of the cells are the channel

            channel_order_category: str  #this is just a comment

            #seperating each 3 rows that belong to one edf and making a new dict out of it
            if counter % 3 == 0:
                channel_order_category = "original"
                pass
            elif counter % 3 == 1:
                channel_order_category = "renamed"
                pass
            else:
                channel_order_category = "reordered"
                #removing the empty cells just for the re-ordered channels
                channels_cell = [s for s in channels_cell if len(s) > 0]
                pass

            channels_cell = [preprocess_channel_names(s) for s in channels_cell]
            #setdefault is a function for Dict and returns the value of the item with the specified key and here we defined the key to be the edf file name
            #and then we put the channel order as the value
            triplet_result.setdefault(filename_cell, dict())
            triplet_result[filename_cell][channel_order_category] = channels_cell

            #_print_records(triplet_result)
            counter += 1
    _print_records(triplet_result)
    return triplet_result


#this function finds the longest re-ordered channel, which will be the most complete channel order in each site
def find_global_channel_order(triplet_info: dict) -> Collection[str]:
    max_channels = -1
    global_channel_order = []
    for key, dict_values in triplet_info.items():
        ordered_channels = dict_values["reordered"]
        if len(ordered_channels) > max_channels:
            max_channels = len(ordered_channels)
            global_channel_order = ordered_channels
    return global_channel_order


class RearrangedInfo:
    existing_non_renamed: Collection[str]
    existing_renamed_tuples: Collection[Tuple[str, str]]
    absent: Collection[str]
    unknown: Collection[str]
    file_identifier: str

    def __init__(self, existing_non_renamed, existing_renamed_tuples, absent, unknown, file_identifier):
        self.existing_non_renamed = existing_non_renamed
        self.existing_renamed_tuples = existing_renamed_tuples
        self.absent = absent
        self.unknown = unknown
        self.file_identifier = file_identifier

    def contains(self, channel_name: str, check_original_names: bool) -> bool:

        existing_renamed = [
            original_name if check_original_names else renamed_name
            for original_name, renamed_name in self.existing_renamed_tuples]
        return (
            channel_name in self.existing_non_renamed or
            channel_name in existing_renamed or
            channel_name in self.absent or
            channel_name in self.unknown
        )

    def get_channel_name(self, channel_name: str, check_original_names: bool, return_original_name: bool) -> str:

        exists_in_nonrenamed = (
            channel_name in self.existing_non_renamed or
            #channel_name in self.absent or
            channel_name in self.unknown
        )
        if exists_in_nonrenamed:
            return channel_name
        existing_renamed = [
            original_name if check_original_names else renamed_name
            for original_name, renamed_name in self.existing_renamed_tuples]
        if channel_name in existing_renamed:
            index = existing_renamed.index(channel_name)
            channel_original_name, channel_renamed_name = self.existing_renamed_tuples[index]
            if return_original_name:
                return channel_original_name
            else:
                return channel_renamed_name
        return "***"
def compare_triplets(global_ideal_channel_order: Collection[str], triplet_info: dict) -> Collection[RearrangedInfo]:
    def nonemptyset(data_collection: Collection[str]) -> set:
        return set([c for c in data_collection if c != ""])

    def compare_single_triple(global_channel_set: set, triplet_key: str, triplet_values: dict) -> RearrangedInfo:
        renamed_including_unknown_channels = nonemptyset([
            renamed_name if renamed_name != "" else original_name
            for original_name, renamed_name in zip(triplet_values["original"], triplet_values["renamed"])
        ])
        original_set = nonemptyset(triplet_values["original"])
        renamed_set = nonemptyset(triplet_values["renamed"])
        reordered_set = nonemptyset(triplet_values["reordered"])
        #
        absent_set = global_channel_set.difference(reordered_set)
        unknown_set = renamed_including_unknown_channels.difference(global_channel_set)
        #
        existing_non_renamed_set = original_set.intersection(global_channel_set)
        existing_renamed_set = renamed_set.difference(existing_non_renamed_set)
        existing_renamed_tuples = [
            (renamed_name, original_name)
            for original_name, renamed_name in zip(triplet_values["original"], triplet_values["renamed"])
            if renamed_name in existing_renamed_set
        ]
        return RearrangedInfo(
            existing_non_renamed=list(existing_non_renamed_set),
            existing_renamed_tuples=existing_renamed_tuples,
            absent=list(absent_set),
            unknown=list(unknown_set),
            file_identifier=triplet_key,
        )
    #
    rearranged_info = []
    global_channel_set = set(global_ideal_channel_order)
    for key, triplet_values in triplet_info.items():
        rearranged_item = compare_single_triple(global_channel_set, key, triplet_values)
        rearranged_info.append(rearranged_item)
    return rearranged_info
def get_common_nonrenamed_channels(info_list: Collection[RearrangedInfo]) -> Collection[str]:
    common_nonrenamed_channels = None
    for rearranged_info in info_list:
        if common_nonrenamed_channels is None:
            common_nonrenamed_channels = set(rearranged_info.existing_non_renamed)
        if len(common_nonrenamed_channels.intersection(set(rearranged_info.existing_non_renamed))) < 16:
            print(1)
        common_nonrenamed_channels = common_nonrenamed_channels.intersection(set(rearranged_info.existing_non_renamed))
    return list(common_nonrenamed_channels)


def get_every_possible_channel(info_list: Collection[RearrangedInfo]) -> Collection[str]:
    all_channels = set([])
    for rearranged_info in info_list:
        all_channels = all_channels.union(set(rearranged_info.existing_non_renamed))
        all_channels = all_channels.union(set([renamed_name for renamed_name, original_name in rearranged_info.existing_renamed_tuples]))
        all_channels = all_channels.union(set(rearranged_info.unknown))
    return sorted(list(all_channels))

def export_as_csv(filename: str, rearranged_info_list: Collection[RearrangedInfo], global_ideal_channel_order: Collection[str]):

    def rearranged_info_as_line(rearranged_info: RearrangedInfo, order_for_printing: Collection[str], extra_channels: Collection[str]) -> str:
        items = [rearranged_info.file_identifier]
        for column_channel_name in order_for_printing:
            if rearranged_info.contains(column_channel_name, check_original_names=True):
                channel_name =  rearranged_info.get_channel_name(column_channel_name,
                                                                 check_original_names=True,
                                                                 return_original_name=False)
                items.append(channel_name)
            else:
                items.append("")

        for column_channel_name in extra_channels:
            if rearranged_info.contains(column_channel_name, check_original_names=True):
                channel_name = rearranged_info.get_channel_name(column_channel_name,
                                                                 check_original_names=True,
                                                                 return_original_name=False)
                items.append(channel_name)
        return items

    common_nonrenamed_channels = get_common_nonrenamed_channels(rearranged_info_list)
    renamed_channels_at_least_once = set(global_ideal_channel_order).difference(set(common_nonrenamed_channels))

    every_channel = get_every_possible_channel(rearranged_info_list)

    global_order_for_printing = sorted(list(common_nonrenamed_channels))
    global_order_for_printing = global_order_for_printing + ["-"]
    global_order_for_printing = global_order_for_printing + sorted(list(renamed_channels_at_least_once))
    global_order_for_printing = global_order_for_printing + ["-"]
    global_order_for_printing = global_order_for_printing + sorted(c for c in global_ideal_channel_order if
                                                             c not in global_order_for_printing)
    global_order_for_printing = global_order_for_printing + ["-"]
    global_unknown_channels = sorted(c for c in every_channel if
                                                             c not in global_order_for_printing)

    print(global_order_for_printing)
    print(common_nonrenamed_channels)
    lines = [
        rearranged_info_as_line(rearranged_info, global_order_for_printing, global_unknown_channels)
        for rearranged_info in rearranged_info_list]

    number_extra_columns = max([
        len(line) -  len(global_order_for_printing) - 1
        for line in lines
    ])
    unknown_channels_for_printing = [f"Unknown{k+1}" for k in range(number_extra_columns)]

    entire_file = []
    entire_file.append(
        "identifier,"
        + ",".join(global_order_for_printing)
        + ","
        + ",".join(unknown_channels_for_printing)
        + "\n")

    for line in lines:
        entire_file.append(",".join(line) + "\n")
    #for rearranged_info in rearranged_info_list:
    #    line = rearranged_info_as_line(rearranged_info, global_order_for_printing, global_unknown_channels)
    #    entire_file.append(",".join(line) + "\n")

    with open(filename, "wt") as f:
        f.writelines(entire_file)

def main():
    #input_csv_filename = "Z:/uci_vmostaghimi/to mat edfs/11.bch_ngupta/channel_mapping.csv"
    # input_csv_filename = "Z:/uci_vmostaghimi/to mat edfs/18.cnh_zkramer/channel_mapping.csv"
    # output_csv_filename = "Z:/uci_vmostaghimi/to mat edfs/18.cnh_zkramer/channel_mapping_Site_report.csv"

    input_csv_filename = "Z:/uci_vmostaghimi/23.uconn_jmadan_new/channel_mapping.csv"
    output_csv_filename = "Z:/uci_vmostaghimi/23.uconn_jmadan_new//channel_mapping_Site_report.csv"

    triplets = read_information_in_triplets(input_csv_filename)
    global_ideal_channel_order = find_global_channel_order(triplets)
    print(global_ideal_channel_order)
    # rearranged_info = compare_triplets(global_ideal_channel_order, triplets)
    # export_as_csv(output_csv_filename, rearranged_info, global_ideal_channel_order)

    rearranged_info = compare_triplets(channel_name_list, triplets)
    export_as_csv(output_csv_filename, rearranged_info, channel_name_list)



if __name__ == '__main__':
    main()