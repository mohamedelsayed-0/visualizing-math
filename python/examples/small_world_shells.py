"""Lightweight Demo: Small-World Shells

Builds a small-world graph and colors nodes by shortest-path shells from a seed.
Good for showing diffusion / information reach without heavy render cost.

Usage:
    viz compile python/examples/small_world_shells.py -o small_world_scene.json
    viz preview small_world_scene.json --port 3000
"""

from __future__ import annotations

import networkx as nx

from mathviz.layout.fruchterman import layout_fruchterman_reingold
from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import add_overview_then_zoom


def build_scene(
    *,
    n: int = 260,
    k: int = 8,
    p: float = 0.08,
    seed: int = 42,
):
    G = nx.watts_strogatz_graph(n=n, k=k, p=p, seed=seed)
    anchor = 0
    distances = nx.single_source_shortest_path_length(G, anchor)
    max_shell = max(distances.values()) if distances else 0

    for node in G.nodes:
        shell = min(max_shell, distances.get(node, max_shell))
        G.nodes[node]["shell"] = f"shell_{shell}"

    positions_arr = layout_fruchterman_reingold(
        G,
        dim=3,
        seed=seed,
        iterations=45,
        scale=95.0,
    )
    node_list = list(G.nodes())
    pos_by_node = {
        node_list[i]: (
            float(positions_arr[i, 0]),
            float(positions_arr[i, 1]),
            float(positions_arr[i, 2]),
        )
        for i in range(len(node_list))
    }

    palette = [
        "#5de2e7",
        "#76d672",
        "#f0e96f",
        "#ffbe5c",
        "#f98a67",
        "#d281ff",
        "#8da8ff",
    ]
    color_map = {
        node: palette[min(distances.get(node, max_shell), len(palette) - 1)]
        for node in G.nodes
    }

    builder = SceneBuilder().from_graph(
        G,
        positions_arr,
        color_map=color_map,
        group_attr="shell",
        size=1.35,
        cluster_layout=True,
        cluster_shape="spiral",
        cluster_spacing=420.0,
        cluster_compactness=0.66,
    )

    shell_groups = sorted({G.nodes[node]["shell"] for node in G.nodes}, key=lambda s: int(s.split("_")[1]))
    builder.add_cluster_reveal(
        time=0.0,
        groups=shell_groups,
        duration=0.8,
        stagger=0.55,
    )
    builder.add_highlight_edges(source=str(anchor), time=6.4, color="#ffffff", duration=1.2)

    add_overview_then_zoom(
        builder,
        pos_by_node.values(),
        focus_target=pos_by_node[anchor],
        duration=10.5,
        overview_distance_scale=2.5,
        focus_distance_scale=0.62,
        sweep_distance_scale=1.02,
        fit_padding=1.16,
        overview_hold_ratio=0.23,
        focus_ratio=0.58,
        sweep_ratio=0.84,
        overview_fov=64.0,
        focus_fov=40.0,
        sweep_fov=50.0,
        end_fov=58.0,
    )

    builder.set_render(
        width=1920,
        height=1080,
        fps=24,
        duration=10.5,
        background="#050a14",
        bloom_strength=1.25,
        bloom_radius=0.24,
        bloom_threshold=0.84,
        fog_near=130,
        fog_far=1000,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene

    scene = build_scene()
    compile_scene(scene, "small_world_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to small_world_scene.json")
