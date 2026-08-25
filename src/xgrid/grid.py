"""Core data model for crossword grids: parsing, numbering, and slot extraction."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

BLOCK = "#"


@dataclass(frozen=True)
class Slot:
    number: int
    direction: str  # "across" or "down"
    row: int
    col: int
    length: int

    @property
    def cells(self) -> List[Tuple[int, int]]:
        if self.direction == "across":
            return [(self.row, self.col + i) for i in range(self.length)]
        return [(self.row + i, self.col) for i in range(self.length)]


class Grid:
    def __init__(self, rows: List[str]):
        if not rows:
            raise ValueError("grid must have at least one row")
        width = len(rows[0])
        if width == 0 or any(len(r) != width for r in rows):
            raise ValueError("all grid rows must be the same non-zero length")
        self.rows = rows
        self.height = len(rows)
        self.width = width

    @classmethod
    def from_text(cls, text: str) -> "Grid":
        lines = [line for line in text.splitlines() if line.strip() != ""]
        return cls(lines)

    def to_text(self) -> str:
        return "\n".join(self.rows)

    def is_block(self, row: int, col: int) -> bool:
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return True
        return self.rows[row][col] == BLOCK

    def numbering(self) -> Dict[Tuple[int, int], int]:
        """Assign standard crossword numbers: a cell is numbered if it
        starts an across or down entry of length two or more."""
        numbers: Dict[Tuple[int, int], int] = {}
        next_number = 1
        for r in range(self.height):
            for c in range(self.width):
                if self.is_block(r, c):
                    continue
                starts_across = self.is_block(r, c - 1) and not self.is_block(r, c + 1)
                starts_down = self.is_block(r - 1, c) and not self.is_block(r + 1, c)
                if starts_across or starts_down:
                    numbers[(r, c)] = next_number
                    next_number += 1
        return numbers

    def slots(self) -> List[Slot]:
        numbers = self.numbering()
        result: List[Slot] = []
        for (r, c), number in sorted(numbers.items()):
            if self.is_block(r, c - 1) and not self.is_block(r, c + 1):
                length = 0
                cc = c
                while not self.is_block(r, cc):
                    length += 1
                    cc += 1
                result.append(Slot(number, "across", r, c, length))
            if self.is_block(r - 1, c) and not self.is_block(r + 1, c):
                length = 0
                rr = r
                while not self.is_block(rr, c):
                    length += 1
                    rr += 1
                result.append(Slot(number, "down", r, c, length))
        return result

    def is_symmetric(self) -> bool:
        """Check the standard 180-degree rotational symmetry of block cells."""
        for r in range(self.height):
            for c in range(self.width):
                mirror = self.is_block(self.height - 1 - r, self.width - 1 - c)
                if self.is_block(r, c) != mirror:
                    return False
        return True

    def block_count(self) -> int:
        return sum(
            1 for r in range(self.height) for c in range(self.width) if self.is_block(r, c)
        )
