"""Q2 - Asteroid Defense System.

Reads observations from stdin:

    N K
    t1 x1 y1
    ...
    tN xN yN
    ANGLE SPEED

Fits the asteroid's quadratic trajectory x(t)=a+bt+ct^2, y(t)=d+et+ft^2 by
least squares on the noisy observations, integrates the interceptor's drag
ODE from (0, 0) starting at t_obs = tN, and reports the earliest time T with
||A(T) - I(T)|| <= 1 as "HIT T" (absolute error <= 1e-3), or "MISS".
"""

import math
import sys

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

G = 9.81
BLAST_RADIUS = 1.0
# The interceptor is ballistic (gravity + drag): it goes up, comes down, and
# once it is well below any plausible target there is no further chance of
# interception. Simulating a generous horizon after launch is sufficient.
SIM_HORIZON = 500.0
SAMPLES_PER_SECOND = 200


def read_input(stream):
    tokens = stream.read().split()
    pos = 0

    def take():
        nonlocal pos
        value = tokens[pos]
        pos += 1
        return value

    n = int(take())
    k = float(take())
    obs = np.array([[float(take()) for _ in range(3)] for _ in range(n)])
    angle_deg = float(take())
    speed = float(take())
    return k, obs, angle_deg, speed


def fit_trajectory(obs):
    """Least-squares quadratic fit; returns (coeffs_x, coeffs_y) for polyval."""
    t, x, y = obs[:, 0], obs[:, 1], obs[:, 2]
    coeffs_x = np.polyfit(t, x, 2)
    coeffs_y = np.polyfit(t, y, 2)
    return coeffs_x, coeffs_y


def simulate_interceptor(k, angle_deg, speed, t_obs):
    """Integrate the interceptor ODE from launch at (0,0) at time t_obs."""
    angle = math.radians(angle_deg)
    state0 = [0.0, 0.0, speed * math.cos(angle), speed * math.sin(angle)]

    def rhs(_t, state):
        _x, _y, vx, vy = state
        v = math.hypot(vx, vy)
        return [vx, vy, -k * vx * v, -G - k * vy * v]

    return solve_ivp(
        rhs,
        (t_obs, t_obs + SIM_HORIZON),
        state0,
        method="RK45",
        dense_output=True,
        rtol=1e-9,
        atol=1e-9,
        max_step=0.5,
    )


def main():
    k, obs, angle_deg, speed = read_input(sys.stdin)
    coeffs_x, coeffs_y = fit_trajectory(obs)
    t_obs = obs[-1, 0]

    sol = simulate_interceptor(k, angle_deg, speed, t_obs)
    t_end = sol.t[-1]

    def distance(t):
        ax = np.polyval(coeffs_x, t)
        ay = np.polyval(coeffs_y, t)
        ix, iy, _, _ = sol.sol(t)
        return math.hypot(ax - ix, ay - iy) - BLAST_RADIUS

    # Dense sampling to bracket the first crossing of distance == blast radius,
    # then brentq to refine the earliest interception time to < 1e-3.
    # The dense output is evaluated vectorized over all samples at once.
    num_samples = max(2, int((t_end - t_obs) * SAMPLES_PER_SECOND))
    ts = np.linspace(t_obs, t_end, num_samples)
    states = sol.sol(ts)
    ds = (
        np.hypot(
            np.polyval(coeffs_x, ts) - states[0],
            np.polyval(coeffs_y, ts) - states[1],
        )
        - BLAST_RADIUS
    )

    if ds[0] <= 0.0:
        print(f"HIT {t_obs:.3f}")
        return

    crossings = np.nonzero((ds[:-1] > 0.0) & (ds[1:] <= 0.0))[0]
    if crossings.size == 0:
        print("MISS")
        return

    i = crossings[0]
    t_hit = brentq(distance, ts[i], ts[i + 1], xtol=1e-6)
    print(f"HIT {t_hit:.3f}")


if __name__ == "__main__":
    main()
