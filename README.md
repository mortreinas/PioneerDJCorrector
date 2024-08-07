# PioneerDJCorrector Python Script Documentation

## Introduction
The PioneerDJCorrector Python script aims to solve the "E-8305 issue" faced by users of Pioneer DJ equipment. This issue occurs when certain WAV files are not recognized as a supported file format due to conflicts in the WAV header data. The script automates the conversion process, ensuring compatibility with Pioneer DJ gear.

## Installation
1. **FFmpeg Installation**: FFmpeg should be installed and defined as a path variable. If not, the script attempts to install it automatically using system-specific package managers (`winget` for Windows, `apt-get` for Linux, and `brew` for macOS).

2. **Python Environment**: Python is required to run the script. Ensure Python is installed on your system.

3. **Script and FFmpeg Placement**: Place the script (`pioneer_dj_corrector.py`) in any directory. There is no longer a requirement for FFmpeg and the script to be in the same folder.

## Usage
1. **File Organization**: You have a rekordbox analyzed flash drive, and the audio is in the `Contents` folder by default.

2. **Running the Script**: Execute the script using a Python interpreter (`python pioneer_dj_corrector.py`). The script prompts the user to select a USB drive containing audio files for conversion. After conversion, it prompts to delete temporary files.

## Features
1. **WAV Format Conversion**:
   - The script recursively scans the `Contents` directory, identifying audio files in WAV, FLAC, or AIFF format.
   - Converts each audio file to WAV format with specific options (`pcm_s16le`, `44100Hz` sample rate, stereo channels) to ensure Pioneer DJ equipment compatibility.

2. **Temporary Folder Management**:
   - The script creates a temporary folder to perform conversions, ensuring organized and clean execution.

## Requirements
- Python environment.
- FFMPEG installed and defined as a path variable. If not, the script attempts to install it automatically.
- Rekordbox should be shut down while the script is running.
- Ensure there is sufficient space on the device where the script will run.


You can create an executable by running 
`pyinstaller --onefile '.\PioneerDJCorrector_v1.py'`

If you are using built exe, just execute it, and wait for it to finish. thats it.