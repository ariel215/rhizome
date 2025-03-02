#! python3 

from tcod import context as tcontext, tileset, console as tconsole, event as tevent
from .game import caves
import pathlib


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
    map = caves.create_map(ROWS,COLUMNS,THRESHOLD,CLOSED)
    with tcontext.new(rows=ROWS, columns=COLUMNS,tileset=tiles) as ctx:
        while True:
            ctx.present(console)
            console.print(0,0,caves.to_string(map))
            for event in tevent.wait():
                match event:
                    case tevent.Quit:
                        return
                    case tevent.KeyDown(sym=tevent.KeySym.SPACE):
                        map = caves.create_map(ROWS,COLUMNS,THRESHOLD,CLOSED)
                    case tevent.KeyDown(sym=tevent.KeySym.ESCAPE):
                        return


if __name__ == "__main__":
    main()
