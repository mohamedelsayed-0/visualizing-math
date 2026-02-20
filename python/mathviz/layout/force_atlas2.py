"""ForceAtlas2 layout wrapper.

Uses the `fa2` package when available. If it is not installed, falls back to
NetworkX spring_layout with FA2-like parameters.
"""

from __future__ import annotations

import random

import networkx as nx
import numpy as np


def _rescale(positions: np.ndarray, scale: float) -> np.ndarray:
    max_abs = float(np.max(np.abs(positions))) if positions.size else 0.0
    if max_abs > 0:
        return positions / max_abs * scale
    return positions


def layout_forceatlas2(
    G: nx.Graph,
    *,
    iterations: int = 100,
    dim: int = 3,
    seed: int | None = None,
    scale: float = 100.0,
) -> np.ndarray:
    """Compute ForceAtlas2 layout for a NetworkX graph.

    Prefers the `fa2` implementation. If unavailable, uses NetworkX
    spring_layout tuned to approximate FA2 behavior.

    Args:
        G: A NetworkX graph.
        iterations: Number of iterations.
        dim: Output dimensions (2 or 3).
        seed: Random seed for reproducibility.
        scale: Scale factor for the layout.

    Returns:
        np.ndarray of shape (N, 3) with node positions.
    """
    if G.number_of_nodes() == 0:
        return np.zeros((0, 3), dtype=np.float64)

    node_list = list(G.nodes())
    n = len(node_list)

    # Prefer real FA2 implementation when available.
    try:
        from fa2 import ForceAtlas2  # type: ignore

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        fa2 = ForceAtlas2(
            outboundAttractionDistribution=False,
            linLogMode=False,
            adjustSizes=False,
            edgeWeightInfluence=1.0,
            jitterTolerance=1.0,
            barnesHutOptimize=True,
            barnesHutTheta=1.2,
            multiThreaded=False,
            scalingRatio=2.0,
            strongGravityMode=False,
            gravity=1.0,
            verbose=False,
        )

        pos2d = fa2.forceatlas2_networkx_layout(G, pos=None, iterations=iterations)

        positions = np.zeros((n, 3), dtype=np.float64)
        for i, node in enumerate(node_list):
            x, y = pos2d[node]
            positions[i, 0] = float(x)
            positions[i, 1] = float(y)

        # Native fa2 is 2D; synthesize deterministic z for 3D workflows.
        if dim >= 3:
            pos3d = nx.spring_layout(
                G,
                dim=3,
                iterations=max(15, iterations // 4),
                seed=seed,
                scale=1.0,
            )
            for i, node in enumerate(node_list):
                coords = pos3d[node]
                positions[i, 2] = float(coords[2]) if len(coords) >= 3 else 0.0

        return _rescale(positions, scale)
    except Exception:
        pass

    # Fallback: spring layout tuned toward FA2 behavior.
    k = scale / (G.number_of_nodes() ** 0.5) if G.number_of_nodes() > 1 else scale
    pos_dict = nx.spring_layout(
        G,
        dim=min(dim, 3),
        iterations=iterations,
        seed=seed,
        scale=scale,
        k=k,
    )

    positions = np.zeros((n, 3), dtype=np.float64)
    for i, node in enumerate(node_list):
        coords = pos_dict[node]
        positions[i, 0] = coords[0]
        positions[i, 1] = coords[1]
        if dim >= 3 and len(coords) >= 3:
            positions[i, 2] = coords[2]

    return positions
