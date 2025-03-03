from tcod.ecs import Registry
from random import Random
from .components import *
from .caves import create_map, to_rgb
from .tags import *
from typing import Dict
from functools import lru_cache

WallTile = Graphic(ord("X"))
FloorTile = Graphic(ord("."))

PLAYER_COLOR = [0xc6, 0xd3, 0x13]

player: Entity
""" The player in the game"""

world: Registry
""" The global ECS registry"""   

def new_world(settings: Dict) -> Registry:
    global world
    world = Registry()
    # global RNG
    rng = world[None].components[Random] = Random()
    # initialize the map
    map_settings = settings["map"]
    map = create_map(closed=True,**map_settings)
    
    free_positions = [idx for idx, value in np.ndenumerate(map) if not value]
    world[None].components[Map] = map

    # initialize the player
    global player
    player = world.new_entity()
    player.components[Position] = Vector(*(rng.choice(free_positions)))
    player.components[Graphic] = Graphic(ord("@"), PLAYER_COLOR)
    player.tags |= {Player, Actor}


    return world

def get_world():
    global world
    return world

def get_player():
    global player
    return player