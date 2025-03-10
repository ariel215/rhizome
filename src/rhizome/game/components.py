from dataclasses import dataclass
from enum import Enum
from functools import wraps
from tcod.ecs import Entity, callbacks
from typing import Final, Tuple
import numpy as np

__all__ = ["Vector", "Position", "BoundingBox", "Camera", 
           "Graphic", "Map", "Stats", "Name",
           "Size", "Trait",
           "on_vector_changed", "move_inside"
           ]


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

    def __bool__(self):
        return self.x !=0 or self.y != 0
    
    def __str__(self):
        return f"Vector({self.x}, {self.y})"
    

    def clamp(self, min: "Vector", max: "Vector")->"Vector":
        """
        Return a new vector with components restricted to lie 
        between `min` (inclusivee) and `max` (exclusive)

        Prereqs: `min.x < max.x` and `min.y < max.y`

        """
        return Vector(
            x=min(max.x-1,max(min.x,self.x)),
            y=min(max.y-1,max(min.y,self.y))
        )
    
Position: Final = ("Position", Vector)

@callbacks.register_component_changed(component=Position)
def on_vector_changed(entity: Entity, old: Vector | None, new: Vector | None):
    if old == new:
        return
    if old is not None:
        entity.tags.discard(old)
    if new is not None:
        entity.tags.add(new)


class BoundingBox:
    """
    A half-open bounding box, containing its top and left edges
    but not its bottom and right edges
    """

    def __init__(self, top_left: Vector, bottom_right: Vector):
        self.top_left = top_left
        self.bottom_right = bottom_right

    def __eq__(self, value):
        return self.top_left == value.top_left and self.bottom_right == value.bottom_right
    
    def __str__(self):
        return f"BoundingBox({self.top_left}, {self.bottom_right})"

    @classmethod
    def centered(cls: "BoundingBox", point: Vector, height: int, width:int) -> "BoundingBox":
        """
        Create a bounding box centered on `point` whose interior is 
        `height` tall and `width` wide
        
        """
        top_left = point - (width // 2, height // 2,)
        bottom_right = point + (width // 2 + (width % 2), height // 2 + (height % 2), ) 
        return cls(top_left, bottom_right)
    
    @classmethod
    def from_top_left(cls: "BoundingBox", point:Vector, height: int, width: int) -> "BoundingBox":
        """"
        Create a bounding box whose top left corner is `point`
        and whose interior is `height` tall and `width` wide
        """
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

    box1 = [(4,4), (10,6)]
    box2 = [(0,0), (8,8)]
    move_inside = [(2,4), (8,6)]
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


@dataclass(frozen=True)
class Camera: 
    height: int
    width: int
    tracking_radius: int

    def bounding_box(self, position: Vector) -> BoundingBox:
        return BoundingBox.from_top_left(position, self.height, self.width)
    
    def tracking_box(self, position: Vector) -> BoundingBox: 
        return BoundingBox.centered(position, self.tracking_radius, self.tracking_radius)

@dataclass(frozen=True)
class Graphic:
    char: str = "!"
    fg: tuple[int, int, int] = (255,255,255)
    bg: tuple[int, int, int] = (0,0,0)

    @property
    def ch(self):
        return ord(self.char)

@dataclass
class Stats: 
    health: int
    max_health: int
    strength: int
    damage_range: Tuple[int,int] = (0,0) # variability of damage
    toughness: int = 0 # reduces damage taken by X
    toxicity: int = 0 # deal damage when hit
    camoflauge: int = 0 # makes it harder to be seen
    digestion: int = 1 # how quickly you absorb food

    def __str__(self):
        health = f"Health: {self.health}/{self.max_health} "
        healthbar = "|" * ((10 * self.health ) // self.max_health)
        strength = f"Strength: {self.strength}"
        lines = [health, healthbar, strength]
        if self.toughness:
            lines.append(f"Toughness: {self.toughness}")
        if self.toxicity: 
            lines += f"Toxicity: {self.toxicity}"
        if self.camoflauge:
            lines += f"Camoflauge: {self.camoflauge}"
        if self.digestion > 1:
            lines += f"Digestion: {self.digestion}"
        
        
        return "\n".join(lines)

class Trait(str, Enum):
    Shell = "shell"
    Fangs = "fangs"
    Jaws = "jaws"
    Bristles = "bristles"
    VenomSacs = "venom sacs"


Map: Final = ("Map", np.ndarray)
Name: Final = ("Name", str)
Depth: Final = ("Depth", int)
Size: Final = ("Size", int)
LevelNo: Final = ("LevelNo", int)