# Bomberman 3D

A 3D Bomberman clone in Python using [Ursina](https://www.ursinaengine.org/).

```
.venv\Scripts\python.exe main.py          # play
.venv\Scripts\python.exe tests\smoke_test.py   # headless end-to-end check
```

**Controls:** WASD / arrows move · Space bomb · E detonate remote bombs · R restart · Esc quit

**Power-ups:** blue +1 bomb · pink +1 range · yellow +speed · green kick · purple remote detonator

## Layout

```
main.py                  entry point: create the app, scene and Game
bomberman/
  config.py              all tunable numbers + colour palette
  events.py              EventBus + Event enum
  board.py               grid data (walls/crates), no rendering
  world.py               live state of one round + spatial queries
  game.py                composition root + round state machine
  level.py               LevelBuilder: arena, player, enemies
  explosion.py           ExplosionSystem: bomb -> cross of flames
  rules.py               deaths, win/lose
  powerups.py            PowerUpEffect classes, weighted factory, spawner
  ai.py                  enemy Brain strategies
  controls.py            key -> Command bindings, KeyboardController
  ui.py                  HUD (event driven)
  scene.py               camera, lights, background
  entities/
    grid_mover.py        base class for cell-to-cell movement
    player.py, enemy.py, bomb.py, flame.py, powerup.py
    fuses.py             TimedFuse / RemoteFuse strategies
```

## Design

| Pattern | Where | What it buys |
|---|---|---|
| Observer | `EventBus` | Bombs announce `BOMB_EXPLODED`; the explosion system, power-up spawner and HUD react without the bomb knowing they exist. |
| Strategy | `Fuse`, `Brain` | New bomb timing (e.g. proximity mine) or enemy AI (e.g. chaser) = one new class; `Bomb` and `Enemy` don't change. |
| Command | `controls.py` | Keys map to command objects, so rebinding or adding an action doesn't touch game logic. |
| State | `Playing` / `RoundOver` | Input and rules are gated by the current state instead of `if game_over` checks everywhere. |
| Factory | `PowerUpFactory` | Weighted random drops, skipping one-time powers the player already has. |
| Builder | `LevelBuilder` | Level generation is isolated from the game loop and can be swapped for hand-made maps. |
| Template method | `GridMover` | Shared movement; subclasses only decide where to go. |

SOLID in practice:

- **Single responsibility:** `Board` is data, `World` is round state, `Rules` judges, `Hud` draws.
- **Open/closed:** adding a power-up is one `PowerUpEffect` subclass plus an entry in `DEFAULT_EFFECTS`.
- **Liskov:** every `Fuse` and `Brain` can stand in for another; `Fuse.trigger()` defaults to a safe no-op.
- **Interface segregation:** power-up effects only see `PlayerStats`, not the whole `Player`.
- **Dependency inversion:** entities get the `World` through their constructor, with no globals; `Game` is the only place that wires concrete classes together.
