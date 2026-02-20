/**
 * Zod schema for the Scene JSON format.
 * Must mirror the Pydantic models in python/mathviz/scene/models.py
 */

import { z } from "zod";

const Vec3 = z.tuple([z.number(), z.number(), z.number()]);

export const NodeDataSchema = z.object({
  id: z.string(),
  position: Vec3,
  color: z.string().default("#ffffff"),
  size: z.number().default(1.0),
  glow: z.number().default(1.0),
  group: z.string().nullable().default(null),
  reveal_order: z.number().int().default(0),
});

export const EdgeDataSchema = z.object({
  source: z.string(),
  target: z.string(),
  weight: z.number().default(1.0),
  color: z.string().nullable().default(null),
  visible: z.boolean().default(true),
});

export const CameraKeyframeSchema = z.object({
  time: z.number().min(0),
  position: Vec3,
  target: Vec3,
  fov: z.number().default(60.0),
  easing: z.string().default("ease-in-out"),
});

export const AnimationStepSchema = z.object({
  time: z.number().min(0),
  type: z.enum([
    "reveal_group",
    "cluster_reveal",
    "highlight_edges",
    "set_camera",
    "fade_all",
    "pulse_node",
  ]),
  params: z.record(z.unknown()).default({}),
});

export const RenderSettingsSchema = z.object({
  width: z.number().int().default(1920),
  height: z.number().int().default(1080),
  fps: z.number().int().default(30),
  duration: z.number().default(10.0),
  background: z.string().default("#000011"),
  bloom_strength: z.number().default(1.5),
  bloom_radius: z.number().default(0.4),
  bloom_threshold: z.number().default(0.2),
  fog_near: z.number().default(50.0),
  fog_far: z.number().default(500.0),
  tone_mapping: z
    .enum(["ACESFilmic", "Linear", "Reinhard", "Cineon"])
    .default("ACESFilmic"),
  dof_enabled: z.boolean().default(true),
  dof_focus_distance: z.number().default(100.0),
  dof_aperture: z.number().default(0.025),
});

export const SceneDocumentSchema = z.object({
  version: z.string().default("1.0"),
  nodes: z.array(NodeDataSchema),
  edges: z.array(EdgeDataSchema).default([]),
  camera_path: z.array(CameraKeyframeSchema).default([]),
  animation_timeline: z.array(AnimationStepSchema).default([]),
  render_settings: RenderSettingsSchema.default({}),
});

// Inferred TypeScript types
export type NodeData = z.infer<typeof NodeDataSchema>;
export type EdgeData = z.infer<typeof EdgeDataSchema>;
export type CameraKeyframe = z.infer<typeof CameraKeyframeSchema>;
export type AnimationStep = z.infer<typeof AnimationStepSchema>;
export type RenderSettings = z.infer<typeof RenderSettingsSchema>;
export type SceneDocument = z.infer<typeof SceneDocumentSchema>;
