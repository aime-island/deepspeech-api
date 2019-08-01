import sys
import queue
import json

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import Data

from utils.parse import process_file
from utils.transcribe import transcribe
from utils.model import create_model
from utils.thread_with_trace import thread_with_trace

from streaming.audiobuffer import AudioBuffer
from streaming.transcriber import StreamTranscriber

from config import path, \
    settings

ds = create_model(path, settings)


class Model(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def onMessage(self, payload, isBinary):
        deep_config = json.loads(payload)
        global ds
        ds = create_model(path, deep_config)


class Transcribe(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def onMessage(self, payload, isBinary):
        recording = process_file(payload)
        transcript = transcribe(ds, recording)
        self.sendMessage(bytes(transcript, 'utf8'))


class Stream(WebSocketServerProtocol):

    def sendTranscripts(self, transcripts):
        while(True):
            ts = transcripts.get()
            payload = json.dumps(ts, ensure_ascii=False).encode('utf8')
            self.sendMessage(payload)

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        self.buffer_queue = queue.Queue()
        self.transcript_queue = queue.Queue()

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        self.transcript_queue = None
        self.buffer_queue = None
        self.ab = None
        self.stream = None
        self.run_stream.kill()
        self.send_transcripts.kill()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            settings = json.loads(payload)
            input_rate = settings['sample_rate']
            aggressiveness = settings['aggressiveness']
            self.ab = AudioBuffer(
                buffer_queue=self.buffer_queue,
                input_rate=input_rate)
            self.stream = StreamTranscriber(
                aggressiveness=aggressiveness,
                model=ds)
            self.run_stream = thread_with_trace(
                target=self.stream.run,
                args=(self.buffer_queue, self.transcript_queue, ))
            self.send_transcripts = thread_with_trace(
                target=self.sendTranscripts,
                args=(self.transcript_queue, ))
            self.run_stream.start()
            self.send_transcripts.start()
        else:
            self.ab.insert(payload)


if __name__ == '__main__':

    log.startLogging(sys.stdout)

    transcribeFactory = WebSocketServerFactory()
    transcribeFactory.protocol = Transcribe
    transcribeFactory.startFactory()
    tResource = WebSocketResource(transcribeFactory)

    streamFactory = WebSocketServerFactory()
    streamFactory.protocol = Stream
    streamFactory.startFactory()
    sResource = WebSocketResource(streamFactory)

    modelFactory = WebSocketServerFactory()
    modelFactory.protocol = Model
    modelFactory.startFactory()
    mResource = WebSocketResource(modelFactory)

    # Establish a dummy root resource
    root = Data("", "text/plain")
    root.putChild(b"transcribe", tResource)
    root.putChild(b"stream", sResource)
    root.putChild(b"model", mResource)

    # both under one Twisted Web Site
    site = Site(root)
    reactor.listenTCP(9000, site)

    reactor.run()
