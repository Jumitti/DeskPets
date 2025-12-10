import sys
import os
import time
import random
import ctypes
from ctypes import wintypes

from PIL import Image
import json
from .remove_alpha import GifHelper
from .windows_API import POINT, SIZE, BLENDFUNCTION, Windows
from .state import State

# Configuration
BASE_DIR = os.path.dirname(__file__)
JSON_FILE = os.path.join(BASE_DIR, "pets_data.json")

# JSON
with open(JSON_FILE, "r", encoding="utf-8") as f:
    PETS_DATA = json.load(f)

# Windows API setup
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

ULW_ALPHA = 0x2


# Pet window
class Pet:
    def __init__(self, species, color, fps, size):
        self.hbitmaps = None
        self.frame_interval = None
        self.current_frame = None
        self.frame_count = None
        self.height = None
        self.width = None
        self.frames = None
        self.species = species
        self.color = color
        self.fps = fps
        self.size = size
        self.screen_width = user32.GetSystemMetrics(0)
        self.screen_height = user32.GetSystemMetrics(1)

        species_data = PETS_DATA[species]
        defaults = species_data.get("defaults", {})
        self.STATES_INFO = {}
        for state_name, gif_path in species_data["states"][color].items():
            state_defaults = defaults.get(state_name, {})
            self.STATES_INFO[state_name] = {
                "gif": gif_path,
                "hold": state_defaults.get("hold", self.fps),
                "movement_speed": state_defaults.get("movement_speed", 0),
                "speed_animation": state_defaults.get("speed_animation", 1.0),
            }

        self.state = self.random_state(
            exception=["with_ball", "wallclimb", "walldig", "wallgrab", "wallnap", "fall_from_grab"])
        self.frame_animation()

        self.taskbar_height, self.taskbar_autohide, self.taskbar_edge = Windows.taskbar_settings()
        if self.taskbar_autohide or self.taskbar_edge != 3:
            self.y_def = self.screen_height - self.height
            self.y = self.screen_height - self.height
        else:
            self.y_def = self.screen_height - self.height - self.taskbar_height
            self.y = self.screen_height - self.height - self.taskbar_height
        self.x = self.screen_width - self.width

        self.hwnd = Windows.hwnd(self.x, self.y, self.width, self.height)

        self.immunity = False
        self.lie_duration = 24

        self.wall_scene_step = None
        self.scene_wallclimb = False
        self.fall_last_frame = None
        self.fall_last_hbitmap = None

        self.height_lie = 20

    def random_state(self, exception=None):
        keys = list(self.STATES_INFO.keys())

        if exception:
            if isinstance(exception, str):
                exception = [exception]
            for ex in exception:
                if ex in keys:
                    keys.remove(ex)

        name = random.choice(keys)
        info = self.STATES_INFO[name]

        return State(
            name,
            info["gif"],
            hold=info["hold"],
            movement_speed=info["movement_speed"],
            speed_animation=info["speed_animation"],
            direction=random.choice([-1, 1]),
        )

    def draw_frame(self, hbitmap):
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

    def update_state(self):
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        mouse_x, mouse_y = pt.x, pt.y

        distance = ((self.x - mouse_x) ** 2 + (self.y - mouse_y) ** 2) ** 0.5

        if self.wall_scene_step is not None:
            if self.wall_scene_step == "go_to_wall":
                if self.x < self.screen_width - self.width:
                    self.x += self.state.movement_speed
                    return
                info = self.STATES_INFO["wallclimb"]
                self.state = State("wallclimb", info["gif"], hold=info["hold"],
                                   movement_speed=info["movement_speed"],
                                   speed_animation=info["speed_animation"],
                                   direction=1)
                self.frame_animation()
                self.wall_scene_step = "wallclimb"
                return

            if self.wall_scene_step == "wallclimb":
                mid = self.screen_height // 2
                quarter = mid + self.screen_height // 4
                if quarter > self.y > mid:
                    if random.random() < 0.05:
                        mid = self.y
                    else:
                        self.y -= self.state.movement_speed
                        return
                elif self.y > mid:
                    self.y -= self.state.movement_speed
                    return

                info = self.STATES_INFO["walldig"]
                self.state = State("walldig", info["gif"], hold=info["hold"],
                                   movement_speed=info["movement_speed"], speed_animation=info["speed_animation"],
                                   direction=1)
                self.frame_animation()
                self.wall_scene_step = "walldig"
                return

            if self.wall_scene_step == "walldig" and self.state.next(self):
                info = self.STATES_INFO["wallnap"]
                self.state = State("wallnap", info["gif"], hold=info["hold"],
                                   movement_speed=info["movement_speed"], speed_animation=info["speed_animation"],
                                   direction=-1)
                self.frame_animation()
                self.wall_scene_step = "wallnap"
                return

            if self.wall_scene_step == "wallnap" and self.state.next(self):
                info = self.STATES_INFO["wallgrab"]
                self.state = State("wallgrab", info["gif"], hold=info["hold"],
                                   movement_speed=0, speed_animation=info["speed_animation"],
                                   direction=1)
                self.frame_animation()
                self.wall_scene_step = "wallgrab"
                return

            if self.wall_scene_step == "wallgrab" and self.state.next(self):
                info = self.STATES_INFO["fall_from_grab"]
                self.state = State("fall_from_grab", info["gif"], hold=info["hold"],
                                   movement_speed=info["movement_speed"],
                                   speed_animation=info["speed_animation"],
                                   direction=-1)
                self.frame_animation()
                self.fall_last_frame = self.frames[-1]
                self.fall_last_hbitmap = self.hbitmaps[-1]

                self.wall_scene_step = "fall_frame"
                return

            if self.wall_scene_step == "fall_frame":
                if self.y < self.y_def:
                    self.y += self.state.movement_speed
                    self.x -= self.state.movement_speed // 2

                    self.draw_frame(self.fall_last_hbitmap)
                    return

                self.y = self.y_def
                self.wall_scene_step = None
                self.immunity = False
                self.state = self.random_state(
                    exception=["with_ball", "wallclimb", "walldig",
                               "wallgrab", "wallnap", "fall_from_grab"]
                )
                self.frame_animation()
                return

        color_states = PETS_DATA[self.species]["states"][self.color]
        if "lie" in color_states and distance < self.height_lie and not self.immunity:
            gif_path = color_states["lie"]
            hold = self.lie_duration
            movement_speed = PETS_DATA[self.species]["defaults"].get("lie", {}).get("movement_speed", 0)
            speed_animation = PETS_DATA[self.species]["defaults"].get("lie", {}).get("speed_animation", 1.0)
            self.state = State("lie", gif_path, hold=hold, movement_speed=movement_speed,
                               speed_animation=speed_animation)
            self.immunity = True
            self.frame_animation()

        elif self.state.next(self):
            if self.species == "squirrel" and self.wall_scene_step is None:
                if random.random() < 0.10:
                    self.wall_scene_step = "go_to_wall"

                    locomotions = ["walk", "walk_fast", "run"]
                    chosen = random.choice(locomotions)
                    info = self.STATES_INFO[chosen]

                    self.state = State(chosen, info["gif"], hold=info["hold"],
                                       movement_speed=info["movement_speed"],
                                       speed_animation=info["speed_animation"],
                                       direction=1)
                    self.frame_animation()
                    return
                else:
                    self.state = self.random_state(
                        exception=["with_ball", "wallclimb", "walldig", "wallgrab", "wallnap", "fall_from_grab"])
            elif self.wall_scene_step is not None:
                return
            else:
                self.state = self.random_state(exception=["with_ball", "wallclimb", "walldig", "wallgrab", "wallnap", "fall_from_grab"])

            self.immunity = False
            self.frame_animation()

        min_x = self.screen_width - self.screen_width // 4  # left
        max_x = self.screen_width - self.width  # right
        if self.x < min_x:
            self.x = min_x
            if self.state.name != "walldig":
                self.state.direction *= -1
        if self.x > max_x:
            self.x = max_x
            if self.state.name != "walldig":
                self.state.direction *= -1

    def frame_animation(self):
        self.frames = []
        for f in GifHelper.load_gif_frames(self.state.gif):
            orig_width, orig_height = f.size
            if self.size.lower() == "very small":
                new_height = 20
            elif self.size.lower() == "small":
                new_height = 40
            elif self.size.lower() == "original":
                new_height = orig_height
            elif self.size.lower() == "medium":
                new_height = 125
            elif self.size.lower() == "big":
                new_height = 150
            elif self.size.lower() == "really big":
                new_height = 200
            new_width = int(orig_width * new_height / orig_height)
            resized = f.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.frames.append(resized)

        self.height_lie = new_height

        self.width, self.height = self.frames[0].size
        self.frame_count = len(self.frames)
        self.current_frame = 0
        self.state.counter = 0
        if self.state.speed_animation != 0.0:
            self.frame_interval = 1.0 / (self.fps * self.state.speed_animation)
        self.hbitmaps = [GifHelper.pil_to_hbitmap(f) for f in self.frames]

    def close(self):
        if hasattr(self, "hbitmaps"):
            for hb in self.hbitmaps:
                try:
                    gdi32.DeleteObject(hb)
                except Exception:
                    pass
        self.hbitmaps = []

        if hasattr(self, "hwnd") and self.hwnd:
            import ctypes
            ctypes.windll.user32.DestroyWindow(self.hwnd)
            self.hwnd = None

        self.current_frame = 0
