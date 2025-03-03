from tcod.ecs import Registry
from random import Random
from .components import *
from .caves import create_map, to_rgb
from .tags import *
from typing import Dict

WallTile = Graphic(ord("X"))
FloorTile = Graphic(ord("."))

YELLOW = [0xc6, 0xd3, 0x13]

def new_world(settings: Dict) -> Registry:
    world = Registry()
    # global RNG
    rng = world[None].components[Random] = Random()
    # initialize the map
    map_settings = settings["map"]
    map = create_map(closed=True,**map_settings)
    
    free_positions = [idx for idx, value in np.ndenumerate(map) if not value]
    rgb_map = to_rgb(map, WallTile.ch, FloorTile.ch)
    world[None].components[Map] = rgb_map

    # initialize the player
    player = world.new_entity()
    player.components[Position] = Vector(*(rng.choice(free_positions)))
    player.components[Graphic] = Graphic(ord("@"), YELLOW)
    player.tags.add(Player)


    return world