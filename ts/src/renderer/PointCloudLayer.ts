import * as THREE from "three";
import type { NodeData } from "@/schema/scene";

const vertexShader = /* glsl */ `
  attribute vec3 offset;
  attribute vec3 instanceColor;
  attribute float instanceSize;
  attribute float instanceGlow;
  attribute float revealProgress;

  varying vec3 vColor;
  varying float vGlow;
  varying float vReveal;
  varying vec2 vUv;

  void main() {
    vColor = instanceColor;
    vGlow = instanceGlow;
    vReveal = revealProgress;
    vUv = uv;
    float s = instanceSize * revealProgress;
    vec3 mvPosition = (modelViewMatrix * vec4(offset, 1.0)).xyz;
    mvPosition.xy += position.xy * s;

    gl_Position = projectionMatrix * vec4(mvPosition, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  varying vec3 vColor;
  varying float vGlow;
  varying float vReveal;
  varying vec2 vUv;

  void main() {
    if (vReveal < 0.01) discard;

    vec2 centered = vUv * 2.0 - 1.0;
    float dist = length(centered);
    if (dist > 1.0) discard;
    float circleMask = 1.0 - smoothstep(0.90, 1.00, dist);
    float core = 1.0 - smoothstep(0.0, 0.62, dist);
    float halo = exp(-dist * dist * 5.0) * 0.72;
    float pulse = max(1.0, vReveal);
    float glowBoost = max(0.0, vGlow);
    float baseIntensity = core * 0.96 + halo * 0.08;
    float glowIntensity = halo * glowBoost * 1.18 * mix(1.0, pulse, 0.72);
    float intensity = (baseIntensity + glowIntensity) * 0.86 * circleMask;
    float alpha =
      (core * 0.82 + halo * (0.10 + glowBoost * 0.48) * mix(1.0, pulse, 0.30))
      * min(vReveal, 1.16)
      * circleMask;
    gl_FragColor = vec4(vColor * intensity, alpha);
  }
`;

export class PointCloudLayer {
  readonly mesh: THREE.Mesh;

  private _offsetAttr: THREE.InstancedBufferAttribute;
  private _colorAttr: THREE.InstancedBufferAttribute;
  private _sizeAttr: THREE.InstancedBufferAttribute;
  private _glowAttr: THREE.InstancedBufferAttribute;
  private _revealAttr: THREE.InstancedBufferAttribute;
  private _count: number;

  constructor(nodes: NodeData[], maxCount?: number) {
    this._count = nodes.length;
    const max = maxCount ?? nodes.length;

    const baseGeo = new THREE.PlaneGeometry(1, 1);
    const geo = new THREE.InstancedBufferGeometry();
    geo.index = baseGeo.index;
    geo.attributes.position = baseGeo.attributes.position;
    geo.attributes.uv = baseGeo.attributes.uv;

    const offsets = new Float32Array(max * 3);
    const colors = new Float32Array(max * 3);
    const sizes = new Float32Array(max);
    const glows = new Float32Array(max);
    const reveals = new Float32Array(max);

    const tmpColor = new THREE.Color();

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      offsets[i * 3] = n.position[0];
      offsets[i * 3 + 1] = n.position[1];
      offsets[i * 3 + 2] = n.position[2];

      tmpColor.set(n.color);
      colors[i * 3] = tmpColor.r;
      colors[i * 3 + 1] = tmpColor.g;
      colors[i * 3 + 2] = tmpColor.b;

      sizes[i] = n.size;
      glows[i] = n.glow ?? 1.0;
      reveals[i] = 1.0;
    }

    this._offsetAttr = new THREE.InstancedBufferAttribute(offsets, 3);
    this._colorAttr = new THREE.InstancedBufferAttribute(colors, 3);
    this._sizeAttr = new THREE.InstancedBufferAttribute(sizes, 1);
    this._glowAttr = new THREE.InstancedBufferAttribute(glows, 1);
    this._revealAttr = new THREE.InstancedBufferAttribute(reveals, 1);

    geo.setAttribute("offset", this._offsetAttr);
    geo.setAttribute("instanceColor", this._colorAttr);
    geo.setAttribute("instanceSize", this._sizeAttr);
    geo.setAttribute("instanceGlow", this._glowAttr);
    geo.setAttribute("revealProgress", this._revealAttr);
    geo.instanceCount = this._count;

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    this.mesh = new THREE.Mesh(geo, material);
    this.mesh.frustumCulled = false;
  }

  setRevealRange(startIndex: number, count: number, progress: number): void {
    const arr = this._revealAttr.array as Float32Array;
    for (let i = startIndex; i < startIndex + count && i < this._count; i++) {
      arr[i] = progress;
    }
    this._revealAttr.needsUpdate = true;
  }

  setRevealByGroup(
    nodes: NodeData[],
    group: string,
    progress: number
  ): void {
    const arr = this._revealAttr.array as Float32Array;
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].group === group) {
        arr[i] = progress;
      }
    }
    this._revealAttr.needsUpdate = true;
  }

  hideAll(): void {
    (this._revealAttr.array as Float32Array).fill(0);
    this._revealAttr.needsUpdate = true;
  }

  showAll(): void {
    (this._revealAttr.array as Float32Array).fill(1);
    this._revealAttr.needsUpdate = true;
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.ShaderMaterial).dispose();
  }
}
