"""Pydantic v2 models for the Scene JSON schema.

This is the single source of truth for the scene format.
The TypeScript Zod schema (ts/src/schema/scene.ts) must mirror these types.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class NodeData(BaseModel):
    """A single node/point in the scene."""

    id: str
    position: Tuple[float, float, float]
    color: str = "#ffffff"
    size: float = 1.0
    glow: float = 1.0
    group: Optional[str] = None
    reveal_order: int = 0


class EdgeData(BaseModel):
    """A directed edge between two nodes."""

    source: str
    target: str
    weight: float = 1.0
    color: Optional[str] = None
    visible: bool = True


class CameraKeyframe(BaseModel):
    """A single camera keyframe on the timeline."""

    time: float = Field(ge=0.0, description="Time in seconds")
    position: Tuple[float, float, float]
    target: Tuple[float, float, float]
    fov: float = 60.0
    easing: str = "ease-in-out"


class AnimationStep(BaseModel):
    """A single animation event on the timeline."""

    time: float = Field(ge=0.0, description="Time in seconds")
    type: Literal[
        "reveal_group",
        "cluster_reveal",
        "highlight_edges",
        "set_camera",
        "fade_all",
        "pulse_node",
    ]
    params: Dict[str, Any] = Field(default_factory=dict)


class RenderSettings(BaseModel):
    """Global render configuration."""

    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = 10.0
    background: str = "#000011"
    # Bloom
    bloom_strength: float = 1.5
    bloom_radius: float = 0.4
    bloom_threshold: float = 0.2
    # Fog
    fog_near: float = 50.0
    fog_far: float = 500.0
    # Tone mapping
    tone_mapping: Literal["ACESFilmic", "Linear", "Reinhard", "Cineon"] = "ACESFilmic"
    # DOF
    dof_enabled: bool = True
    dof_focus_distance: float = 100.0
    dof_aperture: float = 0.025


class SceneDocument(BaseModel):
    """Root scene document — the complete scene definition."""

    version: str = "1.0"
    nodes: List[NodeData]
    edges: List[EdgeData] = Field(default_factory=list)
    camera_path: List[CameraKeyframe] = Field(default_factory=list)
    animation_timeline: List[AnimationStep] = Field(default_factory=list)
    render_settings: RenderSettings = Field(default_factory=RenderSettings)
