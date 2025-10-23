import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from sobits_interfaces.action import SpeechRecognition
from ament_index_python.packages import get_package_share_directory

import subprocess
import numpy as np
import threading
import queue
import time
import wave
import os
import re
import glob
from scipy.signal import resample_poly
from collections import deque
import sys

class WhisperServer(Node):
    def __init__(self):
        super().__init__('whisper_server')
        self.PULSEAUDIO_SOURCE_NAME_PATTERN = re.compile(r'^\s*(?:Name|名前):\s*(.+)\s*$')
        self.PULSEAUDIO_SAMPLE_SPEC_PATTERN = re.compile(r'^\s*(?:Sample Specification|サンプル仕様):\s*(\S+)\s+(\d+)ch\s+(\d+)Hz')

        self.declare_parameter('model_name', 'small')
        self.declare_parameter('language', 'en')
        self.declare_parameter('replace_prompt_whisper', [""])
        self.declare_parameter('task', 'transcribe')
        self.declare_parameter('use_prompt', False)
        self.declare_parameter('use_feedback', True)
        self.declare_parameter('min_wipe_duration', 0.2)
        self.declare_parameter('extra_audio_duration_sec', 0.2)

        self.declare_parameter('backend', 'whisper')
        self.declare_parameter("compute_type", "float16")

        self.model_name = self.get_parameter('model_name').get_parameter_value().string_value
        self.use_feedback_enabled = self.get_parameter('use_feedback').get_parameter_value().bool_value
        self.backend = self.get_parameter('backend').get_parameter_value().string_value
        compute_type = self.get_parameter("compute_type").get_parameter_value().string_value
        
        self.SOUND_FILES_PATH = os.path.join(get_package_share_directory('sobits_interfaces'), 'mp3')

        share_dir = get_package_share_directory('speech_recognition_whisper')
        self.sound_file_directory = os.path.join(share_dir, 'sound_file')
        os.makedirs(self.sound_file_directory, exist_ok=True)
        self.wav_path = os.path.join(self.sound_file_directory, "output.wav")
        self.get_logger().info(f"Output path: {self.wav_path}")
        self.parec_proc = None

        source_name, sample_rate, channels = self.get_pulseaudio_source_info()

        if source_name is None:
            self.get_logger().warn("Failed to get default microphone. Using fallback settings.")
            self.source_name = "default"
            self.sample_rate = 44100
            self.channels = 2
        else:
            self.source_name = source_name
            self.sample_rate = sample_rate if sample_rate is not None else 44100
            self.channels = channels if channels is not None else 2
        
        self.get_logger().info(f"Microphone: {self.source_name}, Sample rate: {self.sample_rate} Hz, Channels: {self.channels}")
        
        try:
            load_start = time.time()
            if self.backend == "whisper":
                import whisper
                self.model = whisper.load_model(self.model_name)
                self.get_logger().info(f"Whisper model '{self.model_name}' loaded on {self.model.device}.")
            elif self.backend == "faster-whisper":
                from faster_whisper import WhisperModel
                self.model = WhisperModel(self.model_name, device="cuda", compute_type=compute_type)
                self.get_logger().info(f"Faster-Whisper model '{self.model_name}' loaded.")
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
            load_end = time.time()
            self.get_logger().info(f"Time to model loading: {load_end - load_start:.2f} sec")
            
        except Exception as e:
            self.get_logger().fatal(f"Failed to load {self.backend} model: {e}")
            self.model = None
            return
        
        self.vad_processor = None
        if self.use_feedback_enabled:
            from .vad import VadProcessor
            self.vad_processor = VadProcessor(self)
            self.hop_size, self.vad_chunk_size_bytes, self.vad_name = self.vad_processor.get_hop_size()
            self.get_logger().info(f"VAD model loaded.")

        self.action_server = ActionServer(
            self, SpeechRecognition, "speech_recognition",
            execute_callback=self.execute_callback,
            callback_group=ReentrantCallbackGroup(),
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )
        YELLOW = '\033[93m'
        ENDC = '\033[0m'
        self.get_logger().info(f"Microphone: {YELLOW}{self.source_name}{ENDC}")
        self.get_logger().info(f"Sample Rate: {self.sample_rate} Hz, Channels: {self.channels}")
        self.get_logger().info(f"{YELLOW}Whisper Server is READY and waiting for requests.{ENDC}")
    
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

    def play_sound(self, filename):
        path = os.path.join(self.SOUND_FILES_PATH, filename)
        try:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path], check=True)
        except FileNotFoundError:
            self.get_logger().warn(f"ffplay not found: {filename}")
        except subprocess.CalledProcessError as e:
            self.get_logger().warn(f"Failed to play sound: {e}")
        except Exception as e:
            self.get_logger().warn(f"An error occurred during sound playback: {e}")

    def resample_audio(self, audio_np: np.ndarray, orig_sr: int, target_sr: int, channels: int):
        if channels > 1:
            audio_np = audio_np.reshape(-1, channels)
            audio_np = audio_np.mean(axis=1)
        return resample_poly(audio_np, target_sr, orig_sr)

    def goal_callback(self, goal_request):
        self.get_logger().info("Goal received")
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Cancel request received")
        return CancelResponse.ACCEPT
    
    async def execute_callback(self, goal_handle):
        self._cleanup_files()
        self.language = self.get_parameter('language').get_parameter_value().string_value
        self.prompt = self.get_parameter('replace_prompt_whisper').get_parameter_value().string_array_value
        self.task = self.get_parameter('task').get_parameter_value().string_value
        self.use_prompt = self.get_parameter('use_prompt').get_parameter_value().bool_value

        timeout_sec = goal_handle.request.timeout_sec
        self.get_logger().info(f"Recording started for {timeout_sec} seconds")
        silent = goal_handle.request.silent_mode
        feedback_rate = goal_handle.request.feedback_rate
        
        audio_q = queue.Queue()
        all_audio_buffer = []
        chunk_size_bytes = self.vad_chunk_size_bytes if self.use_feedback_enabled else 256 * 2 * 1

        if not silent:
            start_sound_thread = threading.Thread(target=self.play_sound, args=('start_sound.mp3',))
            start_sound_thread.start()
            start_sound_thread.join()
        
        def capture():
            try:
                proc = subprocess.Popen([
                    'parec', '-d', self.source_name,
                    '--format=s16le',
                    '--channels', str(self.channels),
                    '--rate', str(self.sample_rate),
                    '--file-format=raw',
                ], stdout=subprocess.PIPE)
                self.parec_proc = proc
                
                while True:
                    if not rclpy.ok() or self.parec_proc.poll() is not None:
                        break
                    chunk = self.parec_proc.stdout.read(chunk_size_bytes)
                    if not chunk:
                        break
                    audio_q.put(chunk)
            except Exception as e:
                self.get_logger().error(f"Recording error: {e}")
            finally:
                audio_q.put(None)
        thread = threading.Thread(target=capture, daemon = True)
        thread.start()

        start = time.time()
        response = SpeechRecognition.Result()

        if self.use_feedback_enabled:
            min_wipe_duration = self.get_parameter('min_wipe_duration').get_parameter_value().double_value
            extra_audio_duration_sec = self.get_parameter('extra_audio_duration_sec').get_parameter_value().double_value
            
            audio_buffer = []
            file_counter = 0
            extra_audio_buffer_size = int(extra_audio_duration_sec* 16000 / self.hop_size)
            pre_audio_buffer = deque(maxlen=extra_audio_buffer_size)
            post_audio_buffer = deque(maxlen=extra_audio_buffer_size)
            is_speaking = False
            vad_audio_buffer = np.array([], dtype=np.int16)

            while rclpy.ok():
                now = time.time()
                if now - start > timeout_sec:
                    break
                if goal_handle.is_cancel_requested:
                    self.get_logger().info("Goal canceled")
                    goal_handle.canceled()
                    if self.parec_proc:
                        self.parec_proc.terminate()
                    return response
                try:
                    chunk = audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue
                if chunk is None:
                    break
                
                current_audio_np = np.frombuffer(chunk, dtype=np.int16)
                resampled_data = self.resample_audio(current_audio_np, self.sample_rate, 16000, self.channels)
                vad_audio_buffer = np.concatenate([vad_audio_buffer, resampled_data.astype(np.int16)])
                all_audio_buffer.append(resampled_data)

                if len(vad_audio_buffer) >= self.hop_size:
                    vad_chunk = vad_audio_buffer[:self.hop_size]
                    vad_audio_buffer = vad_audio_buffer[self.hop_size:]

                    is_voice_now = self.vad_processor.vad_processor(vad_chunk, feedback_rate)
                    if is_voice_now:
                        if not is_speaking:
                            audio_buffer.extend(list(pre_audio_buffer))
                            pre_audio_buffer.clear()
                        audio_buffer.append(vad_chunk)
                        is_speaking = True
                    else:
                        if is_speaking:
                            post_audio_buffer.append(vad_chunk)  
                            if self.vad_name == "None" or len(post_audio_buffer) == post_audio_buffer.maxlen:
                                is_speaking = False

                                duration_sec = len(audio_buffer) * self.hop_size / 16000
                                if duration_sec < min_wipe_duration:
                                    audio_buffer = []
                                    post_audio_buffer.clear()
                                    continue
                                self.get_logger().info("Speech segment ended. Processing feedback.")

                                file_counter += 1
                                feedback_wav_path = os.path.join(self.sound_file_directory, f'feedback_{file_counter}.wav')
                                combined_buffer = audio_buffer + list(post_audio_buffer)

                                if self._save_buffer_to_wav(combined_buffer, feedback_wav_path, 16000, 1):
                                    try:
                                        prompt_text = " ".join(self.prompt) if self.use_prompt and self.prompt else ""
                                        if self.backend == "whisper":
                                            result = self.model.transcribe(
                                            feedback_wav_path,
                                            language=self.language,
                                            task=self.task,
                                            initial_prompt=prompt_text if prompt_text else None
                                            )
                                            text = result.get("text", "")
                                        
                                        elif self.backend == "faster-whisper":
                                            segments, _ = self.model.transcribe(feedback_wav_path, language=self.language, task=self.task if self.task in ["transcribe", "translate"] else "transcribe", initial_prompt=prompt_text if prompt_text else None)
                                            text = " ".join([seg.text for seg in segments]).strip()
                                        else:
                                            text =""
                                        feedback = SpeechRecognition.Feedback()
                                        if not text:
                                            feedback.addition_text = "No speech recognized."
                                            self.get_logger().warn("No speech recognized.")
                                        else:
                                            safe_text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                                            feedback.addition_text = safe_text
                                            self.get_logger().info(f"Feedback Result: {safe_text}")
                                        goal_handle.publish_feedback(feedback)
                                    except Exception as e:
                                        self.get_logger().error(f"Feedback error: {e}")
                                
                                audio_buffer = []
                                post_audio_buffer.clear()
                        else:
                            pre_audio_buffer.append(vad_chunk)
        else:
            while rclpy.ok():
                now = time.time()
                if now - start > timeout_sec:
                    self.get_logger().info("Timeout reached.")
                    break
                if goal_handle.is_cancel_requested:
                    self.get_logger().info("Goal canceled")
                    goal_handle.canceled()
                    if self.parec_proc:
                        self.parec_proc.terminate()
                    return response
                try:
                    chunk = audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue
                if chunk is None:
                    break
                
                current_audio_np = np.frombuffer(chunk, dtype=np.int16)
                resampled_data = self.resample_audio(current_audio_np, self.sample_rate, 16000, self.channels)
                all_audio_buffer.append(resampled_data)
        if self.parec_proc:
            self.parec_proc.terminate()
        thread.join(timeout=2.0)
        response.result_text = "No audio recorded."

        if all_audio_buffer:
            final_audio_data_int16 = np.concatenate(all_audio_buffer).astype(np.int16)
            final_wav_path = os.path.join(self.sound_file_directory, "final_output.wav")
            if self._save_buffer_to_wav(final_audio_data_int16, final_wav_path, 16000, 1):
                self.get_logger().info(f"Final audio saved to {final_wav_path}")
            else:
                self.get_logger().warn(f"Failed to save final audio to {final_wav_path}")

            final_audio_data = final_audio_data_int16.astype(np.float32) / 32768.0
            if final_audio_data.size > 0:
                try:
                    prompt_text = " ".join(self.prompt) if self.use_prompt and self.prompt else ""
                    if self.backend == "whisper":
                        result = self.model.transcribe(
                            final_wav_path,
                            language=self.language,
                            task=self.task,
                            initial_prompt=prompt_text if prompt_text else None
                        )
                        text = result.get("text", "")
                    elif self.backend == "faster-whisper":
                        segments, _ = self.model.transcribe(final_wav_path, language=self.language, task=self.task if self.task in ["transcribe", "translate"] else "transcribe", initial_prompt=prompt_text if prompt_text else None)
                        text = " ".join([seg.text for seg in segments]).strip()
                    else:
                        text = ""
                    if not text:
                        response.result_text = "No speech recognized."
                        self.get_logger().warn("No speech recognized.")
                    else:
                        safe_text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                        response.result_text = safe_text
                        self.get_logger().info(f"Final Result: {safe_text}")
                except Exception as e:
                    self.get_logger().error(f"Final recognition error: {e}")
        if not silent:
            threading.Thread(target=self.play_sound, args=('end_sound.mp3',)).start()
        goal_handle.succeed()
        return response
    
    def _cleanup_files(self):
        wip_files = glob.glob(os.path.join(self.sound_file_directory, "*.wav"))
        for f in wip_files:
            try:
                os.remove(f)
                self.get_logger().info(f"Removed old WAV file: {f}")
            except Exception as e:
                self.get_logger().warn(f"Failed to remove WAV file {f}: {e}")
    
    def _save_buffer_to_wav(self, frames, file_path, sample_rate, channels):
        if isinstance(frames, np.ndarray):
            if frames.size == 0:
                self.get_logger().warn("No frames to save.")
                return False
        elif not frames:
            self.get_logger().warn("No frames to save.")
            return False
        
        try:
            if isinstance(frames, list) and len(frames) > 0 and isinstance(frames[0], np.ndarray):
                frames_bytes = b"".join([frame.tobytes() for frame in frames])
            elif isinstance(frames, list) and len(frames) == 1 and isinstance(frames[0], bytes):
                 frames_bytes = frames[0]
            elif isinstance(frames, np.ndarray):
                 frames_bytes = frames.tobytes()
            else:
                self.get_logger().error("Unsupported frames type.")
                return False

            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(frames_bytes)
            return True
        except Exception as e:
            self.get_logger().error(f"Failed to save WAV file: {e}")
            return False    

def main(args=None):
    rclpy.init(args=args)
    whisper_server = WhisperServer()
    executor = MultiThreadedExecutor()
    executor.add_node(whisper_server)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        whisper_server.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()