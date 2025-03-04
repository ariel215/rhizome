from dataclasses import dataclass
from typing import Final, List, Callable, Tuple
import tcod.constants
from tcod.event import KeySym, KeyboardEvent, Quit
from rhizome.game import maps, systems
from rhizome.game.components import BoundingBox, Camera, Graphic, Map, Position, Vector
from rhizome.game.world import FloorTile, WallTile, get_world, new_world
from tcod.console import Console
from rhizome.game.state_manager import Push, Pop
import logging

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
    }

    def __init__(self, settings):
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


    def draw(self, console: Console):
        world = get_world()
        (cam_ent,) = world.Q.all_of(components=[Camera])
        camera = cam_ent.components[Camera]
        position = cam_ent.components[Position]
        bounds = camera.bounding_box(position)

        map = world[None].components[Map]

        self.console.rgb[:] = maps.to_rgb(map, wall=WallTile, floor=FloorTile)
        char_channel = self.console.rgb['ch']
        fg_channel = self.console.rgb['fg']
        for entity in world.Q.all_of(components=[Graphic,Position]):
            position = entity.components[Position]
            if position in bounds:
                graphic = entity.components[Graphic]
                char_channel[position.y, position.x] = graphic.ch
                fg_channel[position.y, position.x] = graphic.fg
        console.rgb[:camera.height, :camera.width] = self.console.rgb[bounds.top:bounds.bottom, bounds.left:bounds.right]


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
    restart = MenuState.MenuItem("Restart", new_world)
    quit = MenuState.MenuItem("Quit", exit)

    return MenuState([continue_, restart, quit],Vector(10,10))