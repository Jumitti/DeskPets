import ctypes
import json
import os
import traceback
from ctypes import windll
from ctypes import wintypes

import win32gui

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

WS_EX_LAYERED = 0x80000
WS_EX_TOPMOST = 0x0008
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE = 0x08000000
WS_POPUP = 0x80000000

user32FS = windll.user32
user32FS.SetProcessDPIAware()  # optional, makes functions return real pixel numbers instead of scaled values

full_screen_rect = (0, 0, user32FS.GetSystemMetrics(0), user32FS.GetSystemMetrics(1))


def is_full_screen():
    try:
        hWnd = user32FS.GetForegroundWindow()
        rect = win32gui.GetWindowRect(hWnd)
        return rect == full_screen_rect
    except:
        return False


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte)
    ]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long)]


class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("hWnd", wintypes.HWND),
                ("uCallbackMessage", ctypes.c_uint),
                ("uEdge", ctypes.c_uint),
                ("rc", RECT),
                ("lParam", ctypes.c_int)]


def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            return {"layer": "front"}
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"layer": "front"}


class Windows:
    @staticmethod
    def hwnd(x, y, width, height):
        try:
            cfg = load_config()
            layer = cfg.get("layer", "front")

            ex_style = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE

            if layer == "front" and not is_full_screen():
                ex_style |= WS_EX_TOPMOST

            h = user32.CreateWindowExW(
                ex_style,
                "Static",
                None,
                WS_POPUP,
                x, y, width, height,
                None, None, None, None
            )
            user32.ShowWindow(h, 5)
            return h

        except Exception as e:
            print(e)
            traceback.print_exc()

    @staticmethod
    def taskbar_settings():
        try:
            ABS_AUTOHIDE = 0x1
            ABM_GETSTATE = 4
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            state = ctypes.windll.shell32.SHAppBarMessage(ABM_GETSTATE, ctypes.byref(abd))

            ABM_GETTASKBARPOS = 5
            shappbar = ctypes.windll.shell32.SHAppBarMessage
            abd = APPBARDATA()
            abd.cbSize = ctypes.sizeof(APPBARDATA)
            result = shappbar(ABM_GETTASKBARPOS, ctypes.byref(abd))

            if result:
                tb_rect = abd.rc
                tb_width = tb_rect.right - tb_rect.left
                tb_height = tb_rect.bottom - tb_rect.top
                tb_edge = abd.uEdge  # 0=left,1=top,2=right,3=bottom
                return tb_height, bool(state & ABS_AUTOHIDE), tb_edge
            else:
                return 60, bool(state & ABS_AUTOHIDE)
        except Exception as e:
            print(e)
            traceback.print_exc()
