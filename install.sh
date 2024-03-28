#!/bin/bash


echo "╔══╣ Install: Speech Recognition Whisper (STARTING) ╠══╗"

sudo apt-get update

pip3 install whisper

pip3 install git+https://github.com/openai/whisper.git

sudo apt-get install ffmpeg

sudo apt-get install python3-pyaudio

pip3 install playsound

cd ~/catkin_ws/src/speech_recognition_whisper/
python3 setup.py

echo "╚══╣ Install: Speech Recognition Whisper (FINISHED) ╠══╝"