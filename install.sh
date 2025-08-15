#!/bin/bash

echo "╔══╣ Install: Speech Recognition Whisper (STARTING) ╠══╗"


# Keep the current directory
DIR=$(pwd)

sudo apt update -y

sudo apt install pulseaudio-utils -y
sudo apt install ffmpeg

yes | sudo apt install -y ros-humble-vision-msgs
echo "System dependencies installed."

echo "--- Installing Python packages via pip3 ---"
python3 -m pip install -U pip
python3 -m pip install git+https://github.com/openai/whisper.git 

cd $DIR
python3 install.py

# Install "sobits_msgs"
cd ..
SOBITS_MSGS_REPO="sobits_msgs"
# Check if the repository already exists
if [ ! -d "$SOBITS_MSGS_REPO" ]; then
    echo "Cloning $SOBITS_MSGS_REPO repository..."
    git clone -b humble-devel https://github.com/TeamSOBITS/sobits_interfaces.git
    echo "$SOBITS_MSGS_REPO cloned successfully."
else
    echo "$SOBITS_MSGS_REPO repository already exists. Skipping clone."
fi

cd $DIR

echo "╚══╣ Install: Speech Recognition Whisper (FINISHED) ╠══╝"
