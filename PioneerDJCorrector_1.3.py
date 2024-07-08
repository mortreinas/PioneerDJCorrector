import os
import shutil
import platform
import subprocess
import psutil
import tempfile
import hashlib
import json
from tqdm import tqdm
import re

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        install_ffmpeg()

def im_done():
    input("The script has ended its job, you can take your FLaShDrivE, press enter to close me :) byeeee...... (any feedback is welcome)")

def install_ffmpeg():
    system = platform.system()
    if system == "Windows":
        subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg"])
    elif system == "Linux":
        subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"])
    elif system == "Darwin":
        subprocess.run(["brew", "install", "ffmpeg"])
    else:
        print("Unsupported operating system.")

def check_usb_drive():
    partitions = psutil.disk_partitions(all=True)
    usb_drives = [partition.mountpoint for partition in partitions if 'removable' in partition.opts]
    if not usb_drives:
        print("No USB drives found.")
        im_done()
        return None
    else:
        usb_drive = usb_drives[0]
        usb_drive_size = shutil.disk_usage(usb_drive)
        print(f"USB drive found: {usb_drive} ({usb_drive_size.free / (1024 ** 3):.2f} GB free)")
        return usb_drive

def select_temp_folder():
    try:
        # Create a temporary folder in the script's directory
        temp_folder = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))
        print("Temporary folder created at:", temp_folder)
        return temp_folder
    except Exception as e:
        print("An error occurred while creating the temporary folder:", e)
        im_done()
        return None

def smart_copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    errors = []
    total_files = sum([len(files) for r, d, files in os.walk(src)])
    with tqdm(total=total_files, desc="Copying files", unit="file") as pbar:
        for root, dirs, files in os.walk(src):
            relative_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dst, relative_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            for file in files:
                s = os.path.join(root, file)
                d = os.path.join(dest_dir, file)
                try:
                    shutil.copy2(s, d)
                    pbar.update(1)
                except Exception as e:
                    errors.append((s, d, e))
    if errors:
        raise Exception(errors)

def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def read_pioneerdj_file(usb_drive):
    pioneerdj_file_path = os.path.join(usb_drive, "pioneerdj.dick")
    if os.path.exists(pioneerdj_file_path):
        with open(pioneerdj_file_path, "r") as f:
            return json.load(f)
    return {}

def write_pioneerdj_file(usb_drive, data):
    pioneerdj_file_path = os.path.join(usb_drive, "pioneerdj.dick")
    with open(pioneerdj_file_path, "w") as f:
        json.dump(data, f, indent=4)

def convert_audio(input_file, output_folder, pioneerdj_data):
    if shutil.which("ffmpeg") is None:
        tqdm.write("ffmpeg not found. Please ensure it is installed and added to the system PATH.")
        im_done()
        return

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Output file will have the same name as the input file
    output_file = os.path.join(output_folder, os.path.basename(input_file))

    process = subprocess.Popen(
        ["ffmpeg", "-y", "-i", input_file, "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", "-map_metadata", "0", output_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    process.wait()

    # Calculate file hash and size
    file_hash = calculate_file_hash(input_file)
    file_size = os.path.getsize(input_file)
    pioneerdj_data[os.path.basename(input_file)] = {"hash": file_hash, "size": file_size}

def process_usb_drive(usb_drive):
    contents_dir = os.path.join(usb_drive, "Contents")
    temp_folder = select_temp_folder()
    if temp_folder is None:
        tqdm.write("Invalid temporary folder.")
        im_done()
        return

    # Check available space on the destination drive
    temp_drive = os.path.splitdrive(temp_folder)[0]
    temp_drive_free_space = shutil.disk_usage(temp_drive).free
    usb_drive_used_space = shutil.disk_usage(usb_drive).used

    if temp_drive_free_space < usb_drive_used_space:
        tqdm.write("Not enough space on the destination drive.")
        im_done()
        return

    temp_contents_dir = os.path.join(temp_folder, "Contents")
    tqdm.write("Copying 'Contents' directory from USB drive to temporary folder...")
    try:
        if os.path.exists(temp_contents_dir):
            shutil.rmtree(temp_contents_dir)  # Remove the directory if it already exists
        smart_copytree(contents_dir, temp_contents_dir)
    except Exception as e:
        tqdm.write(f"An error occurred while copying 'Contents' directory: {e}")
        im_done()
        return

    # Read existing pioneerdj.dick file
    pioneerdj_data = read_pioneerdj_file(usb_drive)

    skipped_files = []

    # Create a new dictionary for the updated data
    updated_pioneerdj_data = {}

    # Calculate total number of audio files to convert
    total_files = sum(
        1 for _, _, files in os.walk(temp_contents_dir)
        for file in files if file.lower().endswith((".wav", ".aif", ".flac"))
        and os.path.basename(file) not in pioneerdj_data
    )

    with tqdm(total=total_files, desc="Overall progress", unit="file") as overall_pbar:
        for root, dirs, files in os.walk(temp_contents_dir):
            for file in files:
                if file.lower().endswith((".wav", ".aif", ".flac")):
                    input_file = os.path.join(root, file)
                    file_hash = calculate_file_hash(input_file)
                    file_size = os.path.getsize(input_file)
                    if os.path.basename(file) in pioneerdj_data and pioneerdj_data[os.path.basename(file)]["hash"] == file_hash and pioneerdj_data[os.path.basename(file)]["size"] == file_size:
                        skipped_files.append(file)
                        # Add skipped file to the updated data
                        updated_pioneerdj_data[os.path.basename(file)] = pioneerdj_data[os.path.basename(file)]
                        continue
                    # Calculate the relative path within the temporary directory
                    relative_path = os.path.relpath(root, temp_contents_dir)
                    # Set the output folder correctly
                    relative_output_folder = os.path.join(usb_drive, "Contents", relative_path)
                    overall_pbar.set_description(f"Converting {file}")
                    convert_audio(input_file, relative_output_folder, updated_pioneerdj_data)
                    os.remove(input_file)
                    overall_pbar.update(1)

    # Write the updated pioneerdj.dick file
    write_pioneerdj_file(usb_drive, updated_pioneerdj_data)

    tqdm.write("Conversion completed.")
    if skipped_files:
        tqdm.write("Skipped files:")
        for skipped_file in skipped_files:
            tqdm.write(skipped_file)

    # Prompt user to delete the temporary folder
    shutil.rmtree(temp_folder)
    tqdm.write("Temporary folder deleted.")
    im_done()

def main():
    check_ffmpeg()
    usb_drive = check_usb_drive()
    if usb_drive:
        process_usb_drive(usb_drive)

if __name__ == "__main__":
    main()
