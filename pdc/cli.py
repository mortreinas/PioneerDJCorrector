"""CLI entry point for Pioneer DJ Corrector."""

from tqdm import tqdm

from pdc.processor import process


def run_cli(usb_drive: str) -> None:
    """Process USB drive with tqdm progress."""

    def on_status(msg: str) -> None:
        tqdm.write(msg)

    pbar: tqdm | None = None

    def on_progress(phase: str, current: int, total: int, desc: str) -> None:
        nonlocal pbar
        if pbar is None:
            pbar = tqdm(total=total, desc="Processing", unit="file")
        pbar.n = current
        pbar.set_postfix_str(desc[:30] if desc else "")
        pbar.refresh()

    try:
        process(usb_drive, on_status=on_status, on_progress=on_progress)
    finally:
        if pbar is not None:
            pbar.close()


def prompt_and_exit() -> None:
    input("Press Enter to close...")
