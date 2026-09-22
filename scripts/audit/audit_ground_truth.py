"""Deterministic metadata-only audit for RCAEval labels and leakage risks.

This script deliberately reads only cases.parquet.  It does not enumerate or
download case telemetry.  Its JSON output is supporting evidence for the
Subagent-F audit report, not an experiment-ready model feature table.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
METADATA = ROOT / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
OUTPUT = ROOT / "audits" / "rcaeval" / "subagent-f-ground-truth-leakage-data.json"

CASE_PATTERN = re.compile(
    r"^(?P<prefix>re(?P<suite_number>[123])(?P<system_code>ob|ss|tt))_"
    r"(?P<service>.+)_(?P<fault>[^_]+)_(?P<repetition>[0-9]+)$"
)


def records(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    """Return JSON-safe rows in deterministic lexical/numeric order."""
    return json.loads(frame.loc[:, columns].to_json(orient="records"))


def grouped_counts(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    counted = (
        frame.groupby(columns, dropna=False)
        .size()
        .reset_index(name="case_count")
        .sort_values(columns, kind="stable")
        .reset_index(drop=True)
    )
    return records(counted, [*columns, "case_count"])


def parse_case(case: str) -> dict[str, object]:
    match = CASE_PATTERN.fullmatch(case)
    if not match:
        return {"case": case, "pattern_match": False}
    return {
        "case": case,
        "pattern_match": True,
        "parsed_suite": f"RE{match['suite_number']}",
        "parsed_system": match["system_code"],
        "parsed_root_cause_service": match["service"],
        "parsed_fault": match["fault"],
        "parsed_repetition": int(match["repetition"]),
    }


def main() -> None:
    data = pd.read_parquet(METADATA)
    parsed = pd.DataFrame([parse_case(case) for case in data["case"]])
    joined = data.join(parsed.drop(columns="case"))

    unexpected_columns = sorted(
        set(data.columns)
        - {
            "case",
            "dataset",
            "suite",
            "system",
            "system_name",
            "root_cause_service",
            "fault",
            "fault_description",
            "repetition",
            "inject_time",
            "n_metrics",
            "n_timesteps",
            "time_start",
            "time_end",
            "duration_minutes",
            "normal_timesteps",
            "faulty_timesteps",
            "has_logs",
            "n_logs",
            "has_traces",
            "n_traces",
            "has_root_cause_file",
        }
    )
    identifier_match_columns = [
        "parsed_suite",
        "parsed_system",
        "parsed_root_cause_service",
        "parsed_fault",
        "parsed_repetition",
    ]
    source_columns = ["suite", "system", "root_cause_service", "fault", "repetition"]
    identifier_match = joined["pattern_match"].fillna(False)
    for parsed_column, source_column in zip(identifier_match_columns, source_columns):
        identifier_match &= joined[parsed_column].eq(joined[source_column])

    derived_window_checks = {
        "normal_plus_faulty_equals_n_timesteps": int(
            (data["normal_timesteps"] + data["faulty_timesteps"] == data["n_timesteps"]).sum()
        ),
        "inject_time_equals_time_start_plus_normal_timesteps": int(
            (data["inject_time"] == data["time_start"] + data["normal_timesteps"]).sum()
        ),
        "inject_time_within_inclusive_time_range": int(
            data["inject_time"].between(data["time_start"], data["time_end"], inclusive="both").sum()
        ),
    }
    injection_window_anomalies = data.loc[
        (data["inject_time"] != data["time_start"] + data["normal_timesteps"])
        | ~data["inject_time"].between(data["time_start"], data["time_end"], inclusive="both"),
        [
            "case",
            "dataset",
            "suite",
            "system",
            "root_cause_service",
            "fault",
            "inject_time",
            "time_start",
            "time_end",
            "n_timesteps",
            "normal_timesteps",
            "faulty_timesteps",
            "duration_minutes",
        ],
    ].sort_values("case")

    root_fault_group_sizes = (
        data.groupby(["dataset", "root_cause_service", "fault"], dropna=False)
        .size()
        .reset_index(name="repetitions_in_group")
    )
    root_service_cross_systems = (
        data.groupby("root_cause_service", dropna=False)["system"]
        .nunique()
        .reset_index(name="system_count")
        .query("system_count > 1")
        .sort_values("root_cause_service")
    )

    root_cause_file_cases = data.loc[
        data["has_root_cause_file"],
        ["case", "dataset", "suite", "system", "root_cause_service", "fault", "repetition", "n_logs", "n_traces"],
    ].sort_values("case")

    candidate_cases = [
        "re1ob_productcatalogservice_cpu_3",
        "re2ob_checkoutservice_socket_1",
        "re2ss_orders_loss_2",
        "re2tt_ts-auth-service_cpu_1",
        "re3ss_carts_f1_1",
        "re3tt_ts-route-service_f2_1",
    ]
    candidate_case_rows = data.loc[
        data["case"].isin(candidate_cases),
        [
            "case",
            "dataset",
            "suite",
            "system",
            "root_cause_service",
            "fault",
            "fault_description",
            "repetition",
            "inject_time",
            "has_logs",
            "n_logs",
            "has_traces",
            "n_traces",
            "has_root_cause_file",
        ],
    ].sort_values("case")

    payload: dict[str, object] = {
        "scope": "DATASET-WIDE METADATA FACT — cases.parquet only; no raw telemetry",
        "input": {
            "path": str(METADATA),
            "sha256": hashlib.sha256(METADATA.read_bytes()).hexdigest(),
            "rows": int(len(data)),
            "columns": list(data.columns),
            "column_profile": {
                column: {
                    "dtype": str(data[column].dtype),
                    "null_count": int(data[column].isna().sum()),
                    "distinct_non_null": int(data[column].nunique(dropna=True)),
                }
                for column in data.columns
            },
            "unexpected_columns": unexpected_columns,
            "duplicate_case_count": int(data["case"].duplicated().sum()),
        },
        "case_directory_encoding": {
            "regex": CASE_PATTERN.pattern,
            "all_rows_match_case_pattern_and_index_labels": int(identifier_match.sum()),
            "non_matching_rows": records(
                joined.loc[
                    ~identifier_match,
                    ["case", *source_columns, *identifier_match_columns, "pattern_match"],
                ].sort_values("case"),
                ["case", *source_columns, *identifier_match_columns, "pattern_match"],
            ),
        },
        "derived_injection_window_checks": {
            **derived_window_checks,
            "total_rows": int(len(data)),
            "anomalous_rows": records(injection_window_anomalies, list(injection_window_anomalies.columns)),
        },
        "counts": {
            "by_dataset": grouped_counts(data, ["dataset", "suite", "system"]),
            "by_root_cause_service": grouped_counts(data, ["system", "root_cause_service"]),
            "by_fault": grouped_counts(data, ["fault", "fault_description"]),
            "root_cause_fault_group_size_distribution": grouped_counts(
                root_fault_group_sizes, ["repetitions_in_group"]
            ),
            "root_cause_service_labels_used_by_multiple_systems": records(
                root_service_cross_systems,
                list(root_service_cross_systems.columns),
            ),
            "by_suite_and_modality": grouped_counts(
                data, ["suite", "system", "has_logs", "has_traces", "has_root_cause_file"]
            ),
            "root_cause_file_cases": records(
                root_cause_file_cases,
                list(root_cause_file_cases.columns),
            ),
            "no_log_cases_with_trace_count": records(
                data.loc[
                    ~data["has_logs"] & (data["n_traces"] > 0),
                    ["case", "dataset", "root_cause_service", "fault", "n_logs", "n_traces"],
                ].sort_values("case"),
                ["case", "dataset", "root_cause_service", "fault", "n_logs", "n_traces"],
            ),
        },
        "metadata_fields_absent": [
            "operation_label",
            "resource_label",
            "affected_node_label",
            "propagation_path_label",
            "explicit_injection_target_separate_from_root_cause_service",
        ],
        "independent_raw_case_proposal": {
            "proposed_case_ids": candidate_cases,
            "metadata_rows_found": records(candidate_case_rows, list(candidate_case_rows.columns)),
            "proposal_rows_found": int(len(candidate_case_rows)),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "sha256": payload["input"]["sha256"], "rows": len(data)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
