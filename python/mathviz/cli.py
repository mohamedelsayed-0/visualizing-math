"""CLI entry point for mathviz: viz compile/preview/render/layout."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import click


@click.group()
def cli() -> None:
    """mathviz — Cinematic graph & point cloud visualization toolkit."""
    pass


@cli.command()
@click.argument("script", type=click.Path(exists=True))
@click.option("-o", "--output", default="scene.json", help="Output scene JSON path.")
def compile(script: str, output: str) -> None:
    """Compile a Python scene script to Scene JSON.

    The script must define a `build_scene()` function that returns a SceneDocument.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("user_scene", script)
    if spec is None or spec.loader is None:
        click.secho(f"Error: cannot load {script}", fg="red", err=True)
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "build_scene"):
        click.secho(
            f"Error: {script} must define a build_scene() function",
            fg="red",
            err=True,
        )
        sys.exit(1)

    scene = module.build_scene()

    from mathviz.scene.compiler import compile_scene

    compile_scene(scene, output)
    click.secho(f"Compiled scene to {output}", fg="green")


@cli.command()
@click.argument("scene_json", type=click.Path(exists=True))
@click.option("--port", default=3000, help="Dev server port.")
def preview(scene_json: str, port: int) -> None:
    """Launch interactive preview of a scene JSON file."""
    _require_command("npx")
    _require_command("node")
    ts_dir = _find_ts_dir()

    dest = _stage_scene_for_preview(ts_dir, scene_json)
    click.echo(f"Staged {scene_json} -> {dest}")

    # Launch vite dev server
    click.echo(f"Starting preview server on http://localhost:{port}")
    subprocess.run(
        ["npx", "vite", "--port", str(port)],
        cwd=str(ts_dir),
        check=True,
    )


@cli.command()
@click.argument("scene_json", type=click.Path(exists=True))
@click.option("-o", "--output", default="output", help="Output directory.")
@click.option("--format", "fmt", type=click.Choice(["mp4", "frames"]), default="mp4")
@click.option("--keep-frames", is_flag=True, help="Keep PNG frames after MP4 encoding.")
def render(scene_json: str, output: str, fmt: str, keep_frames: bool) -> None:
    """Render a scene to video (MP4) or PNG frame sequence."""
    _require_command("npx")
    _require_command("node")
    from mathviz.scene.compiler import load_scene

    scene = load_scene(scene_json)
    s = scene.render_settings

    output_dir = Path(output).resolve()
    frames_dir = output_dir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    ts_dir = _find_ts_dir()

    dest = _stage_scene_for_preview(ts_dir, scene_json)
    click.echo(f"Staged {scene_json} -> {dest}")

    # Start vite in the background
    click.echo("Starting Vite dev server...")
    vite_proc = subprocess.Popen(
        ["npx", "vite", "--port", "3456"],
        cwd=str(ts_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        import time
        time.sleep(3)  # Wait for vite to start

        # Run headless capture via Node
        frame_count = math.ceil(s.fps * s.duration)
        click.echo(f"Capturing {frame_count} frames at {s.fps}fps...")
        _capture_frames_with_headless_module(
            ts_dir=ts_dir,
            output_dir=frames_dir,
            width=s.width,
            height=s.height,
            fps=s.fps,
            duration=s.duration,
            vite_url="http://localhost:3456",
        )

        if fmt == "mp4":
            _encode_mp4(frames_dir, output_dir / "output.mp4", s.fps)
            if not keep_frames:
                shutil.rmtree(frames_dir)
            click.secho(f"Video saved to {output_dir / 'output.mp4'}", fg="green")
        else:
            click.secho(f"Frames saved to {frames_dir}", fg="green")

    finally:
        vite_proc.terminate()
        vite_proc.wait()


@cli.command()
@click.argument("graph_path", type=click.Path(exists=True))
@click.option("-o", "--output", default="positions.json", help="Output positions file.")
@click.option(
    "--algo",
    type=click.Choice(["forceatlas2", "fruchterman", "umap"]),
    default="fruchterman",
    help="Layout algorithm.",
)
@click.option("--iterations", default=100, help="Layout iterations.")
@click.option("--seed", default=42, help="Random seed.")
@click.option("--dim", default=3, help="Output dimensions (2 or 3).")
def layout(
    graph_path: str, output: str, algo: str, iterations: int, seed: int, dim: int
) -> None:
    """Compute layout positions for a graph file."""
    from mathviz.data.loaders import (
        from_edge_list,
        from_json_edge_list,
        from_networkx_pickle,
    )

    path = Path(graph_path)
    if path.suffix == ".json":
        G = from_json_edge_list(path)
    elif path.suffix in {".gpickle", ".pickle", ".pkl"}:
        G = from_networkx_pickle(path)
    else:
        G = from_edge_list(path)

    click.echo(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    click.echo(f"Computing {algo} layout (dim={dim}, iter={iterations})...")

    if algo == "forceatlas2":
        from mathviz.layout.force_atlas2 import layout_forceatlas2
        positions = layout_forceatlas2(G, iterations=iterations, dim=dim, seed=seed)
    elif algo == "fruchterman":
        from mathviz.layout.fruchterman import layout_fruchterman_reingold
        positions = layout_fruchterman_reingold(
            G, iterations=iterations, dim=dim, seed=seed
        )
    elif algo == "umap":
        from mathviz.layout.umap_layout import layout_umap
        positions = layout_umap(G, n_components=dim, seed=seed)
    else:
        click.echo(f"Unknown algorithm: {algo}", err=True)
        sys.exit(1)

    # Save as JSON: {node_id: [x, y, z]}
    node_list = list(G.nodes())
    pos_dict: dict[str, list[float]] = {}
    with click.progressbar(node_list, label="Serializing layout positions") as bar:
        for i, node in enumerate(bar):
            pos_dict[str(node)] = positions[i].tolist()

    Path(output).write_text(json.dumps(pos_dict, indent=2), encoding="utf-8")
    click.secho(f"Positions saved to {output}", fg="green")


def _require_command(name: str) -> str:
    """Ensure a CLI command exists and return its path."""
    path = shutil.which(name)
    if not path:
        click.secho(f"Error: required command '{name}' not found in PATH", fg="red", err=True)
        sys.exit(1)
    return path


def _find_ts_dir() -> Path:
    """Find the ts/ directory relative to the project."""
    # Walk up from this file to find the project root
    current = Path(__file__).resolve().parent
    while current != current.parent:
        ts_dir = current / "ts"
        if ts_dir.exists():
            return ts_dir
        # Also check parent (we might be in python/mathviz/)
        ts_dir = current.parent / "ts"
        if ts_dir.exists():
            return ts_dir
        current = current.parent

    # Fallback: relative to cwd
    ts_dir = Path.cwd() / "ts"
    if ts_dir.exists():
        return ts_dir

    click.echo("Error: Cannot find ts/ directory", err=True)
    sys.exit(1)


def _run_ts_function(
    ts_dir: Path,
    module_relpath: str,
    export_name: str,
    args: list[object],
    *,
    capture_stdout: bool = False,
    emit_result: bool = True,
) -> str:
    """Transpile and execute a TS module export with Node + esbuild."""
    tmp_dir = ts_dir / ".mathviz_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    out_module = tmp_dir / f"{Path(module_relpath).stem}.mjs"
    subprocess.run(
        [
            "npx",
            "esbuild",
            module_relpath,
            "--platform=node",
            "--format=esm",
            "--target=es2020",
            "--log-level=error",
            f"--outfile={out_module}",
        ],
        cwd=str(ts_dir),
        check=True,
        stdout=subprocess.DEVNULL,
    )

    runner = f"""\
import {{ pathToFileURL }} from 'node:url';

const modulePath = {json.dumps(str(out_module))};
const mod = await import(pathToFileURL(modulePath).href);
const fn = mod[{json.dumps(export_name)}];
if (typeof fn !== 'function') {{
  throw new Error(`Export {export_name} is not a function in ${{modulePath}}`);
}}
const result = await fn(...{json.dumps(args)});
if ({'true' if emit_result else 'false'} && result !== undefined) {{
  console.log(JSON.stringify(result));
}}
"""

    proc = subprocess.run(
        ["node", "--input-type=module", "-e", runner],
        cwd=str(ts_dir),
        check=True,
        text=True,
        capture_output=capture_stdout,
    )
    return proc.stdout.strip() if capture_stdout else ""


def _stage_scene_for_preview(ts_dir: Path, scene_json: str) -> Path:
    """Stage a scene for preview using ts/src/preview/server.ts helper."""
    try:
        stdout = _run_ts_function(
            ts_dir,
            "src/preview/server.ts",
            "stageSceneForPreview",
            [str(Path(scene_json).resolve())],
            capture_stdout=True,
        )
        if stdout:
            last_line = stdout.splitlines()[-1].strip()
            if last_line:
                try:
                    staged = json.loads(last_line)
                    return Path(staged)
                except json.JSONDecodeError:
                    return Path(last_line)
    except Exception:
        pass

    # Fallback staging path if TS helper cannot run.
    dest = ts_dir / "public" / "scene.json"
    shutil.copy2(scene_json, dest)
    return dest


def _capture_frames_with_headless_module(
    *,
    ts_dir: Path,
    output_dir: Path,
    width: int,
    height: int,
    fps: int,
    duration: float,
    vite_url: str,
) -> None:
    """Capture frames via ts/src/capture/headless.ts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    _run_ts_function(
        ts_dir,
        "src/capture/headless.ts",
        "captureFrames",
        [
            {
                "sceneJsonPath": "scene.json",
                "outputDir": str(output_dir),
                "width": int(width),
                "height": int(height),
                "fps": int(fps),
                "duration": float(duration),
                "viteUrl": vite_url,
            }
        ],
        emit_result=False,
        capture_stdout=False,
    )


def _encode_mp4(frames_dir: Path, output_path: Path, fps: int) -> None:
    """Encode PNG frames to MP4 using ffmpeg."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        click.echo("Warning: ffmpeg not found. Frames saved but MP4 not created.", err=True)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pattern = str(frames_dir / "frame_%06d.png")

    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate", str(fps),
            "-i", pattern,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(output_path),
        ],
        check=True,
    )


if __name__ == "__main__":
    cli()
