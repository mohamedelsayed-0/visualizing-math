"""Fruchterman-Reingold layout using NetworkX's built-in spring_layout."""

from __future__ import annotations

import networkx as nx
import numpy as np


def layout_fruchterman_reingold(
    G: nx.Graph,
    *,
    iterations: int = 50,
    dim: int = 3,
    seed: int | None = None,
    scale: float = 100.0,
) -> np.ndarray:
    """Compute Fruchterman-Reingold layout for a NetworkX graph.

    Args:
        G: A NetworkX graph.
        iterations: Number of iterations.
        dim: Output dimensions (2 or 3).
        seed: Random seed for reproducibility.
        scale: Scale factor for the layout.

    Returns:
        np.ndarray of shape (N, 3) with node positions.
    """
    pos_dict = nx.spring_layout(
        G,
        dim=min(dim, 3),
        iterations=iterations,
        seed=seed,
        scale=scale,
    )

    node_list = list(G.nodes())
    positions = np.zeros((len(node_list), 3), dtype=np.float64)

    for i, node in enumerate(node_list):
        coords = pos_dict[node]
        positions[i, 0] = coords[0]
        positions[i, 1] = coords[1]
        if dim >= 3 and len(coords) >= 3:
            positions[i, 2] = coords[2]

    return positions
