# xgrid

A small library for working with crossword grids as plain text, plus a CLI
for inspecting them.

Crossword grids look simple but have a few rules that are annoying to
reimplement every time you touch one: which cells get a clue number, how
long each across/down entry is, and whether the block pattern has the
180-degree rotational symmetry that most published crosswords require.
`xgrid` parses a text grid and answers those questions.

## Grid format

A grid is plain text, one line per row. `#` marks a black (block) cell;
anything else (a letter, or `.` for an empty white cell) is fillable. All
rows must be the same length.

```
##...
...#.
.....
.#...
...##
```

## Library usage

```python
from xgrid import Grid

grid = Grid.from_text(open("puzzle.txt").read())

for slot in grid.slots():
    print(slot.number, slot.direction, slot.length, slot.cells)

print("symmetric:", grid.is_symmetric())
```

## CLI usage

```
$ xgrid puzzle.txt
5x5 grid, 6 blocks
symmetry: ok
5 across, 5 down

  1 across  row 0 col 2 len 3
  1 down    row 0 col 2 len 5
  2 down    row 0 col 4 len 4
  3 across  row 1 col 0 len 3
  3 down    row 1 col 0 len 4
  4 down    row 1 col 1 len 2
  5 across  row 2 col 0 len 5
  6 down    row 2 col 3 len 2
  7 across  row 3 col 2 len 3
  8 across  row 4 col 0 len 3
```

Pass `--render` to print the grid with clue numbers overlaid instead of
the slot report. A single character can't hold both a fill letter and a
clue number, so each grid row prints as two lines, a number line above a
cell line:

```
$ xgrid puzzle.txt --render
    1   2
# # . . .
3 4
. . . # .
5
. . . . .
    7
. # . . .
8
. . . # #
```

Pass `--validate` to check the block layout instead of printing the slot
report: it checks 180-degree symmetry, flags any entry shorter than
three letters, and flags white cells that a block layout has split off
from the rest of the fill. It exits with status 1 if it finds problems.

```
$ xgrid puzzle.txt --validate
4 down at row 1 col 1 is 2 letters long, shorter than the 3-letter minimum
```

`Grid.validate(min_length=3)` is the library equivalent; pass a lower
`min_length` to relax the minimum entry length.

Pass `--json` for the same report as a JSON object instead of the text
table above:

```
$ xgrid puzzle.txt --json
{
  "width": 5,
  "height": 5,
  "block_count": 6,
  "symmetric": true,
  "across_count": 5,
  "down_count": 5,
  "slots": [
    {"number": 1, "direction": "across", "row": 0, "col": 2, "length": 3},
    {"number": 1, "direction": "down", "row": 0, "col": 2, "length": 5},
    ...
  ]
}
```

## .puz files

The CLI reads `.puz` files (the format used by Across Lite and most other
crossword software) directly, based on the file extension:

```
$ xgrid crossword.puz --json
```

For reading and writing them programmatically:

```python
from xgrid.puz import PuzFile

puzzle = PuzFile.read("crossword.puz")
print(puzzle.title, puzzle.author)
print(puzzle.solution.to_text())

puzzle.notes = "handmade, no rebus squares"
puzzle.write("crossword-edited.puz")
```

`solution` and `fill` are `Grid` instances: the solved answers and the
solver's current progress. `clues` is a flat list of strings in the same
order as `Grid.slots()` (across then down for each number). To pair each
clue with the slot it belongs to:

```python
for slot, clue in puzzle.numbered_clues():
    print(slot.number, slot.direction, clue)

print(puzzle.across_clues())  # [(1, "..."), (3, "..."), ...]
print(puzzle.down_clues())    # [(1, "..."), (2, "..."), ...]
```

`numbered_clues()` raises `ValueError` if the clue count doesn't match
the slot count, which the CLI also reports rather than printing a
mismatched report. When a `.puz` file has clues, `xgrid puzzle.puz` and
`--json` include the clue text on each slot.

Only the standard header, grid, and string sections are handled. Rebus
squares, circled letters, timers, and other optional extension sections
aren't parsed, and scrambled (locked) puzzles are rejected outright.

## Install

No third-party dependencies, standard library only.

```
pip install -e .
```

## Tests

```
python -m unittest discover
```

## Status

Early. The grid model, numbering, basic `.puz` reading/writing, the
`--render` command, clue-to-slot association, and block layout
validation are solid. There's no grid generator yet.
