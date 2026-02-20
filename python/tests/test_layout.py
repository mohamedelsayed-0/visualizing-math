"""Tests for layout algorithms."""

import networkx as nx
import numpy as np
import pytest

from mathviz.layout.force_atlas2 import layout_forceatlas2
from mathviz.layout.fruchterman import layout_fruchterman_reingold
from mathviz.layout.umap_layout import layout_umap

try:
    import umap  # noqa: F401

    HAS_UMAP = True
except Exception:
    HAS_UMAP = False


class TestFruchtermanReingold:
    def test_basic_layout(self):
        G = nx.path_graph(10)
        positions = layout_fruchterman_reingold(G, dim=3, seed=42)

        assert positions.shape == (10, 3)
        assert not np.any(np.isnan(positions))

    def test_deterministic(self):
        G = nx.barabasi_albert_graph(50, 2, seed=0)
        pos1 = layout_fruchterman_reingold(G, dim=3, seed=42)
        pos2 = layout_fruchterman_reingold(G, dim=3, seed=42)
        np.testing.assert_array_equal(pos1, pos2)

    def test_2d_layout(self):
        G = nx.cycle_graph(8)
        positions = layout_fruchterman_reingold(G, dim=2, seed=42)

        assert positions.shape == (8, 3)
        # z-coordinates should be 0 for 2D layout
        np.testing.assert_array_equal(positions[:, 2], 0.0)

    def test_no_overlapping_positions(self):
        """No two nodes should be at the exact same position."""
        G = nx.barabasi_albert_graph(100, 3, seed=42)
        positions = layout_fruchterman_reingold(G, dim=3, seed=42)

        # Check pairwise distances (at least for a sample)
        for i in range(min(50, len(positions))):
            for j in range(i + 1, min(50, len(positions))):
                dist = np.linalg.norm(positions[i] - positions[j])
                assert dist > 1e-10, f"Nodes {i} and {j} overlap"

    def test_empty_graph(self):
        G = nx.Graph()
        G.add_node(0)
        positions = layout_fruchterman_reingold(G, dim=3, seed=42)
        assert positions.shape == (1, 3)


class TestForceAtlas2:
    def test_basic_layout(self):
        G = nx.path_graph(12)
        positions = layout_forceatlas2(G, dim=3, seed=42, iterations=30)

        assert positions.shape == (12, 3)
        assert not np.any(np.isnan(positions))

    def test_deterministic(self):
        G = nx.barabasi_albert_graph(60, 2, seed=5)
        pos1 = layout_forceatlas2(G, dim=3, seed=123, iterations=40)
        pos2 = layout_forceatlas2(G, dim=3, seed=123, iterations=40)
        np.testing.assert_array_equal(pos1, pos2)

    def test_no_overlapping_positions(self):
        """No two nodes should be at the exact same position."""
        G = nx.barabasi_albert_graph(80, 3, seed=42)
        positions = layout_forceatlas2(G, dim=3, seed=42, iterations=40)

        for i in range(min(40, len(positions))):
            for j in range(i + 1, min(40, len(positions))):
                dist = np.linalg.norm(positions[i] - positions[j])
                assert dist > 1e-10, f"Nodes {i} and {j} overlap"

    def test_empty_graph(self):
        G = nx.Graph()
        positions = layout_forceatlas2(G, dim=3, seed=42)
        assert positions.shape == (0, 3)


class TestUmapLayout:
    @pytest.mark.skipif(not HAS_UMAP, reason="umap-learn not installed")
    def test_umap_shape_and_nan(self):
        G = nx.barabasi_albert_graph(40, 2, seed=42)
        positions = layout_umap(G, n_components=3, seed=42)

        assert positions.shape == (40, 3)
        assert not np.any(np.isnan(positions))
