import pickle
import requests
import json
import time
import hashlib

class YandexRadio:
    def __init__(self, tag, ui):
        self.api = 'https://radio.yandex.ru/api/v2.0/handlers/'
        self.cookies_file = 'cookies.dat'
        self.ui = ui
        self.tag = tag
        self.gate = self.api + 'radio/' + tag
        self.auth()
        self.radioStarted()

    def auth(self):
        try:
            with open(self.cookies_file, 'r') as f:
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
        with open(self.cookies_file, 'w') as f:
            pickle.dump(self.cookies, f)
