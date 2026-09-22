"""Independent stdlib + PyArrow cross-check for key Subagent-F counts.

No pandas imports and no telemetry access.  This avoids relying on a single
dataframe implementation for the label/leakage assertions in the report.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
SOURCE = ROOT / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
OUTPUT = ROOT / "audits" / "rcaeval" / "subagent-f-ground-truth-pyarrow-crosscheck.json"
PATTERN = re.compile(
    r"^re(?P<suite_number>[123])(?P<system_code>ob|ss|tt)_"
    r"(?P<service>.+)_(?P<fault>[^_]+)_(?P<repetition>[0-9]+)$"
)


def main() -> None:
    table = pq.read_table(SOURCE)
    rows = table.to_pylist()
    case_matches = 0
    case_mismatches: list[str] = []
    windows_sum = 0
    windows_start = 0
    windows_range = 0
    root_cause_file_cases: list[str] = []
    for row in rows:
        match = PATTERN.fullmatch(row["case"])
        if (
            match
            and f"RE{match['suite_number']}" == row["suite"]
            and match["system_code"] == row["system"]
            and match["service"] == row["root_cause_service"]
            and match["fault"] == row["fault"]
            and int(match["repetition"]) == row["repetition"]
        ):
            case_matches += 1
        else:
            case_mismatches.append(row["case"])
        windows_sum += int(row["normal_timesteps"] + row["faulty_timesteps"] == row["n_timesteps"])
        windows_start += int(row["inject_time"] == row["time_start"] + row["normal_timesteps"])
        windows_range += int(row["time_start"] <= row["inject_time"] <= row["time_end"])
        if row["has_root_cause_file"]:
            root_cause_file_cases.append(row["case"])
    output = {
        "implementation": "stdlib + pyarrow.parquet; no pandas",
        "path": str(SOURCE),
        "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "row_count": len(rows),
        "column_names": table.column_names,
        "case_name_matches_all_ground_truth_fields": case_matches,
        "case_name_mismatches": sorted(case_mismatches),
        "normal_plus_faulty_equals_n_timesteps": windows_sum,
        "inject_time_equals_time_start_plus_normal_timesteps": windows_start,
        "inject_time_within_inclusive_time_range": windows_range,
        "has_root_cause_file_count": len(root_cause_file_cases),
        "root_cause_file_cases": sorted(root_cause_file_cases),
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
