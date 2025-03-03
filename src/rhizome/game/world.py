from tcod.ecs import Registry
from random import Random

from rhizome.game.components import move_inside
from .components import *
from .maps import create_map, to_rgb
from .tags import *
from typing import Dict


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
    player_position = Vector(*(rng.choice(free_positions)))
    player.components[Position] = player_position
    player.components[Graphic] = Graphic(ord("@"), PLAYER_COLOR)
    player.tags |= {Player, Actor}


    # camera
    camera_ent = world.new_entity()
    camera = Camera(**settings["camera"])
    camera_bounds = BoundingBox.centered(player_position, height=camera.height, width=camera.width)
    map_bounds = BoundingBox(Vector(0,0), Vector(map.shape[1], map.shape[0]))
    camera_bounds = move_inside(camera_bounds, map_bounds)
    camera_ent.components[Position] = camera_bounds.top_left
    camera_ent.components[Camera] = camera

    if settings["debug"]:
        camera_ent.components[Graphic] = Graphic(ord("O"), (255,0,0))

    return world


def get_world():
    global world
    return world

def get_player():
    global player
    return player