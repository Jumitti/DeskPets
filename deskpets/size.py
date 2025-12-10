import json
import os
from PyQt6 import QtWidgets, QtGui, QtCore

BASE_DIR = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE_DIR, "pets_data.json")
LIST_FILE = os.path.join(BASE_DIR, "pets_list.json")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
EXTRA_ROOT = os.path.join(BASE_DIR, "media/extraIcons")


def ap(path):
    return os.path.abspath(path)


def load_icon(species):
    p1 = ap(os.path.join(EXTRA_ROOT, species, "icon.png"))
    if os.path.isfile(p1):
        return p1

    p2 = ap(os.path.join(MEDIA_ROOT, species, "icon.png"))
    if os.path.isfile(p2):
        return p2

    return None


class SizeSelector(QtWidgets.QComboBox):
    changed = QtCore.pyqtSignal()

    SIZES = ["Very Small", "Small", "Original", "Medium", "Big", "Really Big"]

    def __init__(self, selected):
        super().__init__()
        self.addItems(self.SIZES)
        if selected in self.SIZES:
            self.setCurrentText(selected)
        else:
            self.setCurrentText("Original")
        self.currentIndexChanged.connect(self.changed.emit)

    def get_selected(self):
        return self.currentText()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        event.ignore()


class PetBlock(QtWidgets.QFrame):
    changed = QtCore.pyqtSignal()

    def __init__(self, species, selected_size):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        layout = QtWidgets.QVBoxLayout(self)

        icon_path = load_icon(species)
        icon_lbl = QtWidgets.QLabel()
        if icon_path:
            pix = QtGui.QPixmap(icon_path)
            if not pix.isNull():
                pix = pix.scaled(
                    72, 72,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation
                )
                icon_lbl.setPixmap(pix)
            else:
                icon_lbl.setText("[no icon]")
        else:
            icon_lbl.setText("[no icon]")

        title = species.capitalize()
        self.label = QtWidgets.QLabel(title)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        self.size_selector = SizeSelector(selected_size)
        self.size_selector.changed.connect(self.changed.emit)  # auto-save

        layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.label)
        layout.addWidget(self.size_selector)

        self.species = species

        self.setMinimumWidth(160)
        self.setMaximumWidth(260)

    def get_selected_size(self):
        return self.size_selector.get_selected()


class Main(QtWidgets.QScrollArea):
    def __init__(self, main_window):
        super().__init__()
        self.setWidgetResizable(True)

        self.container = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.container)

        self.grid_wrap = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.grid_wrap)
        self.grid.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.grid.setSpacing(14)
        self.layout.addWidget(self.grid_wrap)

        self.setWidget(self.container)

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(LIST_FILE, "r", encoding="utf-8") as f:
            cur = json.load(f)

        cur_map = {p["species"]: p for p in cur["pets"]}

        self.blocks = []

        for species in data.keys():
            selected_size = "Original"
            if species in cur_map:
                selected_size = cur_map[species].get("size", "Original")
            block = PetBlock(species, selected_size)
            block.changed.connect(self.save)
            self.blocks.append(block)

        self.populate_grid()
        self.main_window = main_window

    def populate_grid(self):
        width = self.viewport().width()
        col_count = max(1, width // 240)

        for i in reversed(range(self.grid.count())):
            w = self.grid.itemAt(i).widget()
            if isinstance(w, PetBlock):
                self.grid.removeWidget(w)
                w.setParent(None)

        row = col = 0
        for block in self.blocks:
            self.grid.addWidget(block, row, col)
            col += 1
            if col >= col_count:
                col = 0
                row += 1

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.populate_grid()

    def save(self):
        with open(LIST_FILE, "r", encoding="utf-8") as f:
            cur = json.load(f)

        cur_map = {p["species"]: p for p in cur["pets"]}

        for block in self.blocks:
            species = block.species
            selected_size = block.get_selected_size()
            if species in cur_map:
                cur_map[species]["size"] = selected_size
            else:
                cur_map[species] = {"species": species, "colors": [], "enabled": False, "size": selected_size}

        cur["pets"] = list(cur_map.values())
        with open(LIST_FILE, "w", encoding="utf-8") as f:
            json.dump(cur, f, indent=4)

        self.main_window.start_refresh()


class SizeSettings(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setWindowIcon(QtGui.QIcon("logo.ico"))
        self.resize(900, 600)

        self.scroll = Main(main_window)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.scroll)
