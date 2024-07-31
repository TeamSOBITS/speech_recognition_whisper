#!/bin/bash


echo "╔══╣ Install: Speech Recognition Whisper (STARTING) ╠══╗"

sudo apt-get update

pip3 install whisper

pip3 install git+https://github.com/openai/whisper.git

sudo apt-get install ffmpeg

sudo apt-get install python3-pyaudio

pip3 install playsound

cd ~/colcon_ws/src/speech_recognition_whisper/
python3 install.py

# Install "sobits_msgs"
cd ~/colcon_ws/src/
# git clone https://github.com/TeamSOBITS/sobits_msgs.git
# cd ~/colcon_ws/src/speech_recognition_vosk/

echo "╚══╣ Install: Speech Recognition Whisper (FINISHED) ╠══╝"