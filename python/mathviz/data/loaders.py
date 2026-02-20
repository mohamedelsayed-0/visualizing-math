"""Data loaders: convert various graph formats to internal representations."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np


def from_networkx(
    G: nx.Graph,
    positions: dict[Any, tuple[float, float, float]] | np.ndarray | None = None,
) -> tuple[nx.Graph, np.ndarray | None]:
    """Normalize a NetworkX graph for use with mathviz.

    Args:
        G: Any NetworkX graph (Graph, DiGraph, etc.)
        positions: Optional pre-computed positions.

    Returns:
        Tuple of (normalized graph, positions array or None).
    """
    # Convert to undirected if directed
    if G.is_directed():
        G = G.to_undirected()

    # Normalize positions to ndarray
    if positions is not None and isinstance(positions, dict):
        node_list = list(G.nodes())
        pos_arr = np.zeros((len(node_list), 3), dtype=np.float64)
        for i, node in enumerate(node_list):
            p = positions[node]
            pos_arr[i, 0] = float(p[0])
            pos_arr[i, 1] = float(p[1])
            pos_arr[i, 2] = float(p[2]) if len(p) > 2 else 0.0
        return G, pos_arr

    return G, positions if isinstance(positions, np.ndarray) else None


def from_edge_list(
    path: str | Path,
    *,
    delimiter: str = ",",
    has_header: bool = True,
    weight_col: int | None = None,
) -> nx.Graph:
    """Load a graph from a CSV/TSV edge list file.

    Expected format: source,target[,weight]

    Args:
        path: Path to edge list file.
        delimiter: Column delimiter.
        has_header: Whether the file has a header row.
        weight_col: Column index for edge weights (0-based).

    Returns:
        A NetworkX Graph.
    """
    G = nx.Graph()
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()

    start = 1 if has_header else 0
    for line in lines[start:]:
        parts = line.strip().split(delimiter)
        if len(parts) < 2:
            continue
        source = parts[0].strip()
        target = parts[1].strip()
        weight = 1.0
        if weight_col is not None and weight_col < len(parts):
            try:
                weight = float(parts[weight_col].strip())
            except ValueError:
                weight = 1.0
        G.add_edge(source, target, weight=weight)

    return G


def from_json_edge_list(path: str | Path) -> nx.Graph:
    """Load a graph from a JSON edge list file.

    Expected format: [{"source": "a", "target": "b", "weight": 1.0}, ...]
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    G = nx.Graph()
    for edge in data:
        G.add_edge(
            str(edge["source"]),
            str(edge["target"]),
            weight=float(edge.get("weight", 1.0)),
        )
    return G


def from_networkx_pickle(path: str | Path) -> nx.Graph:
    """Load a NetworkX graph from a pickle/gpickle file."""
    with Path(path).open("rb") as f:
        obj = pickle.load(f)

    if not isinstance(obj, nx.Graph):
        raise TypeError(f"Pickle at {path} does not contain a NetworkX graph")

    return obj
