import os
import json
import subprocess
import shutil
from tqdm import tqdm
from file_utils import calculate_file_hash
from common_utils import im_done
import subprocess
import os

def is_pcm_s16le_44100(file_path):
    """Check if the file is already in PCM S16LE format with a sample rate of 44100 Hz."""
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries",
            "stream=codec_name,sample_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        output = subprocess.check_output(command).decode().strip().split('\n')
        codec_name = output[0]
        sample_rate = output[1]

        return codec_name == "pcm_s16le" and sample_rate == "44100"
    except subprocess.CalledProcessError as e:
        tqdm.write(f"Error checking file format: {e}")
        return False

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

    # Hide the console window for the subprocess
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

    process = subprocess.Popen(
        ["ffmpeg", "-y", "-i", input_file, "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2", "-map_metadata", "0", output_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        creationflags=creationflags
    )

    process.wait()

    # Calculate file hash and size
    file_hash = calculate_file_hash(input_file)
    file_size = os.path.getsize(input_file)
    pioneerdj_data[os.path.basename(input_file)] = {"hash": file_hash, "size": file_size}
