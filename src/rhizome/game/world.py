import numpy as np
from tcod.ecs import Registry, Entity
from random import Random
from rhizome.game.components import move_inside
from .components import *
from .maps import create_map, to_rgb
from .tags import *
from typing import Dict


WallTile = Graphic("X")
FloorTile = Graphic(".")

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

    def get_position(condition=None):
        valid = free_positions if condition is None else [p for p in free_positions if condition(p)]
        pos = rng.choice(valid)
        free_positions.remove(pos)
        return Vector(pos[1], pos[0])

    # initialize the player
    global player
    player_settings = settings["player"]
    player = world.new_entity()
    player_position = get_position()
    player.components[Position] = player_position
    player.components[Graphic] = Graphic(**player_settings["graphic"])
    player.components[Stats] = Stats(player_settings["health"],player_settings["health"],player_settings["strength"])
    
    
    player.tags |= {Player, Actor}

    for (enemy_kind, enemy_settings) in settings['enemy'].items():
        for _ in range(10):
            enemy = world.new_entity()
            enemy.components[Position] = get_position()
            enemy.components[Stats] = Stats(enemy_settings["health"], enemy_settings["health"], enemy_settings["strength"])
            enemy.components[Graphic] = Graphic(**enemy_settings["graphic"])
            enemy.tags |= {Actor, Enemy, enemy_kind, Solid}


    # camera
    camera_ent = world.new_entity()
    camera = Camera(**settings["camera"])
    camera_bounds = BoundingBox.centered(player_position, height=camera.height, width=camera.width)
    map_bounds = BoundingBox(Vector(0,0), Vector(map.shape[1], map.shape[0]))
    camera_bounds = move_inside(camera_bounds, map_bounds)
    camera_ent.components[Position] = camera_bounds.top_left
    camera_ent.components[Camera] = camera

    return world


def get_world():
    global world
    return world

def get_player():
    global player
    return player