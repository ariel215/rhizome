from dataclasses import dataclass
import enum
from typing import Final, Protocol
import numpy as np
from  tcod.ecs import Entity
from tcod.map import compute_fov
from tcod.path import Pathfinder, SimpleGraph


from rhizome.game.components import Map, Position, Vector
from rhizome.game.tags import Solid
from .world import get_player, get_world

class Wandering:
    pass

class Hunting:
    pass

class Fighting:
    pass

class Waiting(int):
    pass

type AiState = Wandering | Hunting | Fighting | Waiting


class Strategy(Protocol):
    def next_state(self, entity) -> "Strategy":
        ...

    def movement(self, entity) -> Vector:
        ...


def move_towards(entity: Vector, target: Vector) -> Vector:
    world = get_world()
    map = world[None].components[Map]
    cost = map.copy()
    for object in world.Q.all_of(components=[Position], tags=[Solid]):
        position = object.components[Position]
        graph[position.y, position.x] = True
    
    graph = SimpleGraph(cost,1,0)
    pathfinder = Pathfinder(graph)
    pathfinder.add_root((entity.y, entity.x))
    path = pathfinder.path_to((target.y, target.x))
    return Vector(*path[0])


@dataclass
class SpiderStrategy:
    state: AiState
    alert_radius: Final[int] = 20


    def movement(self, entity: Entity) -> Vector:
        match self.state:
            case Waiting():
                return Vector(0,0)
            case Hunting():
                position = entity.components[Position]
                target = get_player().components[Position]
                return move_towards(position, target)
            

    def next_state(self, entity: Entity)->"SpiderStrategy":
        world = get_world()
        position = entity.components[Position]
        map = world[None].components[Map]
        player = get_player()
        fov = compute_fov(~map, (position.y, position.x),radius=self.alert_radius)
        player_position = player.components[Position]
        visible = fov[player_position.y, player_position.x]
        distance = player_position - position
        adjacent = abs(distance.x) == 1 ^ abs(distance.y)==1
        match self.state:
            case Wandering():
                if visible:
                    return SpiderStrategy(Hunting)
                else: 
                    return self
            case Hunting():
                if adjacent:
                    return SpiderStrategy(Fighting)
                if not visible:
                    return Waiting(turns_left=4)
            case Fighting():
                if not adjacent:
                    return SpiderStrategy(Hunting)
                else:
                    return self
            case Waiting(turns_left):
                if visible:
                    return SpiderStrategy(Hunting)
                elif turns_left > 0:
                    return SpiderStrategy(turns_left - 1)
                else:
                    return SpiderStrategy(Wandering)