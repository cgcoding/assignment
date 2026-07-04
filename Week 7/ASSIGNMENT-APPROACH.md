# Advanced Python (Pandas / NumPy / SciPy) - Step-by-Step Assignment Approach

> Spec: [CSO606_Python_Advanced_Assignment.pdf](CSO606_Python_Advanced_Assignment.pdf).
> Allowed libraries: Python standard library, NumPy, Pandas, SciPy only.
> Marks: Q1 = 40 (14 + 8 + 8 + 10), Q2 = 40, Q3 = 40. Total **120**.
>
> Required submission tree:
>
> ```
> <EO ID>/
> |-- q1/ q1_t1.py q1_t2.py q1_t3.py q1_t4.py
> |-- q2/ projectile.py
> `-- q3/ delivery_hub.py
> ```

## Input-file naming note

The data files shipped in this folder are `titanic.csv`, `q1_t2.csv`, `q1_t3.csv`,
`q1_t4.csv`, but the PDF requires the scripts to read `q1_t1_input.csv` ...
`q1_t4_input.csv`. Spec-named copies were created inside [q1/](q1) (e.g.
`q1/q1_t1_input.csv` is a copy of `titanic.csv`), and the scripts read those exact names -
formatting/naming mistakes are explicitly penalised and not re-evaluated. Q3's
`delivery_locations.txt` (the PDF's 6-point sample) and Q2's PDF example input
(`q2/sample_input.txt`) were also created for local verification.

---

## Q1 - The Lost Research Archive (40 marks)

### Task 1 - Passenger Archive Analysis (14 marks) - [q1/q1_t1.py](q1/q1_t1.py)

Read `q1_t1_input.csv`, write `q1_t1_output.csv` with exactly these 11 columns:
`pclass, sex, passenger_count, survivor_count, survival_pct, avg_age, median_fare,
age_std, survival_rank, mean_rolling_survival, max_rolling_survival`.

1. **Part A (group stats).** One `groupby(["pclass", "sex"]).agg(...)` with named
   aggregations: `size` (count), `sum` of `survived` (survivors),
   `100 * mean(survived)` (survival %), `mean`/`std` of `age`, `median` of `fare`.
   Pandas skips NaN ages automatically - exactly what "average passenger age" wants.
2. **Part B (dense rank).** `groupby("pclass")["survival_pct"].rank(method="dense",
   ascending=False)` - the PDF's example (90, 90, 75, 40 -> 1, 1, 2, 3) is precisely
   dense ranking on descending values, *within each class*.
3. **Part C (rolling survival).** Sort passengers by ascending `fare` **within each
   pclass** (stable `mergesort` keeps equal-fare order deterministic), then
   `groupby("pclass")["survived"].transform(lambda s: s.rolling(5, min_periods=1).mean())`.
   `min_periods=1` implements "use all available observations when fewer than 5 exist".
   Then aggregate the per-passenger `rolling_survival` back to (pclass, sex) with
   `mean`/`max` and merge onto the Part A/B table.

**Gotchas**

- The shipped Titanic CSV uses capitalised headers (`Pclass`, `Sex`, `Survived`); the
  script lowercases all column names first so the spec's lowercase names work.
- The rolling window runs over the *class* (sorted by fare), not over (class, sex) -
  the sex split happens only when aggregating the rolling values afterwards.
- `rank(...).astype(int)` because dense ranks are integers, not floats, in the sample.

### Task 2 - Signal Recovery Puzzle (8 marks) - [q1/q1_t2.py](q1/q1_t2.py)

`since_reset` = observations since the most recent `signal == 0` (reset rows are 0; before
any reset, count from the start of the file beginning at 1).

Vectorized recipe: `segment = (signal == 0).cumsum()` gives a segment id that increments at
each reset row; `groupby(segment).cumcount()` numbers rows 0, 1, 2, ... within each segment
(0 on the reset row itself); rows in segment 0 (before the first reset) get `+1` so counting
starts at 1. Verified to reproduce the PDF example
`[7,2,0,3,4,2,5,0,3,4] -> [1,2,0,1,2,3,4,0,1,2]` exactly.

### Task 3 - Fragment Reconstruction Puzzle (8 marks) - [q1/q1_t3.py](q1/q1_t3.py)

Group-wise rolling mean of `measurement` by `experiment`, window 3, preserving input order:
`df.groupby("experiment")["measurement"].transform(lambda s: s.rolling(3, min_periods=1).mean())`.

- `transform` keeps the original index -> original row order is preserved automatically.
- `rolling(...).mean()` skips NaNs inside the window and `min_periods=1` keeps partial
  windows, which is exactly the semantics of the PDF's worked 16-row example (validated
  programmatically: all 16 `smoothened_measurement` values match, including the NaN rows
  getting the mean of their windows' non-NaN values).

### Task 4 - Minefield Mapping System (10 marks) - [q1/q1_t4.py](q1/q1_t4.py)

Minesweeper counts: for every non-hazard cell, the number of hazards among its 8 neighbours;
hazard cells become NaN; output pivoted with rows = y, columns = x.

Recipe: `pivot(index="y", columns="x", values="hazard")` to get the grid, then the neighbour
count is the sum of the grid shifted onto each of the 8 neighbour offsets
(`grid.shift(dy, axis=0).shift(dx, axis=1).fillna(0)`) - `shift` naturally drops
out-of-grid cells. Finally `counts.mask(hazard.eq(1))` NaNs the hazard cells.

---

## Q2 - Asteroid Defense System (40 marks) - [q2/projectile.py](q2/projectile.py)

**Pipeline** (input on stdin: `N K`, then N rows `t x y`, then `ANGLE SPEED`):

1. **Fit** - the asteroid is quadratic in t on both axes; `np.polyfit(t, x, 2)` /
   `np.polyfit(t, y, 2)` is the least-squares estimator for the noisy observations. No
   hardcoded trajectory assumptions - all six coefficients come from the data.
2. **Integrate** - interceptor launches from (0,0) at `t_obs = t_N` with
   `v = SPEED * (cos ANGLE, sin ANGLE)` (degrees -> radians!) and obeys
   `dv/dt = -K * v * |v|` horizontally and `-g - K * vy * |v|` vertically (g = 9.81).
   `scipy.integrate.solve_ivp(..., dense_output=True, rtol=atol=1e-9, max_step=0.5)`
   over a generous 500 s horizon gives a continuously evaluable interceptor path.
3. **Intercept** - define `f(t) = ||A(t) - I(t)|| - 1`. Sample at 200 points/second to
   find the first sign change (`> 0` to `<= 0`), then refine the bracket with
   `scipy.optimize.brentq` (xtol 1e-6, far below the required 1e-3). First crossing =
   *earliest* interception time. Print `HIT <t>` (3 decimals) or `MISS`.

**Gotchas**

- ANGLE is in **degrees** (`math.radians` before cos/sin).
- The earliest time matters - take the *first* bracketed crossing, not the closest
  approach.
- If the distance is already <= 1 exactly at launch, report `t_obs` itself.
- Dense sampling (200/s) is needed because a fast interceptor can cross the 1-unit blast
  sphere within a fraction of a second; a coarse grid could step over the crossing.

**Validation**

- PDF sample input -> `MISS` (verified geometrically: the closest approach is ~30.4 units
  at t = 10.7; the asteroid lands at t = 12.1 while the interceptor is still ~40 units
  high, so no interception is possible).
- Synthetic ground-truth test: constructed a quadratic asteroid passing exactly through the
  simulated interceptor position at t* = 8.0 (t_obs = 5.0, K = 0.02); an independent
  4M-sample reference gives earliest hit t = 7.79360 and the script prints `HIT 7.794` -
  within the 1e-3 tolerance. With Gaussian noise (sigma = 0.3) added to the observations it
  still reports `HIT 7.863`, degrading gracefully with the noisy fit.

---

## Q3 - Optimizing Delivery Hubs (40 marks) - [q3/delivery_hub.py](q3/delivery_hub.py)

Eight functions, strictly **no loops over data or clusters** (only the `while True:`
convergence loop in `kmeans`):

| Function | Vectorized recipe |
|---|---|
| `load_data` (3) | `np.loadtxt(path, delimiter=",", ndmin=2)` -> N x 2 array |
| `initialise_centers` (5) | `np.random.choice(N, K, replace=False)` indices, or convert the given `init_centers` with `np.asarray(..., dtype=float)` |
| `initialise_labels` (2) | `np.zeros(N, dtype=int)` |
| `calculate_distances` (8) | broadcast `data[:, None, :] - centers[None, :, :]` -> (N, K, 2); `sqrt(sum(diff**2, axis=2))` -> (N, K) |
| `update_labels` (4) | `np.argmin(distances, axis=1)` |
| `update_centers` (10) | boolean mask `labels == np.arange(K)[:, None]` of shape (K, N); `mask @ data` sums member coordinates; divide by per-cluster counts (guarded with `np.maximum(counts, 1)` for empty clusters) |
| `check_termination` (2) | `np.array_equal(labels1, labels2)` |
| `kmeans` (6) | `while True:` distances -> labels -> centers; break when labels stop changing; returns `(centers, labels, exec_time)` timed with `time.perf_counter()` |

**Gotchas**

- The termination test compares **labels**, not centers ("the zone labels remain identical
  to the previous iteration").
- `initialise_centers` must sample **without replacement** (duplicate initial hubs collapse
  clusters).
- The `@` (matrix-product) trick in `update_centers` is exactly the hint in the PDF and
  avoids any loop over K.

**Validation**

- The PDF's 6-point sample with `init_centers = [[1,1],[8,8]]` reproduces the expected
  output exactly: centers `[[1.3333, 1.3333], [8.3333, 8.3333]]`, labels `[0 0 0 1 1 1]`.
- Scale test: 150,000 points drawn from three Gaussian blobs converge in 0.17 s with all
  three centers within 0.1 of the generating means - confirming the implementation is
  fully vectorized and scales.

---

## Execution Results (2026-07-04)

Run with Python 3.12.3 (pandas 3.0.3, numpy 2.5.0, scipy 1.18.0) in an isolated venv.

| Deliverable | Result |
|---|---|
| `q1/q1_t1.py` | PASS - 6 (pclass, sex) groups, all 11 columns; dense ranks 1/2 per class (females rank 1 in every class) |
| `q1/q1_t2.py` | PASS - output matches the reset semantics; the PDF example reproduces exactly |
| `q1/q1_t3.py` | PASS - PDF's 16-row worked example reproduced to 1e-5 on every row |
| `q1/q1_t4.py` | PASS - 4x4 grid, hazards NaN, counts hand-checked against the input |
| `q2/projectile.py` | PASS - PDF sample -> `MISS` (verified geometrically); synthetic ground-truth hit reported within 1e-3 |
| `q3/delivery_hub.py` | PASS - PDF sample output matched exactly; 150k-point scale test converges in 0.17 s |

### Revalidation (2026-07-04, second pass)

All outputs were regenerated fresh and cross-checked against **independent brute-force
reimplementations** (plain loops/dicts, no pandas groupby/rolling), plus static
conformance checks:

- **Task 1** - every one of the 9 computed columns matches the brute-force recomputation
  for all 6 groups to 1e-9 (sample std ddof=1, stable fare sort, inclusive window of 5);
  column names and order match the PDF's 11-column list exactly.
- **Task 2** - a simple running-counter loop over the real input reproduces
  `since_reset` exactly; all input rows/columns preserved.
- **Task 3** - a manual last-3-values NaN-skipping mean over the real input matches every
  `smoothened_measurement` value; row order preserved.
- **Task 4** - a double-loop neighbour count over the real 4x4 grid matches every cell;
  hazards are NaN; rows = y, columns = x.
- **Q2** - 7 scenarios: PDF sample (`MISS`, verified geometrically), four synthetic
  ground-truth hits sweeping the constraint space (K = 0.001 / 0.02 / 0.03 / 0.1, angles
  30-70 deg, speeds 80-200, observation windows starting at t = 0, 1, and 4) - all
  reported within **1e-3** of a 6M-sample reference; a genuine far-miss; and a noisy
  (sigma = 0.5) hit that degrades gracefully. The distance sampling was also vectorized
  (single dense-output evaluation) - runtime dropped from ~8 s to ~1 s.
- **Q3** - AST-level check: **0 for loops, 0 comprehensions/generator expressions,
  exactly 1 while** in the whole module; all 8 required function names and parameter
  lists match the PDF; PDF sample output exact; unit checks on every function
  (shapes, argmin, termination, random init without replacement); and a 12,000-point
  3-cluster run matches a naive loop-based reference k-means **exactly** (centers to
  1e-9, labels identical).

**Remaining caveats**

- Q2/Q3 hidden test cases obviously could not be run; the implementations avoid hardcoded
  assumptions (all trajectory coefficients fitted; K, angle, speed all read from input;
  K-Means handles arbitrary K and point counts).
- Q1 Task 4's output format writes the pivoted grid with the y index as the first CSV
  column (rows = y, columns = x per the spec); if the grader wants a headerless matrix,
  drop the `index`/`header` from `to_csv`.
