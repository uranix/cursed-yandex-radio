# cursed-yandex-radio
A simple Yandex Radio client with minimalistic curses-based text interface

### USAGE
`$ python cursedyar.py <tag>`
where `tag` is like `genre/rock`, `mood/calm`, `activity/party`, etc.

Should work both under python2 and python3.

Requires `pygst` v1.0 with mp3 decoder and http source plugins (for Debian/Ubuntu `python-gst1.0` (or `python3-gst1.0`), `gstreamer1.0-plugins-good`).
