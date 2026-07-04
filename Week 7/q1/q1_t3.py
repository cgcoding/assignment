"""Q1 Task 3 - Fragment Reconstruction Puzzle.

Reads q1_t3_input.csv and computes a group-wise rolling average of the
`measurement` column (grouped by `experiment`, window 3, preserving original
row order). Missing measurements are ignored inside a window (min_periods=1
plus pandas' NaN-skipping mean). The result is stored in a new column
`smoothened_measurement` and written to q1_t3_output.csv.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "q1_t3_input.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "q1_t3_output.csv")


def main():
    df = pd.read_csv(INPUT_PATH)

    # transform() keeps the original index, so the smoothed values line up
    # with the input rows and the original order is preserved.
    df["smoothened_measurement"] = (
        df.groupby("experiment")["measurement"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
    )

    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
