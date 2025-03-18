from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Iterator, Optional

import numpy as np  # type: ignore
from tcod.console import Console

import core.tile_types as tile_types
from game.entity import Actor, Item

if TYPE_CHECKING:
    from core.engine import Engine
    from game.entity import Entity

class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, screen_width: int, screen_height: int, player, entities: Iterable[Entity] = ()
    ):
        """
        Initializes a new instance of the GameMap class.

        :param engine: Instance of the Engine class.
        :param width: Width of the map.
        :param height: Height of the map.
        :param screen_width: Width of the screen.
        :param screen_height: Height of the screen.
        :param player: The player.
        :param entities: Entities on the map.
        """
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        # Fields that indicate visible and explored tiles
        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen before

        self.downstairs_location = (0, 0)

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center = self.screen_width // 2, self.screen_height // 2
        self.player = player

    @property
    def gamemap(self) -> GameMap:
        """
        Returns the instance of the GameMap class.
        """
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """
        Iterates over all living actors on the map.

        :return: Iterator over living actors.
        """
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        """
        Iterates over all items on the map.

        :return: Iterator over items.
        """
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Entity]:
        """
        Returns the entity that blocks movement at the given location.

        :param location_x: X coordinate of the location.
        :param location_y: Y coordinate of the location.
        :return: Entity that blocks movement or None if there is no such entity.
        """
        for entity in self.entities:
            if (
                entity.blocks_movement
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity

        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        """
        Returns the actor at the given location.

        :param x: X coordinate of the location.
        :param y: Y coordinate of the location.
        :return: Actor at the location or None if there is no actor.
        """
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """
        Checks if the given location is within the bounds of the map.

        :param x: X coordinate of the location.
        :param y: Y coordinate of the location.
        :return: True if the location is within bounds, otherwise False.
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console, player_x: int, player_y: int) -> None:
        """
        Renders the map.

        If a tile is in the "visible" array, draw it with the "light" colors.
        If it isn't, but it's in the "explored" array, draw it with the "dark" colors.
        Otherwise, the default is "SHROUD".

        :param console: Console for drawing.
        :param player_x: X coordinate of the player.
        :param player_y: Y coordinate of the player.
        """
        console.rgb[0: self.width, 0: self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )[player_x - self.center[0]:player_x + self.center[0], player_y - self.center[1]:player_y + self.center[1]]

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        first_pixel = self.player.x - self.center[0], self.player.y - self.center[1]

        for entity in entities_sorted_for_rendering:
            if entity.char == "@":
                continue

            if self.visible[entity.x, entity.y]:
                entity_x = entity.x - first_pixel[0]
                entity_y = entity.y - first_pixel[1]
                if abs(entity.x - self.player.x) < self.center[0] + 1 and abs(entity.y - self.player.y) < self.center[1] + 1:
                    console.print(entity_x, entity_y, entity.char, fg=entity.color)

        console.print(self.center[0], self.center[1], self.player.char, fg=self.player.color)


class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        map_width: int,
        map_height: int,
        max_rooms: int,
        room_min_size: int,
        room_max_size: int,
        current_floor: int = 0,
        screen_width: int,
        screen_height: int,
        player
    ):
        """
        Initializes a new instance of the GameWorld class.

        :param engine: Instance of the Engine class.
        :param map_width: Width of the map.
        :param map_height: Height of the map.
        :param max_rooms: Maximum number of rooms.
        :param room_min_size: Minimum size of a room.
        :param room_max_size: Maximum size of a room.
        :param current_floor: Current floor level.
        :param screen_width: Width of the screen.
        :param screen_height: Height of the screen.
        :param player: The player.
        """
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.current_floor = current_floor

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player = player

    def generate_floor(self) -> None:
        """
        Generates a new floor by incrementing the current floor level and creating a new dungeon map.

        The map dimensions are increased by 10 units in both width and height for each new floor.
        """
        from game.procgen import generate_dungeon

        self.current_floor += 1

        self.engine.game_map = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            engine=self.engine,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            player=self.player
        )
        self.map_width += 10
        self.map_height += 10