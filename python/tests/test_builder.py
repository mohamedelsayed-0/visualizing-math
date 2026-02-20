"""Tests for the SceneBuilder fluent API."""

import networkx as nx
import numpy as np

from mathviz.scene.builder import SceneBuilder


class TestSceneBuilder:
    def test_add_nodes_and_edges(self):
        scene = (
            SceneBuilder()
            .add_node("a", (0, 0, 0), color="#ff0000")
            .add_node("b", (1, 1, 1), color="#00ff00")
            .add_edge("a", "b", weight=2.0)
            .build()
        )
        assert len(scene.nodes) == 2
        assert len(scene.edges) == 1
        assert scene.nodes[0].color == "#ff0000"
        assert scene.edges[0].weight == 2.0

    def test_from_graph(self):
        G = nx.path_graph(5)
        positions = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [2, 0, 0],
            [3, 0, 0],
            [4, 0, 0],
        ], dtype=np.float64)

        scene = SceneBuilder().from_graph(G, positions).build()
        assert len(scene.nodes) == 5
        assert len(scene.edges) == 4
        assert scene.nodes[2].position == (2.0, 0.0, 0.0)

    def test_from_graph_with_groups(self):
        G = nx.Graph()
        G.add_node(0, community="a")
        G.add_node(1, community="a")
        G.add_node(2, community="b")
        G.add_edge(0, 1)
        G.add_edge(1, 2)

        positions = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=np.float64)

        scene = (
            SceneBuilder()
            .from_graph(G, positions, group_attr="community")
            .build()
        )
        assert scene.nodes[0].group == "a"
        assert scene.nodes[2].group == "b"
        assert scene.nodes[0].reveal_order == 0
        assert scene.nodes[2].reveal_order == 1

    def test_camera_keyframes_sorted(self):
        scene = (
            SceneBuilder()
            .add_node("a", (0, 0, 0))
            .add_camera_keyframe(5.0, (0, 0, 100), (0, 0, 0))
            .add_camera_keyframe(0.0, (0, 0, 200), (0, 0, 0))
            .add_camera_keyframe(10.0, (0, 0, 50), (0, 0, 0))
            .build()
        )
        times = [kf.time for kf in scene.camera_path]
        assert times == [0.0, 5.0, 10.0]

    def test_timeline_sorted(self):
        scene = (
            SceneBuilder()
            .add_node("a", (0, 0, 0), group="g1")
            .add_reveal("g1", time=5.0)
            .add_fade_all(time=1.0, opacity=0.5)
            .build()
        )
        times = [s.time for s in scene.animation_timeline]
        assert times == [1.0, 5.0]

    def test_cluster_reveal_step(self):
        scene = (
            SceneBuilder()
            .add_node("a", (0, 0, 0), group="g1")
            .add_node("b", (1, 0, 0), group="g2")
            .add_cluster_reveal(time=2.0, groups=["g1", "g2"], duration=0.7, stagger=0.3)
            .build()
        )

        step = scene.animation_timeline[0]
        assert step.type == "cluster_reveal"
        assert step.params["groups"] == ["g1", "g2"]

    def test_pulse_node_step(self):
        scene = (
            SceneBuilder()
            .add_node("a", (0, 0, 0), group="g1")
            .add_pulse_node("a", time=1.5, duration=0.8, amplitude=1.2)
            .build()
        )

        step = scene.animation_timeline[0]
        assert step.type == "pulse_node"
        assert step.params["node"] == "a"
        assert step.params["duration"] == 0.8
        assert step.params["amplitude"] == 1.2

    def test_set_render(self):
        scene = (
            SceneBuilder()
            .add_node("a", (0, 0, 0))
            .set_render(width=3840, height=2160, fps=60, bloom_strength=3.0)
            .build()
        )
        assert scene.render_settings.width == 3840
        assert scene.render_settings.fps == 60
        assert scene.render_settings.bloom_strength == 3.0

    def test_deterministic_output(self):
        """Same inputs should produce byte-identical JSON."""
        def make_scene():
            G = nx.path_graph(10)
            pos = np.zeros((10, 3), dtype=np.float64)
            for i in range(10):
                pos[i, 0] = float(i)
            return (
                SceneBuilder()
                .from_graph(G, pos)
                .add_camera_keyframe(0, (0, 0, 100), (0, 0, 0))
                .set_render(duration=5)
                .build()
            )

        scene1 = make_scene()
        scene2 = make_scene()
        assert scene1.model_dump_json() == scene2.model_dump_json()
