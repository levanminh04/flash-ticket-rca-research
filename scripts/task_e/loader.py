"""Trusted TD12 development I/O and telemetry-only numeric bundle construction.

Returned ``service_names``, ``s0`` and ``audit`` are controller-side artifacts.
They must never be included in numeric worker inputs. No models or network I/O.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

METRIC_SUFFIXES = (
    "latency-90", "latency-50", "workload", "diskio", "latency",
    "socket", "error", "load", "cpu", "mem",
)
CHANNEL_TYPES = np.array([0] * 10 + [1, 2], dtype=np.int64)
WORKSPACE = Path(r"D:/Project/flash-ticket-rca-research")
RAW_ROOTS = (WORKSPACE / "datasets/rcaeval/raw-samples",
             WORKSPACE / "datasets/rcaeval/task-e-development")
TRACE_FIELDS = (
    "time", "traceID", "spanID", "serviceName", "methodName", "operationName",
    "parentSpanID", "startTimeMillis", "startTime", "duration", "statusCode",
)
LOG_FIELDS = ("timestamp", "container_name", "message")
DEV_CELLS = (
    ("ts-auth-service", "cpu"), ("ts-auth-service", "delay"),
    ("ts-order-service", "disk"), ("ts-order-service", "loss"),
    ("ts-route-service", "mem"), ("ts-route-service", "socket"),
    ("ts-train-service", "cpu"), ("ts-train-service", "delay"),
    ("ts-travel-service", "disk"), ("ts-travel-service", "loss"),
)
DEV_IDS = frozenset(f"re2tt_{root}_{fault}_{repeat}"
                    for root, fault in DEV_CELLS for repeat in (1, 2, 3))


class LoaderError(ValueError):
    """A requested telemetry input cannot be interpreted under TD12."""


class UnresolvedProtocolError(LoaderError):
    """An encountered input needs explicit D adjudication, not silent repair."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_schema(modality: str, table: Any) -> None:
    names = table.column_names
    if len(names) != len(set(names)):
        raise LoaderError("Duplicate physical column names")
    expected = TRACE_FIELDS if modality == "traces" else LOG_FIELDS
    if modality != "metrics" and tuple(names) != expected:
        raise LoaderError(f"Unexpected {modality} fields/order: {names}")
    time_key = {"metrics": "time", "traces": "startTimeMillis", "logs": "timestamp"}[modality]
    if time_key not in names or not pa.types.is_integer(table.schema.field(time_key).type):
        raise LoaderError(f"{time_key} must have an integer physical type")
    if modality == "metrics":
        if any(not pd.api.types.is_numeric_dtype(table[c].to_pandas().dtype)
               for c in names if c != "time"):
            raise LoaderError("Metric values must have numeric physical types")
    else:
        string_fields = TRACE_FIELDS[:7] if modality == "traces" else LOG_FIELDS[1:]
        for field in string_fields:
            if str(table.schema.field(field).type) not in {"string", "large_string"}:
                raise LoaderError(f"{field} must have a string physical type")
        if modality == "traces":
            for field in TRACE_FIELDS[7:]:
                if not pa.types.is_integer(table.schema.field(field).type):
                    raise LoaderError(f"{field} must have an integer physical type")


def load_case(paths_by_modality: Mapping[str, str | Path | None],
              metadata_record: Mapping[str, Any], *,
              expected_files: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Read a development case, keeping schema failures as explicit availability.

    Exact source paths and immutable bytes must match the frozen source manifest
    before Parquet parsing. There is no unverified model-loader entry point.
    This is the trusted boundary. Missing M is allowed for C1 available-block
    fusion; C5 separately requires observed M time for its runtime origin.
    No global row defect invalidates a past window at this stage.
    """
    case = metadata_record.get("case")
    if case not in DEV_IDS:
        raise LoaderError("Only the exact TD12 thirty development IDs are admitted")
    unknown = set(paths_by_modality) - {"metrics", "traces", "logs"}
    if unknown:
        raise LoaderError(f"Unexpected modality keys: {sorted(unknown)}")
    raw: dict[str, Any] = {"metrics": None, "traces": None, "logs": None}
    audit: dict[str, Any] = {"scope": "trusted-development-loader", "case": case,
                             "modalities": {}, "metadata": dict(metadata_record)}
    for modality in raw:
        provided = paths_by_modality.get(modality)
        entry: dict[str, Any] = {"present": False, "status": "MISSING"}
        audit["modalities"][modality] = entry
        if provided is None:
            continue
        path = Path(provided).resolve()
        allowed_relative = Path(case) / f"{modality}.parquet"
        admitted = False
        for root in RAW_ROOTS:
            try:
                relative = path.relative_to(root.resolve())
            except ValueError:
                continue
            if relative == allowed_relative:
                admitted = True
                break
        if not admitted:
            raise LoaderError("Telemetry path is outside the exact development case/modality roots")
        expected = expected_files.get(modality)
        if expected is None:
            raise LoaderError(f"No frozen source identity supplied for {modality}")
        expected_sha = expected.get("sha256", expected.get("official_lfs_sha256"))
        expected_bytes = expected.get("bytes")
        if (not isinstance(expected_sha, str) or len(expected_sha) != 64 or
                any(c not in "0123456789abcdef" for c in expected_sha.lower()) or
                not isinstance(expected_bytes, int) or expected_bytes <= 0):
            raise LoaderError(f"Invalid frozen source identity for {modality}")
        entry.update(path=str(path), expected_bytes=expected_bytes, expected_sha256=expected_sha.lower())
        if not path.is_file():
            continue
        entry.update(present=True, bytes=path.stat().st_size, sha256=_sha256(path))
        entry["source_identity_verified"] = (entry["bytes"] == expected_bytes and
                                               entry["sha256"] == expected_sha.lower())
        if not entry["source_identity_verified"]:
            raise LoaderError(f"Source identity mismatch before Parquet read: {modality}")
        try:
            table = pq.read_table(path)
            _validate_schema(modality, table)
            frame = table.to_pandas()
            raw[modality] = frame
            time_key = {"metrics": "time", "traces": "startTimeMillis", "logs": "timestamp"}[modality]
            valid_time = frame[time_key].dropna()
            entry.update(status="LOADED", rows=len(frame), columns=list(frame.columns),
                         schema=str(table.schema), nulls={c: int(v) for c, v in frame.isna().sum().items()},
                         time_min=int(valid_time.min()) if len(valid_time) else None,
                         time_max=int(valid_time.max()) if len(valid_time) else None,
                         full_row_duplicates=int(frame.duplicated().sum()))
        except Exception as exc:
            entry.update(status="CORRUPT_OR_UNSUPPORTED", error_type=type(exc).__name__, error=str(exc))
    raw["audit"] = audit
    return raw


def _frame(raw: Mapping[str, Any], modality: str) -> pd.DataFrame | None:
    value = raw.get(modality)
    if value is not None and not isinstance(value, pd.DataFrame):
        raise LoaderError(f"{modality} is not a DataFrame")
    return value


def _integer_clock(series: pd.Series, field: str) -> None:
    """Refuse fractional/unplaceable timestamps; never round an unknown clock."""
    try:
        values = series.to_numpy(dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise LoaderError(f"Unsupported numeric clock for {field}") from exc
    if not np.isfinite(values).all() or not np.equal(values, np.floor(values)).all():
        raise LoaderError(f"{field} must contain finite integral timestamp units")


def _c1_window_frame(frame: pd.DataFrame | None, field: str,
                     lo: int, hi: int) -> pd.DataFrame | None:
    """Select known-window rows before checking their timestamp integrality.

    Finite numeric timestamps outside [lo,hi) have a known position and cannot
    veto this C1 window merely because they are fractional. Nonfinite or
    nonnumeric timestamps cannot safely be placed outside the window and remain
    explicit failures. This is not C5 streaming or archive qualification.
    """
    if frame is None:
        return None
    if field not in frame or not pd.api.types.is_numeric_dtype(frame[field].dtype):
        raise LoaderError(f"Unplaceable numeric clock for {field}")
    try:
        values = frame[field].to_numpy(dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise LoaderError(f"Unsupported numeric clock for {field}") from exc
    if not np.isfinite(values).all():
        raise LoaderError(f"{field} contains unplaceable nonfinite timestamps")
    selected = frame.loc[(values >= lo) & (values < hi)].copy()
    _integer_clock(selected[field], field)
    return selected


def _trace_slice(frame: pd.DataFrame | None, lo: int, hi: int) -> pd.DataFrame:
    if frame is None:
        raise LoaderError("Required trace block missing/corrupt")
    if any(c not in frame for c in TRACE_FIELDS):
        raise LoaderError("Required trace fields missing")
    _integer_clock(frame.startTimeMillis, "startTimeMillis")
    selected = frame.loc[(frame.startTimeMillis >= lo * 1000) &
                         (frame.startTimeMillis < hi * 1000)].copy()
    required = ["traceID", "spanID", "serviceName", "startTimeMillis"]
    if selected[required].isna().any().any():
        raise LoaderError("Null required trace identity inside requested window")
    if any(selected[c].eq("").any() for c in required[:3]):
        raise LoaderError("Empty required trace identity inside requested window")
    return selected


def _deduplicate_trace(frame: pd.DataFrame, *, c5: bool = False) -> tuple[pd.DataFrame, int]:
    clean = frame.drop_duplicates()
    if clean.duplicated(["traceID", "spanID"], keep=False).any():
        if c5:
            raise UnresolvedProtocolError(
                "C5 conflicting span payload: affected channel/bin, graph-fit treatment "
                "and post-encounter propagation require D adjudication; past outputs must not be repaired")
        raise LoaderError("Conflicting (traceID,spanID) payload in selected C1 window")
    return clean, len(frame) - len(clean)


def _metric_mapping(frame: pd.DataFrame | None, services: list[str]) -> tuple[dict[str, tuple[int, int]], list[str]]:
    if frame is None:
        return {}, []
    index = {s: i for i, s in enumerate(services)}
    mapping: dict[str, tuple[int, int]] = {}
    unmatched = []
    for column in frame.columns:
        if column == "time":
            continue
        found = False
        for channel, suffix in enumerate(METRIC_SUFFIXES):
            if column.endswith("_" + suffix):
                service = column[:-(len(suffix) + 1)]
                if service in index:
                    mapping[column] = (index[service], channel)
                    found = True
                break
        if not found:
            unmatched.append(column)
    return mapping, unmatched


def _metric_bins(frame: pd.DataFrame | None, services: list[str], lo: int, hi: int,
                 width: int, minimum_seconds: int, *, invalidate_channel: bool) -> tuple[np.ndarray, dict[str, Any]]:
    count = (hi - lo) // width
    values = np.full((len(services), 10, count), np.nan, dtype=np.float64)
    mapping, unmatched = _metric_mapping(frame, services)
    report: dict[str, Any] = {"loaded": frame is not None, "mapping": mapping,
                              "unmatched_columns": unmatched, "conflicting_seconds": {},
                              "identical_duplicate_seconds": {}, "finite_bins": {}}
    if frame is None:
        return values, report
    if "time" not in frame:
        raise LoaderError("Unplaceable metric timestamps")
    _integer_clock(frame.time, "metrics.time")
    selected = frame.loc[(frame.time >= lo) & (frame.time < hi)]
    for column, (node, channel) in mapping.items():
        data = selected[["time", column]].copy()
        groups = data.groupby("time", sort=True, dropna=False)[column]
        conflicts = groups.nunique(dropna=False)
        conflict_times = conflicts.index[conflicts > 1]
        report["conflicting_seconds"][column] = [int(x) for x in conflict_times]
        report["identical_duplicate_seconds"][column] = int(len(data) - data.time.nunique() -
                                                           sum(groups.size().loc[conflict_times] - 1))
        if len(conflict_times) and invalidate_channel:
            report["finite_bins"][column] = 0
            continue
        clean = data.drop_duplicates("time", keep="first").copy()
        clean["bin"] = ((clean.time - lo) // width).astype(int)
        clean.loc[~np.isfinite(clean[column].to_numpy(dtype=np.float64)), column] = np.nan
        grouped = clean.groupby("bin")[column]
        medians = grouped.median()
        coverage = grouped.count()
        bad_bins = set(((np.asarray(conflict_times, dtype=np.int64) - lo) // width).tolist())
        for b, value in medians.items():
            if 0 <= b < count and coverage.loc[b] >= minimum_seconds and b not in bad_bins:
                values[node, channel, b] = value
        report["finite_bins"][column] = int(np.isfinite(values[node, channel]).sum())
    return values, report


def _counts(frame: pd.DataFrame | None, services: list[str], lo: int, hi: int,
            width: int, modality: str) -> tuple[np.ndarray, dict[str, Any]]:
    count = (hi - lo) // width
    result = np.full((len(services), count), np.nan, dtype=np.float64)
    report = {"loaded": frame is not None, "mapped_rows": 0, "unmapped_rows": 0,
              "reference_presence": [False] * len(services)}
    if frame is None:
        return result, report
    result.fill(0.0)
    name = "serviceName" if modality == "traces" else "container_name"
    time = "startTimeMillis" if modality == "traces" else "timestamp"
    multiplier = 1000 if modality == "traces" else 1
    if name not in frame or time not in frame:
        raise LoaderError(f"Required {modality} count fields absent")
    _integer_clock(frame[time], f"{modality}.{time}")
    selected = frame.loc[(frame[time] >= lo * multiplier) & (frame[time] < hi * multiplier)].copy()
    selected["bin"] = ((selected[time] - lo * multiplier) // (width * multiplier)).astype(int)
    index = {s: i for i, s in enumerate(services)}
    mapped = selected.loc[selected[name].isin(index)]
    report["mapped_rows"] = len(mapped)
    report["unmapped_rows"] = len(selected) - len(mapped)
    for (service, b), rows in mapped.groupby([name, "bin"], sort=False):
        if 0 <= b < count:
            result[index[service], b] = np.log1p(len(rows))
            report["reference_presence"][index[service]] = True
    return result, report


def _graph(frame: pd.DataFrame, services: list[str]) -> tuple[np.ndarray, dict[str, Any]]:
    adjacency = np.zeros((len(services), len(services)), dtype=np.bool_)
    index = {s: i for i, s in enumerate(services)}
    parents = frame[["traceID", "spanID", "serviceName"]].rename(
        columns={"spanID": "parentSpanID", "serviceName": "parentServiceName"})
    children = frame.loc[frame.parentSpanID.notna() & frame.parentSpanID.ne("")]
    joined = children.merge(parents, on=["traceID", "parentSpanID"], how="left", validate="many_to_one")
    resolved = joined.loc[joined.parentServiceName.notna()]
    edges: dict[str, int] = {}
    for (parent, child), group in resolved.groupby(["parentServiceName", "serviceName"], sort=False):
        if parent != child and parent in index and child in index:
            adjacency[index[parent], index[child]] = True
            edges[f"{index[parent]}->{index[child]}"] = len(group)
    report = {"nodes": len(services), "edges": int(adjacency.sum()),
              "selected_spans": len(frame), "nonnull_selected_parents": len(children),
              "resolved_selected_parents": len(resolved), "unresolved_selected_parents": len(children)-len(resolved),
              "edge_observation_counts": edges, "adjacency_sha256": hashlib.sha256(adjacency.tobytes()).hexdigest(),
              "isolates": int((~(adjacency.any(axis=0) | adjacency.any(axis=1))).sum())}
    return adjacency, report


def c1_bundle(raw: Mapping[str, Any], tau: int, bin_seconds: int = 10,
              horizon: int = 300) -> dict[str, Any]:
    """Common known-window telemetry; no local scoring or labels in arrays."""
    if bin_seconds <= 0 or horizon <= 0 or horizon % bin_seconds:
        raise LoaderError("C1 horizon must contain complete positive-width bins")
    tau = int(tau)
    trace_window = _c1_window_frame(_frame(raw, "traces"), "startTimeMillis",
                                    (tau-horizon)*1000, (tau+horizon)*1000)
    selected = _trace_slice(trace_window, tau-horizon, tau+horizon)
    selected, duplicates = _deduplicate_trace(selected)
    services = sorted(set(selected.serviceName))
    ref_t = selected.loc[selected.startTimeMillis < tau*1000]
    query_t = selected.loc[selected.startTimeMillis >= tau*1000]
    minimum = int(np.ceil(bin_seconds * .5))
    metric_window = _c1_window_frame(_frame(raw, "metrics"), "time",
                                     tau-horizon, tau+horizon)
    ref_m, ref_a = _metric_bins(metric_window, services, tau-horizon, tau,
                               bin_seconds, minimum, invalidate_channel=True)
    query_m, query_a = _metric_bins(metric_window, services, tau, tau+horizon,
                                   bin_seconds, minimum, invalidate_channel=True)
    # A conflict anywhere in the admitted windows invalidates that common channel.
    conflicted = set(c for c, times in ref_a["conflicting_seconds"].items() if times)
    conflicted |= set(c for c, times in query_a["conflicting_seconds"].items() if times)
    mapping, _ = _metric_mapping(metric_window, services)
    for column in conflicted:
        node, channel = mapping[column]
        ref_m[node, channel] = np.nan
        query_m[node, channel] = np.nan
    ref_counts, rt = _counts(ref_t, services, tau-horizon, tau, bin_seconds, "traces")
    query_counts, qt = _counts(query_t, services, tau, tau+horizon, bin_seconds, "traces")
    try:
        logs = _c1_window_frame(_frame(raw, "logs"), "timestamp",
                                tau-horizon, tau+horizon)
        ref_l, rl = _counts(logs, services, tau-horizon, tau, bin_seconds, "logs")
        query_l, ql = _counts(logs, services, tau, tau+horizon, bin_seconds, "logs")
    except LoaderError as exc:
        # Logs are excluded from primary C1; their failure cannot veto common M/T.
        ref_l, rl = _counts(None, services, tau-horizon, tau, bin_seconds, "logs")
        query_l, ql = _counts(None, services, tau, tau+horizon, bin_seconds, "logs")
        rl["error"] = ql["error"] = str(exc)
    adjacency, ga = _graph(ref_t, services)
    ref = np.concatenate((ref_m, ref_counts[:, None], ref_l[:, None]), axis=1)
    query = np.concatenate((query_m, query_counts[:, None], query_l[:, None]), axis=1)
    return {"ref": ref, "query": query, "adj": adjacency, "service_names": services,
            "channel_types": CHANNEL_TYPES.copy(),
            "audit": {"profile": "TD12-C1-MT", "metric_ref": ref_a, "metric_query": query_a,
                      "trace_ref": rt, "trace_query": qt, "log_ref": rl, "log_query": ql,
                      "graph": ga, "identical_trace_duplicates_collapsed": duplicates,
                      "conflicted_metric_channels": sorted(conflicted),
                      "trace_reference_presence": rt["reference_presence"],
                      "log_reference_presence": rl["reference_presence"],
                      "query_only_services": sorted(set(query_t.serviceName)-set(ref_t.serviceName)),
                      "primary_excludes_log_channel": True}}


def c5_bundle(raw: Mapping[str, Any], bin_seconds: int = 5, warmup_seconds: int = 180,
              fit_bins: int = 24, cal_bins: int = 12, *,
              cutoff_seconds: int | None = None, trace_strategy: str = "auto",
              trace_chunk_size: int | None = None) -> dict[str, Any]:
    """TD13 event-time archival inputs with committed bins and frozen graph.

    ``values[T,N,C]``, adjacency, channel_types, fit_service_mask and relative
    endpoints are numeric inputs. All names, epochs and audit stay trusted.
    ``cutoff_seconds`` makes an exact complete-bin materialization; extending
    this cache requires replaying verified source, never a cleaned full table.
    Qualification is established only by separately preserved run receipts.
    """
    from scripts.task_e.replay import (ReplayInputError, trace_replay,
                                       validate_event_clock)

    if (any(not isinstance(value, int) or value <= 0
            for value in (bin_seconds, warmup_seconds, fit_bins, cal_bins)) or
            warmup_seconds != (fit_bins + cal_bins) * bin_seconds):
        raise LoaderError("C5 warmup must match the declared fit/calibration bins")
    metrics = _frame(raw, "metrics")
    if metrics is None or "time" not in metrics or metrics.time.empty:
        raise LoaderError("C5 runtime origin unavailable without observed metric time")
    try:
        validate_event_clock(metrics.time, "metrics.time")
    except ReplayInputError as exc:
        raise LoaderError(str(exc)) from exc
    s0 = int(metrics.time.min())
    observed_end = int(metrics.time.max()) + 1
    complete_bins = (observed_end-s0) // bin_seconds
    end = s0 + complete_bins*bin_seconds
    if cutoff_seconds is not None:
        if (not isinstance(cutoff_seconds, int) or cutoff_seconds < warmup_seconds or
                cutoff_seconds % bin_seconds or cutoff_seconds > complete_bins * bin_seconds):
            raise LoaderError("C5 cutoff must be a complete observed bin after warmup")
        end = s0 + cutoff_seconds
        complete_bins = cutoff_seconds // bin_seconds
    if complete_bins < fit_bins + cal_bins:
        raise LoaderError("Insufficient archive for declared C5 warmup")
    try:
        replay = trace_replay(_frame(raw, "traces"), s0=s0, end=end,
                              bin_seconds=bin_seconds, fit_bins=fit_bins,
                              cal_bins=cal_bins, strategy=trace_strategy,
                              chunk_size=trace_chunk_size)
    except ReplayInputError as exc:
        raise LoaderError(str(exc)) from exc
    services = replay["service_names"]
    metric_values, ma = _metric_bins(metrics, services, s0, end, bin_seconds,
                                   int(np.ceil(bin_seconds*.5)), invalidate_channel=False)
    trace_values = replay["values"].T
    try:
        log_values, la = _counts(_frame(raw, "logs"), services, s0, end,
                                bin_seconds, "logs")
    except LoaderError as exc:
        log_values, la = _counts(None, services, s0, end, bin_seconds, "logs")
        la.update(error=str(exc), status="UNAVAILABLE_LOG_CLOCK_OR_SCHEMA")
    log_fit_presence = np.any(np.isfinite(log_values[:, :fit_bins]) &
                              (log_values[:, :fit_bins] > 0), axis=1)
    values = np.concatenate((metric_values, trace_values[:, None], log_values[:, None]), axis=1)
    return {"values": np.moveaxis(values, -1, 0), "adj": replay["adj"],
            "service_names": services, "channel_types": CHANNEL_TYPES.copy(),
            "fit_service_mask": replay["fit_service_mask"],
            "endpoints": np.arange(1, complete_bins+1, dtype=np.int64)*bin_seconds,
            "s0": s0, "audit": {"profile": "TD13-C5-EVENT-TIME",
              "qualification": "UNQUALIFIED_PENDING_EXTERNAL_TD13_REPLAY_RECEIPT",
              "metric": ma, "trace": replay["audit"], "log": la,
              "graph": replay["audit"]["graph"], "warmup_services": services,
              "fit_services": [name for name, yes in zip(services, replay["fit_service_mask"]) if yes],
              "trace_fit_presence": replay["audit"]["fit_presence"],
              "log_fit_presence": log_fit_presence.tolist(),
              "fit_bins": fit_bins, "cal_bins": cal_bins,
              "identical_trace_duplicates_collapsed": replay["audit"]["identical_duplicates_collapsed"],
              "trailing_partial_seconds": observed_end-end,
              "trace_conflict_policy": replay["audit"]["policy"]}}
