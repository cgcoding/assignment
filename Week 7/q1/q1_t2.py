"""Q1 Task 2 - Signal Recovery Puzzle.

Reads q1_t2_input.csv and adds a `since_reset` column: for every row, the
number of observations since the most recent calibration reset (signal == 0).
Reset rows themselves are 0; rows before any reset count from the beginning
of the dataset (starting at 1). All existing rows/columns are preserved.

Example: signal = [7,2,0,3,4,2,5,0,3,4] -> since_reset = [1,2,0,1,2,3,4,0,1,2]
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "q1_t2_input.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "q1_t2_output.csv")


def main():
    df = pd.read_csv(INPUT_PATH)

    is_reset = df["signal"].eq(0)
    # Segment id: increments at every reset row, so each segment starts at a
    # reset (except segment 0, the run before the first reset).
    segment = is_reset.cumsum()
    # Position within the segment: 0 on the reset row itself, 1, 2, ... after.
    since_reset = df.groupby(segment).cumcount()
    # Before any reset exists, counting starts at 1 from the dataset start.
    since_reset[segment.eq(0)] += 1

    df["since_reset"] = since_reset
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
