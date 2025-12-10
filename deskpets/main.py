import sys
import os
import ctypes
import json
import time

from PyQt6 import QtWidgets, QtGui, QtCore
from PIL import Image

from .pets import Pet
from .remove_alpha import GifHelper
from .window import MainWindow

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, "pets_list.json")
FPS_DEFAULT = 8
SIZE_DEFAULT = "small"
gdi32 = ctypes.windll.gdi32


class PetWorker(QtCore.QThread):
    def __init__(self, pets):
        super().__init__()
        self.pets = pets
        self.running = True

    def run(self):
        while self.running:
            now = time.time()
            for pet in self.pets:
                if now - getattr(pet, "last_update", 0) >= pet.frame_interval:
                    pet.last_update = now
                    pet.update_state()
                    frame_idx = pet.current_frame
                    if pet.state.direction < 0:
                        flipped = pet.frames[frame_idx].transpose(Image.FLIP_LEFT_RIGHT)
                        hbitmap = GifHelper.pil_to_hbitmap(flipped)
                        pet.draw_frame(hbitmap)
                        gdi32.DeleteObject(hbitmap)
                    else:
                        pet.draw_frame(pet.hbitmaps[frame_idx])
                    pet.current_frame = (pet.current_frame + 1) % pet.frame_count
            time.sleep(0.01)

    def stop(self):
        self.running = False


def load_pets():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    pets = []
    for entry in cfg.get("pets", []):
        if not entry.get("enabled", True):
            continue
        species = entry["species"]
        fps = entry.get("fps", FPS_DEFAULT)
        size = entry.get("size", SIZE_DEFAULT)
        for color in entry.get("colors", []):
            pets.append(Pet(species, color, fps, size))
    return pets


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.hide()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
