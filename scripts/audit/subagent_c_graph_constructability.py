"""Independent raw-sample graph-constructability audit for RCAEval Task B.

Scope is deliberately limited to the six cases named in
audits/rcaeval/raw-sample-plan.json.  It neither downloads data nor reads
other auditors' reports.  The JSON output is evidence for the accompanying
Subagent C report, not a dataset-wide statistic.
"""

from __future__ import annotations

import collections
import json
import re
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


WORKSPACE = Path(__file__).resolve().parents[2]
PLAN_PATH = WORKSPACE / "audits" / "rcaeval" / "raw-sample-plan.json"
RAW_ROOT = WORKSPACE / "datasets" / "rcaeval" / "raw-samples"
OUTPUT_PATH = (
    WORKSPACE
    / "audits"
    / "rcaeval"
    / "subagent-c-graph-constructability-evidence.json"
)

TRACE_COLUMNS = [
    "traceID",
    "spanID",
    "serviceName",
    "methodName",
    "operationName",
    "parentSpanID",
    "startTime",
    "duration",
]
HEX_RE = re.compile(r"^[0-9a-f]+$")


def is_present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def bounded_examples(values: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return values[:limit]


def sorted_counter_items(counter: collections.Counter[Any], limit: int | None = None) -> list[tuple[Any, int]]:
    """Stable count ordering so repeated runs yield the same evidence structure."""
    items = sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))
    return items if limit is None else items[:limit]


def count_string_hints(operation_names: collections.Counter[str]) -> dict[str, int]:
    """Count labels that merely *look like* protocols/resources, without inferring them."""
    tokens = [
        "grpc",
        "http",
        "kafka",
        "rabbit",
        "queue",
        "topic",
        "redis",
        "mongo",
        "mysql",
        "postgres",
        "sql",
        "jdbc",
        "amqp",
        "messag",
    ]
    return {
        token: sum(count for name, count in operation_names.items() if token in name.lower())
        for token in tokens
    }


def audit_trace_case(case_id: str, trace_path: Path) -> dict[str, Any]:
    parquet_file = pq.ParquetFile(trace_path)
    schema_names = parquet_file.schema_arrow.names
    missing_columns = [name for name in TRACE_COLUMNS if name not in schema_names]
    if missing_columns:
        raise RuntimeError(f"{case_id}: expected trace fields absent: {missing_columns}")

    table = parquet_file.read(columns=TRACE_COLUMNS)
    columns = table.to_pydict()
    row_count = table.num_rows

    missing = collections.Counter()
    service_counts: collections.Counter[str] = collections.Counter()
    operation_counts: collections.Counter[str] = collections.Counter()
    method_counts: collections.Counter[str] = collections.Counter()
    service_operation_counts: collections.Counter[tuple[str, str]] = collections.Counter()
    operation_services: dict[str, set[str]] = collections.defaultdict(set)
    service_operations: dict[str, set[str]] = collections.defaultdict(set)
    id_length_counts: dict[str, collections.Counter[int]] = {
        "traceID": collections.Counter(),
        "spanID": collections.Counter(),
        "parentSpanID": collections.Counter(),
    }
    id_non_hex = collections.Counter()

    # A composite key is required because a span ID has no declared global scope.
    span_map: dict[tuple[str, str], tuple[str | None, str | None, int | None, int | None]] = {}
    composite_duplicate_count = 0
    global_span_ids: set[str] = set()
    global_span_duplicate_count = 0
    child_records: list[tuple[str, str, str, str | None, str | None, int | None, int | None]] = []

    for index in range(row_count):
        trace_id = columns["traceID"][index]
        span_id = columns["spanID"][index]
        service = columns["serviceName"][index]
        method = columns["methodName"][index]
        operation = columns["operationName"][index]
        parent_span_id = columns["parentSpanID"][index]
        start_time = columns["startTime"][index]
        duration = columns["duration"][index]

        for field_name, value in (
            ("traceID", trace_id),
            ("spanID", span_id),
            ("serviceName", service),
            ("methodName", method),
            ("operationName", operation),
            ("parentSpanID", parent_span_id),
            ("startTime", start_time),
            ("duration", duration),
        ):
            if not is_present(value):
                missing[field_name] += 1

        for id_name, value in (
            ("traceID", trace_id),
            ("spanID", span_id),
            ("parentSpanID", parent_span_id),
        ):
            if is_present(value):
                text = str(value)
                id_length_counts[id_name][len(text)] += 1
                if not HEX_RE.fullmatch(text):
                    id_non_hex[id_name] += 1

        if is_present(service):
            service_text = str(service)
            service_counts[service_text] += 1
        else:
            service_text = None
        if is_present(operation):
            operation_text = str(operation)
            operation_counts[operation_text] += 1
        else:
            operation_text = None
        if is_present(method):
            method_counts[str(method)] += 1

        if service_text is not None and operation_text is not None:
            service_operation_counts[(service_text, operation_text)] += 1
            operation_services[operation_text].add(service_text)
            service_operations[service_text].add(operation_text)

        if is_present(trace_id) and is_present(span_id):
            composite_key = (str(trace_id), str(span_id))
            if composite_key in span_map:
                composite_duplicate_count += 1
            else:
                span_map[composite_key] = (service_text, operation_text, start_time, duration)

            span_text = str(span_id)
            if span_text in global_span_ids:
                global_span_duplicate_count += 1
            else:
                global_span_ids.add(span_text)

        if is_present(trace_id) and is_present(span_id):
            child_records.append(
                (
                    str(trace_id),
                    str(span_id),
                    str(parent_span_id) if is_present(parent_span_id) else "",
                    service_text,
                    operation_text,
                    start_time,
                    duration,
                )
            )

    parent_present = 0
    parent_found_same_trace = 0
    parent_missing_same_trace = 0
    parent_self_reference = 0
    same_service_parent_child = 0
    cross_service_parent_child = 0
    unknown_service_parent_child = 0
    service_call_counts: collections.Counter[tuple[str, str]] = collections.Counter()
    service_call_noncontainment_counts: collections.Counter[tuple[str, str]] = collections.Counter()
    temporal_containment = 0
    temporal_noncontainment = 0
    temporal_uncheckable = 0
    cross_service_examples: list[dict[str, Any]] = []
    unresolved_parent_examples: list[dict[str, Any]] = []
    temporal_noncontainment_examples: list[dict[str, Any]] = []

    for (
        trace_id,
        child_span_id,
        parent_span_id,
        child_service,
        child_operation,
        child_start,
        child_duration,
    ) in child_records:
        if not parent_span_id:
            continue
        parent_present += 1
        parent = span_map.get((trace_id, parent_span_id))
        if parent is None:
            parent_missing_same_trace += 1
            if len(unresolved_parent_examples) < 8:
                unresolved_parent_examples.append(
                    {
                        "traceID": trace_id,
                        "childSpanID": child_span_id,
                        "parentSpanID": parent_span_id,
                        "childService": child_service,
                        "childOperation": child_operation,
                    }
                )
            continue

        parent_found_same_trace += 1
        parent_service, parent_operation, parent_start, parent_duration = parent
        if child_span_id == parent_span_id:
            parent_self_reference += 1
        if child_service is None or parent_service is None:
            unknown_service_parent_child += 1
        elif child_service == parent_service:
            same_service_parent_child += 1
        else:
            cross_service_parent_child += 1
            service_call_counts[(parent_service, child_service)] += 1
            if len(cross_service_examples) < 8:
                cross_service_examples.append(
                    {
                        "traceID": trace_id,
                        "parentSpanID": parent_span_id,
                        "parentService": parent_service,
                        "parentOperation": parent_operation,
                        "childSpanID": child_span_id,
                        "childService": child_service,
                        "childOperation": child_operation,
                    }
                )

        # This tests numerical timestamp compatibility only.  It is not a
        # proof that the parent caused the child or that the edge is a network call.
        timing_values = (parent_start, parent_duration, child_start, child_duration)
        if not all(value is not None for value in timing_values):
            temporal_uncheckable += 1
        else:
            parent_end = int(parent_start) + int(parent_duration)
            child_end = int(child_start) + int(child_duration)
            if int(parent_start) <= int(child_start) and parent_end >= child_end:
                temporal_containment += 1
            else:
                temporal_noncontainment += 1
                if parent_service is not None and child_service is not None and parent_service != child_service:
                    service_call_noncontainment_counts[(parent_service, child_service)] += 1
                if len(temporal_noncontainment_examples) < 8:
                    temporal_noncontainment_examples.append(
                        {
                            "traceID": trace_id,
                            "parentSpanID": parent_span_id,
                            "childSpanID": child_span_id,
                            "parentStart": parent_start,
                            "parentDuration": parent_duration,
                            "childStart": child_start,
                            "childDuration": child_duration,
                        }
                    )

    multi_service_operation_names = {
        name: sorted(services)
        for name, services in operation_services.items()
        if len(services) > 1
    }
    per_service_operation_cardinality = {
        service: len(operations)
        for service, operations in sorted(service_operations.items())
    }

    return {
        "case": case_id,
        "trace_file": str(trace_path),
        "rows": row_count,
        "schema": [{"name": field.name, "type": str(field.type)} for field in parquet_file.schema_arrow],
        "field_null_counts": dict(sorted(missing.items())),
        "service": {
            "distinct_non_null": len(service_counts),
            "top_by_span_count": sorted_counter_items(service_counts, 20),
        },
        "operation": {
            "distinct_non_null": len(operation_counts),
            "top_by_span_count": sorted_counter_items(operation_counts, 20),
            "distinct_service_operation_pairs": len(service_operation_counts),
            "per_service_distinct_operation_count": per_service_operation_cardinality,
            "operation_names_observed_in_multiple_services": multi_service_operation_names,
            "protocol_or_resource_word_occurrence_in_raw_operation_labels": count_string_hints(operation_counts),
        },
        "method": {
            "distinct_non_null": len(method_counts),
            "top_by_span_count": sorted_counter_items(method_counts, 20),
        },
        "id_integrity": {
            "composite_traceID_spanID_duplicate_rows": composite_duplicate_count,
            "spanID_duplicate_rows_global_scope_only": global_span_duplicate_count,
            "id_length_counts": {
                name: dict(sorted(counts.items())) for name, counts in id_length_counts.items()
            },
            "non_hex_id_value_counts": dict(sorted(id_non_hex.items())),
        },
        "parent_reference_integrity": {
            "parentSpanID_present": parent_present,
            "parent_found_with_same_traceID": parent_found_same_trace,
            "parent_not_found_with_same_traceID": parent_missing_same_trace,
            "self_references": parent_self_reference,
            "same_service_parent_child": same_service_parent_child,
            "cross_service_parent_child": cross_service_parent_child,
            "unknown_service_parent_child": unknown_service_parent_child,
            "numeric_time_containment": temporal_containment,
            "numeric_time_noncontainment": temporal_noncontainment,
            "numeric_time_uncheckable": temporal_uncheckable,
            "candidate_cross_service_call_edges": [
                {
                    "parent_service": parent_service,
                    "child_service": child_service,
                    "parent_child_span_pairs": count,
                    "numeric_time_noncontainment": service_call_noncontainment_counts[
                        (parent_service, child_service)
                    ],
                }
                for (parent_service, child_service), count in sorted_counter_items(service_call_counts)
            ],
            "cross_service_examples": bounded_examples(cross_service_examples),
            "unresolved_parent_examples": bounded_examples(unresolved_parent_examples),
            "temporal_noncontainment_examples": bounded_examples(temporal_noncontainment_examples),
        },
    }


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    selected_cases = [entry["case"] for entry in plan["cases"]]
    result: dict[str, Any] = {
        "audit_role": "Subagent C — graph constructability",
        "scope": "RAW SAMPLE FINDING only; six cases named in raw-sample-plan.json",
        "selected_cases": selected_cases,
        "trace_cases": {},
        "selected_cases_without_traces_parquet": [],
    }

    for case_id in selected_cases:
        trace_path = RAW_ROOT / case_id / "traces.parquet"
        if trace_path.exists():
            result["trace_cases"][case_id] = audit_trace_case(case_id, trace_path)
        else:
            result["selected_cases_without_traces_parquet"].append(case_id)

    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
