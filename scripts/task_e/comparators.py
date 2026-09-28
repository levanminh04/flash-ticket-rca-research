"""Declared TD12 comparator adapters; no fallback rankings or GT access.

RCD execution requires an injected, externally qualified, pinned/patched bare
upstream function. This module never imports an arbitrary installed RCAEval.
"""

import numpy as np

from .ranking import _channel_types, local_scores


def baro_scores(ref, query, channel_types, floor=.01):
    """Paper-component BARO adaptation: absolute temporal MAX, then service MAX.

    Uses common TD reference/query metric bins, finite-bin eligibility, type-7
    quantiles and the selected study-specific floor. No MBOCPD, count evidence,
    upstream domain filters, constant dropping or signed-max code path is used.
    Returns scores plus the same numeric diagnostics as local_scores.
    """
    ref, query = np.asarray(ref, dtype=np.float64), np.asarray(query, dtype=np.float64)
    if ref.ndim != 3 or query.ndim != 3 or ref.shape[:2] != query.shape[:2]:
        raise ValueError("ref/query must have matching N,K and three dimensions")
    types = _channel_types(channel_types, ref.shape[1])
    js = [j for j, kind in enumerate(types) if kind == "metric"]
    result = local_scores(ref[:, js, :], query[:, js, :], [0] * len(js),
                          {"floor": floor, "pool": "max", "fusion": "max",
                           "temporal": "max", "cap": None, "include_logs": False})
    result["scores"] = result["blocks"]["metric"].copy()
    result["method"] = "BARO-RANK-adapted-TD12"
    return result


def local_max_scores(blocks, block_masks):
    """Mandatory Local-MAX-MT context, retaining unavailable-zero masks."""
    m, t = np.asarray(blocks["metric"]), np.asarray(blocks["trace"])
    mm, tm = np.asarray(block_masks["metric"], dtype=bool), np.asarray(
        block_masks["trace"], dtype=bool)
    if m.ndim != 1 or m.shape != t.shape or m.shape != mm.shape or m.shape != tm.shape:
        raise ValueError("MT blocks/masks must be matching vectors")
    if not np.isfinite(m).all() or not np.isfinite(t).all() or (m < 0).any() or (t < 0).any():
        raise ValueError("MT blocks must be finite nonnegative placeholders")
    return {"scores": np.maximum(np.where(mm, m, 0.), np.where(tm, t, 0.)),
            "mask": mm | tm, "method": "Local-MAX-MT"}


def rcd_run(dataframe, seed=420, bins=5, *, upstream_rcd):
    """Execute qualified bare RCD on a trusted 600-row opaque numeric frame.

    time must be exactly relative seconds 0..599; boundary300 is used only for
    slicing and the source patch drops time immediately afterward. All other
    columns are numeric opaque metric keys; owner mapping stays in the trusted
    caller. Inputs are already eligibility-checked and reference-median-imputed.
    Parameters are gamma5/localizedTrue/datasetNone/dk_select_usefulFalse.
    Each seed must run sequentially or in its own process, not shared threads.
    A valid empty ranks list is preserved for all-V worst-tie padding by caller;
    exceptions/duplicate metric keys/malformed output are explicit failures.
    No root labels, epoch, service vocabulary or owner mapping are accepted.
    """
    def failure(reason, message=None):
        return {"method": "RCD-RCAEval-adapted-TD12", "seed": seed, "bins": bins,
                "status": "FAILURE", "ranks": None, "reason": reason,
                "error": message}

    if not callable(upstream_rcd):
        return failure("unqualified_upstream_callable")
    if seed not in (420, 421, 422) or bins not in (3, 5, 7):
        return failure("unregistered_seed_or_bins")
    if "time" not in dataframe.columns or dataframe.columns.duplicated().any():
        return failure("missing_time_or_duplicate_columns")
    columns = [c for c in dataframe.columns if c != "time"]
    if not columns:
        return failure("no_eligible_columns")
    if any(not isinstance(c, str) or not c or c == "F-node" for c in columns):
        return failure("invalid_metric_key")
    try:
        times = dataframe["time"].to_numpy(dtype=np.float64)
        values = dataframe[columns].to_numpy(dtype=np.float64)
    except (TypeError, ValueError):
        return failure("nonnumeric_input")
    if not np.array_equal(times, np.arange(600, dtype=np.float64)):
        return failure("invalid_relative_grid")
    if not np.isfinite(values).all():
        return failure("nonfinite_after_imputation")
    try:
        result = upstream_rcd(dataframe.copy(deep=True), 300,
                              dk_select_useful=False, gamma=5, localized=True,
                              bins=bins, verbose=False, dataset=None, seed=seed)
    except Exception as exc:
        # Deliberately exclude exception text: third-party errors can carry
        # paths or identifiers. Trusted orchestration records sanitized details.
        return failure("upstream_exception", type(exc).__name__)
    if not isinstance(result, dict) or not isinstance(result.get("ranks"), (list, tuple)):
        return failure("malformed_output")
    ranks = list(result["ranks"])
    if any(not isinstance(c, str) or not c for c in ranks):
        return failure("unparseable_metric_rank")
    if len(set(ranks)) != len(ranks):
        return failure("duplicate_metric_rank")
    return {"method": "RCD-RCAEval-adapted-TD12", "seed": seed, "bins": bins,
            "status": "SUCCESS", "ranks": ranks, "reason": None, "error": None,
            "unknown_metric_keys": [c for c in ranks if c not in columns]}
