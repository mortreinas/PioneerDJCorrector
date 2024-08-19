import os
import shutil
from tqdm import tqdm
from usb_utils import check_usb_drive
from file_utils import select_temp_folder, smart_copytree, im_done, calculate_file_hash
from pioneerdj_utils import read_pioneerdj_file, write_pioneerdj_file, is_pcm_s16le_44100, convert_audio  # Import convert_audio

def process_usb_drive(usb_drive):
    contents_dir = os.path.join(usb_drive, "Contents")
    pioneerdj_data = read_pioneerdj_file(usb_drive)

    # First, check files on the USB drive and update pioneerdj.dick directly
    skipped_files = []
    total_files = 0

    tqdm.write("Checking files on USB drive...")

    for root, dirs, files in os.walk(contents_dir):
        for file in files:
            if file.lower().endswith((".wav", ".aif", ".flac")):
                input_file = os.path.join(root, file)
                file_hash = calculate_file_hash(input_file)
                file_size = os.path.getsize(input_file)

                # If the file is already documented and in the correct format, skip it
                if (file in pioneerdj_data and
                        pioneerdj_data[file]["hash"] == file_hash and
                        pioneerdj_data[file]["size"] == file_size):
                    skipped_files.append(file)
                    continue

                # Check if the file is already in the correct format
                if is_pcm_s16le_44100(input_file):
                    tqdm.write(f"Skipping {file} as it is already in PCM S16LE 44100 Hz format.")
                    pioneerdj_data[file] = {"hash": file_hash, "size": file_size}
                    skipped_files.append(file)
                    continue

                total_files += 1  # Increment count for files to be processed

    # Write updated pioneerdj.dick file early to avoid redundant checks next time
    write_pioneerdj_file(usb_drive, pioneerdj_data)

    # Create a temporary folder
    temp_folder = select_temp_folder()
    if temp_folder is None:
        tqdm.write("Invalid temporary folder.")
        im_done()
        return

    # Now, copy only the files that need to be converted
    if total_files > 0:
        temp_contents_dir = os.path.join(temp_folder, "Contents")
        tqdm.write("Copying files to temporary folder...")

        for root, dirs, files in os.walk(contents_dir):
            for file in files:
                if file in skipped_files:
                    continue  # Skip already processed files

                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, contents_dir)
                dest_dir = os.path.join(temp_contents_dir, relative_path)

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)

                shutil.copy2(input_file, os.path.join(dest_dir, file))

    # Prompt user to delete the temporary folder after conversion (if any)
    if total_files > 0:
        convert_and_clean(temp_folder, usb_drive, pioneerdj_data)

    shutil.rmtree(temp_folder)
    tqdm.write("Temporary folder deleted.")
    im_done()

def convert_and_clean(temp_folder, usb_drive, pioneerdj_data):
    temp_contents_dir = os.path.join(temp_folder, "Contents")
    total_files = sum(
        1 for _, _, files in os.walk(temp_contents_dir)
        for file in files if file.lower().endswith((".wav", ".aif", ".flac"))
    )

    with tqdm(total=total_files, desc="Overall progress", unit="file") as overall_pbar:
        for root, dirs, files in os.walk(temp_contents_dir):
            for file in files:
                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, temp_contents_dir)
                relative_output_folder = os.path.join(usb_drive, "Contents", relative_path)

                overall_pbar.set_description(f"Converting {file}")
                convert_audio(input_file, relative_output_folder, pioneerdj_data)
                os.remove(input_file)
                overall_pbar.update(1)

    write_pioneerdj_file(usb_drive, pioneerdj_data)
    tqdm.write("Conversion completed.")
