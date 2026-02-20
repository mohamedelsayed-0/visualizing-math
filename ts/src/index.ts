/**
 * mathviz-renderer — Entry point for the interactive preview.
 *
 * Loads scene.json from the URL or from a global variable,
 * then initializes the SceneManager and starts the preview loop.
 */

import { SceneManager } from "@/renderer/SceneManager";

async function main(): Promise<void> {
  // Try to load scene data from global (injected by preview server)
  // or fetch from scene.json in the same directory
  let sceneData: unknown;

  if ((window as any).__MATHVIZ_SCENE__) {
    sceneData = (window as any).__MATHVIZ_SCENE__;
  } else {
    const params = new URLSearchParams(window.location.search);
    const scenePath = params.get("scene") ?? "scene.json";
    const resp = await fetch(scenePath);
    if (!resp.ok) {
      document.body.innerHTML = `<p style="color:#ff4444;font-family:monospace;padding:2em">Failed to load ${scenePath}: ${resp.status}</p>`;
      return;
    }
    sceneData = await resp.json();
  }

  const canvas = document.getElementById("viz-canvas") as HTMLCanvasElement;
  if (!canvas) {
    document.body.innerHTML = `<p style="color:#ff4444;font-family:monospace;padding:2em">No canvas element found</p>`;
    return;
  }

  const manager = SceneManager.fromJSON(sceneData, canvas);

  // Resize to fill the window
  const resize = () => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    const dpr = window.devicePixelRatio ?? 1;
    const previewRatio = Math.min(Math.max(dpr, 1.25), 2.5);
    manager.renderer.setPixelRatio(previewRatio);
    manager.camera.aspect = w / h;
    manager.camera.updateProjectionMatrix();
    manager.renderer.setSize(w, h);
    manager.resizePostProcessing(w, h);
  };
  resize(); // initial fit

  manager.startPreview();

  // Space toggles pause/resume on the normal preview page without UI controls.
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.code !== "Space") return;

    const target = event.target as HTMLElement | null;
    const tag = target?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA") return;

    event.preventDefault();
    manager.togglePreviewPause();
  };
  window.addEventListener("keydown", onKeyDown);

  // Expose for headless frame capture
  (window as any).__MATHVIZ_MANAGER__ = manager;

  window.addEventListener("resize", resize);
}

main().catch(console.error);
