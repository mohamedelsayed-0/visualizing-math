import type { AnimationStep, NodeData, EdgeData } from "@/schema/scene";
import type { PointCloudLayer } from "./PointCloudLayer";
import type { EdgeLayer } from "./EdgeLayer";
import type { CameraController } from "./CameraController";

export class TimelinePlayer {
  private _steps: AnimationStep[];
  private _nodes: NodeData[];
  private _edges: EdgeData[];
  private _points: PointCloudLayer;
  private _edgeLayer: EdgeLayer | null;
  private _camera: CameraController;
  private _appliedUpTo: number = -1;
  private _lastTime: number = -Infinity;
  private _activeReveals = new Map<
    string,
    { startTime: number; duration: number }
  >();
  private _activePulses = new Map<
    string,
    { nodeIndex: number; startTime: number; duration: number; amplitude: number }
  >();
  private _hasRevealTimeline: boolean;
  private _knownGroups: string[];
  private _nodeIndexById: Map<string, number>;

  constructor(
    steps: AnimationStep[],
    nodes: NodeData[],
    edges: EdgeData[],
    points: PointCloudLayer,
    edgeLayer: EdgeLayer | null,
    camera: CameraController
  ) {
    this._steps = [...steps].sort((a, b) => a.time - b.time);
    this._nodes = nodes;
    this._edges = edges;
    this._points = points;
    this._edgeLayer = edgeLayer;
    this._camera = camera;
    this._knownGroups = this._collectGroups(nodes);
    this._nodeIndexById = new Map(nodes.map((n, i) => [n.id, i]));
    this._hasRevealTimeline = this._steps.some(
      (s) => s.type === "reveal_group" || s.type === "cluster_reveal"
    );
    this.reset();
  }

  update(currentTime: number): void {
    if (currentTime < this._lastTime) {
      this.reset();
    }
    this._lastTime = currentTime;

    this._camera.update(currentTime);

    for (let i = 0; i < this._steps.length; i++) {
      const step = this._steps[i];
      if (step.time > currentTime) break;
      if (i <= this._appliedUpTo) continue;

      this._applyStep(step);
      this._appliedUpTo = i;
    }

    this._updateActiveReveals(currentTime);
    this._updateActivePulses(currentTime);
  }

  reset(): void {
    this._appliedUpTo = -1;
    this._lastTime = -Infinity;
    this._activeReveals.clear();
    this._activePulses.clear();
    this._edgeLayer?.resetStyles();
    if (this._hasRevealTimeline) {
      this._points.hideAll();
    } else {
      this._points.showAll();
    }
  }

  private _applyStep(step: AnimationStep): void {
    switch (step.type) {
      case "reveal_group":
        this._startRevealGroup(step);
        break;
      case "cluster_reveal":
        this._startClusterReveal(step);
        break;
      case "highlight_edges":
        this._applyHighlightEdges(step);
        break;
      case "fade_all":
        this._applyFadeAll(step);
        break;
      case "pulse_node":
        this._startPulseNode(step);
        break;
      case "set_camera":
        break;
    }
  }

  private _startRevealGroup(step: AnimationStep): void {
    const group = step.params.group as string;
    if (!group) return;
    const duration = Math.max(1e-4, Number(step.params.duration ?? 1.0));
    this._activeReveals.set(group, {
      startTime: step.time,
      duration,
    });
  }

  private _startClusterReveal(step: AnimationStep): void {
    const stagger = Math.max(0, Number(step.params.stagger ?? 0.4));
    const duration = Math.max(1e-4, Number(step.params.duration ?? 1.0));
    const groups =
      (Array.isArray(step.params.groups)
        ? (step.params.groups as unknown[])
            .filter((g): g is string => typeof g === "string")
        : this._knownGroups) ?? [];

    for (let i = 0; i < groups.length; i++) {
      this._activeReveals.set(groups[i], {
        startTime: step.time + i * stagger,
        duration,
      });
    }
  }

  private _updateActiveReveals(currentTime: number): void {
    for (const [group, state] of this._activeReveals) {
      const progress = (currentTime - state.startTime) / state.duration;
      const clamped = Math.max(0, Math.min(1, progress));
      this._points.setRevealByGroup(this._nodes, group, clamped);

      if (progress >= 1) {
        this._activeReveals.delete(group);
      }
    }
  }

  private _applyHighlightEdges(step: AnimationStep): void {
    if (!this._edgeLayer) return;
    const color = (step.params.color as string) ?? "#ffaa00";
    const source = step.params.source as string | undefined;
    const target = step.params.target as string | undefined;
    this._edgeLayer.highlightEdges(
      this._edges,
      { source, target },
      color,
      1.0
    );
  }

  private _applyFadeAll(step: AnimationStep): void {
    const opacity = (step.params.opacity as number) ?? 0.3;
    this._points.setRevealRange(0, this._nodes.length, opacity);
  }

  private _startPulseNode(step: AnimationStep): void {
    const nodeId =
      (step.params.node as string | undefined) ??
      (step.params.id as string | undefined);
    if (!nodeId) return;

    const nodeIndex = this._nodeIndexById.get(nodeId);
    if (nodeIndex === undefined) return;

    const duration = Math.max(1e-3, Number(step.params.duration ?? 1.0));
    const amplitude = Math.max(0.05, Number(step.params.amplitude ?? 0.8));

    this._activePulses.set(nodeId, {
      nodeIndex,
      startTime: step.time,
      duration,
      amplitude,
    });
  }

  private _updateActivePulses(currentTime: number): void {
    for (const [nodeId, pulse] of this._activePulses) {
      const elapsed = currentTime - pulse.startTime;
      if (elapsed < 0) continue;

      const t = elapsed / pulse.duration;
      if (t >= 1) {
        this._points.setRevealRange(pulse.nodeIndex, 1, 1.0);
        this._activePulses.delete(nodeId);
        continue;
      }

      const envelope = Math.sin(Math.PI * t);
      const reveal = 1.0 + pulse.amplitude * envelope;
      this._points.setRevealRange(pulse.nodeIndex, 1, reveal);
    }
  }

  private _collectGroups(nodes: NodeData[]): string[] {
    const groups = new Map<string, number>();

    for (const node of nodes) {
      if (!node.group) continue;
      const existingOrder = groups.get(node.group);
      if (existingOrder === undefined) {
        groups.set(node.group, node.reveal_order);
      } else {
        groups.set(node.group, Math.min(existingOrder, node.reveal_order));
      }
    }

    return [...groups.entries()]
      .sort((a, b) => {
        if (a[1] !== b[1]) return a[1] - b[1];
        return a[0].localeCompare(b[0]);
      })
      .map(([group]) => group);
  }
}
