import pygst
pygst.require('0.10')
import gst
import time

class Player:
    def __init__(self):
        self.player = gst.element_factory_make('playbin', 'player')
        alsa = gst.element_factory_make('alsasink', 'cardname0')
        self.player.set_property('audio-sink', alsa)

    def play(self, yar, track, info):
        global terminate

        url = yar.gettrack(*track)
        yar.ui.refresh()
        yar.ui.header(yar.tag)
        yar.ui.title(info[0])
        yar.ui.album(info[1])
        yar.ui.artist(info[2])

        reason = 'trackFinished'
        url = url.replace('https://', 'http://')
        self.player.set_property('uri', url)
        self.player.set_state(gst.STATE_PLAYING)
        yar.started(*track)

        startTime = time.time()
        bus = self.player.get_bus()
        while True:
            msg = bus.poll(gst.MESSAGE_ANY, 100)
            key = yar.ui.poll()

            if terminate:
                break

            if key == ord('q') or key == 27:
                terminate = True
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
                yar.feedback('like', dur, *track)

            if msg == None:
                continue
            if msg.type == gst.MESSAGE_EOS or msg.type == gst.MESSAGE_ERROR:
                break

        self.player.set_state(gst.STATE_NULL)
        stopTime = time.time()
        dur = stopTime - startTime
        yar.feedback(reason, dur, *track)
