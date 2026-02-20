import * as THREE from "three";
import { SceneDocumentSchema, type SceneDocument } from "@/schema/scene";
import { PointCloudLayer } from "./PointCloudLayer";
import { EdgeLayer } from "./EdgeLayer";
import { PostProcessingPipeline } from "./PostProcessing";
import { CameraController } from "./CameraController";
import { TimelinePlayer } from "./TimelinePlayer";

export class SceneManager {
  readonly renderer: THREE.WebGLRenderer;
  readonly scene: THREE.Scene;
  readonly camera: THREE.PerspectiveCamera;

  private _doc: SceneDocument;
  private _points: PointCloudLayer;
  private _edges: EdgeLayer | null = null;
  private _postProcessing: PostProcessingPipeline;
  private _cameraCtrl: CameraController;
  private _timeline: TimelinePlayer;

  private _currentTime: number = 0;
  private _lastWallTime: number = 0;
  private _animating: boolean = false;

  constructor(doc: SceneDocument, canvas?: HTMLCanvasElement) {
    this._doc = doc;
    const s = doc.render_settings;

    const isPreview = !!canvas;
    const initW = isPreview ? (canvas!.clientWidth || window.innerWidth) : s.width;
    const initH = isPreview ? (canvas!.clientHeight || window.innerHeight) : s.height;

    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      preserveDrawingBuffer: true,
    });
    this.renderer.setSize(initW, initH);
    const deviceRatio = window.devicePixelRatio ?? 1;
    const preferredRatio = isPreview ? Math.max(deviceRatio, 1.25) : deviceRatio;
    this.renderer.setPixelRatio(Math.min(preferredRatio, 2.5));
    this.renderer.setClearColor(s.background);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(s.background);

    this.camera = new THREE.PerspectiveCamera(60, initW / initH, 0.1, 10000);
    this.camera.position.set(0, 0, 200);
    this._configureCameraClipPlanes(doc);

    this._points = new PointCloudLayer(doc.nodes);
    this.scene.add(this._points.mesh);

    if (doc.edges.length > 0) {
      this._edges = new EdgeLayer(doc.edges, doc.nodes);
      this.scene.add(this._edges.mesh);
    }

    this._cameraCtrl = new CameraController(this.camera, doc.camera_path);

    this._timeline = new TimelinePlayer(
      doc.animation_timeline,
      doc.nodes,
      doc.edges,
      this._points,
      this._edges,
      this._cameraCtrl
    );

    this._postProcessing = new PostProcessingPipeline(
      this.renderer,
      this.scene,
      this.camera,
      s
    );
  }

  static fromJSON(json: unknown, canvas?: HTMLCanvasElement): SceneManager {
    const doc = SceneDocumentSchema.parse(json);
    return new SceneManager(doc, canvas);
  }

  startPreview(): void {
    if (this._animating) return;
    this._animating = true;
    this._lastWallTime = performance.now() / 1000;
    this._animate();
  }

  stopPreview(): void {
    this._animating = false;
  }

  togglePreviewPause(): void {
    if (this._animating) {
      this.stopPreview();
    } else {
      this.startPreview();
    }
  }

  renderFrame(time: number): void {
    this._currentTime = time;
    this._timeline.update(this._currentTime);
    this._postProcessing.render();
  }

  resizePostProcessing(width: number, height: number): void {
    this._postProcessing.setSize(width, height);
  }

  captureFrame(): string {
    return this.renderer.domElement.toDataURL("image/png");
  }

  get duration(): number {
    return this._doc.render_settings.duration;
  }

  get fps(): number {
    return this._doc.render_settings.fps;
  }

  get isPreviewPlaying(): boolean {
    return this._animating;
  }

  private _animate = (): void => {
    if (!this._animating) return;
    requestAnimationFrame(this._animate);

    const now = performance.now() / 1000;
    const delta = now - this._lastWallTime;
    this._lastWallTime = now;
    this._currentTime = (this._currentTime + Math.max(0, delta)) % this._doc.render_settings.duration;

    this._timeline.update(this._currentTime);
    this._postProcessing.render();
  };

  dispose(): void {
    this._animating = false;
    this._points.dispose();
    this._edges?.dispose();
    this._postProcessing.dispose();
    this.renderer.dispose();
  }

  private _configureCameraClipPlanes(doc: SceneDocument): void {
    let maxExtent = 0;

    for (const node of doc.nodes) {
      const [x, y, z] = node.position;
      maxExtent = Math.max(maxExtent, Math.hypot(x, y, z));
    }

    for (const keyframe of doc.camera_path) {
      const [px, py, pz] = keyframe.position;
      const [tx, ty, tz] = keyframe.target;
      maxExtent = Math.max(maxExtent, Math.hypot(px, py, pz), Math.hypot(tx, ty, tz));
    }

    const safeExtent = Math.max(1000, maxExtent);
    this.camera.near = 0.05;
    this.camera.far = Math.max(10000, safeExtent * 24 + 4000);
    this.camera.updateProjectionMatrix();
  }
}
