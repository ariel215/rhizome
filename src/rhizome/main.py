#! python3 

from tcod import context as tcontext, tileset, console as tconsole, event as tevent
import tcod.ecs
from .game import components, maps, states
from .game.components import Vector
from .game.world import new_world, WallTile, FloorTile
import rhizome.game.systems as systems
import rhizome.game.world
import pathlib
import tomllib

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
    with open(HERE / "data" / "settings.toml", "rb") as fp:
        settings = tomllib.load(fp)
    tileset.procedural_block_elements(tileset=tiles)
    console = tconsole.Console(ROWS,COLUMNS)
    world  = new_world(settings)
    with tcontext.new(rows=ROWS, columns=COLUMNS,tileset=tiles) as ctx:
        state_stack = [states.GameState(settings)]
        while True:
            ctx.present(console)
            for event in tevent.wait():
                state_stack[-1].on_event(event)
            for state in state_stack:
                state.draw(console)



if __name__ == "__main__":
    main()
