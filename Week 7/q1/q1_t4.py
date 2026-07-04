"""Q1 Task 4 - Minefield Mapping System.

Reads q1_t4_input.csv (columns x, y, hazard). For every non-hazard cell,
counts the hazards among its eight neighbours (cells outside the grid are
ignored); hazard cells are recorded as NaN. The result is pivoted into a grid
(rows = y, columns = x) and written to q1_t4_output.csv.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "q1_t4_input.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "q1_t4_output.csv")

NEIGHBOUR_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


def main():
    df = pd.read_csv(INPUT_PATH)

    # Hazard grid: rows = y, columns = x.
    hazard = df.pivot(index="y", columns="x", values="hazard").sort_index()

    # Adjacent hazard count = sum of the hazard grid shifted onto each of the
    # eight neighbour positions. shift() drops values that fall off the grid,
    # which is exactly the "ignore cells outside the grid" rule.
    counts = sum(
        hazard.shift(dy, axis=0).shift(dx, axis=1).fillna(0)
        for dy, dx in NEIGHBOUR_OFFSETS
    )

    # Hazard cells themselves are NaN in the final map.
    result = counts.mask(hazard.eq(1))

    result.to_csv(OUTPUT_PATH)


if __name__ == "__main__":
    main()
