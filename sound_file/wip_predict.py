# coding: utf-8
import whisper
import time
import pyaudio
import wave
from playsound import playsound
import os

from ament_index_python.packages import get_package_share_directory    

import random

path = os.path.join(get_package_share_directory('speech_recognition_whisper'), 'sound_file', 'wip_result.txt')
# path = 'wip_result.txt'

f = open(path, 'r', encoding='UTF-8')
model_name = str(f.read().split("\n")[0].split(":")[1])
model = whisper.load_model(model_name)
f.close()

last_predict_time = time.time()
while True:
    f = open(path, 'r', encoding='UTF-8')
    data = f.read()
    f.close()

    rate = float(data.split("\n")[1].split(":")[1])
    if (str(data.split("\n")[2].split(":")[1]) == "TRUE"): flag = True
    else:                                                  flag = False

    if (((time.time() - last_predict_time) > (1.0/rate)) and (not flag)):
        if os.path.exists(os.path.join(get_package_share_directory('speech_recognition_whisper'), 'sound_file', 'wip_output.wav')):
            wip_result = model.transcribe(os.path.join(get_package_share_directory('speech_recognition_whisper'), 'sound_file', 'wip_output.wav'))
            f = open(path, 'r', encoding='UTF-8')
            data = f.read()
            f.close()
            f = open(path, 'w', encoding='UTF-8')
            f.write("\n".join(data.split("\n")[:3]) + '\nTEXT:' + str(wip_result["text"]))
            f.close()
        last_predict_time = time.time()
    elif (not flag):
        time.sleep(0.1)
    else:
        exit()