from dataclasses import dataclass
from tcod.ecs import Entity, callbacks
import tcod.ecs
from typing import Final, Tuple
import numpy as np

@dataclass(frozen=True)
class Vector:
    x: int
    y: int

    def __add__(self, other: "Vector" | Tuple[int, int]):
        match other:
            case Vector(x=x,y=y):
                return type(self)(self.x + x, self.y + y)
            case (x,y):
                return type(self)(self.x + x, self.y + y)


@dataclass(frozen=True)
class Graphic:
    ch: int = ord("!")
    fg: tuple[int, int, int] = (255,255,255)

Gold: Final = ("Gold", int)
Position: Final = ("Position", Vector)
Map: Final = ("Map", np.array)

@callbacks.register_component_changed(component=Position)
def on_vector_changed(entity: Entity, old: Vector | None, new: Vector | None):
    if old == new:
        return
    if old is not None:
        entity.tags.discard(old)
    if new is not None:
        entity.tags.add(new)