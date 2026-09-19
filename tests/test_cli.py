import contextlib
import io
import json
import os
import tempfile
import unittest

from xgrid.cli import main
from xgrid.grid import Grid
from xgrid.puz import PuzFile

README_GRID = "\n".join(
    [
        "##...",
        "...#.",
        ".....",
        ".#...",
        "...##",
    ]
)


def run_cli(argv):
    """Run main() and capture (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class TextGridTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.path = os.path.join(self.tmpdir.name, "puzzle.txt")
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(README_GRID)

    def test_human_report(self):
        code, out, err = run_cli([self.path])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("5x5 grid, 6 blocks", out)
        self.assertIn("symmetry: ok", out)
        self.assertIn("5 across, 5 down", out)
        self.assertIn("1 across  row 0 col 2 len 3", out)

    def test_json_report(self):
        code, out, _ = run_cli([self.path, "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["width"], 5)
        self.assertEqual(report["height"], 5)
        self.assertEqual(report["block_count"], 6)
        self.assertTrue(report["symmetric"])
        self.assertEqual(report["across_count"], 5)
        self.assertEqual(report["down_count"], 5)
        self.assertEqual(
            report["slots"][0],
            {"number": 1, "direction": "across", "row": 0, "col": 2, "length": 3},
        )
        self.assertNotIn("clue", report["slots"][0])

    def test_render(self):
        code, out, _ = run_cli([self.path, "--render"])
        self.assertEqual(code, 0)
        self.assertEqual(out, Grid.from_text(README_GRID).render() + "\n")

    def test_missing_file_reports_error_on_stderr(self):
        code, out, err = run_cli([os.path.join(self.tmpdir.name, "missing.txt")])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("xgrid:", err)

    def test_asymmetric_grid_reports_broken_symmetry(self):
        path = os.path.join(self.tmpdir.name, "lopsided.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("#..\n...\n...\n")
        code, out, _ = run_cli([path, "--json"])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out)["symmetric"])


class PuzFileCliTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_puzzle(self, name="puzzle.puz", clues=None):
        solution = Grid(["AT", "GO"])
        fill = Grid(["AT", "GO"])
        puzzle = PuzFile(solution=solution, fill=fill, clues=clues or [])
        path = os.path.join(self.tmpdir.name, name)
        puzzle.write(path)
        return path

    def test_puz_json_includes_clues(self):
        path = self._write_puzzle(
            clues=["In the manner of", "Toward", "Where a play runs", "Leave"]
        )
        code, out, _ = run_cli([path, "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(
            [(s["number"], s["direction"], s["clue"]) for s in report["slots"]],
            [
                (1, "across", "In the manner of"),
                (1, "down", "Toward"),
                (2, "down", "Where a play runs"),
                (3, "across", "Leave"),
            ],
        )

    def test_puz_without_clues_omits_clue_field(self):
        path = self._write_puzzle(clues=[])
        code, out, _ = run_cli([path, "--json"])
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertTrue(all("clue" not in s for s in report["slots"]))

    def test_puz_with_mismatched_clue_count_reports_error(self):
        path = self._write_puzzle(clues=["only one"])
        code, out, err = run_cli([path])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("xgrid:", err)

    def test_puz_case_insensitive_extension(self):
        path = self._write_puzzle(name="PUZZLE.PUZ", clues=[])
        code, _, _ = run_cli([path, "--json"])
        self.assertEqual(code, 0)

    def test_not_a_puz_file_reports_error(self):
        path = os.path.join(self.tmpdir.name, "bad.puz")
        with open(path, "wb") as handle:
            handle.write(b"\x00" * 60)
        code, out, err = run_cli([path])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("xgrid:", err)


if __name__ == "__main__":
    unittest.main()
