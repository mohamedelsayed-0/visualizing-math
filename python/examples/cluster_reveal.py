"""Demo 2: Graph Clustering Reveal

Progressive reveal of graph clusters: nodes fade in by community,
edges appear between groups with distinct colors.

Usage:
    viz compile examples/cluster_reveal.py -o cluster_scene.json
    viz preview cluster_scene.json
"""

from __future__ import annotations

import networkx as nx

from mathviz.scene.builder import SceneBuilder
from mathviz.layout.fruchterman import layout_fruchterman_reingold
from mathviz.scene.helpers import add_overview_then_zoom


def build_scene(
    *,
    sizes: list[int] | None = None,
    layout_iterations: int = 50,
):
    """Build the cluster reveal scene."""
    # Generate a stochastic block model graph (clear clusters)
    if sizes is None:
        sizes = [80, 60, 50, 40, 30]
    probs = [
        [0.25, 0.01, 0.01, 0.01, 0.01],
        [0.01, 0.30, 0.01, 0.01, 0.01],
        [0.01, 0.01, 0.28, 0.01, 0.01],
        [0.01, 0.01, 0.01, 0.35, 0.01],
        [0.01, 0.01, 0.01, 0.01, 0.32],
    ]
    G = nx.stochastic_block_model(sizes, probs, seed=42)

    # Label each node with its block/cluster
    block_labels = []
    for i, size in enumerate(sizes):
        block_labels.extend([i] * size)
    for node in G.nodes():
        G.nodes[node]["cluster"] = f"block_{block_labels[node]}"

    # Layout
    positions = layout_fruchterman_reingold(
        G,
        dim=3,
        seed=42,
        scale=120.0,
        iterations=layout_iterations,
    )

    palette = ["#ff7f7f", "#66d7ff", "#7dffac", "#ffd36c", "#c9a7ff"]

    builder = SceneBuilder()
    node_list = list(G.nodes())
    max_degree = max(G.degree[node] for node in node_list)

    for idx, node in enumerate(node_list):
        deg_norm = G.degree[node] / max(1, max_degree)
        cluster_id = block_labels[node]
        builder.add_node(
            id=str(node),
            position=(
                float(positions[idx, 0]),
                float(positions[idx, 1]),
                float(positions[idx, 2]),
            ),
            color=palette[cluster_id],
            size=1.02 + (deg_norm ** 0.60) * 0.95,
            glow=0.22 + (deg_norm ** 0.85) * 0.78,
            group=f"block_{cluster_id}",
            reveal_order=cluster_id,
        )

    for u, v in G.edges:
        builder.add_edge(str(u), str(v), color="#2b3650", visible=True)

    add_overview_then_zoom(
        builder,
        positions,
        focus_target=(0.0, 0.0, 0.0),
        global_target=(0.0, 0.0, 0.0),
        duration=13.0,
        overview_distance_scale=2.9,
        focus_distance_scale=0.74,
        sweep_distance_scale=1.06,
        fit_padding=1.24,
        overview_hold_ratio=0.08,
        focus_ratio=0.36,
        sweep_ratio=0.78,
        overview_fov=68.0,
        focus_fov=50.0,
        sweep_fov=58.0,
        end_fov=66.0,
    )

    # Reveal clusters one by one with a single cluster_reveal step.
    builder.add_cluster_reveal(
        time=0.45,
        groups=[f"block_{i}" for i in range(len(sizes))],
        duration=0.85,
        stagger=1.85,
    )

    hub = max(G.nodes(), key=lambda n: G.degree[n])
    builder.add_highlight_edges(
        source=str(hub),
        time=7.2,
        color="#ffaa00",
        duration=2.0,
    )

    builder.set_render(
        width=1920,
        height=1080,
        fps=30,
        duration=13.0,
        background="#0a0a1a",
        bloom_strength=0.78,
        bloom_radius=0.14,
        bloom_threshold=0.95,
        fog_near=140,
        fog_far=900,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene
    scene = build_scene()
    compile_scene(scene, "cluster_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to cluster_scene.json")
