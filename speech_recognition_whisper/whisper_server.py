import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

import json
from std_msgs.msg import String
from sobits_interfaces.action import SpeechRecognition
from ament_index_python.packages import get_package_share_directory

import whisper
import subprocess
import re
import os
import threading
import time
import glob
import asyncio

class WhisperServer(Node):
    SOUND_FILES_PATH = os.path.join(get_package_share_directory('sobits_interfaces'), 'mp3')
    PULSEAUDIO_SOURCE_NAME_PATTERN = re.compile(r'^\s*(?:Name|名前):\s*(.+)\s*$')
    PULSEAUDIO_SAMPLE_SPEC_PATTERN = re.compile(r'^\s*(?:Sample Specification|サンプル仕様):\s*(\S+)\s+(\d+)ch\s+(\d+)Hz')

    def __init__(self):
        super().__init__('whisper_server')

        share_dir = get_package_share_directory('speech_recognition_whisper')
        self.sound_file_directory = os.path.join(os.path.abspath(os.path.join(share_dir, '..', '..', '..', '..')),
                                                 'src', 'speech_recognition_whisper', 'sound_file')
        os.makedirs(self.sound_file_directory, exist_ok=True)
        self.wav_path = os.path.join(self.sound_file_directory, "output.wav")

        self.default_audio_source, self.default_sample_rate, self.default_channels = self.get_pulseaudio_source_info()
        if not self.default_audio_source:
            self.get_logger().fatal("Could not determine PulseAudio default input source. Node terminating.")
            self.model = None
            return

        if self.default_sample_rate is None or self.default_channels is None:
            self.get_logger().warn(
                f"Sample rate or channels unknown for {self.default_audio_source}. Using default 48000 Hz, 1 channel.")
            self.default_sample_rate = 48000
            self.default_channels = 1

        self.get_logger().info(f"Mic: {self.default_audio_source}, Rate: {self.default_sample_rate} Hz, Channels: {self.default_channels}")

        self.raw_audio_format = 's16le'
        self.raw_audio_rate = self.default_sample_rate
        self.raw_audio_channels = self.default_channels

        self.whisper_wav_rate = 16000
        self.whisper_wav_channels = 1

        self.declare_parameter('model_name', 'small')
        self.whisper_model_name = self.get_parameter('model_name').get_parameter_value().string_value

        try:
            self.model = whisper.load_model(self.whisper_model_name)
            self.get_logger().info(f"Whisper model '{self.whisper_model_name}' loaded on {self.model.device}.")
        except Exception as e:
            self.get_logger().fatal(f"Failed to load whisper model: {e}")
            self.model = None
            return

        self.declare_parameter('language', 'en')
        self.declare_parameter('replace_prompt_whisper', [""])
        self.declare_parameter('task', 'transcribe')
        self.declare_parameter('use_feedback', False)
        self.declare_parameter('use_prompt', True)

        self.language = self.get_parameter('language').get_parameter_value().string_value
        self.prompt = self.get_parameter('replace_prompt_whisper').get_parameter_value().string_array_value
        self.task = self.get_parameter('task').get_parameter_value().string_value
        self.use_feedback_enabled = self.get_parameter('use_feedback').get_parameter_value().bool_value
        self.use_prompt = self.get_parameter('use_prompt').get_parameter_value().bool_value

        self.get_logger().info(f"use_feedback: {self.use_feedback_enabled}")

        self.action_server = ActionServer(
            self, SpeechRecognition, "speech_recognition",
            execute_callback=self.speech_to_text,
            callback_group=ReentrantCallbackGroup(),
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )

        self.wip_subscriber = self.create_subscription(
            String,
            '/speech_recognition/wip_result',
            self.wip_callback,
            10
        )

        self.wip_feedback_control_publisher = self.create_publisher(String, '/speech_recognition/wip_feedback', 10)

        self.current_goal_handle = None
        self.async_loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self.loop_thread.start()

        YELLOW = '\033[93m'
        ENDC = '\033[0m'
        self.get_logger().info(f"{YELLOW}Mic: {self.default_audio_source}{ENDC}, Rate: {self.default_sample_rate} Hz, Channels: {self.default_channels}")
        self.get_logger().info(f"{YELLOW}Whisper Server is READY and waiting for requests.{ENDC}")

    def _start_event_loop(self):
        asyncio.set_event_loop(self.async_loop)
        self.async_loop.run_forever()

    def goal_callback(self, goal_request):
        self.get_logger().info('Received goal request')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    def wip_callback(self, msg):
        if self.use_feedback_enabled and self.current_goal_handle and self.current_goal_handle.is_active:
            feedback_msg = SpeechRecognition.Feedback()
            feedback_msg.addition_text = msg.data
            self.current_goal_handle.publish_feedback(feedback_msg)
            self.get_logger().info(f"Published WIP feedback: '{msg.data}'")

    def speech_to_text(self, goal_handle):
        future = asyncio.run_coroutine_threadsafe(self._speech_to_text_async(goal_handle), self.async_loop)
        return future.result()

    async def _speech_to_text_async(self, goal_handle):
        response = SpeechRecognition.Result()
        self.current_goal_handle = goal_handle

        if self.model is None:
            self.get_logger().error("Whisper model not loaded.")
            goal_handle.abort()
            response.result_text = "System Error: Whisper model not loaded."
            self.current_goal_handle = None
            return response

        duration = goal_handle.request.timeout_sec
        feedback_rate = goal_handle.request.feedback_rate
        self.get_logger().info(f"Recording duration: {duration}s, Feedback rate: {feedback_rate} Hz")
        self._cleanup_files()

        wip_segment_duration = 1.0 / feedback_rate if feedback_rate > 0 else 0.5

        fifo_wip = os.path.join(self.sound_file_directory, "audio_fifo_wip")
        fifo_final = os.path.join(self.sound_file_directory, "audio_fifo_final")
        self._create_fifo(fifo_wip)
        self._create_fifo(fifo_final)

        try:
            if not goal_handle.request.silent_mode:
                threading.Thread(target=self._play_sound_with_ffplay, args=('start_sound.mp3',)).start()
                await asyncio.sleep(0.5)

            self.parec_proc = subprocess.Popen([
                'parec', '-d', self.default_audio_source,
                f'--format={self.raw_audio_format}',
                f'--channels={self.raw_audio_channels}',
                f'--rate={self.raw_audio_rate}',
                '--file-format=raw'
            ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

            self.tee_proc = subprocess.Popen([
                'tee', fifo_wip, fifo_final
            ], stdin=self.parec_proc.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            self.parec_proc.stdout.close()

            self.ffmpeg_wip_proc = subprocess.Popen([
                'ffmpeg',
                '-f', self.raw_audio_format,
                '-ar', str(self.raw_audio_rate),
                '-ac', str(self.raw_audio_channels),
                '-i', fifo_wip,
                '-f', 'segment',
                '-segment_time', str(wip_segment_duration),
                '-segment_format', 'wav',
                '-reset_timestamps', '1',
                '-map', '0:a',
                '-acodec', 'pcm_s16le',
                '-ar', str(self.whisper_wav_rate),
                '-ac', str(self.whisper_wav_channels),
                '-y',
                os.path.join(self.sound_file_directory, "temp_wip_output_%03d.wav"),
                '-loglevel', 'error'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            self.ffmpeg_final_proc = subprocess.Popen([
                'ffmpeg',
                '-f', self.raw_audio_format,
                '-ar', str(self.raw_audio_rate),
                '-ac', str(self.raw_audio_channels),
                '-i', fifo_final,
                '-acodec', 'pcm_s16le',
                '-ar', str(self.whisper_wav_rate),
                '-ac', str(self.whisper_wav_channels),
                '-t', str(duration),
                self.wav_path,
                '-y',
                '-loglevel', 'error'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

            if self.use_feedback_enabled:
                msg_dict = {
                    "active": True,
                    "feedback_rate": feedback_rate  
                }
                msg = String()
                msg.data = json.dumps(msg_dict)
                self.wip_feedback_control_publisher.publish(msg)
            start_time = time.time()
            while (time.time() - start_time) < (duration + 5):
                if goal_handle.is_cancel_requested:
                    raise rclpy.action.CancelGoalException()
                if self.ffmpeg_final_proc.poll() is not None:
                    break
                await asyncio.sleep(0.1)
            else:
                raise subprocess.TimeoutExpired(self.ffmpeg_final_proc.args, duration + 5)

            goal_handle.succeed()
        except rclpy.action.CancelGoalException:
            goal_handle.canceled()
            response.result_text = "Action cancelled by client."
            return response
        except FileNotFoundError as e:
            self.get_logger().error(f"Command not found: {e.filename}")
            goal_handle.abort()
            response.result_text = f"System Error: Command not found ({e.filename})"
            return response
        except subprocess.TimeoutExpired:
            self.get_logger().error("Recording timed out.")
            goal_handle.abort()
            response.result_text = "Recording timed out."
            return response
        except Exception as e:
            self.get_logger().error(f"Error during recording or processing: {e}")
            goal_handle.abort()
            response.result_text = f"Error: {e}"
            return response
        finally:
            self._terminate_processes()
            self._remove_fifo(fifo_wip)
            self._remove_fifo(fifo_final)
            if self.use_feedback_enabled:
                msg_dict = {
                    "active": False,
                    "feedback_rate": feedback_rate  
                }
                msg = String()
                msg.data = json.dumps(msg_dict)
                self.wip_feedback_control_publisher.publish(msg)
            self.current_goal_handle = None

        if not goal_handle.request.silent_mode:
            threading.Thread(target=self._play_sound_with_ffplay, args=('end_sound.mp3',)).start()

        if not os.path.exists(self.wav_path) or os.path.getsize(self.wav_path) == 0:
            self.get_logger().warn("No audio recorded.")
            goal_handle.abort()
            response.result_text = "No audio recorded."
            return response

        try:
            prompt_text = " ".join(self.prompt) if self.use_prompt and self.prompt else ""
            result = self.model.transcribe(
                self.wav_path,
                language=self.language,
                task=self.task,
                initial_prompt=prompt_text if prompt_text else None
            )
            text = result.get("text", "") if result else ""
            if not text:
                self.get_logger().warn("No speech recognized.")
                response.result_text = "No speech recognized."
            else:
                response.result_text = text
                self.get_logger().info(f"Recognition result: '{text}'")
        except Exception as e:
            self.get_logger().error(f"Transcription error: {e}")
            goal_handle.abort()
            response.result_text = f"Transcription error: {e}"
            return response

        return response

    def _play_sound_with_ffplay(self, filename):
        sound_path = os.path.join(self.SOUND_FILES_PATH, filename)
        if not os.path.exists(sound_path):
            self.get_logger().warn(f"Sound file not found: {sound_path}")
            return
        try:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', sound_path], check=True)
        except Exception as e:
            self.get_logger().warn(f"Sound playback failed: {e}")

    def get_pulseaudio_source_info(self):
        try:
            info = subprocess.run(['pactl', 'info'], capture_output=True, text=True, check=True)
            default_source = None
            for line in info.stdout.splitlines():
                if "Default Source:" in line or "デフォルトソース:" in line:
                    default_source = line.split(':', 1)[1].strip()
                    break
            if not default_source:
                self.get_logger().warn("Default PulseAudio source not found.")
                return None, None, None

            list_sources = subprocess.run(['pactl', 'list', 'sources'], capture_output=True, text=True, check=True)
            blocks = []
            current_block = []
            for line in list_sources.stdout.splitlines():
                if line.strip().startswith("Source #"):
                    if current_block:
                        blocks.append(current_block)
                    current_block = [line]
                else:
                    current_block.append(line)
            if current_block:
                blocks.append(current_block)

            for block in blocks:
                for line in block:
                    m = self.PULSEAUDIO_SOURCE_NAME_PATTERN.match(line)
                    if m and m.group(1).strip() == default_source:
                        rate, channels = self.parse_sample_rate_and_channels(block)
                        return default_source, rate, channels

            for block in blocks:
                for line in block:
                    m = self.PULSEAUDIO_SOURCE_NAME_PATTERN.match(line)
                    if m:
                        name = m.group(1).strip()
                        if default_source in name or name in default_source:
                            rate, channels = self.parse_sample_rate_and_channels(block)
                            return default_source, rate, channels

            self.get_logger().warn(f"Could not find detailed info for source '{default_source}'.")
            return default_source, None, None

        except Exception as e:
            self.get_logger().error(f"PulseAudio source info error: {e}")
            return None, None, None

    def parse_sample_rate_and_channels(self, lines):
        for line in lines:
            m = self.PULSEAUDIO_SAMPLE_SPEC_PATTERN.match(line)
            if m:
                return int(m.group(3)), int(m.group(2))
        return None, None

    def _cleanup_files(self):
        wip_files = glob.glob(os.path.join(self.sound_file_directory, "temp_wip_output_*.wav"))
        for f in wip_files:
            try:
                os.remove(f)
                self.get_logger().info(f"Removed old WIP file: {f}")
            except Exception as e:
                self.get_logger().warn(f"Failed to remove WIP file {f}: {e}")
        if os.path.exists(self.wav_path):
            try:
                os.remove(self.wav_path)
                self.get_logger().info(f"Removed old WAV file: {self.wav_path}")
            except Exception as e:
                self.get_logger().warn(f"Failed to remove WAV file {self.wav_path}: {e}")

    def _create_fifo(self, path):
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                self.get_logger().warn(f"Failed to remove FIFO {path}: {e}")
        os.mkfifo(path)
        self.get_logger().info(f"Created FIFO: {path}")

    def _remove_fifo(self, path):
        if os.path.exists(path):
            try:
                os.remove(path)
                self.get_logger().info(f"Removed FIFO: {path}")
            except Exception as e:
                self.get_logger().warn(f"Failed to remove FIFO {path}: {e}")

    def _terminate_processes(self):
        for proc in [getattr(self, attr) for attr in ['parec_proc', 'tee_proc', 'ffmpeg_wip_proc', 'ffmpeg_final_proc'] if hasattr(self, attr)]:
            if proc and proc.poll() is None:
                self.get_logger().warn(f"Killing lingering process: {proc.args[0]}")
                proc.kill()
                proc.wait(timeout=5)

def main(args=None):
    rclpy.init(args=args)
    node = WhisperServer()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()