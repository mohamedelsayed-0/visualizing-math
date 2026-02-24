"""Demo 3: Embedding Space Exploration

UMAP point cloud with color-coded categories, camera orbit.

Usage:
    viz compile examples/embedding_explore.py -o embedding_scene.json
    viz preview embedding_scene.json
"""

from __future__ import annotations

import networkx as nx

from mathviz.scene.builder import SceneBuilder
from mathviz.layout.fruchterman import layout_fruchterman_reingold
from mathviz.scene.helpers import add_overview_then_zoom


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

    node_list = list(G.nodes())
    pos_by_node = {
        node_list[i]: (
            float(positions[i, 0]),
            float(positions[i, 1]),
            float(positions[i, 2]),
        )
        for i in range(len(node_list))
    }

    # Build scene
    builder = SceneBuilder()
    builder.from_graph(
        G,
        pos_by_node,
        color_map=color_map,
        group_attr="category",
        size=0.86,
        cluster_layout=False,
    )

    duration = 12.5
    add_overview_then_zoom(
        builder,
        pos_by_node.values(),
        focus_target=(0.0, 0.0, 0.0),
        global_target=(0.0, 0.0, 0.0),
        duration=duration,
        overview_distance_scale=3.0,
        focus_distance_scale=1.02,
        sweep_distance_scale=1.24,
        fit_padding=1.40,
        overview_hold_ratio=0.26,
        focus_ratio=0.60,
        sweep_ratio=0.86,
        overview_fov=68.0,
        focus_fov=60.0,
        sweep_fov=64.0,
        end_fov=68.0,
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
        bloom_strength=0.92,
        bloom_radius=0.18,
        bloom_threshold=0.92,
        fog_near=170,
        fog_far=1250,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene
    scene = build_scene()
    compile_scene(scene, "embedding_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to embedding_scene.json")
