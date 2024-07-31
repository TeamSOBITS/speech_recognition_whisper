#!/usr/bin/env python3
from playsound import playsound
import os

# Path to the audio file
path = os.path.join('/home/sobits/colcon_ws/install/speech_recognition_whisper/share/speech_recognition_whisper/mp3', 'start_sound.mp3')


# Play the sound
try:
    playsound(path)
    print(f"Successfully played sound from {path}")
except Exception as e:
    print(f"An error occurred: {e}")
