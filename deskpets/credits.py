import sys
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWebEngineWidgets import QWebEngineView

class BrowserWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeskPets GitHub")
        self.resize(1024, 768)

        self.browser = QWebEngineView()
        self.browser.setUrl(QtCore.QUrl("https://github.com/Jumitti/DeskPets"))
        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = BrowserWindow("https://github.com/Jumitti/DeskPets")
    window.show()
    sys.exit(app.exec())
