"""Frozen contextual comparator boundaries required by TD-v1.3.

These are separate complete-method comparators.  In particular, Local-MAX-MT
is not the C1 ``L`` arm.  RCD requires an explicitly injected callable from the
qualified pinned environment; there is no fallback ranking or generic import.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from .ranking import _channel_types, local_scores


LOCAL_MAX_MT = "Local-MAX-MT"
BARO_ADAPTED = "BARO-RANK-adapted-TD12"
RCD_ADAPTED = "RCD-RCAEval-adapted-TD12"


def baro_scores(ref, query, channel_types, floor=0.01):
    """Run the registered BARO component adaptation, not full upstream BARO."""
    ref = np.asarray(ref, dtype=np.float64)
    query = np.asarray(query, dtype=np.float64)
    if ref.ndim != 3 or query.ndim != 3 or ref.shape[:2] != query.shape[:2]:
        raise ValueError("ref/query must have matching N,K and three dimensions")
    types = _channel_types(channel_types, ref.shape[1])
    indices = [index for index, kind in enumerate(types) if kind == "metric"]
    result = local_scores(
        ref[:, indices, :],
        query[:, indices, :],
        [0] * len(indices),
        {
            "floor": floor,
            "pool": "max",
            "fusion": "max",
            "temporal": "max",
            "cap": None,
            "include_logs": False,
        },
    )
    result["scores"] = result["blocks"]["metric"].copy()
    result["method"] = BARO_ADAPTED
    return result


def local_max_scores(blocks, block_masks):
    """Run mandatory Local-MAX-MT with unavailable-zero masks preserved."""
    metric = np.asarray(blocks["metric"])
    trace = np.asarray(blocks["trace"])
    metric_mask = np.asarray(block_masks["metric"], dtype=bool)
    trace_mask = np.asarray(block_masks["trace"], dtype=bool)
    if (
        metric.ndim != 1
        or metric.shape != trace.shape
        or metric.shape != metric_mask.shape
        or metric.shape != trace_mask.shape
    ):
        raise ValueError("MT blocks/masks must be matching vectors")
    if (
        not np.isfinite(metric).all()
        or not np.isfinite(trace).all()
        or (metric < 0).any()
        or (trace < 0).any()
    ):
        raise ValueError("MT blocks must be finite nonnegative placeholders")
    return {
        "scores": np.maximum(
            np.where(metric_mask, metric, 0.0),
            np.where(trace_mask, trace, 0.0),
        ),
        "mask": metric_mask | trace_mask,
        "method": LOCAL_MAX_MT,
    }


def rcd_run(dataframe, seed=420, bins=5, *, upstream_rcd: Callable | None):
    """Execute the qualified bare RCD callable on an opaque 600-row frame."""

    def failure(reason, message=None):
        return {
            "method": RCD_ADAPTED,
            "seed": seed,
            "bins": bins,
            "status": "FAILURE",
            "ranks": None,
            "reason": reason,
            "error": message,
        }

    if not callable(upstream_rcd):
        return failure("unqualified_upstream_callable")
    if seed not in (420, 421, 422) or bins not in (3, 5, 7):
        return failure("unregistered_seed_or_bins")
    if "time" not in dataframe.columns or dataframe.columns.duplicated().any():
        return failure("missing_time_or_duplicate_columns")
    columns = [column for column in dataframe.columns if column != "time"]
    if not columns:
        return failure("no_eligible_columns")
    if any(
        not isinstance(column, str) or not column or column == "F-node"
        for column in columns
    ):
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
        result = upstream_rcd(
            dataframe.copy(deep=True),
            300,
            dk_select_useful=False,
            gamma=5,
            localized=True,
            bins=bins,
            verbose=False,
            dataset=None,
            seed=seed,
        )
    except Exception as exc:  # third-party boundary; sanitize the message
        return failure("upstream_exception", type(exc).__name__)
    if not isinstance(result, dict) or not isinstance(result.get("ranks"), (list, tuple)):
        return failure("malformed_output")
    ranks = list(result["ranks"])
    if any(not isinstance(column, str) or not column for column in ranks):
        return failure("unparseable_metric_rank")
    if len(set(ranks)) != len(ranks):
        return failure("duplicate_metric_rank")
    return {
        "method": RCD_ADAPTED,
        "seed": seed,
        "bins": bins,
        "status": "SUCCESS",
        "ranks": ranks,
        "reason": None,
        "error": None,
        "unknown_metric_keys": [column for column in ranks if column not in columns],
    }


COMPARATOR_IDS = (LOCAL_MAX_MT, BARO_ADAPTED, RCD_ADAPTED)


__all__ = [
    "BARO_ADAPTED",
    "COMPARATOR_IDS",
    "LOCAL_MAX_MT",
    "RCD_ADAPTED",
    "baro_scores",
    "local_max_scores",
    "rcd_run",
]
