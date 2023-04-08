import sys

DATA_DIR = 'data/'
DB_DIR = DATA_DIR + 'db/'
CONFIGS_DIR = DATA_DIR + 'configs/'
EXPORT_DIR = 'export/'
TEMP_DIR = DATA_DIR + 'temp/'
TEMP_FILE_NAME = 'temp.m3u'
SQL_TYPE = 'sqlite:///'
TAG_SPLITTER = ':'

if sys.platform.startswith('linux'):
    PLAYER_PATH = "mpv"
    # PLAYER_PATH = "vlc"
else:
    PLAYER_PATH = "C:/Program Files/VideoLAN/VLC/vlc.exe"
