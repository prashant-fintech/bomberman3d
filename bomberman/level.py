import random

from ursina import color

from .ai import WanderBrain
from .board import Tile, manhattan
from .config import DIRECTIONS, Cell, Config, Palette
from .entities.enemy import Enemy
from .entities.player import Player

PLAYER_SPAWN: Cell = (1, 1)
MIN_ENEMY_DISTANCE = 9     # extra enemies spawn at least this far (in steps) from the player


class LevelBuilder:
    """Builds a fresh random arena into the World: floor, walls, crates, player, enemies."""

    def __init__(self, config: Config, rng: random.Random):
        self.config = config
        self.rng = rng

    def build(self, world) -> None:
        corners = self._enemy_corners()
        safe = self._safe_zone([PLAYER_SPAWN, *corners])
        self._build_arena(world, safe)
        world.player = Player(world, PLAYER_SPAWN)
        self._spawn_enemies(world, corners)

    # ------------------------------------------------------------ layout
    def _enemy_corners(self) -> list[Cell]:
        w, h = self.config.width, self.config.height
        return [(w - 2, h - 2), (w - 2, 1), (1, h - 2)]

    @staticmethod
    def _safe_zone(spawns: list[Cell]) -> set[Cell]:
        """Spawn cells plus their neighbours stay crate-free so nobody starts boxed in."""
        return {(x + dx, z + dz) for x, z in spawns for dx, dz in [(0, 0), *DIRECTIONS]}

    def _build_arena(self, world, safe: set[Cell]) -> None:
        board = world.board
        for x, z in board.cells():
            shade = Palette.floor_light if (x + z) % 2 else Palette.floor_dark
            world.spawn(model='cube', color=color.hex(shade), scale=(1, .1, 1), position=(x, -.05, z))

            is_border = x in (0, board.width - 1) or z in (0, board.height - 1)
            is_pillar = x % 2 == 0 and z % 2 == 0
            if is_border or is_pillar:
                board.set_tile((x, z), Tile.WALL)
                world.spawn(model='cube', texture='brick', color=color.hex(Palette.wall), position=(x, .5, z))
            elif (x, z) not in safe and self.rng.random() < self.config.crate_chance:
                board.set_tile((x, z), Tile.CRATE)
                world.crate_views[(x, z)] = world.spawn(model='cube', texture='white_cube', scale=.9,
                                                        color=color.hex(Palette.crate), position=(x, .45, z))

    def _spawn_enemies(self, world, corners: list[Cell]) -> None:
        far_open = [c for c in world.board.cells()
                    if not world.board.is_solid(c) and c not in corners
                    and manhattan(c, PLAYER_SPAWN) >= MIN_ENEMY_DISTANCE]
        extra_needed = max(0, self.config.enemy_count - len(corners))
        cells = corners[:self.config.enemy_count] + self.rng.sample(far_open, min(extra_needed, len(far_open)))
        for cell in cells:
            brain = WanderBrain(self.config.enemy_turn_chance, self.rng)
            world.enemies.append(Enemy(world, cell, brain))
