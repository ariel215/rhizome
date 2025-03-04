
import numpy as np
from tcod.path import SimpleGraph, Pathfinder
from tcod.ecs import *

from rhizome.game import systems
from rhizome.game.components import Map, Stats, Vector
from rhizome.game.world import add_player

def test_pf():

    map = [
        [1,1,1,],
        [1,1,1,],
        [1,1,1]
    ]

    graph  = SimpleGraph(cost = map, cardinal=1,diagonal=0)
    pf = Pathfinder(graph)
    pf.add_root((0,0))
    path = pf.path_to((2,2))
    assert len(path) == 5

def test_collisions():
    map = np.zeros((3,3))
    world = Registry()
    world[None].components[Map] = map

    player = add_player(world, Vector(0,0), None, stats=Stats(1,1,1) )
    collisions  = systems.collide_entity(player, Vector(0,0))
    assert not collisions
    collisions = systems.collide_entity(player, Vector(1,0))
    assert not collisions