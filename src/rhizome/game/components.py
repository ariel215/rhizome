from dataclasses import dataclass
from tcod.ecs import Entity, callbacks

@dataclass(frozen=True)
class Vector:
    x: int
    y: int

    def __add__(self, other: "Vector"):
        return type(self)(self.x + other.x, self.y + other.y)
    

@callbacks.register_component_changed
def on_vector_changed(entity: Entity, old: Vector | None, new: Vector | None):
    if old == new:
        return
    if old is not None:
        entity.tags.discard(old)
    if new is not None:
        entity.tags.add(new)