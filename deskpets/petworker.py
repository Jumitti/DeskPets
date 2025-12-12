import json
import os
import time
import traceback

from PIL import Image
from PyQt6 import QtCore

from .pets import Pet

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "pets_list.json")
FPS_DEFAULT = 8
SIZE_DEFAULT = "small"


def load_pets():
    try:
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
    except Exception as e:
        print(e)
        traceback.print_exc()
        return []


class PetWorker(QtCore.QThread):
    frame_ready = QtCore.pyqtSignal(object, object)  # pet, frame image

    def __init__(self, pets):
        try:
            super().__init__()
            self.pets = pets
            self.running = True
        except Exception as e:
            print(e)
            traceback.print_exc()

    def run(self):
        try:
            while self.running:
                now = time.time()
                for pet in self.pets:
                    if now - getattr(pet, "last_update", 0) >= pet.frame_interval:
                        pet.last_update = now
                        pet.update_state()
                        frame_idx = pet.current_frame
                        frame_image = pet.frames[frame_idx]
                        if pet.state.direction < 0:
                            frame_image = frame_image.transpose(Image.FLIP_LEFT_RIGHT)
                        self.frame_ready.emit(pet, frame_image)
                        pet.current_frame = (frame_idx + 1) % pet.frame_count
                time.sleep(0.01)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def stop(self):
        self.running = False
