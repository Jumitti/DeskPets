import random
import traceback

from .state import State


def go_climb(self):
    try:
        if self.wall_scene_step is None:
            if random.random() < 0.10:
                self.wall_scene_step = "go_to_wall"

                locomotions = ["walk", "walk_fast", "run"]
                chosen = random.choice(locomotions)
                info = self.STATES_INFO[chosen]

                self.state = State(chosen, info["gif"], hold=info["hold"],
                                   movement_speed=info["movement_speed"],
                                   speed_animation=info["speed_animation"],
                                   direction=1)
                return
            else:
                self.state = self.random_state(
                    exception=["with_ball", "wallclimb", "walldig", "wallgrab", "wallnap", "fall_from_grab"])
        elif self.wall_scene_step is not None:
            return
    except Exception as e:
        print(e)
        traceback.print_exc()


def squirrel_climb(self):
    try:
        if self.wall_scene_step == "go_to_wall":
            if self.x + self.state.movement_speed < self.screen_width - self.width:
                self.x += self.state.movement_speed
                return

            self.x = self.screen_width - self.width

            info = self.STATES_INFO["wallclimb"]
            self.state = State("wallclimb", info["gif"], hold=info["hold"],
                               movement_speed=info["movement_speed"],
                               speed_animation=info["speed_animation"],
                               direction=1)
            self.frame_animation()
            self.wall_scene_step = "wallclimb"
            return

        elif self.wall_scene_step == "wallclimb":
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

        elif self.wall_scene_step == "walldig" and self.state.next(self):
            info = self.STATES_INFO["wallnap"]
            self.state = State("wallnap", info["gif"], hold=info["hold"],
                               movement_speed=info["movement_speed"], speed_animation=info["speed_animation"],
                               direction=-1)
            self.frame_animation()

            if random.random() < 0.90:
                self.wall_scene_step = "wallnap"
            return

        elif self.wall_scene_step == "wallnap" and self.state.next(self):
            info = self.STATES_INFO["wallgrab"]
            self.state = State("wallgrab", info["gif"], hold=info["hold"],
                               movement_speed=0, speed_animation=info["speed_animation"],
                               direction=1)
            self.frame_animation()

            if random.random() < 0.90:
                self.wall_scene_step = "wallgrab"
            return

        elif self.wall_scene_step == "wallgrab" and self.state.next(self):

            if random.random() < 0.10:
                info = self.STATES_INFO["wallnap"]
                self.state = State("wallnap", info["gif"], hold=info["hold"],
                                   movement_speed=info["movement_speed"],
                                   speed_animation=info["speed_animation"],
                                   direction=-1)
                self.frame_animation()
                return

            info = self.STATES_INFO["fall_from_grab"]
            self.state = State("fall_from_grab", info["gif"], hold=info["hold"],
                               movement_speed=info["movement_speed"],
                               speed_animation=info["speed_animation"],
                               direction=-1)
            self.frame_animation()

            if self.frames:
                self.fall_last_frame = self.frames[-1]
                self.frames = [self.fall_last_frame]
                self.frame_count = 1
                self.current_frame = 0

            self.wall_scene_step = "fall_frame"
            return

        elif self.wall_scene_step == "fall_frame":
            if self.y < self.y_def:
                self.y += self.state.movement_speed
                self.x -= max(1, self.state.movement_speed // 2)
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

    except Exception as e:
        print(e)
        traceback.print_exc()
