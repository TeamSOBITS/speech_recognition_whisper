#!/bin/bash

echo "╔══╣ Install: Speech Recognition Whisper (STARTING) ╠══╗"


# Keep the current directory
DIR=$(pwd)

sudo apt-get update
sudo apt-get install -y \
    ffmpeg \
    python3-pyaudio

python3 -m pip install -U pip
python3 -m pip install \
    playsound
# python3 -m pip install whisper
python3 -m pip install git+https://github.com/openai/whisper.git 


cd $DIR
python3 install.py

# Install "sobits_msgs"
cd ..
git clone https://github.com/TeamSOBITS/sobits_msgs.git

# Install "alsamixer"
# sudo apt-get remove --purge alsa-base pulseaudio
# sudo apt-get install alsa-base pulseaudio
# sudo alsa force-reload

cd $DIR


echo "╚══╣ Install: Speech Recognition Whisper (FINISHED) ╠══╝"
