"""Tunable settings and shared type aliases. Gameplay numbers live here and nowhere else."""
from dataclasses import dataclass

Cell = tuple[int, int]
Direction = tuple[int, int]

RIGHT, LEFT, UP, DOWN = (1, 0), (-1, 0), (0, 1), (0, -1)
DIRECTIONS: tuple[Direction, ...] = (RIGHT, LEFT, UP, DOWN)


@dataclass(frozen=True)
class Config:
    width: int = 15                 # odd sizes keep the pillar pattern symmetric
    height: int = 13
    fuse_seconds: float = 2.5
    chain_delay: float = 0.08       # how quickly a flame sets off a neighbouring bomb
    flame_seconds: float = 0.6
    crate_chance: float = 0.65
    powerup_chance: float = 0.35
    enemy_count: int = 4
    enemy_speed: float = 2.2
    enemy_turn_chance: float = 0.25
    player_speed: float = 4.0
    player_max_speed: float = 7.5
    speed_boost: float = 0.8
    start_bombs: int = 1
    start_fire: int = 2
    kick_speed: float = 9.0
    contact_distance: float = 0.65


class Palette:
    background = '#1b1f2a'
    floor_light = '#4a8c3f'
    floor_dark = '#428137'
    wall = '#8a8f99'
    crate = '#b5793d'
    player = '#f1f1f1'
    helmet = '#e94560'
    enemy = '#c0392b'
    bomb = '#1c1c1c'
    bomb_cord = '#8d6e63'
    remote_light_on = '#ff0000'
    remote_light_off = '#550000'
    flame_hot = '#ff5400'
    flame_bright = '#ffd166'
    win = '#7cfc00'
    lose = '#ff4d4d'
    hint = '#aaaaaa'
