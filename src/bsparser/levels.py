from statistics import median
from typing import List

IRREGULAR_SHARE = 0.25  # off the grid by more than this share of a step (and more than the tolerance)


def _clusters(xs: List[float], tolerance: float) -> List[List[float]]:
    """Left to right. A position within `tolerance` of the previous one joins its cluster."""
    clusters: List[List[float]] = []
    for x in sorted(xs):
        if clusters and x - clusters[-1][-1] <= tolerance:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    return clusters


def assign_levels(xs: List[float], tolerance: float) -> List[int]:
    """Level 0 is the leftmost cluster."""
    clusters = _clusters(xs, tolerance)
    return [next(i for i, c in enumerate(clusters) if x <= c[-1] + 1e-9) for x in xs]


def irregular_levels(xs: List[float], tolerance: float) -> List[int]:
    """Levels whose centre is far from the regular grid (leftmost centre plus whole steps).
    The step is the median gap between level centres, so it needs at least three levels."""
    centres = [sum(c) / len(c) for c in _clusters(xs, tolerance)]
    if len(centres) < 3:
        return []
    step = median(b - a for a, b in zip(centres, centres[1:]))
    limit = max(tolerance, IRREGULAR_SHARE * step)
    irregular = []
    for i, centre in enumerate(centres):
        position = (centre - centres[0]) / step
        if abs(position - round(position)) * step > limit:
            irregular.append(i)
    return irregular
