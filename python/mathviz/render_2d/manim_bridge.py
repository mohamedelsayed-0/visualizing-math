"""Manim bridge — converts SceneDocument to Manim Scene for 2D rendering.

This is a thin adapter for v1. Focus is on 3D; this provides basic 2D support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mathviz.scene.models import SceneDocument


def scene_to_manim(doc: SceneDocument) -> str:
    """Generate a Manim Python script from a SceneDocument.

    Returns a string of Python code that can be executed with `manim render`.
    """
    lines = [
        "from manim import *",
        "",
        "class MathVizScene(Scene):",
        "    def construct(self):",
    ]

    # Create dots for nodes
    for node in doc.nodes:
        x, y, _z = node.position
        lines.append(
            f'        dot_{node.id} = Dot(point=[{x}, {y}, 0], '
            f'color="{node.color}", radius=0.05 * {node.size})'
        )

    # Create lines for edges
    for i, edge in enumerate(doc.edges):
        if not edge.visible:
            continue
        lines.append(
            f'        edge_{i} = Line('
            f'dot_{edge.source}.get_center(), '
            f'dot_{edge.target}.get_center(), '
            f'stroke_opacity=0.3, stroke_width=1)'
        )

    # Animate: fade in edges, then nodes
    edge_names = [f"edge_{i}" for i, e in enumerate(doc.edges) if e.visible]
    node_names = [f"dot_{n.id}" for n in doc.nodes]

    if edge_names:
        lines.append(f"        self.play(*[Create({e}) for e in [{', '.join(edge_names)}]])")
    if node_names:
        lines.append(f"        self.play(*[FadeIn({n}) for n in [{', '.join(node_names)}]])")

    lines.append(f"        self.wait({doc.render_settings.duration})")

    return "\n".join(lines)
