import os
import sys
import argparse
import multiprocessing
from pathlib import Path
from functools import partial
import subprocess
from tqdm import tqdm


def valid_exts(ext_str):
    if ext_str == '*':
        return None
    return [e.lower() for e in ext_str.split('|')]


def get_all_audio_files(input_dir, exts):
    input_dir = Path(input_dir)
    if exts is None:
        return [f for f in input_dir.rglob('*') if f.is_file()]
    return [f for f in input_dir.rglob('*') if f.suffix[1:].lower() in exts]

def convert_file(file_path, input_dir, output_dir, output_format, sample_rate, bit_depth):
    try:
        rel_path = file_path.relative_to(input_dir)
        output_file = output_dir / rel_path.with_suffix(f'.{output_format}')
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Handle bit depth correctly based on format
        bit_depth_args = []
        if output_format in ['wav', 'aiff', 'flac']:
            if bit_depth == '16':
                bit_depth_args = ["-sample_fmt", "s16"]
            elif bit_depth == '24':
                bit_depth_args = ["-sample_fmt", "s32", "-bits_per_raw_sample", "24"]
            elif bit_depth == '32':
                bit_depth_args = ["-sample_fmt", "s32"]
        elif output_format == 'mp3':
            # For MP3, use -b:a for bitrate instead
            bitrate = int(bit_depth) * 8
            bit_depth_args = ["-b:a", f"{bitrate}k"]
        else:
            # For other formats, use quality settings
            bit_depth_args = ["-q:a", "0"]

        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(file_path),
            "-ar", str(sample_rate),
        ]
        cmd.extend(bit_depth_args)
        cmd.extend([
            "-f", output_format,
            str(output_file)
        ])

        subprocess.run(cmd, check=True)
        return True, str(file_path)
    except subprocess.CalledProcessError as e:
        return False, f"{file_path}: ffmpeg failed\n{e}"
    except Exception as e:
        return False, f"{file_path}: {e}"

# keep for doc
# audioop is deprecated https://docs.python.org/3/library/audioop.html
# def convert_file(file_path, input_dir, output_dir, output_format, sample_rate, bit_depth):
#     try:
#         rel_path = file_path.relative_to(input_dir)
#         output_file = output_dir / rel_path.with_suffix(f'.{output_format}')
#         output_file.parent.mkdir(parents=True, exist_ok=True)

#         audio = AudioSegment.from_file(file_path)
#         audio = audio.set_frame_rate(int(sample_rate)).set_sample_width(int(int(bit_depth) / 8))

#         audio.export(output_file, format=output_format)
#         return True, str(file_path)
#     except Exception as e:
#         return False, f"{file_path}: {e}"


def parse_args():
    parser = argparse.ArgumentParser(description="Convert audio files recursively.")
    parser.add_argument('input_dir', help='Input folder', nargs='?')
    parser.add_argument('output_dir', help='Output folder', nargs='?')
    parser.add_argument('exts', help='Extension filter, e.g., wav|mp3|flac or *', nargs='?')
    parser.add_argument('format', help='Output format (e.g., wav, mp3, flac, aiff)', nargs='?')
    parser.add_argument('rate', help='Sample rate (e.g., 44100)', nargs='?')
    parser.add_argument('bit_depth', help='Bit depth (e.g., 16, 24)', nargs='?')
    parser.add_argument('--workers', type=int, default=multiprocessing.cpu_count(), help='Number of CPU cores to use')
    parser.add_argument('--gui', action='store_true', help='Launch the graphical user interface')
    return parser.parse_args()


def main():
    args = parse_args()

    # Launch GUI if requested or no arguments provided
    if args.gui or len(sys.argv) == 1:
        try:
            from gui import main as gui_main
            gui_main()
            return
        except ImportError:
            print("GUI dependencies not installed. Please install PyQt6 to use the GUI.")
            sys.exit(1)

    # Check if all required arguments are provided
    if not all([args.input_dir, args.output_dir, args.exts, args.format, args.rate, args.bit_depth]):
        print("Error: Missing required arguments for CLI mode.")
        print("Usage: convert.py INPUT_DIR OUTPUT_DIR EXTENSIONS OUTPUT_FORMAT SAMPLE_RATE BIT_DEPTH [--workers N]")
        print("       convert.py --gui  # Launch GUI mode")
        sys.exit(1)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory {input_dir} does not exist or is not a directory.")
        sys.exit(1)

    if output_dir.exists() and not os.listdir(output_dir):
        print(f"Output directory {output_dir} already exists but is empty. Continuing...")
    elif output_dir.exists():
        print(f"Warning: Output directory {output_dir} already exists and is not empty.")
        response = input("Continue anyway? Files may be overwritten. (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    else:
        output_dir.mkdir(parents=True)

    exts = valid_exts(args.exts)
    files = get_all_audio_files(input_dir, exts)

    if not files:
        print("No audio files found.")
        return

    convert_fn = partial(
        convert_file,
        input_dir=input_dir,
        output_dir=output_dir,
        output_format=args.format,
        sample_rate=args.rate,
        bit_depth=args.bit_depth
    )

    print(f"Processing {len(files)} files using {args.workers} workers...")

    with multiprocessing.Pool(processes=args.workers) as pool:
        for success, result in tqdm(pool.imap_unordered(convert_fn, files), total=len(files)):
            if not success:
                print(f"❌ Error: {result}")

    print("✅ Done.")


if __name__ == '__main__':
    main()