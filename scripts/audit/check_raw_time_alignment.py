"""Compare selected raw metrics timestamps with their raw inject_time.txt values."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
RAW_ROOT = ROOT / "datasets" / "rcaeval" / "raw-samples"
PLAN = ROOT / "audits" / "rcaeval" / "raw-sample-plan.json"
OUTPUT = ROOT / "audits" / "rcaeval" / "raw-time-alignment.json"


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    records = []
    for item in plan["cases"]:
        case_dir = RAW_ROOT / item["case"]
        metrics_path = case_dir / "metrics.parquet"
        inject_path = case_dir / "inject_time.txt"
        times = pq.read_table(metrics_path, columns=["time"])["time"].to_pylist()
        inject_time = int(inject_path.read_text(encoding="utf-8").strip())
        records.append(
            {
                "case": case_dir.name,
                "raw_inject_time": inject_time,
                "raw_metric_time_min": min(times),
                "raw_metric_time_max": max(times),
                "raw_metric_row_count": len(times),
                "rows_before_injection": sum(value < inject_time for value in times),
                "rows_at_or_after_injection": sum(value >= inject_time for value in times),
                "inject_within_raw_metric_range": min(times) <= inject_time <= max(times),
            }
        )
    result = {"scope": "RAW SAMPLE FINDING", "cases": records}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
