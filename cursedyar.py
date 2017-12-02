#!/usr/bin/env python3

from __future__ import absolute_import

import sys
import curses
import locale

from ui import UserInterface
from client import YandexRadio
from player import Player

def main(wnd):
    global terminate
    if len(sys.argv) > 1:
        tag = sys.argv[1]
    else:
        tag = 'activity/work-background'
    ui = UserInterface(wnd)
    yar = YandexRadio(tag, ui)
    pl = Player()

    lastplayed = None
    queue = []
    while not pl.terminate:
        if len(queue) == 0:
            queue = yar.gettracks(lastplayed)

        curtrack = queue[0]
        queue = queue[1:]
        info = curtrack[2]
        # dur = curtrack[3]
        batch = curtrack[4]
        curtrack = curtrack[:2]
        pl.play(yar, curtrack, info, batch)
        lastplayed = curtrack
    yar.save_cookies()

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(main)
