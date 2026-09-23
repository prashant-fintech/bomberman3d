from ursina import distance

from .events import Event, EventBus


class Rules:
    """Who dies this frame, and whether the round is won or lost."""

    def __init__(self, world, events: EventBus):
        self.world = world
        self.events = events

    def apply(self) -> None:
        world, player = self.world, self.world.player
        if world.is_burning(player.cell):
            self._kill_player()
        for enemy in list(world.enemies):
            if world.is_burning(enemy.cell):
                enemy.die()
                world.enemies.remove(enemy)
                self.events.publish(Event.ENEMY_KILLED, enemy=enemy)
            elif distance(enemy.position, player.position) < world.config.contact_distance:
                self._kill_player()
        if player.alive and not world.enemies:
            self.events.publish(Event.GAME_WON)

    def _kill_player(self) -> None:
        player = self.world.player
        if player.alive:
            player.die()
            self.events.publish(Event.GAME_LOST)
