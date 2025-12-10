import random


class State:
    def __init__(self, name, gif, hold=0, movement_speed=0, speed_animation=1.0, direction=1):
        self.name = name
        self.gif = gif
        self.hold = hold
        self.movement_speed = movement_speed
        self.speed_animation = speed_animation
        self.direction = direction
        self.counter = 0

    def next(self, pet):
        self.counter += 1
        if self.name == "wallclimb":
            pet.y -= self.movement_speed
            if pet.y < 0:
                pet.y = 0
        elif self.movement_speed != 0:
            pet.x += self.movement_speed * self.direction
            if pet.x < 0:
                pet.x = 0
                self.direction *= -1
            if pet.x > pet.screen_width - pet.width:
                pet.x = pet.screen_width - pet.width
                self.direction *= -1
        if self.hold and self.counter >= self.hold:
            return True
        return False

