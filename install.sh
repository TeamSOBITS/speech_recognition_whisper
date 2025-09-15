#!/bin/bash
echo "╔══╣ Install: Speech Recognition Whisper (STARTING) ╠══╗"

# Keep the current directory
DIR=$(pwd)

sudo apt update -y

sudo apt install pulseaudio-utils -y
sudo apt install ffmpeg

yes | sudo apt install -y ros-humble-vision-msgs
echo "System dependencies installed."

echo "--- Cleaning old cuDNN (if any) ---"
sudo apt remove -y libcudnn8* libcudnn9* || true
sudo apt autoremove -y

echo "--- Installing cuDNN 9.x (CUDA 12) ---"
sudo apt install -y libcudnn9-cuda-12 libcudnn9-dev-cuda-12
echo " cuDNN 9 installed."


echo "--- Installing Python packages via pip3 ---"
python3 -m pip install -U pip
python3 -m pip install git+https://github.com/openai/whisper.git 

echo "--- Installing Faster-Whisper ---"
python3 -m pip install -U faster-whisper


echo "--- Installing VAD ---"

pip3 install -U --force-reinstall -v git+https://github.com/TEN-framework/ten-vad.git

sudo apt install libc++1 -y

cd $DIR
python3 install.py

# Install "sobits_interfaces"
cd ..
sobits_interfaces_REPO="sobits_interfaces"
# Check if the repository already exists
if [ ! -d "$sobits_interfaces_REPO" ]; then
    echo "Cloning $sobits_interfaces_REPO repository..."
    git clone -b humble-devel https://github.com/TeamSOBITS/sobits_interfaces.git
    echo "$sobits_interfaces_REPO cloned successfully."
else
    echo "$sobits_interfaces_REPO repository already exists. Skipping clone."
fi

cd $DIR

echo "╚══╣ Install: Speech Recognition Whisper (FINISHED) ╠══╝"
