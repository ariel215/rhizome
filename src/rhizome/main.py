#! python3 

from tcod import context as tcontext, tileset, console as tconsole, event as tevent
import tcod.ecs
from .game import caves, components, states
from .game.components import Vector
from .game.world import new_world, WallTile, FloorTile
import rhizome.game.world
import pathlib
import tomllib

COLUMNS = 100
ROWS = 100
THRESHOLD = 0.42
CLOSED = True

HERE = pathlib.Path(__file__).parent

def draw_world(console, world: tcod.ecs.Registry):
    console.rgb[:] = caves.to_rgb(world[None].components[components.Map], wall=WallTile, floor=FloorTile)
    char_channel = console.rgb['ch']
    fg_channel = console.rgb['fg']
    for entity in world.Q.all_of(components=[components.Graphic,components.Position]):
        position = entity.components[components.Position]
        graphic = entity.components[components.Graphic]
        char_channel[position.y, position.x] = graphic.ch
        fg_channel[position.y, position.x] = graphic.fg


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
        state = states.GameState()
        while True:
            ctx.present(console)
            draw_world(console,world)
            for event in tevent.wait():
                state.on_event(event)


if __name__ == "__main__":
    main()
