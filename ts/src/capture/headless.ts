/**
 * Headless frame capture using Puppeteer.
 *
 * Launches a headless Chromium, loads the Three.js scene, and captures
 * frames at exact timeline positions for deterministic video output.
 */

import puppeteer from "puppeteer";
import { writeFileSync, mkdirSync, existsSync } from "fs";
import { resolve } from "path";

export interface CaptureOptions {
  sceneJsonPath: string;
  outputDir: string;
  width: number;
  height: number;
  fps: number;
  duration: number;
  viteUrl?: string;
}

export function computeTotalFrames(fps: number, duration: number): number {
  return Math.ceil(fps * duration);
}

/**
 * Capture all frames of a scene to PNG files.
 * Returns the list of frame file paths.
 */
export async function captureFrames(opts: CaptureOptions): Promise<string[]> {
  const {
    sceneJsonPath,
    outputDir,
    width,
    height,
    fps,
    duration,
    viteUrl = "http://localhost:3000",
  } = opts;

  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  const totalFrames = computeTotalFrames(fps, duration);
  const framePaths: string[] = [];

  const browser = await puppeteer.launch({
    headless: true,
    args: [`--window-size=${width},${height}`, "--no-sandbox"],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 1 });

    // Load the preview page with the scene
    const url = `${viteUrl}?scene=${encodeURIComponent(sceneJsonPath)}`;
    await page.goto(url, { waitUntil: "networkidle0" });

    // Wait for the manager to be available
    await page.waitForFunction("window.__MATHVIZ_MANAGER__", {
      timeout: 30000,
    });

    // Stop the preview loop so we control frame timing
    await page.evaluate(() => {
      (window as any).__MATHVIZ_MANAGER__.stopPreview();
    });

    // Capture each frame
    for (let frame = 0; frame < totalFrames; frame++) {
      const time = frame / fps;
      const paddedFrame = String(frame).padStart(6, "0");
      const framePath = resolve(outputDir, `frame_${paddedFrame}.png`);

      // Render the exact frame
      await page.evaluate((t: number) => {
        (window as any).__MATHVIZ_MANAGER__.renderFrame(t);
      }, time);

      // Screenshot the canvas
      const canvasHandle = await page.$("#viz-canvas");
      if (canvasHandle) {
        const screenshot = await canvasHandle.screenshot({ type: "png" });
        writeFileSync(framePath, screenshot);
        framePaths.push(framePath);
      }

      // Progress logging
      if (frame % fps === 0) {
        const sec = Math.floor(frame / fps);
        console.log(
          `Captured frame ${frame}/${totalFrames} (${sec}s / ${duration}s)`
        );
      }
    }
  } finally {
    await browser.close();
  }

  return framePaths;
}
