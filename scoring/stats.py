"""
Small statistics helpers for aggregating scores.

The confidence interval is a normal approximation (1.96 * standard error).
It is computed ACROSS TASKS, because task difficulty is the dominant source of
variance: a benchmark of 6 tasks per tier cannot support a tight interval no
matter how many times each task is resampled. Resampling only reduces noise in
each task's own score.
"""
from __future__ import annotations
import math


def mean_ci(values: list[float]) -> tuple[float, float]:
    """Return (mean, 95% CI half-width). Half-width is 0.0 when n < 2."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    if n < 2:
        return mean, 0.0
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, 1.96 * math.sqrt(var / n)


def combine_means(means_and_halfwidths: list[tuple[float, float]]) -> tuple[float, float]:
    """
    Mean of several independent group means, with the half-widths propagated
    in quadrature: sqrt(sum(hw_i^2)) / k.
    """
    k = len(means_and_halfwidths)
    if k == 0:
        return 0.0, 0.0
    mean = sum(m for m, _ in means_and_halfwidths) / k
    hw = math.sqrt(sum(h ** 2 for _, h in means_and_halfwidths)) / k
    return mean, hw
