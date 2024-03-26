import pyaudio
import wave


output_filename = "../sound_file/output.wav"  # 保存するファイル名
record_seconds = 5              # 録音する秒数(Serviceの引数にしたい)
sample_rate=44100
chunk_size=1024
channels=1
audio_format=pyaudio.paInt16

audio = pyaudio.PyAudio()


## 録音開始
stream = audio.open(format=audio_format,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk_size)

frames = []

for i in range(0, int(sample_rate / chunk_size * record_seconds) + 1):
    data = stream.read(chunk_size)
    frames.append(data)
## 録音終了

stream.stop_stream()
stream.close()
audio.terminate()

## 音声ファイルの書き出し
wf = wave.open(output_filename, 'wb')
wf.setnchannels(channels)
wf.setsampwidth(audio.get_sample_size(audio_format))
wf.setframerate(sample_rate)
wf.writeframes(b''.join(frames))
wf.close()
