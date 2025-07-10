import pyaudio
import wave


timeout_sec = 5
channels = 1
sample_rate = 44100
chunk_size = 16000
audio_format = pyaudio.paInt16


# Record audio
audio = pyaudio.PyAudio()
try:
    stream = audio.open(format=audio_format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk_size)
except Exception as e:
    print(f"Audio stream error: {e}")

frames = []
for _ in range(int(sample_rate / chunk_size * timeout_sec)):
    data = stream.read(chunk_size, exception_on_overflow=False)
    frames.append(data)

stream.stop_stream()
stream.close()
audio.terminate()

# Save the recorded audio
with wave.open('output.wav', 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(audio.get_sample_size(audio_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))