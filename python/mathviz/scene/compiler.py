"""Scene compilation: validate and serialize SceneDocument to JSON."""

from __future__ import annotations

import json
from pathlib import Path

from mathviz.scene.models import SceneDocument


def compile_scene(scene: SceneDocument, output: str | Path | None = None) -> str:
    """Validate and serialize a SceneDocument to JSON.

    Args:
        scene: A validated SceneDocument instance.
        output: Optional file path to write the JSON to.

    Returns:
        The JSON string.
    """
    json_str = scene.model_dump_json(indent=2)

    if output is not None:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json_str, encoding="utf-8")

    return json_str


def load_scene(path: str | Path) -> SceneDocument:
    """Load and validate a SceneDocument from a JSON file."""
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    return SceneDocument.model_validate(data)
