from ursina import Entity, color, time
from ursina.shaders import unlit_shader

from ..config import Cell


class PowerUp(Entity):
    """The spinning pickup on the floor. What it *does* lives in its effect (see powerups.py)."""

    def __init__(self, world, cell: Cell, effect):
        super().__init__(model='cube', color=color.hex(effect.color), shader=unlit_shader, scale=.42,
                         position=(cell[0], .4, cell[1]), rotation=(45, 0, 45))
        world.track(self)
        world.powerups[cell] = self
        self.effect = effect

    def update(self):
        self.rotation_y += 120 * time.dt
