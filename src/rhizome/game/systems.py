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
    if new_position == pos:
        return []
    
    map = world[None].components[Map]
    try:
        if map[new_position.y, new_position.x]:
            return []
    except IndexError:
        raise IndexError(f"cannot add {pos} to {direction}: out of bounds")

    collision = world.Q.all_of(tags=[new_position])
    for obj in collision:
        print(obj.components[Name])
        if Solid in obj.tags:
            break
    else:
        entity.components[Position] = new_position
    return [ent for ent in collision if ent is not entity]

def move_player(direction: Vector):
    player = get_player()
    collision = collide_entity(player,  direction=direction)
    if collision:
        obstacles = [ent for ent in collision if Solid in ent.tags]
        for obstacle in obstacles:
            handle_collision(player, obstacle)


def handle_collision(collider: Entity, collided: Entity):
    collider_stats = collider.components.get(Stats)
    collided_stats = collided.components.get(Stats)
    if collided_stats and collider_stats:
        print(f"{collider.components.get(Name, "(unnamed)")} hit {collided.components.get(Name, "(unnamed)")}")
        new_stats = collided.components[Stats] = damage(collider_stats, collided_stats)
        if new_stats.health == 0:
            kill(collided)
        

def damage(attacker: Stats, attacked: Stats):
    if attacked.health >0:
        print(f"dealt {attacker.strength} damage!")
    new_health = max(attacked.health - attacker.strength,0)
    return Stats(new_health, attacked.max_health, attacked.strength)

def kill(entity: Entity):
    if Player not in entity.tags:
        position = entity.components[Position]
        name = entity.components[Name]
        if Enemy in entity.tags:
            corpse_graphic = Graphic(**settings["items"]["corpse"]["graphic"])
            add_item(entity.registry, position=position,graphic=corpse_graphic,tags={Edible}, name=f"{name} corpse")
        entity.clear()


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
