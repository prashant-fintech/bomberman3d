from .board import Tile, step
from .config import DIRECTIONS, Cell
from .entities.flame import Flame
from .events import Event, EventBus


class ExplosionSystem:
    """Turns an exploded bomb into a cross of flames. Bombs just announce they blew up; this does the rest."""

    def __init__(self, world, events: EventBus):
        self.world = world
        events.subscribe(Event.BOMB_EXPLODED, self._on_bomb_exploded)

    def _on_bomb_exploded(self, bomb) -> None:
        self.blast(bomb.cell, bomb.radius)

    def blast(self, origin: Cell, radius: int) -> None:
        world = self.world
        Flame(world, origin)
        for direction in DIRECTIONS:
            for distance in range(1, radius + 1):
                cell = step(origin, direction, distance)
                tile = world.board.tile(cell)
                if tile is Tile.WALL:
                    break
                Flame(world, cell)
                if tile is Tile.CRATE:
                    world.destroy_crate(cell)
                    break
                if cell in world.bombs:                                   # chain reaction
                    world.bombs[cell].fuse.ignite(world.config.chain_delay)
                if cell in world.powerups:
                    world.remove_powerup(cell)
