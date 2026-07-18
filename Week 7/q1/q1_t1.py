"""Q1 Task 1: passenger survival report grouped by (pclass, sex)."""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "q1_t1_input.csv"
OUTPUT_PATH = BASE_DIR / "q1_t1_output.csv"


def main():
    df = pd.read_csv(INPUT_PATH)
    # The input CSV may use capitalised headers (Pclass, Sex, ...).
    df.columns = [c.lower() for c in df.columns]

    # Part A: group statistics
    stats = (
        df.groupby(["pclass", "sex"])
        .agg(
            passenger_count=("survived", "size"),
            survivor_count=("survived", "sum"),
            survival_pct=("survived", lambda s: 100.0 * s.mean()),
            avg_age=("age", "mean"),
            median_fare=("fare", "median"),
            age_std=("age", "std"),
        )
        .reset_index()
    )

    # Part B: dense rank of survival_pct within each class
    stats["survival_rank"] = (
        stats.groupby("pclass")["survival_pct"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )

    # Part C: rolling survival within each class, sorted by ascending fare.
    # min_periods=1 uses all available observations for partial windows.
    ordered = df.sort_values(["pclass", "fare"], kind="mergesort")
    ordered["rolling_survival"] = (
        ordered.groupby("pclass")["survived"]
        .transform(lambda s: s.rolling(window=5, min_periods=1).mean())
    )

    rolling_stats = (
        ordered.groupby(["pclass", "sex"])["rolling_survival"]
        .agg(mean_rolling_survival="mean", max_rolling_survival="max")
        .reset_index()
    )

    out = stats.merge(rolling_stats, on=["pclass", "sex"])
    out = out[
        [
            "pclass",
            "sex",
            "passenger_count",
            "survivor_count",
            "survival_pct",
            "avg_age",
            "median_fare",
            "age_std",
            "survival_rank",
            "mean_rolling_survival",
            "max_rolling_survival",
        ]
    ]
    out.to_csv(OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
