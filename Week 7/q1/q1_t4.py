"""Q1 Task 4: adjacent hazard counts on the exploration grid."""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "q1_t4_input.csv"
OUTPUT_PATH = BASE_DIR / "q1_t4_output.csv"

NEIGHBOUR_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


def main():
    df = pd.read_csv(INPUT_PATH)

    # Grid with rows = y, columns = x.
    hazard = df.pivot(index="y", columns="x", values="hazard").sort_index()

    # Sum the grid shifted onto each of the 8 neighbour positions;
    # shift drops cells that fall outside the grid.
    counts = sum(
        hazard.shift(dy, axis=0).shift(dx, axis=1).fillna(0)
        for dy, dx in NEIGHBOUR_OFFSETS
    )

    # Hazard cells are recorded as NaN.
    result = counts.mask(hazard.eq(1))

    result.to_csv(OUTPUT_PATH)


if __name__ == "__main__":
    main()
