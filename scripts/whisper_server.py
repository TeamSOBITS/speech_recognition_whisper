#!/usr/bin/env python3
# coding: utf-8
import rospy
import roslib.packages
from sobits_msgs.srv import SpeechRecognition, SpeechRecognitionResponse
import whisper
import pyaudio
import wave
from playsound import playsound



# 完成の枠組み
class WhisperServer():
    def __init__(self):
        self.path = roslib.packages.get_pkg_dir("speech_recognition_whisper")
        self.model = whisper.load_model(str(rospy.get_param("/whisper_server/model")))
        self.sample_rate = int(rospy.get_param("/whisper_server/sample_rate"))
        self.chunk_size = int(rospy.get_param("/whisper_server/chunk_size"))
        self.channels = int(rospy.get_param("/whisper_server/channels"))
        self.audio_format=pyaudio.paInt16
        rospy.Service("/speech_recognition", SpeechRecognition, self.speech_to_text)
        rospy.loginfo("Waiting for service...")
        rospy.spin()


    # Serviceの具体的な内容
    def speech_to_text(self, mrv):
        playsound(self.path + "/mp3/start_sound.mp3")
        # 録音開始
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.audio_format,
                            channels=self.channels,
                            rate=self.sample_rate,
                            input=True,
                            frames_per_buffer=self.chunk_size)
    
        frames = []

        for i in range(0, int(self.sample_rate / self.chunk_size * int(mrv.timeout_sec)) + 1):
            data = stream.read(self.chunk_size)
            frames.append(data)
        # 録音終了
        playsound(self.path + "/mp3/end_sound.mp3")

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # 音声ファイルの書き出し
        wf = wave.open(self.path + "/sound_file/output.wav", 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(audio.get_sample_size(self.audio_format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        result = self.model.transcribe(self.path + "/sound_file/output.wav")
        print(result["text"])
        return SpeechRecognitionResponse(transcript = [result["text"]])



if __name__ == "__main__":
    rospy.init_node("whisper_server")
    ws = WhisperServer()