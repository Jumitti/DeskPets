import ctypes
import os
import traceback

from PyQt6 import QtWidgets, QtGui

from .credits import BrowserWindow
from .petworker import PetWorker, load_pets
from .remove_alpha import GifHelper
from .selector import PetSelector
from .settings import Settings
from .size import SizeSettings
from .windows_API import POINT, SIZE, BLENDFUNCTION, Windows, is_full_screen

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

BASE_DIR = os.path.dirname(__file__)
LOGO_DIR = os.path.join(BASE_DIR, "logo.ico")

ULW_ALPHA = 0x2

STATE_FULLSCREEN = False


def draw_pet_frame(pet, frame_image):
    try:
        if getattr(pet, "hwnd", None):
            hbitmap = GifHelper.pil_to_hbitmap(frame_image)
            draw_frame(pet, hbitmap)
            gdi32.DeleteObject(hbitmap)
    except Exception as e:
        print(e)
        traceback.print_exc()


def draw_frame(self, hbitmap):
    global STATE_FULLSCREEN
    try:
        full_screen_now = is_full_screen()
        if full_screen_now != STATE_FULLSCREEN:
            STATE_FULLSCREEN = full_screen_now
            if getattr(self, "main_window", None):
                self.main_window.start_refresh()

        hdc_screen = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        gdi32.SelectObject(hdc_mem, hbitmap)

        blend = BLENDFUNCTION()
        blend.BlendOp = 0
        blend.BlendFlags = 0
        blend.SourceConstantAlpha = 255
        blend.AlphaFormat = 1

        pt_pos = POINT(self.x, self.y)
        size = SIZE(self.width, self.height)
        pt_src = POINT(0, 0)

        user32.UpdateLayeredWindow(self.hwnd, hdc_screen, ctypes.byref(pt_pos),
                                   ctypes.byref(size), hdc_mem, ctypes.byref(pt_src),
                                   0, ctypes.byref(blend), ULW_ALPHA)

        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc_screen)

    except Exception as e:
        print(e)
        traceback.print_exc()


def close(pet):
    try:
        if getattr(pet, "hbitmaps", None):
            for hb in pet.hbitmaps:
                try:
                    gdi32.DeleteObject(hb)
                except Exception:
                    pass
        pet.hbitmaps = []

        if getattr(pet, "hwnd", None):
            ctypes.windll.user32.DestroyWindow(pet.hwnd)
            pet.hwnd = None

        pet.current_frame = 0
    except Exception as e:
        print(e)
        traceback.print_exc()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        try:
            super().__init__()
            self.setWindowTitle("Pet Manager")
            self.resize(800, 600)
            self.setWindowIcon(QtGui.QIcon(LOGO_DIR))
            app.setWindowIcon(QtGui.QIcon(LOGO_DIR))
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"DeskPets")

            # Tabs
            self.tabs = QtWidgets.QTabWidget()
            self.setCentralWidget(self.tabs)
            self.tab_add_pet = QtWidgets.QWidget()
            self.tab_size_pet = QtWidgets.QWidget()
            self.tab_settings = QtWidgets.QWidget()
            self.tab_credits = QtWidgets.QWidget()
            self.tabs.addTab(self.tab_add_pet, "Add Pets")
            self.tabs.addTab(self.tab_size_pet, "Size Pets")
            self.tabs.addTab(self.tab_settings, "Settings")
            self.tabs.addTab(self.tab_credits, "Credits")

            self.tab_add_pet.setLayout(QtWidgets.QVBoxLayout())
            self.pet_selector = PetSelector(self)
            self.tab_add_pet.layout().addWidget(self.pet_selector)

            self.tab_size_pet.setLayout(QtWidgets.QVBoxLayout())
            self.size_settings = SizeSettings(self)
            self.tab_size_pet.layout().addWidget(self.size_settings)

            self.tab_settings.setLayout(QtWidgets.QVBoxLayout())
            self.settings_settings = Settings(self)
            self.tab_settings.layout().addWidget(self.settings_settings)

            self.tab_credits.setLayout(QtWidgets.QVBoxLayout())
            self.browser_window = BrowserWindow()
            self.tab_credits.layout().addWidget(self.browser_window)

            # Tray
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

            # Pets
            self.pets = []
            self.worker = None
        except Exception as e:
            print(e)
            traceback.print_exc()

    def start_refresh(self):
        try:
            if self.worker:
                self.worker.stop()
            for pet in getattr(self, "pets", []):
                close(pet)
            # self.pets = load_pets() or []

            self.pets = load_pets() or []
            for pet in self.pets:
                pet.main_window = self

            self.worker = PetWorker(self.pets)
            self.worker.frame_ready.connect(draw_pet_frame)
            self.worker.start()
        except Exception as e:
            print(e)
            traceback.print_exc()

    def closeEvent(self, event):
        try:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Pet Manager", "Application minimized to tray",
                QtWidgets.QSystemTrayIcon.MessageIcon.Information, 2000
            )
        except Exception as e:
            print(e)
            traceback.print_exc()

    def show_window(self):
        try:
            self.show()
            self.raise_()
            self.activateWindow()
        except Exception as e:
            print(e)
            traceback.print_exc()
