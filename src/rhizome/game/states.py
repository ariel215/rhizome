from typing import Final
from tcod.event import KeySym, KeyboardEvent, Quit
from rhizome.game import systems



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

    def on_event(self, event):
        match event:
            case KeyboardEvent(sym=key_sim, type=type_):
                if type_ == "KEYDOWN" and key_sim in self.DIRECTION_KEYS:
                    systems.move_player(self.DIRECTION_KEYS[key_sim])
                elif key_sim == KeySym.ESCAPE:
                    raise SystemExit
            case Quit():
                print(event)
                raise SystemExit
        