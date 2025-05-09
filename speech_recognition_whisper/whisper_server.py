# -*- coding:utf-8 -*-
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException
from rclpy.executors import MultiThreadedExecutor
from sobits_interfaces.action import SpeechRecognition
import whisper
import time
import pyaudio
import wave
from playsound import playsound
import os
import subprocess

from ament_index_python.packages import get_package_share_directory

class WhisperServer(Node):
    def __init__(self):
        super().__init__('whisper_server')

        self.declare_parameter('model', 'base')
        self.declare_parameter('launguage', 'en')
        self.declare_parameter('replace_prompt_whisper', [""])
        self.declare_parameter('task', 'transcribe')
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('chunk_size', 1024)
        self.declare_parameter('channels', 1)
        self.declare_parameter('use_feedback', True)
        self.declare_parameter('use_prompt', True)

        self.model = whisper.load_model(self.get_parameter('model').get_parameter_value().string_value)
        self.launguage = self.get_parameter('launguage').get_parameter_value().string_value
        self.prompt = self.get_parameter('replace_prompt_whisper').get_parameter_value().string_array_value
        self.task = self.get_parameter('task').get_parameter_value().string_value
        self.sample_rate = self.get_parameter('sample_rate').get_parameter_value().integer_value
        self.chunk_size = self.get_parameter('chunk_size').get_parameter_value().integer_value
        self.channels = self.get_parameter('channels').get_parameter_value().integer_value
        self.use_feedback = self.get_parameter('use_feedback').get_parameter_value().bool_value
        self.use_prompt = self.get_parameter('use_prompt').get_parameter_value().bool_value
        self.audio_format = pyaudio.paInt16

        self.path = get_package_share_directory('speech_recognition_whisper')
        self.sound_folder_path = os.path.join(get_package_share_directory('sobits_interfaces'), 'mp3')

        self.server = ActionServer(
            self,
            SpeechRecognition,
            "speech_recognition",
            execute_callback=self.speech_to_text,
            callback_group=ReentrantCallbackGroup(),
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback)

        self.get_logger().info('Whisper Server is ready and waiting for service requests.')

    def goal_callback(self, goal_request):
        self.get_logger().info('Received goal request')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    async def speech_to_text(self, goal_handle):
        feedback = SpeechRecognition.Feedback()
        response = SpeechRecognition.Result()

        if (self.use_feedback):
            if os.path.exists(os.path.join(self.path, 'sound_file', 'wip_output.wav')):
                cmd = "rm %s" % (os.path.join(self.path, 'sound_file', 'wip_output.wav'))
                subprocess.call(cmd, shell=True)
            if os.path.exists(os.path.join(self.path, 'sound_file', 'output.wav')):
                cmd = "rm %s" % (os.path.join(self.path, 'sound_file', 'output.wav'))
                subprocess.call(cmd, shell=True)

            f = open(os.path.join(self.path, 'sound_file', 'wip_result.txt'), 'w', encoding='UTF-8')
            f.write('MODEL NAME:' + str(self.get_parameter('model').get_parameter_value().string_value) + "\n")
            f.write('RATE:' + str(1.0/float(goal_handle.request.feedback_rate)) + "\n")
            f.write('EXIT:FALSE\n')
            f.write('TEXT:')
            f.close()

            subprocess.Popen(["python3", str(os.path.join(self.path, 'sound_file', 'wip_predict.py'))])

        if (not goal_handle.request.silent_mode):
            playsound(os.path.join(self.sound_folder_path, 'start_sound.mp3'))

        audio = pyaudio.PyAudio()
        try:
            stream = audio.open(format=self.audio_format,
                                channels=self.channels,
                                rate=self.sample_rate,
                                input=True,
                                frames_per_buffer=self.chunk_size)
        except Exception as e:
            self.get_logger().error(f"Audio stream error: {e}")

        frames = []
        wip_frames = []
        last_feedback_time = time.time()
        for _ in range(int(self.sample_rate / self.chunk_size * (goal_handle.request.timeout_sec + 1))):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Goal canceled')
                response.result_text = ""
                return response

            time.sleep(1.0 / self.sample_rate)
            data = stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(data)

            if (self.use_feedback):
                wip_frames.append(data)

                if ((time.time() - last_feedback_time) > (1.0/float(goal_handle.request.feedback_rate))):
                    with wave.open(os.path.join(self.path, 'sound_file', 'wip_output.wav'), 'wb') as wf:
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(audio.get_sample_size(self.audio_format))
                        wf.setframerate(self.sample_rate)
                        wf.writeframes(b''.join(wip_frames))
                    f = open(os.path.join(self.path, 'sound_file', 'wip_result.txt'), 'r', encoding='UTF-8')
                    feedback.addition_text = str(f.read().split("\n")[3].split(":")[1])
                    f.close()
                    self.get_logger().info('Publishing feedback: {0}'.format(feedback.addition_text))
                    goal_handle.publish_feedback(feedback)
                    wip_frames = []
                    last_feedback_time = time.time()

        if (self.use_feedback):
            f = open(os.path.join(self.path, 'sound_file', 'wip_result.txt'), 'w', encoding='UTF-8')
            f.write('MODEL NAME:' + str(self.get_parameter('model').get_parameter_value().string_value) + "\n")
            f.write('RATE:' + str(1.0/float(goal_handle.request.feedback_rate)) + "\n")
            f.write('EXIT:TRUE\n')
            f.write('TEXT:')
            f.close()

        if (not goal_handle.request.silent_mode):
            playsound(os.path.join(self.sound_folder_path, 'end_sound.mp3'))

        stream.stop_stream()
        stream.close()
        audio.terminate()

        self.get_logger().info('Saving audio to: {}'.format(os.path.join(self.path, 'sound_file', 'output.wav')))
        with wave.open(os.path.join(self.path, 'sound_file', 'output.wav'), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))

        self.get_logger().info('Starting transcription.')

        if (self.use_prompt and (len(self.prompt)!=0) and (self.prompt[0]!="")):
            result = self.model.transcribe(
                        os.path.join(self.path, 'sound_file', 'output.wav'),
                        language=self.launguage,
                        task=self.task,
                        initial_prompt=" ".join(self.prompt),
            )
        else:
            result = self.model.transcribe(
                        os.path.join(self.path, 'sound_file', 'output.wav'),
                        language=self.launguage,
                        task=self.task,
            )
        self.get_logger().info('Transcription finished. Result: {}'.format(result["text"]))
        response.result_text = result["text"]
        goal_handle.succeed()
        return response

def main(args=None):
    try:
        rclpy.init(args=args)

        server = WhisperServer()

        executor = MultiThreadedExecutor()

        rclpy.spin(server, executor=executor)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
if __name__ == '__main__':
    main()