"""Scene helper utilities for reusable camera choreography."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from mathviz.scene.builder import SceneBuilder


Vec3 = tuple[float, float, float]


def compute_scene_bounds(positions: Iterable[Vec3]) -> tuple[Vec3, float]:
    """Compute bounding-box center and bounding-sphere radius for 3D positions."""
    pts = np.array(list(positions), dtype=np.float64)
    if pts.size == 0:
        return (0.0, 0.0, 0.0), 1.0

    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)
    center_arr = (mins + maxs) * 0.5
    radius = float(np.linalg.norm(maxs - mins) * 0.5)

    center = (float(center_arr[0]), float(center_arr[1]), float(center_arr[2]))
    return center, max(radius, 1.0)


def fit_distance_for_sphere(
    radius: float,
    fov_degrees: float,
    *,
    padding: float = 1.12,
) -> float:
    """Compute camera distance needed to fit a sphere in view for a given vertical FOV."""
    safe_radius = max(float(radius), 1.0)
    fov = max(5.0, min(175.0, float(fov_degrees)))
    half_fov_rad = math.radians(fov * 0.5)
    distance = safe_radius / math.tan(half_fov_rad)
    return max(safe_radius, distance * max(1.0, float(padding)))


def add_overview_then_zoom(
    builder: SceneBuilder,
    positions: Iterable[Vec3],
    *,
    focus_target: Vec3,
    duration: float,
    start_time: float = 0.0,
    global_target: Vec3 | None = None,
    secondary_target: Vec3 | None = None,
    overview_distance_scale: float = 2.4,
    focus_distance_scale: float = 0.72,
    sweep_distance_scale: float = 1.05,
    fit_padding: float = 1.12,
    overview_height_ratio: float = 0.40,
    focus_lateral_ratio: float = 0.55,
    focus_height_ratio: float = 0.30,
    sweep_lateral_ratio: float = 0.80,
    sweep_height_ratio: float = 0.45,
    sweep_depth_ratio: float = 0.95,
    end_lateral_ratio: float = 0.35,
    end_height_ratio: float = 0.20,
    overview_hold_ratio: float = 0.18,
    focus_ratio: float = 0.50,
    sweep_ratio: float = 0.78,
    overview_fov: float = 62.0,
    focus_fov: float = 40.0,
    sweep_fov: float = 52.0,
    end_fov: float = 58.0,
) -> None:
    """Add a reusable camera path: full overview -> focus zoom -> sweep -> pullback.

    This helper is intended for dense graph scenes where an opening full-context shot
    is followed by a focused close-up on an important region.
    """
    scene_center, radius = compute_scene_bounds(positions)
    gx, gy, gz = global_target if global_target is not None else scene_center
    fx, fy, fz = focus_target

    overview_distance = max(
        radius * overview_distance_scale,
        fit_distance_for_sphere(radius, overview_fov, padding=fit_padding),
    )

    overview_pos = (
        gx,
        gy + radius * overview_height_ratio,
        gz + overview_distance,
    )
    focus_pos = (
        fx + radius * focus_distance_scale * focus_lateral_ratio,
        fy + radius * focus_distance_scale * focus_height_ratio,
        fz + radius * focus_distance_scale,
    )

    if secondary_target is None:
        sx, sy, sz = fx, fy, fz
    else:
        sx, sy, sz = secondary_target

    sweep_pos = (
        sx - radius * sweep_distance_scale * sweep_lateral_ratio,
        sy + radius * sweep_distance_scale * sweep_height_ratio,
        sz + radius * sweep_distance_scale * sweep_depth_ratio,
    )
    end_pos = (
        gx + radius * end_lateral_ratio,
        gy - radius * end_height_ratio,
        gz + radius * (overview_distance_scale * 1.20),
    )

    if not (0.0 < overview_hold_ratio < focus_ratio < sweep_ratio < 1.0):
        raise ValueError(
            "overview_hold_ratio, focus_ratio, and sweep_ratio must satisfy "
            "0 < overview_hold_ratio < focus_ratio < sweep_ratio < 1"
        )

    t0 = start_time
    t1 = start_time + duration * overview_hold_ratio
    t2 = start_time + duration * focus_ratio
    t3 = start_time + duration * sweep_ratio
    t4 = start_time + duration

    builder.add_camera_keyframe(t0, overview_pos, (gx, gy, gz), fov=overview_fov)
    builder.add_camera_keyframe(t1, overview_pos, (gx, gy, gz), fov=overview_fov - 2.0)
    builder.add_camera_keyframe(t2, focus_pos, (fx, fy, fz), fov=focus_fov)
    builder.add_camera_keyframe(t3, sweep_pos, (sx, sy, sz), fov=sweep_fov)
    builder.add_camera_keyframe(t4, end_pos, (gx, gy, gz), fov=end_fov)
