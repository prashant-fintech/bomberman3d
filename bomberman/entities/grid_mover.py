from ursina import Entity, Vec3, time

from ..board import cell_of, step
from ..config import Cell, Direction


class GridMover(Entity):
    """Base for creatures that walk cell-to-cell. Subclasses decide *where* to go; this decides *how*."""

    def __init__(self, world, speed: float, **kwargs):
        super().__init__(**kwargs)
        world.track(self)
        self.world = world
        self._speed = speed
        self.target: Cell | None = None
        self.alive = True

    @property
    def cell(self) -> Cell:
        return cell_of(self)

    @property
    def is_moving(self) -> bool:
        return self.target is not None

    def move_speed(self) -> float:
        return self._speed

    def try_move(self, direction: Direction) -> bool:
        if self.is_moving or not self.alive:
            return False
        nxt = step(self.cell, direction)
        if self.world.is_blocked(nxt):
            return False
        self.target = nxt
        return True

    def advance(self) -> None:
        if self.target is None:
            return
        goal = Vec3(self.target[0], self.y, self.target[1])
        delta = goal - self.position
        distance = self.move_speed() * time.dt
        if delta.length() <= distance:
            self.position = goal
            self.target = None
        else:
            self.position += delta.normalized() * distance

    def die(self) -> None:
        if not self.alive:
            return
        self.alive = False
        self.target = None
        self.animate_scale(0, duration=.35)
