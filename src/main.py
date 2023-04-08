import logging
import sys

from qt.main import start_qt_app
from server import start_react_server
from utils.settings import Settings


class AppSettings:
    def __init__(self):
        self.settings = Settings()


def main():
    logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
    app_settings = AppSettings()
    if len(sys.argv) > 1 and sys.argv[1] == "react":
        start_react_server(app_settings)
    else:
        start_qt_app(app_settings)


if __name__ == "__main__":
    main()
