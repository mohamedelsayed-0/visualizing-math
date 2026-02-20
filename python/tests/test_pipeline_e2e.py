"""Optional end-to-end pipeline tests (disabled by default).

Enable with:
    MATHVIZ_E2E=1 .venv/bin/pytest -q python/tests/test_pipeline_e2e.py
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from mathviz.scene.builder import SceneBuilder
from mathviz.scene.compiler import compile_scene


pytestmark = pytest.mark.skipif(
    os.getenv("MATHVIZ_E2E") != "1",
    reason="Set MATHVIZ_E2E=1 to run end-to-end render tests",
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _python_exe() -> str:
    root = _project_root()
    venv_python = root / ".venv" / "bin" / "python"
    return str(venv_python) if venv_python.exists() else shutil.which("python3") or "python3"


def _render_tiny_scene(tmp_path: Path, fmt: str, keep_frames: bool = False) -> Path:
    root = _project_root()
    scene = (
        SceneBuilder()
        .add_node("a", (0.0, 0.0, 0.0), group="g1")
        .add_node("b", (10.0, 0.0, 0.0), group="g1")
        .add_edge("a", "b")
        .add_reveal("g1", time=0.0, duration=0.1)
        .set_render(width=640, height=360, fps=5, duration=1.0, dof_enabled=False)
        .build()
    )

    scene_json = tmp_path / "scene.json"
    compile_scene(scene, scene_json)

    out_dir = tmp_path / "out"
    cmd = [
        _python_exe(),
        "-m",
        "mathviz.cli",
        "render",
        str(scene_json),
        "-o",
        str(out_dir),
        "--format",
        fmt,
    ]
    if keep_frames:
        cmd.append("--keep-frames")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "python")

    subprocess.run(cmd, cwd=str(root), check=True, env=env)
    return out_dir


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _can_launch_puppeteer(ts_dir: Path) -> bool:
    check_script = """\
import puppeteer from 'puppeteer';
const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
await browser.close();
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", check_script],
        cwd=str(ts_dir),
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def test_video_pipeline_frame_count(tmp_path: Path) -> None:
    if shutil.which("node") is None or shutil.which("npx") is None:
        pytest.skip("node/npx required for render pipeline")
    ts_dir = _project_root() / "ts"
    if not _can_launch_puppeteer(ts_dir):
        pytest.skip("Puppeteer/Chromium cannot launch in this environment")

    out_dir = _render_tiny_scene(tmp_path, fmt="frames")

    frames = sorted((out_dir / "frames").glob("frame_*.png"))
    assert len(frames) == math.ceil(5 * 1.0)


def test_video_pipeline_mp4_exists(tmp_path: Path) -> None:
    if shutil.which("node") is None or shutil.which("npx") is None:
        pytest.skip("node/npx required for render pipeline")
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg required for mp4 encoding")
    ts_dir = _project_root() / "ts"
    if not _can_launch_puppeteer(ts_dir):
        pytest.skip("Puppeteer/Chromium cannot launch in this environment")

    out_dir = _render_tiny_scene(tmp_path, fmt="mp4", keep_frames=True)

    assert (out_dir / "output.mp4").exists()
    assert (out_dir / "frames").exists()

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-count_packets",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=nb_read_packets",
                "-of",
                "csv=p=0",
                str(out_dir / "output.mp4"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        frame_count = int(result.stdout.strip())
        assert frame_count == math.ceil(5 * 1.0)


def test_interactive_preview_has_no_console_errors(tmp_path: Path) -> None:
    if shutil.which("node") is None or shutil.which("npx") is None:
        pytest.skip("node/npx required for preview test")

    root = _project_root()
    ts_dir = root / "ts"
    if not _can_launch_puppeteer(ts_dir):
        pytest.skip("Puppeteer/Chromium cannot launch in this environment")

    scene = (
        SceneBuilder()
        .add_node("a", (0.0, 0.0, 0.0), group="g1")
        .add_node("b", (1.0, 0.0, 0.0), group="g1")
        .add_edge("a", "b")
        .set_render(duration=1.0, dof_enabled=False)
        .build()
    )
    scene_json = tmp_path / "preview_scene.json"
    compile_scene(scene, scene_json)

    staged_scene = ts_dir / "public" / "scene.json"
    shutil.copy2(scene_json, staged_scene)

    port = "3460"
    vite_proc = subprocess.Popen(
        ["npx", "vite", "--port", port],
        cwd=str(ts_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(3)
        check_script = f"""\
import puppeteer from 'puppeteer';

const errors = [];
const ignoredConsoleSubstrings = ['favicon.ico', 'Failed to load resource'];
const browser = await puppeteer.launch({{
  headless: true,
  args: ['--no-sandbox'],
}});

try {{
  const page = await browser.newPage();
  page.on('console', (msg) => {{
    if (msg.type() !== 'error') return;
    const text = msg.text();
    if (ignoredConsoleSubstrings.some((needle) => text.includes(needle))) return;
    errors.push(text);
  }});
  await page.goto('http://localhost:{port}', {{ waitUntil: 'networkidle0' }});
  await page.waitForFunction('window.__MATHVIZ_MANAGER__', {{ timeout: 30000 }});
  if (errors.length > 0) {{
    console.error(JSON.stringify(errors));
    process.exit(1);
  }}
}} finally {{
  await browser.close();
}}
"""

        subprocess.run(
            ["node", "--input-type=module", "-e", check_script],
            cwd=str(ts_dir),
            check=True,
        )
    finally:
        vite_proc.terminate()
        try:
            vite_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            vite_proc.kill()


def test_visual_regression_frame_zero_snapshot(tmp_path: Path) -> None:
    if shutil.which("node") is None or shutil.which("npx") is None:
        pytest.skip("node/npx required for render pipeline")
    ts_dir = _project_root() / "ts"
    if not _can_launch_puppeteer(ts_dir):
        pytest.skip("Puppeteer/Chromium cannot launch in this environment")

    out_dir = _render_tiny_scene(tmp_path, fmt="frames")
    frame0 = out_dir / "frames" / "frame_000000.png"
    assert frame0.exists()

    snapshot_hash_file = (
        _project_root() / "python" / "tests" / "snapshots" / "tiny_scene_frame0.sha256"
    )
    assert snapshot_hash_file.exists()

    expected_hash = snapshot_hash_file.read_text(encoding="utf-8").strip()
    actual_hash = _sha256(frame0)
    assert actual_hash == expected_hash
