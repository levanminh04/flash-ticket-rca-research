"""Pure numeric C1 evidence, graph ranking, and finite structural controls.

Semantics are extracted from the Task E implementation qualified under
TD-v1.3.  No filesystem, labels, service names, or evaluator data enter this
module.  Count channels must already be log1p transformed by a trusted adapter.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence

import numpy as np


def _channel_types(channel_types: Sequence[object], k: int) -> list[str]:
    names = {
        0: "metric",
        1: "trace",
        2: "log",
        "metric": "metric",
        "trace": "trace",
        "log": "log",
    }
    if len(channel_types) != k:
        raise ValueError("channel_types length does not match K")
    try:
        result = [names[value] for value in channel_types]
    except (KeyError, TypeError) as exc:
        raise ValueError("channel_types must be 0/1/2 or metric/trace/log") from exc
    if result.count("trace") > 1 or result.count("log") > 1:
        raise ValueError("TD has at most one trace-count and one log-count channel")
    return result


def local_scores(ref, query, channel_types, config: Mapping[str, object]):
    """Compute frozen C1 local evidence and explicit availability masks."""
    ref = np.asarray(ref, dtype=np.float64)
    query = np.asarray(query, dtype=np.float64)
    if ref.ndim != 3 or query.ndim != 3 or ref.shape[:2] != query.shape[:2]:
        raise ValueError("ref/query must have matching (N,K) and three dimensions")
    if ref.shape[2] < 1 or query.shape[2] < 1:
        raise ValueError("reference/query need at least one bin")
    n, k = ref.shape[:2]
    types = _channel_types(channel_types, k)
    cfg = dict(config)
    floor = float(cfg.get("floor", 0.01))
    pool = cfg.get("pool", "max")
    fusion = cfg.get("fusion", "max")
    temporal = cfg.get("temporal", "q90")
    cap = cfg.get("cap")
    include_logs = bool(cfg.get("include_logs", False))
    if not np.isfinite(floor) or floor <= 0:
        raise ValueError("floor must be finite and positive")
    if pool not in ("max", "q90") or temporal not in ("max", "q90"):
        raise ValueError("pool/temporal must be max or q90")
    if fusion not in ("max", "availablemean") or cap not in (None, 20):
        raise ValueError("unsupported fusion or historical cap")

    scores = np.zeros((n, k), dtype=np.float64)
    valid = np.zeros((n, k), dtype=bool)
    numerical = np.zeros((n, k), dtype=bool)
    ref_n = np.isfinite(ref).sum(axis=2)
    query_n = np.isfinite(query).sum(axis=2)
    ref_min = math.ceil(0.8 * ref.shape[2])
    query_min = math.ceil(0.8 * query.shape[2])
    centers = np.full((n, k), np.nan)
    scales = np.full((n, k), np.nan)
    reasons: list[list[str | None]] = [[None] * k for _ in range(n)]

    for i in range(n):
        for j, kind in enumerate(types):
            if kind == "log" and not include_logs:
                reasons[i][j] = "excluded_primary_log"
                continue
            a = ref[i, j, np.isfinite(ref[i, j])]
            b = query[i, j, np.isfinite(query[i, j])]
            if len(a) < ref_min or len(b) < query_min:
                reasons[i][j] = "insufficient_finite_bins"
                continue
            if kind != "metric":
                if (a < 0).any() or (b < 0).any():
                    reasons[i][j] = "invalid_negative_count"
                    continue
                if not (a > 0).any():
                    reasons[i][j] = "absent_reference_count"
                    continue
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                center = np.quantile(a, 0.5, method="linear")
                q25, q75 = np.quantile(a, [0.25, 0.75], method="linear")
                scale = max(
                    q75 - q25,
                    floor * np.quantile(np.abs(a), 0.5, method="linear"),
                    1e-12,
                )
                ratio = np.abs(b - center) / scale
            if (
                not np.isfinite(center)
                or not np.isfinite(scale)
                or not np.isfinite(ratio).all()
            ):
                numerical[i, j] = True
                reasons[i][j] = "numerical_channel_failure"
                continue
            if cap == 20:
                ratio = np.minimum(ratio, 20.0) / 20.0
            score = (
                np.max(ratio)
                if temporal == "max"
                else np.quantile(ratio, 0.9, method="linear")
            )
            if not np.isfinite(score):
                numerical[i, j] = True
                reasons[i][j] = "numerical_channel_failure"
                continue
            centers[i, j], scales[i, j] = center, scale
            scores[i, j], valid[i, j] = score, True
            reasons[i][j] = "available"

    blocks = {kind: np.zeros(n) for kind in ("metric", "trace", "log")}
    block_masks = {kind: np.zeros(n, dtype=bool) for kind in blocks}
    for kind in blocks:
        js = [j for j, value in enumerate(types) if value == kind]
        for i in range(n):
            values = scores[i, js][valid[i, js]]
            if len(values):
                blocks[kind][i] = (
                    np.quantile(values, 0.9, method="linear")
                    if kind == "metric" and pool == "q90"
                    else np.max(values)
                )
                block_masks[kind][i] = True

    participating = ("metric", "trace", "log") if include_logs else ("metric", "trace")
    local = np.zeros(n)
    local_mask = np.zeros(n, dtype=bool)
    for i in range(n):
        values = [blocks[kind][i] for kind in participating if block_masks[kind][i]]
        if values:
            maximum = max(values)
            local[i] = (
                maximum
                if fusion == "max" or maximum == 0.0
                else maximum * np.mean(np.asarray(values) / maximum)
            )
            local_mask[i] = True
    if not np.isfinite(local).all():
        raise RuntimeError("local fusion numerical invariant failed")
    return {
        "local": local,
        "blocks": blocks,
        "channel_scores": scores,
        "masks": {"channels": valid, "blocks": block_masks, "local": local_mask},
        "diagnostics": {
            "reference_valid_bins": ref_n,
            "query_valid_bins": query_n,
            "reference_min_bins": ref_min,
            "query_min_bins": query_min,
            "centers": centers,
            "scales": scales,
            "channel_reasons": reasons,
            "numerical_channel_failures": numerical,
            "config": cfg,
        },
    }


def _adjacency(adj) -> np.ndarray:
    result = np.asarray(adj)
    if result.ndim != 2 or result.shape[0] != result.shape[1]:
        raise ValueError("adj must be square")
    if not np.isfinite(result).all() or not np.isin(result, [0, 1]).all():
        raise ValueError("adj must be finite binary observed relations")
    result = result.astype(bool, copy=True)
    if np.diag(result).any():
        raise ValueError("observed same-service relations are provenance, not edges")
    return result


def rank_scores(local, adj, operator="ppr", direction="reverse", damping=0.85):
    """Apply the registered graph operator to a nonnegative local vector."""
    a = _adjacency(adj)
    local = np.asarray(local, dtype=np.float64)
    if (
        local.ndim != 1
        or len(local) != len(a)
        or not np.isfinite(local).all()
        or (local < 0).any()
    ):
        raise ValueError("local must be a finite nonnegative vector matching adj")
    if operator not in ("ppr", "diffusion") or direction not in ("reverse", "undirected"):
        raise ValueError("unsupported operator/direction")
    damping = float(damping)
    if not np.isfinite(damping) or not 0 <= damping < 1:
        raise ValueError("damping must be in [0,1)")
    if operator == "diffusion" and direction != "undirected":
        raise ValueError("value diffusion is registered only as undirected")

    graph = (a | a.T) if direction == "undirected" else a.T
    transition = graph.astype(np.float64)
    degrees = transition.sum(axis=1)
    isolates = degrees == 0
    transition[isolates, isolates] = 1.0
    degrees[isolates] = 1.0
    transition /= degrees[:, None]
    scale = float(local.max()) if len(local) else 0.0
    diagnostics = {
        "operator": operator,
        "direction": direction,
        "damping": damping,
        "raw_local_scale": scale,
        "isolates": isolates,
        "transition": transition,
        "no_evidence": scale == 0,
    }
    if scale == 0:
        scores = np.zeros_like(local)
        diagnostics.update(residual_inf=0.0, personalization=np.zeros_like(local))
        return {"scores": scores, "rounded_scores": scores.copy(), "diagnostics": diagnostics}

    normalized = local / scale
    rhs_base = normalized / normalized.sum() if operator == "ppr" else normalized
    matrix = np.eye(len(local)) - damping * (
        transition.T if operator == "ppr" else transition
    )
    rhs = (1.0 - damping) * rhs_base
    try:
        scores = np.linalg.solve(matrix, rhs)
    except np.linalg.LinAlgError as exc:
        raise RuntimeError("ranking solve failed") from exc
    residual = float(np.max(np.abs(matrix @ scores - rhs)))
    if not np.isfinite(scores).all() or residual > 1e-10:
        raise RuntimeError("ranking residual/nonfinite invariant failed")
    if operator == "ppr":
        if scores.min() < -1e-12 or abs(scores.sum() - 1.0) > 1e-10:
            raise RuntimeError("PPR nonnegative/mass invariant failed")
        scores = np.maximum(scores, 0.0)
        scores /= scores.sum()
        residual = float(np.max(np.abs(matrix @ scores - rhs)))
        if residual > 1e-10 or abs(scores.sum() - 1.0) > 1e-10:
            raise RuntimeError("PPR invariant failed after roundoff normalization")
        diagnostics["personalization"] = rhs_base
    elif scores.min() < normalized.min() - 1e-10 or scores.max() > normalized.max() + 1e-10:
        raise RuntimeError("value diffusion convex-bound invariant failed")
    diagnostics["residual_inf"] = residual
    return {
        "scores": scores,
        "rounded_scores": np.round(scores, 12),
        "diagnostics": diagnostics,
    }


def _components(adjacency: np.ndarray) -> np.ndarray:
    weak = adjacency | adjacency.T
    labels = np.full(len(adjacency), -1, dtype=np.int64)
    for start in range(len(adjacency)):
        if labels[start] >= 0:
            continue
        labels[start] = start
        stack = [start]
        while stack:
            source = stack.pop()
            for target in np.flatnonzero(weak[source]):
                if labels[target] < 0:
                    labels[target] = start
                    stack.append(int(target))
    return labels


def _graph_hash(adjacency: np.ndarray) -> str:
    return hashlib.sha256(
        str(adjacency.shape).encode("ascii") + np.packbits(adjacency).tobytes()
    ).hexdigest()


def perturb_graphs(adj, handle: str, representation: str, count=256, budget=200):
    """Generate exact fixed-budget independent finite edge-switch chains."""
    original = _adjacency(adj)
    if representation not in ("directed", "undirected"):
        raise ValueError("representation must be directed or undirected")
    if not isinstance(handle, str) or not handle or "|" in handle:
        raise ValueError("handle must be an issued opaque nonempty delimiter-free string")
    if not isinstance(count, int) or count < 1 or not isinstance(budget, int) or budget < 1:
        raise ValueError("count/budget must be positive integers")
    directed = representation == "directed"
    if not directed:
        original |= original.T
    baseline_edges = [
        tuple(map(int, edge))
        for edge in np.argwhere(original if directed else np.triu(original, 1))
    ]
    edge_count = len(baseline_edges)
    proposals = budget * max(1, edge_count)
    partition = _components(original)
    component_sizes = {
        int(component): int((partition == component).sum())
        for component in np.unique(partition)
    }
    original_in = original.sum(axis=0)
    original_out = original.sum(axis=1)
    results, receipts = [], []

    for draw in range(count):
        material = f"TD12|R|{handle}|{representation}|{draw}"
        seed = int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")
        rng = np.random.Generator(np.random.PCG64(seed))
        current = original.copy()
        edges, present = list(baseline_edges), set(baseline_edges)
        weak = [
            set(map(int, np.flatnonzero((current | current.T)[node])))
            for node in range(len(current))
        ]
        accepted = 0
        rejected = {
            "insufficient_edges": 0,
            "shared_endpoint": 0,
            "existing_edge": 0,
            "component_partition": 0,
        }

        def set_edge(edge, value):
            source, target = edge
            current[source, target] = value
            if not directed:
                current[target, source] = value
            if current[source, target] or current[target, source]:
                weak[source].add(target)
                weak[target].add(source)
            else:
                weak[source].discard(target)
                weak[target].discard(source)

        for _ in range(proposals):
            if edge_count < 2:
                rejected["insufficient_edges"] += 1
                continue
            first_index = int(rng.integers(edge_count))
            second_index = int(rng.integers(edge_count - 1))
            if second_index >= first_index:
                second_index += 1
            old_first, old_second = edges[first_index], edges[second_index]
            a, b = old_first
            c, d = old_second
            if not directed:
                if rng.integers(2):
                    a, b = b, a
                if rng.integers(2):
                    c, d = d, c
            if len({a, b, c, d}) != 4:
                rejected["shared_endpoint"] += 1
                continue
            new_first, new_second = (a, d), (c, b)
            if not directed:
                new_first, new_second = tuple(sorted(new_first)), tuple(sorted(new_second))
            if new_first in present or new_second in present or new_first == new_second:
                rejected["existing_edge"] += 1
                continue
            if partition[a] != partition[c]:
                rejected["component_partition"] += 1
                continue
            set_edge(old_first, False)
            set_edge(old_second, False)
            set_edge(new_first, True)
            set_edge(new_second, True)
            seen, stack = {a}, [a]
            while stack:
                source = stack.pop()
                for target in weak[source]:
                    if target not in seen:
                        seen.add(target)
                        stack.append(target)
            if len(seen) != component_sizes[int(partition[a])]:
                set_edge(new_first, False)
                set_edge(new_second, False)
                set_edge(old_first, True)
                set_edge(old_second, True)
                rejected["component_partition"] += 1
                continue
            present.remove(old_first)
            present.remove(old_second)
            present.update((new_first, new_second))
            edges[first_index], edges[second_index] = new_first, new_second
            accepted += 1

        invariant = (
            np.array_equal(current.sum(axis=0), original_in)
            and np.array_equal(current.sum(axis=1), original_out)
            and np.array_equal(_components(current), partition)
            and not np.diag(current).any()
        )
        if not invariant or accepted + sum(rejected.values()) != proposals:
            raise RuntimeError("finite-control invariant failed")
        retained = len(present.intersection(baseline_edges)) / max(1, edge_count)
        changed = np.any(current != original, axis=1)
        if directed:
            changed |= np.any(current != original, axis=0)
        receipts.append(
            {
                "draw": draw,
                "seed": seed,
                "proposals": proposals,
                "accepted": accepted,
                "acceptance_rate": accepted / proposals,
                "rejections": rejected,
                "hash": _graph_hash(current),
                "invariants": True,
                "retained_edge_fraction": retained,
                "changed_node_fraction": float(changed.mean()) if len(changed) else 0.0,
            }
        )
        results.append(current)

    hashes = [receipt["hash"] for receipt in receipts]
    median_retained = float(np.median([r["retained_edge_fraction"] for r in receipts]))
    distinct = len(set(hashes))
    return {
        "graphs": np.stack(results),
        "per_draw": receipts,
        "summary": {
            "representation": representation,
            "planned": count,
            "completed": count,
            "failed": 0,
            "budget": budget,
            "edges": edge_count,
            "proposals_per_draw": proposals,
            "partition": partition,
            "component_sizes": component_sizes,
            "distinct_final_graphs": distinct,
            "median_retained_edge_fraction": median_retained,
            "mobile": distinct >= 32 and median_retained <= 0.8,
            "degenerate": distinct == 1,
        },
    }
