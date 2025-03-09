#! python3 

from tcod import context as tcontext, tileset, console as tconsole, event as tevent
from rhizome.game import ui_states
from rhizome.game.world import new_level, settings
from rhizome.game.ui_manager import *
from rhizome.game.world import settings
import pathlib

HERE = pathlib.Path(__file__).parent

def main():
    tiles = tileset.load_tilesheet(
        HERE / 'data/Alloy_curses_12x12.png',
        columns=16,
        rows=16,
        charmap=tileset.CHARMAP_CP437
    )
    tileset.procedural_block_elements(tileset=tiles)
    console = tconsole.Console(**settings["screen"])
    state_manager = UIManager([ui_states.IntroScreen(title="Rhizome")])

    with tcontext.new(console=console,tileset=tiles) as ctx:
        while True:
            for event in tevent.wait():
                state_manager.on_event(event)
                if not state_manager.states:
                    raise SystemExit
            state_manager.draw(console)
            ctx.present(console)


if __name__ == "__main__":
    main()
