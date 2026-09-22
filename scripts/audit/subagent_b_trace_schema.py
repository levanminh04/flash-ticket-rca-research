"""Deterministic raw-schema audit for Task B / Subagent B.

Reads only trace-bearing files listed in the six-case raw-download manifest.
It does not download data or infer architecture/causality.  The JSON result is
written beneath the dedicated research workspace for reproducible review.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


WORKSPACE = Path(__file__).resolve().parents[2]
RAW_ROOT = WORKSPACE / "datasets" / "rcaeval" / "raw-samples"
MANIFEST_PATH = RAW_ROOT / "raw-download-manifest.json"
PLAN_PATH = WORKSPACE / "audits" / "rcaeval" / "raw-sample-plan.json"
OUTPUT_PATH = WORKSPACE / "results" / "subagent-b-trace-schema.json"

STRING_COLUMNS = [
    "time",
    "traceID",
    "spanID",
    "serviceName",
    "methodName",
    "operationName",
    "parentSpanID",
]
INTEGER_COLUMNS = ["startTimeMillis", "startTime", "duration", "statusCode"]
ALL_COLUMNS = STRING_COLUMNS + INTEGER_COLUMNS


def raw_value(value: Any) -> Any:
    """Convert Arrow scalar values without turning a null into text."""
    return value.as_py() if value is not None else None


def string_presence(value: Any) -> str:
    if value is None:
        return "null"
    if value == "":
        return "empty"
    return "value"


def safe_divide(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None


def ranked(counter: Counter, limit: int = 15) -> list[dict[str, Any]]:
    return [{"value": str(key), "rows": int(value)} for key, value in counter.most_common(limit)]


def analyze_trace_file(case: str, path: Path) -> dict[str, Any]:
    parquet_file = pq.ParquetFile(path)
    schema = [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in parquet_file.schema_arrow
    ]
    observed_columns = [field["name"] for field in schema]
    unexpected_columns = sorted(set(observed_columns) - set(ALL_COLUMNS))
    missing_expected_columns = sorted(set(ALL_COLUMNS) - set(observed_columns))

    row_count = 0
    null_counts: Counter[str] = Counter()
    empty_counts: Counter[str] = Counter()
    distinct_values: dict[str, set[Any]] = {column: set() for column in ALL_COLUMNS}
    value_counts: dict[str, Counter] = {column: Counter() for column in ALL_COLUMNS}
    numeric_min: dict[str, int | None] = {column: None for column in INTEGER_COLUMNS}
    numeric_max: dict[str, int | None] = {column: None for column in INTEGER_COLUMNS}
    negative_duration_rows = 0
    zero_duration_rows = 0
    starttime_vs_millis = Counter()

    # Composite (traceID, spanID) is the conservative identity for resolving
    # parentSpanID.  The parent field does not carry a trace ID itself.
    composite_keys: set[str] = set()
    span_ids_global: set[str] = set()
    key_details: dict[str, tuple[int | None, int | None, str | None, str | None]] = {}
    parent_rows: list[tuple[str, str, str, int | None, int | None, str | None, str | None]] = []
    duplicate_composite_rows = 0
    duplicate_spanid_global_rows = 0
    trace_ids: set[str] = set()
    service_operation_pairs: set[tuple[str, str]] = set()
    operation_services: dict[str, set[str]] = defaultdict(set)
    service_operations: dict[str, set[str]] = defaultdict(set)
    operation_text_patterns: dict[str, Counter] = {
        "http_verb_at_start": Counter(),
        "grpc_literal": Counter(),
        "database_like_literal": Counter(),
        "messaging_like_literal": Counter(),
    }
    operation_text_examples: dict[str, Counter] = {
        "http_verb_at_start": Counter(),
        "grpc_literal": Counter(),
        "database_like_literal": Counter(),
        "messaging_like_literal": Counter(),
    }

    selected_columns = [column for column in ALL_COLUMNS if column in observed_columns]
    for batch in parquet_file.iter_batches(batch_size=65536, columns=selected_columns):
        values = batch.to_pydict()
        rows = batch.num_rows
        for index in range(rows):
            row_count += 1
            row: dict[str, Any] = {column: values[column][index] for column in selected_columns}
            for column in selected_columns:
                value = row[column]
                if value is None:
                    null_counts[column] += 1
                    continue
                if column in STRING_COLUMNS and value == "":
                    empty_counts[column] += 1
                    continue
                distinct_values[column].add(value)
                value_counts[column][value] += 1
                if column in INTEGER_COLUMNS:
                    numeric_min[column] = value if numeric_min[column] is None else min(numeric_min[column], value)
                    numeric_max[column] = value if numeric_max[column] is None else max(numeric_max[column], value)

            duration = row.get("duration")
            if duration is not None:
                if duration < 0:
                    negative_duration_rows += 1
                if duration == 0:
                    zero_duration_rows += 1

            start_time = row.get("startTime")
            start_time_millis = row.get("startTimeMillis")
            if start_time is not None and start_time_millis is not None:
                starttime_vs_millis["both_present"] += 1
                if start_time // 1000 == start_time_millis:
                    starttime_vs_millis["startTime_div_1000_equals_startTimeMillis"] += 1
                else:
                    starttime_vs_millis["startTime_div_1000_differs"] += 1

            trace_id = row.get("traceID")
            span_id = row.get("spanID")
            parent_span_id = row.get("parentSpanID")
            service = row.get("serviceName")
            operation = row.get("operationName")
            if trace_id not in (None, ""):
                trace_ids.add(trace_id)
            if service not in (None, "") and operation not in (None, ""):
                service_operation_pairs.add((service, operation))
                operation_services[operation].add(service)
                service_operations[service].add(operation)
            if operation not in (None, ""):
                operation_lower = operation.lower()
                textual_matches = {
                    "http_verb_at_start": bool(re.match(r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)(?:\\s|$)", operation)),
                    "grpc_literal": "grpc" in operation_lower,
                    "database_like_literal": bool(re.search(r"repository|\\bfind\\b|\\bupdate\\b|\\bsave\\b|\\bdelete\\b|getmore", operation_lower)),
                    "messaging_like_literal": bool(re.search(r"kafka|rabbit|queue|topic|publish|consume|produce", operation_lower)),
                }
                for pattern_name, is_match in textual_matches.items():
                    if is_match:
                        operation_text_patterns[pattern_name]["matched_rows"] += 1
                        operation_text_examples[pattern_name][operation] += 1

            if trace_id not in (None, "") and span_id not in (None, ""):
                composite_key = f"{trace_id}\x1f{span_id}"
                if composite_key in composite_keys:
                    duplicate_composite_rows += 1
                else:
                    composite_keys.add(composite_key)
                    key_details[composite_key] = (start_time, duration, service, operation)
                if span_id in span_ids_global:
                    duplicate_spanid_global_rows += 1
                else:
                    span_ids_global.add(span_id)
                if parent_span_id not in (None, ""):
                    parent_rows.append((
                        composite_key,
                        f"{trace_id}\x1f{parent_span_id}",
                        parent_span_id,
                        start_time,
                        duration,
                        service,
                        operation,
                    ))

    resolved_parents = 0
    unresolved_parents = 0
    parent_resolved_global_spanid = 0
    parent_resolved_only_outside_child_trace = 0
    self_parent_rows = 0
    parent_child_same_service = 0
    parent_child_cross_service = 0
    parent_child_unknown_service = 0
    child_start_before_parent = 0
    child_end_after_parent = 0
    timing_comparable = 0
    parent_child_service_pairs: Counter = Counter()
    for (
        child_key,
        parent_key,
        parent_span_id,
        child_start,
        child_duration,
        child_service,
        _child_operation,
    ) in parent_rows:
        if parent_span_id in span_ids_global:
            parent_resolved_global_spanid += 1
        parent = key_details.get(parent_key)
        if parent is None:
            unresolved_parents += 1
            if parent_span_id in span_ids_global:
                parent_resolved_only_outside_child_trace += 1
            continue
        resolved_parents += 1
        if child_key == parent_key:
            self_parent_rows += 1
        parent_start, parent_duration, parent_service, _parent_operation = parent
        if child_service in (None, "") or parent_service in (None, ""):
            parent_child_unknown_service += 1
        elif child_service == parent_service:
            parent_child_same_service += 1
        else:
            parent_child_cross_service += 1
            parent_child_service_pairs[(child_service, parent_service)] += 1
        if (
            child_start is not None
            and child_duration is not None
            and parent_start is not None
            and parent_duration is not None
        ):
            timing_comparable += 1
            if child_start < parent_start:
                child_start_before_parent += 1
            if child_start + child_duration > parent_start + parent_duration:
                child_end_after_parent += 1

    no_parent_rows = row_count - len(parent_rows)
    exact_operation_reused_across_services = {
        operation: sorted(services)
        for operation, services in operation_services.items()
        if len(services) > 1
    }
    operation_cardinality_by_service = [
        {"serviceName": service, "distinct_operationName": len(operations)}
        for service, operations in sorted(service_operations.items())
    ]

    return {
        "case": case,
        "local_path": str(path),
        "file_bytes": path.stat().st_size,
        "parquet": {
            "row_count": row_count,
            "row_groups": parquet_file.metadata.num_row_groups,
            "schema": schema,
            "unexpected_columns": unexpected_columns,
            "missing_expected_columns": missing_expected_columns,
        },
        "column_profile": {
            column: {
                "null_rows": int(null_counts[column]),
                "empty_string_rows": int(empty_counts[column]) if column in STRING_COLUMNS else None,
                "non_null_non_empty_distinct": len(distinct_values[column]),
                "top_values": ranked(value_counts[column]),
            }
            for column in selected_columns
        },
        "identity_and_parent_resolution": {
            "distinct_traceID": len(trace_ids),
            "distinct_spanID_global": len(span_ids_global),
            "distinct_traceID_spanID_composite": len(composite_keys),
            "duplicate_traceID_spanID_rows": duplicate_composite_rows,
            "duplicate_spanID_global_rows": duplicate_spanid_global_rows,
            "rows_with_nonempty_parentSpanID": len(parent_rows),
            "rows_with_null_or_empty_parentSpanID": no_parent_rows,
            "parent_resolved_same_traceID": resolved_parents,
            "parent_unresolved_same_traceID": unresolved_parents,
            "parent_resolution_rate": safe_divide(resolved_parents, len(parent_rows)),
            "parent_resolved_anywhere_in_raw_file_by_spanID": parent_resolved_global_spanid,
            "parent_resolved_only_outside_child_traceID": parent_resolved_only_outside_child_trace,
            "self_parent_rows": self_parent_rows,
            "resolved_parent_child_same_service": parent_child_same_service,
            "resolved_parent_child_cross_service": parent_child_cross_service,
            "resolved_parent_child_unknown_service": parent_child_unknown_service,
            "top_cross_service_child_parent_pairs": [
                {"child_service": child, "parent_service": parent, "rows": count}
                for (child, parent), count in parent_child_service_pairs.most_common(15)
            ],
        },
        "timing": {
            "numeric_min": numeric_min,
            "numeric_max": numeric_max,
            "negative_duration_rows": negative_duration_rows,
            "zero_duration_rows": zero_duration_rows,
            "startTime_vs_startTimeMillis": dict(starttime_vs_millis),
            "resolved_parent_child_timing_comparable": timing_comparable,
            "resolved_child_start_before_parent_start": child_start_before_parent,
            "resolved_child_end_after_parent_end": child_end_after_parent,
        },
        "operation_identity": {
            "distinct_service_operationName_pairs": len(service_operation_pairs),
            "distinct_operationName_reused_across_more_than_one_service": len(exact_operation_reused_across_services),
            "examples_exact_operationName_reused_across_services": [
                {"operationName": operation, "services": services}
                for operation, services in sorted(exact_operation_reused_across_services.items())[:25]
            ],
            "operation_cardinality_by_service": operation_cardinality_by_service,
        },
        "structured_attribute_assessment": {
            "http": "No dedicated HTTP method, URL, route, status, host, or peer column exists in this Parquet schema.",
            "rpc": "No dedicated RPC system/service/method or peer column exists in this Parquet schema.",
            "database": "No dedicated database system/operation/statement/resource column exists in this Parquet schema.",
            "messaging": "No dedicated messaging system/destination/operation column exists in this Parquet schema.",
            "resource_peer": "No dedicated resource attributes, host, container, pod, process, or peer attributes column exists in this Parquet schema.",
            "caution": "Text patterns inside operationName/methodName are raw strings, not structured semantic attributes.",
            "operationName_textual_pattern_counts": {
                pattern: {
                    "matched_rows": counter["matched_rows"],
                    "top_exact_operationName_values": ranked(operation_text_examples[pattern], limit=10),
                }
                for pattern, counter in operation_text_patterns.items()
            },
        },
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    plan_cases = {item["case"] for item in plan["cases"]}
    trace_files: list[tuple[str, Path]] = []
    cases_without_trace_file: list[str] = []
    for item in manifest["cases"]:
        case = item["case"]
        if case not in plan_cases:
            raise RuntimeError(f"Manifest case is outside six-case plan: {case}")
        file_entries = [entry for entry in item["files"] if entry["remote_file"].endswith("/traces.parquet")]
        if not file_entries:
            cases_without_trace_file.append(case)
            continue
        if len(file_entries) != 1:
            raise RuntimeError(f"Expected one traces.parquet file for {case}, found {len(file_entries)}")
        trace_path = Path(file_entries[0]["local_path"])
        if not trace_path.is_file():
            raise FileNotFoundError(trace_path)
        trace_files.append((case, trace_path))

    if not trace_files:
        raise RuntimeError("No trace-bearing raw sample is available")

    cases = [analyze_trace_file(case, path) for case, path in trace_files]
    result = {
        "audit": "Task B / Subagent B — Trace Schema Auditor",
        "scope": "RAW SAMPLE FINDING — only trace-bearing files from the six-case raw-sample plan; not a dataset-wide claim.",
        "source": manifest["source"],
        "plan_path": str(PLAN_PATH),
        "manifest_path": str(MANIFEST_PATH),
        "trace_bearing_cases": [case for case, _path in trace_files],
        "planned_cases_without_downloaded_traces_parquet": cases_without_trace_file,
        "checks": [
            "Parquet schema and row count from pyarrow.parquet.ParquetFile",
            "Column null/empty/distinct/top-value counts streamed from raw records",
            "Parent resolution uses exact (traceID, parentSpanID) lookup within the same raw file",
            "No data downloaded, transformed, or used to infer architecture or causal propagation",
        ],
        "cases": cases,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
