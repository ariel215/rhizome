from tcod.ecs import Registry, Entity
from tcod.ecs.query import BoundQuery
from .components import *
from rhizome.game.world import FloorTile, WallTile, get_world, get_player
from rhizome.game.tags import *
import numpy as np
import math

def collide_entity(entity: Entity, direction: Vector) -> BoundQuery | None:
    """
    Attempts to move an entity in the given direction 

    If there is a wall where the entity is trying to move to:
        returns (False, None), and leaves the entity's position unaltered
    If there is empty space where the entity is trying to move to: 
        return (True, None) and update the entity's position
    If there is another entity there:
         
    """
    world = get_world()
    pos = entity.components[Position]
    new_position = pos + direction
    map = world[None].components[Map]
    if map[new_position.y, new_position.x]:
        return False
    
    collision = world.Q.all_of(tags=[new_position])
    if not collision.all_of(tags=[Solid]):
        entity.components[Position] = new_position
    return collision    

def move_player(direction: Vector):
    player = get_player()
    collision = collide_entity(player,  direction=direction)
    if collision:
        obstacles = collision.all_of(tags=[Solid])
        for obstacle in obstacles:
            handle_collision(player, obstacle)


def handle_collision(collider: Entity, collided: Entity):
    collider_stats = collider.components.get(Stats)
    collided_stats = collided.components.get(Stats)
    if collided_stats and collider_stats:
        collided.components[Stats] = damage(collider_stats, collided_stats)
        

def damage(attacker: Stats, attacked: Stats):
    if attacked.health >0:
        print(f"dealt {attacker.strength} damage!")
    new_health = max(attacked.health - attacker.strength,0)
    return Stats(new_health, attacked.max_health, attacked.strength)

 
def move_camera(direction: Vector):
    world = get_world()
    player = get_player()
    player_position = player.components[Position]
    cam_ent, = world.Q.all_of(components=[Camera])
    
    camera = cam_ent.components[Camera]
    cam_position = cam_ent.components[Position]
    center = camera.bounding_box(cam_position).center
    new_position = cam_position + direction
    new_fov = BoundingBox.from_top_left(new_position, height = camera.height, width=camera.width)
    map = world[None].components[Map]
    map_box = BoundingBox(Vector(0,0), Vector(map.shape[1], map.shape[0]))
    if new_fov.top_left in map_box and new_fov.bottom_right in map_box:
        cam_ent.components[Position] = new_position
