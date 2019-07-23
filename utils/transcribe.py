import scipy.io.wavfile as wav
import os


def transcribe(ds, filename):
    print("Starting transcription...")
    fs, audio = wav.read(os.path.join('./tmp', filename))
    transcript = ds.stt(audio, fs)
    os.remove(os.path.join('./tmp', filename))
    print("Transcribed: ", transcript)
    return transcript
