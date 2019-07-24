import collections
import webrtcvad
import numpy as np
import wave
import os
from datetime import datetime


class StreamTranscriber(object):

    def __init__(self, aggressiveness, model):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.model = model
        self.frame_duration_ms = 30
        self.sample_rate = 16000
        self.running = False

    def generate_frames(self):
        while True:
            yield self.buffer_queue.get()

    """ def write_wav(self, filename, data):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close() """

    def voice_detection(self, padding_ms=300, ratio=0.75, frames=None):
        if frames is None:
            frames = self.generate_frames()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            is_speech = self.vad.is_speech(frame, self.sample_rate)
            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, _ in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len(
                    [f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

    def run(self, buffer_queue, transcript_queue):
        print("started")
        self.buffer_queue = buffer_queue
        self.running = True
        frames = self.voice_detection()
        sctxt = self.model.setupStream()
        # wav_data = bytearray()
        for frame in frames:
            if frame is not None:
                self.model.feedAudioContent(
                    sctxt, np.frombuffer(frame, np.int16))
                # wav_data.extend(frame)
            else:
                text = self.model.finishStream(sctxt)
                print('transcript:', text)
                """ self.write_wav(
                    os.path.join('./tmp',
                    datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")),
                    wav_data) """
                # wav_data = bytearray()
                transcript_queue.put(bytes(text, 'utf8'))
                sctxt = self.model.setupStream()
