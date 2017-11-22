import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst as gst
import sys
import time

import signal

class Player:
    def __init__(self):
        gst.init(sys.argv)

        player = gst.ElementFactory.make('playbin', 'player')
        sink = gst.ElementFactory.make('autoaudiosink', 'audio_sink')

        if not sink or not player:
            raise RuntimeError('Could not create GST audio pipeline')

        player.set_property('audio-sink', sink)

        self.player = player

        self.terminate = False
        def sigint(signum, frame):
            self.terminate = True
        signal.signal(signal.SIGINT, sigint)

    def play(self, yar, track, info, batch):
        tid, aid = track
        url = yar.gettrack(tid, aid)
        yar.ui.refresh()
        yar.ui.header(yar.tag)
        yar.ui.title(info[0])
        yar.ui.album(info[1])
        yar.ui.artist(info[2])

        self.player.set_property('uri', url)
        self.player.set_state(gst.State.PLAYING)

        yar.started(tid, aid, batch)

        startTime = time.time()
        bus = self.player.get_bus()
        reason = 'trackFinished'
        while True:
            msg = bus.poll(gst.MessageType.ANY, 100)
            key = yar.ui.poll()

            if self.terminate:
                break

            if key == ord('q') or key == 27:
                self.terminate = True
                break
            if key == ord('d'):
                reason = 'dislike'
                break
            if key in [ord('\n'), ord('n'), ord('s'), ord(' ')]:
                reason = 'skip'
                break
            if key == ord('l'):
                evTime = time.time()
                dur = evTime - startTime
                yar.feedback('like', dur, *track, batch)

            if msg == None:
                continue
            if msg.type == gst.MessageType.EOS or msg.type == gst.MessageType.ERROR:
                break

        self.player.set_state(gst.State.NULL)
        stopTime = time.time()
        dur = stopTime - startTime
        yar.feedback(reason, dur, tid, aid, batch)
