import os
import re
import glob
import time
import whisper
import threading
import subprocess
import asyncio
import wave

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from sobits_interfaces.action import SpeechRecognition
from ament_index_python.packages import get_package_share_directory

from .vad import VadProcessor

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
        self.feedback_rate = 1.5

        self.declare_parameter('model_name', 'small')
        self.declare_parameter('backend', 'whisper')
        self.whisper_model_name = self.get_parameter('model_name').get_parameter_value().string_value
        self.backend = self.get_parameter('backend').get_parameter_value().string_value

        try:
            if self.backend == "whisper":
                import whisper
                self.model = whisper.load_model(self.whisper_model_name)
                self.get_logger().info(f"Whisper model '{self.whisper_model_name}' loaded on {self.model.device}.")
            elif self.backend == "faster-whisper":
                from faster_whisper import WhisperModel
                self.model = WhisperModel(self.whisper_model_name, device="cuda", compute_type="float16")
                self.get_logger().info(f"Faster-Whisper model '{self.whisper_model_name}' loaded.")
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
        except Exception as e:
            self.get_logger().fatal(f"Failed to load {self.backend} model: {e}")
            self.model = None
            return

        self.declare_parameter('language', 'en')
        self.declare_parameter('replace_prompt_whisper', [""])
        self.declare_parameter('task', 'transcribe')
        self.declare_parameter('use_feedback', True)
        self.declare_parameter('use_prompt', False)
        self.declare_parameter('min_wipe_duration', 0.2)

        self.use_feedback_enabled = self.get_parameter('use_feedback').get_parameter_value().bool_value
        self.min_wipe_duration = self.get_parameter('min_wipe_duration').get_parameter_value().double_value

        self.model_wip = None
        self.vad_processor = None
        if self.use_feedback_enabled:
            try:
                if self.backend == "whisper":
                    import whisper   
                    self.model_wip = whisper.load_model(self.whisper_model_name)
                    self.get_logger().info("WIP feedback model loaded.")
                elif self.backend == "faster-whisper":
                    from faster_whisper import WhisperModel
                    self.model_wip = WhisperModel(self.whisper_model_name, device="cuda", compute_type="float16")
                    self.get_logger().info("WIP feedback model loaded (faster-whisper).")
                self.vad_processor = VadProcessor(self)
                self.get_logger().info("VAD model for WIP feedback loaded.")
            except Exception as e:
                self.get_logger().error(f"Failed to load WIP feedback model or VAD model: {e}")
                self.model_wip = None
                self.vad_processor = None
        self.get_logger().info(f"use_feedback: {self.use_feedback_enabled}")

        self.action_server = ActionServer(
            self, SpeechRecognition, "speech_recognition",
            execute_callback=self.speech_to_text,
            callback_group=ReentrantCallbackGroup(),
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )

        self.current_goal_handle = None
        self.async_loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self.loop_thread.start()

        self.wip_thread = None
        self.wip_stop_event = None

        YELLOW = '\033[93m'
        ENDC = '\033[0m'
        self.get_logger().info(f"{YELLOW}Mic: {self.default_audio_source}{ENDC}, Rate: {self.default_sample_rate} Hz, Channels: {self.default_channels}")
        self.get_logger().info(f"{YELLOW}Whisper Server is READY and waiting for requests.{ENDC}")

    def _start_event_loop(self):
        asyncio.set_event_loop(self.async_loop)
        self.async_loop.run_forever()

    def goal_callback(self, goal_request):
        self.get_logger().info('Goal received')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Cancel received')
        if self.wip_stop_event:
            self.wip_stop_event.set()
        return CancelResponse.ACCEPT

    def speech_to_text(self, goal_handle):
        self.language = self.get_parameter('language').get_parameter_value().string_value
        self.prompt = self.get_parameter('replace_prompt_whisper').get_parameter_value().string_array_value
        self.task = self.get_parameter('task').get_parameter_value().string_value
        self.use_prompt = self.get_parameter('use_prompt').get_parameter_value().bool_value

        self.wip_stop_event = threading.Event()

        if self.use_feedback_enabled and self.model_wip is not None:
            self.wip_thread = threading.Thread(target=self._wip_feedback_worker,
                                               args=(self.wip_stop_event, goal_handle), daemon=True)
            self.wip_thread.start()
        else:
            self.wip_thread = None

        future = asyncio.run_coroutine_threadsafe(self._speech_to_text_async(goal_handle), self.async_loop)
        response = future.result()

        self.wip_stop_event.set()
        if self.wip_thread:
            self.wip_thread.join()
        return response

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
        self.feedback_rate = goal_handle.request.feedback_rate
        self.get_logger().info(f"Recording duration: {duration}s, Feedback rate: {self.feedback_rate} Hz")

        self._cleanup_files()

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

            self.ffmpeg_final_proc = subprocess.Popen([
                'ffmpeg',
                '-loglevel', 'quiet',
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

            start_time = time.time()
            while (time.time() - start_time) < (duration + 5):
                if goal_handle.is_cancel_requested:
                    self.get_logger().info("Cancel requested. Aborting recording.")
                    goal_handle.canceled()
                    response.result_text = "Action cancelled by client."
                    return response
                if self.ffmpeg_final_proc.poll() is not None:
                    break
                await asyncio.sleep(0.1)
            else:
                self.get_logger().error("Recording timed out.")
                goal_handle.abort()
                response.result_text = "Recording timed out."
                return response

            goal_handle.succeed()

        except FileNotFoundError as e:
            self.get_logger().error(f"Command not found: {e.filename}")
            goal_handle.abort()
            response.result_text = f"System Error: Command not found ({e.filename})"
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
            if self.backend == "whisper":
                result = self.model.transcribe(
                    self.wav_path,
                    language=self.language,
                    task=self.task,
                    initial_prompt=prompt_text if prompt_text else None
                )
                text = result.get("text", "")
            elif self.backend == "faster-whisper":
                segments, _ = self.model.transcribe(self.wav_path, language=self.language, task=self.task if self.task in ["transcribe", "translate"] else "transcribe", initial_prompt=prompt_text if prompt_text else None)
                text = " ".join([seg.text for seg in segments]).strip()
            else:
                text = ""
                
            if not text:
                self.get_logger().warn("No speech recognized.")
                response.result_text = "No speech recognized."
            else:
                safe_text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                response.result_text = safe_text
                self.get_logger().info(f"Final recognition result: {safe_text}")
        except Exception as e:
            self.get_logger().error(f"Transcription error: {e}")
            goal_handle.abort()
            response.result_text = f"Transcription error: {e}"
            return response

        return response
    
    def _save_buffer_to_wav(self, frames, file_path, sample_rate, channels):
        if not frames:
            return False
        
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b"".join(frames))
        return True

    def _wip_feedback_worker(self, stop_event, goal_handle):
        if not self.model_wip or not self.vad_processor:
            self.get_logger().info("WIP feedback model not loaded or feedback disabled, skipping WIP thread.")
            return

        self.get_logger().info("WIP feedback thread started.")
        
        fifo_wip = os.path.join(self.sound_file_directory, "audio_fifo_wip")

        self.get_logger().info(f"Waiting for FIFO file to be created: {fifo_wip}")
        for _ in range(200):
            if os.path.exists(fifo_wip):
                break
            time.sleep(0.05)
        else:
            self.get_logger().error(f"Timed out waiting for FIFO file: {fifo_wip}")
            stop_event.set()
            return

        hop_size, vad_chunk_size_bytes = self.vad_processor.get_hop_size()
        
        audio_buffer = []
        is_speaking = False
        
        ffmpeg_resample_proc = None
        try:
            ffmpeg_resample_proc = subprocess.Popen(
                [
                    'ffmpeg',
                    '-f', self.raw_audio_format,
                    '-ar', str(self.raw_audio_rate),
                    '-ac', str(self.raw_audio_channels),
                    '-i', fifo_wip,
                    '-f', 's16le',
                    '-acodec', 'pcm_s16le',
                    '-ar', str(self.whisper_wav_rate),
                    '-ac', '1',
                    '-'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            self.get_logger().info("Starting to read from WIP FIFO for VAD.")
            while not stop_event.is_set():
                resampled_data = ffmpeg_resample_proc.stdout.read(vad_chunk_size_bytes)
                if not resampled_data:
                    time.sleep(0.01)
                    continue

                is_voice = self.vad_processor.vad_processor(resampled_data, self.feedback_rate)

                if is_voice:
                    if not is_speaking:
                        is_speaking = True
                        audio_buffer = []
                    audio_buffer.append(resampled_data)
                else:
                    if is_speaking:
                        is_speaking = False
                        
                        duration_sec = len(audio_buffer) * hop_size / self.whisper_wav_rate
                        if duration_sec < self.min_wipe_duration:
                            audio_buffer = []
                            continue

                        temp_file = os.path.join(self.sound_file_directory, f"wip_session_{int(time.time())}.wav")
                        if self._save_buffer_to_wav(audio_buffer, temp_file, self.whisper_wav_rate, self.whisper_wav_channels):
                            try:
                                if self.backend == "whisper":
                                    result = self.model_wip.transcribe(
                                        temp_file,
                                        language=self.language,
                                        task=self.task,
                                        initial_prompt=prompt_text if prompt_text else None
                                    )
                                    text = result.get("text", "")
                                elif self.backend == "faster-whisper":
                                    segments, _ = self.model_wip.transcribe(
                                        temp_file,
                                        language=self.language,
                                        task=self.task if self.task in ["transcribe", "translate"] else "transcribe",
                                        initial_prompt=prompt_text if prompt_text else None
                                    )
                                    text = " ".join([seg.text for seg in segments]).strip()
                                else:
                                    text = ""
                                if text and goal_handle.is_active:
                                    feedback = SpeechRecognition.Feedback()
                                    feedback.addition_text = text
                                    goal_handle.publish_feedback(feedback)
                                    self.get_logger().info(f"WIP feedback published: '{text}'")
                                
                            except Exception as e:
                                self.get_logger().warn(f"WIP recognition error: {e}")
                            finally:
                                audio_buffer = []
        except Exception as e:
            self.get_logger().error(f"Fatal error in WIP feedback worker: {e}")
            stop_event.set()
        finally:
            if ffmpeg_resample_proc:
                ffmpeg_resample_proc.terminate()
                ffmpeg_resample_proc.wait()
            
        self.get_logger().info("WIP feedback thread stopped.")
        
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
        wip_files = glob.glob(os.path.join(self.sound_file_directory, "wip_session_*.wav"))
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
        for proc in [getattr(self, attr) for attr in ['parec_proc', 'tee_proc', 'ffmpeg_final_proc'] if hasattr(self, attr)]:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
                proc.wait(timeout=3)

def main(args=None):
    rclpy.init(args=args)
    whisper_server = WhisperServer()
    executor = MultiThreadedExecutor()
    executor.add_node(whisper_server)
    try:
        executor.spin()
    finally:
        whisper_server.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
