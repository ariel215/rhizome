import itertools
import math
import numpy as np
from tcod.ecs import Registry, Entity
from random import Random
from rhizome.game.components import move_inside
from rhizome.game.ui_manager import UIManager
from .components import *
from .components import LevelNo
from .maps import create_map, to_rgb
from .tags import *
from typing import Dict
import rhizome.game.strategies as strategies
import tomllib
import pkgutil

WallTile = Graphic("X")
FloorTile = Graphic(".")

PLAYER_COLOR = [0xc6, 0xd3, 0x13]

player: Entity
""" The player in the game"""

world: Registry
""" The global ECS registry"""

settings: Dict = tomllib.loads(
    pkgutil.get_data("rhizome.data", "settings.toml").decode()
)

def add_player(world, position: Vector, stats: Stats | None = None)->Entity:
    player_settings = settings["player"]
    graphic = Graphic(**player_settings["graphic"])
    stats = stats or Stats(player_settings["health"],player_settings["health"],player_settings["strength"])

    player = world.new_entity()
    player.components[Position] = position
    player.components[Graphic] = graphic
    player.components[Stats] = stats
    player.components[Name] = "Player"
    player.tags |= {Player, Actor, Solid}
    return player    


def add_item(world: Registry, position, graphic, tags, name="")->Entity:
    item = world.new_entity()
    item.components[Position] = position
    item.components[Graphic] = graphic
    item.components[Name] = name
    item.tags |= {Item} | tags

    return item


def add_camera(world: Registry, position: Vector) -> Entity:
    map = world[None].components[Map]
    camera = Camera(**settings["camera"])
    camera_ent = world.new_entity()
    camera_bounds = BoundingBox.centered(position, height=camera.height, width=camera.width)
    map_bounds = BoundingBox(Vector(0,0), Vector(map.shape[1], map.shape[0]))
    camera_bounds = move_inside(camera_bounds, map_bounds)
    camera_ent.components[Position] = camera_bounds.top_left
    camera_ent.components[Camera] = camera
    return camera_ent


def add_hole(world: Registry, position: Vector) -> Entity:
    """
    Holes take you deeper into the cave
    """
    entity = world.new_entity()
    entity.components[Position] = position
    entity.components[Graphic] = Graphic(**settings["hole"]["graphic"])
    entity.components[Name] = "Hole"
    entity.tags |= {Hole}
    return entity


def take_position(free_positions, condition=None):
    rng = world[None].components[Random]
    valid = free_positions if condition is None else [p for p in free_positions if condition(p)]
    pos = rng.choice(valid)
    free_positions.remove(pos)
    return Vector(pos[1], pos[0])


def get_trait(rng: Random, trait_dict: dict):
    kinds = list(trait_dict.keys()) + [None]
    probabilities = list(trait_dict.values())
    probabilities.append(1 - sum(probabilities))
    return rng.choices(kinds, probabilities)

def scale(stats, level):
    factor = math.pow(1.3,level)
    for stat in vars(stats):
        value = getattr(stats,stat)
        match value:
            case int():
                value = int(value * factor)
            case (low, high):
                value = (low, high + int(factor))
        setattr(stats, stat,value)

def populate_enemies(world :Registry, open_positions, level_number: int):
    rng = world[None].components[Random]
    for (enemy_kind, enemy_settings) in settings['enemy'].items():
        for _ in range(10):
            enemy = world.new_entity()
            enemy.components[Position] = take_position(open_positions)
            stats = enemy.components[Stats] = Stats(enemy_settings["health"], enemy_settings["health"], enemy_settings["strength"])
            enemy.components[Graphic] = Graphic(**enemy_settings["graphic"])
            enemy.components[strategies.Strategy] = strategies.STRATEGIES[enemy_kind]()
            trait = enemy.components[Trait] = get_trait(rng,enemy_settings["traits"])
            acquire_trait(enemy,trait)
            scale(stats, level_number)
            enemy.components[Size] = rng.choice(enemy_settings.get("size_range", [1]))
            enemy.tags |= {Actor, Enemy, enemy_kind, Solid}
            enemy.components[Name] = enemy_kind



def acquire_trait(entity: Entity, trait: Trait):
    ent_stats = entity.components[Stats]
    if trait == Trait.Jaws:
        ent_stats.strength += 1
    elif trait == Trait.Shell:
        ent_stats.toughness += 1
    elif trait == Trait.Fangs: 
        ent_stats.damage_range[-1] += 1
    elif trait == Trait.VenomSacs:
        ent_stats.venom += 1
    elif trait == Trait.Bristles:
        ent_stats.toxicity += 1




def new_level(ui: UIManager | None , new_game: bool = True) -> Registry:
    global world
    if ui is None:
        ui = world[None].components[UIManager]

    world = Registry()
    # global RNG
    
    world[None].components[Random] = Random()

    world[None].components[UIManager] = ui
    level_number = 0 if new_game else world[None].components[LevelNo] + 1
    world[None].components[LevelNo] = level_number

    global player
    print("building level")
    map = create_map(closed=True, **settings["map"])
    world[None].components[Map] = map
    free_positions = [idx for idx, value in np.ndenumerate(map) if not value]

    rng = world[None].components[Random]
    fns = [lambda p: p[0] < map.shape[0] / 3 and p[1] < map.shape[1] / 3,
            lambda p: p[0] < map.shape[0] / 3 and p[1] > 2 * map.shape[1] / 3,
            lambda p: p[0] > 2 * map.shape[0] / 3 and p[1] > 2 * map.shape[1] / 3,
            lambda p: p[0] > 2 * map.shape[0] / 3 and p[1] < map.shape[1] / 2
    ]
    player_corner = rng.randint(0,3)
    hole_corner = (player_corner + 2) % 4
    player_position =take_position(free_positions, fns[player_corner])
    assert player_position 
    hole_position = take_position(free_positions,fns[hole_corner])
    if new_game:
        player = add_player(world, player_position)
    else:
        stats = player.components[Stats]
        player = add_player(world,player_position,stats)

    populate_enemies(world, free_positions, level_number)
    add_hole(world, player_position + (1,1))
    # add_hole(world, hole_position)

    add_camera(world,player_position)
    return world


def get_world():
    global world
    return world


def get_player():
    global player
    return player