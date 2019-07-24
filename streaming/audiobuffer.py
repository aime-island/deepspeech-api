import numpy as np
from scipy import signal


class AudioBuffer(object):

    def __init__(self, buffer_queue=None, input_rate=None):
        self.buffer = buffer_queue
        self.input_rate = input_rate
        self.sample_rate = 16000
        self.frame_duration = 30
        self.inner_buffer = bytearray()

    def insert(self, data):
        if self.input_rate == self.sample_rate:
            self.chunker(bytearray(data))
        else:
            data = self.resample(data)
            self.chunker(bytearray(data))

    def chunker(self, audio):
        if (self.inner_buffer):
            buf = self.inner_buffer
            audio = buf + audio
            del self.inner_buffer
            self.inner_buffer = bytearray()
        chunk_size = int(self.sample_rate * (self.frame_duration / 1000) * 2)
        while (audio):
            if (len(audio) > chunk_size):
                self.buffer.put(bytes(audio[:chunk_size]))
                del audio[:chunk_size]
            else:
                # offset = chunk_size - len(audio)
                # silence = b'\x00' * offset
                # audio += silence
                # self.buffer.put(bytes(audio))
                # break
                self.inner_buffer.extend(audio)
                break

    def resample(self, data):
        data16 = np.fromstring(string=data, dtype=np.int16)
        resample_size = int(len(data16) / self.input_rate * self.sample_rate)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tostring()
