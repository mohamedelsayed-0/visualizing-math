# Math_Visualize

Math_Visualize is a hybrid Python + TypeScript toolkit for cinematic graph/point-cloud visualization:

- Python: scene authoring, graph layout, CLI, schema validation
- TypeScript/Three.js: interactive preview, timeline playback, post-processing, frame capture

It is built around a shared Scene JSON format (Pydantic in Python, Zod in TypeScript).

## Features

- Scene model with nodes, edges, camera path, animation timeline, render settings
- Layout algorithms: Fruchterman-Reingold, ForceAtlas2-style spring layout, UMAP
- Effects: bloom, fog, tone mapping, optional DOF (BokehPass)
- Timeline steps: `reveal_group`, `cluster_reveal`, `highlight_edges`, `fade_all`, `set_camera`
- Camera presets: orbit, flythrough, dolly zoom
- Outputs: interactive web preview, PNG frame sequences, MP4 (via ffmpeg)

## Project Structure

- `python/mathviz/`: Python package (`scene`, `layout`, `data`, CLI)
- `python/examples/`: demo scenes
- `python/tests/`: Python tests
- `ts/src/`: Three.js renderer, timeline, capture
- `ts/tests/`: TypeScript tests
- `PLAN.md`: implementation roadmap
- `USAGE.md`: step-by-step custom visualization walkthrough

## Requirements

- Python 3.9+
- Node.js 18+
- `ffmpeg` (optional, required for MP4 encoding)

## Setup

### 1. Python

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
# optional extras
pip install -e .[fa2,umap,manim]
```

### 2. TypeScript renderer

```bash
cd ../ts
npm install
```

## Quick Start

From repository root:

```bash
# Compile demo scene JSON
python -m mathviz.cli compile python/examples/galaxy_flythrough.py -o scene.json

# Preview in browser (interactive)
python -m mathviz.cli preview scene.json --port 3000

# Render offline (frames + MP4)
python -m mathviz.cli render scene.json -o output --format mp4
```

## CLI Commands

- `viz compile <script.py> -o scene.json`
- `viz preview <scene.json> --port 3000`
- `viz render <scene.json> -o output --format mp4|frames --keep-frames`
- `viz layout <graph.csv|graph.json> -o positions.json --algo fruchterman|forceatlas2|umap`

## Demos

- `python/examples/galaxy_flythrough.py`
- `python/examples/cluster_reveal.py`
- `python/examples/embedding_explore.py`

Each example exposes `build_scene()` and can be compiled with `viz compile`.

## Testing

```bash
# Python
cd python
.venv/bin/pytest -q

# TypeScript
cd ../ts
npm test
npm run build
```

Optional end-to-end render tests (uses Node/Puppeteer and ffmpeg):

```bash
cd ..
MATHVIZ_E2E=1 .venv/bin/pytest -q python/tests/test_pipeline_e2e.py
```

## Notes

- Scene schema parity is enforced in both Python (`models.py`) and TS (`scene.ts`).
- Large scenes are best laid out offline in Python, then rendered in TS.
- For custom scene authoring, follow `USAGE.md`.
