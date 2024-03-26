#!/usr/bin/env python3
# coding: utf-8
import rospy
from speech_recognition_whisper.srv import SpeechRecognitionWhisper, SpeechRecognitionWhisperResponse

## 完成の枠組み
class WhisperServer():
    def __init__(self):
        rospy.Service("/speech_recognition_whisper/speech_recognition", SpeechRecognitionWhisper, self.speech_to_text)
        rospy.loginfo("Waiting for service...")
        rospy.spin()


    ## Serviceの具体的な内容
    def speech_to_text():
        return SpeechRecognitionWhisperResponse(transcript = [""])



if __name__ == "__main__":
    rospy.init_node("whisper_server")
    ws = WhisperServer()