#!/usr/bin/env python3
"""Audit log schema and log/trace/metric joinability in downloaded RCAEval samples.

This audit deliberately inspects only local sample directories under raw-samples.
It neither downloads data nor opens any other subagent's report.  Results are
machine-readable and retain their sample-only scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DEFAULT_ROOT = Path(r"D:\Project\flash-ticket-rca-research")
RAW_RELATIVE = Path("datasets") / "rcaeval" / "raw-samples"
RESULT_RELATIVE = Path("results") / "rcaeval-subagent-e-logs-multimodal.json"

TRACE_ID_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])")
SPAN_ID_RE = re.compile(r"(?i)(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])")
TRACE_WORD_RE = re.compile(r"(?i)\btrace(?:[-_ ]?id)?\b")
SPAN_WORD_RE = re.compile(r"(?i)\bspan(?:[-_ ]?id)?\b")
TRACE_KEY_RE = re.compile(r"(?i)\b(?:trace[-_. ]?id|traceparent)\s*[:=]")
SPAN_KEY_RE = re.compile(r"(?i)\bspan[-_. ]?id\s*[:=]")
BRACKET_CONTEXT_RE = re.compile(
    r"(?i)\[[^,\]]+,(?P<trace>[0-9a-f]{32}),(?P<span>[0-9a-f]{16}),(?:true|false)\]"
)
ERROR_RE = re.compile(r"(?i)\b(exception|error|panic|fatal|caused by)\b")
KV_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_.-]*=[^\s]+")
HTTP_RE = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+\S+")
ISO_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T|\s)")
LEVEL_RE = {
    level: re.compile(rf"(?i)\b{level}\b")
    for level in ("DEBUG", "INFO", "WARN", "WARNING", "ERROR", "FATAL")
}


def json_value(value: Any) -> Any:
    """Convert pandas/numpy values to stable JSON values."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        return json_value(value.item())
    return str(value)


def as_strings(series: pd.Series) -> list[str]:
    return ["" if pd.isna(value) else str(value) for value in series]


def epoch_seconds_iso(value: int | float | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return datetime.fromtimestamp(int(value), tz=UTC).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def metric_entities(columns: list[str]) -> tuple[set[str], list[str]]:
    """Derive wide metric entity names by a documented suffix rule."""
    entities: set[str] = set()
    unparsed: list[str] = []
    patterns = (
        re.compile(r"^(?P<entity>.+)_(?:cpu|mem|diskio|socket|workload|error)$"),
        re.compile(r"^(?P<entity>.+)_latency(?:-(?:50|90))?$"),
    )
    for column in columns:
        if column == "time":
            continue
        match = next((pattern.match(column) for pattern in patterns if pattern.match(column)), None)
        if match:
            entities.add(match.group("entity"))
        else:
            unparsed.append(column)
    return entities, sorted(unparsed)


def count_full_json(messages: list[str]) -> tuple[int, int]:
    candidates = 0
    parsed = 0
    for message in messages:
        stripped = message.strip()
        if not stripped.startswith(("{", "[")):
            continue
        candidates += 1
        try:
            json.loads(stripped)
            parsed += 1
        except (TypeError, ValueError):
            pass
    return candidates, parsed


def analyze_logs(log_path: Path, trace_data: dict[str, Any] | None) -> dict[str, Any]:
    table = pq.read_table(log_path)
    frame = table.to_pandas()
    messages = as_strings(frame["message"])
    timestamps = frame["timestamp"]
    container_names = as_strings(frame["container_name"])

    trace_candidates = 0
    span_candidates = 0
    matching_trace_ids: set[str] = set()
    matching_span_ids: set[str] = set()
    bracket_trace_ids: set[str] = set()
    bracket_span_ids: set[str] = set()
    bracket_context_rows = 0
    trace_ids = trace_data["trace_ids"] if trace_data else set()
    span_ids = trace_data["span_ids"] if trace_data else set()
    for message in messages:
        found_trace_ids = {value.lower() for value in TRACE_ID_RE.findall(message)}
        found_span_ids = {value.lower() for value in SPAN_ID_RE.findall(message)}
        trace_candidates += len(found_trace_ids)
        span_candidates += len(found_span_ids)
        matching_trace_ids.update(found_trace_ids & trace_ids)
        matching_span_ids.update(found_span_ids & span_ids)
        bracket_matches = list(BRACKET_CONTEXT_RE.finditer(message))
        if bracket_matches:
            bracket_context_rows += 1
            bracket_trace_ids.update(match.group("trace").lower() for match in bracket_matches)
            bracket_span_ids.update(match.group("span").lower() for match in bracket_matches)

    json_candidates, valid_json = count_full_json(messages)
    message_lengths = [len(message) for message in messages]
    return {
        "path": str(log_path),
        "sha256": sha256(log_path),
        "schema": [{"name": field.name, "type": str(field.type)} for field in table.schema],
        "rows": int(len(frame)),
        "null_counts": {column: int(frame[column].isna().sum()) for column in frame.columns},
        "timestamp_epoch_seconds": {
            "min": int(timestamps.min()),
            "max": int(timestamps.max()),
            "min_utc": epoch_seconds_iso(timestamps.min()),
            "max_utc": epoch_seconds_iso(timestamps.max()),
            "distinct": int(timestamps.nunique(dropna=True)),
            "nondecreasing": bool(timestamps.is_monotonic_increasing),
        },
        "container_name": {
            "distinct": int(frame["container_name"].nunique(dropna=True)),
            "counts": dict(sorted((key, int(value)) for key, value in Counter(container_names).items() if key)),
        },
        "message_structure": {
            "null": int(frame["message"].isna().sum()),
            "empty_after_strip": int(sum(not message.strip() for message in messages)),
            "distinct": int(frame["message"].nunique(dropna=True)),
            "length_min": int(min(message_lengths)) if message_lengths else 0,
            "length_median": float(pd.Series(message_lengths).median()) if message_lengths else 0.0,
            "length_max": int(max(message_lengths)) if message_lengths else 0,
            "full_json_candidates": json_candidates,
            "full_json_valid": valid_json,
            "key_value_style_rows": int(sum(bool(KV_RE.search(message)) for message in messages)),
            "http_request_style_rows": int(sum(bool(HTTP_RE.search(message)) for message in messages)),
            "iso_timestamp_prefix_rows": int(sum(bool(ISO_PREFIX_RE.search(message)) for message in messages)),
            "level_token_rows": {
                level: int(sum(bool(pattern.search(message)) for message in messages))
                for level, pattern in LEVEL_RE.items()
            },
            "exception_or_error_rows": int(sum(bool(ERROR_RE.search(message)) for message in messages)),
        },
        "embedded_trace_or_span_evidence": {
            "explicit_trace_or_span_columns": [],
            "trace_word_rows": int(sum(bool(TRACE_WORD_RE.search(message)) for message in messages)),
            "span_word_rows": int(sum(bool(SPAN_WORD_RE.search(message)) for message in messages)),
            "trace_id_key_value_style_rows": int(sum(bool(TRACE_KEY_RE.search(message)) for message in messages)),
            "span_id_key_value_style_rows": int(sum(bool(SPAN_KEY_RE.search(message)) for message in messages)),
            "hex32_trace_id_candidates": trace_candidates,
            "hex16_span_id_candidates": span_candidates,
            "four_part_bracket_context_rows": bracket_context_rows,
            "four_part_bracket_context_unique_hex32": len(bracket_trace_ids),
            "four_part_bracket_context_unique_hex16": len(bracket_span_ids),
            "bracket_context_interpretation": "The bracket shape is raw text only. It is not called a trace/span key unless a coexisting trace artifact provides an exact match.",
            "exact_trace_id_matches_to_coexisting_traces": len(matching_trace_ids) if trace_data else None,
            "exact_span_id_matches_to_coexisting_traces": len(matching_span_ids) if trace_data else None,
        },
        "container_set": sorted({value for value in container_names if value}),
        "timestamp_set": {int(value) for value in timestamps.dropna().unique()},
        "timestamp_counts": Counter(int(value) for value in timestamps.dropna()),
    }


def analyze_traces(trace_path: Path) -> dict[str, Any]:
    parquet = pq.ParquetFile(trace_path)
    table = pq.read_table(trace_path, columns=["traceID", "spanID", "serviceName", "startTime", "startTimeMillis"])
    frame = table.to_pandas()
    start_seconds = (frame["startTimeMillis"] // 1000).astype("int64")
    start_time_matches_millis = frame["startTime"].floordiv(1000).eq(frame["startTimeMillis"])
    display_time = as_strings(pq.read_table(trace_path, columns=["time"]).to_pandas()["time"])
    return {
        "path": str(trace_path),
        "sha256": sha256(trace_path),
        "rows": int(len(frame)),
        "schema": [{"name": field.name, "type": str(field.type)} for field in parquet.schema_arrow],
        "null_counts": {column: int(frame[column].isna().sum()) for column in frame.columns},
        "service_set": sorted({str(value) for value in frame["serviceName"].dropna().unique()}),
        "trace_ids": {str(value).lower() for value in frame["traceID"].dropna().unique()},
        "span_ids": {str(value).lower() for value in frame["spanID"].dropna().unique()},
        "timestamp_second_set": {int(value) for value in start_seconds.unique()},
        "timestamp_second_counts": Counter(int(value) for value in start_seconds),
        "timestamp_epoch_seconds": {
            "min": int(start_seconds.min()),
            "max": int(start_seconds.max()),
            "min_utc": epoch_seconds_iso(start_seconds.min()),
            "max_utc": epoch_seconds_iso(start_seconds.max()),
        },
        "timestamp_unit_check": {
            "startTime_div_1000_equals_startTimeMillis_rows": int(start_time_matches_millis.sum()),
            "total_rows": int(len(frame)),
            "interpretation": "For all matching rows, startTime is consistent with microseconds and startTimeMillis with milliseconds; only startTimeMillis is used for the documented second-bin rule.",
        },
        "display_time_string": {
            "non_null": int(sum(bool(value) for value in display_time)),
            "distinct": len(set(display_time)),
            "hh_mm_format_rows": int(sum(bool(re.fullmatch(r"\d{2}:\d{2}", value)) for value in display_time)),
            "interpretation": "The string field time is a coarse display field and is not used as a cross-modal key.",
        },
    }


def analyze_metrics(metric_path: Path) -> dict[str, Any]:
    parquet = pq.ParquetFile(metric_path)
    columns = parquet.schema_arrow.names
    frame = pq.read_table(metric_path, columns=["time"]).to_pandas()
    entities, unparsed = metric_entities(columns)
    return {
        "path": str(metric_path),
        "sha256": sha256(metric_path),
        "rows": int(len(frame)),
        "columns": len(columns),
        "metric_column_names": columns,
        "metric_entity_derivation_rule": "^(entity)_(cpu|mem|diskio|socket|workload|error)$ or ^(entity)_latency(-50|-90)?$",
        "metric_entity_set": sorted(entities),
        "unparsed_value_columns": unparsed,
        "timestamp_set": {int(value) for value in frame["time"].dropna().unique()},
        "timestamp_epoch_seconds": {
            "min": int(frame["time"].min()),
            "max": int(frame["time"].max()),
            "min_utc": epoch_seconds_iso(frame["time"].min()),
            "max_utc": epoch_seconds_iso(frame["time"].max()),
        },
    }


def root_cause_leakage(case_dir: Path) -> dict[str, Any]:
    path = case_dir / "root_cause.txt"
    if not path.exists():
        return {"present": False, "classification": "NOT_PRESENT_IN_THIS_RAW_SAMPLE"}
    content = path.read_bytes()
    return {
        "present": True,
        "path": str(path),
        "bytes": len(content),
        "nonempty_line_count": sum(bool(line.strip()) for line in content.splitlines()),
        "sha256": hashlib.sha256(content).hexdigest(),
        "classification": "FORBIDDEN_MODEL_INPUT",
        "reason": "Case-level root-cause label artifact; retained only for evaluation/provenance, not read into model features.",
    }


def summarize_case(case_dir: Path) -> dict[str, Any]:
    trace_path = case_dir / "traces.parquet"
    metric_path = case_dir / "metrics.parquet"
    log_path = case_dir / "logs.parquet"

    traces = analyze_traces(trace_path) if trace_path.exists() else None
    metrics = analyze_metrics(metric_path) if metric_path.exists() else None
    logs = analyze_logs(log_path, traces) if log_path.exists() else None

    joins: dict[str, Any] = {}
    if logs and metrics:
        metric_times = metrics["timestamp_set"]
        log_times = logs["timestamp_set"]
        containers = set(logs["container_set"])
        entities = set(metrics["metric_entity_set"])
        matching_times = log_times & metric_times
        timestamp_coverage = len(matching_times)
        matching_rows = sum(logs["timestamp_counts"][value] for value in matching_times)
        joins["logs_to_metrics"] = {
            "classification": "DIRECT KEY JOIN",
            "scope": "Direct (timestamp, exact entity name) alignment at 1-second service/container bins only; not an event-level or causal join.",
            "time_key": "logs.timestamp == metrics.time (both raw epoch seconds)",
            "distinct_log_seconds": len(log_times),
            "distinct_log_seconds_with_exact_metric_time": timestamp_coverage,
            "log_rows_with_exact_metric_time": matching_rows,
            "total_log_rows": logs["rows"],
            "exact_container_to_metric_entity_overlap": sorted(containers & entities),
            "log_containers_without_exact_metric_entity": sorted(containers - entities),
            "metric_entities_without_log_container": sorted(entities - containers),
            "entity_mapping_note": "Metric data are wide. Entity names are derived only by the documented suffix rule in this script before exact string equality.",
        }
    else:
        missing = []
        if not logs:
            missing.append("logs.parquet")
        if not metrics:
            missing.append("metrics.parquet")
        joins["logs_to_metrics"] = {
            "classification": "NOT JOINABLE",
            "reason": f"This selected raw sample lacks {', '.join(missing)}.",
        }

    if logs and traces:
        log_times = logs["timestamp_set"]
        trace_times = traces["timestamp_second_set"]
        containers = set(logs["container_set"])
        services = set(traces["service_set"])
        matching_times = log_times & trace_times
        matching_rows = sum(logs["timestamp_counts"][value] for value in matching_times)
        has_direct_id = bool(
            logs["embedded_trace_or_span_evidence"]["exact_trace_id_matches_to_coexisting_traces"]
            or logs["embedded_trace_or_span_evidence"]["exact_span_id_matches_to_coexisting_traces"]
        )
        exact_service_overlap = containers & services
        if has_direct_id:
            classification = "DIRECT KEY JOIN"
        elif matching_times and exact_service_overlap:
            classification = "SERVICE + TIME WINDOW"
        elif matching_times:
            classification = "TIME WINDOW ONLY"
        else:
            classification = "NOT JOINABLE"
        joins["logs_to_traces"] = {
            "classification": classification,
            "reason": "No explicit trace/span fields in logs.parquet and no exact traceID/spanID token match was found; logs are only second-resolution while traces are finer-grained.",
            "time_alignment_rule": "floor(traces.startTimeMillis / 1000) == logs.timestamp",
            "distinct_log_seconds": len(log_times),
            "distinct_log_seconds_with_trace_start_in_same_second": len(matching_times),
            "log_rows_in_a_second_that_contains_at_least_one_trace_start": matching_rows,
            "exact_container_to_trace_service_overlap": sorted(containers & services),
            "log_containers_without_exact_trace_service": sorted(containers - services),
            "trace_services_without_log_container": sorted(services - containers),
            "exact_trace_id_matches": logs["embedded_trace_or_span_evidence"]["exact_trace_id_matches_to_coexisting_traces"],
            "exact_span_id_matches": logs["embedded_trace_or_span_evidence"]["exact_span_id_matches_to_coexisting_traces"],
        }
    else:
        missing = []
        if not logs:
            missing.append("logs.parquet")
        if not traces:
            missing.append("traces.parquet")
        joins["logs_to_traces"] = {
            "classification": "NOT JOINABLE",
            "reason": f"This selected raw sample lacks {', '.join(missing)}.",
        }

    if metrics and traces:
        metric_times = metrics["timestamp_set"]
        trace_times = traces["timestamp_second_set"]
        entities = set(metrics["metric_entity_set"])
        services = set(traces["service_set"])
        matching_times = metric_times & trace_times
        exact_service_overlap = entities & services
        if matching_times and exact_service_overlap:
            classification = "SERVICE + TIME WINDOW"
        elif matching_times:
            classification = "TIME WINDOW ONLY"
        else:
            classification = "NOT JOINABLE"
        joins["metrics_to_traces"] = {
            "classification": classification,
            "reason": "Metrics contain epoch-second aggregate rows and entity-bearing wide column names; traces carry fine-grained span times and no metric-row identifier.",
            "time_alignment_rule": "metrics.time == floor(traces.startTimeMillis / 1000)",
            "distinct_metric_seconds": len(metric_times),
            "distinct_metric_seconds_with_trace_start_in_same_second": len(matching_times),
            "exact_metric_entity_to_trace_service_overlap": sorted(exact_service_overlap),
            "metric_entities_without_exact_trace_service": sorted(entities - services),
            "trace_services_without_exact_metric_entity": sorted(services - entities),
        }
    else:
        missing = []
        if not metrics:
            missing.append("metrics.parquet")
        if not traces:
            missing.append("traces.parquet")
        joins["metrics_to_traces"] = {
            "classification": "NOT JOINABLE",
            "reason": f"This selected raw sample lacks {', '.join(missing)}.",
        }

    # Remove internal sets that cannot be serialized and are not needed in the report.
    for artifact in (logs, traces, metrics):
        if artifact:
            for key in (
                "timestamp_set",
                "timestamp_counts",
                "trace_ids",
                "span_ids",
                "timestamp_second_set",
                "timestamp_second_counts",
            ):
                artifact.pop(key, None)

    return {
        "case_id": case_dir.name,
        "available_files": sorted(path.name for path in case_dir.iterdir() if path.is_file()),
        "logs": logs,
        "traces": traces,
        "metrics": metrics,
        "joins": joins,
        "root_cause_label_leakage": root_cause_leakage(case_dir),
        "case_identifier_leakage_control": {
            "classification": "FORBIDDEN_MODEL_INPUT",
            "reason": "Directory/case identifiers are provenance fields and can encode human-readable fault or target tokens; do not expose them to a model.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    raw_root = workspace / RAW_RELATIVE
    output = args.output.resolve() if args.output else workspace / RESULT_RELATIVE
    if not raw_root.is_dir():
        raise SystemExit(f"raw-samples directory is missing: {raw_root}")

    case_dirs = sorted(
        path for path in raw_root.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    report = {
        "audit": "Subagent E — logs and multimodal joinability",
        "scope": "RAW SAMPLE FINDING: only the locally downloaded selected sample directories listed below.",
        "raw_root": str(raw_root),
        "case_count": len(case_dirs),
        "cases": [summarize_case(case_dir) for case_dir in case_dirs],
        "global_constraints": [
            "No event-level log-to-trace linkage is claimed without an explicit trace/span reference.",
            "Equal epoch-second timestamps support bin alignment only, not causal or request-level correlation.",
            "root_cause.txt and case directory identifiers are forbidden model inputs.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "case_count": len(case_dirs)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
