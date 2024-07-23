import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QFileDialog, QSlider, QTreeWidget,
                             QTreeWidgetItem, QLineEdit, QTabWidget)
from PyQt5.QtGui import QPixmap, QPalette, QColor
from PyQt5.QtCore import Qt, QTimer
import pygame
import os
import random
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.wave import WAVE
from mutagen.id3 import ID3
from collections import defaultdict
from pypresence import Presence

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lucasify")
        self.setGeometry(100, 100, 1200, 800)

        pygame.mixer.init()

        self.music_files = []
        self.music_by_genre = defaultdict(list)
        self.music_by_artist = defaultdict(list)
        self.current_album_cover = None
        self.current_song_index = -1
        self.is_repeating = False
        self.is_shuffling = False

        self.initUI()
        self.init_discord_rpc()

        print('''

 _     _     ____  ____  ____  _  ________  _
/ \   / \ /\/   _\/  _ \/ ___\/ \/    /\  \//
| |   | | |||  /  | / \||    \| ||  __\ \  / 
| |_/\| \_/||  \_ | |-||\___ || || |    / /  
\____/\____/\____/\_/ \|\____/\_/\_/   /_/   

                
''')
        print("================================")
        print("Made in Python by NevrLoose, V1")
        print("================================")
        print("Console Errors")

    def initUI(self):
        self.setStyleSheet("background-color: #1E1E1E; color: #FFFFFF;")
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout, 8)

        nav_layout = QVBoxLayout()
        top_layout.addLayout(nav_layout, 1)

        home_button = QPushButton("Home")
        home_button.setStyleSheet(self.button_style())
        home_button.clicked.connect(self.show_home)
        nav_layout.addWidget(home_button)

        library_button = QPushButton("Library")
        library_button.setStyleSheet(self.button_style())
        library_button.clicked.connect(self.show_library)
        nav_layout.addWidget(library_button)

        playlists_button = QPushButton("Playlists")
        playlists_button.setStyleSheet(self.button_style())
        playlists_button.clicked.connect(self.show_playlists)
        nav_layout.addWidget(playlists_button)

        settings_button = QPushButton("Settings")
        settings_button.setStyleSheet(self.button_style())
        settings_button.clicked.connect(self.show_settings)
        nav_layout.addWidget(settings_button)

        nav_layout.addStretch(1) 

        self.tab_widget = QTabWidget()
        top_layout.addWidget(self.tab_widget, 4)

        self.home_widget = QWidget()
        self.library_widget = QWidget()
        self.playlists_widget = QWidget()
        self.settings_widget = QWidget()

        self.tab_widget.addTab(self.home_widget, "Home")
        self.tab_widget.addTab(self.library_widget, "Library")
        self.tab_widget.addTab(self.playlists_widget, "Playlists")
        self.tab_widget.addTab(self.settings_widget, "Settings")

        self.setup_home()
        self.setup_library()
        self.setup_playlists()
        self.setup_settings()

        self.show_home()

        bottom_panel = QHBoxLayout()
        main_layout.addLayout(bottom_panel, 1)

        self.album_cover_label = QLabel()
        self.album_cover_label.setFixedSize(64, 64)
        bottom_panel.addWidget(self.album_cover_label)

        self.song_info_label = QLabel("No song playing")
        bottom_panel.addWidget(self.song_info_label)

        control_panel = QHBoxLayout()
        bottom_panel.addLayout(control_panel)

        self.prev_button = QPushButton("⏮")
        self.prev_button.setStyleSheet(self.control_button_style())
        self.prev_button.clicked.connect(self.prev_song)
        control_panel.addWidget(self.prev_button)

        self.play_button = QPushButton("▶️")
        self.play_button.setStyleSheet(self.control_button_style())
        self.play_button.clicked.connect(self.play_music)
        control_panel.addWidget(self.play_button)

        self.pause_button = QPushButton("⏸")
        self.pause_button.setStyleSheet(self.control_button_style())
        self.pause_button.clicked.connect(self.pause_music)
        control_panel.addWidget(self.pause_button)

        self.stop_button = QPushButton("⏹")
        self.stop_button.setStyleSheet(self.control_button_style())
        self.stop_button.clicked.connect(self.stop_music)
        control_panel.addWidget(self.stop_button)

        self.next_button = QPushButton("⏭")
        self.next_button.setStyleSheet(self.control_button_style())
        self.next_button.clicked.connect(self.next_song)
        control_panel.addWidget(self.next_button)

        self.repeat_button = QPushButton("🔁")
        self.repeat_button.setStyleSheet(self.control_button_style())
        self.repeat_button.clicked.connect(self.toggle_repeat)
        control_panel.addWidget(self.repeat_button)

        self.shuffle_button = QPushButton("🔀")
        self.shuffle_button.setStyleSheet(self.control_button_style())
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        control_panel.addWidget(self.shuffle_button)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setStyleSheet("QSlider::groove:horizontal { background: #999; height: 8px; } QSlider::handle:horizontal { background: #eee; width: 14px; }")
        self.volume_slider.valueChanged.connect(self.set_volume)
        bottom_panel.addWidget(self.volume_slider)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.setStyleSheet("QSlider::groove:horizontal { background: #999; height: 8px; } QSlider::handle:horizontal { background: #eee; width: 14px; }")
        self.seek_slider.sliderMoved.connect(self.seek_music)
        bottom_panel.addWidget(self.seek_slider)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_seek_slider)
        self.timer.start(1000)

    def button_style(self):
        return """
        QPushButton {
            background-color: #444444;
            border: none;
            color: white;
            padding: 10px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #666666;
        }
        """

    def control_button_style(self):
        return """
        QPushButton {
            background-color: #444444;
            border: none;
            color: white;
            padding: 10px;
            font-size: 20px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #666666;
        }
        """

    def setup_home(self):
        layout = QVBoxLayout()

        genre_label = QLabel("Genres")
        genre_label.setAlignment(Qt.AlignCenter)
        genre_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(genre_label)

        self.genre_tree = QTreeWidget()
        self.genre_tree.setHeaderHidden(True)
        self.genre_tree.itemDoubleClicked.connect(self.play_selected_item)
        layout.addWidget(self.genre_tree)

        artist_label = QLabel("Artists")
        artist_label.setAlignment(Qt.AlignCenter)
        artist_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(artist_label)

        self.artist_tree = QTreeWidget()
        self.artist_tree.setHeaderHidden(True)
        self.artist_tree.itemDoubleClicked.connect(self.play_selected_item)
        layout.addWidget(self.artist_tree)

        self.home_widget.setLayout(layout)

    def setup_library(self):
        layout = QVBoxLayout()

        browse_button = QPushButton("Browse Folder")
        browse_button.setStyleSheet(self.button_style())
        browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(browse_button)

        self.music_listbox = QListWidget()
        self.music_listbox.setStyleSheet("background-color: #444444; color: white;")
        self.music_listbox.itemSelectionChanged.connect(self.display_album_cover)
        layout.addWidget(self.music_listbox)

        self.library_widget.setLayout(layout)

    def setup_playlists(self):
        layout = QVBoxLayout()

        self.playlist_box = QListWidget()
        layout.addWidget(self.playlist_box)

        playlist_controls = QHBoxLayout()
        layout.addLayout(playlist_controls)

        self.playlist_name_input = QLineEdit()
        self.playlist_name_input.setPlaceholderText("New playlist name")
        playlist_controls.addWidget(self.playlist_name_input)

        add_playlist_button = QPushButton("Add Playlist")
        add_playlist_button.setStyleSheet(self.button_style())
        add_playlist_button.clicked.connect(self.add_playlist)
        playlist_controls.addWidget(add_playlist_button)

        self.playlists_widget.setLayout(layout)

    def setup_settings(self):
        layout = QVBoxLayout()
        self.settings_widget.setLayout(layout)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder_path:
            self.load_music_files(folder_path)

    def load_music_files(self, folder_path):
        self.music_files = []
        self.music_by_genre.clear()
        self.music_by_artist.clear()

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.mp3', '.flac', '.wav')):
                    file_path = os.path.join(root, file)
                    self.music_files.append(file_path)
                    try:
                        if file.endswith('.mp3'):
                            audio = MP3(file_path, ID3=ID3)
                        elif file.endswith('.flac'):
                            audio = FLAC(file_path)
                        elif file.endswith('.wav'):
                            audio = WAVE(file_path)
                        else:
                            continue

                        genre = audio.get('TCON', ['Unknown'])[0]
                        artist = audio.get('TPE1', ['Unknown'])[0]

                        self.music_by_genre[genre].append(file_path)
                        self.music_by_artist[artist].append(file_path)

                    except Exception as e:
                        print("================================")
                        print(f"Error loading {file}: {e}")
                        print("================================")

        self.populate_music_list()
        self.populate_genre_tree()
        self.populate_artist_tree()

    def populate_music_list(self):
        self.music_listbox.clear()
        for file in self.music_files:
            self.music_listbox.addItem(file)

    def populate_genre_tree(self):
        self.genre_tree.clear()
        for genre, files in self.music_by_genre.items():
            genre_item = QTreeWidgetItem([genre])
            for file in files:
                QTreeWidgetItem(genre_item, [file])
            self.genre_tree.addTopLevelItem(genre_item)

    def populate_artist_tree(self):
        self.artist_tree.clear()
        for artist, files in self.music_by_artist.items():
            artist_item = QTreeWidgetItem([artist])
            for file in files:
                QTreeWidgetItem(artist_item, [file])
            self.artist_tree.addTopLevelItem(artist_item)

    def play_selected_item(self, item, column):
        file_path = item.text(0)
        self.play_music_file(file_path)

    def display_album_cover(self):
        selected_items = self.music_listbox.selectedItems()
        if not selected_items:
            self.album_cover_label.clear()
            return

        file_path = selected_items[0].text()
        self.update_album_cover(file_path)

    def update_album_cover(self, file_path):
        try:
            if file_path.endswith('.mp3'):
                audio = MP3(file_path, ID3=ID3)
            elif file_path.endswith('.flac'):
                audio = FLAC(file_path)
            elif file_path.endswith('.wav'):
                audio = WAVE(file_path)
            else:
                return

            if 'APIC:' in audio:
                album_cover_data = audio['APIC:'].data
                pixmap = QPixmap()
                pixmap.loadFromData(album_cover_data)
                self.album_cover_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio))
                self.current_album_cover = pixmap
            else:
                self.album_cover_label.clear()

        except Exception as e:
            print("================================")
            print(f"Error loading album cover for {file_path}: {e}")
            print("================================")
            self.album_cover_label.clear()

    def play_music(self):
        if not self.music_files:
            return

        if self.current_song_index == -1:
            self.current_song_index = 0

        file_path = self.music_files[self.current_song_index]
        self.play_music_file(file_path)

    def play_music_file(self, file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        self.song_info_label.setText(file_path)

        audio = MP3(file_path) if file_path.endswith('.mp3') else FLAC(file_path) if file_path.endswith('.flac') else WAVE(file_path)
        total_time = int(audio.info.length)
        self.seek_slider.setRange(0, total_time)

        self.update_album_cover(file_path)
        self.update_discord_rpc(file_path)

    def pause_music(self):
        pygame.mixer.music.pause()

    def stop_music(self):
        pygame.mixer.music.stop()

    def next_song(self):
        if not self.music_files:
            return

        self.current_song_index += 1
        if self.current_song_index >= len(self.music_files):
            self.current_song_index = 0

        file_path = self.music_files[self.current_song_index]
        self.play_music_file(file_path)

    def prev_song(self):
        if not self.music_files:
            return

        self.current_song_index -= 1
        if self.current_song_index < 0:
            self.current_song_index = len(self.music_files) - 1

        file_path = self.music_files[self.current_song_index]
        self.play_music_file(file_path)

    def toggle_repeat(self):
        self.is_repeating = not self.is_repeating
        print("Repeat mode:", "On" if self.is_repeating else "Off")

    def toggle_shuffle(self):
        self.is_shuffling = not self.is_shuffling
        print("Shuffle mode:", "On" if self.is_shuffling else "Off")

    def set_volume(self, value):
        pygame.mixer.music.set_volume(value / 100)

    def seek_music(self, position):
        pygame.mixer.music.set_pos(position)

    def update_seek_slider(self):
        if pygame.mixer.music.get_busy():
            position = pygame.mixer.music.get_pos() / 1000
            self.seek_slider.setValue(int(position))

    def add_playlist(self):
        playlist_name = self.playlist_name_input.text()
        if playlist_name:
            self.playlist_box.addItem(playlist_name)
            self.playlist_name_input.clear()

    def show_home(self):
        self.tab_widget.setCurrentWidget(self.home_widget)

    def show_library(self):
        self.tab_widget.setCurrentWidget(self.library_widget)

    def show_playlists(self):
        self.tab_widget.setCurrentWidget(self.playlists_widget)

    def show_settings(self):
        self.tab_widget.setCurrentWidget(self.settings_widget)

    def init_discord_rpc(self):
        try:
            self.discord_rpc = Presence('1265193669779259465')
            self.discord_rpc.connect()
        except Exception as e:
            print("================================")
            print(f"Error initializing Discord RPC: {e}")
            print("================================")

    def update_discord_rpc(self, file_path):
        try:
            audio = MP3(file_path) if file_path.endswith('.mp3') else FLAC(file_path) if file_path.endswith('.flac') else WAVE(file_path)
            song_name = audio.get('TIT2', ['Unknown Song'])[0]
            artist_name = audio.get('TPE1', ['Unknown Artist'])[0]
            album_name = audio.get('TALB', ['Unknown Album'])[0]

            album_cover_key = None
            if self.current_album_cover:
                temp_path = "/path/to/save/cover.jpg"
                self.current_album_cover.save(temp_path)
                album_cover_key = temp_path

            self.discord_rpc.update(
                state=f"by {artist_name}",
                details=f"Listening to {song_name}",
                large_image=album_cover_key if album_cover_key else "default_image_key",
                large_text=album_name,
                small_image="small_image_key",
                small_text="Music Player"
            )
        except Exception as e:
            print("================================")
            print(f"Error updating Discord RPC: {e}")
            print("================================")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
