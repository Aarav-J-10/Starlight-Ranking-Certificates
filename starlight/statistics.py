import math
from statistics import mean


def quantile(values: list[float], p: float) -> float:
    if not values or not 0 <= p <= 1:
        raise ValueError("Quantile needs data and p in [0,1]")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * p
    low, high = math.floor(rank), math.ceil(rank)
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def ols(x: list[float], y: list[float]) -> dict:
    mx, my = mean(x), mean(y)
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    intercept = my - slope * mx
    return {"slope": slope, "intercept_deg": intercept, "rmse_deg": math.sqrt(mean((b - intercept - slope * a) ** 2 for a, b in zip(x, y)))}


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if type(k) is not int or type(n) is not int or not 0 <= k <= n or n <= 0 or not 0 < alpha < 1:
        raise ValueError("Invalid binomial counts/alpha")
    try:
        from scipy.stats import beta
    except ImportError as error:
        raise ImportError('Exact intervals need: python -m pip install -e ".[science]"') from error
    low = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    high = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return low, high


def paired_interval(plus: int, minus: int, n: int, alpha: float, family: int) -> tuple[float, float]:
    if plus + minus > n or family < 1:
        raise ValueError("Invalid paired counts/family")
    pl, ph = clopper_pearson(plus, n, alpha / (2 * family))
    ml, mh = clopper_pearson(minus, n, alpha / (2 * family))
    return 100 * (pl - mh), 100 * (ph - ml)
