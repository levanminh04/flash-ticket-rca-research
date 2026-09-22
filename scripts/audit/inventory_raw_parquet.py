"""Inventory row counts and physical schemas of selected raw Parquet files."""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
RAW_ROOT = ROOT / "datasets" / "rcaeval" / "raw-samples"
OUTPUT = ROOT / "audits" / "rcaeval" / "raw-parquet-inventory.json"


def main() -> None:
    records = []
    for path in sorted(RAW_ROOT.glob("*/*.parquet")):
        pf = pq.ParquetFile(path)
        records.append(
            {
                "case": path.parent.name,
                "file": path.name,
                "path": str(path),
                "bytes": path.stat().st_size,
                "rows": pf.metadata.num_rows,
                "row_groups": pf.metadata.num_row_groups,
                "columns": [
                    {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                    for field in pf.schema_arrow
                ],
            }
        )
    result = {
        "scope": "RAW SAMPLE FINDING — schema/physical parquet metadata only",
        "file_count": len(records),
        "files": records,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
