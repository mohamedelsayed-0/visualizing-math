"""Example: Lissajous Ribbons

Draws multiple Lissajous trajectories as 3D ribbons.

Usage:
    viz compile python/examples/lissajous_ribbons.py -o lissajous_scene.json
    viz preview lissajous_scene.json --port 3000
"""

from __future__ import annotations

import math

from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import add_overview_then_zoom


def build_scene(
    *,
    streams: int = 6,
    points_per_stream: int = 260,
):
    builder = SceneBuilder()
    duration = 13.5
    positions: list[tuple[float, float, float]] = []

    palettes = ["#54c7ff", "#7effb1", "#ffe177", "#ff9c7c", "#c3a0ff", "#6ff0e2"]
    for s in range(streams):
        group = f"stream_{s}"
        color = palettes[s % len(palettes)]
        phase = s * 0.45
        a = 2 + s
        b = 3 + (s % 3)
        c = 4 + (s % 2)
        previous_id: str | None = None

        for i in range(points_per_stream):
            t = (i / max(1, points_per_stream - 1)) * math.tau
            x = math.sin(a * t + phase) * 220.0
            y = math.sin(b * t) * 150.0
            z = math.cos(c * t + phase * 0.7) * 120.0 + (s - streams / 2.0) * 26.0
            pulse = 0.5 + 0.5 * math.sin(t * 4.0 + phase)
            sparkle = 0.5 + 0.5 * math.cos(t * 3.0 - phase)
            pos = (x, y, z)
            positions.append(pos)
            node_id = f"{group}_{i}"
            builder.add_node(
                id=node_id,
                position=pos,
                color=color,
                size=1.10 + 0.30 * pulse,
                glow=0.30 + 0.30 * sparkle,
                group=group,
                reveal_order=s,
            )

            if previous_id is not None:
                builder.add_edge(
                    source=previous_id,
                    target=node_id,
                    color="#91a5d3",
                    visible=True,
                )
            previous_id = node_id

    for s in range(streams):
        builder.add_reveal(f"stream_{s}", time=0.2 + s * 0.7, duration=0.9)

    add_overview_then_zoom(
        builder,
        positions,
        focus_target=(0.0, 0.0, 0.0),
        duration=duration,
        overview_distance_scale=2.8,
        focus_distance_scale=0.58,
        sweep_distance_scale=0.94,
        fit_padding=1.26,
        overview_hold_ratio=0.24,
        focus_ratio=0.60,
        sweep_ratio=0.86,
        overview_fov=64.0,
        focus_fov=36.0,
        sweep_fov=46.0,
        end_fov=56.0,
    )

    builder.set_render(
        width=1920,
        height=1080,
        fps=24,
        duration=duration,
        background="#070b16",
        bloom_strength=1.05,
        bloom_radius=0.20,
        bloom_threshold=0.88,
        fog_near=160,
        fog_far=1800,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene

    scene = build_scene()
    compile_scene(scene, "lissajous_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to lissajous_scene.json")
