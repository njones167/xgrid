"""Reading and writing the .puz crossword file format (Across Lite).

This covers the standard header, grid, and string sections that every
.puz file has. It does not parse or preserve the optional extension
sections some files carry (rebus, circled squares, a solving timer), and
it refuses scrambled/locked puzzles rather than trying to unscramble
them.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import List, Tuple

from .grid import BLOCK, EMPTY, Grid, Slot

ENCODING = "ISO-8859-1"
FILE_MAGIC = b"ACROSS&DOWN\x00"
MASK_STRING = b"ICHEATED"

_HEADER_FORMAT = "<H12sH8s4sHH12sBBHHH"
_HEADER_SIZE = struct.calcsize(_HEADER_FORMAT)


def _checksum(data: bytes, seed: int = 0) -> int:
    value = seed
    for byte in data:
        if value & 1:
            value = (value >> 1) + 0x8000
        else:
            value >>= 1
        value = (value + byte) & 0xFFFF
    return value


def _text_checksum(
    title: str, author: str, copyright_: str, clues: List[str], notes: str, seed: int = 0
) -> int:
    value = seed
    for text in (title, author, copyright_):
        if text:
            value = _checksum(text.encode(ENCODING) + b"\x00", value)
    for clue in clues:
        if clue:
            value = _checksum(clue.encode(ENCODING), value)
    if notes:
        value = _checksum(notes.encode(ENCODING) + b"\x00", value)
    return value


def _masked_checksums(cib: int, sol: int, grid_: int, part: int) -> bytes:
    values = (cib, sol, grid_, part)
    low = bytes(MASK_STRING[i] ^ (v & 0xFF) for i, v in enumerate(values))
    high = bytes(MASK_STRING[4 + i] ^ (v >> 8) for i, v in enumerate(values))
    return low + high


def _grid_to_solution_bytes(grid: Grid) -> bytes:
    chars = []
    for row in grid.rows:
        for ch in row:
            if ch == BLOCK:
                chars.append(".")
            elif ch == EMPTY:
                raise ValueError(
                    "solution grid has an unfilled cell; .puz solutions must be fully filled"
                )
            else:
                chars.append(ch.upper())
    return "".join(chars).encode(ENCODING)


def _grid_to_fill_bytes(grid: Grid) -> bytes:
    chars = []
    for row in grid.rows:
        for ch in row:
            if ch == BLOCK:
                chars.append(".")
            elif ch == EMPTY:
                chars.append("-")
            else:
                chars.append(ch.upper())
    return "".join(chars).encode(ENCODING)


def _solution_bytes_to_grid(data: bytes, width: int, height: int) -> Grid:
    text = data.decode(ENCODING)
    rows = [text[r * width : (r + 1) * width].replace(".", BLOCK) for r in range(height)]
    return Grid(rows)


def _fill_bytes_to_grid(data: bytes, width: int, height: int) -> Grid:
    text = data.decode(ENCODING)
    rows = []
    for r in range(height):
        row = text[r * width : (r + 1) * width]
        rows.append(row.replace(".", BLOCK).replace("-", EMPTY))
    return Grid(rows)


@dataclass
class PuzFile:
    solution: Grid
    fill: Grid
    clues: List[str] = field(default_factory=list)
    title: str = ""
    author: str = ""
    copyright: str = ""
    notes: str = ""

    def numbered_clues(self) -> List[Tuple[Slot, str]]:
        """Pair each slot in the solution grid with its clue text.

        .puz stores clues as a flat list, ordered by increasing cell
        number and, for a cell that starts both an across and a down
        entry, across before down. That's the same order Grid.slots()
        produces, so the two line up positionally.
        """
        slots = self.solution.slots()
        if len(slots) != len(self.clues):
            raise ValueError(
                f"clue count ({len(self.clues)}) does not match slot count ({len(slots)})"
            )
        return list(zip(slots, self.clues))

    def across_clues(self) -> List[Tuple[int, str]]:
        return [
            (slot.number, clue)
            for slot, clue in self.numbered_clues()
            if slot.direction == "across"
        ]

    def down_clues(self) -> List[Tuple[int, str]]:
        return [
            (slot.number, clue)
            for slot, clue in self.numbered_clues()
            if slot.direction == "down"
        ]

    @classmethod
    def read(cls, path: str) -> "PuzFile":
        with open(path, "rb") as handle:
            data = handle.read()
        if len(data) < _HEADER_SIZE:
            raise ValueError("file is too short to be a .puz file")

        (
            stored_checksum,
            magic,
            stored_cib_checksum,
            _masked,
            _version,
            _reserved1c,
            _scrambled_checksum,
            _reserved20,
            width,
            height,
            num_clues,
            bitmask,
            scrambled_tag,
        ) = struct.unpack(_HEADER_FORMAT, data[:_HEADER_SIZE])

        if magic != FILE_MAGIC:
            raise ValueError("not a .puz file: missing ACROSS&DOWN magic")
        if scrambled_tag:
            raise ValueError("scrambled (locked) .puz files are not supported")

        cib_bytes = struct.pack("<BBHHH", width, height, num_clues, bitmask, scrambled_tag)
        cib_checksum = _checksum(cib_bytes)
        if cib_checksum != stored_cib_checksum:
            raise ValueError("corrupt .puz file: header checksum mismatch")

        offset = _HEADER_SIZE
        cell_count = width * height
        solution_bytes = data[offset : offset + cell_count]
        offset += cell_count
        fill_bytes = data[offset : offset + cell_count]
        offset += cell_count

        def read_string() -> str:
            nonlocal offset
            end = data.index(b"\x00", offset)
            text = data[offset:end].decode(ENCODING)
            offset = end + 1
            return text

        title = read_string()
        author = read_string()
        copyright_ = read_string()
        clues = [read_string() for _ in range(num_clues)]
        notes = read_string() if offset < len(data) else ""

        overall = _checksum(fill_bytes, _checksum(solution_bytes, cib_checksum))
        overall = _text_checksum(title, author, copyright_, clues, notes, seed=overall)
        if overall != stored_checksum:
            raise ValueError("corrupt .puz file: checksum mismatch")

        return cls(
            solution=_solution_bytes_to_grid(solution_bytes, width, height),
            fill=_fill_bytes_to_grid(fill_bytes, width, height),
            clues=clues,
            title=title,
            author=author,
            copyright=copyright_,
            notes=notes,
        )

    def write(self, path: str) -> None:
        width, height = self.solution.width, self.solution.height
        if (self.fill.width, self.fill.height) != (width, height):
            raise ValueError("solution and fill grids must be the same size")
        for r in range(height):
            for c in range(width):
                if self.solution.is_block(r, c) != self.fill.is_block(r, c):
                    raise ValueError("solution and fill grids must have matching block layout")

        solution_bytes = _grid_to_solution_bytes(self.solution)
        fill_bytes = _grid_to_fill_bytes(self.fill)

        bitmask = 0
        scrambled_tag = 0
        cib_bytes = struct.pack(
            "<BBHHH", width, height, len(self.clues), bitmask, scrambled_tag
        )
        cib_checksum = _checksum(cib_bytes)

        sol_checksum = _checksum(solution_bytes)
        grid_checksum = _checksum(fill_bytes)
        part_checksum = _text_checksum(self.title, self.author, self.copyright, self.clues, self.notes)
        masked = _masked_checksums(cib_checksum, sol_checksum, grid_checksum, part_checksum)

        overall = _checksum(fill_bytes, _checksum(solution_bytes, cib_checksum))
        overall = _text_checksum(
            self.title, self.author, self.copyright, self.clues, self.notes, seed=overall
        )

        header = struct.pack(
            _HEADER_FORMAT,
            overall,
            FILE_MAGIC,
            cib_checksum,
            masked,
            b"1.3\x00",
            0,
            0,
            b"\x00" * 12,
            width,
            height,
            len(self.clues),
            bitmask,
            scrambled_tag,
        )

        parts = [header, solution_bytes, fill_bytes]
        for text in (self.title, self.author, self.copyright):
            parts.append(text.encode(ENCODING) + b"\x00")
        for clue in self.clues:
            parts.append(clue.encode(ENCODING) + b"\x00")
        parts.append(self.notes.encode(ENCODING) + b"\x00")

        with open(path, "wb") as handle:
            handle.write(b"".join(parts))
