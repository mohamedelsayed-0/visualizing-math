"""Fluent SceneBuilder API for constructing scene documents."""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np

from mathviz.scene.models import (
    AnimationStep,
    CameraKeyframe,
    EdgeData,
    NodeData,
    RenderSettings,
    SceneDocument,
)


class SceneBuilder:
    """Fluent builder for constructing a SceneDocument.

    Usage:
        scene = (
            SceneBuilder()
            .from_graph(G, positions)
            .add_camera_keyframe(0, (0, 0, 200), (0, 0, 0))
            .add_camera_keyframe(10, (100, 50, 150), (0, 0, 0))
            .add_reveal("group_a", time=2.0)
            .set_render(width=1920, height=1080, duration=10)
            .build()
        )
    """

    def __init__(self) -> None:
        self._nodes: list[NodeData] = []
        self._edges: list[EdgeData] = []
        self._camera_path: list[CameraKeyframe] = []
        self._timeline: list[AnimationStep] = []
        self._render_settings = RenderSettings()

    def add_node(
        self,
        id: str,
        position: tuple[float, float, float],
        *,
        color: str = "#ffffff",
        size: float = 1.0,
        glow: float = 1.0,
        group: str | None = None,
        reveal_order: int = 0,
    ) -> SceneBuilder:
        self._nodes.append(
            NodeData(
                id=id,
                position=position,
                color=color,
                size=size,
                glow=glow,
                group=group,
                reveal_order=reveal_order,
            )
        )
        return self

    def add_edge(
        self,
        source: str,
        target: str,
        *,
        weight: float = 1.0,
        color: str | None = None,
        visible: bool = True,
    ) -> SceneBuilder:
        self._edges.append(
            EdgeData(
                source=source,
                target=target,
                weight=weight,
                color=color,
                visible=visible,
            )
        )
        return self

    def from_graph(
        self,
        G: nx.Graph,
        positions: dict[Any, tuple[float, float, float]] | np.ndarray,
        *,
        color_map: dict[Any, str] | None = None,
        group_attr: str | None = None,
        size: float = 1.0,
        cluster_layout: bool = True,
        cluster_shape: str = "infinity",
        cluster_spacing: float = 280.0,
        cluster_compactness: float = 0.72,
    ) -> SceneBuilder:
        """Populate nodes and edges from a NetworkX graph + positions.

        Args:
            G: A NetworkX graph.
            positions: Either a dict {node_id: (x,y,z)} or an ndarray (N,3)
                       where row order matches G.nodes().
            color_map: Optional dict mapping node_id to hex color.
            group_attr: Node attribute name to use as group (for reveal ordering).
            size: Default node size.
            cluster_layout: If True and group_attr is provided, pack groups together.
            cluster_shape: Global shape used to place group anchors.
            cluster_spacing: Distance between group anchors.
            cluster_compactness: Scale applied inside each group.
        """
        node_list = list(G.nodes())

        # Normalize positions to dict
        if isinstance(positions, np.ndarray):
            pos_dict = {
                node_list[i]: tuple(positions[i].tolist())
                for i in range(len(node_list))
            }
        else:
            pos_dict = positions

        node_groups: dict[Any, str | None] = {}
        if group_attr:
            for node in node_list:
                if group_attr in G.nodes[node]:
                    node_groups[node] = str(G.nodes[node][group_attr])
                else:
                    node_groups[node] = None

            if cluster_layout:
                from mathviz.layout.cluster_shape import group_positions_into_shape

                pos_dict = group_positions_into_shape(
                    pos_dict,
                    node_groups,
                    shape=cluster_shape,
                    spacing=cluster_spacing,
                    compactness=cluster_compactness,
                )

        # Collect unique groups for reveal ordering
        groups: dict[str, int] = {}
        group_counter = 0

        for node in node_list:
            pos = pos_dict[node]
            color = (color_map or {}).get(node, "#ffffff")
            group = None
            reveal_order = 0
            if group_attr:
                group = node_groups.get(node)
            if group is not None:
                if group not in groups:
                    groups[group] = group_counter
                    group_counter += 1
                reveal_order = groups[group]

            self.add_node(
                id=str(node),
                position=(float(pos[0]), float(pos[1]), float(pos[2])),
                color=color,
                size=size,
                group=group,
                reveal_order=reveal_order,
            )

        for u, v, data in G.edges(data=True):
            self.add_edge(
                source=str(u),
                target=str(v),
                weight=float(data.get("weight", 1.0)),
            )

        return self

    def add_camera_keyframe(
        self,
        time: float,
        position: tuple[float, float, float],
        target: tuple[float, float, float],
        *,
        fov: float = 60.0,
        easing: str = "ease-in-out",
    ) -> SceneBuilder:
        self._camera_path.append(
            CameraKeyframe(
                time=time,
                position=position,
                target=target,
                fov=fov,
                easing=easing,
            )
        )
        return self

    def add_reveal(self, group: str, *, time: float, duration: float = 1.0) -> SceneBuilder:
        """Add a progressive reveal animation for a node group."""
        self._timeline.append(
            AnimationStep(
                time=time,
                type="reveal_group",
                params={"group": group, "duration": duration},
            )
        )
        return self

    def add_cluster_reveal(
        self,
        *,
        time: float,
        groups: list[str] | None = None,
        duration: float = 1.0,
        stagger: float = 0.4,
    ) -> SceneBuilder:
        """Reveal multiple groups progressively with a fixed stagger."""
        params: dict[str, Any] = {"duration": duration, "stagger": stagger}
        if groups is not None:
            params["groups"] = groups
        self._timeline.append(
            AnimationStep(
                time=time,
                type="cluster_reveal",
                params=params,
            )
        )
        return self

    def add_highlight_edges(
        self,
        source: str | None = None,
        target: str | None = None,
        *,
        time: float,
        color: str = "#ffaa00",
        duration: float = 1.0,
    ) -> SceneBuilder:
        """Highlight edges matching source/target filters."""
        params: dict[str, Any] = {"color": color, "duration": duration}
        if source is not None:
            params["source"] = source
        if target is not None:
            params["target"] = target
        self._timeline.append(
            AnimationStep(time=time, type="highlight_edges", params=params)
        )
        return self

    def add_fade_all(self, *, time: float, opacity: float = 0.3, duration: float = 1.0) -> SceneBuilder:
        self._timeline.append(
            AnimationStep(
                time=time,
                type="fade_all",
                params={"opacity": opacity, "duration": duration},
            )
        )
        return self

    def add_pulse_node(
        self,
        node_id: str,
        *,
        time: float,
        duration: float = 1.0,
        amplitude: float = 0.8,
    ) -> SceneBuilder:
        """Add a pulse effect to a specific node."""
        self._timeline.append(
            AnimationStep(
                time=time,
                type="pulse_node",
                params={
                    "node": node_id,
                    "duration": duration,
                    "amplitude": amplitude,
                },
            )
        )
        return self

    def set_render(self, **kwargs: Any) -> SceneBuilder:
        """Update render settings. Accepts any RenderSettings field."""
        current = self._render_settings.model_dump()
        current.update(kwargs)
        self._render_settings = RenderSettings(**current)
        return self

    def build(self) -> SceneDocument:
        """Validate and return the SceneDocument."""
        return SceneDocument(
            nodes=self._nodes,
            edges=self._edges,
            camera_path=sorted(self._camera_path, key=lambda k: k.time),
            animation_timeline=sorted(self._timeline, key=lambda s: s.time),
            render_settings=self._render_settings,
        )
