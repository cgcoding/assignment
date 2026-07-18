"""Q1 Task 2: count observations since the most recent calibration reset."""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "q1_t2_input.csv"
OUTPUT_PATH = BASE_DIR / "q1_t2_output.csv"


def main():
    df = pd.read_csv(INPUT_PATH)

    # Each reset (signal == 0) starts a new segment; cumcount numbers the
    # rows within a segment starting from 0 on the reset row itself.
    segment = df["signal"].eq(0).cumsum()
    since_reset = df.groupby(segment).cumcount()
    # Rows before the first reset count from the start of the file, from 1.
    since_reset[segment.eq(0)] += 1

    df["since_reset"] = since_reset
    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
