"""Thin command line wrapper around the xgrid library."""

import argparse
import json
import sys

from .grid import Grid
from .puz import PuzFile


def _load(path: str):
    """Load a grid file, returning (grid, puzzle). puzzle is the source
    PuzFile if path is a .puz file (so its clues are available), else None.
    """
    if path.lower().endswith(".puz"):
        puzzle = PuzFile.read(path)
        return puzzle.solution, puzzle
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return Grid.from_text(text), None


def _analyze(grid: Grid, puzzle: PuzFile = None) -> dict:
    slots = grid.slots()
    across = [s for s in slots if s.direction == "across"]
    down = [s for s in slots if s.direction == "down"]
    clue_by_slot = dict(puzzle.numbered_clues()) if puzzle is not None and puzzle.clues else {}
    slot_reports = []
    for s in slots:
        slot_report = {
            "number": s.number,
            "direction": s.direction,
            "row": s.row,
            "col": s.col,
            "length": s.length,
        }
        if s in clue_by_slot:
            slot_report["clue"] = clue_by_slot[s]
        slot_reports.append(slot_report)
    return {
        "width": grid.width,
        "height": grid.height,
        "block_count": grid.block_count(),
        "symmetric": grid.is_symmetric(),
        "across_count": len(across),
        "down_count": len(down),
        "slots": slot_reports,
    }


def _print_human(report: dict) -> None:
    print(f"{report['width']}x{report['height']} grid, {report['block_count']} blocks")
    print(f"symmetry: {'ok' if report['symmetric'] else 'broken'}")
    print(f"{report['across_count']} across, {report['down_count']} down")
    print()
    for slot in report["slots"]:
        line = (
            f"{slot['number']:>3} {slot['direction']:<7} "
            f"row {slot['row']} col {slot['col']} len {slot['length']}"
        )
        if "clue" in slot:
            line += f"  {slot['clue']}"
        print(line)


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
    parser.add_argument(
        "--validate",
        action="store_true",
        help="check the block layout for symmetry, short entries, and disconnected "
        "cells instead of printing the slot report",
    )
    args = parser.parse_args(argv)

    try:
        grid, puzzle = _load(args.path)
    except (OSError, ValueError) as exc:
        print(f"xgrid: {exc}", file=sys.stderr)
        return 1

    if args.render:
        print(grid.render())
        return 0

    if args.validate:
        problems = grid.validate()
        if args.json:
            print(json.dumps({"valid": not problems, "problems": problems}, indent=2))
        elif problems:
            for problem in problems:
                print(problem)
        else:
            print("ok")
        return 1 if problems else 0

    try:
        report = _analyze(grid, puzzle)
    except ValueError as exc:
        print(f"xgrid: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
