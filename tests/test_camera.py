import numpy as np
import pytest
from rhizome.game.components import Camera, Graphic, Map, move_inside
from rhizome.game.components import BoundingBox, Vector
from rhizome.game.world import add_camera, add_player, new_level
from tcod.ecs import Registry


"""
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

@pytest.mark.parametrize("box1, box2, expected",[
    [[(0,0),(3,3)] , [(1,1),(5,5)], [(1,1), (4,4)]],
    [[(0,1), (3,4)], [(1,1),(5,5)], [(1,1), (4,4)]],
    [[(3,3), (6,6)], [(1,1),(5,5)], [(2,2),(5,5)]],
    [[(4,4), (10,6)], [(0,0),(8,8)], [(2,4), (8,6)]],
])
def test_move_inside(box1, box2, expected):
    def make_box(lst):
        return BoundingBox(Vector(*lst[0]), Vector(*lst[1]))
    box1 = make_box(box1)
    box2 = make_box(box2)
    result = move_inside(box1, box2)
    assert result == make_box(expected)

def test_box_eq():
    box1 = BoundingBox(Vector(0,0), Vector(1,1))
    box2 = BoundingBox(Vector(0,0), Vector(1,1))
    assert box1 == box2


@pytest.mark.parametrize("size, top, bottom",
                         [
                            (1,3,4),
                            (2,2,4),
                            (3,2,5),
                            (4,1,5)])
def test_centered_box(size, top, bottom):
    center = Vector(3,3)
    height = width = size
    box = BoundingBox.centered(center, height, width)
    assert box.top == top
    assert box.bottom == bottom


@pytest.mark.parametrize("size",[2,3,4])
def test_centered_height(size):
    center = Vector(3,3)
    box = BoundingBox.centered(center,size,size)
    assert box.bottom - box.top == size


@pytest.mark.parametrize("size",range(10))
def test_center(size):
    center = Vector(3,3)
    height = width = size
    box = BoundingBox.centered(center, height, width)
    assert box.center == center

@pytest.mark.parametrize("height, width", [(3,5), (5,3), (6,4), (4,6), (3,6), (6,3)])
def test_center_corner(height, width):
    center = Vector(3,3)
    box = BoundingBox.centered(center, height, width)
    box2 = BoundingBox(box.top_left, box.bottom_right)
    

def test_build():
    world = Registry()
    map = np.zeros((10,10))
    world[None].components[Map] = map
    add_player(world, Vector(8,6))
    add_camera(world, Vector(8,6),)

    