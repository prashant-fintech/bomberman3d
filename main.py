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
from ursina import Entity, Ursina
from ursina.shaders import lit_with_shadows_shader

from bomberman import Config, Game, setup_scene


def main() -> None:
    app = Ursina(title='Bomberman 3D', borderless=False)
    Entity.default_shader = lit_with_shadows_shader
    config = Config()
    setup_scene(config)
    Game(config).restart()
    app.run()


if __name__ == '__main__':
    main()
