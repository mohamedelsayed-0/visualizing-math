"""Klotski state-space visualization.

Builds the full reachable state graph for classic Klotski (Huarong Dao),
then highlights:
- solution corridor states in green
- dense left-side non-solution packets in red

Usage:
    viz compile python/examples/klotski_paths.py -o klotski_scene.json
    viz preview klotski_scene.json
    viz render klotski_scene.json -o output/klotski --format frames
"""

from __future__ import annotations

from collections import deque
import hashlib
import math
from typing import Iterable

import networkx as nx
import numpy as np

from mathviz.layout.cluster_shape import group_positions_into_shape
from mathviz.scene.builder import SceneBuilder
from mathviz.scene.helpers import add_overview_then_zoom


BOARD_W = 4
BOARD_H = 5

# State = (big_2x2, vertical_1x2 pieces, horizontal_2x1, small_1x1 pieces)
State = tuple[
    tuple[int, int],
    tuple[tuple[int, int], ...],
    tuple[int, int],
    tuple[tuple[int, int], ...],
]


SHAPE_BIG = ((0, 0), (1, 0), (0, 1), (1, 1))
SHAPE_VERT = ((0, 0), (0, 1))
SHAPE_HORZ = ((0, 0), (1, 0))
SHAPE_SMALL = ((0, 0),)

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def canonical_state(
    big: tuple[int, int],
    verts: Iterable[tuple[int, int]],
    horz: tuple[int, int],
    smalls: Iterable[tuple[int, int]],
) -> State:
    return (big, tuple(sorted(verts)), horz, tuple(sorted(smalls)))


def initial_state() -> State:
    # Classic Klotski initial arrangement.
    return canonical_state(
        big=(1, 0),
        verts=((0, 0), (3, 0), (0, 2), (3, 2)),
        horz=(1, 2),
        smalls=((1, 3), (2, 3), (0, 4), (3, 4)),
    )


def is_goal(state: State) -> bool:
    # Big block reaches the exit at bottom center.
    return state[0] == (1, 3)


def cells_at(shape: Iterable[tuple[int, int]], pos: tuple[int, int]) -> list[tuple[int, int]]:
    px, py = pos
    return [(px + dx, py + dy) for dx, dy in shape]


def state_pieces(state: State) -> list[tuple[str, int, tuple[int, int], tuple[tuple[int, int], ...]]]:
    big, verts, horz, smalls = state
    pieces: list[tuple[str, int, tuple[int, int], tuple[tuple[int, int], ...]]] = [
        ("big", 0, big, SHAPE_BIG),
        ("horz", 0, horz, SHAPE_HORZ),
    ]

    for i, pos in enumerate(verts):
        pieces.append(("vert", i, pos, SHAPE_VERT))
    for i, pos in enumerate(smalls):
        pieces.append(("small", i, pos, SHAPE_SMALL))

    return pieces


def move_piece(state: State, kind: str, idx: int, new_pos: tuple[int, int]) -> State:
    big, verts, horz, smalls = state

    if kind == "big":
        big = new_pos
    elif kind == "horz":
        horz = new_pos
    elif kind == "vert":
        v = list(verts)
        v[idx] = new_pos
        verts = tuple(sorted(v))
    elif kind == "small":
        s = list(smalls)
        s[idx] = new_pos
        smalls = tuple(sorted(s))
    else:
        raise ValueError(f"Unknown piece kind: {kind}")

    return (big, verts, horz, smalls)


def neighbors(state: State) -> list[State]:
    pieces = state_pieces(state)
    occupied: dict[tuple[int, int], tuple[str, int]] = {}

    for kind, idx, pos, shape in pieces:
        for cell in cells_at(shape, pos):
            occupied[cell] = (kind, idx)

    out: set[State] = set()

    for kind, idx, pos, shape in pieces:
        old_cells = set(cells_at(shape, pos))

        for dx, dy in DIRS:
            new_pos = (pos[0] + dx, pos[1] + dy)
            new_cells = cells_at(shape, new_pos)

            fits = True
            for cx, cy in new_cells:
                if cx < 0 or cx >= BOARD_W or cy < 0 or cy >= BOARD_H:
                    fits = False
                    break
                if (cx, cy) in occupied and (cx, cy) not in old_cells:
                    fits = False
                    break

            if fits:
                out.add(move_piece(state, kind, idx, new_pos))

    return list(out)


def build_state_graph() -> tuple[nx.Graph, State, dict[State, int], list[State]]:
    start = initial_state()
    graph = nx.Graph()
    graph.add_node(start)

    dist_start: dict[State, int] = {start: 0}
    queue: deque[State] = deque([start])

    while queue:
        state = queue.popleft()
        d = dist_start[state]

        for nxt in neighbors(state):
            graph.add_edge(state, nxt)
            if nxt not in dist_start:
                dist_start[nxt] = d + 1
                queue.append(nxt)

    goal_states = [s for s in graph.nodes if is_goal(s)]
    if not goal_states:
        raise RuntimeError("No goal states were found in explored Klotski graph")

    return graph, start, dist_start, goal_states


def classify_states(
    graph: nx.Graph,
    dist_start: dict[State, int],
    goal_states: list[State],
) -> tuple[set[State], set[State], dict[State, int], int]:
    dist_goal = multi_source_bfs_lengths(graph, goal_states)
    shortest_len = min(dist_start[s] for s in goal_states)

    solution_states = {
        s
        for s in graph.nodes
        if dist_start[s] + dist_goal[s] == shortest_len
    }

    non_solution = set(graph.nodes) - solution_states
    dense_nopath: set[State] = set()

    if non_solution:
        sub = graph.subgraph(non_solution)
        if sub.number_of_nodes() > 0 and sub.number_of_edges() > 0:
            core = nx.core_number(sub)
            core_values = np.array(list(core.values()), dtype=np.float64)
            core_threshold = float(np.percentile(core_values, 90.0))

            for s, core_num in core.items():
                gap = dist_start[s] + dist_goal[s] - shortest_len
                if core_num >= core_threshold and gap >= 8:
                    dense_nopath.add(s)

        if not dense_nopath:
            ranked = sorted(
                non_solution,
                key=lambda s: (
                    graph.degree[s],
                    dist_start[s] + dist_goal[s] - shortest_len,
                ),
                reverse=True,
            )
            dense_nopath = set(ranked[: max(1, len(ranked) // 12)])

    return solution_states, dense_nopath, dist_goal, shortest_len


def multi_source_bfs_lengths(graph: nx.Graph, sources: Iterable[State]) -> dict[State, int]:
    distances: dict[State, int] = {}
    queue: deque[State] = deque()

    for s in sources:
        if s in distances:
            continue
        distances[s] = 0
        queue.append(s)

    while queue:
        current = queue.popleft()
        base = distances[current]
        for nxt in graph.neighbors(current):
            if nxt in distances:
                continue
            distances[nxt] = base + 1
            queue.append(nxt)

    return distances


def stable_noise(state: State, salt: str) -> float:
    payload = f"{state}|{salt}".encode("utf-8")
    digest = hashlib.blake2s(payload, digest_size=8).digest()
    value = int.from_bytes(digest, "big")
    return value / float(2**64)


def compute_positions(
    graph: nx.Graph,
    dist_start: dict[State, int],
    dist_goal: dict[State, int],
    shortest_len: int,
    solution_states: set[State],
    dense_nopath: set[State],
) -> dict[State, tuple[float, float, float]]:
    max_start = max(dist_start.values()) if dist_start else 1
    max_goal = max(dist_goal.values()) if dist_goal else 1

    positions: dict[State, tuple[float, float, float]] = {}
    layout_groups: dict[State, str] = {}

    for s in graph.nodes:
        ds = dist_start[s]
        dg = dist_goal[s]
        gap = ds + dg - shortest_len

        lane = ds - dg
        radius = 340.0 + gap * 14.0 + abs(lane) * 3.6
        radius += (stable_noise(s, "radius") - 0.5) * 96.0

        theta = stable_noise(s, "theta") * (2.0 * math.pi)
        theta += lane * 0.020

        x = math.cos(theta) * radius + (ds - max_start * 0.46) * 12.4
        y = math.sin(theta) * radius + (dg - max_goal * 0.45) * 11.8
        z = lane * 8.4 + gap * 4.0

        x += (stable_noise(s, "x") - 0.5) * 24.0
        y += (stable_noise(s, "y") - 0.5) * 24.0
        z += (stable_noise(s, "z") - 0.5) * 14.0

        if s in dense_nopath:
            x *= 1.36
            y *= 1.36
            z -= 140.0
            gap_band = min(4, gap // 12)
            side = 0 if lane < 0 else 1
            layout_groups[s] = f"dense_{gap_band}_{side}"
        if s in solution_states:
            x *= 0.43
            y *= 0.43
            z += 180.0
            progress_band = min(7, ds // 16)
            layout_groups[s] = f"solution_{progress_band}"
        elif s not in dense_nopath:
            gap_band = min(6, gap // 18)
            lane_band = max(-2, min(2, lane // 45))
            layout_groups[s] = f"explore_{gap_band}_{lane_band}"

        x *= 2.45
        y *= 2.45
        z *= 1.90

        positions[s] = (float(x), float(y), float(z))

    shaped = group_positions_into_shape(
        positions,
        layout_groups,
        shape="infinity",
        spacing=22500.0,
        compactness=0.50,
        z_wave=2200.0,
        order_by="size",
    )

    for s in dense_nopath:
        px, py, pz = shaped[s]
        shaped[s] = (px - 6200.0, py * 0.92, pz)

    all_points = np.array(list(shaped.values()), dtype=np.float64)
    center_x = float(all_points[:, 0].mean())
    center_y = float(all_points[:, 1].mean())

    for s in graph.nodes:
        if s in dense_nopath or s in solution_states:
            continue
        px, py, pz = shaped[s]
        dx = px - center_x
        dy = py - center_y
        stretch = 1.20
        shaped[s] = (center_x + dx * stretch, center_y + dy * stretch, pz)

    return shaped


def centroid(states: Iterable[State], positions: dict[State, tuple[float, float, float]]) -> tuple[float, float, float]:
    pts = [positions[s] for s in states]
    if not pts:
        return (0.0, 0.0, 0.0)
    arr = np.array(pts, dtype=np.float64)
    c = arr.mean(axis=0)
    return (float(c[0]), float(c[1]), float(c[2]))


def state_id(state: State) -> str:
    big, verts, horz, smalls = state

    parts: list[str] = [f"b{big[0]}{big[1]}", f"h{horz[0]}{horz[1]}"]
    parts.extend(f"v{x}{y}" for x, y in verts)
    parts.extend(f"s{x}{y}" for x, y in smalls)

    return "|".join(parts)


def select_left_dense_packets(
    graph: nx.Graph,
    dense_nopath: set[State],
    positions: dict[State, tuple[float, float, float]],
    global_center: tuple[float, float, float],
) -> set[State]:
    candidates = {s for s in dense_nopath if positions[s][0] < global_center[0]}
    if not candidates:
        return set()

    dense_sub = graph.subgraph(candidates)
    seed_nodes = {s for s, degree in dense_sub.degree() if degree >= 3}
    if not seed_nodes:
        return candidates

    packet_sub = dense_sub.subgraph(seed_nodes)
    packets: set[State] = set()
    for component in nx.connected_components(packet_sub):
        if len(component) >= 10:
            packets.update(component)

    return packets if packets else seed_nodes


def build_scene() -> object:
    graph, start, dist_start, goal_states = build_state_graph()
    solution_states, dense_nopath, dist_goal, shortest_len = classify_states(
        graph,
        dist_start,
        goal_states,
    )
    positions = compute_positions(
        graph,
        dist_start,
        dist_goal,
        shortest_len,
        solution_states,
        dense_nopath,
    )
    solution_center = centroid(solution_states, positions)
    dense_center = centroid(dense_nopath, positions)
    global_center = centroid(graph.nodes, positions)
    dense_left = select_left_dense_packets(graph, dense_nopath, positions, global_center)

    id_map = {s: state_id(s) for s in graph.nodes}
    builder = SceneBuilder()

    for s in graph.nodes:
        if s in solution_states:
            color = "#1aff66"
            size = 2.2
            glow = 4.30
            group = "solution"
            reveal_order = 2
        elif s in dense_left:
            color = "#ff2e2e"
            size = 1.15
            glow = 0.25
            group = "dense_left"
            reveal_order = 1
        else:
            color = "#8bb7ff"
            size = 0.88
            glow = 0.08
            group = "exploration"
            reveal_order = 0

        builder.add_node(
            id=id_map[s],
            position=positions[s],
            color=color,
            size=size,
            glow=glow,
            group=group,
            reveal_order=reveal_order,
        )

    duration = 10.0
    solution_ids = [id_map[s] for s in solution_states]
    pulse_interval = 1.5
    pulse_duration = 1.5
    pulse_times = np.arange(1.5, duration, pulse_interval)
    for pulse_time in pulse_times:
        t = float(pulse_time)
        for node_id in solution_ids:
            builder.add_pulse_node(
                node_id,
                time=t,
                duration=pulse_duration,
                amplitude=1.15,
            )

    for u, v in graph.edges:
        if u in solution_states and v in solution_states:
            edge_color = "#22cc66"
        elif u in dense_left and v in dense_left:
            edge_color = "#ff4d4d"
        else:
            edge_color = "#365a88"

        builder.add_edge(id_map[u], id_map[v], color=edge_color, visible=True)

    add_overview_then_zoom(
        builder,
        positions.values(),
        focus_target=global_center,
        secondary_target=dense_center,
        global_target=global_center,
        duration=duration,
        start_time=0.0,
        overview_distance_scale=2.25,
        focus_distance_scale=0.26,
        sweep_distance_scale=0.46,
        fit_padding=1.20,
        overview_hold_ratio=0.16,
        focus_ratio=0.50,
        sweep_ratio=0.76,
        overview_fov=63.0,
        focus_fov=30.0,
        sweep_fov=38.0,
        end_fov=52.0,
    )

    builder.add_cluster_reveal(
        time=0.0,
        groups=["solution", "dense_left", "exploration"],
        duration=0.9,
        stagger=0.25,
    )

    builder.set_render(
        width=2560,
        height=1440,
        fps=24,
        duration=duration,
        background="#02040b",
        bloom_strength=1.75,
        bloom_radius=0.24,
        bloom_threshold=0.90,
        fog_near=8000,
        fog_far=90000,
        dof_enabled=False,
    )

    scene = builder.build()

    print(
        "Klotski graph stats:",
        f"states={graph.number_of_nodes()}",
        f"edges={graph.number_of_edges()}",
        f"shortest_moves={shortest_len}",
        f"solution_states={len(solution_states)}",
        f"dense_nopath_states={len(dense_nopath)}",
    )

    return scene


if __name__ == "__main__":
    from mathviz.scene.compiler import compile_scene

    scene = build_scene()
    compile_scene(scene, "klotski_scene.json")
    print(f"Scene compiled with {len(scene.nodes)} nodes and {len(scene.edges)} edges")
