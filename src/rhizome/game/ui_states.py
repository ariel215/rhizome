from dataclasses import dataclass
from typing import Final, List, Callable
import tcod.constants
from tcod.event import KeySym, KeyboardEvent, Quit
from rhizome.game import maps, systems, tags
from rhizome.game.components import Camera, Graphic, Map, Name, Position, Stats, Vector
from rhizome.game.world import FloorTile, WallTile, get_player, get_world, create_world, settings
from tcod.console import Console
from tcod.ecs import Entity
from rhizome.game.ui_manager import Push, Pop

__all__ = ["GameState", "MenuState"]

class GameState:
    
    DIRECTION_KEYS: Final = {
        # Arrow keys
        KeySym.LEFT: (-1, 0),
        KeySym.RIGHT: (1, 0),
        KeySym.UP: (0, -1),
        KeySym.DOWN: (0, 1),
        # Arrow key diagonals
        KeySym.HOME: (-1, -1),
        KeySym.END: (-1, 1),
        KeySym.PAGEUP: (1, -1),
        KeySym.PAGEDOWN: (1, 1),
        # WASD
        KeySym.w: (0, -1),
        KeySym.s: (0,1),
        KeySym.a: (-1,0),
        KeySym.d: (1,0),
        # Keypad
        KeySym.KP_4: (-1, 0),
        KeySym.KP_6: (1, 0),
        KeySym.KP_8: (0, -1),
        KeySym.KP_2: (0, 1),
        KeySym.KP_7: (-1, -1),
        KeySym.KP_1: (-1, 1),
        KeySym.KP_9: (1, -1),
        KeySym.KP_3: (1, 1),
        # VI keys
        KeySym.h: (-1, 0),
        KeySym.l: (1, 0),
        KeySym.k: (0, -1),
        KeySym.j: (0, 1),
        KeySym.y: (-1, -1),
        KeySym.b: (-1, 1),
        KeySym.u: (1, -1),
        KeySym.n: (1, 1),
        # Wait
        KeySym.SPACE: (0,0)
    }

    def __init__(self):
        self.console = Console(width=settings["map"]["width"], height=settings["map"]["height"])

    def on_event(self, event):
        match event:
            case KeyboardEvent(sym=key_sim, type=type_):
                if type_ == "KEYDOWN" and key_sim in self.DIRECTION_KEYS:
                    movement_direction = Vector(*self.DIRECTION_KEYS[key_sim])
                    systems.move_player(movement_direction)
                    systems.move_enemies()
                    systems.move_camera(movement_direction)
                elif key_sim == KeySym.ESCAPE:
                    return Push(main_menu())
            case Quit():
                raise SystemExit


    def draw_entity(self, entity):
        position = entity.components[Position]
        graphic = entity.components[Graphic]
        self.console.rgb['ch'][position.y, position.x] = graphic.ch
        self.console.rgb['fg'][position.y, position.x] = graphic.fg


    def draw(self, console: Console):
        world = get_world()
        (cam_ent,) = world.Q.all_of(components=[Camera])
        camera = cam_ent.components[Camera]
        position = cam_ent.components[Position]
        bounds = camera.bounding_box(position)

        map = world[None].components[Map]

        self.console.rgb[:] = maps.to_rgb(map, wall=WallTile, floor=FloorTile)
        for entity in world.Q.all_of(components=[Graphic,Position]):
            if tags.Player not in entity.tags:
                self.draw_entity(entity)
        self.draw_entity(get_player())
        console.rgb[:camera.height, :camera.width] = self.console.rgb[bounds.top:bounds.bottom, bounds.left:bounds.right]


class InfoState:
    def __init__(self, cursor_position: Vector):
        self.cursor = cursor_position

    def on_event(self, event):
        world = get_world()
        map = world[None].components[Map]
        match event:
            case KeyboardEvent(sym=sym, type="KEYDOWN"):
                direction = GameState.DIRECTION_KEYS.get(sym)
                if direction is not None:
                    self.cursor += direction
                    self.cursor = self.cursor.clamp(Vector(0,0), Vector(map.shape[1],map.shape[0]))          
                

    def draw(self, console: Console):
        console.draw_frame(self.cursor.x-1, self.cursor.y-1, 3,3)


class MenuState:
    @dataclass 
    class MenuItem:
        name: str
        action: Callable


    def __init__(self, items: List[MenuItem], position: Vector, name: str = "", n_parents = 0):
        self.items = items
        self.cursor = 0
        self.position = position
        self.name = name
        self.height = len(self.items)
        self.width = max([len(item.name) for item in self.items] + [len(self.name)]) + 3
        self.n_parents = n_parents


    def advance(self):
        if self.cursor < len(self.items) - 1:
            self.cursor += 1
        
    def reverse(self):
        if self.cursor > 0:
            self.cursor -= 1

    @property
    def current(self):
        return self.items[self.cursor]
    
    def select(self):
        return self.current.action()
    
    def draw(self, console: Console):
        item_names = [item.name for item in self.items]
        item_names[self.cursor] = "> " + self.current.name

        console.draw_frame(self.position.x, self.position.y, self.width+2, self.height+2)
        console.print_box(self.position.x, self.position.y, self.width+2, 1, 
                      self.name, alignment=tcod.constants.CENTER)
        console.print(
            self.position.x + 1, self.position.y + 1,
            "\n".join(item_names)
        )

    def on_event(self,event):
        match event:
            case KeyboardEvent(sym=key_sim, type="KEYDOWN", repeat=False):
                match key_sim:
                    case KeySym.UP | KeySym.w: 
                        return self.reverse()
                    case KeySym.DOWN | KeySym.s:
                        return self.advance()
                    case KeySym.KP_ENTER | KeySym.RETURN | KeySym.RETURN2: 
                        return self.select()
                    case KeySym.ESCAPE:
                        return [Pop() for _ in range(self.n_parents + 1)]
                    

def main_menu():
    def exit():
        raise SystemExit
    continue_  =MenuState.MenuItem("Continue", lambda: Pop())
    restart = MenuState.MenuItem("Restart", create_world)
    quit = MenuState.MenuItem("Quit", exit)

    return MenuState([continue_, restart, quit],Vector(10,10))



@dataclass
class InfoWindow:
    position: Vector
    subject: Entity
    height: int
    width: int


    def draw(self,console: Console):
        stats = self.subject.components.get(Stats)
        name = self.subject.components.get(Name,"")
        console.draw_frame(self.position.x, self.position.y,
                           self.width, self.height,
                           name
                           )
        if stats:
            console.print_box(
                self.position.x + 1, self.position.y+1,
                self.width - 2, self.height - 2,
                str(stats))
        
