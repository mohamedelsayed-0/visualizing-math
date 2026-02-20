"""Demo 3: Embedding Space Exploration

UMAP point cloud with color-coded categories, camera orbit.

Usage:
    viz compile examples/embedding_explore.py -o embedding_scene.json
    viz preview embedding_scene.json
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from mathviz.scene.builder import SceneBuilder
from mathviz.layout.fruchterman import layout_fruchterman_reingold


def build_scene(
    *,
    blocks: int = 6,
    block_size: int = 100,
    layout_iterations: int = 50,
):
    """Build the embedding exploration scene.

    Uses Fruchterman-Reingold as a fallback if UMAP is not installed.
    """
    # Generate a graph with clear community structure
    G = nx.planted_partition_graph(blocks, block_size, 0.15, 0.005, seed=42)

    # Assign community labels
    for i, node in enumerate(G.nodes()):
        G.nodes[node]["category"] = f"cat_{i // block_size}"

    # Try UMAP layout, fall back to Fruchterman-Reingold
    try:
        from mathviz.layout.umap_layout import layout_umap
        positions = layout_umap(G, n_components=3, seed=42, scale=120.0)
    except ImportError:
        positions = layout_fruchterman_reingold(
            G,
            dim=3,
            seed=42,
            scale=120.0,
            iterations=layout_iterations,
        )

    # Color palette
    palette = [
        "#e74c3c", "#3498db", "#2ecc71",
        "#f39c12", "#9b59b6", "#1abc9c",
    ]
    color_map = {}
    for node in G.nodes():
        cat_idx = int(G.nodes[node]["category"].split("_")[1])
        color_map[node] = palette[cat_idx % len(palette)]

    # Build scene
    builder = SceneBuilder()
    builder.from_graph(
        G,
        positions,
        color_map=color_map,
        group_attr="category",
        size=0.8,
    )

    # Camera orbit
    duration = 12.0
    steps = 30
    radius = 200
    for i in range(steps + 1):
        angle = (i / steps) * np.pi * 2
        t = (i / steps) * duration
        builder.add_camera_keyframe(
            t,
            (
                float(np.cos(angle) * radius),
                float(radius * 0.3),
                float(np.sin(angle) * radius),
            ),
            (0.0, 0.0, 0.0),
            fov=55,
            easing="linear",
        )

    # Reveal categories sequentially
    for i in range(blocks):
        builder.add_reveal(f"cat_{i}", time=0.5 + i * 1.5, duration=0.8)

    builder.set_render(
        width=1920,
        height=1080,
        fps=30,
        duration=duration,
        background="#050510",
        bloom_strength=2.0,
        bloom_radius=0.6,
        bloom_threshold=0.1,
        fog_near=80,
        fog_far=500,
        dof_enabled=True,
        dof_focus_distance=200,
        dof_aperture=0.015,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene
    scene = build_scene()
    compile_scene(scene, "embedding_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to embedding_scene.json")
