import whisper
from faster_whisper import WhisperModel

# Pre-download OpenAI Whisper model
whisper_model = whisper.load_model("small")

# Pre-download Faster-Whisper model
faster_model = WhisperModel("small", device="cuda", compute_type="float16")


# Available Whisper models:
# tiny, base, small, medium, large,large-v1, large-v2, large-v3, large-v3-turbo

# Available Faster-Whisper models (as of now):
# tiny, base, small, medium, large,large-v1, large-v2, large-v3
