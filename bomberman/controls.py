"""Keyboard input (Command pattern). Rebinding keys or adding an action never touches game logic."""
from abc import ABC, abstractmethod

from ursina import Entity, application, held_keys

from .config import DOWN, LEFT, RIGHT, UP


class Command(ABC):
    @abstractmethod
    def execute(self, game) -> None: ...


class DropBomb(Command):
    def execute(self, game):
        if game.accepts_player_input:
            game.world.player.drop_bomb()


class Detonate(Command):
    def execute(self, game):
        if game.accepts_player_input:
            game.world.player.detonate()


class Restart(Command):
    def execute(self, game):
        game.restart()


class Quit(Command):
    def execute(self, game):
        application.quit()


DEFAULT_KEY_BINDINGS: dict[str, Command] = {
    'space': DropBomb(),
    'e': Detonate(),
    'r': Restart(),
    'escape': Quit(),
}

# checked in order, so horizontal wins when two directions are held
DEFAULT_MOVE_BINDINGS = (
    (('d', 'right arrow'), RIGHT),
    (('a', 'left arrow'), LEFT),
    (('w', 'up arrow'), UP),
    (('s', 'down arrow'), DOWN),
)


class KeyboardController(Entity):
    def __init__(self, game, key_bindings=DEFAULT_KEY_BINDINGS, move_bindings=DEFAULT_MOVE_BINDINGS):
        super().__init__()
        self.game = game
        self.key_bindings = key_bindings
        self.move_bindings = move_bindings

    def input(self, key):
        command = self.key_bindings.get(key)
        if command:
            command.execute(self.game)

    def update(self):
        if not self.game.accepts_player_input:
            return
        for keys, direction in self.move_bindings:
            if any(held_keys[k] for k in keys):
                self.game.world.player.walk(direction)
                return
