import psutil
import shutil
from common_utils import im_done

def check_usb_drive():
    partitions = psutil.disk_partitions(all=True)
    usb_drives = [partition.mountpoint for partition in partitions if 'removable' in partition.opts]
    if not usb_drives:
        print("No USB drives found.")
        im_done()
        return []
    else:
        for usb_drive in usb_drives:
            usb_drive_size = shutil.disk_usage(usb_drive)
            print(f"USB drive found: {usb_drive} ({usb_drive_size.free / (1024 ** 3):.2f} GB free)")
        return usb_drives
