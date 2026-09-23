"""Power-up effects, the weighted factory that picks them, and the spawner that drops them from crates.

Adding a power-up = one new PowerUpEffect subclass + adding it to DEFAULT_EFFECTS (open/closed).
"""
import random
from abc import ABC, abstractmethod

from .config import Cell, Config
from .entities.player import PlayerStats
from .entities.powerup import PowerUp
from .events import Event, EventBus


class PowerUpEffect(ABC):
    name: str
    color: str
    weight: int

    @abstractmethod
    def apply(self, stats: PlayerStats, config: Config) -> None: ...

    def is_redundant(self, stats: PlayerStats) -> bool:
        """True if picking this up again would do nothing (so it shouldn't drop)."""
        return False


class ExtraBomb(PowerUpEffect):
    name, color, weight = 'bomb', '#3a86ff', 3

    def apply(self, stats, config):
        stats.max_bombs += 1


class BiggerBlast(PowerUpEffect):
    name, color, weight = 'fire', '#ff006e', 3

    def apply(self, stats, config):
        stats.fire += 1


class SpeedUp(PowerUpEffect):
    name, color, weight = 'speed', '#ffbe0b', 2

    def apply(self, stats, config):
        stats.speed = min(stats.speed + config.speed_boost, config.player_max_speed)


class Kick(PowerUpEffect):
    name, color, weight = 'kick', '#2ec4b6', 1

    def apply(self, stats, config):
        stats.can_kick = True

    def is_redundant(self, stats):
        return stats.can_kick


class RemoteDetonator(PowerUpEffect):
    name, color, weight = 'remote', '#9b5de5', 1

    def apply(self, stats, config):
        stats.has_remote = True

    def is_redundant(self, stats):
        return stats.has_remote


DEFAULT_EFFECTS: tuple[PowerUpEffect, ...] = (ExtraBomb(), BiggerBlast(), SpeedUp(), Kick(), RemoteDetonator())


class PowerUpFactory:
    """Picks a random effect, weighted, skipping ones the player already maxed out."""

    def __init__(self, rng: random.Random, effects=DEFAULT_EFFECTS):
        self.rng = rng
        self.effects = effects

    def random_effect(self, stats: PlayerStats) -> PowerUpEffect | None:
        pool = [e for e in self.effects if not e.is_redundant(stats)]
        if not pool:
            return None
        return self.rng.choices(pool, weights=[e.weight for e in pool])[0]


class PowerUpSpawner:
    """Listens for destroyed crates and sometimes leaves a power-up behind."""

    def __init__(self, world, events: EventBus, factory: PowerUpFactory, rng: random.Random):
        self.world, self.factory, self.rng = world, factory, rng
        events.subscribe(Event.CRATE_DESTROYED, self._on_crate_destroyed)

    def _on_crate_destroyed(self, cell: Cell) -> None:
        if self.world.player is None or self.rng.random() >= self.world.config.powerup_chance:
            return
        effect = self.factory.random_effect(self.world.player.stats)
        if effect:
            PowerUp(self.world, cell, effect)
