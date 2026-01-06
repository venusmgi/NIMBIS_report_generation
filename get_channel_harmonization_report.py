# Renamed the file from extract_channelOrdersFromChannelMapping.py to get_channel_harmonization_report

"""
EEG Channel Mapping Report Generator
Author: Venus
Date: 2024-01-06
Last Updated: 2025-01-06

Description:
This script processes CSV files containing EEG channel mapping information and generates
a comprehensive report showing channel renames, reorders, and consistency across files.

Input CSV Format:
    - Every 3 rows represent one EDF file
    - Row 1: Original channel names
    - Row 2: Renamed channel names
    - Row 3: Reordered channel names

Output:
    - CSV report showing channel consistency across all files
    - Identifies common channels, renamed channels, and unknown channels
"""
import os
import sys
from typing import Collection, Tuple, Dict, List

# Standard EEG channel names (10-20 system + additional channels)
STANDARD_CHANNEL_NAMES = [
    'Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2',
    'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz',
    'A1', 'A2', 'Eye1', 'Eye2', 'EKG1', 'EKG2', 'EMG1', 'EMG2'
]


# This function removes what "-REF" and "EEG-", from the channel names
def preprocess_channel_names(name: str) -> str:
    """
    Standardize channel names by removing common prefixes/suffixes.

    Args:
        name (str): Original channel name

    Returns:
        str: Cleaned channel name

    Example:
        'EEG-Fp1-Ref' -> 'Fp1'
        'EEG-FZ-Org' -> 'Fz'
    """

    # Remove common prefixes and suffixes
    name = name.replace("EEG", "")
    name = name.replace("Org", "")
    name = name.replace("Ref", "")

    # Standardize midline electrode capitalization
    name = name.replace("CZ", "Cz")
    name = name.replace("FZ", "Fz")
    name = name.replace("PZ", "Pz")
    return name.strip()


# This function reads the csv files, line by line, and removes the spaces in the channel names and removes the empty cells in the re-ordered channels
def read_channel_mapping_triplets(filename: str) -> Dict[str, Dict[str, List[str]]]:
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Channel mapping file not found: {filename}")

    def _print_records(triplet_info):
        print(f"Dataset:")
        for key, dict_values in triplet_info.items():
            print(f"* {key}")
            for category, channels in dict_values.items():
                print(f"   {category}: {channels}")

    triplet_result = {}
    try:
        with open(filename, "rt") as f:
            # skip the header line
            header = f.readline()

            counter = 0
            edf_filename = None

            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Parse CSV line (note: this will break if channel names contain commas)
                cells = [s.strip() for s in line.split(",")]  # TODO: this will break if the name has a comma

                # We only update the "key" with original file names
                # First column is the EDF filename (only on original channel rows, not the reorder or the new)
                if counter % 3 == 0:
                    edf_filename = cells[0]

                # Remaining columns are channel names
                channel_names = cells[1:]
                categories: str  # this is just a comment

                # seperating each 3 rows that belong to one edf and making a new dict out of it
                if counter % 3 == 0:
                    categories = "original"
                    pass
                elif counter % 3 == 1:
                    categories = "renamed"
                    pass
                else:  # counter % 3 == 2
                    categories = "reordered"

                    # Remove empty cells for reordered channels only
                    channel_names = [name for name in channel_names if len(name) > 0]
                    pass

                # Preprocess channel names (remove -EEG,...)
                channel_names = [preprocess_channel_names(name) for name in channel_names]

                # setdefault is a function for Dict and returns the value of the item with the specified key
                # and here we defined the key to be the edf file name
                # then we put the channel order as the value
                # Store in result dictionary
                triplet_result.setdefault(edf_filename, {})
                triplet_result[edf_filename][categories] = channel_names
                counter += 1

        for edf_file, categories in triplet_result.items():
            if not all(category in categories for category in ['original', 'renamed', 'reordered']):
                raise ValueError(f"Incomplete triplet for file: {edf_file}")
        _print_records(triplet_result)
    except Exception as e:
        raise ValueError(f"Error reading channel mapping file: {str(e)}")

    return triplet_result


# this function finds the longest re-ordered channel, which will be the most complete channel order in each site
def find_most_complete_channel_order(triplet_info: Dict[str, Dict[str, List[str]]]) -> List[str]:
    """
    Find the most complete (longest) reordered channel list.

    Args:
        triplet_info: Dictionary of channel mapping triplets

    Returns:
        list: The most complete channel order found
    """

    max_channels = -1
    most_complete_order = []

    for edf_file, categories in triplet_info.items():

        # we only look at the reordered channel category because
        # that is the row that has the main channels that we kept
        reordered_channels = categories["reordered"]
        if len(reordered_channels) > max_channels:
            max_channels = len(reordered_channels)
            most_complete_order = reordered_channels
    return most_complete_order


class ChannelMappingInfo:
    """
    Information about channel mapping for a single EDF file.

    Attributes:
        edf_filename: Name of the EDF file
        existing_unchanged: Channels that exist and weren't renamed
        existing_renamed: List of (original_name, renamed_name) tuples
        absent: Channels expected but not present in this file
        unknown: Channels present but not in the standard List
    """
    edf_filename: str
    existing_unchanged: List[str]
    existing_renamed_tuples: List[Tuple[str, str]]
    absent: List[str]
    unknown: List[str]

    def __init__(self, edf_filename, existing_unchanged, existing_renamed_tuples, absent, unknown):
        self.existing_unchanged = existing_unchanged
        self.existing_renamed_tuples = existing_renamed_tuples
        self.absent = absent
        self.unknown = unknown
        self.edf_filename = edf_filename

    def contains(self, channel_name: str, check_original_names: bool) -> bool:
        """Check if a channel name exists in this mapping."""

        existing_renamed = [
            original_name if check_original_names else renamed_name
            for original_name, renamed_name in self.existing_renamed_tuples
        ]
        return (
                channel_name in self.existing_unchanged or
                channel_name in existing_renamed or
                channel_name in self.absent or
                channel_name in self.unknown
        )

    def get_channel_name(self, channel_name: str, check_original_names: bool, return_original_name: bool) -> str:

        """Get the channel name (original or renamed) if it exists."""

        # Check if it's an unchanged channel
        if channel_name in self.existing_unchanged or channel_name in self.unknown:
            return channel_name

        # Check if it's a renamed channel
        renamed_list = [
            original_name if check_original_names else renamed_name
            for original_name, renamed_name in self.existing_renamed_tuples
        ]
        if channel_name in renamed_list:
            index = renamed_list.index(channel_name)
            channel_original_name, channel_renamed_name = self.existing_renamed_tuples[index]
            return channel_original_name if return_original_name else channel_renamed_name

        return "***"


def analyze_channel_mappings(standard_channels: List[str],
                             triplet_info: Dict[str, Dict[str, List[str]]]) -> \
        list[ChannelMappingInfo]:
    """
    Analyze channel mappings for all EDF files.

    Args:
        standard_channels: List of expected standard channel names
        triplet_info: Dictionary of channel mapping triplets

    Returns:
        list: List of ChannelMappingInfo objects, one per EDF file
    """

    def _nonempty_set(data_collection: Collection[str]) -> set:
        """Convert to set, excluding empty strings."""
        return set([c for c in data_collection if c != ""])

    def _analyze_single_file(standard_set: set, triplet_key: str,
                             categories: dict) -> ChannelMappingInfo:
        """Analyze channel mapping for a single EDF file."""

        # Get channel sets
        original_set = _nonempty_set(categories["original"])
        renamed_set = _nonempty_set(categories["renamed"])
        reordered_set = _nonempty_set(categories["reordered"])

        # Channels that were renamed (include unknowns)
        renamed_including_unknown_channels = _nonempty_set([
            renamed_name if renamed_name != "" else original_name
            for original_name, renamed_name in zip(categories["original"], categories["renamed"])
        ])

        # Categorize channels
        absent_set = standard_set.difference(reordered_set)
        unknown_set = renamed_including_unknown_channels.difference(standard_set)

        # Channels that exist and weren't renamed
        existing_unchanged_set = original_set.intersection(standard_set)
        existing_renamed_set = renamed_set.difference(existing_unchanged_set)
        existing_renamed_tuples = [
            (renamed_name, original_name)
            for original_name, renamed_name in zip(categories["original"], categories["renamed"])
            if renamed_name in existing_renamed_set
        ]
        return ChannelMappingInfo(
            edf_filename=triplet_key,
            existing_unchanged=list(existing_unchanged_set),
            existing_renamed_tuples=existing_renamed_tuples,
            absent=list(absent_set),
            unknown=list(unknown_set),

        )

    # Analyze all files
    results = []
    standard_set = set(standard_channels)

    for edf_file, categories in triplet_info.items():
        mapping_info = _analyze_single_file(standard_set, edf_file, categories)
        results.append(mapping_info)
    return results


def get_common_nonrenamed_channels(mapping_info_list: List[ChannelMappingInfo]) -> List[str]:
    """
    Find channels that exist (unchanged) in ALL files.

    Args:
        mapping_info_list: List of ChannelMappingInfo objects

    Returns:
        list: Channel names common to all files
    """
    if not mapping_info_list:
        return []

    common_nonrenamed_channels = set(mapping_info_list[0].existing_unchanged)

    for mapping_info in mapping_info_list[1:]:
        common_nonrenamed_channels = common_nonrenamed_channels.intersection((set(mapping_info.existing_unchanged)))

    return sorted(list(common_nonrenamed_channels))


def get_all_channels(mapping_info_list: List[ChannelMappingInfo]) -> List[str]:
    all_channels = set([])

    for mapping_info in mapping_info_list:
        all_channels = all_channels.union(set(mapping_info.existing_unchanged))
        all_channels = all_channels.union(
            set([renamed_name for renamed_name, original_name in mapping_info.existing_renamed_tuples]))
        all_channels = all_channels.union(set(mapping_info.unknown))
    return sorted(list(all_channels))


def export_as_csv(output_filename: str, mapping_info_list: List[ChannelMappingInfo], standard_channels: List[str]):
    """
    Export channel mapping analysis as CSV report.

    Creates a CSV with columns organized as:
    1. Common channels (present in all files)
    2. Separator (-)
    3. Sometimes-renamed channels
    4. Separator (-)
    5. Sometimes-absent channels
    6. Separator (-)
    7. Unknown channels (not in standard list)

    Args:
        output_filename: Path for output CSV file
        mapping_info_list: List of ChannelMappingInfo objects
        standard_channels: List of standard channel names
    """

    def _mapping_info_to_row(mapping_info: ChannelMappingInfo,
                             column_order: List[str],
                             extra_columns: List[str]) -> List[str]:

        """Convert a single mapping info to CSV row."""
        row = [mapping_info.edf_filename]

        # Add values for standard columns
        for column_channel_name in column_order:
            if mapping_info.contains(column_channel_name, check_original_names=True):
                channel_name = mapping_info.get_channel_name(column_channel_name,
                                                             check_original_names=True,
                                                             return_original_name=False)
                row.append(channel_name)
            else:
                row.append("")

        # Add extra (unknown) channels
        for column_channel_name in extra_columns:
            if mapping_info.contains(column_channel_name, check_original_names=True):
                channel_name = mapping_info.get_channel_name(column_channel_name,
                                                             check_original_names=True,
                                                             return_original_name=False)
                row.append(channel_name)
        return row

    # Analyze channel distribution
    common_nonrenamed_channels = get_common_nonrenamed_channels(mapping_info_list)
    renamed_channels_at_least_once = set(standard_channels).difference(set(common_nonrenamed_channels))

    all_channels = get_all_channels(mapping_info_list)

    # Build column order for output
    column_order = sorted(list(common_nonrenamed_channels))
    column_order = column_order + ["-"]  # Separator
    column_order = column_order + sorted(list(renamed_channels_at_least_once))
    column_order = column_order + ["-"]  # Separator
    column_order = column_order + sorted(c for c in standard_channels if c not in column_order)
    column_order = column_order + ["-"]  # Separator

    # Unknown channels (not in standard list)
    unknown_channels = sorted(c for c in all_channels if c not in column_order)

    # Generate rows
    rows = [
        _mapping_info_to_row(mapping_info, column_order, unknown_channels)
        for mapping_info in mapping_info_list
    ]

    # Determine number of unknown channel columns needed
    max_extra_columns \
        = max([
        len(row) - len(column_order) - 1
        for row in rows
    ])
    unknown_column_headers = [f"Unknown{k + 1}" for k in range(max_extra_columns)]

    try:
        with open(output_filename, "wt", encoding='utf-8') as f:
            # Write header
            header = "identifier," + ",".join(column_order) + ","
            if unknown_column_headers:
                header += ",".join(unknown_column_headers)
            f.write(header + "\n")
            # Write data rows
            for row in rows:
                f.write(",".join(row) + "\n")
    except Exception as e:
        raise IOError(f"Error writing report file: {str(e)}")


def main():
    """
    Main function to process channel mapping CSV and generate report.
    """

    # INPUT_CSV_FILENAME = "Z:/uci_vmostaghimi/to mat edfs/11.bch_ngupta/channel_mapping.csv"
    # INPUT_CSV_FILENAME = "Z:/uci_vmostaghimi/to mat edfs/18.cnh_zkramer/channel_mapping.csv"
    # OUTPUT_CSV_FILENAME = "Z:/uci_vmostaghimi/to mat edfs/18.cnh_zkramer/channel_mapping_Site_report.csv"

    INPUT_CSV_FILENAME = "Z:/uci_vmostaghimi/23.uconn_jmadan_new/channel_mapping.csv"
    OUTPUT_CSV_FILENAME = "Z:/uci_vmostaghimi/23.uconn_jmadan_new/channel_mapping_Site_report.csv"

    # Use standard channel list or auto-detect
    USE_STANDARD_CHANNELS = True

    # Read channel mapping data
    print(f"Reading: {INPUT_CSV_FILENAME}")
    triplet_data = read_channel_mapping_triplets(INPUT_CSV_FILENAME)

    # Determine reference channel list
    if USE_STANDARD_CHANNELS:
        reference_channels = STANDARD_CHANNEL_NAMES
    else:
        reference_channels = find_most_complete_channel_order(triplet_data)
        print(f"Reference channel order:{reference_channels}")
    # Analyze channel mappings
    print(f"\nAnalyzing channel mappings...")
    mapping_analysis = analyze_channel_mappings(reference_channels, triplet_data)

    # Export report
    export_as_csv(OUTPUT_CSV_FILENAME, mapping_analysis, STANDARD_CHANNEL_NAMES)


if __name__ == '__main__':
    main()