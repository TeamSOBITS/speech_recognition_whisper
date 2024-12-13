#!/usr/bin/env python3
# coding: utf-8
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException
from rclpy.executors import MultiThreadedExecutor
from sobits_interfaces.action import SpeechRecognition
import whisper
import pyaudio
import wave
from playsound import playsound
import os
import getpass

class WhisperServer(Node):
    def __init__(self):
        super().__init__('whisper_server')
        
        # Declare parameters
        self.declare_parameter('model', 'base')
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('chunk_size', 1024)
        self.declare_parameter('channels', 1)
        
        # Get parameters
        self.model = whisper.load_model(self.get_parameter('model').get_parameter_value().string_value)
        self.sample_rate = self.get_parameter('sample_rate').get_parameter_value().integer_value
        self.chunk_size = self.get_parameter('chunk_size').get_parameter_value().integer_value
        self.channels = self.get_parameter('channels').get_parameter_value().integer_value
        self.audio_format = pyaudio.paInt16
        
        # Define path for sound files
        # self.path = os.path.join(os.path.dirname(__file__), '..', 'mp3')
        self.path = "/home/" + str(getpass.getuser()) + "/colcon_ws/src/speech_recognition_whisper"
        
        # Create server
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
        """Accept or reject a client request to begin an action."""
        # This server allows multiple goals in parallel
        self.get_logger().info('Received goal request')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        """Accept or reject a client request to cancel an action."""
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    async def speech_to_text(self, goal_handle):
        feedback = SpeechRecognition.Feedback()
        response = SpeechRecognition.Result()

        # Play start sound
        playsound(os.path.join(self.path, 'mp3', 'start_sound.mp3'))
        
        # Record audio
        audio = pyaudio.PyAudio()
        try:
            stream = audio.open(format=self.audio_format,
                                channels=self.channels,
                                rate=self.sample_rate,
                                input=True,
                                frames_per_buffer=self.chunk_size)
        except Exception as e:
            self.get_logger().error(f"Audio stream error: {e}")
            return response
        
        frames = []
        for _ in range(int(self.sample_rate / self.chunk_size * goal_handle.request.timeout_sec)):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info('Goal canceled')
                response.is_cancel = True
                return response
            data = stream.read(self.chunk_size)
            frames.append(data)
            feedback.wip_result = []
            self.get_logger().info('Publishing feedback: {0}'.format(feedback.wip_result))
            goal_handle.publish_feedback(feedback)
        
        # Stop recording and play end sound
        playsound(os.path.join(self.path, 'mp3', 'end_sound.mp3'))

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the recorded audio
        with wave.open(os.path.join(self.path, 'sound_file', 'output.wav'), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(audio.get_sample_size(self.audio_format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))        
        
        # Transcribe audio
        goal_handle.succeed()
        result = self.model.transcribe(os.path.join(self.path, 'sound_file', 'output.wav'))
        self.get_logger().info(f'Transcribed text: {result["text"]}')
        
        response.transcript = [result["text"]]
        response.is_cancel = False
        self.get_logger().info('Returning result: {}'.format(result["text"]))
        return response

def main(args=None):
    try:
        rclpy.init(args=args)

        server = WhisperServer()

        # Use a MultiThreadedExecutor to enable processing goals concurrently
        executor = MultiThreadedExecutor()

        rclpy.spin(server, executor=executor)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
if __name__ == '__main__':
    main()
