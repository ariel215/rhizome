from dataclasses import dataclass
from random import Random
from typing import Final, Protocol
from  tcod.ecs import Entity
from tcod.map import compute_fov
from tcod.path import Pathfinder, SimpleGraph
from rhizome.game.components import Map, Position, Stats, Vector
from rhizome.game.tags import Beetle, Centipede, Solid, PillBug, Spider
import rhizome.game.world


__all__ = ["Strategy", "SpiderStrategy", "PillbugStrategy", "STRATEGIES"]

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

    def movement(self, entity) -> AiState:
        ...

def move_towards(entity: Vector, target: Vector, distance: int = 1) -> Vector:
    world = rhizome.game.world.world
    map = world[None].components[Map]
    cost = ~map
    for object in world.Q.all_of(components=[Position], tags=[Solid]):
        position = object.components[Position]
        if position != target:
            cost[position.y, position.x] = 0
        
    graph = SimpleGraph(cost=cost,cardinal=1,diagonal=0)
    pathfinder = Pathfinder(graph)
    pathfinder.add_root((entity.y, entity.x))
    path = pathfinder.path_to((target.y, target.x))
    if len(path) > distance:
        return Vector(path[-1][1], path[1][0]) - entity
    elif len(path) > 1:
        return Vector(path[-1][1], path[-1][0]) - entity
    else:
        return Vector(0,0)

@dataclass
class SpiderStrategy:
    state: AiState = Wandering()
    alert_radius: Final[int] = 20

    def movement(self, entity: Entity) -> Vector:
        position = entity.components[Position]

        match self.state:
            case Waiting(_):
                return Vector(0,0)
            case Hunting() | Fighting():
                target = rhizome.game.world.player.components[Position]
                return move_towards(position, target)
            case Wandering():
                rng = entity.registry[None].components[Random]
                direction = rng.choice([(-1,0),(1,0),(0,1),(0,-1)])
                return Vector(*direction)
        raise ValueError(f"Unable to match state {self.state}")

    def next_state(self, entity: Entity)->AiState:
        world = entity.registry
        position = entity.components[Position]
        map = world[None].components[Map]
        player = rhizome.game.world.player
        fov = compute_fov(~map, (position.y, position.x),radius=self.alert_radius)
        player_position = player.components[Position]
        visible = fov[player_position.y, player_position.x]
        distance = player_position - position
        adjacent = abs(distance.x) == 1 ^ abs(distance.y)==1
        match self.state:
            case Wandering():
                if visible:
                    return SpiderStrategy(Hunting())
            case Hunting():
                if adjacent:
                    return SpiderStrategy(Fighting())
                elif not visible:
                    return SpiderStrategy(Waiting(4))
            case Fighting():
                if not adjacent:
                    return SpiderStrategy(Hunting())
            case Waiting(turns_left):
                if visible:
                    return SpiderStrategy(Hunting())
                elif turns_left > 0:
                    return SpiderStrategy(Waiting(turns_left - 1))
                else:
                    return SpiderStrategy(Wandering())
        return self
                

@dataclass
class PillbugStrategy:
    state: AiState = Wandering()
    perseverance: int = 3


    def next_state(self, entity: Entity):
        stats = entity.components[Stats]
        player = rhizome.game.world.player
        player_position = player.components[Position]
        distance = player_position - entity.components[Position]
        adjacent = abs(distance.x) == 1 ^ abs(distance.y)==1
        injured = stats.health < stats.max_health

        match self.state:
            case Wandering():
                if adjacent and injured:
                    return PillbugStrategy(Fighting())
                else:
                    return PillbugStrategy(Waiting(0))
            case Fighting():
                if not adjacent:
                    return PillbugStrategy(Hunting())
            case Hunting():
                if adjacent:
                    return PillbugStrategy(Fighting())
                elif self.perseverance == 0:
                    return PillbugStrategy(Wandering())
                else:
                    return PillbugStrategy(Hunting(), self.perseverance - 1)
            case Waiting(_):
                return PillbugStrategy(Wandering())

    def movement(self, entity: Entity) -> Vector:
        position = entity.components[Position]

        match self.state:
            case Waiting():
                return Vector(0,0)
            case Hunting() | Fighting():
                target = rhizome.game.world.player.components[Position]
                return move_towards(position, target)
            case Wandering():
                rng = entity.registry[None].components[Random]
                direction = rng.choice([(-1,0),(1,0),(0,1),(0,-1)])
                return Vector(*direction)

        raise ValueError(f"Unable to match state {self.state}")

@dataclass
class BeetleStrategy: 
    state: AiState = Wandering()

    def next_state(self, entity: Entity):
        stats = entity.components[Stats]
        player = rhizome.game.world.player
        player_position = player.components[Position]
        distance = player_position - entity.components[Position]
        adjacent = abs(distance.x) == 1 ^ abs(distance.y)==1
        injured = stats.health < stats.max_health

        match self.state:
            case Wandering():
                if adjacent and injured:
                    return BeetleStrategy(Fighting())
                else:
                    return BeetleStrategy(Waiting(0))
            case Fighting():
                if not adjacent:
                    return BeetleStrategy(Hunting())
            case Hunting():
                if adjacent:
                    return BeetleStrategy(Fighting())
                elif self.perseverance == 0:
                    return BeetleStrategy(Wandering())
                else:
                    return BeetleStrategy(Hunting(), self.perseverance - 1)
            case Waiting(_):
                return BeetleStrategy(Wandering())


    def movement(self, entity: Entity) -> Vector:
        position = entity.components[Position]

        match self.state:
            case Waiting():
                return Vector(0,0)
            case Hunting():
                target = rhizome.game.world.player.components[Position]
                return move_towards(position, target, 2)
            case Fighting():
                target = rhizome.game.world.player.components[Position]
                return move_towards(position, target, 1)
            case Wandering():
                rng = entity.registry[None].components[Random]
                direction = rng.choice([(-1,0),(1,0),(0,1),(0,-1), (-2,0),(2,0),(0,2),(0,2)])
                return Vector(*direction)

        raise ValueError(f"Unable to match state {self.state}")


STRATEGIES = {
    PillBug: PillbugStrategy,
    Spider: SpiderStrategy, 
    Centipede: SpiderStrategy,
    Beetle: BeetleStrategy
}