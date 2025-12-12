import traceback

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWebEngineWidgets import QWebEngineView


class BrowserWindow(QtWidgets.QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("DeskPets GitHub")
            self.resize(1024, 768)

            self.browser = QWebEngineView()
            self.browser.setUrl(QtCore.QUrl("https://github.com/Jumitti/DeskPets"))
            self.setCentralWidget(self.browser)
        except Exception as e:
            print(e)
            traceback.print_exc()
