#!/bin/bash

echo "=== AudioBatchConverter Setup ==="
echo ""

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH"
    echo "Please install Python 3.6 or newer and try again"
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ Warning: FFmpeg is not installed or not in PATH"
    echo "The converter requires FFmpeg to function correctly."
    echo ""
    echo "Install FFmpeg with one of the following commands:"
    echo "  • macOS:   brew install ffmpeg"
    echo "  • Ubuntu:  sudo apt install ffmpeg"
    echo "  • Windows: choco install ffmpeg"
    echo ""
    read -p "Continue setup anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Creating Python virtual environment..."
python3 -m venv venv

# Check if venv was created successfully
if [ ! -d "venv" ]; then
    echo "❌ Error: Failed to create virtual environment"
    echo "Please ensure you have the venv module installed: python3 -m pip install --user virtualenv"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "To use AudioBatchConverter:"
echo ""
echo "1. GUI Mode (recommended):"
echo "   venv/bin/python convert.py --gui"
echo ""
echo "2. CLI Mode:"
echo "   venv/bin/python convert.py /path/to/input /path/to/output \"mp3|wav\" flac 44100 16 --workers 4"
echo ""
echo "For more information, see README.md"