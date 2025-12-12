import json
import os

from PyQt6 import QtCore, QtWidgets, QtGui

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"layer": "front"}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"layer": "front"}


class LayerSelector(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.config = load_config()

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        label = QtWidgets.QLabel("Layer")
        layout.addWidget(label, 0, QtCore.Qt.AlignmentFlag.AlignLeft)

        radios_box = QtWidgets.QHBoxLayout()
        radios_box.setSpacing(15)

        self.radio_back = QtWidgets.QRadioButton("Back")
        self.radio_front = QtWidgets.QRadioButton("Front")

        radios_box.addWidget(self.radio_back)
        radios_box.addWidget(self.radio_front)

        layout.addLayout(radios_box)
        layout.addStretch(1)

        if self.config.get("layer") == "back":
            self.radio_back.setChecked(True)
        else:
            self.radio_front.setChecked(True)

        self.radio_back.toggled.connect(self.update_layer)
        self.radio_front.toggled.connect(self.update_layer)

        self.setLayout(layout)

    def update_layer(self):
        self.config["layer"] = "back" if self.radio_back.isChecked() else "front"
        self.save_config()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)

            self.main_window.start_refresh()
        except Exception:
            pass


class Settings(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setWindowIcon(QtGui.QIcon("logo.ico"))
        self.resize(900, 600)

        layout = QtWidgets.QVBoxLayout(self)
        self.layer_selector = LayerSelector(main_window)
        layout.addWidget(self.layer_selector)
