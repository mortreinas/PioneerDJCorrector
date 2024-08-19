from ffmpeg_utils import check_ffmpeg
from usb_utils import check_usb_drive
from process_usb import process_usb_drive
from gui import PioneerDJCorrectorApp

def main():
    check_ffmpeg()
    usb_drive = check_usb_drive()
    if usb_drive:
        process_usb_drive(usb_drive)

if __name__ == "__main__":
    app = PioneerDJCorrectorApp()
    app.mainloop()