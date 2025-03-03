import numpy as np
import tcod
from rhizome.game.components import Graphic

def create_map(height, width, wall_threshold, closed=False) -> np.array:
    """
    Create a map using the 4-5 cellular automaton rule
    
    rows: the number of rows in the map
    columns: the number of columns in the map
    threshold: the initial threshold for assigning a wall
    closed: Whether the edges of the map should be closed (padded with walls)
        or left open
    """
    map = np.random.random((height, width)) <= wall_threshold
    iterating = True
    n_iters = 0
    while iterating and n_iters < 10:
        padded = np.pad(map, 1, constant_values=closed)
        r1 = np.lib.stride_tricks.sliding_window_view(padded, (3,3))
        near = r1.sum(axis=(-1,-2))
        r2 = np.lib.stride_tricks.sliding_window_view(padded,(4,4))
        far = np.pad(r2.sum(axis=(-1,-2)), (1,0),constant_values=1)
        if n_iters < 3:
            new_map = (near > 4) | (far < 2)
        else:
            new_map = near > 4

        iterating = (new_map != map).any()
        map = new_map
        n_iters += 1
    return map


def to_rgb(map, wall:Graphic, floor: Graphic)  -> np.array:
    new = np.zeros(map.shape, dtype=tcod.console.rgb_graphic)
    is_wall = map != 0
    new['ch'][is_wall] = wall.ch
    new['ch'][~is_wall] = floor.ch
    new['fg'] = floor.fg
    return new


def to_string(map: np.array, wall="x", floor="."):
    """
    Convert a map to its string representation
    """
    return "\n".join("".join(row) for row in np.where(map,wall,floor))