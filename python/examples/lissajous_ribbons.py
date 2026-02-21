"""Lightweight Demo: Lissajous Ribbons

Draws several Lissajous trajectories as glowing ribbons in 3D.
No heavy graph algorithms; mostly direct procedural geometry.

Usage:
    viz compile python/examples/lissajous_ribbons.py -o lissajous_scene.json
    viz preview lissajous_scene.json --port 3000
"""

from __future__ import annotations

import math

from mathviz.scene.builder import SceneBuilder


def build_scene(
    *,
    streams: int = 5,
    points_per_stream: int = 320,
):
    builder = SceneBuilder()
    duration = 10.0

    palettes = ["#67d5ff", "#8bff9f", "#ffe07a", "#ff9d75", "#cf9eff", "#7dffdf"]
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
            x = math.sin(a * t + phase) * 185.0
            y = math.sin(b * t) * 125.0
            z = math.cos(c * t + phase * 0.7) * 105.0 + (s - streams / 2.0) * 18.0
            pos = (x, y, z)
            node_id = f"{group}_{i}"
            builder.add_node(
                id=node_id,
                position=pos,
                color=color,
                size=0.86,
                glow=0.26,
                group=group,
                reveal_order=s,
            )

            if previous_id is not None:
                builder.add_edge(
                    source=previous_id,
                    target=node_id,
                    color="#c9d5ef",
                    visible=True,
                )
            previous_id = node_id

    for s in range(streams):
        builder.add_reveal(f"stream_{s}", time=0.2 + s * 0.7, duration=0.9)

    # Smooth orbit + slight elevation change.
    orbit_steps = 26
    for i in range(orbit_steps + 1):
        p = i / orbit_steps
        ang = p * math.tau
        x = math.cos(ang) * 430.0
        z = math.sin(ang) * 430.0
        y = 130.0 + math.sin(ang * 1.5) * 42.0
        builder.add_camera_keyframe(
            p * duration,
            (x, y, z),
            (0.0, 0.0, 0.0),
            fov=56.0,
            easing="linear",
        )

    builder.set_render(
        width=1920,
        height=1080,
        fps=24,
        duration=duration,
        background="#070b16",
        bloom_strength=1.2,
        bloom_radius=0.24,
        bloom_threshold=0.80,
        fog_near=160,
        fog_far=1300,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene

    scene = build_scene()
    compile_scene(scene, "lissajous_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to lissajous_scene.json")
