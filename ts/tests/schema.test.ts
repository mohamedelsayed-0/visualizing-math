/**
 * Tests for the Zod Scene JSON schema.
 */

import { describe, it, expect } from "vitest";
import { SceneDocumentSchema, NodeDataSchema, EdgeDataSchema } from "../src/schema/scene";

describe("NodeDataSchema", () => {
  it("should parse a valid node", () => {
    const result = NodeDataSchema.parse({
      id: "n1",
      position: [1, 2, 3],
    });
    expect(result.id).toBe("n1");
    expect(result.color).toBe("#ffffff");
    expect(result.size).toBe(1.0);
    expect(result.group).toBeNull();
  });

  it("should parse a node with all fields", () => {
    const result = NodeDataSchema.parse({
      id: "n2",
      position: [0, 0, 0],
      color: "#ff0000",
      size: 2.5,
      group: "cluster_a",
      reveal_order: 3,
    });
    expect(result.color).toBe("#ff0000");
    expect(result.group).toBe("cluster_a");
  });

  it("should reject a node without id", () => {
    expect(() => NodeDataSchema.parse({ position: [0, 0, 0] })).toThrow();
  });
});

describe("EdgeDataSchema", () => {
  it("should parse a valid edge with defaults", () => {
    const result = EdgeDataSchema.parse({ source: "a", target: "b" });
    expect(result.weight).toBe(1.0);
    expect(result.visible).toBe(true);
  });
});

describe("SceneDocumentSchema", () => {
  it("should parse a minimal scene", () => {
    const result = SceneDocumentSchema.parse({
      nodes: [{ id: "n1", position: [0, 0, 0] }],
    });
    expect(result.nodes.length).toBe(1);
    expect(result.edges.length).toBe(0);
    expect(result.version).toBe("1.0");
    expect(result.render_settings.width).toBe(1920);
  });

  it("should parse a full scene", () => {
    const result = SceneDocumentSchema.parse({
      version: "1.0",
      nodes: [
        { id: "a", position: [1, 2, 3], group: "g1" },
        { id: "b", position: [4, 5, 6], group: "g1" },
      ],
      edges: [{ source: "a", target: "b", weight: 0.5 }],
      camera_path: [
        { time: 0, position: [0, 0, 100], target: [0, 0, 0] },
        { time: 10, position: [50, 0, 100], target: [0, 0, 0] },
      ],
      animation_timeline: [
        { time: 1, type: "reveal_group", params: { group: "g1" } },
      ],
      render_settings: {
        duration: 10,
        bloom_strength: 2.0,
      },
    });
    expect(result.nodes.length).toBe(2);
    expect(result.edges[0].weight).toBe(0.5);
    expect(result.render_settings.bloom_strength).toBe(2.0);
  });

  it("should reject invalid animation step type", () => {
    expect(() =>
      SceneDocumentSchema.parse({
        nodes: [{ id: "n1", position: [0, 0, 0] }],
        animation_timeline: [{ time: 0, type: "invalid_type", params: {} }],
      })
    ).toThrow();
  });

  it("should parse cluster_reveal animation steps", () => {
    const result = SceneDocumentSchema.parse({
      nodes: [{ id: "n1", position: [0, 0, 0], group: "g1" }],
      animation_timeline: [
        {
          time: 0,
          type: "cluster_reveal",
          params: { groups: ["g1"], duration: 1, stagger: 0.25 },
        },
      ],
    });

    expect(result.animation_timeline[0].type).toBe("cluster_reveal");
  });

  it("should roundtrip JSON correctly", () => {
    const input = {
      nodes: [
        { id: "a", position: [1, 2, 3] as [number, number, number] },
        { id: "b", position: [4, 5, 6] as [number, number, number] },
      ],
      edges: [{ source: "a", target: "b" }],
    };
    const parsed = SceneDocumentSchema.parse(input);
    const json = JSON.stringify(parsed);
    const reparsed = SceneDocumentSchema.parse(JSON.parse(json));
    expect(reparsed.nodes.length).toBe(2);
    expect(reparsed.edges[0].source).toBe("a");
  });
});
