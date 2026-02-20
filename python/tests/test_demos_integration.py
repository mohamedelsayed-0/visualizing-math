"""Integration smoke tests for the demo scenes.

These run each demo's build_scene() in a lightweight configuration,
compile to JSON, and validate round-trip parsing.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from mathviz.scene.compiler import compile_scene, load_scene


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = ROOT / "python" / "examples"


def _load_build_scene(example_file: str):
    path = EXAMPLES_DIR / example_file
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_scene


@pytest.mark.parametrize(
    "example_file,kwargs,expected_step",
    [
        (
            "galaxy_flythrough.py",
            {"num_nodes": 120, "attach_edges_per_node": 2, "layout_iterations": 20},
            "reveal_group",
        ),
        (
            "cluster_reveal.py",
            {"sizes": [12, 10, 8, 6, 4], "layout_iterations": 20},
            "cluster_reveal",
        ),
        (
            "embedding_explore.py",
            {"blocks": 4, "block_size": 30, "layout_iterations": 20},
            "reveal_group",
        ),
    ],
)
def test_demo_scene_build_compile_roundtrip(
    tmp_path: Path,
    example_file: str,
    kwargs: dict,
    expected_step: str,
):
    build_scene = _load_build_scene(example_file)

    scene = build_scene(**kwargs)
    assert len(scene.nodes) > 0
    assert len(scene.animation_timeline) > 0
    assert any(step.type == expected_step for step in scene.animation_timeline)

    out_path = tmp_path / f"{Path(example_file).stem}.json"
    compile_scene(scene, out_path)
    loaded = load_scene(out_path)

    assert len(loaded.nodes) == len(scene.nodes)
    assert loaded.render_settings.duration == scene.render_settings.duration
