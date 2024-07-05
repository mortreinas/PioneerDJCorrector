import os
import shutil
import platform
import subprocess
import psutil
import tempfile
from tqdm import tqdm
import re
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        install_ffmpeg()

def im_done():
    messagebox.showinfo("Done", "The script has ended its job. You can take your Flash Drive. Bye!")

def install_ffmpeg():
    system = platform.system()
    if system == "Windows":
        subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg"])
    elif system == "Linux":
        subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"])
    elif system == "Darwin":
        subprocess.run(["brew", "install", "ffmpeg"])
    else:
        log_message("Unsupported operating system.")

def check_usb_drive():
    partitions = psutil.disk_partitions(all=True)
    usb_drives = [partition.mountpoint for partition in partitions if 'removable' in partition.opts]
    if not usb_drives:
        log_message("No USB drives found.")
        im_done()
        return None
    else:
        usb_drive = usb_drives[0]
        usb_drive_size = shutil.disk_usage(usb_drive)
        log_message(f"USB drive found: {usb_drive} ({usb_drive_size.free / (1024 ** 3):.2f} GB free)")
        return usb_drive

def select_temp_folder():
    try:
        temp_folder = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(__file__)))
        log_message(f"Temporary folder created at: {temp_folder}")
        return temp_folder
    except Exception as e:
        log_message(f"An error occurred while creating the temporary folder: {e}")
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

def convert_audio(input_file, output_folder):
    if shutil.which("ffmpeg") is None:
        log_message("ffmpeg not found. Please ensure it is installed and added to the system PATH.")
        im_done()
        return

    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, os.path.basename(input_file))
    result = subprocess.run(
        ["ffmpeg", "-i", input_file],
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    duration_search = re.search(r"Duration: (\d+):(\d+):(\d+.\d+)", result.stderr)
    if duration_search:
        hours, minutes, seconds = map(float, duration_search.groups())
        total_duration = hours * 3600 + minutes * 60 + seconds
    else:
        total_duration = 0

    with tqdm(total=total_duration, desc="Converting", unit="sec") as pbar:
        process = subprocess.Popen(
            ["ffmpeg", "-y", "-i", input_file, "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", "-map_metadata", "0", output_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        for line in process.stdout:
            time_search = re.search(r"time=(\d+):(\d+):(\d+.\d+)", line)
            if time_search:
                hours, minutes, seconds = map(float, time_search.groups())
                current_time = hours * 3600 + minutes * 60 + seconds
                pbar.update(current_time - pbar.n)

        process.wait()

def process_usb_drive(usb_drive):
    contents_dir = os.path.join(usb_drive, "Contents")
    temp_folder = select_temp_folder()
    if temp_folder is None:
        log_message("Invalid temporary folder.")
        im_done()
        return
    temp_contents_dir = os.path.join(temp_folder, "Contents")
    log_message("Copying 'Contents' directory from USB drive to temporary folder...")
    try:
        if os.path.exists(temp_contents_dir):
            shutil.rmtree(temp_contents_dir)
        smart_copytree(contents_dir, temp_contents_dir)
    except Exception as e:
        log_message(f"An error occurred while copying 'Contents' directory: {e}")
        im_done()
        return
    log_message("Converting audio files...")
    for root, dirs, files in os.walk(temp_contents_dir):
        for file in files:
            if file.lower().endswith((".wav", ".aif", ".flac")):
                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, temp_contents_dir)
                relative_output_folder = os.path.join(usb_drive, "Contents", relative_path)
                convert_audio(input_file, relative_output_folder)
                os.remove(input_file)
    log_message("Conversion completed.")
    shutil.rmtree(temp_folder)
    log_message("Temporary folder deleted.")
    im_done()

def main():
    check_ffmpeg()
    usb_drive = check_usb_drive()
    if usb_drive:
        process_usb_drive(usb_drive)

def log_message(message):
    log_area.insert(tk.END, message + '\n')
    log_area.yview(tk.END)

def start_process():
    threading.Thread(target=main).start()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("USB Audio Converter")

    start_button = tk.Button(root, text="Start", command=start_process)
    start_button.pack(pady=10)

    log_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
    log_area.pack(padx=10, pady=10)

    root.mainloop()
