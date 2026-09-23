"""Headless end-to-end check: drives real game frames without opening a window.

Run:  .venv\\Scripts\\python.exe tests\\smoke_test.py
"""
import sys, time as pytime, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ursina import Ursina, Entity, held_keys, destroy
from ursina.shaders import lit_with_shadows_shader
import ursina

app = Ursina(window_type='none')
Entity.default_shader = lit_with_shadows_shader

from bomberman import Config, Game, setup_scene
from bomberman.board import Tile, cell_of
from bomberman.entities import Bomb, TimedFuse
from bomberman.powerups import PowerUpFactory, DEFAULT_EFFECTS
from bomberman.entities.player import PlayerStats
import random

cfg = Config()
setup_scene(cfg)
game = Game(cfg, seed=42)
game.restart()
W = game.world
C = cell_of

def run_for(s):
    end = pytime.time() + s
    while pytime.time() < end:
        app.step()

def press(k):
    game.controller.input(k)

def hold(k, s):
    held_keys[k] = 1; run_for(s); held_keys[k] = 0

def step1(k):
    """Walk exactly one cell."""
    start = W.player.cell
    held_keys[k] = 1
    for _ in range(200):
        app.step()
        if W.player.is_moving or W.player.cell != start:
            break
    held_keys[k] = 0
    while W.player.is_moving:
        app.step()

def fresh(clear_row=True):
    press('r'); app.step()
    for e in W.enemies:
        e._speed = 0
        e.position = (e.x, e.y, cfg.height - 2) if C(e)[1] < 5 else e.position
    if clear_row:
        for x in range(1, cfg.width - 1):
            if W.board.tile((x, 1)) is Tile.CRATE:
                W.destroy_crate((x, 1))
        for c in list(W.powerups):
            W.remove_powerup(c)

ok = True
def check(name, cond, detail=''):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")

try:
    b = W.board
    walls = sum(b.tile(c) is Tile.WALL for c in b.cells())
    check('arena built', walls == 82 and len(W.enemies) == 4 and C(W.player) == (1, 1),
          f'walls={walls} crates={len(W.crate_views)} enemies={len(W.enemies)}')
    check('hud initialised', 'Enemies: 4' in game.hud.stats.text, repr(game.hud.stats.text))

    # --- timed bomb + dodge around the pillar
    fresh()
    p = W.player
    step1('d')                      # (2,1)
    press('space')
    check('bomb dropped via command', (2, 1) in W.bombs)
    press('space')
    check('max bombs respected', len(W.bombs) == 1)
    step1('a')                      # (1,1)
    step1('w')                      # (1,2) - out of the bomb's line
    check('player dodged to (1,2)', C(p) == (1, 2), str(C(p)))
    run_for(2.6)
    check('bomb exploded, player survived', not W.bombs and p.alive, f'flames={sorted(W.flames)}')
    run_for(.8)
    check('flames cleared', not W.flames)

    # --- crate destruction publishes event -> spawner
    fresh(clear_row=False)
    from bomberman.board import step
    from bomberman.config import DIRECTIONS
    crate, origin = next((c, step(c, d)) for c in W.crate_views for d in DIRECTIONS
                         if b.tile(step(c, d)) is Tile.EMPTY)
    before = len(W.crate_views)
    game.systems[0].blast(origin, 1)
    check('explosion destroys crate', crate not in W.crate_views and b.tile(crate) is Tile.EMPTY,
          f'{before}->{len(W.crate_views)}')

    # --- power-up factory weighting / redundancy
    f = PowerUpFactory(random.Random(1))
    s = PlayerStats(1, 2, 4, can_kick=True, has_remote=True)
    names = {f.random_effect(s).name for _ in range(300)}
    check('owned one-time powers never drop', names == {'bomb', 'fire', 'speed'}, str(names))
    s2 = PlayerStats(1, 2, 4)
    picks = [f.random_effect(s2).name for _ in range(2000)]
    check('weights roughly respected', picks.count('bomb') > 3 * picks.count('kick') * .7,
          str({e.name: picks.count(e.name) for e in DEFAULT_EFFECTS}))

    # --- pick up power-up
    fresh()
    from bomberman.entities import PowerUp
    from bomberman.powerups import Kick, SpeedUp
    PowerUp(W, (2, 1), SpeedUp())
    step1('d')
    check('speed power-up collected', W.player.stats.speed > cfg.player_speed and not W.powerups,
          f'speed={W.player.stats.speed}')
    check('hud refreshed on pickup', 'Speed: 4.8' in game.hud.stats.text, game.hud.stats.text)

    # --- kick
    fresh()
    p = W.player; p.stats.can_kick = True; p.stats.max_bombs = 2
    Bomb(W, (3, 1), p, radius=1, fuse=TimedFuse(99))
    step1('d')                      # (2,1)
    held_keys['d'] = 1; run_for(.06); held_keys['d'] = 0   # push into bomb at (3,1)
    run_for(1.6)
    bomb = next(iter(W.bombs.values()))
    check('kicked bomb slid to far wall', bomb.cell == (cfg.width - 2, 1) and C(p) == (2, 1),
          f'bomb={bomb.cell} player={C(p)}')

    # --- remote + chain reaction
    fresh()
    p = W.player; p.stats.has_remote = True; p.stats.max_bombs = 2
    press('space')                                   # remote bomb at (1,1)
    step1('d')
    step1('d')
    step1('d')                       # (4,1)
    other = Bomb(W, (3, 1), p, radius=1, fuse=TimedFuse(99))   # in range of nothing yet
    run_for(3)
    check('remote bomb waits past normal fuse', (1, 1) in W.bombs, f'player={C(p)}')
    step1('d')                       # (5,1) out of reach of (3,1) radius 1? (4,1) is in reach
    step1('d')                       # (6,1)
    W.bombs[(1, 1)].radius = 2                        # reach (3,1) to test chaining
    press('e'); run_for(.4)
    check('E detonates remote + chains timed bomb', not W.bombs and p.alive,
          f'bombs={list(W.bombs)} player={C(p)} alive={p.alive}')

    # --- win / lose / restart freeze
    fresh()
    for e in W.enemies:
        W.add_flame(e.cell)
    app.step()
    check('win when all enemies burn', game.hud.title.text == 'YOU WIN!' and not game.accepts_player_input)
    press('space')
    check('no bombs after round over', not W.bombs)
    press('r'); app.step()
    check('restart resets', game.accepts_player_input and game.hud.title.text == '' and len(W.enemies) == 4)
    W.add_flame(W.player.cell); app.step()
    check('lose when player burns', game.hud.title.text == 'GAME OVER' and not W.player.alive)

    n1 = len(ursina.scene.entities)
    for _ in range(3):
        press('r'); run_for(.1)
    n2 = len(ursina.scene.entities)
    check('no entity leak across restarts', abs(n2 - n1) < 40, f'{n1} -> {n2}')
except Exception:
    traceback.print_exc()
    ok = False

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
