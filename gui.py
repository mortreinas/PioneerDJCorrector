import os
import shutil
import tkinter as tk
from tkinter import ttk
from threading import Thread
import psutil
from usb_utils import check_usb_drive
from file_utils import select_temp_folder, calculate_file_hash, im_done
from pioneerdj_utils import read_pioneerdj_file, write_pioneerdj_file, is_pcm_s16le_44100, convert_audio

class PioneerDJCorrectorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pioneer DJ Corrector")
        self.geometry("400x350")

        self.usb_drive_var = tk.StringVar()
        self.usb_drive_var.set("Select USB Drive")

        # Dropdown for USB drive selection
        self.usb_drive_dropdown = ttk.Combobox(self, textvariable=self.usb_drive_var)
        self.usb_drive_dropdown.pack(pady=20)

        # Convert button
        self.convert_button = tk.Button(self, text="Convert", command=self.convert_files)
        self.convert_button.pack(pady=10)

        # Label to show current operation
        self.operation_label = tk.Label(self, text="")
        self.operation_label.pack(pady=10)

        # Progress bars with labels
        self.copy_progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.copy_progress.pack(pady=10)

        self.convert_progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate")
        self.convert_progress.pack(pady=10)

        # Status label for displaying progress
        self.status_label = tk.Label(self, text="")
        self.status_label.pack(pady=10)

        self.refresh_usb_drives()

    def refresh_usb_drives(self):
        partitions = psutil.disk_partitions(all=True)
        usb_drives = []
        for partition in partitions:
            if 'removable' in partition.opts:
                usb_drive_size = shutil.disk_usage(partition.mountpoint)
                drive_name = partition.device.split("\\")[-1] if os.name == 'nt' else partition.device.split("/")[-1]
                usb_drives.append(f"{drive_name} ({partition.mountpoint}) - {usb_drive_size.free / (1024 ** 3):.2f} GB free")
        if usb_drives:
            self.usb_drive_dropdown['values'] = usb_drives
        else:
            self.usb_drive_dropdown['values'] = []
            self.status_label.config(text="No USB drives found.")

    def convert_files(self):
        usb_drive = self.usb_drive_var.get()
        if not usb_drive or usb_drive == "Select USB Drive":
            self.status_label.config(text="Please select a USB drive.")
            return

        # Extract the actual mount point from the dropdown selection
        usb_drive_path = usb_drive.split('(')[-1].split(')')[0]

        self.run_in_thread(self.convert_files_thread, usb_drive_path)

    def convert_files_thread(self, usb_drive):
        pioneerdj_data = read_pioneerdj_file(usb_drive)
        contents_dir = os.path.join(usb_drive, "Contents")

        temp_folder = select_temp_folder()
        if temp_folder is None:
            self.status_label.config(text="Failed to create a temporary folder.")
            return

        files_to_process = []
        total_files = 0

        self.operation_label.config(text="Analyzing files...")

        for root, dirs, files in os.walk(contents_dir):
            for file in files:
                if file.lower().endswith((".wav", ".aif", ".flac")):
                    input_file = os.path.join(root, file)
                    file_hash = calculate_file_hash(input_file)
                    if file_hash is None:
                        continue  # Skip this file if hash calculation failed

                    file_size = os.path.getsize(input_file)

                    if file in pioneerdj_data:
                        recorded_hash = pioneerdj_data[file]["hash"]
                        recorded_size = pioneerdj_data[file]["size"]
                        if recorded_hash == file_hash and recorded_size == file_size:
                            continue  # Skip this file since it's already processed

                    if not is_pcm_s16le_44100(input_file):
                        files_to_process.append((input_file, file))
                        total_files += 1
                    else:
                        pioneerdj_data[file] = {"hash": file_hash, "size": file_size}  # Record in the .dick file

        write_pioneerdj_file(usb_drive, pioneerdj_data)

        if total_files > 0:
            self.copy_progress['maximum'] = total_files
            temp_contents_dir = os.path.join(temp_folder, "Contents")

            self.operation_label.config(text="Copying files...")

            for input_file, file in files_to_process:
                relative_path = os.path.relpath(os.path.dirname(input_file), contents_dir)
                dest_dir = os.path.join(temp_contents_dir, relative_path)

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)

                shutil.copy2(input_file, os.path.join(dest_dir, file))
                self.copy_progress['value'] += 1
                self.status_label.config(text=f"Copying: {file}")
                self.update_idletasks()

            self.convert_progress['maximum'] = total_files

            self.operation_label.config(text="Converting files...")

            for input_file, file in files_to_process:
                relative_path = os.path.relpath(os.path.dirname(input_file), contents_dir)
                relative_output_folder = os.path.join(usb_drive, "Contents", relative_path)

                self.status_label.config(text=f"Converting: {file}")
                convert_audio(input_file, relative_output_folder, pioneerdj_data)

                # After converting, recalculate the hash and size, then update the .dick file
                converted_hash = calculate_file_hash(os.path.join(relative_output_folder, file))
                if converted_hash is not None:
                    converted_size = os.path.getsize(os.path.join(relative_output_folder, file))
                    pioneerdj_data[file] = {"hash": converted_hash, "size": converted_size}

                self.convert_progress['value'] += 1
                self.update_idletasks()

            # Update the .dick file after all conversions
            write_pioneerdj_file(usb_drive, pioneerdj_data)

        shutil.rmtree(temp_folder)
        self.operation_label.config(text="Conversion complete!")
        self.status_label.config(text="All files processed successfully.")


    def run_in_thread(self, func, *args):
        thread = Thread(target=func, args=args)
        thread.start()

if __name__ == "__main__":
    app = PioneerDJCorrectorApp()
    app.mainloop()
