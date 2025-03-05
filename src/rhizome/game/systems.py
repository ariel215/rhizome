import random
from tcod.ecs import Entity
from tcod.ecs.query import BoundQuery

from rhizome.game.strategies import Strategy
from .components import *
from rhizome.game.world import get_player, get_world, settings, add_item
from rhizome.game.tags import *

from .components import Name

def collide_entity(entity: Entity, direction: Vector) -> BoundQuery:
    """
    Attempts to move an entity in the given direction 

    If there is a wall where the entity is trying to move to:
        returns (False, None), and leaves the entity's position unaltered
    If there is empty space where the entity is trying to move to: 
        return (True, None) and update the entity's position
    If there is another entity there:
         
    """
    world = entity.registry
    pos = entity.components[Position]
    new_position = pos + direction
    
    map = world[None].components[Map]
    try:
        if map[new_position.y, new_position.x]:
            return []
    except IndexError:
        raise IndexError(f"cannot add {pos} to {direction}: out of bounds")

    collision = world.Q.all_of(tags=[new_position])
    for obj in collision:
        if Solid in obj.tags:
            break
    else:
        entity.components[Position] = new_position
    return [ent for ent in collision if ent is not entity]

def move_player(direction: Vector):
    player = get_player()
    collision = collide_entity(player,  direction=direction)
    for entity in collision: 
        if Solid in entity.tags:
            handle_collision(player, entity)
        elif direction:
            handle_trigger(player, entity)
        else:
            handle_rest(player, entity)

def handle_trigger(entity1, entity2):
    pass

def handle_rest(entity1: Entity, entity2: Entity):
    stats = entity1.components.get(Stats)
    if stats and Edible in entity2.tags:
        digest(entity1, entity2)

def handle_collision(collider: Entity, collided: Entity):
    collider_stats = collider.components.get(Stats)
    collided_stats = collided.components.get(Stats)
    if collided_stats and collider_stats:
        print(f"{collider.components.get(Name, "(unnamed)")} hit {collided.components.get(Name, "(unnamed)")}")
        new_stats = collided.components[Stats] = damage(collider_stats, collided_stats)
        if new_stats.health == 0:
            kill(collided)
        

def damage(attacker: Stats, attacked: Stats) -> Stats:
    damage_dealt = attacker.strength + random.randint(*attacker.damage_range) - attacked.toughness
    attacked.health = max(attacked.health - damage_dealt, 0)
    return attacked.health


def kill(entity: Entity):
    if Player not in entity.tags:
        position = entity.components[Position]
        name = entity.components[Name]
        if Enemy in entity.tags:
            corpse_graphic = Graphic(**settings["items"]["corpse"]["graphic"])
            add_item(entity.registry, position=position,graphic=corpse_graphic,tags={Edible}, name=f"{name} corpse")
        entity.clear()


def digest(entity: Entity, corpse: Entity):
    pstats = entity.components[Stats]
    pstats.health = pstats.max_health
    corpse.clear() 


def move_enemies():
    world = get_world()
    enemies = world.Q.all_of(tags=[Enemy])
    for enemy in enemies:
        strategy = enemy.components[Strategy]
        if not strategy:
            raise ValueError(f"no strategy for entity tagged {enemy.tags}")
        direction = strategy.movement(enemy)
        collisions = collide_entity(enemy,direction)
        for collision in collisions:
            handle_collision(enemy, collision)

    for enemy in enemies:
        strategy = enemy.components[Strategy]
        new_strategy = enemy.components[Strategy].next_state(enemy)
        enemy.components[Strategy] = new_strategy

 
def move_camera(direction: Vector):
    player = get_player()
    world = player.registry
    map = world[None].components[Map]
    player_position = player.components[Position]
    cam_ent, = world.Q.all_of(components=[Camera])
    camera: Camera = cam_ent.components[Camera]
    cam_position = cam_ent.components[Position]
    center = camera.bounding_box(cam_position).center
    tracking_box = camera.tracking_box(center)
    outside = False
    match direction:
        case Vector(1,0):
            outside = player_position.x >= tracking_box.right
        case Vector(-1,0):
            outside = player_position.x < tracking_box.left
        case Vector(0,1): 
            outside = player_position.y >= tracking_box.bottom
        case Vector(0,-1): 
            outside = player_position.y < tracking_box.top
    if outside:
        new_position = cam_position + direction
        new_fov = camera.bounding_box(new_position)
        new_fov = move_inside(new_fov, BoundingBox(Vector(0,0),Vector(*map.shape)))
        cam_ent.components[Position] = new_fov.top_left
