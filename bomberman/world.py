"""Live state of one round, plus the spatial questions entities ask about it.

Entities receive the World in their constructor instead of reaching for globals, so the
dependency is explicit and a round can be torn down and rebuilt cleanly.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Entity, destroy

from .board import Board, Tile, cell_of
from .config import Cell, Config
from .events import Event, EventBus

if TYPE_CHECKING:
    from .entities.bomb import Bomb
    from .entities.enemy import Enemy
    from .entities.player import Player
    from .entities.powerup import PowerUp
    from .powerups import PowerUpEffect


class World:
    def __init__(self, config: Config, events: EventBus):
        self.config = config
        self.events = events
        self.board = Board(config.width, config.height)
        self.crate_views: dict[Cell, Entity] = {}
        self.bombs: dict[Cell, Bomb] = {}
        self.flames: dict[Cell, int] = {}          # cell -> number of overlapping flames
        self.powerups: dict[Cell, PowerUp] = {}
        self.enemies: list[Enemy] = []
        self.player: Player | None = None
        self.frozen = False                        # true once the round is over
        self._entities: list[Entity] = []

    # ------------------------------------------------------------ lifecycle
    def track(self, entity: Entity) -> Entity:
        """Register an entity so it is destroyed with the round (Ursina's destroy() isn't recursive)."""
        self._entities.append(entity)
        return entity

    def spawn(self, **kwargs) -> Entity:
        return self.track(Entity(**kwargs))

    def clear(self) -> None:
        for entity in self._entities:
            destroy(entity)
        self._entities.clear()
        self.board.clear()
        for registry in (self.crate_views, self.bombs, self.flames, self.powerups):
            registry.clear()
        self.enemies.clear()
        self.player = None
        self.frozen = False

    # ------------------------------------------------------------ queries
    def is_blocked(self, cell: Cell) -> bool:
        return self.board.is_solid(cell) or cell in self.bombs

    def is_burning(self, cell: Cell) -> bool:
        return cell in self.flames

    def has_creature(self, cell: Cell) -> bool:
        creatures = [*self.enemies, self.player] if self.player else self.enemies
        return any(c.alive and cell_of(c) == cell for c in creatures)

    def bombs_owned_by(self, owner) -> list[Bomb]:
        return [b for b in self.bombs.values() if b.owner is owner]

    # ------------------------------------------------------------ mutations
    def add_flame(self, cell: Cell) -> None:
        self.flames[cell] = self.flames.get(cell, 0) + 1

    def remove_flame(self, cell: Cell) -> None:
        self.flames[cell] -= 1
        if self.flames[cell] <= 0:
            del self.flames[cell]

    def destroy_crate(self, cell: Cell) -> None:
        self.board.set_tile(cell, Tile.EMPTY)
        destroy(self.crate_views.pop(cell))
        self.events.publish(Event.CRATE_DESTROYED, cell=cell)

    def remove_powerup(self, cell: Cell) -> None:
        destroy(self.powerups.pop(cell))

    def take_powerup(self, cell: Cell) -> PowerUpEffect | None:
        powerup = self.powerups.get(cell)
        if powerup is None:
            return None
        self.remove_powerup(cell)
        return powerup.effect
