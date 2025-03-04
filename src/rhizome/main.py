#! python3 

from tcod import context as tcontext, tileset, console as tconsole, event as tevent
from .game import states
from .game.world import create_world
import pathlib
from rhizome.game.state_manager import *

COLUMNS = 100
ROWS = 100
THRESHOLD = 0.42
CLOSED = True

HERE = pathlib.Path(__file__).parent

def main():
    tiles = tileset.load_tilesheet(
        HERE / 'data/Alloy_curses_12x12.png',
        columns=16,
        rows=16,
        charmap=tileset.CHARMAP_CP437
    )
    tileset.procedural_block_elements(tileset=tiles)
    console = tconsole.Console(ROWS,COLUMNS)
    create_world()
    state_manager = StateManager(states.GameState())
    with tcontext.new(rows=ROWS, columns=COLUMNS,tileset=tiles) as ctx:
        while True:
            for event in tevent.wait():
                state_manager.on_event(event)
            state_manager.draw(console)
            ctx.present(console)


if __name__ == "__main__":
    main()
