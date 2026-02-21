# USAGE: Build Any Visualization Quickly

This guide is a reusable workflow, not just one demo.
Use it as a template for graph data, point clouds, or custom math structures.

## Fast Start

```bash
# 1) Compile any scene script
viz compile python/examples/your_scene.py -o your_scene.json

# 2) Preview locally
viz preview your_scene.json --port 3000

# 3) Render MP4
viz render your_scene.json -o output/your_scene --format mp4
```

## General Template (Graph Data)

Create `python/examples/your_scene.py`:

```python
from __future__ import annotations

import networkx as nx

from mathviz.layout.fruchterman import layout_fruchterman_reingold
from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import add_overview_then_zoom


def build_scene():
    # 1) Data
    G = nx.barabasi_albert_graph(280, 3, seed=42)

    # 2) Optional grouping labels (for reveal + cluster layout)
    communities = nx.community.greedy_modularity_communities(G)
    for i, comm in enumerate(communities):
        for node in comm:
            G.nodes[node]["group"] = f"group_{i}"

    # 3) Layout
    positions = layout_fruchterman_reingold(
        G,
        dim=3,
        seed=42,
        iterations=45,
        scale=110.0,
    )

    # 4) Color map
    palette = ["#7dd3fc", "#86efac", "#fde68a", "#fca5a5", "#c4b5fd"]
    color_map = {}
    for node in G.nodes:
        idx = int(G.nodes[node]["group"].split("_")[1]) % len(palette)
        color_map[node] = palette[idx]

    # 5) Build nodes/edges
    builder = SceneBuilder().from_graph(
        G,
        positions,
        color_map=color_map,
        group_attr="group",
        size=1.15,
        cluster_layout=True,
        cluster_shape="infinity",
        cluster_spacing=360.0,
        cluster_compactness=0.70,
    )

    # 6) Camera helper: full overview -> zoom -> sweep
    # If using ndarray positions, pass a list/tuple iterable (positions is already iterable rows).
    add_overview_then_zoom(
        builder,
        positions,
        focus_target=(0.0, 0.0, 0.0),
        duration=11.0,
        overview_distance_scale=2.45,
        focus_distance_scale=0.70,
        sweep_distance_scale=1.02,
        fit_padding=1.15,
    )

    # 7) Timeline
    builder.add_cluster_reveal(time=0.0, duration=0.9, stagger=0.4)

    # 8) Render settings
    builder.set_render(
        width=1920,
        height=1080,
        fps=24,
        duration=11.0,
        background="#060a14",
        bloom_strength=1.25,
        bloom_radius=0.24,
        bloom_threshold=0.84,
        fog_near=120,
        fog_far=900,
        dof_enabled=False,
    )

    return builder.build()
```

## General Template (Point-Cloud / Non-Graph Data)

Use this when your data is just points or trajectories:

```python
from mathviz.scene.builder import SceneBuilder


def build_scene():
    builder = SceneBuilder()

    # Add points directly
    for i, (x, y, z) in enumerate(my_points):
        builder.add_node(
            id=f"p_{i}",
            position=(x, y, z),
            color="#9ad8ff",
            size=0.9,
            glow=0.2,
            group="points",
        )

    # Optional: connect sequential points / trajectories
    for i in range(1, len(my_points)):
        builder.add_edge(f"p_{i-1}", f"p_{i}", color="#c7d3ea", visible=True)

    # Camera + render
    builder.add_camera_keyframe(0.0, (0, 90, 260), (0, 0, 0), fov=60)
    builder.add_camera_keyframe(8.0, (220, 80, 120), (0, 0, 0), fov=56)
    builder.set_render(width=1920, height=1080, fps=24, duration=8.0)

    return builder.build()
```

## Knobs You Will Reuse Most

- Layout density: `scale`, `iterations`
- Cluster packing: `cluster_spacing`, `cluster_compactness`, `cluster_shape`
- Node readability: `size`, `glow`
- Scene brightness: `bloom_strength`, `bloom_threshold`, edge opacity/color
- Camera storytelling: `add_overview_then_zoom(...)`

## Lightweight Example Gallery

These are intentionally smaller/faster than Klotski but still visually strong:

```bash
# Prime numbers on a square spiral
viz compile python/examples/prime_spiral.py -o prime_spiral_scene.json
viz preview prime_spiral_scene.json --port 3000

# Small-world graph colored by BFS shells
viz compile python/examples/small_world_shells.py -o small_world_scene.json
viz preview small_world_scene.json --port 3000

# Procedural Lissajous ribbon trajectories
viz compile python/examples/lissajous_ribbons.py -o lissajous_scene.json
viz preview lissajous_scene.json --port 3000
```

## Useful Existing Heavy Demo

```bash
viz compile python/examples/klotski_paths.py -o klotski_scene.json
viz preview klotski_scene.json --port 3000
```

## Iteration Loop

1. Edit scene script.
2. `viz compile ...`
3. `viz preview ...`
4. Finalize with `viz render ... --format mp4`

## Playback Control

In preview, press `Space` to pause/resume without on-screen controls.
