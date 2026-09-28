"""Numeric-only TD-v1.2 local evidence, ranking and finite graph controls.

No filesystem, telemetry retrieval, labels or service names enter this module.
Count channels are already log1p-transformed by the trusted loader.
"""

import hashlib
import math

import numpy as np


def _channel_types(channel_types, k):
    names = {0: "metric", 1: "trace", 2: "log", "metric": "metric",
             "trace": "trace", "log": "log"}
    if len(channel_types) != k:
        raise ValueError("channel_types length does not match K")
    try:
        result = [names[t] for t in channel_types]
    except (KeyError, TypeError) as exc:
        raise ValueError("channel_types must be 0/1/2 or metric/trace/log") from exc
    if result.count("trace") > 1 or result.count("log") > 1:
        raise ValueError("TD has at most one trace-count and one log-count channel")
    return result


def local_scores(ref, query, channel_types, config):
    """Return local evidence for (N,K,B) numeric arrays, including missing masks.

    Config: floor .001/.01 (sensitivity .0001 also supported), pool max/q90,
    fusion max/availablemean, temporal q90/max, cap None/20, include_logs False.
    cap=20 is the historical min(deviation,20)/20 diagnostic, not a new primary.
    Type-7 quantiles use linear interpolation. A valid count channel needs a
    positive reference count. Missing/nonfinite observations do not become zero
    observations; unavailable scores are zero placeholders with masks=False.
    Arithmetic failures invalidate that channel and are returned explicitly.
    """
    ref = np.asarray(ref, dtype=np.float64)
    query = np.asarray(query, dtype=np.float64)
    if ref.ndim != 3 or query.ndim != 3 or ref.shape[:2] != query.shape[:2]:
        raise ValueError("ref/query must have matching (N,K) and three dimensions")
    if ref.shape[2] < 1 or query.shape[2] < 1:
        raise ValueError("reference/query need at least one bin")
    n, k = ref.shape[:2]
    types = _channel_types(channel_types, k)
    cfg = dict(config)
    floor = float(cfg.get("floor", .01))
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
    ref_min = math.ceil(.8 * ref.shape[2])
    query_min = math.ceil(.8 * query.shape[2])
    centers = np.full((n, k), np.nan)
    scales = np.full((n, k), np.nan)
    reasons = [[None] * k for _ in range(n)]
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
                center = np.quantile(a, .5, method="linear")
                q25, q75 = np.quantile(a, [.25, .75], method="linear")
                scale = max(q75 - q25, floor * np.quantile(np.abs(a), .5,
                            method="linear"), 1e-12)
                ratio = np.abs(b - center) / scale
            if (not np.isfinite(center) or not np.isfinite(scale) or
                    not np.isfinite(ratio).all()):
                numerical[i, j] = True
                reasons[i][j] = "numerical_channel_failure"
                continue
            if cap == 20:
                ratio = np.minimum(ratio, 20.) / 20.
            score = np.max(ratio) if temporal == "max" else np.quantile(
                ratio, .9, method="linear")
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
        js = [j for j, t in enumerate(types) if t == kind]
        for i in range(n):
            values = scores[i, js][valid[i, js]]
            if len(values):
                blocks[kind][i] = (np.quantile(values, .9, method="linear")
                                   if kind == "metric" and pool == "q90"
                                   else np.max(values))
                block_masks[kind][i] = True
    participating = ("metric", "trace", "log") if include_logs else ("metric", "trace")
    local = np.zeros(n)
    local_mask = np.zeros(n, dtype=bool)
    for i in range(n):
        values = [blocks[t][i] for t in participating if block_masks[t][i]]
        if values:
            maximum = max(values)
            local[i] = (maximum if fusion == "max" or maximum == 0. else
                        maximum * np.mean(np.asarray(values) / maximum))
            local_mask[i] = True
    if not np.isfinite(local).all():
        raise RuntimeError("local fusion numerical invariant failed")
    return {"local": local, "blocks": blocks, "channel_scores": scores,
            "masks": {"channels": valid, "blocks": block_masks, "local": local_mask},
            "diagnostics": {"reference_valid_bins": ref_n, "query_valid_bins": query_n,
                "reference_min_bins": ref_min, "query_min_bins": query_min,
                "centers": centers, "scales": scales, "channel_reasons": reasons,
                "numerical_channel_failures": numerical, "config": cfg}}


def _adjacency(adj):
    a = np.asarray(adj)
    if a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise ValueError("adj must be square")
    if not np.isfinite(a).all() or not np.isin(a, [0, 1]).all():
        raise ValueError("adj must be finite binary observed relations")
    a = a.astype(bool, copy=True)
    if np.diag(a).any():
        raise ValueError("observed same-service relations are provenance, not edges")
    return a


def rank_scores(local, adj, operator="ppr", direction="reverse", damping=.85):
    """Rank a nonnegative local vector using parent->child observed adjacency.

    ppr uses reverse or undirected processing and solves probability mass.
    diffusion uses undirected processing and returns max-normalized value scores.
    Identity can be supplied as an empty graph (isolate self-loops arise here).
    Returns scores, rounded_scores and diagnostics; numerical invariant failure
    raises RuntimeError, never silently falls back to local evidence.
    """
    a = _adjacency(adj)
    l = np.asarray(local, dtype=np.float64)
    if l.ndim != 1 or len(l) != len(a) or not np.isfinite(l).all() or (l < 0).any():
        raise ValueError("local must be a finite nonnegative vector matching adj")
    if operator not in ("ppr", "diffusion") or direction not in ("reverse", "undirected"):
        raise ValueError("unsupported operator/direction")
    d = float(damping)
    if not np.isfinite(d) or not 0 <= d < 1:
        raise ValueError("damping must be in [0,1)")
    if operator == "diffusion" and direction != "undirected":
        raise ValueError("value diffusion is registered only as undirected")
    graph = (a | a.T) if direction == "undirected" else a.T
    transition = graph.astype(np.float64)
    degrees = transition.sum(axis=1)
    isolates = degrees == 0
    transition[isolates, isolates] = 1.
    degrees[isolates] = 1.
    transition /= degrees[:, None]
    scale = float(l.max()) if len(l) else 0.
    diag = {"operator": operator, "direction": direction, "damping": d,
            "raw_local_scale": scale, "isolates": isolates,
            "transition": transition, "no_evidence": scale == 0}
    if scale == 0:
        scores = np.zeros_like(l)
        diag.update(residual_inf=0., personalization=np.zeros_like(l))
        return {"scores": scores, "rounded_scores": scores.copy(), "diagnostics": diag}
    z = l / scale
    rhs_base = z / z.sum() if operator == "ppr" else z
    mat = np.eye(len(l)) - d * (transition.T if operator == "ppr" else transition)
    rhs = (1. - d) * rhs_base
    try:
        scores = np.linalg.solve(mat, rhs)
    except np.linalg.LinAlgError as exc:
        raise RuntimeError("ranking solve failed") from exc
    residual = float(np.max(np.abs(mat @ scores - rhs)))
    if not np.isfinite(scores).all() or residual > 1e-10:
        raise RuntimeError("ranking residual/nonfinite invariant failed")
    if operator == "ppr":
        if scores.min() < -1e-12 or abs(scores.sum() - 1.) > 1e-10:
            raise RuntimeError("PPR nonnegative/mass invariant failed")
        scores = np.maximum(scores, 0.)
        scores /= scores.sum()
        residual = float(np.max(np.abs(mat @ scores - rhs)))
        if residual > 1e-10 or abs(scores.sum() - 1.) > 1e-10:
            raise RuntimeError("PPR invariant failed after roundoff normalization")
        diag["personalization"] = rhs_base
    elif scores.min() < z.min() - 1e-10 or scores.max() > z.max() + 1e-10:
        raise RuntimeError("value diffusion convex-bound invariant failed")
    diag["residual_inf"] = residual
    return {"scores": scores, "rounded_scores": np.round(scores, 12), "diagnostics": diag}


def _components(a):
    weak = a | a.T
    labels = np.full(len(a), -1, dtype=np.int64)
    for start in range(len(a)):
        if labels[start] >= 0:
            continue
        labels[start] = start
        stack = [start]
        while stack:
            u = stack.pop()
            for v in np.flatnonzero(weak[u]):
                if labels[v] < 0:
                    labels[v] = start
                    stack.append(int(v))
    return labels


def _graph_hash(a):
    return hashlib.sha256(str(a.shape).encode("ascii") + np.packbits(a).tobytes()).hexdigest()


def perturb_graphs(adj, handle, representation, count=256, budget=200):
    """Generate fixed-budget independent TD12 PCG64 edge-switch chains.

    representation is directed or undirected. Seeds are first eight SHA256
    bytes interpreted big-endian from TD12|R|handle|representation|j. Every chain
    starts observed. Ordered distinct edge pairs are uniform; undirected edge
    orientations use independent fair coins. Rejections are self-transitions.
    No score, root, convergence criterion or adaptive proposal budget is used.
    Returns graphs, per_draw receipts and summary; never removes degenerate draws.
    """
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
    baseline_edges = [tuple(map(int, e)) for e in np.argwhere(
        original if directed else np.triu(original, 1))]
    ecount = len(baseline_edges)
    proposals = budget * max(1, ecount)
    partition = _components(original)
    component_sizes = {int(c): int((partition == c).sum()) for c in np.unique(partition)}
    original_in, original_out = original.sum(axis=0), original.sum(axis=1)
    results, receipts = [], []
    for j in range(count):
        material = "TD12|R|%s|%s|%s" % (handle, representation, j)
        seed = int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:8], "big")
        rng = np.random.Generator(np.random.PCG64(seed))
        current = original.copy()
        edges, present = list(baseline_edges), set(baseline_edges)
        weak = [set(map(int, np.flatnonzero((current | current.T)[i])))
                for i in range(len(current))]
        accepted = 0
        rejected = {"insufficient_edges": 0, "shared_endpoint": 0,
                    "existing_edge": 0, "component_partition": 0}

        def set_edge(edge, value):
            u, v = edge
            current[u, v] = value
            if not directed:
                current[v, u] = value
            if current[u, v] or current[v, u]:
                weak[u].add(v)
                weak[v].add(u)
            else:
                weak[u].discard(v)
                weak[v].discard(u)

        for _ in range(proposals):
            if ecount < 2:
                rejected["insufficient_edges"] += 1
                continue
            ia = int(rng.integers(ecount))
            ib = int(rng.integers(ecount - 1))
            if ib >= ia:
                ib += 1
            old1, old2 = edges[ia], edges[ib]
            a, b = old1
            c, d = old2
            if not directed:
                if rng.integers(2):
                    a, b = b, a
                if rng.integers(2):
                    c, d = d, c
            if len({a, b, c, d}) != 4:
                rejected["shared_endpoint"] += 1
                continue
            new1, new2 = (a, d), (c, b)
            if not directed:
                new1, new2 = tuple(sorted(new1)), tuple(sorted(new2))
            if new1 in present or new2 in present or new1 == new2:
                rejected["existing_edge"] += 1
                continue
            if partition[a] != partition[c]:
                rejected["component_partition"] += 1
                continue
            set_edge(old1, False)
            set_edge(old2, False)
            set_edge(new1, True)
            set_edge(new2, True)
            seen, stack = {a}, [a]
            while stack:
                u = stack.pop()
                for v in weak[u]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            if len(seen) != component_sizes[int(partition[a])]:
                set_edge(new1, False)
                set_edge(new2, False)
                set_edge(old1, True)
                set_edge(old2, True)
                rejected["component_partition"] += 1
                continue
            present.remove(old1)
            present.remove(old2)
            present.update((new1, new2))
            edges[ia], edges[ib] = new1, new2
            accepted += 1
        invariant = (np.array_equal(current.sum(axis=0), original_in) and
                     np.array_equal(current.sum(axis=1), original_out) and
                     np.array_equal(_components(current), partition) and
                     not np.diag(current).any())
        if not invariant or accepted + sum(rejected.values()) != proposals:
            raise RuntimeError("finite-control invariant failed")
        overlap = len(present.intersection(baseline_edges)) / max(1, ecount)
        changed = np.any(current != original, axis=1)
        if directed:
            changed |= np.any(current != original, axis=0)
        receipts.append({"draw": j, "seed": seed, "proposals": proposals,
            "accepted": accepted, "acceptance_rate": accepted / proposals,
            "rejections": rejected, "hash": _graph_hash(current), "invariants": True,
            "retained_edge_fraction": overlap,
            "changed_node_fraction": float(changed.mean()) if len(changed) else 0.})
        results.append(current)
    hashes = [r["hash"] for r in receipts]
    overlap = float(np.median([r["retained_edge_fraction"] for r in receipts]))
    distinct = len(set(hashes))
    return {"graphs": np.stack(results), "per_draw": receipts,
            "summary": {"representation": representation, "planned": count,
                "completed": count, "failed": 0, "budget": budget, "edges": ecount,
                "proposals_per_draw": proposals, "partition": partition,
                "component_sizes": component_sizes, "distinct_final_graphs": distinct,
                "median_retained_edge_fraction": overlap,
                "mobile": distinct >= 32 and overlap <= .8,
                "degenerate": distinct == 1}}
