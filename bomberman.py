"""
Bomberman 3D - built with Ursina.

Controls:
    WASD / arrow keys   move
    Space               drop bomb
    E                   detonate remote bombs (needs the remote power-up)
    R                   restart
    Esc                 quit

Blow up all the enemies to win. Crates may hide power-ups:
    blue   = +1 bomb      pink = +1 blast range      yellow = +speed
    green  = kick (walk into a bomb to send it sliding)
    purple = remote detonator (bombs wait until you press E)
"""
import math
import random

from ursina import *
from ursina.shaders import lit_with_shadows_shader, unlit_shader

# ---------------------------------------------------------------- settings
W, H = 15, 13                # grid size (odd numbers keep the pillar pattern symmetric)
FUSE = 2.5                   # seconds before a bomb explodes
FLAME_TIME = 0.6             # seconds a flame stays deadly
CRATE_CHANCE = 0.65
POWERUP_CHANCE = 0.35
ENEMY_COUNT = 4
PLAYER_SPEED = 4.0
ENEMY_SPEED = 2.2
KICK_SPEED = 9.0             # cells per second for a kicked bomb
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

POWERUPS = {  # kind -> (color, drop weight)
    'bomb':   (color.hex('#3a86ff'), 3),
    'fire':   (color.hex('#ff006e'), 3),
    'speed':  (color.hex('#ffbe0b'), 2),
    'kick':   (color.hex('#2ec4b6'), 1),
    'remote': (color.hex('#9b5de5'), 1),
}

app = Ursina(title='Bomberman 3D', borderless=False)
window.color = color.hex('#1b1f2a')
Entity.default_shader = lit_with_shadows_shader

# ---------------------------------------------------------------- game state
level_entities = []   # everything belonging to the current round, destroyed on restart
grid = {}             # cell -> 'wall' | 'crate'
crates = {}           # cell -> crate entity
bombs = {}            # cell -> Bomb
flames = {}           # cell -> number of active flames on that cell
powerups = {}         # cell -> PowerUp
enemies = []
player = None
game_over = False


def track(e):
    level_entities.append(e)
    return e


def spawn(**kwargs):
    return track(Entity(**kwargs))


def cell_of(e):
    return (round(e.x), round(e.z))


def in_bounds(c):
    return 0 <= c[0] < W and 0 <= c[1] < H


def blocked(c):
    return not in_bounds(c) or c in grid or c in bombs


# ---------------------------------------------------------------- entities
class Mover(Entity):
    """Something that walks cell-to-cell on the grid."""

    def __init__(self, speed, **kwargs):
        super().__init__(**kwargs)
        track(self)
        self.speed = speed
        self.target = None
        self.alive = True

    def step_towards_target(self):
        if self.target is None:
            return
        goal = Vec3(self.target[0], self.y, self.target[1])
        delta = goal - self.position
        step = self.speed * time.dt
        if delta.length() <= step:
            self.position = goal
            self.target = None
        else:
            self.position += delta.normalized() * step


class Player(Mover):
    def __init__(self, cell):
        super().__init__(PLAYER_SPEED, model='sphere', color=color.hex('#f1f1f1'), scale=.75,
                         position=(cell[0], .4, cell[1]))
        spawn(parent=self, model='sphere', color=color.hex('#e94560'), scale=(.65, .45, .65), y=.4)  # helmet
        for sx in (-.18, .18):
            spawn(parent=self, model='sphere', color=color.black, scale=.15, position=(sx, .08, -.45))
        self.max_bombs = 1
        self.fire = 2
        self.active_bombs = 0
        self.can_kick = False
        self.has_remote = False

    def update(self):
        if not self.alive or game_over:
            return
        if self.target is None:
            dx = bool(held_keys['d'] or held_keys['right arrow']) - bool(held_keys['a'] or held_keys['left arrow'])
            dz = bool(held_keys['w'] or held_keys['up arrow']) - bool(held_keys['s'] or held_keys['down arrow'])
            if dx:
                dz = 0
            if dx or dz:
                here = cell_of(self)
                nxt = (here[0] + dx, here[1] + dz)
                if not blocked(nxt):
                    self.target = nxt
                elif self.can_kick and nxt in bombs:
                    bombs[nxt].kick((dx, dz))
        self.step_towards_target()

        c = cell_of(self)
        if c in powerups:
            self.collect(powerups.pop(c))

    def collect(self, p):
        if p.kind == 'bomb':
            self.max_bombs += 1
        elif p.kind == 'fire':
            self.fire += 1
        elif p.kind == 'speed':
            self.speed = min(self.speed + .8, 7.5)
        elif p.kind == 'kick':
            self.can_kick = True
        elif p.kind == 'remote':
            self.has_remote = True
        destroy(p)

    def drop_bomb(self):
        c = cell_of(self)
        if self.alive and c not in bombs and self.active_bombs < self.max_bombs:
            Bomb(c, self, remote=self.has_remote)

    def detonate(self):
        for b in list(bombs.values()):
            if b.owner is self and b.remote:
                b.timer = 0


class Enemy(Mover):
    def __init__(self, cell):
        super().__init__(ENEMY_SPEED, model='sphere', color=color.hex('#c0392b'), scale=.7,
                         position=(cell[0], .35, cell[1]))
        for sx in (-.2, .2):
            spawn(parent=self, model='sphere', color=color.white, scale=.28, position=(sx, .15, -.4))
            spawn(parent=self, model='sphere', color=color.black, scale=.13, position=(sx, .15, -.52))
        self.dir = random.choice(DIRS)
        self.phase = random.random() * 10

    def update(self):
        if not self.alive:
            return
        self.y = .35 + abs(math.sin(time.time() * 7 + self.phase)) * .12
        if game_over:
            return
        if self.target is None:
            here = cell_of(self)
            options = [d for d in DIRS if not blocked((here[0] + d[0], here[1] + d[1]))]
            if not options:
                return
            if self.dir not in options or random.random() < .25:
                self.dir = random.choice(options)
            self.target = (here[0] + self.dir[0], here[1] + self.dir[1])
        self.step_towards_target()


class Bomb(Entity):
    def __init__(self, cell, owner, remote=False):
        super().__init__(model='sphere', color=color.hex('#1c1c1c'), scale=.8, position=(cell[0], .4, cell[1]))
        track(self)
        spawn(parent=self, model='cube', color=color.hex('#8d6e63'), scale=(.12, .35, .12), y=.55)
        self.cell, self.owner, self.done = cell, owner, False
        self.remote = remote
        self.timer = math.inf if remote else FUSE      # remote bombs wait for E (or another blast)
        if remote:
            self.light = spawn(parent=self, model='sphere', color=color.red, shader=unlit_shader,
                               scale=.22, y=.78)
        self.slide_dir = None
        self.slide_target = None
        owner.active_bombs += 1
        bombs[cell] = self

    def kick(self, direction):
        if self.slide_dir is None and self._next_free(direction):
            self.slide_dir = direction

    def _next_free(self, direction):
        nxt = (self.cell[0] + direction[0], self.cell[1] + direction[1])
        if blocked(nxt) or any(cell_of(e) == nxt for e in enemies) or cell_of(player) == nxt:
            return None
        return nxt

    def update(self):
        self.timer -= time.dt
        if self.remote:
            self.light.color = color.red if int(time.time() * 4) % 2 else color.hex('#550000')
            self.scale = .8
        else:
            rate = 18 if self.timer < 1 else 7
            self.scale = .8 * (1 + .1 * math.sin(time.time() * rate))
        if self.slide_dir:
            self.slide()
        if self.timer <= 0:
            self.explode()

    def slide(self):
        if self.slide_target is None:
            self.slide_target = self._next_free(self.slide_dir)
            if self.slide_target is None:          # hit something: stop dead on this cell
                self.slide_dir = None
                self.position = Vec3(self.cell[0], self.y, self.cell[1])
                return
        goal = Vec3(self.slide_target[0], self.y, self.slide_target[1])
        delta = goal - self.position
        step = KICK_SPEED * time.dt
        if delta.length() <= step:
            self.position = goal
            bombs.pop(self.cell, None)
            self.cell = self.slide_target
            bombs[self.cell] = self
            self.slide_target = None
        else:
            self.position += delta.normalized() * step

    def explode(self):
        if self.done:
            return
        self.done = True
        bombs.pop(self.cell, None)
        if self.slide_target is not None:           # exploded mid-slide: blast from wherever it is now
            self.cell = cell_of(self)
        self.owner.active_bombs -= 1
        Flame(self.cell)
        for dx, dz in DIRS:
            for i in range(1, self.owner.fire + 1):
                c = (self.cell[0] + dx * i, self.cell[1] + dz * i)
                kind = grid.get(c)
                if not in_bounds(c) or kind == 'wall':
                    break
                Flame(c)
                if kind == 'crate':
                    break_crate(c)
                    break
                if c in bombs:                      # chain reaction
                    bombs[c].timer = min(bombs[c].timer, .08)
                if c in powerups:
                    destroy(powerups.pop(c))
        destroy(self)


class Flame(Entity):
    def __init__(self, cell):
        super().__init__(model='cube', color=color.hex('#ff8c1a'), shader=unlit_shader,
                         scale=.95, position=(cell[0], .45, cell[1]))
        track(self)
        self.cell, self.timer = cell, FLAME_TIME
        flames[cell] = flames.get(cell, 0) + 1

    def update(self):
        self.timer -= time.dt
        k = max(self.timer / FLAME_TIME, 0)
        self.scale = .35 + .6 * k
        self.color = color.hex('#ffd166') if int(self.timer * 20) % 2 else color.hex('#ff5400')
        if self.timer <= 0:
            flames[self.cell] -= 1
            if flames[self.cell] <= 0:
                del flames[self.cell]
            destroy(self)


class PowerUp(Entity):
    def __init__(self, cell):
        owned = {'kick': player.can_kick, 'remote': player.has_remote}
        kinds = [k for k in POWERUPS if not owned.get(k)]     # don't drop one-time powers you already have
        self.kind = random.choices(kinds, weights=[POWERUPS[k][1] for k in kinds])[0]
        super().__init__(model='cube', color=POWERUPS[self.kind][0], shader=unlit_shader, scale=.42,
                         position=(cell[0], .4, cell[1]), rotation=(45, 0, 45))
        track(self)
        powerups[cell] = self

    def update(self):
        self.rotation_y += 120 * time.dt


def break_crate(c):
    destroy(crates.pop(c))
    del grid[c]
    if random.random() < POWERUP_CHANCE:
        PowerUp(c)


# ---------------------------------------------------------------- level setup
def new_game():
    global player, game_over
    for e in level_entities:
        destroy(e)
    level_entities.clear()
    for d in (grid, crates, bombs, flames, powerups):
        d.clear()
    enemies.clear()
    game_over = False
    message.text = sub_message.text = ''

    player_spawn = (1, 1)
    corner_spawns = [(W - 2, H - 2), (W - 2, 1), (1, H - 2)]
    safe = set()
    for sx, sz in [player_spawn] + corner_spawns:
        safe.add((sx, sz))
        for dx, dz in DIRS:
            safe.add((sx + dx, sz + dz))

    for x in range(W):
        for z in range(H):
            c = (x, z)
            shade = '#4a8c3f' if (x + z) % 2 else '#428137'
            spawn(model='cube', color=color.hex(shade), scale=(1, .1, 1), position=(x, -.05, z))
            is_border = x in (0, W - 1) or z in (0, H - 1)
            is_pillar = x % 2 == 0 and z % 2 == 0
            if is_border or is_pillar:
                spawn(model='cube', texture='brick', color=color.hex('#8a8f99'), position=(x, .5, z))
                grid[c] = 'wall'
            elif c not in safe and random.random() < CRATE_CHANCE:
                crates[c] = spawn(model='cube', texture='white_cube', color=color.hex('#b5793d'),
                                  scale=.9, position=(x, .45, z))
                grid[c] = 'crate'

    player = Player(player_spawn)

    far_empty = [(x, z) for x in range(W) for z in range(H)
                 if (x, z) not in grid and abs(x - 1) + abs(z - 1) > 8 and (x, z) not in corner_spawns]
    extra = random.sample(far_empty, max(0, min(ENEMY_COUNT - len(corner_spawns), len(far_empty))))
    for c in corner_spawns[:ENEMY_COUNT] + extra:
        enemies.append(Enemy(c))


def end_game(text, col):
    global game_over
    game_over = True
    message.text = text
    message.color = col
    sub_message.text = 'Press R to play again'


def kill_player():
    if not player.alive:
        return
    player.alive = False
    player.animate_scale(0, duration=.4)
    end_game('GAME OVER', color.hex('#ff4d4d'))


# ---------------------------------------------------------------- main loop
def update():
    hud.text = (f'Enemies: {len(enemies)}    Bombs: {player.max_bombs}    '
                f'Range: {player.fire}    Speed: {player.speed:.1f}'
                + ('    [Kick]' if player.can_kick else '')
                + ('    [Remote: E]' if player.has_remote else ''))
    if game_over:
        return
    if cell_of(player) in flames:
        kill_player()
    for e in enemies[:]:
        if cell_of(e) in flames:
            e.alive = False
            enemies.remove(e)
            e.animate_scale(0, duration=.3)
        elif distance(e.position, player.position) < .65:
            kill_player()
    if not game_over and not enemies:
        end_game('YOU WIN!', color.hex('#7CFC00'))


def input(key):
    if key == 'space' and not game_over:
        player.drop_bomb()
    elif key == 'e' and not game_over:
        player.detonate()
    elif key == 'r':
        new_game()
    elif key == 'escape':
        application.quit()


# ---------------------------------------------------------------- camera, light, UI
camera.position = ((W - 1) / 2, 17, -5.5)
camera.look_at(Vec3((W - 1) / 2, 0, (H - 1) / 2 - .5))
sun = DirectionalLight(shadows=False)
sun.look_at(Vec3(.6, -1, .8))
AmbientLight(color=color.hex('#8a8a8a'))

hud = Text(text='', position=window.top_left + Vec2(.02, -.02), scale=1.1)
Text(text='WASD move  |  Space bomb  |  E detonate  |  R restart', position=window.bottom_left + Vec2(.02, .04),
     scale=.9, color=color.hex('#aaaaaa'))
message = Text(text='', origin=(0, 0), scale=3, y=.12)
sub_message = Text(text='', origin=(0, 0), scale=1.2, y=.02)

new_game()

if __name__ == '__main__':
    app.run()
