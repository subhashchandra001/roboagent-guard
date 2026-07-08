import math


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    if not math.isfinite(value):
        raise ValueError("score must be finite")
    return max(low, min(high, value))


def inverse_ratio(value: float, good_at_or_above: float) -> float:
    return clamp(1.0 - (value / good_at_or_above))


def ratio(value: float, bad_at_or_above: float) -> float:
    return clamp(value / bad_at_or_above)
