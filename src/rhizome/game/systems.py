import random
from tcod.ecs import Entity
from tcod.ecs.query import BoundQuery

from rhizome.game import world
from rhizome.game.strategies import Strategy
from rhizome.game.ui_manager import UIManager
from .components import *
from rhizome.game.world import get_player, get_world, new_level, settings, add_item
from rhizome.game.tags import *
from rhizome.game.logging import log

from .components import Name
from .components import Trait

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
        return []

    collision = world.Q.all_of(tags=[new_position])
    for obj in collision:
        if Solid in obj.tags:
            break
    else:
        entity.components[Position] = new_position
    return [ent for ent in collision if ent is not entity]

def move_player(direction: Vector) -> Entity:
    player = get_player()
    collision = collide_entity(player,  direction=direction)
    for entity in collision:
        if Solid in entity.tags:
            return handle_collision(player, entity)
        elif direction:
            return handle_trigger(player, entity)
        else:
            return handle_rest(player, entity)
    return player

def handle_trigger(entity1, entity2):
    print(f"{entity1.components[Name]} triggered {entity2.components[Name]}")
    if entity1.components[Name] == "Player":
        assert Player in entity1.tags
    if entity2.components[Name] == "Hole":
        assert Hole in entity2.tags
    if Player in entity1.tags and Hole in entity2.tags:
        new_level(entity1.registry[None].components[UIManager], new_game=False)
        return get_player()
    return entity1
    

def handle_rest(entity1: Entity, entity2: Entity):
    stats = entity1.components.get(Stats)
    if stats and Edible in entity2.tags:
        digest(entity1, entity2)
    return entity1

def handle_collision(collider: Entity, collided: Entity):
    collider_stats = collider.components.get(Stats)
    collided_stats = collided.components.get(Stats)
    if collided_stats and collider_stats:
        damage_dealt = damage(collider_stats, collided_stats)
        log(f"{collider.components.get(Name, "(unnamed)")} dealt {damage_dealt} to {collided.components.get(Name, "(unnamed)")}")
        collided_stats.health -= damage_dealt
    return collider

def damage(attacker: Stats, attacked: Stats) -> int:
    damage_dealt = attacker.strength + random.randint(*attacker.damage_range) - attacked.toughness
    return min(damage_dealt, attacked.health)


def kill(entity: Entity):
    position = entity.components[Position]
    name = entity.components[Name]
    if Enemy in entity.tags:
        corpse_graphic = Graphic(**settings["items"]["corpse"]["graphic"])
        corpse = add_item(entity.registry, position=position,graphic=corpse_graphic,tags={Edible}, name=f"{name} corpse")
        corpse.components[Size] = entity.components.get(Size,1)
        traits = entity.components.get(Trait)
        if traits:
            corpse.components[Trait] = traits
    entity.clear()


def player_dead():
    player = get_player()
    return player.components[Stats].health <= 0
    

def digest(entity: Entity, corpse: Entity):
    size = corpse.components.get(Size)
    pstats = entity.components[Stats]
    amount_eaten = min(pstats.digestion,size)
    health_gained = 2 * amount_eaten
    pstats.health += health_gained
    size -= amount_eaten
    if size <= 0:
        log(f"consumed {corpse.components[Name]}")
        trait = corpse.components[Trait]
        if trait: 
            log(f"Its {trait} has made you stronger")
        world.acquire_trait(entity, trait)
        corpse.clear() 
    else:
        corpse.components[Size] = size



def move_enemies():
    world = get_world()
    enemies = world.Q.all_of(tags=[Enemy])
    for enemy in enemies:
        strategy = enemy.components.get(Strategy)
        if not strategy:
            raise ValueError(f"no strategy for entity {enemy.components.get(Name, "???")}")
        direction = strategy.movement(enemy)
        collisions = collide_entity(enemy,direction)
        for collision in collisions:
            handle_collision(enemy, collision)


    for enemy in enemies:
        strategy = enemy.components[Strategy]
        new_strategy = enemy.components[Strategy].next_state(enemy)
        enemy.components[Strategy] = new_strategy

    for enemy in enemies: 
        stats = enemy.components[Stats]
        if stats.health <= 0:
            kill(enemy)
 
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
