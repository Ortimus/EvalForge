import math

from scoring.stats import combine_means, mean_ci


def test_mean_ci_basic():
    mean, hw = mean_ci([1.0, 0.0, 1.0, 0.0])
    assert mean == 0.5
    # sample std = 0.5774, SE = 0.2887, hw = 1.96 * 0.2887
    assert math.isclose(hw, 1.96 * math.sqrt((4 * 0.25) / 3 / 4), rel_tol=1e-9)


def test_mean_ci_degenerate():
    assert mean_ci([]) == (0.0, 0.0)
    assert mean_ci([0.7]) == (0.7, 0.0)
    assert mean_ci([1.0, 1.0, 1.0]) == (1.0, 0.0)


def test_combine_means_quadrature():
    mean, hw = combine_means([(0.8, 0.3), (0.4, 0.4)])
    assert math.isclose(mean, 0.6)
    assert math.isclose(hw, 0.5 / 2)      # sqrt(0.3^2 + 0.4^2) / 2
    assert combine_means([]) == (0.0, 0.0)
