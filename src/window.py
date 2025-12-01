import sys
import os
import subprocess
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QVBoxLayout, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QRect, QSize, QVariantAnimation
from PySide6.QtGui import QPixmap, QTransform, QPainter, QColor, QAction, QCursor, QIcon, QFont

from .threads import MusicMonitorThread, ArtWorker

class VinylWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.setFixedSize(300, 300)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # State
        self.current_song = None
        self.current_artist = None
        self.player_status = "stopped"
        self.rotation_angle = 0
        self.is_dragging = False
        self.drag_position = QPoint()
        self.is_hovering = False
        
        # Assets Paths
        self.assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        self.base_path = os.path.join(self.assets_dir, 'turntable_base.png')
        self.tonearm_path = os.path.join(self.assets_dir, 'tonearm.png')
        self.default_art_path = os.path.join(self.assets_dir, 'default_art.png')
        
        # Load Assets
        self.base_pixmap = QPixmap(self.base_path).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation) if os.path.exists(self.base_path) else QPixmap(300, 300)
        self.tonearm_pixmap = QPixmap(self.tonearm_path).scaled(80, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation) if os.path.exists(self.tonearm_path) else QPixmap(80, 200)
        self.default_pixmap = QPixmap(self.default_art_path).scaled(190, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation) if os.path.exists(self.default_art_path) else QPixmap(190, 190)
        self.current_record_pixmap = self.default_pixmap
        
        # Threads
        self.music_thread = MusicMonitorThread()
        self.music_thread.track_changed.connect(self.on_track_changed)
        self.music_thread.status_changed.connect(self.on_status_changed)
        self.music_thread.start()
        
        self.art_worker = ArtWorker()
        self.art_worker.art_ready.connect(self.on_art_ready)
        
        # Animation Timer (Record Spinning)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.spin_record)
        
        # Tonearm Animation
        self.tonearm_angle = 0
        self.tonearm_anim = QVariantAnimation(self)
        self.tonearm_anim.setDuration(1000)
        self.tonearm_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.tonearm_anim.valueChanged.connect(self.update_tonearm_angle)
        
        # UI Elements (Controls)
        self.init_controls()

    def init_controls(self):
        # Controls Overlay (Hidden by default)
        self.controls_widget = QWidget(self)
        self.controls_widget.setGeometry(0, 0, 300, 300)
        self.controls_widget.setStyleSheet("background-color: rgba(0, 0, 0, 100); border-radius: 20px;")
        self.controls_widget.hide()

        layout = QVBoxLayout(self.controls_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Top Bar (Window Controls)
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignRight)
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2); 
                color: white; 
                border-radius: 12px; 
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5F56;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)
        
        layout.addStretch()
        
        # Playback Controls
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)
        
        prev_btn = QPushButton("⏮")
        prev_btn.setFixedSize(40, 40)
        prev_btn.setStyleSheet("color: white; font-size: 20px; background: transparent; border: none;")
        prev_btn.setCursor(Qt.PointingHandCursor)
        prev_btn.clicked.connect(lambda: self.control_media("previous track"))
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(50, 50)
        self.play_btn.setStyleSheet("color: white; font-size: 30px; background: transparent; border: 2px solid white; border-radius: 25px;")
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.toggle_play)
        
        next_btn = QPushButton("⏭")
        next_btn.setFixedSize(40, 40)
        next_btn.setStyleSheet("color: white; font-size: 20px; background: transparent; border: none;")
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(lambda: self.control_media("next track"))
        
        controls_layout.addWidget(prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(next_btn)
        
        layout.addLayout(controls_layout)
        layout.addStretch()

    # Paint Event - The Core Rendering Loop
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 1. Draw Base
        painter.drawPixmap(0, 0, self.base_pixmap)
        
        # 2. Draw Record (Rotated)
        painter.save()
        center_x, center_y = 150, 150
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        painter.translate(-center_x, -center_y)
        
        # Center the record (190x190)
        record_x = (300 - 190) // 2
        record_y = (300 - 190) // 2
        painter.drawPixmap(record_x, record_y, self.current_record_pixmap)
        painter.restore()
        
        # 3. Draw Tonearm (Rotated)
        painter.save()
        # Tonearm pivot point logic
        # The tonearm image is 80x200. We place it at (210, 20).
        # Pivot is roughly at (60, 20) relative to the image top-left.
        tonearm_x, tonearm_y = 210, 20
        pivot_x = tonearm_x + 60
        pivot_y = tonearm_y + 20
        
        painter.translate(pivot_x, pivot_y)
        painter.rotate(self.tonearm_angle)
        painter.translate(-pivot_x, -pivot_y)
        
        painter.drawPixmap(tonearm_x, tonearm_y, self.tonearm_pixmap)
        painter.restore()

    # Hover Events
    def enterEvent(self, event):
        self.is_hovering = True
        self.controls_widget.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovering = False
        self.controls_widget.hide()
        super().leaveEvent(event)

    # Thread Slots
    def on_track_changed(self, info):
        self.current_song = info['song']
        self.current_artist = info['artist']
        self.art_worker.fetch(info['artist'], info['song']) # Fetch by song now
        
    def on_status_changed(self, status):
        self.player_status = status
        if status == 'playing':
            self.start_playing()
            self.play_btn.setText("❚❚")
        else:
            self.stop_playing()
            self.play_btn.setText("▶")

    def on_art_ready(self, pixmap):
        self.current_record_pixmap = pixmap.scaled(190, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.update() # Trigger repaint

    # Animation Logic
    def start_playing(self):
        self.tonearm_anim.stop()
        self.tonearm_anim.setStartValue(self.tonearm_angle)
        self.tonearm_anim.setEndValue(25)
        self.tonearm_anim.start()
        self.animation_timer.start(16) # ~60 FPS for smoothness

    def stop_playing(self):
        self.tonearm_anim.stop()
        self.tonearm_anim.setStartValue(self.tonearm_angle)
        self.tonearm_anim.setEndValue(0)
        self.tonearm_anim.start()
        self.animation_timer.stop()

    def update_tonearm_angle(self, angle):
        self.tonearm_angle = angle
        self.update()

    def spin_record(self):
        self.rotation_angle = (self.rotation_angle + 1) % 360 # Slower, smoother spin
        self.update()

    # Media Control
    def control_media(self, command):
        script = f"""
        if application "Spotify" is running then
            tell application "Spotify" to {command}
        else
            if application "Music" is running then
                tell application "Music" to {command}
            end if
        end if
        """
        subprocess.run(['osascript', '-e', script])

    def toggle_play(self):
        self.control_media("playpause")

    # Volume Control (Scroll)
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            # Volume Up
            subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 5)'])
        else:
            # Volume Down
            subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 5)'])
        event.accept()

    # Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_dragging = False

    def closeEvent(self, event):
        self.music_thread.stop()
        self.music_thread.wait()
        self.art_worker.quit()
        self.art_worker.wait()
        QApplication.quit() # Ensure full quit
        event.accept()
