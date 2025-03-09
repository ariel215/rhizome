from dataclasses import dataclass
import itertools
from typing import Any, Final, List, Callable
import tcod.constants
from tcod.event import KeySym, KeyboardEvent, Quit
from rhizome.game import maps, systems, tags
from rhizome.game.components import Camera, Graphic, Map, Name, Position, Stats, Vector
from rhizome.game.world import FloorTile, WallTile, get_player, get_world, new_level, settings
from tcod.console import Console
from tcod.ecs import Entity
from rhizome.game.ui_manager import Push, Pop, Replace, Update
from rhizome.game.logging import logger


__all__ = ["GameState", "MenuState"]


    
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
            
@dataclass
class HistoryWindow:
    height: int
    width: int
    position: Vector


    def draw(self, console: Console):
        console.draw_frame(
            self.position.x, self.position.y,
            self.width, self.height,
            "History"
        )
        log_length = self.height - 5
        messages = list(itertools.islice(reversed(logger.messages),log_length))
        for lineno, message in enumerate(reversed(messages)):
            console.print(self.position.x + 1, self.position.y + 1 + lineno,
                          message)


class GameState:
    def __init__(self):
        self.console = Console(width=settings["map"]["width"], height=settings["map"]["height"])
        info_window_position = Vector(settings["camera"]["width"], 0)
        history_position = Vector(settings["camera"]["width"], settings["screen"]["height"]//2)
        subject = get_player()
        height=settings["screen"]["height"] // 2
        width=settings["screen"]["width"] - settings["camera"]["width"]
        self.info_window = InfoWindow(position=info_window_position,
                                      subject=subject,
                                      height=height,
                                      width=width
                                      )
        self.history_window = HistoryWindow(
            position = history_position,
            height = height, width=width
        )


    def on_event(self, event):
        match event:
            case KeyboardEvent(sym=key_sim, type=type_):
                if type_ == "KEYDOWN" and key_sim in DIRECTION_KEYS:
                    movement_direction = Vector(*DIRECTION_KEYS[key_sim])
                    player = systems.move_player(movement_direction)
                    systems.move_enemies()
                    systems.move_camera(movement_direction)
                    if systems.player_dead():
                        return Pop()
                    self.info_window.subject = player
                        
                elif key_sim == KeySym.ESCAPE:
                    return Push(main_menu())
            case Quit():
                raise SystemExit


    def draw_entity(self, entity):
        position = entity.components[Position]
        graphic = entity.components[Graphic]
        self.console.rgb['ch'][position.y, position.x] = graphic.ch
        self.console.rgb['fg'][position.y, position.x] = graphic.fg
        self.console.rgb['bg'][position.y, position.x] = graphic.bg


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
        self.info_window.draw(console)
        self.history_window.draw(console)

    def update(self, new_subject: Entity, *args,**kwargs):
        self.info_window.subject = new_subject


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
            "\n".join(item_names),
            fg=[0xff, 0xff, 0xff],
            bg=[0,0,0]
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
                        return [Pop()] * (self.n_parents + 1)
                    
    def update(*args, **kwargs):
        pass


class MessageBox:
    def __init__(self, message, alignment = tcod.constants.LEFT):
        self.message = message
        self.height = 10
        self.width = settings["camera"]["width"] // 2
        self.x = settings["camera"]["width"] // 4
        self.y = settings["camera"]["height"] - (self.height + 3)
        self.alignment = alignment

    def on_event(self, event):
        match event:
            case KeyboardEvent(sym=sym,type="KEYDOWN"):
                if sym in (KeySym.SPACE, KeySym.ESCAPE, KeySym.RETURN):
                    return Pop()

    def draw(self, console:Console, ):
        console.draw_frame(self.x, self.y, self.width, self.height, clear=True)
        console.print_box(self.x+1, self.y+1, self.width-2, self.height-2, self.message, alignment=self.alignment)


def main_menu():
    def exit():
        return [Pop(), Pop()]
    def restart():
        new_level()
        return [Pop(), Update(new_subject=get_player())]
    continue_  =MenuState.MenuItem("Continue", lambda: Pop())
    restart = MenuState.MenuItem("Restart", restart)
    quit = MenuState.MenuItem("Quit", exit)

    return MenuState([continue_, restart, quit],Vector(10,10))

def game_over():
    def exit():
        raise SystemExit
    def restart():
        new_level()
        return [Pop(), Update(new_subject=get_player())]
    restart = MenuState.MenuItem("Restart", restart)
    quit = MenuState.MenuItem("Quit", exit)

    return MenuState([restart, quit],Vector(10,10), name="Game Over")


class IntroScreen:
    def __init__(self, title):
        self.width = settings["screen"]["width"]
        self.height = settings["screen"]["height"]
        self.game_title = title
        self.player_location = Vector(self.width // 2, 12)


    def draw(self, console: Console):
        console.clear()
        console.print_box(0,6, self.width, 1, self.game_title,
                          alignment=tcod.constants.CENTER)
        
        console.print(self.player_location.x, self.player_location.y, 
            settings["player"]["graphic"]["char"], 
            fg = settings["player"]["graphic"]["fg"],
        )

        console.print_box(0, 20, self.width, 14,
                          "You're a little mushroom. But you want to be...a BIG mushroom!\n"
                          "Fight bugs. Absorb their flesh. Grow strong.\n\n\n"
                          "Controls: WASD to move and SPACE to stand still.\n"
                          "Press SPACE to begin!",
                          alignment=tcod.constants.CENTER
        )

                          
    def on_event(self, event):
        match event:
            case KeyboardEvent(sym=sym, type="KEYDOWN"):
                match sym:
                    case KeySym.RETURN | KeySym.RETURN2 | KeySym.SPACE:
                        new_level(self)
                        return Push(GameState())
                    case KeySym.ESCAPE:
                        return Pop()
                    case _: 
                        if sym in DIRECTION_KEYS:
                            self.player_location += DIRECTION_KEYS[sym]
        