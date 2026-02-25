"""USB drive detection and listing."""

import os
import shutil

import psutil


def list_removable_drives() -> list[tuple[str, str]]:
    """Return list of (mountpoint, display_string) for removable drives."""
    result = []
    for part in psutil.disk_partitions(all=True):
        if "removable" not in part.opts:
            continue
        try:
            usage = shutil.disk_usage(part.mountpoint)
            free_gb = usage.free / (1024**3)
            drive_name = (
                part.device.split("\\")[-1] if os.name == "nt" else part.device.split("/")[-1]
            )
            display = f"{drive_name} ({part.mountpoint}) - {free_gb:.2f} GB free"
            result.append((part.mountpoint, display))
        except OSError:
            continue
    return result


def get_display_strings() -> list[str]:
    """Return display strings for GUI dropdown."""
    return [display for _, display in list_removable_drives()]


def parse_mountpoint_from_display(display: str) -> str:
    """Extract mountpoint from display string like 'E: (E:\\) - 1.5 GB free'."""
    start = display.find("(") + 1
    end = display.find(")", start)
    return display[start:end] if start > 0 and end > start else ""
