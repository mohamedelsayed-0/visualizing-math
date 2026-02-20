"""Tests for the Scene JSON schema (Pydantic models)."""

import json

import pytest
from pydantic import ValidationError

from mathviz.scene.models import (
    AnimationStep,
    CameraKeyframe,
    EdgeData,
    NodeData,
    RenderSettings,
    SceneDocument,
)


class TestNodeData:
    def test_valid_node(self):
        node = NodeData(id="n1", position=(1.0, 2.0, 3.0))
        assert node.id == "n1"
        assert node.position == (1.0, 2.0, 3.0)
        assert node.color == "#ffffff"
        assert node.size == 1.0
        assert node.group is None
        assert node.reveal_order == 0

    def test_node_with_all_fields(self):
        node = NodeData(
            id="n2",
            position=(0.0, 0.0, 0.0),
            color="#ff0000",
            size=2.5,
            group="cluster_a",
            reveal_order=3,
        )
        assert node.color == "#ff0000"
        assert node.group == "cluster_a"

    def test_node_serialization_roundtrip(self):
        node = NodeData(id="n1", position=(1.0, 2.0, 3.0), group="g1")
        data = json.loads(node.model_dump_json())
        restored = NodeData.model_validate(data)
        assert restored == node


class TestEdgeData:
    def test_valid_edge(self):
        edge = EdgeData(source="a", target="b")
        assert edge.weight == 1.0
        assert edge.visible is True

    def test_edge_with_weight(self):
        edge = EdgeData(source="a", target="b", weight=0.5, color="#aabbcc")
        assert edge.weight == 0.5
        assert edge.color == "#aabbcc"


class TestCameraKeyframe:
    def test_valid_keyframe(self):
        kf = CameraKeyframe(
            time=5.0,
            position=(0, 0, 100),
            target=(0, 0, 0),
        )
        assert kf.fov == 60.0
        assert kf.easing == "ease-in-out"

    def test_negative_time_rejected(self):
        with pytest.raises(ValidationError):
            CameraKeyframe(time=-1.0, position=(0, 0, 0), target=(0, 0, 0))


class TestAnimationStep:
    def test_valid_step(self):
        step = AnimationStep(
            time=2.0,
            type="reveal_group",
            params={"group": "cluster_0", "duration": 1.0},
        )
        assert step.type == "reveal_group"

    def test_invalid_step_type(self):
        with pytest.raises(ValidationError):
            AnimationStep(time=0, type="invalid_type", params={})

    def test_cluster_reveal_step(self):
        step = AnimationStep(
            time=1.5,
            type="cluster_reveal",
            params={"stagger": 0.2, "duration": 0.8},
        )
        assert step.type == "cluster_reveal"


class TestRenderSettings:
    def test_defaults(self):
        s = RenderSettings()
        assert s.width == 1920
        assert s.height == 1080
        assert s.fps == 30
        assert s.bloom_strength == 1.5
        assert s.tone_mapping == "ACESFilmic"
        assert s.dof_enabled is True

    def test_custom_settings(self):
        s = RenderSettings(width=3840, height=2160, fps=60, bloom_strength=3.0)
        assert s.width == 3840
        assert s.fps == 60


class TestSceneDocument:
    def test_minimal_scene(self):
        doc = SceneDocument(
            nodes=[NodeData(id="n1", position=(0, 0, 0))],
        )
        assert len(doc.nodes) == 1
        assert len(doc.edges) == 0
        assert doc.version == "1.0"

    def test_full_scene_roundtrip(self):
        doc = SceneDocument(
            nodes=[
                NodeData(id="a", position=(1, 2, 3), group="g1"),
                NodeData(id="b", position=(4, 5, 6), group="g1"),
            ],
            edges=[EdgeData(source="a", target="b", weight=0.5)],
            camera_path=[
                CameraKeyframe(time=0, position=(0, 0, 100), target=(0, 0, 0)),
                CameraKeyframe(time=10, position=(50, 0, 100), target=(0, 0, 0)),
            ],
            animation_timeline=[
                AnimationStep(time=1, type="reveal_group", params={"group": "g1"}),
            ],
            render_settings=RenderSettings(duration=10, bloom_strength=2.0),
        )
        json_str = doc.model_dump_json()
        restored = SceneDocument.model_validate_json(json_str)
        assert len(restored.nodes) == 2
        assert restored.edges[0].weight == 0.5
        assert restored.render_settings.bloom_strength == 2.0

    def test_json_schema_generation(self):
        schema = SceneDocument.model_json_schema()
        assert "nodes" in schema["properties"]
        assert "render_settings" in schema["properties"]
