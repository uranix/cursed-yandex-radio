import time

import sys

class UserInterface:
    HEADER=0
    TITLE=2
    ALBUM=3
    ARTIST=4
    STATUS=6
    FEEDBACK=7
    ERRORS=8
    HELP=10

    def __init__(self, wnd):
        self.wnd = wnd
        wnd.timeout(0)

    def poll(self):
        return self.wnd.getch()
    def refresh(self):
        self.put(UserInterface.HELP, 'q,Esc,^C: quit, n,s,Enter,Space: skip, l:like, d:dislike and skip')
    def header(self, info):
        self.put(UserInterface.HEADER, 'Now playing: ' + info)
    def title(self, info):
        self.put(UserInterface.TITLE, 'Title: ' + info)
    def album(self, info):
        self.put(UserInterface.ALBUM, 'Album: ' + info)
    def artist(self, info):
        self.put(UserInterface.ARTIST, 'Artist: ' + info)
    def status(self, info):
        with open('status.log', 'a') as f:
            if sys.version_info[0] < 3: info = info.encode('utf-8')
            f.write(time.strftime('[%d %b %Y %H:%M:%S] ', time.localtime()) + info + '\n')
        self.put(UserInterface.STATUS, 'Status: ' + info)
    def feedback(self, info):
        with open('feedback.log', 'a') as f:
            if sys.version_info[0] < 3: info = info.encode('utf-8')
            f.write(time.strftime('[%d %b %Y %H:%M:%S] ', time.localtime()) + info + '\n')
        self.put(UserInterface.FEEDBACK, 'Feedback status: ' + info)
    def error(self, info):
        with open('error.log', 'a') as f:
            if sys.version_info[0] < 3: info = info.encode('utf-8')
            f.write(time.strftime('[%d %b %Y %H:%M:%S] ', time.localtime()) + info + '\n')
        self.put(UserInterface.ERRORS, 'Error: ' + info)
    def put(self, line, info):
        my, mx = self.wnd.getmaxyx()
        strlen = len(info)
        pad = mx - strlen
        padl = pad // 2

        if sys.version_info[0] < 3: info = info.encode('utf-8')

        self.wnd.addstr(line, 0, ' '*padl + info + ' '*(pad - padl))
