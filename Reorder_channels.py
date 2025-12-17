import mne

# Load the EDF file
edf_file_path = 'Z:/uci_vmostaghimi/ach_dsamanta/20-0001 (2017)/diagnosis/20-0001_DX_01_0001.edf'
raw = mne.io.read_raw_edf(edf_file_path, preload=True)

# Define the desired channel order
desired_order = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'Fz', 'Cz', 'Pz']

# Reorder the channels
raw.pick_channels(desired_order)
# Save the reordered data to a new EDF file
reordered_edf_file_path = 'Z:/uci_vmostaghimi/20-0001_DX_01_0001.edf'
raw.save(reordered_edf_file_path, overwrite=True)
#TODO:
#use pyedflib.EdfWriter(file_name, n_channels, file_type=1)[source] to write edf


