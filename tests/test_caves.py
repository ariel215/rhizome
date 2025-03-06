# import numpy as np
# from rhizome.game import caves
# def test_small():
#     cave = np.array([
#         [0,1,0],
#         [1,1,1],
#         [0,1,0]
#     ])
#     ###
#     # padded: 
#     # [1,1,1,1,1],
#     # [1,0,1,0,1]
#     # [1,1,1,1,1],
#     # [1,0,1,0,1],
#     # [1,1,1,1,1]
#     updated = [
#         [0,0,0],
#         [0,1,0],
#         [0,0,0]
#     ]

#     assert np.all(caves.generation(cave) == updated)

from rhizome.game.components import Vector


def test_vector():
    assert Vector(1,0)
    assert Vector(0,1)
    assert Vector(-1,-1)
    assert not Vector(0,0)