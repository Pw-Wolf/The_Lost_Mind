# from json import loads
from typing import Tuple

import numpy as np

import core.settings as settings

graphic_dt = np.dtype(
    [
        ("ch", np.int32),
        ("fg", "3B"),
        ("bg", "3B"),
    ]
)

tile_dt = np.dtype(
    [
        ("walkable", np.bool_),  # True if this tile can be walked over.
        ("transparent", np.bool_),  # True if this tile doesn't block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
    ]
)


def new_tile(
    *,  # Enforce the use of keywords, so that parameter order doesn't matter.
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]]
) -> np.ndarray:
    """ Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (70, 70, 70)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)

wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord(" "), (255, 255, 255), (30, 30, 30)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50)),
)


down_stairs = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(">"), (0, 0, 100), (150, 50, 150)),
    light=(ord(">"), (255, 255, 255), (170, 80, 170)),
)

if settings.data_settings['theme_classic']:
    floor = new_tile(
        walkable=True,
        transparent=True,
        dark=(ord("."), (100, 100, 100), (0, 0, 0)),
        light=(ord("."), (200, 200, 200), (0, 0, 0)),
    )
    wall = new_tile(
        walkable=False,
        transparent=False,
        dark=(ord("#"), (100, 100, 100), (0, 0, 0)),
        light=(ord("#"), (200, 200, 200), (0, 0, 0)),
    )
    down_stairs = new_tile(
        walkable=True,
        transparent=True,
        dark=(ord(">"), (100, 100, 100), (0, 0, 0)),
        light=(ord(">"), (200, 200, 200), (0, 0, 0)),
    )

elif settings.data_settings['theme_classic']:
    floor = new_tile(
        walkable=True,
        transparent=True,
        dark=(ord(" "), (255, 255, 255), (148, 176, 174)),
        light=(ord(" "), (255, 255, 255), (190, 190, 190)),
    )
    wall = new_tile(
        walkable=False,
        transparent=False,
        dark=(ord(" "), (255, 255, 255), (30, 30, 30)),
        light=(ord(" "), (255, 255, 255), (109, 136, 138)),
    )

    down_stairs = new_tile(
        walkable=True,
        transparent=True,
        dark=(ord(">"), (0, 0, 100), (150, 50, 150)),
        light=(ord(">"), (255, 255, 255), (170, 80, 170)),
    )
