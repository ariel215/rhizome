from dataclasses import dataclass
from functools import wraps
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
            case int(s):
                return type(self)(self.x + s, self.y + s)

    def __sub__(self, other: "Vector" | Tuple[int,int]):
        match other:
            case Vector(x=x,y=y):
                return type(self)(self.x - x, self.y - y)
            case (x,y):
                return type(self)(self.x - x, self.y - y)
            case int(s): 
                return type(self)(self.x + s, self.y + s)
            
    def __mul__(self, other):
        match other: 
            case Vector(x=x, y=y):
                return type(self)(self.x * x ,self.y* y)
            case (x,y):
                return type(self)(self.x * x ,self.y* y)
            case int(s):
                return type(self)(self.x * s, self.y * s)
    
    def __floordiv__(self, other):
        match other: 
            case Vector(x=x, y=y):
                return type(self)(self.x // x ,self.y// y)
            case (x,y):
                return type(self)(self.x // x ,self.y// y)
            case int(s):
                return type(self)(self.x // s, self.y // s)
    
    def __str__(self):
        return f"Vector({self.x}, {self.y})"



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

class BoundingBox:

    def __init__(self, top_left: Vector, bottom_right: Vector):
        self.top_left = top_left
        self.bottom_right = bottom_right

    def __eq__(self, value):
        return self.top_left == value.top_left and self.bottom_right == value.bottom_right
    
    def __str__(self):
        return f"BoundingBox({self.top_left}, {self.bottom_right})"

    @classmethod
    def centered(cls: "BoundingBox", point: Vector, height: int, width:int):
        top_left = point - (height // 2, width // 2)
        bottom_right = point + (height // 2, width // 2)
        return cls(top_left, bottom_right)
    
    @classmethod
    def from_top_left(cls: "BoundingBox", point:Vector, height: int, width: int):
        return cls(point, point+(width, height))

    @property
    def top(self) -> int:
        return self.top_left.y

    @property
    def left(self) -> int:
        return self.top_left.x

    @property
    def right(self) -> int: 
        return self.bottom_right.x

    @property
    def bottom(self) -> int: 
        return self.bottom_right.y
    
    @property
    def center(self) -> Vector:
        return (self.top_left + self.bottom_right) // 2

    def __contains__(self, point: Vector) -> bool:
        return self.top <= point.y <= self.bottom and self.left <= point.x <= self.right


@dataclass(frozen=True)
class Camera: 
    height: int
    width: int
    tracking_radius: int

    def bounding_box(self, position: Vector) -> BoundingBox:
        return BoundingBox.from_top_left(position, self.height, self.width)


def move_inside(box1: BoundingBox, box2: BoundingBox) -> BoundingBox:
    """
    Reposition box 1 so that it is contained inside of box2
    If there is no way to do so (because box1 is too large), raise ValueError

    Returns: a new bounding box, the same size as box1, but flush with box2 
    along any dimension that box1 was previously outsized box2


    Examples:
    box1 = [(0,0), (3,3)]
    box2 = [(1,1), (5,5)]
    move_inside(box1, box2) = [(1,1), (4,4)]

    box1 = [(0,1), (3,4)]
    box2 = [(1,1), (5,5)]
    move_inside(box1, box2) = [(1,1), (4,4)]


    box1 = [(3,3) (6,6)]
    box2 = [(1,1), (5,5)]
    move_inside(box1, box2) = [(2,2), (5,5)]
    """

    # box1.top_left should be greater or equal to box2.top_left in both dimensions
    d_top = box1.top_left - box2.top_left
    d_bottom = box1.bottom_right - box2.bottom_right
    if (d_top.x < 0 and d_bottom.x > 0) or (d_top.y < 0 and d_bottom.y > 0):
        raise ValueError()

    dx = dy = 0
    if d_top.x < 0:
        dx = -d_top.x

    if d_bottom.x > 0:
        dx = -d_bottom.x

    if d_top.y <0:
        dy = -d_top.y
    if d_bottom.y > 0:
        dy = -d_bottom.y

    return BoundingBox(box1.top_left + (dx,dy), box1.bottom_right + (dx,dy))
