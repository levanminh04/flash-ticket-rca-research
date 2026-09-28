"""Trusted TD-v1.3 event-time trace replay, never an arrival-time simulator.

The vectorized path handles keys occurring once. Repeated keys use the same
timestamp-batched state machine as ``strategy='general'``. Looking ahead to
dispatch a key changes work only, never its earlier numeric observations.
This is a stateless source-to-cutoff materializer: extending a cached cutoff
requires replaying its verified source, not resuming from a cleaned table.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd

TRACE_FIELDS = (
    "time", "traceID", "spanID", "serviceName", "methodName", "operationName",
    "parentSpanID", "startTimeMillis", "startTime", "duration", "statusCode",
)


class ReplayInputError(ValueError):
    pass


def validate_event_clock(series: pd.Series, name: str) -> None:
    """Physical admission is deliberately outside conditional replay claims."""
    if not pd.api.types.is_numeric_dtype(series.dtype):
        raise ReplayInputError(f"UNQUALIFIABLE_EVENT_CLOCK: {name}")
    try:
        values = series.to_numpy(dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ReplayInputError(f"UNQUALIFIABLE_EVENT_CLOCK: {name}") from exc
    if not np.isfinite(values).all() or not np.equal(values, np.floor(values)).all():
        raise ReplayInputError(f"UNQUALIFIABLE_EVENT_CLOCK: {name}")


def _name(value: Any) -> bool:
    return isinstance(value, str) and value != ""


def _payload(row: tuple) -> tuple:
    # A single null sentinel and Python numeric equality make int64 and its
    # nullable float representation compare in their declared units.
    return tuple(None if pd.isna(value) else
                 value.item() if isinstance(value, np.generic) else value
                 for value in row)


def _fingerprint(payload: tuple) -> str:
    canonical = [int(x) if isinstance(x, float) and x.is_integer() else x
                 for x in payload]
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def _graph(first: pd.DataFrame, poisoned: set, services: list[str], fit_ms: int):
    fit = first.loc[first.startTimeMillis < fit_ms].copy()
    if poisoned:
        key_index = pd.MultiIndex.from_frame(fit[["traceID", "spanID"]])
        fit = fit.loc[~key_index.isin(list(poisoned))]
    parents = fit[["traceID", "spanID", "serviceName"]].rename(
        columns={"spanID": "parentSpanID", "serviceName": "parentServiceName"})
    children = fit.loc[fit.parentSpanID.notna() & fit.parentSpanID.ne("")]
    joined = children.merge(parents, on=["traceID", "parentSpanID"],
                            how="left", validate="many_to_one")
    resolved = joined.loc[joined.parentServiceName.notna()]
    supports = resolved.loc[resolved.parentServiceName.ne(resolved.serviceName)].copy()
    index = {name: i for i, name in enumerate(services)}
    adjacency = np.zeros((len(services), len(services)), dtype=bool)
    counts = {}
    for (parent, child), group in supports.groupby(
            ["parentServiceName", "serviceName"], sort=True):
        if parent in index and child in index:
            adjacency[index[parent], index[child]] = True
            counts[f"{index[parent]}->{index[child]}"] = len(group)
    audit = {"nodes": len(services), "edges": int(adjacency.sum()),
             "selected_spans": len(fit), "nonnull_selected_parents": len(children),
             "resolved_selected_parents": len(resolved),
             "unresolved_selected_parents": len(children) - len(resolved),
             "edge_observation_counts": counts,
             "adjacency_sha256": hashlib.sha256(adjacency.tobytes()).hexdigest(),
             "isolates": int((~(adjacency.any(axis=0) | adjacency.any(axis=1))).sum())}
    return adjacency, audit, supports


def trace_replay(frame: pd.DataFrame, *, s0: int, end: int, bin_seconds: int,
                 fit_bins: int, cal_bins: int, strategy: str = "auto",
                 chunk_size: int | None = None) -> dict[str, Any]:
    """Materialize committed counts and the integrity-checked fit graph.

    ``end`` is an absolute exclusive cutoff. ``chunk_size`` changes only bulk
    aggregation; duplicate-key timestamp batches are never split semantically.
    Service names and identity audit are trusted-controller artifacts only.
    """
    if strategy not in {"auto", "general"}:
        raise ValueError("trace replay strategy must be auto or general")
    if chunk_size is not None and (not isinstance(chunk_size, int) or chunk_size < 1):
        raise ValueError("chunk_size must be a positive integer")
    if frame is None or any(field not in frame for field in TRACE_FIELDS):
        raise ReplayInputError("Required trace block/fields missing or corrupt")
    validate_event_clock(frame.startTimeMillis, "trace.startTimeMillis")
    origin_ms, end_ms = s0 * 1000, end * 1000
    fit_ms = (s0 + fit_bins * bin_seconds) * 1000
    warm_ms = (s0 + (fit_bins + cal_bins) * bin_seconds) * 1000
    if end_ms < warm_ms:
        raise ReplayInputError("Insufficient archive for declared C5 warmup")
    selected = frame.loc[(frame.startTimeMillis >= origin_ms) &
                         (frame.startTimeMillis < end_ms), list(TRACE_FIELDS)].copy()
    selected.reset_index(drop=True, inplace=True)
    named = selected.serviceName.map(_name)
    fit_names = set(selected.loc[named & (selected.startTimeMillis < fit_ms), "serviceName"])
    warm_names = set(selected.loc[named & (selected.startTimeMillis < warm_ms), "serviceName"])
    services = sorted(fit_names) + sorted(warm_names - fit_names)
    service_index = {name: i for i, name in enumerate(services)}
    fit_service_mask = np.array([name in fit_names for name in services], dtype=bool)
    bin_count = (end - s0) // bin_seconds
    counts = np.zeros((bin_count, len(services)), dtype=np.int64)
    bad = np.zeros_like(counts, dtype=bool)
    key_valid = selected.traceID.map(_name) & selected.spanID.map(_name)
    duplicate_key = selected.duplicated(["traceID", "spanID"], keep=False)
    ordinary = key_valid & named & ~duplicate_key if strategy == "auto" else pd.Series(
        False, index=selected.index)
    accepted = list(selected.index[ordinary])
    events = []
    tombstones = {}
    duplicates = 0
    tainted_rows = 0
    malformed_rows = 0

    def mask(event_ms, owners, all_services=False):
        b = (int(event_ms) - origin_ms) // (1000 * bin_seconds)
        if all_services:
            bad[b, :] = True
        else:
            for owner in owners:
                if owner in service_index:
                    bad[b, service_index[owner]] = True
        return int(b)

    malformed = selected.loc[~key_valid]
    for row in malformed.itertuples(index=False, name=None):
        owner = row[3]
        b = mask(row[7], {owner} if _name(owner) else set(), not _name(owner))
        events.append({"kind": "MALFORMED_KEY", "event_ms": int(row[7]),
                       "bin": b, "owners": [owner] if _name(owner) else [],
                       "all_services": not _name(owner)})
    malformed_rows += len(malformed)

    exceptional = selected.loc[key_valid & ~ordinary]
    for key, group in exceptional.groupby(["traceID", "spanID"], sort=False):
        owners, fingerprints = set(), set()
        first_seen = int(group.startTimeMillis.min())
        first_payload = None
        quarantined = False
        first_conflict = None
        for event_ms, batch in group.groupby("startTimeMillis", sort=True):
            payloads = {}
            for row in batch.itertuples(index=True, name=None):
                payloads.setdefault(_payload(row[1:]), row[0])
            duplicates += len(batch) - len(payloads)
            owners.update(payload[3] for payload in payloads if _name(payload[3]))
            unknown_owner = any(not _name(payload[3]) for payload in payloads)
            seen = fingerprints | set(payloads)
            conflict_now = len(seen) > 1
            if quarantined or conflict_now or unknown_owner:
                if not quarantined:
                    first_conflict = int(event_ms)
                quarantined = True
                b = mask(event_ms, owners, unknown_owner)
                tainted_rows += len(batch)
                malformed_rows += sum(not _name(payload[3]) for payload in payloads)
                comparison = first_payload if first_payload is not None else min(
                    payloads, key=_fingerprint)
                differing = [field for j, field in enumerate(TRACE_FIELDS)
                             if any(p[j] != comparison[j] for p in payloads)]
                events.append({"kind": "MALFORMED_OWNER" if unknown_owner else
                               "TRACE_CONFLICT" if first_conflict == int(event_ms) else
                               "QUARANTINED_OCCURRENCE", "key": list(key),
                               "event_ms": int(event_ms), "first_seen_ms": first_seen,
                               "first_conflict_ms": first_conflict, "bin": b,
                               "owners": sorted(owners), "all_services": unknown_owner,
                               "fingerprints": sorted(_fingerprint(p) for p in payloads),
                               "differing_fields": differing})
            elif not fingerprints:
                first_payload = next(iter(payloads))
                accepted.append(payloads[first_payload])
            fingerprints = seen
        if quarantined:
            tombstones[key] = {"first_seen_ms": first_seen,
                               "first_conflict_ms": first_conflict,
                               "owners": sorted(owners),
                               "fingerprints": sorted(_fingerprint(p) for p in fingerprints)}

    first = selected.loc[accepted].copy()
    size = chunk_size or max(1, len(first))
    for lo in range(0, len(first), size):
        part = first.iloc[lo:lo + size]
        nodes = part.serviceName.map(service_index)
        mapped = nodes.notna()
        bins = ((part.loc[mapped, "startTimeMillis"].to_numpy(np.int64) - origin_ms)
                // (bin_seconds * 1000))
        np.add.at(counts, (bins, nodes.loc[mapped].to_numpy(np.int64)), 1)
    values = np.log1p(counts.astype(np.float64))
    values[bad] = np.nan
    poisoned_fit = {key for key, state in tombstones.items()
                    if state["first_conflict_ms"] < fit_ms}
    adjacency, graph, supports = _graph(first, poisoned_fit, services, fit_ms)
    if poisoned_fit:
        _, before_graph, _ = _graph(first, set(), services, fit_ms)
    else:
        before_graph = graph
    graph["removed_supports_known_by_freeze"] = (
        sum(before_graph["edge_observation_counts"].values()) -
        sum(graph["edge_observation_counts"].values()))
    discredited = []
    for key, state in tombstones.items():
        if state["first_conflict_ms"] < fit_ms:
            continue
        depends = (supports.traceID.eq(key[0]) &
                   (supports.spanID.eq(key[1]) | supports.parentSpanID.eq(key[1])))
        if depends.any():
            discredited.append({"key": list(key), "event_ms": state["first_conflict_ms"],
                                "support_count": int(depends.sum())})
    audit = {"policy": "TD13_EVENT_TIME_LOCAL_TRACE_PERMANENT_KEY_QUARANTINE",
             "replay_kind": "EVENT_TIME_ARCHIVE_NOT_ARRIVAL_TIME",
             "cutoff_seconds": end - s0, "fit_cutoff_seconds": fit_bins * bin_seconds,
             "warmup_seconds": (fit_bins + cal_bins) * bin_seconds,
             "accepted_span_observations": len(first),
             "identical_duplicates_collapsed": duplicates,
             "tainted_physical_rows": tainted_rows, "malformed_rows": malformed_rows,
             "masked_service_bins": int(bad.sum()), "events": sorted(
                 events, key=lambda e: (e["event_ms"], json.dumps(e, sort_keys=True))),
             "quarantined_keys": [{"key": list(key), **state}
                                  for key, state in sorted(tombstones.items())],
             "post_freeze_discredited_support": sorted(discredited,
                 key=lambda item: (item['event_ms'], item['key'])),
             "pre_origin_rows_audit_only": int((frame.startTimeMillis < origin_ms).sum()),
             "out_of_v_accepted_rows": int((~first.serviceName.isin(service_index)).sum()),
             "fit_presence": np.any(np.isfinite(values[:fit_bins]) &
                                    (values[:fit_bins] > 0), axis=0).tolist(),
             "cache_semantics": "exact-cutoff materialization; append replays verified source",
             "graph": graph}
    return {"values": values, "adj": adjacency, "service_names": services,
            "fit_service_mask": fit_service_mask, "audit": audit}
