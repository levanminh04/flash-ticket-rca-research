"""Independent deterministic evidence collection for Subagent H's red-team review.

This script deliberately reads only the already-pinned metadata and the six
previously downloaded raw samples.  It never downloads data, never reads a
case ID as telemetry, and keeps every conclusion at its evidence scope.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
METADATA = ROOT / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
RAW_ROOT = ROOT / "datasets" / "rcaeval" / "raw-samples"
MANIFEST = RAW_ROOT / "raw-download-manifest.json"
PLAN = ROOT / "audits" / "rcaeval" / "raw-sample-plan.json"
B2B_MANIFEST = ROOT / "audits" / "rcaeval" / "b2b-re2tt-multimodal-download-manifest.json"
B2_TRACE_AUDIT = ROOT / "audits" / "rcaeval" / "re2tt-trace-full-subset-audit.json"
OUT = ROOT / "audits" / "rcaeval" / "subagent-h-red-team-evidence.json"

CASE_RE = re.compile(
    r"^re(?P<suite_number>[123])(?P<system_code>ob|ss|tt)_"
    r"(?P<service>.+)_(?P<fault>[^_]+)_(?P<repetition>[0-9]+)$"
)
METRIC_ENTITY_PATTERNS = [
    re.compile(r"^(?P<entity>.+)_(?:cpu|mem|diskio|socket|workload|error)$"),
    re.compile(r"^(?P<entity>.+)_latency(?:-(?:50|90))?$"),
]
HEX32_RE = re.compile(r"(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})(?![0-9A-Fa-f])")
HEX16_RE = re.compile(r"(?<![0-9A-Fa-f])([0-9A-Fa-f]{16})(?![0-9A-Fa-f])")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_names(path: Path) -> list[str]:
    return pq.read_schema(path).names


def parquet_time_range(path: Path) -> tuple[int, int, int]:
    table = pq.read_table(path, columns=["time"])
    values = table.column("time").to_pylist()
    return min(values), max(values), len(values)


def metric_entities(columns: list[str]) -> set[str]:
    entities: set[str] = set()
    for column in columns:
        for pattern in METRIC_ENTITY_PATTERNS:
            match = pattern.fullmatch(column)
            if match:
                entities.add(match.group("entity"))
                break
    return entities


def main() -> None:
    metadata_table = pq.read_table(METADATA)
    rows = metadata_table.to_pylist()
    metadata_columns = metadata_table.schema.names
    by_case = {row["case"]: row for row in rows}

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    manifest_cases = [entry["case"] for entry in manifest["cases"]]
    plan_cases = [entry["case"] for entry in plan["cases"]]

    regex_mismatches: list[dict[str, object]] = []
    for row in rows:
        match = CASE_RE.fullmatch(row["case"])
        if not match:
            regex_mismatches.append({"case": row["case"], "reason": "no_match"})
            continue
        expected = {
            "service": row["root_cause_service"],
            "fault": row["fault"],
            "repetition": str(row["repetition"]),
        }
        actual = {key: match.group(key) for key in expected}
        if actual != expected:
            regex_mismatches.append(
                {"case": row["case"], "expected": expected, "actual": actual}
            )

    re2tt = [row for row in rows if row["dataset"] == "RE2-TT"]
    re2tt_groups = Counter(
        (row["root_cause_service"], row["fault"]) for row in re2tt
    )
    re2tt_in_window = [
        row["case"]
        for row in re2tt
        if row["time_start"] <= row["inject_time"] <= row["time_end"]
    ]
    re2tt_normal_boundary = [
        row["case"]
        for row in re2tt
        if row["inject_time"] == row["time_start"] + row["normal_timesteps"]
    ]

    raw_case_evidence: list[dict[str, object]] = []
    total_manifest_files = 0
    matching_manifest_hashes = 0
    root_cause_file_evidence: list[dict[str, object]] = []
    trace_required_absent = [
        "span.kind",
        "http",
        "rpc",
        "db",
        "messaging",
        "peer",
        "resource",
        "container",
        "host",
        "pod",
        "link",
        "event",
    ]
    for case_entry in manifest["cases"]:
        case = case_entry["case"]
        case_dir = RAW_ROOT / case
        files = {Path(item["local_path"]).name: item for item in case_entry["files"]}
        file_status: dict[str, object] = {}
        for filename, item in files.items():
            local = Path(item["local_path"])
            total_manifest_files += 1
            exists = local.exists()
            actual_hash = sha256(local) if exists else None
            match = bool(exists and local.stat().st_size == item["bytes"] and actual_hash == item["sha256"])
            if match:
                matching_manifest_hashes += 1
            file_status[filename] = {
                "exists": exists,
                "bytes_match": bool(exists and local.stat().st_size == item["bytes"]),
                "sha256_match": actual_hash == item["sha256"],
            }

        entry: dict[str, object] = {
            "case": case,
            "planned": case in plan_cases,
            "metadata_dataset": by_case[case]["dataset"],
            "manifest_file_status": file_status,
        }
        metrics_path = case_dir / "metrics.parquet"
        logs_path = case_dir / "logs.parquet"
        traces_path = case_dir / "traces.parquet"
        if metrics_path.exists():
            metric_columns = schema_names(metrics_path)
            time_start, time_end, count = parquet_time_range(metrics_path)
            inject_time = int((case_dir / "inject_time.txt").read_text(encoding="utf-8").strip())
            entry["metrics"] = {
                "column_count": len(metric_columns),
                "has_direct_trace_or_log_id_column": any(
                    token.lower() in {"traceid", "spanid", "logid", "eventid"}
                    for token in metric_columns
                ),
                "time_start": time_start,
                "time_end": time_end,
                "row_count": count,
                "inject_time": inject_time,
                "injection_in_metric_window": time_start <= inject_time <= time_end,
            }
        if logs_path.exists():
            log_columns = schema_names(logs_path)
            entry["logs"] = {
                "columns": log_columns,
                "has_direct_trace_or_span_id_column": any(
                    token.lower() in {"traceid", "spanid"} for token in log_columns
                ),
                "has_container_name": "container_name" in log_columns,
            }
        if traces_path.exists():
            trace_columns = schema_names(traces_path)
            lowered = [column.lower() for column in trace_columns]
            entry["traces"] = {
                "columns": trace_columns,
                "contains_typed_protocol_or_resource_field": {
                    token: any(token in column for column in lowered)
                    for token in trace_required_absent
                },
            }
        if logs_path.exists() and metrics_path.exists():
            log_table = pq.read_table(logs_path, columns=["timestamp", "container_name"])
            log_times = log_table.column("timestamp").to_pylist()
            containers = log_table.column("container_name").to_pylist()
            metric_table = pq.read_table(metrics_path, columns=["time"])
            metric_times = set(metric_table.column("time").to_pylist())
            entities = metric_entities(schema_names(metrics_path))
            direct_rows = sum(
                1
                for timestamp, container in zip(log_times, containers, strict=True)
                if timestamp in metric_times and container in entities
            )
            entry["logs_to_metrics_key_check"] = {
                "classification": "DIRECT_KEY_JOIN_AT_SERVICE_SECOND_BIN",
                "rule": "logs.timestamp == metrics.time AND logs.container_name equals an entity deterministically parsed from a metric column suffix",
                "metric_entity_rule": "^(entity)_(cpu|mem|diskio|socket|workload|error)$ OR ^(entity)_latency(-50|-90)?$",
                "log_rows": len(log_times),
                "log_rows_matching_time_and_exact_entity": direct_rows,
                "exact_container_entity_overlap": sorted(set(containers) & entities),
                "limitation": "This maps each log event to a service-second metric bin and possibly multiple metric series; it is not an event-to-single-metric or causal mapping.",
            }
        if logs_path.exists() and traces_path.exists():
            messages = pq.read_table(logs_path, columns=["message"]).column("message").to_pylist()
            hex32 = {match.group(1).lower() for message in messages if message for match in HEX32_RE.finditer(message)}
            hex16 = {match.group(1).lower() for message in messages if message for match in HEX16_RE.finditer(message)}
            trace_table = pq.read_table(traces_path, columns=["traceID", "spanID"])
            trace_ids = {value.lower() for value in trace_table.column("traceID").to_pylist() if value}
            span_ids = {value.lower() for value in trace_table.column("spanID").to_pylist() if value}
            entry["logs_to_traces_embedded_id_check"] = {
                "classification": "NO_DIRECT_ID_JOIN_IF_MATCH_COUNTS_ARE_ZERO",
                "log_schema_has_trace_or_span_column": any(
                    column.lower() in {"traceid", "spanid"} for column in schema_names(logs_path)
                ),
                "hex32_candidates_in_log_messages": len(hex32),
                "hex16_candidates_in_log_messages": len(hex16),
                "exact_trace_id_matches": len(hex32 & trace_ids),
                "exact_span_id_matches": len(hex16 & span_ids),
            }
        root_cause_path = case_dir / "root_cause.txt"
        if root_cause_path.exists() and logs_path.exists():
            root_rows = list(csv.reader(root_cause_path.read_text(encoding="utf-8").splitlines()))
            root_cells = {cell for row in root_rows for cell in row if cell}
            log_messages = set(
                pq.read_table(logs_path, columns=["message"]).column("message").to_pylist()
            )
            matched_cells = sorted(cell for cell in root_cells if cell in log_messages)
            root_cause_file_evidence.append(
                {
                    "case": case,
                    "root_cause_rows": len(root_rows),
                    "nonempty_cells": len(root_cells),
                    "exact_log_message_cell_matches": len(matched_cells),
                }
            )
        raw_case_evidence.append(entry)

    problematic_metadata_cases = [
        row["case"]
        for row in rows
        if not (row["time_start"] <= row["inject_time"] <= row["time_end"])
    ]

    b2b_evidence: dict[str, object] | None = None
    if B2B_MANIFEST.exists():
        b2b = json.loads(B2B_MANIFEST.read_text(encoding="utf-8"))
        b2b_case = b2b["case"]
        b2b_dir = RAW_ROOT / b2b_case
        b2b_status: dict[str, object] = {}
        for item in b2b["files"]:
            local = Path(item["local_path"])
            actual_hash = sha256(local) if local.exists() else None
            b2b_status[local.name] = {
                "exists": local.exists(),
                "bytes_match": bool(local.exists() and local.stat().st_size == item["bytes"]),
                "sha256_matches_manifest": actual_hash == item["sha256"],
                "sha256_matches_official_lfs": actual_hash == item["official_lfs_sha256"],
            }
        b2b_logs = b2b_dir / "logs.parquet"
        b2b_metrics = b2b_dir / "metrics.parquet"
        b2b_traces = b2b_dir / "traces.parquet"
        log_table = pq.read_table(b2b_logs, columns=["timestamp", "container_name", "message"])
        metric_table = pq.read_table(b2b_metrics, columns=["time"])
        trace_table = pq.read_table(b2b_traces, columns=["traceID", "spanID", "serviceName", "startTimeMillis"])
        log_times = log_table.column("timestamp").to_pylist()
        containers = log_table.column("container_name").to_pylist()
        messages = log_table.column("message").to_pylist()
        entities = metric_entities(schema_names(b2b_metrics))
        metric_times = set(metric_table.column("time").to_pylist())
        direct_rows = sum(
            1
            for timestamp, container in zip(log_times, containers, strict=True)
            if timestamp in metric_times and container in entities
        )
        hex32 = {match.group(1).lower() for message in messages if message for match in HEX32_RE.finditer(message)}
        hex16 = {match.group(1).lower() for message in messages if message for match in HEX16_RE.finditer(message)}
        trace_ids = {value.lower() for value in trace_table.column("traceID").to_pylist() if value}
        span_ids = {value.lower() for value in trace_table.column("spanID").to_pylist() if value}
        trace_seconds = {
            value // 1000
            for value in trace_table.column("startTimeMillis").to_pylist()
            if value is not None
        }
        trace_services = {
            value for value in trace_table.column("serviceName").to_pylist() if value
        }
        b2b_evidence = {
            "scope": "RAW SAMPLE FINDING — one targeted normal log-bearing RE2-TT case",
            "case": b2b_case,
            "metadata_dataset": by_case[b2b_case]["dataset"],
            "manifest_revision": b2b["source"]["revision"],
            "file_integrity": b2b_status,
            "schemas": {
                "logs": schema_names(b2b_logs),
                "metrics_column_count": len(schema_names(b2b_metrics)),
                "traces": schema_names(b2b_traces),
            },
            "logs_to_metrics": {
                "classification": "DIRECT_KEY_JOIN_AT_SERVICE_SECOND_BIN",
                "rule": "logs.timestamp == metrics.time AND logs.container_name equals an entity deterministically parsed from a metric-column suffix",
                "log_rows": len(log_times),
                "log_rows_matching_time_and_exact_entity": direct_rows,
                "exact_container_entity_overlap_count": len(set(containers) & entities),
                "limitation": "A log event maps to a service-second bin and possibly several metric series; it does not map to one event-level metric observation.",
            },
            "logs_to_traces": {
                "classification": "SERVICE_AND_TIME_WINDOW_ONLY",
                "log_schema_has_trace_or_span_column": any(
                    column.lower() in {"traceid", "spanid"} for column in schema_names(b2b_logs)
                ),
                "exact_trace_id_matches": len(hex32 & trace_ids),
                "exact_span_id_matches": len(hex16 & span_ids),
                "matching_log_seconds_to_trace_start_seconds": len(set(log_times) & trace_seconds),
                "exact_container_trace_service_overlap_count": len(set(containers) & trace_services),
            },
            "metrics_to_traces": {
                "classification": "SERVICE_AND_TIME_WINDOW_ONLY",
                "metric_schema_has_trace_or_span_column": any(
                    column.lower() in {"traceid", "spanid"} for column in schema_names(b2b_metrics)
                ),
                "matching_metric_seconds_to_trace_start_seconds": len(metric_times & trace_seconds),
                "exact_metric_entity_trace_service_overlap_count": len(entities & trace_services),
            },
        }

    b2_full_trace_scrutiny: dict[str, object] | None = None
    if B2_TRACE_AUDIT.exists():
        b2 = json.loads(B2_TRACE_AUDIT.read_text(encoding="utf-8"))
        cases = b2["cases"]
        per_case_service_counts = [
            len(case["operation_representation"]["service_names"]) for case in cases
        ]
        per_case_operation_pair_counts = [
            case["operation_representation"]["distinct_service_operation_pairs"]
            for case in cases
        ]
        low_parent_cases = sorted(
            [
                {
                    "case": case["case"],
                    "rate": case["parent_resolution"]["parent_resolution_rate_among_unambiguous_candidates"],
                }
                for case in cases
                if case["parent_resolution"]["parent_resolution_rate_among_unambiguous_candidates"] < 0.9
            ],
            key=lambda item: item["rate"],
        )
        b2_full_trace_scrutiny = {
            "scope": "FULL-SUBSET PROPERTY — all 90 RE2-TT trace objects; deterministic results created by the separate B2 auditor",
            "source_revision": b2["source"]["revision"],
            "case_count": b2["summary"]["case_count"],
            "row_count": b2["summary"]["rows"],
            "physical_schema_variants": b2["summary"]["physical_schema_variants"],
            "complete_trace_span_service_operation_rate": b2["summary"]["identity_coverage"]["rows_complete_trace_span_service_operation_rate"],
            "distinct_literal_service_names": b2["summary"]["operation_representation"]["distinct_service_names"],
            "distinct_literal_service_operation_pairs": b2["summary"]["operation_representation"]["distinct_service_operation_pairs"],
            "operation_names_reused_across_more_than_one_service": b2["summary"]["operation_representation"]["operation_names_reused_across_more_than_one_service"],
            "per_case_literal_service_count": {
                "minimum": min(per_case_service_counts),
                "maximum": max(per_case_service_counts),
                "cases_at_minimum": sum(count == min(per_case_service_counts) for count in per_case_service_counts),
            },
            "per_case_literal_service_operation_pair_count": {
                "minimum": min(per_case_operation_pair_counts),
                "maximum": max(per_case_operation_pair_counts),
            },
            "parent_resolution_rate": b2["summary"]["parent_resolution"]["parent_resolution_rate_among_unambiguous_candidates"],
            "parent_unresolved_count": b2["summary"]["parent_resolution"]["unresolved_same_trace"],
            "cases_below_90_percent_parent_resolution": low_parent_cases,
            "semantic_schema_field_matches": b2["summary"]["semantic_schema_field_matches"],
            "observed_cross_service_parent_child_pair_count": len(b2["summary"]["observed_parent_to_child_service_edges"]),
        }
    output = {
        "scope": {
            "metadata": "DATASET-WIDE METADATA FACT — 735 pinned cases",
            "raw": "RAW SAMPLE FINDING — six planned cases only",
            "note": "This is evidence collection for an independent methodology red-team review; it does not select a method.",
        },
        "provenance": {
            "metadata_path": str(METADATA),
            "metadata_sha256": sha256(METADATA),
            "manifest_revision": manifest["source"]["revision"],
            "manifest_cases": manifest_cases,
            "plan_cases": plan_cases,
            "same_case_order": manifest_cases == plan_cases,
            "metadata_columns": metadata_columns,
        },
        "integrity": {
            "manifest_file_count": total_manifest_files,
            "files_matching_recorded_size_and_hash": matching_manifest_hashes,
            "all_match": total_manifest_files == matching_manifest_hashes,
        },
        "dataset_wide_leakage": {
            "case_regex_matches_and_recovers_service_fault_repetition": len(rows) - len(regex_mismatches),
            "metadata_rows": len(rows),
            "mismatches": regex_mismatches,
        },
        "re2tt_metadata": {
            "case_count": len(re2tt),
            "root_cause_service_counts": dict(sorted(Counter(row["root_cause_service"] for row in re2tt).items())),
            "fault_counts": dict(sorted(Counter(row["fault"] for row in re2tt).items())),
            "service_fault_cells": len(re2tt_groups),
            "repetitions_per_service_fault_cell": sorted(set(re2tt_groups.values())),
            "all_inject_times_in_window": len(re2tt_in_window) == len(re2tt),
            "all_inject_times_equal_normal_boundary": len(re2tt_normal_boundary) == len(re2tt),
            "logs_present": sum(bool(row["has_logs"]) for row in re2tt),
            "traces_present": sum(bool(row["has_traces"]) for row in re2tt),
            "root_cause_files_present": sum(bool(row["has_root_cause_file"]) for row in re2tt),
            "candidate_universe_metadata_columns": [
                column for column in metadata_columns if "candidate" in column.lower()
            ],
            "ground_truth_columns_absent": [
                label
                for label in [
                    "operation_label",
                    "resource_label",
                    "affected_node_label",
                    "propagation_path_label",
                    "injection_target",
                ]
                if label not in metadata_columns
            ],
        },
        "metadata_injection_window_outliers": problematic_metadata_cases,
        "raw_sample_evidence": raw_case_evidence,
        "root_cause_file_evidence": root_cause_file_evidence,
        "b2b_re2tt_normal_log_case_evidence": b2b_evidence,
        "b2_re2tt_full_trace_scrutiny": b2_full_trace_scrutiny,
    }
    OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(json.dumps({
        "metadata_rows": len(rows),
        "regex_recovery": len(rows) - len(regex_mismatches),
        "manifest_integrity": output["integrity"],
        "re2tt_cases": len(re2tt),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
