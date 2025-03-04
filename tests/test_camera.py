from rhizome.game.components import move_inside
from rhizome.game.components import BoundingBox, Vector



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
"""


def test_move_inside():
    box1 = [(0,0),(3,3)] , [(0,1), (3,4)] , [(3,3), (6,6)]
    box2 = BoundingBox(Vector(1,1,), Vector(5,5))
    expected = [(1,1), (4,4)], [(1,1), (4,4)], [(2,2), (5,5)]
    def make_box(lst):
        return BoundingBox(Vector(*lst[0]), Vector(*lst[1]))
    
    for input, output in zip(box1,expected):
        bb = make_box(input)
        result = move_inside(bb, box2)
        box_out = make_box(output)
        assert result == box_out


def test_box_eq():
    box1 = BoundingBox(Vector(0,0), Vector(1,1))
    box2 = BoundingBox(Vector(0,0), Vector(1,1))
    assert box1 == box2