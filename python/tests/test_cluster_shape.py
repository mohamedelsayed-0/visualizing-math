from __future__ import annotations

import numpy as np

from mathviz.layout.cluster_shape import group_positions_into_shape


def test_group_positions_into_shape_separates_group_centers():
    positions = {
        "a0": (0.0, 0.0, 0.0),
        "a1": (4.0, 1.0, 0.0),
        "b0": (0.0, 0.0, 0.0),
        "b1": (-3.0, 2.0, 0.0),
        "c0": (0.0, 0.0, 0.0),
        "c1": (1.0, -4.0, 0.0),
    }
    groups = {
        "a0": "A",
        "a1": "A",
        "b0": "B",
        "b1": "B",
        "c0": "C",
        "c1": "C",
    }

    transformed = group_positions_into_shape(
        positions,
        groups,
        shape="heart",
        spacing=400.0,
        compactness=0.7,
    )

    centers = {}
    for label in {"A", "B", "C"}:
        pts = np.array([transformed[n] for n, g in groups.items() if g == label], dtype=np.float64)
        centers[label] = pts.mean(axis=0)

    assert np.linalg.norm(centers["A"] - centers["B"]) > 120.0
    assert np.linalg.norm(centers["B"] - centers["C"]) > 120.0


def test_group_positions_into_shape_deterministic():
    positions = {
        "n0": (0.0, 0.0, 0.0),
        "n1": (1.0, 2.0, 3.0),
        "n2": (4.0, 5.0, 6.0),
        "n3": (-2.0, 0.0, 1.0),
    }
    groups = {
        "n0": "g0",
        "n1": "g0",
        "n2": "g1",
        "n3": "g1",
    }

    a = group_positions_into_shape(positions, groups, shape="infinity", spacing=250.0)
    b = group_positions_into_shape(positions, groups, shape="infinity", spacing=250.0)

    assert a == b
