"""Deterministic raw-sample metrics audit for RCAEval Task B / Subagent D.

This script intentionally reads only the six cases named by the approved
raw-sample plan.  It does not download data and it treats inject_time and
metadata timing as provenance/evaluation evidence only, never as model input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


KNOWN_METRIC_IDENTITIES = (
    "latency-99",
    "latency-95",
    "latency-90",
    "latency-75",
    "latency-50",
    "latency",
    "diskio",
    "workload",
    "socket",
    "error",
    "load",
    "cpu",
    "mem",
)


def json_safe(value: Any) -> Any:
    """Convert pandas/numpy scalars to JSON-safe values without losing nulls."""
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    return value


def parse_metric_column(column: str) -> tuple[str | None, str | None]:
    """Parse only a suffix explicitly present in a raw metric column name."""
    for identity in KNOWN_METRIC_IDENTITIES:
        suffix = f"_{identity}"
        if column.endswith(suffix) and len(column) > len(suffix):
            return column[: -len(suffix)], identity
    return None, None


def profile_time(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    non_null = numeric.dropna()
    unique_sorted = sorted(non_null.unique().tolist())
    deltas = [int(right - left) for left, right in zip(unique_sorted, unique_sorted[1:])]
    delta_counts = Counter(deltas)
    return {
        "raw_dtype": str(series.dtype),
        "null_values": int(series.isna().sum()),
        "non_null_values": int(non_null.shape[0]),
        "min": json_safe(non_null.min()) if not non_null.empty else None,
        "max": json_safe(non_null.max()) if not non_null.empty else None,
        "unique_values": len(unique_sorted),
        "duplicate_timestamp_rows": int(non_null.shape[0] - len(unique_sorted)),
        "integer_valued": bool((non_null % 1 == 0).all()) if not non_null.empty else False,
        "unique_timestamp_deltas": dict(sorted(delta_counts.items())),
        "nominal_step_seconds_inferred": (
            min(delta_counts) if delta_counts else None
        ),
        "gaps_larger_than_nominal": (
            int(sum(count for delta, count in delta_counts.items() if delta > min(delta_counts)))
            if delta_counts
            else 0
        ),
        "timestamp_semantics": "INFERENCE: values have epoch-like magnitude and observed deltas are raw numeric differences; no timezone/unit metadata field was found in metrics.parquet.",
    }


def profile_case(
    case: str,
    case_dir: Path,
    metadata_by_case: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metric_path = case_dir / "metrics.parquet"
    result: dict[str, Any] = {
        "case": case,
        "metrics_file_present": metric_path.is_file(),
        "scope": "RAW SAMPLE FINDING — one selected case only",
    }
    if not metric_path.is_file():
        result["status"] = "UNKNOWN"
        result["reason"] = "No metrics.parquet was downloaded for this selected case."
        return result

    parquet = pq.ParquetFile(metric_path)
    table = parquet.read()
    df = table.to_pandas()
    columns = list(df.columns)
    timestamp_column = "time" if "time" in columns else None
    metric_columns = [column for column in columns if column != timestamp_column]

    parsed_columns: list[dict[str, Any]] = []
    entities: set[str] = set()
    family_to_columns: dict[str, list[str]] = defaultdict(list)
    entity_to_families: dict[str, set[str]] = defaultdict(set)
    unparsed: list[str] = []
    for column in metric_columns:
        entity, identity = parse_metric_column(column)
        parsed_columns.append(
            {"column": column, "entity_token": entity, "metric_identity": identity}
        )
        if entity is None or identity is None:
            unparsed.append(column)
        else:
            entities.add(entity)
            family_to_columns[identity].append(column)
            entity_to_families[entity].add(identity)

    null_counts = {column: int(df[column].isna().sum()) for column in metric_columns}
    nonzero_nulls = {
        column: count for column, count in sorted(null_counts.items()) if count > 0
    }
    all_null_columns = [
        column for column, count in null_counts.items() if count == len(df.index)
    ]
    all_zero_non_null_columns = []
    for column in metric_columns:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if not values.empty and bool((values == 0).all()):
            all_zero_non_null_columns.append(column)

    metadata_row = metadata_by_case.get(case)
    inject_file = case_dir / "inject_time.txt"
    raw_inject_content = inject_file.read_text(encoding="utf-8").strip() if inject_file.is_file() else None
    try:
        inject_from_file = int(raw_inject_content) if raw_inject_content else None
    except ValueError:
        inject_from_file = None
    metadata_inject = (
        json_safe(metadata_row.get("inject_time")) if metadata_row is not None else None
    )
    if metadata_inject is not None:
        metadata_inject = int(metadata_inject)

    time_profile = profile_time(df[timestamp_column]) if timestamp_column else None
    time_min = time_profile["min"] if time_profile else None
    time_max = time_profile["max"] if time_profile else None
    metadata_consistency = None
    if metadata_row is not None:
        metadata_metrics = json_safe(metadata_row.get("n_metrics"))
        metadata_timesteps = json_safe(metadata_row.get("n_timesteps"))
        metadata_start = json_safe(metadata_row.get("time_start"))
        metadata_end = json_safe(metadata_row.get("time_end"))
        metadata_normal = json_safe(metadata_row.get("normal_timesteps"))
        metadata_faulty = json_safe(metadata_row.get("faulty_timesteps"))
        metadata_consistency = {
            "metadata_n_metrics_equals_raw_metric_column_count": (
                int(metadata_metrics) == len(metric_columns)
                if metadata_metrics is not None
                else None
            ),
            "metadata_n_timesteps_equals_raw_row_count": (
                int(metadata_timesteps) == len(df.index)
                if metadata_timesteps is not None
                else None
            ),
            "metadata_time_start_equals_raw_min_time": (
                int(metadata_start) == time_min if metadata_start is not None and time_min is not None else None
            ),
            "metadata_time_end_equals_raw_max_time": (
                int(metadata_end) == time_max if metadata_end is not None and time_max is not None else None
            ),
            "metadata_normal_plus_faulty_equals_raw_row_count": (
                int(metadata_normal) + int(metadata_faulty) == len(df.index)
                if metadata_normal is not None and metadata_faulty is not None
                else None
            ),
            "limit": "Agreement in counts/range does not create a raw per-row label and does not validate an injection timestamp that lies outside the raw range.",
        }
    injection_position: dict[str, Any] = {
        "inject_time_file_present": inject_file.is_file(),
        "inject_time_file_raw": raw_inject_content,
        "inject_time_file_parsed": inject_from_file,
        "metadata_inject_time": metadata_inject,
        "file_and_metadata_match": (
            inject_from_file == metadata_inject
            if inject_from_file is not None and metadata_inject is not None
            else None
        ),
        "model_input_classification": "FORBIDDEN MODEL INPUT",
        "interpretation_limit": "These timestamps are provenance/evaluation fields. They do not create per-row normal/fault labels and must not be supplied to a model.",
    }
    if timestamp_column and inject_from_file is not None:
        numeric_time = pd.to_numeric(df[timestamp_column], errors="coerce")
        injection_position.update(
            {
                "inject_time_inside_raw_metric_range": bool(
                    time_min <= inject_from_file <= time_max
                )
                if time_min is not None and time_max is not None
                else None,
                "inject_time_minus_raw_start_seconds": (
                    int(inject_from_file - time_min) if time_min is not None else None
                ),
                "inject_time_minus_raw_end_seconds": (
                    int(inject_from_file - time_max) if time_max is not None else None
                ),
                "rows_before_inject_time": int((numeric_time < inject_from_file).sum()),
                "rows_at_inject_time": int((numeric_time == inject_from_file).sum()),
                "rows_after_inject_time": int((numeric_time > inject_from_file).sum()),
            }
        )

    schema_fields = [
        {"name": field.name, "type": str(field.type)} for field in parquet.schema_arrow
    ]
    schema_fingerprint = hashlib.sha256(
        json.dumps(schema_fields, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    result.update(
        {
            "status": "VERIFIED",
            "file": str(metric_path),
            "file_size_bytes": metric_path.stat().st_size,
            "parquet_rows": int(parquet.metadata.num_rows),
            "parquet_row_groups": int(parquet.metadata.num_row_groups),
            "schema": schema_fields,
            "schema_fingerprint_sha256": schema_fingerprint,
            "timestamp_column": timestamp_column,
            "time_profile": time_profile,
            "metric_column_count": len(metric_columns),
            "metric_columns": metric_columns,
            "parsed_metric_columns": parsed_columns,
            "metric_identities": {
                identity: {
                    "column_count": len(columns_for_identity),
                    "columns": sorted(columns_for_identity),
                }
                for identity, columns_for_identity in sorted(family_to_columns.items())
            },
            "entity_tokens": sorted(entities),
            "entity_count": len(entities),
            "entity_metric_identities": {
                entity: sorted(identities)
                for entity, identities in sorted(entity_to_families.items())
            },
            "unparsed_metric_columns": sorted(unparsed),
            "missingness": {
                "metric_cells": int(len(df.index) * len(metric_columns)),
                "null_metric_cells": int(sum(null_counts.values())),
                "columns_with_nulls": nonzero_nulls,
                "all_null_columns": sorted(all_null_columns),
                "all_zero_non_null_columns": sorted(all_zero_non_null_columns),
            },
            "duplicate_full_rows": int(df.duplicated().sum()),
            "metadata_timing_provenance": (
                {
                    key: json_safe(metadata_row.get(key))
                    for key in (
                        "case",
                        "inject_time",
                        "time_start",
                        "time_end",
                        "normal_timesteps",
                        "faulty_timesteps",
                        "n_metrics",
                        "n_timesteps",
                    )
                }
                if metadata_row is not None
                else None
            ),
            "metadata_raw_consistency": metadata_consistency,
            "injection_position": injection_position,
            "raw_row_fault_label_present": any(
                column.lower() in {"fault", "is_faulty", "label", "anomaly", "root_cause"}
                for column in columns
            ),
            "normal_fault_window_status": "UNKNOWN — metrics.parquet has no observed per-row fault/normal label column. Metadata/inject_time remain provenance/evaluation only.",
            "possible_join_keys": {
                "timestamp": {
                    "raw_field": timestamp_column,
                    "classification": "TIME-WINDOW APPROXIMATION",
                    "evidence": "The raw table has a numeric time column but no trace_id, span_id, log_id, or explicit cross-modal event key.",
                    "limit": "Exact join semantics across modalities cannot be established from metrics.parquet alone.",
                },
                "entity_token": {
                    "raw_field": "metric column name prefix before a recognized suffix",
                    "classification": "SERVICE-LEVEL ONLY",
                    "evidence": "Entity-like tokens occur in metric-column names (for example, names ending in _cpu or _latency-90); there is no separate service/resource ID column.",
                    "limit": "Mapping tokens to services, operations, databases, or external resources requires an explicit normalization rule and corroborating raw evidence.",
                },
                "trace_or_span_identifier": {
                    "raw_field": None,
                    "classification": "NOT SUPPORTED",
                    "evidence": "No trace_id, span_id, parent_span_id, or equivalent field appears in the metrics schema.",
                },
            },
        }
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(r"D:\Project\flash-ticket-rca-research"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "audits" / "rcaeval" / "subagent-d-metrics-data.json"
    plan_path = root / "audits" / "rcaeval" / "raw-sample-plan.json"
    metadata_path = root / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
    raw_root = root / "datasets" / "rcaeval" / "raw-samples"

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    selected_cases = [entry["case"] for entry in plan["cases"]]
    if len(selected_cases) != 6 or len(set(selected_cases)) != 6:
        raise ValueError("Raw-sample plan must name exactly six unique cases.")

    metadata_df = pq.read_table(metadata_path).to_pandas()
    metadata_by_case = {
        str(row["case"]): row.to_dict() for _, row in metadata_df.iterrows()
    }
    profiles = [
        profile_case(case, raw_root / case, metadata_by_case) for case in selected_cases
    ]
    present = [profile for profile in profiles if profile["metrics_file_present"]]
    report = {
        "scope": "RAW SAMPLE FINDING — exactly six planned cases; no dataset-wide prevalence claim",
        "auditor": "Subagent D — Metric Auditor",
        "inputs": {
            "raw_sample_plan": str(plan_path),
            "metadata_cases": str(metadata_path),
            "raw_samples_root": str(raw_root),
        },
        "selected_case_count": len(selected_cases),
        "cases_with_metrics": len(present),
        "cases_without_metrics": [
            profile["case"] for profile in profiles if not profile["metrics_file_present"]
        ],
        "case_profiles": profiles,
        "cross_case_scope_limit": "All counts below describe only the six selected raw samples and must not be generalized to the full RCAEval dataset.",
        "cross_case_observations": {
            "common_timestamp_field": sorted(
                {profile.get("timestamp_column") for profile in present}
            ),
            "all_have_trace_or_span_key": all(
                profile["possible_join_keys"]["trace_or_span_identifier"]["classification"]
                != "NOT SUPPORTED"
                for profile in present
            ),
            "metrics_cases_with_raw_row_fault_labels": [
                profile["case"]
                for profile in present
                if profile["raw_row_fault_label_present"]
            ],
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "cases_with_metrics": len(present)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
