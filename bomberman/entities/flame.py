from ursina import Entity, color, destroy, time
from ursina.shaders import unlit_shader

from ..config import Cell, Palette


class Flame(Entity):
    def __init__(self, world, cell: Cell):
        super().__init__(model='cube', color=color.hex(Palette.flame_hot), shader=unlit_shader,
                         scale=.95, position=(cell[0], .45, cell[1]))
        world.track(self)
        world.add_flame(cell)
        self.world = world
        self.cell = cell
        self.duration = self.remaining = world.config.flame_seconds

    def update(self):
        self.remaining -= time.dt
        k = max(self.remaining / self.duration, 0)
        self.scale = .35 + .6 * k
        self.color = color.hex(Palette.flame_bright if int(self.remaining * 20) % 2 else Palette.flame_hot)
        if self.remaining <= 0:
            self.world.remove_flame(self.cell)
            destroy(self)
