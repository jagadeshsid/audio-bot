import whisper

def transcribe(file_path):
    # Load the model (consider using "tiny" or "base" depending on resource availability)
    model = whisper.load_model("base")

    # Transcribe the audio
    result = model.transcribe(file_path, fp32=True)

    return result['text']

#call transcribe method from main
if __name__ == "__main__":
    transcribe("test.wav")