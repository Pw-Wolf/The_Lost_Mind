from __future__ import annotations

import random
from typing import TYPE_CHECKING, Dict, Iterator, List, Tuple

import tcod

import game.entity_factories as entity_factories
import core.tile_types as tile_types
from game.game_map import GameMap

if TYPE_CHECKING:
    from core.engine import Engine
    from game.entity import Entity

# Maximum items by floor level
max_items_by_floor = [
    (1, 1),
    (4, 2),
    (8, 1),
    (9, 2),
    (11, 3),
    (12, 1),
    (14, 3),
]

# Maximum monsters by floor level
max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
    (8, 6),
    (10, 7),
    (15, 8),
    (30, 15),
]

# Modifier base stats for monsters by floor level
modifier_base_stats = [
    (50, 6),
    (40, 5),
    (30, 4),
    (20, 3),
    (15, 2),
    (12, 1.75),
    (8, 1.5),
    (5, 1),
    (3, 0.5),
    (1, 0.25)
]

# Item chances by floor level
item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 40)],
    2: [(entity_factories.confusion_scroll, 15), (entity_factories.dull_dagger, 3), (entity_factories.leather_armor, 5)],
    3: [(entity_factories.dagger, 3), (entity_factories.sharp_dagger, 2)],
    4: [(entity_factories.lightning_scroll, 8), (entity_factories.health_potion_big, 10), (entity_factories.dull_sword, 2)],
    6: [(entity_factories.fireball_scroll, 2), (entity_factories.sword, 2)],
    8: [(entity_factories.sharp_sword, 1), (entity_factories.chain_mail, 3)],
    10: [(entity_factories.iron_armor, 2)],
    12: [(entity_factories.diamond_armor, 1)]
}

# Enemy chances by floor level
enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],
    5: [(entity_factories.troll, 30), (entity_factories.goblin, 2)],
    8: [(entity_factories.troll, 60), (entity_factories.goblin, 4)],
}


def get_max_value_for_floor(max_value_by_floor: List[Tuple[int, int]], floor: int) -> int:
    """
    Get the maximum value for the given floor level.

    :param max_value_by_floor: List of tuples containing floor level and value.
    :param floor: Current floor level.
    :return: Maximum value for the given floor level.
    """
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    """
    Get a list of entities at random based on weighted chances for the given floor level.

    :param weighted_chances_by_floor: Dictionary of floor levels and their corresponding entity chances.
    :param number_of_entities: Number of entities to get.
    :param floor: Current floor level.
    :return: List of randomly chosen entities.
    """
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initialize a new RectangularRoom instance.

        :param x: X coordinate of the top-left corner.
        :param y: Y coordinate of the top-left corner.
        :param width: Width of the room.
        :param height: Height of the room.
        """
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """
        Get the center coordinates of the room.

        :return: Tuple containing the center coordinates (x, y).
        """
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """
        Get the inner area of the room as a 2D array index.

        :return: Tuple containing slices for the inner area.
        """
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """
        Check if this room intersects with another RectangularRoom.

        :param other: Another RectangularRoom instance.
        :return: True if the rooms intersect, otherwise False.
        """
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int, multiplier: Dict[str, bool]) -> Dict[str, bool]:
    """
    Place entities (monsters and items) in the given room.

    :param room: RectangularRoom instance.
    :param dungeon: GameMap instance.
    :param floor_number: Current floor level.
    :param multiplier: Dictionary to track if monster stats have been modified.
    :return: Updated multiplier dictionary.
    """
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )
    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for lvl, mod in modifier_base_stats:
        if floor_number >= lvl:
            for monster in monsters:
                if multiplier[monster.name] and len(monsters) > 0:
                    monster.fighter.base_defense = monster.fighter.default_base_defense * mod
                    monster.fighter.base_power = monster.fighter.default_base_power * mod
                    monster.fighter.max_hp = monster.fighter.default_max_hp * mod
                    monster.fighter._hp = monster.fighter.default_max_hp * mod

                    multiplier[monster.name] = False

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity.spawn(dungeon, x, y)

    return multiplier


def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """
    Create an L-shaped tunnel between two points.

    :param start: Starting coordinates (x, y).
    :param end: Ending coordinates (x, y).
    :return: Iterator of coordinates for the tunnel.
    """
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    engine: Engine,
    screen_width: int,
    screen_height: int,
    player
) -> GameMap:
    """
    Generate a new dungeon map.

    :param max_rooms: Maximum number of rooms.
    :param room_min_size: Minimum size of a room.
    :param room_max_size: Maximum size of a room.
    :param map_width: Width of the map.
    :param map_height: Height of the map.
    :param engine: Instance of the Engine class.
    :param screen_width: Width of the screen.
    :param screen_height: Height of the screen.
    :param player: The player entity.
    :return: Generated GameMap instance.
    """
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player], player=player, screen_height=screen_height, screen_width=screen_width)

    rooms: List[RectangularRoom] = []
    center_of_last_room = (0, 0)

    multiplier = {
        "Troll": True,
        "Orc": True,
        "Goblin": True,
    }

    for _ in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(screen_width // 2, dungeon.width - room_width - 1 - screen_width)
        y = random.randint(screen_height // 2, dungeon.height - room_height - 1 - screen_height)

        new_room = RectangularRoom(x, y, room_width, room_height)

        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.

        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first ro  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.om, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        multiplier = place_entities(new_room, dungeon, engine.game_world.current_floor, multiplier)

        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        rooms.append(new_room)

    multiplier = {
        "Troll": True,
        "Orc": True,
        "Goblin": True,
    }

    return dungeon
