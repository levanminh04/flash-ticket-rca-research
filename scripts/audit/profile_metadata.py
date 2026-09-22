"""Generate machine-readable schema and frequency evidence for RCAEval metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
METADATA_PATH = ROOT / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
OUTPUT_PATH = ROOT / "audits" / "rcaeval" / "metadata-profile.json"


def native(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def frequencies(series: pd.Series, limit: int = 100) -> dict[str, int] | None:
    values = series.value_counts(dropna=False)
    if len(values) > limit:
        return None
    result: dict[str, int] = {}
    for key, value in values.items():
        label = "<NULL>" if pd.isna(key) else str(native(key))
        result[label] = int(value)
    return result


def main() -> None:
    if not METADATA_PATH.exists():
        raise FileNotFoundError(f"Metadata missing: {METADATA_PATH}")

    frame = pd.read_parquet(METADATA_PATH)
    columns: dict[str, dict] = {}
    for name in frame.columns:
        series = frame[name]
        columns[name] = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "distinct_non_null": int(series.nunique(dropna=True)),
            "frequencies": frequencies(series),
        }

    named_fields = {}
    for name in (
        "dataset",
        "suite",
        "system",
        "case",
        "fault",
        "root_cause_service",
        "root_cause_indicator",
        "inject_time",
        "n_metrics",
        "n_logs",
        "n_traces",
    ):
        if name in frame.columns:
            named_fields[name] = columns[name]

    duplicate_case_count = None
    if "case" in frame.columns:
        duplicate_case_count = int(frame["case"].duplicated().sum())

    profile = {
        "scope": "DATASET-WIDE METADATA FACT",
        "metadata_path": str(METADATA_PATH),
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "duplicate_case_count": duplicate_case_count,
        "columns": columns,
        "named_fields": named_fields,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, default=native) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(profile, ensure_ascii=False, indent=2, default=native))


if __name__ == "__main__":
    main()
