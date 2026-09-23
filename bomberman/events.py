"""Observer pattern: publishers and subscribers only know about the bus, never about each other."""
from collections import defaultdict
from enum import Enum, auto
from typing import Callable


class Event(Enum):
    GAME_STARTED = auto()       # no payload
    GAME_WON = auto()           # no payload
    GAME_LOST = auto()          # no payload
    BOMB_EXPLODED = auto()      # bomb=Bomb
    CRATE_DESTROYED = auto()    # cell=Cell
    ENEMY_KILLED = auto()       # enemy=Enemy
    POWERUP_COLLECTED = auto()  # effect=PowerUpEffect


class EventBus:
    def __init__(self):
        self._handlers: dict[Event, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event: Event, handler: Callable[..., None]) -> None:
        self._handlers[event].append(handler)

    def publish(self, event: Event, **payload) -> None:
        for handler in list(self._handlers[event]):
            handler(**payload)
