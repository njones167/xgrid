import os
import tempfile
import unittest

from xgrid.grid import Grid
from xgrid.puz import PuzFile


class PuzRoundTripTests(unittest.TestCase):
    def test_round_trip_preserves_grids_clues_and_metadata(self):
        solution = Grid(["CAT", "AGO", "TOE"])
        fill = Grid(["CAT", "AG.", "TOE"])
        puzzle = PuzFile(
            solution=solution,
            fill=fill,
            clues=["Feline", "Long past", "Digit on a foot", "Cat sound?"],
            title="Sample",
            author="njones167",
            copyright="2026 njones167",
            notes="a test puzzle",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "sample.puz")
            puzzle.write(path)
            loaded = PuzFile.read(path)

        self.assertEqual(loaded.solution.rows, solution.rows)
        self.assertEqual(loaded.fill.rows, fill.rows)
        self.assertEqual(loaded.clues, puzzle.clues)
        self.assertEqual(loaded.title, "Sample")
        self.assertEqual(loaded.author, "njones167")
        self.assertEqual(loaded.copyright, "2026 njones167")
        self.assertEqual(loaded.notes, "a test puzzle")

    def test_round_trip_with_blank_metadata(self):
        solution = Grid(["AB", "CD"])
        fill = Grid(["AB", "CD"])
        puzzle = PuzFile(solution=solution, fill=fill)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "blank.puz")
            puzzle.write(path)
            loaded = PuzFile.read(path)

        self.assertEqual(loaded.clues, [])
        self.assertEqual(loaded.title, "")
        self.assertEqual(loaded.notes, "")

    def test_solution_must_be_fully_filled(self):
        solution = Grid(["CA.", "AGO", "TOE"])
        fill = Grid(["CA.", "AGO", "TOE"])
        puzzle = PuzFile(solution=solution, fill=fill)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bad.puz")
            with self.assertRaises(ValueError):
                puzzle.write(path)

    def test_mismatched_block_layout_is_rejected(self):
        solution = Grid(["CAT", "AGO", "TOE"])
        fill = Grid(["CAT", "#GO", "TOE"])
        puzzle = PuzFile(solution=solution, fill=fill)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "mismatch.puz")
            with self.assertRaises(ValueError):
                puzzle.write(path)

    def test_rejects_file_without_magic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "not-a-puzzle.puz")
            with open(path, "wb") as handle:
                handle.write(b"\x00" * 60)
            with self.assertRaises(ValueError):
                PuzFile.read(path)

    def test_detects_corrupted_grid_data(self):
        solution = Grid(["CAT", "AGO", "TOE"])
        fill = Grid(["CAT", "AGO", "TOE"])
        puzzle = PuzFile(solution=solution, fill=fill, clues=["a", "b"])
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "flip.puz")
            puzzle.write(path)
            with open(path, "r+b") as handle:
                handle.seek(60)  # last byte of the 9-cell solution grid
                handle.write(b"Z")
            with self.assertRaises(ValueError):
                PuzFile.read(path)


if __name__ == "__main__":
    unittest.main()
