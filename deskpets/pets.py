import ctypes
import json
import os
import random
import traceback

from PIL import Image

from .remove_alpha import GifHelper
from .squirrel_climb import squirrel_climb, go_climb
from .state import State
from .windows_API import POINT, Windows

# Configuration
BASE_DIR = os.path.dirname(__file__)
JSON_FILE = os.path.join(BASE_DIR, "pets_data.json")

# JSON
with open(JSON_FILE, "r", encoding="utf-8") as f:
    PETS_DATA = json.load(f)

# Windows API setup
user32 = ctypes.windll.user32


# Pet window
class Pet:
    def __init__(self, species, color, fps, size):
        try:
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
        except Exception as e:
            print(e)
            traceback.print_exc()

    def random_state(self, exception=None):
        try:
            keys = list(self.STATES_INFO.keys())

            if exception:
                if isinstance(exception, str):
                    exception = [exception]
                for ex in exception:
                    if ex in keys:
                        keys.remove(ex)

            if not keys:
                keys = list(self.STATES_INFO.keys())

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
        except Exception as e:
            print(e)
            traceback.print_exc()

    def update_state(self):
        try:
            pt = POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            mouse_x, mouse_y = pt.x, pt.y

            distance = ((self.x - mouse_x) ** 2 + (self.y - mouse_y) ** 2) ** 0.5

            if self.wall_scene_step is not None:
                squirrel_climb(self)
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
                if self.species == "squirrel":
                    go_climb(self)
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
        except Exception as e:
            print(e)
            traceback.print_exc()

    def frame_animation(self):
        try:
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
        except Exception as e:
            print(e)
            traceback.print_exc()
