"""Q1 Task 3: group-wise rolling average of measurements."""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "q1_t3_input.csv"
OUTPUT_PATH = BASE_DIR / "q1_t3_output.csv"


def main():
    df = pd.read_csv(INPUT_PATH)

    # transform keeps the original index, so row order is preserved.
    # NaN measurements are skipped inside each window of 3.
    df["smoothened_measurement"] = (
        df.groupby("experiment")["measurement"]
        .transform(lambda s: s.rolling(window=3, min_periods=1).mean())
    )

    df.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
