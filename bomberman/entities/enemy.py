import math
import random

from ursina import color, time

from ..ai import Brain
from ..board import step
from ..config import DIRECTIONS, Palette
from .grid_mover import GridMover


class Enemy(GridMover):
    """Moves wherever its Brain says. Swap the brain to change behaviour; this class stays the same."""

    def __init__(self, world, cell, brain: Brain):
        super().__init__(world, world.config.enemy_speed, model='sphere', color=color.hex(Palette.enemy),
                         scale=.7, position=(cell[0], .35, cell[1]))
        for sx in (-.2, .2):
            world.spawn(parent=self, model='sphere', color=color.white, scale=.28, position=(sx, .15, -.4))
            world.spawn(parent=self, model='sphere', color=color.black, scale=.13, position=(sx, .15, -.52))
        self.brain = brain
        self._bob_phase = random.random() * 10

    def update(self):
        if not self.alive:
            return
        self.y = .35 + abs(math.sin(time.time() * 7 + self._bob_phase)) * .12
        if self.world.frozen:
            return
        if not self.is_moving:
            options = [d for d in DIRECTIONS if not self.world.is_blocked(step(self.cell, d))]
            if options:
                self.try_move(self.brain.next_direction(self, options))
        self.advance()
