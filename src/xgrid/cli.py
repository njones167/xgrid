"""Thin command line wrapper around the xgrid library."""

import argparse
import json
import sys

from .grid import Grid
from .puz import PuzFile


def _load_grid(path: str) -> Grid:
    if path.lower().endswith(".puz"):
        return PuzFile.read(path).solution
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return Grid.from_text(text)


def _analyze(grid: Grid) -> dict:
    slots = grid.slots()
    across = [s for s in slots if s.direction == "across"]
    down = [s for s in slots if s.direction == "down"]
    return {
        "width": grid.width,
        "height": grid.height,
        "block_count": grid.block_count(),
        "symmetric": grid.is_symmetric(),
        "across_count": len(across),
        "down_count": len(down),
        "slots": [
            {
                "number": s.number,
                "direction": s.direction,
                "row": s.row,
                "col": s.col,
                "length": s.length,
            }
            for s in slots
        ],
    }


def _print_human(report: dict) -> None:
    print(f"{report['width']}x{report['height']} grid, {report['block_count']} blocks")
    print(f"symmetry: {'ok' if report['symmetric'] else 'broken'}")
    print(f"{report['across_count']} across, {report['down_count']} down")
    print()
    for slot in report["slots"]:
        print(
            f"{slot['number']:>3} {slot['direction']:<7} "
            f"row {slot['row']} col {slot['col']} len {slot['length']}"
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xgrid", description="Inspect crossword grid files.")
    parser.add_argument(
        "path", help="path to a grid text file (# for block cells) or a .puz file"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON instead of text"
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="print the grid with clue numbers overlaid instead of the slot report",
    )
    args = parser.parse_args(argv)

    try:
        grid = _load_grid(args.path)
    except (OSError, ValueError) as exc:
        print(f"xgrid: {exc}", file=sys.stderr)
        return 1

    if args.render:
        print(grid.render())
        return 0

    report = _analyze(grid)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
