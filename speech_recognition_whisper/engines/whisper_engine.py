import os
import torch
import traceback
import time
from .base_engine import BaseEngine

class WhisperEngine(BaseEngine):
    def __init__(self, node):
        super().__init__(node)
        self.node.declare_parameter('backend', 'whisper')
        self.node.declare_parameter('model_name', 'small')
        self.node.declare_parameter('compute_type', 'float16')
        self.node.declare_parameter('device', '')
        self.node.declare_parameter('language', 'ja')
        self.node.declare_parameter('task', 'transcribe')
        self.node.declare_parameter('use_prompt', False)
        self.node.declare_parameter('replace_prompt_whisper', [""])

        self.backend = self.node.get_parameter('backend').value
        self.model_name = self.node.get_parameter('model_name').value
        self.compute_type = self.node.get_parameter('compute_type').value
        self.device_pref = self.node.get_parameter('device').value
        
        self.is_streamable = False
        
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            device_str = self.device_pref if self.device_pref else ("cuda:0" if torch.cuda.is_available() else "cpu")

            if self.backend == "whisper":
                import whisper
                self.model = whisper.load_model(self.model_name, device=device_str)
                self.logger.info(f"[{self.backend}] Model '{self.model_name}' loaded on {device_str}")
            
            elif self.backend == "faster-whisper":
                from faster_whisper import WhisperModel
                self.model = WhisperModel(self.model_name, device=device_str, compute_type=self.compute_type)
                self.logger.info(f"[{self.backend}] Model '{self.model_name}' loaded on {device_str}")

        except Exception as e:
            self.logger.fatal(f"Failed to load Whisper model: {e}\n{traceback.format_exc()}")
            raise e

    def transcribe(self, audio_path):
        if self.model is None:
            return "Error: Model not loaded"

        language = self.node.get_parameter('language').value
        task = self.node.get_parameter('task').value
        use_prompt = self.node.get_parameter('use_prompt').value
        prompt_list = self.node.get_parameter('replace_prompt_whisper').value
        prompt_text = " ".join(prompt_list) if use_prompt else ""

        try:
            if self.backend == "whisper":
                result = self.model.transcribe(
                    audio_path,
                    language=language,
                    task=task,
                    initial_prompt=prompt_text if prompt_text else None
                )
                return result.get("text", "").strip()
            
            elif self.backend == "faster-whisper":
                segments, _ = self.model.transcribe(
                    audio_path,
                    language=language,
                    task=task,
                    initial_prompt=prompt_text if prompt_text else None
                )
                return " ".join([s.text for s in segments]).strip()

        except Exception as e:
            self.logger.error(f"Transcription error: {e}\n{traceback.format_exc()}")
            return ""