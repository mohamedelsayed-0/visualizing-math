# USAGE: Implement a Custom Visualization

This guide shows how to implement a **cluster-reveal flythrough** from scratch using the existing toolkit.

## End Product

After this you should have created a visualization where:

- a graph is laid out in 3D
- node clusters are revealed progressively
- the camera flies through the scene
- selected edges are highlighted
- output is previewed interactively and rendered to video

## 1. Create a Scene Script

Create `python/examples/my_cluster_flythrough.py`:

```python
from __future__ import annotations

import networkx as nx

from mathviz.layout.fruchterman import layout_fruchterman_reingold
from mathviz.scene.builder import SceneBuilder


def build_scene():
    # 1) Data: clustered graph
    sizes = [60, 50, 40, 30]
    probs = [
        [0.25, 0.01, 0.01, 0.01],
        [0.01, 0.28, 0.01, 0.01],
        [0.01, 0.01, 0.30, 0.01],
        [0.01, 0.01, 0.01, 0.32],
    ]
    G = nx.stochastic_block_model(sizes, probs, seed=42)

    labels = []
    for i, size in enumerate(sizes):
        labels.extend([i] * size)
    for node in G.nodes():
        G.nodes[node]["cluster"] = f"cluster_{labels[node]}"

    # 2) Layout
    positions = layout_fruchterman_reingold(G, dim=3, seed=42, iterations=80, scale=120.0)

    # 3) Colors by cluster
    palette = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#f7dc6f"]
    color_map = {node: palette[labels[node] % len(palette)] for node in G.nodes()}

    # 4) Build scene
    builder = SceneBuilder().from_graph(
        G,
        positions,
        color_map=color_map,
        group_attr="cluster",
        size=1.3,
    )

    # Camera path
    builder.add_camera_keyframe(0.0, (0, 40, 220), (0, 0, 0), fov=68)
    builder.add_camera_keyframe(4.0, (100, 25, 160), (0, 0, 0), fov=60)
    builder.add_camera_keyframe(8.0, (-90, 20, 150), (0, 0, 0), fov=58)
    builder.add_camera_keyframe(12.0, (0, 40, 220), (0, 0, 0), fov=68)

    # Cluster reveal (single timeline step with stagger)
    builder.add_cluster_reveal(
        time=0.8,
        groups=["cluster_0", "cluster_1", "cluster_2", "cluster_3"],
        duration=1.0,
        stagger=2.0,
    )

    # Optional edge highlight
    builder.add_highlight_edges(time=9.5, color="#ffffff", duration=1.0)

    builder.set_render(
        width=1920,
        height=1080,
        fps=30,
        duration=12.0,
        background="#080814",
        bloom_strength=1.4,
        bloom_radius=0.45,
        bloom_threshold=0.2,
        fog_near=90,
        fog_far=450,
        dof_enabled=True,
        dof_focus_distance=170,
    )

    return builder.build()
```

## 2. Compile Scene JSON

```bash
viz compile python/examples/my_cluster_flythrough.py -o my_scene.json
```

## 3. Preview Interactively

```bash
viz preview my_scene.json --port 3000
```

Open `http://localhost:3000`.

## 4. Render Frames or MP4

```bash
# PNG frames only
viz render my_scene.json -o output --format frames

# MP4 (requires ffmpeg)
viz render my_scene.json -o output --format mp4
```

## 5. Iteration Workflow

Use this loop for fast iteration:

1. Edit scene script (`build_scene`)
2. Re-run `viz compile ...`
3. Re-run `viz preview ...`
4. Finalize with `viz render ...`

## Useful Implementation Notes

- Use `group_attr` in `from_graph(...)` so reveal/cluster timeline steps can target groups.
- `cluster_reveal` reveals groups progressively with `stagger` and `duration`.
- For large graphs, keep most edges subtle and use `highlight_edges` selectively.
- Keep camera keyframes sparse (4-10 keyframes), let interpolation smooth motion.
- Layout should be computed in Python first; renderer should focus on playback/capture.
