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

## Install

No third-party dependencies, standard library only.

```
pip install -e .
```

## Status

Early. The grid model and numbering are solid; everything else (clue text,
puzzle formats like `.puz`, grid generation) is still to come.
