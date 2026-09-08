import unittest

from xgrid.grid import Grid, Slot

README_GRID = "\n".join(
    [
        "##...",
        "...#.",
        ".....",
        ".#...",
        "...##",
    ]
)


class NumberingTests(unittest.TestCase):
    def test_readme_grid_numbering(self):
        grid = Grid.from_text(README_GRID)
        numbers = grid.numbering()
        self.assertEqual(
            numbers,
            {
                (0, 2): 1,
                (0, 4): 2,
                (1, 0): 3,
                (1, 1): 4,
                (2, 0): 5,
                (2, 3): 6,
                (3, 2): 7,
                (4, 0): 8,
            },
        )

    def test_isolated_single_cell_is_not_numbered(self):
        # a cell with blocks on every side can't start a two-letter entry
        # in either direction, so it gets no number at all.
        grid = Grid(["###", "#.#", "###"])
        self.assertEqual(grid.numbering(), {})

    def test_fully_open_row_numbers_only_the_first_cell(self):
        grid = Grid(["....."])
        self.assertEqual(grid.numbering(), {(0, 0): 1})


class SlotExtractionTests(unittest.TestCase):
    def test_readme_grid_slots(self):
        grid = Grid.from_text(README_GRID)
        self.assertEqual(
            grid.slots(),
            [
                Slot(1, "across", 0, 2, 3),
                Slot(1, "down", 0, 2, 5),
                Slot(2, "down", 0, 4, 4),
                Slot(3, "across", 1, 0, 3),
                Slot(3, "down", 1, 0, 4),
                Slot(4, "down", 1, 1, 2),
                Slot(5, "across", 2, 0, 5),
                Slot(6, "down", 2, 3, 2),
                Slot(7, "across", 3, 2, 3),
                Slot(8, "across", 4, 0, 3),
            ],
        )

    def test_slot_cells_across(self):
        slot = Slot(1, "across", row=2, col=1, length=3)
        self.assertEqual(slot.cells, [(2, 1), (2, 2), (2, 3)])

    def test_slot_cells_down(self):
        slot = Slot(1, "down", row=0, col=2, length=4)
        self.assertEqual(slot.cells, [(0, 2), (1, 2), (2, 2), (3, 2)])

    def test_isolated_single_cell_has_no_slots(self):
        grid = Grid(["###", "#.#", "###"])
        self.assertEqual(grid.slots(), [])

    def test_no_slot_shorter_than_two_cells(self):
        grid = Grid.from_text(README_GRID)
        self.assertTrue(all(slot.length >= 2 for slot in grid.slots()))


class RenderTests(unittest.TestCase):
    def test_readme_grid_render(self):
        grid = Grid.from_text(README_GRID)
        self.assertEqual(
            grid.render(),
            "\n".join(
                [
                    "    1   2",
                    "# # . . .",
                    "3 4",
                    ". . . # .",
                    "5",
                    ". . . . .",
                    "    7",
                    ". # . . .",
                    "8",
                    ". . . # #",
                ]
            ),
        )

    def test_render_has_two_lines_per_grid_row(self):
        grid = Grid.from_text(README_GRID)
        self.assertEqual(len(grid.render().splitlines()), grid.height * 2)

    def test_render_with_no_numbers(self):
        grid = Grid(["###", "#.#", "###"])
        self.assertEqual(grid.render(), "\n# # #\n\n# . #\n\n# # #")

    def test_render_pads_columns_for_double_digit_numbers(self):
        # 11 slots forces a two-character number field, which must line
        # up with the single-character cell fields below it.
        grid = Grid(
            [
                "..#..#..#..",
                "..#..#..#..",
            ]
        )
        rendered = grid.render()
        number_line, cell_line = rendered.splitlines()[:2]
        self.assertTrue(number_line.startswith("1 "))
        self.assertTrue(cell_line.startswith(". "))


class GridConstructionTests(unittest.TestCase):
    def test_from_text_skips_blank_lines(self):
        grid = Grid.from_text("\n\n...\n.#.\n...\n\n")
        self.assertEqual(grid.rows, ["...", ".#.", "..."])

    def test_empty_text_is_rejected(self):
        with self.assertRaises(ValueError):
            Grid.from_text("")

    def test_ragged_rows_are_rejected(self):
        with self.assertRaises(ValueError):
            Grid(["...", ".."])


if __name__ == "__main__":
    unittest.main()
