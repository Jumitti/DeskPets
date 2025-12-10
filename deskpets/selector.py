import json
import os
from PyQt6 import QtWidgets, QtGui, QtCore

DATA_FILE = "pets_data.json"
LIST_FILE = "pets_list.json"
MEDIA_ROOT = "media"
EXTRA_ROOT = "media/extraIcons"


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


class ColorGrid(QtWidgets.QWidget):
    changed = QtCore.pyqtSignal()

    def __init__(self, colors, selected):
        super().__init__()
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(4)

        self.buttons = {}
        cols = 4
        r = c = 0

        for col in colors:
            b = QtWidgets.QPushButton(col)
            b.setCheckable(True)
            b.setChecked(col in selected)
            b.setMinimumWidth(60)
            b.clicked.connect(self.changed.emit)
            layout.addWidget(b, r, c)
            self.buttons[col] = b

            c += 1
            if c >= cols:
                c = 0
                r += 1

    def get_selected(self):
        return [c for c, b in self.buttons.items() if b.isChecked()]


class PetBlock(QtWidgets.QFrame):
    changed = QtCore.pyqtSignal()

    def __init__(self, species, available_colors, enabled, selected_colors):
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
        self.checkbox = QtWidgets.QCheckBox(title)
        self.checkbox.setChecked(enabled)
        self.checkbox.stateChanged.connect(self.changed.emit)  # auto-save

        if len(available_colors) > 1:
            self.color_widget = ColorGrid(available_colors, selected_colors)
            self.color_widget.changed.connect(self.changed.emit)  # auto-save
        else:
            self.color_widget = None

        layout.addWidget(icon_lbl, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.checkbox, alignment=QtCore.Qt.AlignmentFlag.AlignHCenter)

        if self.color_widget:
            layout.addWidget(self.color_widget)

        self.available_colors = available_colors
        self.selected_colors = selected_colors

        self.setMinimumWidth(160)
        self.setMaximumWidth(260)

    def get_selected_colors(self):
        if self.color_widget:
            return self.color_widget.get_selected()
        else:
            return self.available_colors[:]


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

        for species, info in data.items():
            if "colors" not in info:
                continue

            if species in cur_map:
                enabled = cur_map[species]["enabled"]
                selected = cur_map[species]["colors"]
            else:
                enabled = False
                selected = []

            block = PetBlock(species, info["colors"], enabled, selected)
            block.changed.connect(self.save)  # connect auto-save
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
        result = {"pets": []}

        for block in self.blocks:
            species = block.checkbox.text().lower()
            chosen = block.get_selected_colors()

            result["pets"].append({
                "species": species,
                "colors": chosen,
                "enabled": block.checkbox.isChecked()
            })

        with open(LIST_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

        self.main_window.start_refresh()


class PetSelector(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Pet Selector")
        self.setWindowIcon(QtGui.QIcon("logo.ico"))
        self.resize(900, 600)

        self.scroll = Main(main_window)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.scroll)
