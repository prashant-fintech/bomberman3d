"""Composition root: builds every system, wires them through the event bus, and runs the round state machine."""
import random
from abc import ABC

from ursina import Entity

from .config import Config
from .controls import KeyboardController
from .events import Event, EventBus
from .explosion import ExplosionSystem
from .level import LevelBuilder
from .powerups import PowerUpFactory, PowerUpSpawner
from .rules import Rules
from .ui import Hud
from .world import World


# ---------------------------------------------------------------- State pattern
class GameState(ABC):
    accepts_player_input = False

    def update(self, game: 'Game') -> None:
        pass


class Playing(GameState):
    accepts_player_input = True

    def update(self, game):
        game.rules.apply()


class RoundOver(GameState):
    """Won or lost: the world is frozen until the player restarts."""


# ---------------------------------------------------------------- game
class Game(Entity):
    def __init__(self, config: Config = Config(), seed: int | None = None):
        super().__init__()
        rng = random.Random(seed)
        self.events = EventBus()
        self.world = World(config, self.events)
        self.level_builder = LevelBuilder(config, rng)
        self.rules = Rules(self.world, self.events)
        self.systems = [
            ExplosionSystem(self.world, self.events),
            PowerUpSpawner(self.world, self.events, PowerUpFactory(rng), rng),
        ]
        self.hud = Hud(self.world, self.events)
        self.controller = KeyboardController(self)
        self.state: GameState = RoundOver()

        self.events.subscribe(Event.GAME_WON, self._end_round)
        self.events.subscribe(Event.GAME_LOST, self._end_round)

    @property
    def accepts_player_input(self) -> bool:
        return self.state.accepts_player_input

    def restart(self) -> None:
        self.world.clear()
        self.level_builder.build(self.world)
        self.state = Playing()
        self.events.publish(Event.GAME_STARTED)

    def update(self):
        self.state.update(self)

    def _end_round(self) -> None:
        self.state = RoundOver()
        self.world.frozen = True
