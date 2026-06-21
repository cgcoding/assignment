"""Question 3 - The Floo Powder Allocator.

Minimum number of scoops (with unlimited reuse of each size) that sum to exactly
T ounces, or -1 if impossible. Solved with bottom-up dynamic programming.

Input (stdin):
    Line 1: K and T
    Line 2: K scoop sizes
Output: minimum scoops, or -1.
"""

import sys


def min_scoops(target, sizes):
    dp = [0] + [float("inf")] * target
    for amount in range(1, target + 1):
        best = dp[amount]
        for size in sizes:
            if size <= amount and dp[amount - size] + 1 < best:
                best = dp[amount - size] + 1
        dp[amount] = best
    return dp[target] if dp[target] != float("inf") else -1


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    k = int(data[0])
    target = int(data[1])
    sizes = [int(x) for x in data[2:2 + k]]
    print(min_scoops(target, sizes))


if __name__ == "__main__":
    main()
