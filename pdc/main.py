"""Entry point for Pioneer DJ Corrector."""

import sys

from pdc.ffmpeg import ensure_available
from pdc.gui import run_app
from pdc.usb import list_removable_drives


def main() -> None:
    """Run GUI (default) or CLI if --cli and drive selected."""
    ensure_available()

    if "--cli" in sys.argv:
        drives = list_removable_drives()
        if not drives:
            print("No USB drives found.")
            return
        for mountpoint, display in drives:
            print(display)
        mountpoint = drives[0][0]
        if len(drives) > 1:
            choice = input(f"Select drive (1-{len(drives)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(drives):
                mountpoint = drives[int(choice) - 1][0]
        from pdc.cli import prompt_and_exit, run_cli

        run_cli(mountpoint)
        prompt_and_exit()
    else:
        run_app()


if __name__ == "__main__":
    main()
