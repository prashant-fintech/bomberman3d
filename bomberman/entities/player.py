from dataclasses import dataclass

from ursina import color

from ..board import step
from ..config import Direction, Palette
from ..events import Event
from .bomb import Bomb
from .fuses import RemoteFuse, TimedFuse
from .grid_mover import GridMover


@dataclass
class PlayerStats:
    """Everything power-ups are allowed to change. Effects touch this, never the Player itself."""
    max_bombs: int
    fire: int
    speed: float
    can_kick: bool = False
    has_remote: bool = False


class Player(GridMover):
    def __init__(self, world, cell):
        cfg = world.config
        super().__init__(world, cfg.player_speed, model='sphere', color=color.hex(Palette.player), scale=.75,
                         position=(cell[0], .4, cell[1]))
        world.spawn(parent=self, model='sphere', color=color.hex(Palette.helmet), scale=(.65, .45, .65), y=.4)
        for sx in (-.18, .18):
            world.spawn(parent=self, model='sphere', color=color.black, scale=.15, position=(sx, .08, -.45))
        self.stats = PlayerStats(max_bombs=cfg.start_bombs, fire=cfg.start_fire, speed=cfg.player_speed)

    def move_speed(self):
        return self.stats.speed

    # ------------------------------------------------------------ actions (called by the controller)
    def walk(self, direction: Direction) -> None:
        if self.try_move(direction) or self.is_moving:
            return
        bomb = self.world.bombs.get(step(self.cell, direction))
        if bomb and self.stats.can_kick:
            bomb.kick(direction)

    def drop_bomb(self) -> None:
        cell = self.cell
        if not self.alive or cell in self.world.bombs:
            return
        if len(self.world.bombs_owned_by(self)) >= self.stats.max_bombs:
            return
        fuse = RemoteFuse() if self.stats.has_remote else TimedFuse(self.world.config.fuse_seconds)
        Bomb(self.world, cell, owner=self, radius=self.stats.fire, fuse=fuse)

    def detonate(self) -> None:
        for bomb in self.world.bombs_owned_by(self):
            bomb.fuse.trigger()

    # ------------------------------------------------------------ per frame
    def update(self):
        if not self.alive:
            return
        self.advance()
        effect = self.world.take_powerup(self.cell)
        if effect:
            effect.apply(self.stats, self.world.config)
            self.world.events.publish(Event.POWERUP_COLLECTED, effect=effect)
