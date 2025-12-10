import sys
import os
from PyQt6 import QtWidgets, QtGui, QtCore
from .selector import PetSelector
from .size import SizeSettings
from .credits import BrowserWindow

import ctypes

BASE_DIR = os.path.dirname(__file__)
LOGO_DIR = os.path.join(BASE_DIR, "logo.ico")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.setWindowTitle("Pet Manager")
        self.resize(800, 600)
        self.setWindowIcon(QtGui.QIcon(LOGO_DIR))

        app_icon = QtGui.QIcon(LOGO_DIR)
        app.setWindowIcon(app_icon)

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"DeskPets")
        hwnd = int(self.winId())

        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_add_pet = QtWidgets.QWidget()
        self.tab_size_pet = QtWidgets.QWidget()
        self.tab_credits = QtWidgets.QWidget()

        self.tabs.addTab(self.tab_add_pet, "Add Pets")
        self.tabs.addTab(self.tab_size_pet, "Size Pets")
        self.tabs.addTab(self.tab_credits, "Credits")

        self.tab_add_pet.setLayout(QtWidgets.QVBoxLayout())
        self.pet_selector = PetSelector(self)
        self.tab_add_pet.layout().addWidget(self.pet_selector)

        self.tab_size_pet.setLayout(QtWidgets.QVBoxLayout())
        self.size_settings = SizeSettings(self)
        self.tab_size_pet.layout().addWidget(self.size_settings)

        self.tab_credits.setLayout(QtWidgets.QVBoxLayout())
        self.browser_window = BrowserWindow()
        self.tab_credits.layout().addWidget(self.browser_window)

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(LOGO_DIR))

        show_action = QtGui.QAction("Show", self)
        refresh_action = QtGui.QAction("Refresh", self)
        quit_action = QtGui.QAction("Quit", self)

        show_action.triggered.connect(self.show_window)
        refresh_action.triggered.connect(self.start_refresh)
        quit_action.triggered.connect(QtWidgets.QApplication.instance().quit)

        tray_menu = QtWidgets.QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(refresh_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.show()

        self.pets = []
        self.worker = None
        self.start_refresh()

        self.pet_selector = PetSelector(self)

    def start_refresh(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()

        from .main import PetWorker, load_pets

        for pet in getattr(self, "pets", []):
            pet.close()

        self.pets = load_pets()
        self.worker = PetWorker(self.pets)
        self.worker.start()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Pet Manager",
            "Application minimized to tray",
            QtWidgets.QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()
