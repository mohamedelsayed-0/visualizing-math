"""Demo 1: State-Space Galaxy Flythrough

Generates a random graph, computes layout, and creates a cinematic
flythrough with glowing particles and selective edge highlights.

Usage:
    viz compile examples/galaxy_flythrough.py -o galaxy_scene.json
    viz preview galaxy_scene.json
    viz render galaxy_scene.json -o output/
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from mathviz.scene.builder import SceneBuilder
from mathviz.layout.fruchterman import layout_fruchterman_reingold


def build_scene(
    *,
    num_nodes: int = 2000,
    attach_edges_per_node: int = 3,
    layout_iterations: int = 50,
):
    """Build the galaxy flythrough scene."""
    # Generate a scale-free graph (Barabási-Albert)
    G = nx.barabasi_albert_graph(num_nodes, attach_edges_per_node, seed=42)

    # Assign communities using greedy modularity
    communities = nx.community.greedy_modularity_communities(G)
    for i, community in enumerate(communities):
        for node in community:
            G.nodes[node]["community"] = f"cluster_{i}"

    # Compute 3D layout
    positions = layout_fruchterman_reingold(
        G,
        dim=3,
        seed=42,
        scale=150.0,
        iterations=layout_iterations,
    )

    # Color map by community
    palette = [
        "#ff6b6b", "#4ecdc4", "#45b7d1", "#f7dc6f",
        "#bb8fce", "#82e0aa", "#f0b27a", "#85c1e9",
        "#f1948a", "#73c6b6", "#d4ac0d", "#af7ac5",
    ]
    color_map = {}
    for node in G.nodes():
        community = G.nodes[node].get("community", "cluster_0")
        idx = int(community.split("_")[1]) % len(palette)
        color_map[node] = palette[idx]

    # Build scene
    builder = SceneBuilder()
    builder.from_graph(
        G,
        positions,
        color_map=color_map,
        group_attr="community",
        size=1.2,
    )

    # Camera flythrough: start far away, zoom in, orbit around
    builder.add_camera_keyframe(0.0, (0, 0, 400), (0, 0, 0), fov=70)
    builder.add_camera_keyframe(3.0, (100, 50, 250), (0, 0, 0), fov=60)
    builder.add_camera_keyframe(6.0, (-80, -30, 180), (0, 0, 0), fov=55)
    builder.add_camera_keyframe(8.0, (50, 100, 200), (0, 0, 0), fov=60)
    builder.add_camera_keyframe(10.0, (0, 0, 350), (0, 0, 0), fov=65)

    # Progressive reveal by community
    for i, community in enumerate(communities[:8]):
        builder.add_reveal(f"cluster_{i}", time=0.5 + i * 0.8, duration=0.6)

    # Highlight edges from the highest-degree node
    hub = max(G.nodes(), key=lambda n: G.degree(n))
    builder.add_highlight_edges(source=str(hub), time=5.0, color="#ffaa00", duration=2.0)

    # Render settings
    builder.set_render(
        width=1920,
        height=1080,
        fps=30,
        duration=10.0,
        background="#000011",
        bloom_strength=0.8,
        bloom_radius=0.3,
        bloom_threshold=0.3,
        fog_near=200,
        fog_far=800,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene
    scene = build_scene()
    compile_scene(scene, "galaxy_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to galaxy_scene.json")
