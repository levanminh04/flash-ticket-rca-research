"""Deterministic metadata-only audit for RCAEval cases.parquet.

This script intentionally reads only the official metadata file.  It does not
enumerate, download, or open any raw telemetry case.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


WORKSPACE = Path(r"D:\Project\flash-ticket-rca-research")
METADATA = WORKSPACE / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
PROVENANCE = WORKSPACE / "datasets" / "rcaeval" / "metadata" / "metadata-provenance.json"


def normalize(value: Any) -> Any:
    """Convert pandas/numpy values to JSON-safe builtins."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {key: normalize(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def count_table(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    return records(
        frame.groupby(columns, dropna=False).size().reset_index(name="cases").sort_values(
            ["cases", *columns], ascending=[False, *([True] * len(columns))]
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args()

    file_bytes = METADATA.read_bytes()
    df = pd.read_parquet(METADATA)
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    string_columns = [
        "case",
        "dataset",
        "suite",
        "system",
        "system_name",
        "root_cause_service",
        "fault",
        "fault_description",
    ]
    numeric_columns = [
        "repetition",
        "inject_time",
        "n_metrics",
        "n_timesteps",
        "time_start",
        "time_end",
        "duration_minutes",
        "normal_timesteps",
        "faulty_timesteps",
        "n_logs",
        "n_traces",
    ]

    duplicate_case_rows = df[df.duplicated("case", keep=False)].sort_values("case")
    duplicate_full_rows = df[df.duplicated(keep=False)].sort_values("case")
    blank_string_counts = {
        col: int((df[col].isna() | df[col].astype("string").str.strip().eq("")).sum())
        for col in string_columns
    }
    null_counts = {col: int(df[col].isna().sum()) for col in df.columns}
    negative_counts = {col: int((df[col] < 0).sum()) for col in numeric_columns}

    time_elapsed = df["time_end"] - df["time_start"]
    duration_seconds = df["duration_minutes"] * 60
    normal_delta = df["inject_time"] - df["time_start"]
    expected_duration_one_decimal = (time_elapsed / 60).round(1)
    case_suffix = pd.to_numeric(df["case"].str.rsplit("_", n=1).str[-1], errors="coerce")

    result: dict[str, Any] = {
        "input": {
            "metadata_path": str(METADATA),
            "rows": int(len(df)),
            "columns": list(df.columns),
            "dtypes": {key: str(value) for key, value in df.dtypes.items()},
            "file_bytes": len(file_bytes),
            "sha256": hashlib.sha256(file_bytes).hexdigest(),
            "provenance": provenance,
        },
        "counts": {
            "by_suite": count_table(df, ["suite"]),
            "by_dataset": count_table(df, ["dataset"]),
            "by_system": count_table(df, ["system", "system_name"]),
            "by_suite_system": count_table(df, ["suite", "system", "system_name"]),
            "by_fault": count_table(df, ["fault", "fault_description"]),
            "by_root_cause_service": count_table(df, ["root_cause_service"]),
            "by_system_root_cause_service": count_table(df, ["system", "root_cause_service"]),
            "by_modality": records(
                df.groupby(["has_logs", "has_traces", "has_root_cause_file"], dropna=False)
                .agg(
                    cases=("case", "size"),
                    min_n_metrics=("n_metrics", "min"),
                    max_n_metrics=("n_metrics", "max"),
                    min_n_logs=("n_logs", "min"),
                    max_n_logs=("n_logs", "max"),
                    min_n_traces=("n_traces", "min"),
                    max_n_traces=("n_traces", "max"),
                )
                .reset_index()
                .sort_values("cases", ascending=False)
            ),
        },
        "numeric_summary": records(
            df[numeric_columns]
            .agg(["count", "min", "max", "mean", "median", "nunique"])
            .transpose()
            .reset_index(names="field")
        ),
        "consistency": {
            "duplicate_case_rows": int(len(duplicate_case_rows)),
            "duplicate_full_rows": int(len(duplicate_full_rows)),
            "duplicate_cases": records(duplicate_case_rows),
            "blank_string_counts": blank_string_counts,
            "null_counts": null_counts,
            "negative_counts": negative_counts,
            "has_logs_true_n_logs_zero": int((df["has_logs"] & df["n_logs"].eq(0)).sum()),
            "has_logs_false_n_logs_nonzero": int((~df["has_logs"] & df["n_logs"].ne(0)).sum()),
            "has_traces_true_n_traces_zero": int((df["has_traces"] & df["n_traces"].eq(0)).sum()),
            "has_traces_false_n_traces_nonzero": int((~df["has_traces"] & df["n_traces"].ne(0)).sum()),
            "n_metrics_zero": int(df["n_metrics"].eq(0).sum()),
            "time_end_before_or_equal_start": int(df["time_end"].le(df["time_start"]).sum()),
            "inject_outside_closed_window": int(
                ((df["inject_time"] < df["time_start"]) | (df["inject_time"] > df["time_end"])).sum()
            ),
            "normal_plus_faulty_not_n_timesteps": int(
                (df["normal_timesteps"] + df["faulty_timesteps"]).ne(df["n_timesteps"]).sum()
            ),
            "duration_minutes_not_elapsed_seconds_div_60": int(
                duration_seconds.ne(time_elapsed).sum()
            ),
            "n_timesteps_not_elapsed_seconds_plus_1": int(df["n_timesteps"].ne(time_elapsed + 1).sum()),
            "normal_timesteps_not_inject_minus_start": int(df["normal_timesteps"].ne(normal_delta).sum()),
            "duration_matches_elapsed_minutes_rounded_to_one_decimal": int(
                df["duration_minutes"].eq(expected_duration_one_decimal).sum()
            ),
            "case_numeric_suffix_not_repetition": int(case_suffix.ne(df["repetition"]).sum()),
            "case_to_dataset_count": int(df.groupby("case")["dataset"].nunique().gt(1).sum()),
            "system_to_name_count": int(df.groupby("system")["system_name"].nunique().gt(1).sum()),
            "suite_to_dataset_count": int(df.groupby("suite")["dataset"].nunique().gt(1).sum()),
            "dataset_to_suite_count": int(df.groupby("dataset")["suite"].nunique().gt(1).sum()),
            "dataset_to_system_count": int(df.groupby("dataset")["system"].nunique().gt(1).sum()),
            "fault_to_description_count": int(
                df.groupby("fault")["fault_description"].nunique().gt(1).sum()
            ),
            "root_cause_indicator_column_present": "root_cause_indicator" in df.columns,
        },
        "outliers": {
            "zero_or_nonpositive_values": records(
                df[
                    df[["n_metrics", "n_timesteps", "normal_timesteps", "faulty_timesteps"]]
                    .le(0)
                    .any(axis=1)
                ]
            ),
            "lowest_n_metrics": records(df.nsmallest(10, "n_metrics")),
            "highest_n_metrics": records(df.nlargest(10, "n_metrics")),
            "highest_n_logs": records(df.nlargest(10, "n_logs")),
            "highest_n_traces": records(df.nlargest(10, "n_traces")),
        },
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return

    print(f"rows={result['input']['rows']}")
    print(f"sha256={result['input']['sha256']}")
    print("columns=" + ",".join(result["input"]["columns"]))
    for key, value in result["consistency"].items():
        if key not in {"duplicate_cases", "blank_string_counts", "null_counts", "negative_counts"}:
            print(f"{key}={value}")


if __name__ == "__main__":
    main()
