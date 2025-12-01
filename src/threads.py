from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
from PySide6.QtGui import QPixmap
from .music_monitor import get_current_track_info
from .art_handler import fetch_album_art, process_art_to_circle
import time

class MusicMonitorThread(QThread):
    track_changed = Signal(dict)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        last_info = {}
        while self.running:
            info = get_current_track_info()
            
            # Emit status change if it changed
            if info.get('status') != last_info.get('status'):
                self.status_changed.emit(info['status'])
            
            # Emit track change if song/artist changed
            if info.get('song') != last_info.get('song') or info.get('artist') != last_info.get('artist'):
                self.track_changed.emit(info)
            
            last_info = info
            time.sleep(1) # Check every second

    def stop(self):
        self.running = False
        self.wait()

class ArtWorker(QThread):
    art_ready = Signal(QPixmap)

    def __init__(self):
        super().__init__()
        self.artist = None
        self.album = None

    def fetch(self, artist, album):
        self.artist = artist
        self.album = album
        self.start()

    def run(self):
        if not self.artist or not self.album:
            return
            
        art_url = fetch_album_art(self.artist, self.album)
        if art_url:
            pixmap = process_art_to_circle(art_url)
            if pixmap:
                self.art_ready.emit(pixmap)
