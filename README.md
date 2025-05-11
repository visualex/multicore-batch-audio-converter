# AudioBatchConvert

**Fast, recursive, multi-core audio batch converter using FFmpeg and Python.**  
Convert entire folders of audio files into a consistent format using all available CPU cores.

My hardware supports different file formats and backups in WAV were too big so I needed an efficient tool to convert all my samples to other formats. Backups are great in flac. 

---

## Features

* **Multi-core processing** – utilizes all available CPU cores (configurable)
* **Recursive folder traversal** – scans subdirectories for audio files
* **Flexible format support** – input wildcard all formats "*" or match "wav|aiff" and output to one of WAV, FLAC, AIFF, MP3, etc.
* **Preserves directory structure** – mirrors input folder layout in output
* **Error handling** – failed conversions are logged without stopping the process
* **Cross-platform** – works on macOS (tested), Linux (expected), and Windows(🤷)
* **FFmpeg-based** – leverages the power and reliability of FFmpeg (https://ffmpeg.org/)

---

## Requirements

* **bash or comp. shell**
* **FFmpeg** (must be installed and available in your system path, You can check this by running: `ffmpeg -version`)

---

## Installation

Clone this repository and set up a virtual environment:

```bash

git clone https://github.com/yourname/multicore-batch-audio-converter.git
cd multicore-batch-audio-converter

# configure requirements
bash setup_env.sh

```

## Usage

```
venv/bin/python convert.py INPUT_DIR OUTPUT_DIR EXTENSIONS OUTPUT_FORMAT SAMPLE_RATE BIT_DEPTH [--workers N]

Argument | Description
INPUT_DIR | Root folder to search for audio files
OUTPUT_DIR | Destination folder to write converted files (will mirror directory layout)
EXTENSIONS | Pipe-separated list of extensions to match "wav|mp3|aiff" or all "*"
OUTPUT_FORMAT | Choose one output format (e.g. wav, flac, aiff, mp3)
SAMPLE_RATE | Output sample rate (e.g. 44100, 48000,)
BIT_DEPTH | Output bit depth (e.g. 16, 24)
--workers N | (Optional) Number of parallel processes to use (default: all cores)
```


## Example

Convert all .flac and .mp3 files from ~/audio_library to 16-bit 44.1kHz WAV format in ~/converted using 4 cores:

```
venv/bin/python convert.py ~/audio_library ~/converted "flac|mp3" wav 44100 16 --workers 4
```

## License

This project is licensed under the MIT License.

```
    !*⚠️*! FFmpeg is a required external dependency and is licensed separately under LGPL/GPL.
    This project does not bundle FFmpeg — please install it according to your platform.
```

