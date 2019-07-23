import uuid
import ffmpeg
import os
from io import BytesIO
import soundfile as sf


def process_file(file):
    if not os.path.exists('./tmp'):
        os.makedirs('./tmp')
    data, samplerate = sf.read(BytesIO(file))
    fileLocation = os.path.join('./tmp', str(uuid.uuid4()) + '.wav')
    sf.write(fileLocation, data, samplerate)
    convertedFile = normalize_file(fileLocation)
    os.remove(fileLocation)
    return convertedFile


def normalize_file(file):
    filename = str(uuid.uuid4()) + ".wav"
    loc = os.path.join('./tmp', filename)
    stream = ffmpeg.input(file)
    stream = ffmpeg.output(stream, loc, acodec='pcm_s16le', ac=1, ar='16k')
    ffmpeg.run(stream)
    return filename
