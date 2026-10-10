"""Confidence intervals used by the report. No third-party stats package."""

import math
import random


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion. Returns (low, high)."""
    if n <= 0:
        raise ValueError("n must be positive")
    if successes < 0 or successes > n:
        raise ValueError("successes must be between 0 and n")
    phat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (phat + z2 / (2.0 * n)) / denom
    margin = z * math.sqrt((phat * (1.0 - phat) / n) + z2 / (4.0 * n * n)) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def bootstrap_mean_ci(values: list[float], reps: int = 10000, seed: int = 0) -> dict:
    """Percentile bootstrap CI for the mean. Empty input returns nulls."""
    if not values:
        return {"n": 0, "mean": None, "low": None, "high": None, "reps": reps, "seed": seed}
    n = len(values)
    if n == 1:
        only = float(values[0])
        return {"n": 1, "mean": only, "low": only, "high": only, "reps": reps, "seed": seed}
    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        total = 0.0
        for _i in range(n):
            total += values[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    low_index = int(0.025 * (reps - 1))
    high_index = int(0.975 * (reps - 1))
    return {
        "n": n,
        "mean": sum(values) / n,
        "low": means[low_index],
        "high": means[high_index],
        "reps": reps,
        "seed": seed,
    }
