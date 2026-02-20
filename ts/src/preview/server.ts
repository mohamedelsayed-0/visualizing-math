/**
 * Preview server utilities.
 *
 * The preview is served by Vite's dev server. This module provides helpers
 * for the CLI to copy scene.json into the public dir and launch vite.
 */

import { existsSync, copyFileSync, mkdirSync } from "fs";
import { resolve, dirname } from "path";

/**
 * Copy a scene.json file into the ts/public directory so Vite can serve it.
 */
export function stageSceneForPreview(sceneJsonPath: string): string {
  const cwdRoot = process.cwd();
  const tsRoot = existsSync(resolve(cwdRoot, "public"))
    ? cwdRoot
    : resolve(dirname(new URL(import.meta.url).pathname), "../..");
  const publicDir = resolve(tsRoot, "public");

  if (!existsSync(publicDir)) {
    mkdirSync(publicDir, { recursive: true });
  }

  const dest = resolve(publicDir, "scene.json");
  copyFileSync(sceneJsonPath, dest);
  return dest;
}
