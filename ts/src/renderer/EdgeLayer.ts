/**
 * EdgeLayer — GPU-instanced line segments for graph edges.
 *
 * Uses InstancedBufferGeometry with a 2-vertex line base.
 * Only renders visible edges. Supports opacity-based LOD at high edge counts.
 */

import * as THREE from "three";
import type { EdgeData, NodeData } from "@/schema/scene";

const vertexShader = /* glsl */ `
  attribute vec3 startPos;
  attribute vec3 endPos;
  attribute vec3 instanceColor;
  attribute float instanceOpacity;

  varying vec3 vColor;
  varying float vOpacity;

  void main() {
    vColor = instanceColor;
    vOpacity = instanceOpacity;

    // position.x is 0.0 for start vertex, 1.0 for end vertex
    vec3 pos = mix(startPos, endPos, position.x);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  varying vec3 vColor;
  varying float vOpacity;

  void main() {
    if (vOpacity < 0.01) discard;
    gl_FragColor = vec4(vColor, vOpacity);
  }
`;

export class EdgeLayer {
  readonly mesh: THREE.LineSegments;

  private _startAttr: THREE.InstancedBufferAttribute;
  private _endAttr: THREE.InstancedBufferAttribute;
  private _colorAttr: THREE.InstancedBufferAttribute;
  private _opacityAttr: THREE.InstancedBufferAttribute;
  private _edgeCount: number;
  private _baseColors: Float32Array;
  private _baseOpacities: Float32Array;

  constructor(edges: EdgeData[], nodes: NodeData[]) {
    // Build node position lookup
    const posMap = new Map<string, [number, number, number]>();
    for (const n of nodes) {
      posMap.set(n.id, n.position);
    }

    // Filter to visible edges only
    const visibleEdges = edges.filter((e) => e.visible);
    this._edgeCount = visibleEdges.length;

    // Base geometry: a line from 0 to 1 on x-axis
    const baseGeo = new THREE.BufferGeometry();
    baseGeo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute([0, 0, 0, 1, 0, 0], 3)
    );

    const geo = new THREE.InstancedBufferGeometry();
    geo.setAttribute("position", baseGeo.attributes.position);

    const starts = new Float32Array(this._edgeCount * 3);
    const ends = new Float32Array(this._edgeCount * 3);
    const colors = new Float32Array(this._edgeCount * 3);
    const opacities = new Float32Array(this._edgeCount);

    const tmpColor = new THREE.Color();

    for (let i = 0; i < visibleEdges.length; i++) {
      const e = visibleEdges[i];
      const sp = posMap.get(e.source);
      const ep = posMap.get(e.target);
      if (!sp || !ep) continue;

      starts[i * 3] = sp[0];
      starts[i * 3 + 1] = sp[1];
      starts[i * 3 + 2] = sp[2];

      ends[i * 3] = ep[0];
      ends[i * 3 + 1] = ep[1];
      ends[i * 3 + 2] = ep[2];

      tmpColor.set(e.color ?? "#444466");
      colors[i * 3] = tmpColor.r;
      colors[i * 3 + 1] = tmpColor.g;
      colors[i * 3 + 2] = tmpColor.b;

      opacities[i] = 0.3; // default subtle opacity
    }

    this._startAttr = new THREE.InstancedBufferAttribute(starts, 3);
    this._endAttr = new THREE.InstancedBufferAttribute(ends, 3);
    this._colorAttr = new THREE.InstancedBufferAttribute(colors, 3);
    this._opacityAttr = new THREE.InstancedBufferAttribute(opacities, 1);
    this._baseColors = colors.slice();
    this._baseOpacities = opacities.slice();

    geo.setAttribute("startPos", this._startAttr);
    geo.setAttribute("endPos", this._endAttr);
    geo.setAttribute("instanceColor", this._colorAttr);
    geo.setAttribute("instanceOpacity", this._opacityAttr);
    geo.instanceCount = this._edgeCount;

    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: THREE.NormalBlending,
    });

    this.mesh = new THREE.LineSegments(geo, material);
    this.mesh.frustumCulled = false;
  }

  /** Restore edge colors/opacities to their initial values. */
  resetStyles(): void {
    const colorArr = this._colorAttr.array as Float32Array;
    const opacityArr = this._opacityAttr.array as Float32Array;

    colorArr.set(this._baseColors);
    opacityArr.set(this._baseOpacities);

    this._colorAttr.needsUpdate = true;
    this._opacityAttr.needsUpdate = true;
  }

  /** Highlight edges matching a filter by setting their color and opacity. */
  highlightEdges(
    edges: EdgeData[],
    filter: { source?: string; target?: string },
    color: string,
    opacity: number
  ): void {
    const tmpColor = new THREE.Color(color);
    const colorArr = this._colorAttr.array as Float32Array;
    const opacityArr = this._opacityAttr.array as Float32Array;

    let idx = 0;
    for (const e of edges) {
      if (!e.visible) continue;
      const matchSource = !filter.source || e.source === filter.source;
      const matchTarget = !filter.target || e.target === filter.target;
      if (matchSource && matchTarget) {
        colorArr[idx * 3] = tmpColor.r;
        colorArr[idx * 3 + 1] = tmpColor.g;
        colorArr[idx * 3 + 2] = tmpColor.b;
        opacityArr[idx] = opacity;
      }
      idx++;
    }

    this._colorAttr.needsUpdate = true;
    this._opacityAttr.needsUpdate = true;
  }

  dispose(): void {
    this.mesh.geometry.dispose();
    (this.mesh.material as THREE.ShaderMaterial).dispose();
  }
}
