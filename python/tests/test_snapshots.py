"""Snapshot tests for deterministic scene JSON output."""

from __future__ import annotations

from pathlib import Path

from mathviz.scene.builder import SceneBuilder
from mathviz.scene.compiler import compile_scene


SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "basic_scene.json"


def _build_basic_scene_json() -> str:
    scene = (
        SceneBuilder()
        .add_node("a", (0.0, 0.0, 0.0), color="#ff0000", size=1.5, group="g1", reveal_order=0)
        .add_node("b", (10.0, 0.0, 0.0), color="#00ff00", size=1.0, group="g2", reveal_order=1)
        .add_edge("a", "b", weight=2.0, color="#333333", visible=True)
        .add_camera_keyframe(0.0, (0.0, 0.0, 100.0), (0.0, 0.0, 0.0), fov=60.0)
        .add_reveal("g1", time=0.5, duration=1.0)
        .set_render(
            width=1280,
            height=720,
            fps=24,
            duration=4.0,
            background="#01010a",
            dof_enabled=False,
        )
        .build()
    )
    return compile_scene(scene)


def test_scene_json_matches_snapshot() -> None:
    assert SNAPSHOT_PATH.exists(), f"Missing snapshot: {SNAPSHOT_PATH}"

    actual = _build_basic_scene_json().strip()
    expected = SNAPSHOT_PATH.read_text(encoding="utf-8").strip()

    assert actual == expected
