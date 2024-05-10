import os
import shutil
import platform
import subprocess
import psutil
import tempfile

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        install_ffmpeg()

def im_done():
    input("The script has ended its job, you can take you FLaShDrivE, press enter to close me :) byeeee...... (any feedback is welcome)")

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
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            smart_copytree(s, d, symlinks, ignore)
        else:
            try:
                if not os.path.exists(d):
                    shutil.copy2(s, d)
                else:
                    shutil.copy2(s, d + '_new')
            except Exception as e:
                errors.append((s, d, e))
    if errors:
        raise Exception(errors)

def convert_audio(input_file, output_folder):
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found. Please ensure it is installed and added to the system PATH.")
        im_done()
        return
    
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Output file will have the same name as the input file
    output_file = os.path.join(output_folder, os.path.basename(input_file))

    subprocess.run(["ffmpeg", "-y", "-i", input_file, "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", "-map_metadata", "0", output_file])

def process_usb_drive(usb_drive):
    contents_dir = os.path.join(usb_drive, "Contents")
    temp_folder = select_temp_folder()
    if temp_folder is None:
        print("Invalid temporary folder.")
        im_done()
        return
    
    temp_contents_dir = os.path.join(temp_folder, "Contents")
    
    print("Copying 'Contents' directory from USB drive to temporary folder...")
    try:
        if os.path.exists(temp_contents_dir):
            shutil.rmtree(temp_contents_dir)  # Remove the directory if it already exists
        shutil.copytree(contents_dir, temp_contents_dir)
    except Exception as e:
        print("An error occurred while copying 'Contents' directory:", e)
        im_done()
        return
    
    print("Converting audio files...")
    for root, dirs, files in os.walk(temp_contents_dir):
        for file in files:
            if file.lower().endswith((".wav", ".aif", ".flac")):
                input_file = os.path.join(root, file)
                
                # Calculate the relative path within the temporary directory
                relative_path = os.path.relpath(root, temp_contents_dir)
                
                # Set the output folder correctly
                relative_output_folder = os.path.join(usb_drive, "Contents", relative_path)
                
                convert_audio(input_file, relative_output_folder)
                os.remove(input_file)
    
    print("Conversion completed.")

    # Prompt user to delete the temporary folder
    delete_temp_folder = input("Delete temporary folder? (yes/no): ").strip().lower()
    if delete_temp_folder == "yes":
        shutil.rmtree(temp_folder)
        print("Temporary folder deleted.")
        im_done()
    else:
        print("Temporary folder not deleted.")
        im_done()



def main():
    check_ffmpeg()
    usb_drive = check_usb_drive()
    if usb_drive:
        process_usb_drive(usb_drive)

if __name__ == "__main__":
    main()
