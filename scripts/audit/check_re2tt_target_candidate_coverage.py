"""Check whether each RE2-TT service-level ground-truth target is observable in its trace candidate set."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
METADATA = ROOT / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
TRACE_AUDIT = ROOT / "audits" / "rcaeval" / "re2tt-trace-full-subset-audit.json"
OUTPUT = ROOT / "audits" / "rcaeval" / "re2tt-target-candidate-coverage.json"


def main() -> None:
    metadata = pd.read_parquet(METADATA)
    subset = metadata.loc[metadata["dataset"].eq("RE2-TT"), ["case", "root_cause_service"]]
    targets = dict(zip(subset["case"], subset["root_cause_service"], strict=True))
    trace_audit = json.loads(TRACE_AUDIT.read_text(encoding="utf-8"))
    rows = []
    for case in trace_audit["cases"]:
        case_id = case["case"]
        services = case["operation_representation"]["service_names"]
        target = targets[case_id]
        rows.append(
            {
                "case": case_id,
                "root_cause_service": target,
                "candidate_service_count": len(services),
                "root_target_present_in_telemetry_candidate_set": target in set(services),
            }
        )
    result = {
        "scope": "FULL-SUBSET PROPERTY — all RE2-TT cases using full trace-audit output",
        "case_count": len(rows),
        "root_target_present_count": sum(
            row["root_target_present_in_telemetry_candidate_set"] for row in rows
        ),
        "root_target_absent_cases": [
            row for row in rows if not row["root_target_present_in_telemetry_candidate_set"]
        ],
        "minimum_telemetry_candidate_count": min(row["candidate_service_count"] for row in rows),
        "maximum_telemetry_candidate_count": max(row["candidate_service_count"] for row in rows),
        "cases": rows,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
