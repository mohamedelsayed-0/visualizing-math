"""Lightweight Demo: Prime Spiral (Ulam-style)

Visualizes integers on a square spiral and highlights prime numbers.
This example is lightweight but still visually rich.

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


def spiral_coords(count: int) -> list[tuple[int, int]]:
    if count <= 0:
        return []

    coords = [(0, 0)]
    x, y = 0, 0
    step_len = 1
    directions = ((1, 0), (0, 1), (-1, 0), (0, -1))
    direction_idx = 0

    while len(coords) < count:
        for _ in range(2):
            dx, dy = directions[direction_idx % 4]
            for _ in range(step_len):
                if len(coords) >= count:
                    break
                x += dx
                y += dy
                coords.append((x, y))
            direction_idx += 1
        step_len += 1

    return coords


def centroid(points: Iterable[Vec3]) -> Vec3:
    pts = list(points)
    if not pts:
        return (0.0, 0.0, 0.0)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sz = sum(p[2] for p in pts)
    inv = 1.0 / len(pts)
    return (sx * inv, sy * inv, sz * inv)


def build_scene(*, count: int = 1800, spacing: float = 6.0):
    coords = spiral_coords(count)
    builder = SceneBuilder()

    positions: list[Vec3] = []
    prime_positions: list[Vec3] = []

    for i, (sx, sy) in enumerate(coords, start=1):
        x = sx * spacing
        y = sy * spacing
        # Small z undulation adds depth while keeping spiral readable.
        z = (
            math.sin(i * 0.052) * spacing * 0.8
            + math.cos(i * 0.017) * spacing * 0.55
        )
        pos = (x, y, z)
        positions.append(pos)

        prime = is_prime(i)
        if prime:
            color = "#30ff8a"
            size = 1.95
            glow = 3.3
            group = "prime"
            prime_positions.append(pos)
        else:
            color = "#cbd7f0"
            size = 0.78
            glow = 0.12
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

        if i > 1 and i % 3 == 0:
            builder.add_edge(
                source=str(i - 1),
                target=node_id,
                color="#2c3954",
                visible=True,
            )

    focus_target = centroid(prime_positions) if prime_positions else centroid(positions)
    add_overview_then_zoom(
        builder,
        positions,
        focus_target=focus_target,
        global_target=centroid(positions),
        duration=11.0,
        overview_distance_scale=2.4,
        focus_distance_scale=0.55,
        sweep_distance_scale=0.95,
        fit_padding=1.18,
        overview_hold_ratio=0.22,
        focus_ratio=0.55,
        sweep_ratio=0.82,
        overview_fov=62.0,
        focus_fov=38.0,
        sweep_fov=48.0,
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
        bloom_strength=1.35,
        bloom_radius=0.26,
        bloom_threshold=0.86,
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
