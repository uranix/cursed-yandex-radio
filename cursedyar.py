#!/usr/bin/env python2.7

import json
import requests
import time
import hashlib
import random
import pygst
pygst.require('0.10')
import gst
import gobject, sys
import signal
import pickle
import curses
import locale

terminate = False

def sigint(signal, frame):
    global terminate
    terminate = True

class UserInterface:
    HEADER=1
    TITLE=3
    ALBUM=4
    ARTIST=5
    STATUS=7
    FEEDBACK=8
    ERRORS=9

    def __init__(self, wnd):
        self.wnd = wnd
        wnd.border(0)
        wnd.timeout(0)

    def poll(self):
        return self.wnd.getch()
    def refresh(self):
        pass
    def header(self, info):
        self.put(UserInterface.HEADER, 'Now playing: ' + info)
    def title(self, info):
        self.put(UserInterface.TITLE, 'Title: ' + info)
    def album(self, info):
        self.put(UserInterface.ALBUM, 'Album: ' + info)
    def artist(self, info):
        self.put(UserInterface.ARTIST, 'Artist: ' + info)
    def status(self, info):
        self.put(UserInterface.STATUS, 'Status: ' + info)
    def feedback(self, info):
        self.put(UserInterface.FEEDBACK, 'Feedback status: ' + info)
    def error(self, info):
        self.put(UserInterface.ERRORS, 'Error: ' + info)
    def put(self, line, info):
        my, mx = self.wnd.getmaxyx()
        strlen = len(info)
        self.wnd.addstr(line, 1, info.encode('utf-8') + ' '*(mx-strlen-2))

class YandexRadio:
    def __init__(self, tag, ui):
        self.api = 'https://radio.yandex.ru/api/v2.0/handlers/'
        self.ui = ui
        self.tag = tag
        self.gate = self.api + 'radio/' + tag
        self.auth()
        self.radioStarted()

    def auth(self):
        try:
            with open('cookies.dat', 'r') as f:
                self.cookies = pickle.load(f)
        except:
            self.cookies = {}
        url = self.api + 'auth'
        resp = requests.get(url, cookies=self.cookies)
        self.ui.status('Auth')
        authdata = json.loads(resp.text)
        if len(self.cookies) == 0:
            self.cookies = resp.cookies
        yaplid = repr(time.time() * 1e4)
        self.cookies['device_id'] = '"' + authdata['device_id'] + '"'
        self.cookies['Ya_Music_Player_ID'] = yaplid
        self.sign = authdata['csrf']

    def radioStarted(self):
        url = self.gate + '/feedback/radioStarted'
        r = requests.post(url, data={'sign' : self.sign}, cookies=self.cookies)
        self.ui.status('Post radioStarted')
        if r.status_code != 202:
            self.ui.error('radioStarted: ' + r.text)

    def hashify(self, s):
        return hashlib.md5('XGRlBW9FXlekgbPrRHuSiA' + s.replace('\r\n', '\n')).hexdigest();

    def gettrack(self, tid, aid):
        url = self.api + 'track/%d:%d/download/m?hq=0' % (tid, aid)
        resp = requests.get(url, cookies=self.cookies)
        self.ui.status('Ask for download')
        meta = json.loads(resp.text)
        src = meta['src'] + '&format=json'
        resp = requests.get(src, cookies=self.cookies)
        self.ui.status('Get track url')
        d = json.loads(resp.text)
        n = self.hashify(d['path'][1:] + d['s'])
        path = 'https://' + d['host'] + '/get-' + meta['codec'] + '/' + \
            n + '/' + d['ts'] + \
            d['path'] + '?track-id=' + str(tid) + '&play=false&'
        return path

    def started(self, tid, aid):
        url = self.gate + '/feedback/trackStarted'
        r = requests.post(url, data={'trackId' : '%d:%d' % (tid, aid), 'sign' : self.sign}, cookies=self.cookies)
        self.ui.status('Post trackStarted')
        if r.status_code != 202:
            self.ui.error('trackStarted: ' + r.text)

    def feedback(self, reason, dur, tid, aid):
        url = self.gate + '/feedback/' + reason
        r = requests.post(url, data={'trackId' : '%d:%d' % (tid, aid), 'totalPlayed' : str(dur),'sign' : self.sign}, cookies=self.cookies)
        self.ui.feedback(reason + ' totalPlayed = ' + str(dur) + 's')
        self.ui.status('Post feedback')
        if r.status_code != 202:
            self.ui.error(reason + ': ' + r.text)

    def gettracks(self, prev = None):
        url = self.gate + '/tracks'
        params = {}
        if prev != None:
            params['queue[]'] = '%d:%d' % prev
        resp = requests.get(url, params=params, cookies=self.cookies)
        self.ui.status('Get queue')
        if resp.status_code != 200:
            self.ui.put(8, 'tracks: ' + resp.text)
        d = json.loads(resp.text)
        tracks = []
        for z in d['tracks']:
            if z['type'] != 'track':
                continue
            track = z['track']
            album = track['albums'][0]
            artists = ', '.join([x['name'] for x in track['artists']])
            tid = int(track['id'])
            aid = int(album['id'])
            dur = track['durationMs']
            info = (track['title'], album['title'], artists)
            tracks.append((tid, aid, info, dur));
        return tracks

    def save_cookies(self):
        with open('cookies.dat', 'w') as f:
            pickle.dump(self.cookies, f)

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
            if key == ord('\n') or key == ord('n') or key == ord('s'):
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
        dur = curtrack[3]
        curtrack = curtrack[:2]
        pl.play(yar, curtrack, info)
    yar.save_cookies()

if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    curses.wrapper(main)
