/**
 * PostProcessing — EffectComposer pipeline with bloom, fog, DOF, and tone mapping.
 */

import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { BokehPass } from "three/examples/jsm/postprocessing/BokehPass.js";
import { OutputPass } from "three/examples/jsm/postprocessing/OutputPass.js";
import type { RenderSettings } from "@/schema/scene";

const TONE_MAP: Record<string, THREE.ToneMapping> = {
  ACESFilmic: THREE.ACESFilmicToneMapping,
  Linear: THREE.LinearToneMapping,
  Reinhard: THREE.ReinhardToneMapping,
  Cineon: THREE.CineonToneMapping,
};

export class PostProcessingPipeline {
  readonly composer: EffectComposer;

  private _bloomPass: UnrealBloomPass;
  private _bokehPass: BokehPass | null = null;
  private _renderer: THREE.WebGLRenderer;

  constructor(
    renderer: THREE.WebGLRenderer,
    scene: THREE.Scene,
    camera: THREE.PerspectiveCamera,
    settings: RenderSettings
  ) {
    this._renderer = renderer;

    // Tone mapping
    renderer.toneMapping =
      TONE_MAP[settings.tone_mapping] ?? THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;

    // Fog
    scene.fog = new THREE.Fog(
      settings.background,
      settings.fog_near,
      settings.fog_far
    );

    // Composer — match the renderer's pixel ratio for Retina/HiDPI sharpness
    this.composer = new EffectComposer(renderer);
    this.composer.setPixelRatio(renderer.getPixelRatio());

    // 1. Render pass
    this.composer.addPass(new RenderPass(scene, camera));

    // 2. Bloom
    const size = renderer.getSize(new THREE.Vector2());
    this._bloomPass = new UnrealBloomPass(
      size,
      settings.bloom_strength,
      settings.bloom_radius,
      settings.bloom_threshold
    );
    this.composer.addPass(this._bloomPass);

    // 3. DOF (optional)
    if (settings.dof_enabled) {
      this._bokehPass = new BokehPass(scene, camera, {
        focus: settings.dof_focus_distance,
        aperture: settings.dof_aperture,
        maxblur: 0.005,
      });
      this.composer.addPass(this._bokehPass);
    }

    // 4. Output pass (applies tone mapping + color space conversion)
    this.composer.addPass(new OutputPass());
  }

  render(): void {
    this.composer.render();
  }

  setSize(width: number, height: number): void {
    this.composer.setSize(width, height);
    this._bloomPass.resolution.set(width, height);
  }

  dispose(): void {
    this.composer.dispose();
  }
}
