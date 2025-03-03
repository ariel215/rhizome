from tcod.ecs import Registry, Entity
from .components import Vector, Position, Map
from rhizome.game.world import get_world, get_player

def collide_entity(entity: Entity, direction: Vector) -> Entity | None:
    """
    Attempts to move an entity in the given direction 

    If there is a wall where the entity is trying to move to:
        returns (False, None), and leaves the entity's position unaltered
    If there is empty space where the entity is trying to move to: 
        return (True, None) and update the entity's position
    If there is another entity there:
        - check if collision 
     
    """
    world = get_world()
    pos = entity.components[Position]
    new_position = pos + direction
    map = world[None].components[Map]
    if map[new_position.y, new_position.x]:
        return (False, None)
    
    collision = world.Q.all_of(tags=[new_position])
    if collision:
        return collision[0]
    else:
        entity.components[Position] = new_position
        return None
    

def move_player(direction):
    collide_entity(get_player(),  direction=direction)