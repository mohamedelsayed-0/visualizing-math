/**
 * CameraController — Keyframe interpolation with cubic Hermite splines + presets.
 */

import * as THREE from "three";
import type { CameraKeyframe } from "@/schema/scene";

// ── Easing functions ─────────────────────────────────────────────────────────

type EasingFn = (t: number) => number;

const EASINGS: Record<string, EasingFn> = {
  linear: (t) => t,
  "ease-in": (t) => t * t,
  "ease-out": (t) => t * (2 - t),
  "ease-in-out": (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
};

function getEasing(name: string): EasingFn {
  return EASINGS[name] ?? EASINGS["ease-in-out"];
}

type Vec3 = [number, number, number];

function hermite(p0: Vec3, p1: Vec3, m0: Vec3, m1: Vec3, t: number): Vec3 {
  const t2 = t * t;
  const t3 = t2 * t;
  const h00 = 2 * t3 - 3 * t2 + 1;
  const h10 = t3 - 2 * t2 + t;
  const h01 = -2 * t3 + 3 * t2;
  const h11 = t3 - t2;

  return [
    h00 * p0[0] + h10 * m0[0] + h01 * p1[0] + h11 * m1[0],
    h00 * p0[1] + h10 * m0[1] + h01 * p1[1] + h11 * m1[1],
    h00 * p0[2] + h10 * m0[2] + h01 * p1[2] + h11 * m1[2],
  ];
}

function vecDiff(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}

function vecScale(v: Vec3, s: number): Vec3 {
  return [v[0] * s, v[1] * s, v[2] * s];
}

// ── CameraController ─────────────────────────────────────────────────────────

export class CameraController {
  private _keyframes: CameraKeyframe[];
  private _camera: THREE.PerspectiveCamera;

  constructor(camera: THREE.PerspectiveCamera, keyframes: CameraKeyframe[]) {
    this._camera = camera;
    this._keyframes = [...keyframes].sort((a, b) => a.time - b.time);
  }

  /** Update camera position/target/fov based on current time. */
  update(time: number): void {
    if (this._keyframes.length === 0) return;

    // Before first keyframe
    if (time <= this._keyframes[0].time) {
      this._applyKeyframe(this._keyframes[0]);
      return;
    }

    // After last keyframe
    const last = this._keyframes[this._keyframes.length - 1];
    if (time >= last.time) {
      this._applyKeyframe(last);
      return;
    }

    // Find surrounding keyframes
    let i = 0;
    while (i < this._keyframes.length - 1 && this._keyframes[i + 1].time <= time) {
      i++;
    }

    const kf0 = this._keyframes[i];
    const kf1 = this._keyframes[i + 1];
    const segmentDuration = kf1.time - kf0.time;
    const rawT = (time - kf0.time) / segmentDuration;
    const t = getEasing(kf1.easing)(rawT);

    const p0 = kf0.position as Vec3;
    const p1 = kf1.position as Vec3;
    const c0 = kf0.target as Vec3;
    const c1 = kf1.target as Vec3;

    const m0 = this._tangentFor(i, "position");
    const m1 = this._tangentFor(i + 1, "position");
    const c0t = this._tangentFor(i, "target");
    const c1t = this._tangentFor(i + 1, "target");

    // Cubic Hermite interpolation gives smoother flythroughs than linear lerp.
    const camPos = hermite(p0, p1, m0, m1, t);
    const camTarget = hermite(c0, c1, c0t, c1t, t);

    this._camera.position.set(camPos[0], camPos[1], camPos[2]);
    this._camera.lookAt(new THREE.Vector3(camTarget[0], camTarget[1], camTarget[2]));

    // Lerp FOV
    this._camera.fov = THREE.MathUtils.lerp(kf0.fov, kf1.fov, t);
    this._camera.updateProjectionMatrix();
  }

  private _applyKeyframe(kf: CameraKeyframe): void {
    this._camera.position.set(...kf.position);
    this._camera.lookAt(new THREE.Vector3(...kf.target));
    this._camera.fov = kf.fov;
    this._camera.updateProjectionMatrix();
  }

  private _tangentFor(index: number, field: "position" | "target"): Vec3 {
    const curr = this._keyframes[index][field] as Vec3;
    const prev =
      (this._keyframes[index - 1]?.[field] as Vec3 | undefined) ?? curr;
    const next =
      (this._keyframes[index + 1]?.[field] as Vec3 | undefined) ?? curr;

    if (index === 0) {
      return vecDiff(next, curr);
    }
    if (index === this._keyframes.length - 1) {
      return vecDiff(curr, prev);
    }
    return vecScale(vecDiff(next, prev), 0.5);
  }
}

// ── Camera Presets ───────────────────────────────────────────────────────────

/** Generate orbit keyframes around a center point. */
export function orbitPreset(
  center: [number, number, number],
  radius: number,
  duration: number,
  steps: number = 60
): CameraKeyframe[] {
  const keyframes: CameraKeyframe[] = [];
  for (let i = 0; i <= steps; i++) {
    const angle = (i / steps) * Math.PI * 2;
    const time = (i / steps) * duration;
    keyframes.push({
      time,
      position: [
        center[0] + Math.cos(angle) * radius,
        center[1] + radius * 0.3,
        center[2] + Math.sin(angle) * radius,
      ],
      target: center,
      fov: 60,
      easing: "linear",
    });
  }
  return keyframes;
}

/** Generate flythrough keyframes through a series of waypoints. */
export function flythroughPreset(
  waypoints: [number, number, number][],
  target: [number, number, number],
  duration: number
): CameraKeyframe[] {
  return waypoints.map((pos, i) => ({
    time: (i / (waypoints.length - 1)) * duration,
    position: pos,
    target,
    fov: 60,
    easing: "ease-in-out",
  }));
}

/**
 * Generate a dolly-zoom (Vertigo effect): camera moves while FOV compensates
 * to keep the target's apparent size roughly constant.
 */
export function dollyZoomPreset(
  start: [number, number, number],
  end: [number, number, number],
  target: [number, number, number],
  duration: number,
  steps: number = 60,
  startFov: number = 60
): CameraKeyframe[] {
  const targetV = new THREE.Vector3(...target);
  const startV = new THREE.Vector3(...start);
  const startDistance = startV.distanceTo(targetV);
  const framingConstant =
    Math.tan(THREE.MathUtils.degToRad(startFov) / 2) * startDistance;

  const keyframes: CameraKeyframe[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const pos: Vec3 = [
      THREE.MathUtils.lerp(start[0], end[0], t),
      THREE.MathUtils.lerp(start[1], end[1], t),
      THREE.MathUtils.lerp(start[2], end[2], t),
    ];

    const d = new THREE.Vector3(...pos).distanceTo(targetV);
    const fovRad = 2 * Math.atan(framingConstant / Math.max(1e-6, d));
    const fov = THREE.MathUtils.clamp(THREE.MathUtils.radToDeg(fovRad), 20, 110);

    keyframes.push({
      time: t * duration,
      position: pos,
      target,
      fov,
      easing: "linear",
    });
  }

  return keyframes;
}
