#!/bin/bash


echo "╔══╣ Install: Speech Recognition Whisper (STARTING) ╠══╗"

sudo apt-get update

pip3 install whisper

pip3 install git+https://github.com/openai/whisper.git

sudo apt-get install ffmpeg

sudo apt-get install python-pyaudio python3-pyaudio

cd ~/catkin_ws/src/speech_recognition_whisper/
python3 setup.py

echo "╚══╣ Install: Speech Recognition Whisper (FINISHED) ╠══╝"