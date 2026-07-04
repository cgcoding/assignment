"""Q1 Task 1 - Passenger Archive Analysis.

Reads q1_t1_input.csv and writes q1_t1_output.csv with, for every
(pclass, sex) group:

  Part A: passenger_count, survivor_count, survival_pct, avg_age,
          median_fare, age_std
  Part B: survival_rank - dense rank of survival_pct within each pclass
          (highest survival percentage gets rank 1)
  Part C: mean_rolling_survival / max_rolling_survival of a per-passenger
          rolling survival average (window 5, all available observations when
          fewer than 5 exist) computed within each pclass after sorting
          passengers by ascending fare.
"""

import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, "q1_t1_input.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "q1_t1_output.csv")


def main():
    df = pd.read_csv(INPUT_PATH)
    # The archive CSV may use capitalised headers (Pclass, Sex, ...);
    # normalise to the lowercase names used by the spec.
    df.columns = [c.lower() for c in df.columns]

    # ── Part A: per (pclass, sex) statistics ────────────────────────────────
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

    # ── Part B: dense rank of survival_pct within each class ───────────────
    stats["survival_rank"] = (
        stats.groupby("pclass")["survival_pct"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )

    # ── Part C: rolling survival trend ──────────────────────────────────────
    # Within each pclass, sort passengers by ascending fare, then take a
    # rolling mean of `survived` (window 5, min_periods=1 so partial windows
    # use all available observations).
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
