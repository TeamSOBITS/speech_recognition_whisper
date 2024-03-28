import whisper

## modelのダウンロード
model = whisper.load_model("small")

## モデルを通して音声ファイルを通す
result = model.transcribe("../sound_file/output.wav")

## これが文字起こし(Serviceの戻り値にしたい)
print(result["text"])