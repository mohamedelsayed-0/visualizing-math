"""UMAP layout for embedding/dimensionality reduction."""

from __future__ import annotations

import networkx as nx
import numpy as np


def layout_umap(
    G: nx.Graph,
    *,
    n_components: int = 3,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    seed: int | None = None,
    scale: float = 100.0,
    node_features: np.ndarray | None = None,
) -> np.ndarray:
    """Compute UMAP layout for a NetworkX graph.

    If node_features is provided, uses those directly.
    Otherwise, computes a graph-based feature matrix from the adjacency.

    Args:
        G: A NetworkX graph.
        n_components: Output dimensions (2 or 3).
        n_neighbors: UMAP n_neighbors parameter.
        min_dist: UMAP min_dist parameter.
        seed: Random seed for reproducibility.
        scale: Scale factor for the output.
        node_features: Optional (N, D) feature matrix for nodes.

    Returns:
        np.ndarray of shape (N, 3) with node positions.
    """
    try:
        import umap
    except ImportError:
        raise ImportError(
            "umap-learn is required for UMAP layout. Install with: pip install umap-learn"
        )

    if node_features is not None:
        X = node_features
    else:
        # Use adjacency matrix as features
        X = nx.to_numpy_array(G, dtype=np.float64)

    reducer = umap.UMAP(
        n_components=min(n_components, 3),
        n_neighbors=min(n_neighbors, len(G.nodes()) - 1),
        min_dist=min_dist,
        random_state=seed,
    )

    embedding = reducer.fit_transform(X)

    # Pad to 3D if needed
    positions = np.zeros((embedding.shape[0], 3), dtype=np.float64)
    positions[:, : embedding.shape[1]] = embedding

    # Scale
    if np.max(np.abs(positions)) > 0:
        positions = positions / np.max(np.abs(positions)) * scale

    return positions
