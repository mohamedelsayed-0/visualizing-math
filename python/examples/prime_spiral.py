"""Example: Prime Spiral

Visualizes integers on a true polar spiral and highlights prime numbers.

Usage:
    viz compile python/examples/prime_spiral.py -o prime_spiral_scene.json
    viz preview prime_spiral_scene.json --port 3000
"""

from __future__ import annotations

import math
from typing import Iterable

from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import add_overview_then_zoom


Vec3 = tuple[float, float, float]


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    limit = int(math.sqrt(n))
    for d in range(3, limit + 1, 2):
        if n % d == 0:
            return False
    return True


def centroid(points: Iterable[Vec3]) -> Vec3:
    pts = list(points)
    if not pts:
        return (0.0, 0.0, 0.0)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sz = sum(p[2] for p in pts)
    inv = 1.0 / len(pts)
    return (sx * inv, sy * inv, sz * inv)


def spiral_point(index: int, theta_step: float, radial_pitch: float) -> Vec3:
    theta = index * theta_step
    radius = 8.0 + radial_pitch * theta
    x = math.cos(theta) * radius
    y = math.sin(theta) * radius
    z = (
        math.sin(theta * 0.75) * 13.0
        + math.cos(theta * 0.31) * 7.0
        + (index * 0.008)
    )
    return (x, y, z)


def build_scene(*, count: int = 1650, theta_step: float = 0.31, radial_pitch: float = 0.58):
    builder = SceneBuilder()

    positions: list[Vec3] = []
    prime_positions: list[Vec3] = []

    for i in range(1, count + 1):
        pos = spiral_point(i, theta_step, radial_pitch)
        positions.append(pos)

        prime = is_prime(i)
        if prime:
            color = "#66ffad"
            size = 1.44
            glow = 2.25
            group = "prime"
            prime_positions.append(pos)
        else:
            color = "#2a3650"
            size = 0.62
            glow = 0.0
            group = "composite"

        node_id = str(i)
        builder.add_node(
            id=node_id,
            position=pos,
            color=color,
            size=size,
            glow=glow,
            group=group,
            reveal_order=1 if prime else 0,
        )

        if i > 1:
            builder.add_edge(
                source=str(i - 1),
                target=node_id,
                color="#4d648e",
                visible=True,
            )

    center = centroid(positions)
    focus_target = prime_positions[len(prime_positions) // 2] if prime_positions else center
    add_overview_then_zoom(
        builder,
        positions,
        focus_target=focus_target,
        global_target=center,
        duration=11.0,
        overview_distance_scale=2.55,
        focus_distance_scale=0.62,
        sweep_distance_scale=0.98,
        fit_padding=1.16,
        overview_hold_ratio=0.20,
        focus_ratio=0.57,
        sweep_ratio=0.84,
        overview_fov=60.0,
        focus_fov=36.0,
        sweep_fov=46.0,
        end_fov=56.0,
    )

    builder.add_cluster_reveal(
        time=0.0,
        groups=["composite", "prime"],
        duration=0.9,
        stagger=0.7,
    )

    builder.set_render(
        width=1920,
        height=1080,
        fps=24,
        duration=11.0,
        background="#060912",
        bloom_strength=1.02,
        bloom_radius=0.18,
        bloom_threshold=0.95,
        fog_near=180,
        fog_far=1800,
        dof_enabled=False,
    )

    return builder.build()


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene

    scene = build_scene()
    compile_scene(scene, "prime_spiral_scene.json")
    print(f"Scene: {len(scene.nodes)} nodes, {len(scene.edges)} edges")
    print("Saved to prime_spiral_scene.json")
