"""Lightweight Demo: Small-World Shells

Builds a small-world graph and colors nodes by shortest-path shells from a seed.
Good for showing diffusion / information reach without heavy render cost.

Usage:
    viz compile python/examples/small_world_shells.py -o small_world_scene.json
    viz preview small_world_scene.json --port 3000
"""

from __future__ import annotations

import math
import random
from typing import Dict

import networkx as nx

from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import add_overview_then_zoom, compute_scene_bounds


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

    rng = random.Random(seed)
    shells: Dict[int, list[int]] = {s: [] for s in range(max_shell + 1)}
    for node in G.nodes:
        shells[distances.get(node, max_shell)].append(node)

    shell_spacing = 140.0
    pos_by_node: Dict[int, tuple[float, float, float]] = {}

    for shell in range(max_shell + 1):
        nodes_in_shell = shells[shell]
        if not nodes_in_shell:
            continue

        nodes_ordered = sorted(nodes_in_shell, key=lambda node: (-G.degree[node], node))
        count_in_shell = len(nodes_ordered)
        base_radius = 16.0 + shell * shell_spacing
        angle_shift = shell * 0.41
        angle_jitter = (2.0 * math.pi) / max(12, count_in_shell * 1.9)

        for idx, node in enumerate(nodes_ordered):
            angle = (2.0 * math.pi * idx) / max(1, count_in_shell)
            angle += angle_shift + (rng.random() - 0.5) * angle_jitter

            radial_jitter = (rng.random() - 0.5) * shell_spacing * 0.13
            radius = max(10.0, base_radius + radial_jitter)

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            z = (shell - max_shell * 0.5) * 18.0 + (rng.random() - 0.5) * 10.0
            pos_by_node[node] = (x, y, z)

    palette = [
        "#5de2e7",
        "#76d672",
        "#f0e96f",
        "#ffbe5c",
        "#f98a67",
        "#d281ff",
        "#8da8ff",
    ]
    builder = SceneBuilder()

    for node in G.nodes:
        shell = distances.get(node, max_shell)
        is_anchor = node == anchor
        color = "#ffffff" if is_anchor else palette[min(shell, len(palette) - 1)]
        size = 2.45 if is_anchor else max(0.90, 1.35 - shell * 0.08)
        glow = 1.65 if is_anchor else (0.28 if shell <= 1 else 0.12)
        builder.add_node(
            id=str(node),
            position=pos_by_node[node],
            color=color,
            size=size,
            glow=glow,
            group=f"shell_{shell}",
            reveal_order=shell,
        )

    for u, v in G.edges:
        su = distances.get(u, max_shell)
        sv = distances.get(v, max_shell)
        delta = abs(su - sv)
        if delta == 0:
            edge_color = "#1f2f48"
        elif delta == 1:
            edge_color = "#82b6ff"
        else:
            edge_color = "#ffb06c"  # shortcut edges emphasize small-world jumps
        builder.add_edge(str(u), str(v), color=edge_color, visible=True)

    shell_groups = sorted(
        {G.nodes[node]["shell"] for node in G.nodes},
        key=lambda s: int(s.split("_")[1]),
    )
    builder.add_cluster_reveal(
        time=0.0,
        groups=shell_groups,
        duration=0.85,
        stagger=0.82,
    )
    builder.add_highlight_edges(source=str(anchor), time=0.9, color="#ffffff", duration=1.1)

    for shell in range(max_shell + 1):
        nodes = shells[shell]
        if not nodes:
            continue
        t = 0.45 + shell * 0.82
        for node in nodes:
            builder.add_pulse_node(
                str(node),
                time=t,
                duration=1.0 if node == anchor else 0.62,
                amplitude=1.8 if node == anchor else 0.56,
            )

    center, _ = compute_scene_bounds(pos_by_node.values())

    add_overview_then_zoom(
        builder,
        pos_by_node.values(),
        focus_target=center,
        global_target=center,
        duration=12.0,
        overview_distance_scale=3.15,
        focus_distance_scale=1.10,
        sweep_distance_scale=1.30,
        fit_padding=1.42,
        overview_hold_ratio=0.28,
        focus_ratio=0.64,
        sweep_ratio=0.88,
        overview_fov=70.0,
        focus_fov=62.0,
        sweep_fov=66.0,
        end_fov=70.0,
    )

    builder.set_render(
        width=1920,
        height=1080,
        fps=24,
        duration=12.0,
        background="#050a14",
        bloom_strength=0.95,
        bloom_radius=0.18,
        bloom_threshold=0.92,
        fog_near=280,
        fog_far=2300,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene

    scene = build_scene()
    compile_scene(scene, "small_world_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to small_world_scene.json")
