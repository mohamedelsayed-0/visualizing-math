"""Tests for scene helper utilities."""

from __future__ import annotations

from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import (
    add_overview_then_zoom,
    compute_scene_bounds,
    fit_distance_for_sphere,
)


def test_compute_scene_bounds():
    center, radius = compute_scene_bounds([
        (-2.0, -4.0, 0.0),
        (6.0, 2.0, 8.0),
    ])

    assert center == (2.0, -1.0, 4.0)
    assert radius > 0


def test_add_overview_then_zoom_adds_camera_path():
    builder = SceneBuilder().add_node("n0", (0.0, 0.0, 0.0))

    add_overview_then_zoom(
        builder,
        positions=[(-30.0, 0.0, 0.0), (30.0, 20.0, 15.0)],
        focus_target=(0.0, 0.0, 0.0),
        secondary_target=(20.0, 10.0, 5.0),
        duration=10.0,
    )

    scene = builder.build()
    assert len(scene.camera_path) == 5
    assert scene.camera_path[0].time == 0.0
    assert scene.camera_path[-1].time == 10.0


def test_fit_distance_for_sphere_increases_as_fov_narrows():
    wide = fit_distance_for_sphere(radius=100.0, fov_degrees=90.0)
    narrow = fit_distance_for_sphere(radius=100.0, fov_degrees=45.0)
    assert narrow > wide
