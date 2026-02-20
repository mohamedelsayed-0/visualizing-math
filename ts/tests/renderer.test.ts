import { describe, expect, it, vi } from "vitest";
import * as THREE from "three";

import {
  CameraController,
  dollyZoomPreset,
  flythroughPreset,
  orbitPreset,
} from "../src/renderer/CameraController";
import { TimelinePlayer } from "../src/renderer/TimelinePlayer";
import { computeTotalFrames } from "../src/capture/headless";
import type { AnimationStep, NodeData } from "../src/schema/scene";

function makeNode(id: string, group?: string, revealOrder = 0): NodeData {
  return {
    id,
    position: [0, 0, 0],
    color: "#ffffff",
    size: 1,
    glow: 1,
    group: group ?? null,
    reveal_order: revealOrder,
  };
}

describe("CameraController", () => {
  it("interpolates camera path and eases between keyframes", () => {
    const camera = new THREE.PerspectiveCamera(60, 16 / 9, 0.1, 1000);
    const ctrl = new CameraController(camera, [
      {
        time: 0,
        position: [0, 0, 10],
        target: [0, 0, 0],
        fov: 60,
        easing: "linear",
      },
      {
        time: 2,
        position: [10, 0, 10],
        target: [0, 0, 0],
        fov: 40,
        easing: "linear",
      },
      {
        time: 4,
        position: [0, 0, 10],
        target: [0, 0, 0],
        fov: 60,
        easing: "linear",
      },
    ]);

    ctrl.update(1);

    // Hermite interpolation on this path should overshoot linear midpoint (5.0).
    expect(camera.position.x).toBeGreaterThan(5);
    expect(camera.fov).toBe(50);
  });

  it("generates camera presets", () => {
    const orbit = orbitPreset([0, 0, 0], 50, 5, 10);
    expect(orbit).toHaveLength(11);
    expect(orbit[0].time).toBe(0);
    expect(orbit[orbit.length - 1].time).toBe(5);

    const fly = flythroughPreset(
      [
        [0, 0, 10],
        [10, 0, 10],
        [20, 0, 10],
      ],
      [0, 0, 0],
      6
    );
    expect(fly).toHaveLength(3);
    expect(fly[2].time).toBe(6);

    const dolly = dollyZoomPreset([0, 0, 120], [0, 0, 60], [0, 0, 0], 4, 8, 60);
    expect(dolly).toHaveLength(9);
    expect(dolly[dolly.length - 1].fov).toBeGreaterThan(dolly[0].fov);
  });
});

describe("TimelinePlayer", () => {
  it("applies progressive reveal_group using duration", () => {
    const points = {
      setRevealByGroup: vi.fn(),
      setRevealRange: vi.fn(),
      showAll: vi.fn(),
      hideAll: vi.fn(),
    } as any;

    const camera = { update: vi.fn() } as any;
    const steps: AnimationStep[] = [
      {
        time: 1,
        type: "reveal_group",
        params: { group: "g1", duration: 2 },
      },
    ];
    const nodes = [makeNode("n1", "g1")];

    const timeline = new TimelinePlayer(steps, nodes, [], points, null, camera);

    timeline.update(1);
    timeline.update(2);

    expect(points.hideAll).toHaveBeenCalled();
    expect(points.setRevealByGroup).toHaveBeenCalledWith(nodes, "g1", 0.5);
  });

  it("applies pulse_node as a temporary reveal boost", () => {
    const points = {
      setRevealByGroup: vi.fn(),
      setRevealRange: vi.fn(),
      showAll: vi.fn(),
      hideAll: vi.fn(),
    } as any;
    const camera = { update: vi.fn() } as any;
    const steps: AnimationStep[] = [
      {
        time: 0,
        type: "pulse_node",
        params: { node: "n1", duration: 2, amplitude: 0.5 },
      },
    ];

    const timeline = new TimelinePlayer(steps, [makeNode("n1")], [], points, null, camera);
    timeline.update(1.0);

    const calls = points.setRevealRange.mock.calls as unknown[][];
    expect(calls.length).toBeGreaterThan(0);
    const [index, count, reveal] = calls[calls.length - 1] as [number, number, number];
    expect(index).toBe(0);
    expect(count).toBe(1);
    expect(reveal).toBeGreaterThan(1.0);
  });

  it("expands cluster_reveal into staggered group reveals", () => {
    const points = {
      setRevealByGroup: vi.fn(),
      setRevealRange: vi.fn(),
      showAll: vi.fn(),
      hideAll: vi.fn(),
    } as any;
    const camera = { update: vi.fn() } as any;
    const steps: AnimationStep[] = [
      {
        time: 0,
        type: "cluster_reveal",
        params: { groups: ["g1", "g2"], duration: 1, stagger: 0.5 },
      },
    ];

    const timeline = new TimelinePlayer(
      steps,
      [makeNode("n1", "g1", 0), makeNode("n2", "g2", 1)],
      [],
      points,
      null,
      camera
    );

    timeline.update(0.75);

    const g1Calls = points.setRevealByGroup.mock.calls.filter(
      (call: unknown[]) => call[1] === "g1"
    );
    const g2Calls = points.setRevealByGroup.mock.calls.filter(
      (call: unknown[]) => call[1] === "g2"
    );

    expect(g1Calls[g1Calls.length - 1][2]).toBeCloseTo(0.75, 6);
    expect(g2Calls[g2Calls.length - 1][2]).toBeCloseTo(0.25, 6);
  });

  it("resets timeline state when time loops backward", () => {
    const points = {
      setRevealByGroup: vi.fn(),
      setRevealRange: vi.fn(),
      showAll: vi.fn(),
      hideAll: vi.fn(),
    } as any;
    const edgeLayer = { resetStyles: vi.fn() } as any;
    const camera = { update: vi.fn() } as any;

    const timeline = new TimelinePlayer(
      [{ time: 0, type: "reveal_group", params: { group: "g1", duration: 1 } }],
      [makeNode("n1", "g1")],
      [],
      points,
      edgeLayer,
      camera
    );

    timeline.update(0.8);
    timeline.update(0.1);

    // Called once during ctor reset and again when time loops backward.
    expect(points.hideAll.mock.calls.length).toBeGreaterThanOrEqual(2);
    expect(edgeLayer.resetStyles).toHaveBeenCalled();
  });
});

describe("capture utilities", () => {
  it("computes deterministic frame counts", () => {
    expect(computeTotalFrames(30, 10)).toBe(300);
    expect(computeTotalFrames(24, 2.5)).toBe(60);
    expect(computeTotalFrames(60, 0.01)).toBe(1);
  });
});
