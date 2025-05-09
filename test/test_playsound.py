#!/usr/bin/env python3
from playsound import playsound
import os

# Path to the audio file
path = os.path.join('/home/sobits/colcon_ws/install/sobits_interfaces/share/sobits_interfaces/mp3', 'start_sound.mp3')


# Play the sound
playsound(path)
