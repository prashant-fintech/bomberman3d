"""The arena as pure data: which cells are walls, crates or open floor. No rendering here."""
from enum import Enum

from .config import Cell, Direction


class Tile(Enum):
    EMPTY = 0
    WALL = 1
    CRATE = 2


class Board:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self._tiles: dict[Cell, Tile] = {}

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def tile(self, cell: Cell) -> Tile:
        if not self.in_bounds(cell):
            return Tile.WALL
        return self._tiles.get(cell, Tile.EMPTY)

    def set_tile(self, cell: Cell, tile: Tile) -> None:
        if tile is Tile.EMPTY:
            self._tiles.pop(cell, None)
        else:
            self._tiles[cell] = tile

    def is_solid(self, cell: Cell) -> bool:
        return self.tile(cell) is not Tile.EMPTY

    def cells(self):
        for x in range(self.width):
            for z in range(self.height):
                yield x, z

    def clear(self) -> None:
        self._tiles.clear()


def cell_of(entity) -> Cell:
    """The grid cell an entity is (mostly) standing on."""
    return round(entity.x), round(entity.z)


def step(cell: Cell, direction: Direction, distance: int = 1) -> Cell:
    return cell[0] + direction[0] * distance, cell[1] + direction[1] * distance


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
