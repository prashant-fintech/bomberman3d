from ursina import Text, Vec2, color, window

from .config import Palette
from .events import Event, EventBus


class Hud:
    """Stats line and win/lose banner. Redraws only when an event says something changed."""

    def __init__(self, world, events: EventBus):
        self.world = world
        self.stats = Text(text='', position=window.top_left + Vec2(.02, -.02), scale=1.1)
        Text(text='WASD move  |  Space bomb  |  E detonate  |  R restart',
             position=window.bottom_left + Vec2(.02, .04), scale=.9, color=color.hex(Palette.hint))
        self.title = Text(text='', origin=(0, 0), scale=3, y=.12)
        self.subtitle = Text(text='', origin=(0, 0), scale=1.2, y=.02)

        events.subscribe(Event.GAME_STARTED, self._on_start)
        events.subscribe(Event.GAME_WON, lambda: self._banner('YOU WIN!', Palette.win))
        events.subscribe(Event.GAME_LOST, lambda: self._banner('GAME OVER', Palette.lose))
        events.subscribe(Event.ENEMY_KILLED, lambda enemy: self.refresh())
        events.subscribe(Event.POWERUP_COLLECTED, lambda effect: self.refresh())

    def refresh(self) -> None:
        s = self.world.player.stats
        self.stats.text = (f'Enemies: {len(self.world.enemies)}    Bombs: {s.max_bombs}    '
                           f'Range: {s.fire}    Speed: {s.speed:.1f}'
                           + ('    [Kick]' if s.can_kick else '')
                           + ('    [Remote: E]' if s.has_remote else ''))

    def _on_start(self) -> None:
        self.title.text = self.subtitle.text = ''
        self.refresh()

    def _banner(self, text: str, hex_color: str) -> None:
        self.title.text = text
        self.title.color = color.hex(hex_color)
        self.subtitle.text = 'Press R to play again'
