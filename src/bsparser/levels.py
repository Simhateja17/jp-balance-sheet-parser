from typing import List


def assign_levels(xs: List[float], tolerance: float) -> List[int]:
    """Level 0 is the leftmost cluster. Positions within `tolerance` of the previous one share a cluster."""
    clusters: List[float] = []  # last x seen in each cluster, left to right
    for x in sorted(xs):
        if clusters and x - clusters[-1] <= tolerance:
            clusters[-1] = x
        else:
            clusters.append(x)
    return [next(i for i, last in enumerate(clusters) if x <= last + 1e-9) for x in xs]
