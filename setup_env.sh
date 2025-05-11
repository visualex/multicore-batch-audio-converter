#!/bin/bash

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "#run:"
echo "venv/bin/python convert.py /path/to/input /path/to/output \"mp3|wav\" flac 44100 16 --workers 4"

