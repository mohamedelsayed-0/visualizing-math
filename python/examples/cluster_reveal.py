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

    # Color palette per cluster
    palette = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#f7dc6f", "#bb8fce"]
    color_map = {
        node: palette[block_labels[node]] for node in G.nodes()
    }

    # Build scene
    builder = SceneBuilder()
    builder.from_graph(
        G,
        positions,
        color_map=color_map,
        group_attr="cluster",
        size=1.5,
    )

    # Start with everything hidden
    # (The renderer defaults to visible; timeline reveal_group sets to 1.0)

    # Camera: static elevated view, slow orbit
    builder.add_camera_keyframe(0.0, (0, 80, 200), (0, 0, 0), fov=65)
    builder.add_camera_keyframe(5.0, (100, 60, 180), (0, 0, 0), fov=60)
    builder.add_camera_keyframe(10.0, (-50, 80, 200), (0, 0, 0), fov=65)
    builder.add_camera_keyframe(15.0, (0, 80, 200), (0, 0, 0), fov=65)

    # Reveal clusters one by one with a single cluster_reveal step.
    builder.add_cluster_reveal(
        time=1.0,
        groups=[f"block_{i}" for i in range(len(sizes))],
        duration=1.0,
        stagger=2.5,
    )

    # Highlight inter-cluster edges at the end
    builder.add_highlight_edges(time=14.0, color="#ffffff", duration=1.0)

    builder.set_render(
        width=1920,
        height=1080,
        fps=30,
        duration=15.0,
        background="#0a0a1a",
        bloom_strength=1.5,
        bloom_radius=0.4,
        fog_near=80,
        fog_far=400,
        dof_enabled=True,
        dof_focus_distance=180,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene
    scene = build_scene()
    compile_scene(scene, "cluster_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to cluster_scene.json")
