#!/usr/bin/env python

from __future__ import absolute_import

import sys
import signal
import curses
import locale

from ui import UserInterface
from client import YandexRadio
from player import Player

terminate = False

def sigint(signal, frame):
    global terminate
    terminate = True

def main(wnd):
    global terminate
    if len(sys.argv) > 1:
        tag = sys.argv[1]
    else:
        tag = 'activity/work-background'
    ui = UserInterface(wnd)
    yar = YandexRadio(tag, ui)
    pl = Player()
    signal.signal(signal.SIGINT, sigint)

    lastplayed = None
    while not terminate:
        queue = yar.gettracks(lastplayed)
        curtrack = queue[0]
        info = curtrack[2]
        # dur = curtrack[3]
        curtrack = curtrack[:2]
        pl.play(yar, curtrack, info)
    yar.save_cookies()

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(main)
