"""Strategy pattern: *when* a bomb goes off is pluggable, so the Bomb class never changes for new fuse types."""
import math
from abc import ABC, abstractmethod

from ursina import color, time
from ursina.shaders import unlit_shader

from ..config import Palette

BOMB_SCALE = .8


class Fuse(ABC):
    @abstractmethod
    def tick(self, dt: float) -> bool:
        """Advance time; return True when the bomb should explode."""

    @abstractmethod
    def ignite(self, delay: float) -> None:
        """Force an explosion within `delay` seconds (used for chain reactions)."""

    def trigger(self) -> None:
        """The owner pressed detonate. Most fuses ignore this."""

    def decorate(self, bomb) -> None:
        """Add any visuals this fuse needs when the bomb is placed."""

    def animate(self, bomb) -> None:
        """Per-frame visuals."""


class TimedFuse(Fuse):
    def __init__(self, seconds: float):
        self.remaining = seconds

    def tick(self, dt):
        self.remaining -= dt
        return self.remaining <= 0

    def ignite(self, delay):
        self.remaining = min(self.remaining, delay)

    def animate(self, bomb):
        rate = 18 if self.remaining < 1 else 7
        bomb.scale = BOMB_SCALE * (1 + .1 * math.sin(time.time() * rate))


class RemoteFuse(TimedFuse):
    """Waits forever until the owner detonates it or another blast reaches it."""

    def __init__(self):
        super().__init__(math.inf)
        self._light = None

    def trigger(self):
        self.ignite(0)

    def decorate(self, bomb):
        self._light = bomb.world.spawn(parent=bomb, model='sphere', shader=unlit_shader, scale=.22, y=.78,
                                       color=color.hex(Palette.remote_light_on))

    def animate(self, bomb):
        on = int(time.time() * 4) % 2
        self._light.color = color.hex(Palette.remote_light_on if on else Palette.remote_light_off)
