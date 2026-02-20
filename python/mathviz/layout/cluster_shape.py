from __future__ import annotations

from collections import defaultdict
import math
from typing import Hashable, Mapping

import numpy as np


Vec3 = tuple[float, float, float]


def _shape_anchor_points(count: int, shape: str) -> list[tuple[float, float]]:
    if count <= 0:
        return []

    points: list[tuple[float, float]] = []
    for i in range(count):
        t = (2.0 * math.pi * i) / count
        if shape == "circle":
            x = math.cos(t)
            y = math.sin(t)
        elif shape == "infinity":
            d = 1.0 + math.sin(t) ** 2
            x = math.cos(t) / d
            y = (math.sin(t) * math.cos(t)) / d
        elif shape == "heart":
            x = 16.0 * (math.sin(t) ** 3)
            y = (
                13.0 * math.cos(t)
                - 5.0 * math.cos(2.0 * t)
                - 2.0 * math.cos(3.0 * t)
                - math.cos(4.0 * t)
            )
        elif shape == "spiral":
            r = 0.35 + 0.95 * (i / max(1, count - 1))
            a = t * 2.25
            x = r * math.cos(a)
            y = r * math.sin(a)
        else:
            raise ValueError(f"Unknown cluster shape '{shape}'")
        points.append((x, y))

    max_r = max(math.hypot(x, y) for x, y in points) or 1.0
    return [(x / max_r, y / max_r) for x, y in points]


def group_positions_into_shape(
    positions: Mapping[Hashable, Vec3],
    groups: Mapping[Hashable, str | None],
    *,
    shape: str = "infinity",
    spacing: float = 280.0,
    compactness: float = 0.72,
    z_wave: float = 120.0,
    order_by: str = "size",
) -> dict[Hashable, Vec3]:
    """Pack grouped points into a larger global shape while keeping local structure."""
    out = {k: (float(v[0]), float(v[1]), float(v[2])) for k, v in positions.items()}

    buckets: dict[str, list[Hashable]] = defaultdict(list)
    for node_id, group in groups.items():
        if group is None or node_id not in out:
            continue
        buckets[group].append(node_id)

    if len(buckets) <= 1:
        return out

    if order_by == "name":
        labels = sorted(buckets.keys())
    else:
        labels = sorted(buckets.keys(), key=lambda g: (-len(buckets[g]), g))

    anchors = _shape_anchor_points(len(labels), shape)
    compact = max(0.05, float(compactness))
    sep = max(1.0, float(spacing))
    wave = float(z_wave)

    for idx, label in enumerate(labels):
        ids = buckets[label]
        pts = np.array([out[n] for n in ids], dtype=np.float64)
        center = pts.mean(axis=0)

        ax, ay = anchors[idx]
        anchor = np.array(
            [
                ax * sep,
                ay * sep,
                math.sin((2.0 * math.pi * idx) / max(1, len(labels))) * wave,
            ],
            dtype=np.float64,
        )

        local = (pts - center) * compact
        out_pts = local + anchor

        for i, node_id in enumerate(ids):
            p = out_pts[i]
            out[node_id] = (float(p[0]), float(p[1]), float(p[2]))

    return out
