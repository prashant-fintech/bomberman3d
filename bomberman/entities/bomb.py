from ursina import Entity, Vec3, color, destroy, time

from ..board import cell_of, step
from ..config import Cell, Direction, Palette
from ..events import Event
from .fuses import BOMB_SCALE, Fuse


class Bomb(Entity):
    def __init__(self, world, cell: Cell, owner, radius: int, fuse: Fuse):
        super().__init__(model='sphere', color=color.hex(Palette.bomb), scale=BOMB_SCALE,
                         position=(cell[0], .4, cell[1]))
        world.track(self)
        world.spawn(parent=self, model='cube', color=color.hex(Palette.bomb_cord), scale=(.12, .35, .12), y=.55)
        self.world = world
        self.cell = cell
        self.owner = owner
        self.radius = radius
        self.fuse = fuse
        self.exploded = False
        self._slide_dir: Direction | None = None
        self._slide_target: Cell | None = None
        fuse.decorate(self)
        world.bombs[cell] = self

    # ------------------------------------------------------------ kicking
    def kick(self, direction: Direction) -> None:
        if self._slide_dir is None and self._free_cell_towards(direction):
            self._slide_dir = direction

    def _free_cell_towards(self, direction: Direction) -> Cell | None:
        nxt = step(self.cell, direction)
        if self.world.is_blocked(nxt) or self.world.has_creature(nxt):
            return None
        return nxt

    def _slide(self) -> None:
        if self._slide_target is None:
            self._slide_target = self._free_cell_towards(self._slide_dir)
            if self._slide_target is None:              # hit something: stop on this cell
                self._slide_dir = None
                self.position = Vec3(self.cell[0], self.y, self.cell[1])
                return
        goal = Vec3(self._slide_target[0], self.y, self._slide_target[1])
        delta = goal - self.position
        distance = self.world.config.kick_speed * time.dt
        if delta.length() <= distance:
            self.position = goal
            self.world.bombs.pop(self.cell, None)
            self.cell = self._slide_target
            self.world.bombs[self.cell] = self
            self._slide_target = None
        else:
            self.position += delta.normalized() * distance

    # ------------------------------------------------------------ lifecycle
    def update(self):
        if self.exploded:
            return
        self.fuse.animate(self)
        if self._slide_dir:
            self._slide()
        if self.fuse.tick(time.dt):
            self.explode()

    def explode(self) -> None:
        if self.exploded:
            return
        self.exploded = True
        self.world.bombs.pop(self.cell, None)
        if self._slide_target is not None:              # exploded mid-slide: blast from where it is now
            self.cell = cell_of(self)
        self.world.events.publish(Event.BOMB_EXPLODED, bomb=self)
        destroy(self)
