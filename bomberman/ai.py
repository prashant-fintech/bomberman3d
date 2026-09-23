"""Enemy behaviour (Strategy pattern). Add a new AI by subclassing Brain; Enemy needs no changes."""
import random
from abc import ABC, abstractmethod

from .config import Direction


class Brain(ABC):
    @abstractmethod
    def next_direction(self, enemy, options: list[Direction]) -> Direction:
        """Pick one of the open directions. `options` is never empty."""


class WanderBrain(Brain):
    """Keeps walking the same way, occasionally turning at random."""

    def __init__(self, turn_chance: float, rng: random.Random):
        self.turn_chance = turn_chance
        self.rng = rng
        self.heading: Direction | None = None

    def next_direction(self, enemy, options):
        if self.heading not in options or self.rng.random() < self.turn_chance:
            self.heading = self.rng.choice(options)
        return self.heading
