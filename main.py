import sys

from utils.settings import Settings
from qt.mainwindow import start_qt_app
from server import *

class App:
    def __init__(self):
        self.settings = Settings()

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'qt':
        app = App()
        start_qt_app(app)
    else:
        app = App()
        start_react_server(app)

if __name__ == '__main__':
    main()
