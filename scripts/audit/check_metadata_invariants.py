"""Check deterministic internal consistency constraints in RCAEval cases.parquet."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
INPUT = ROOT / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
OUTPUT = ROOT / "audits" / "rcaeval" / "metadata-invariants.json"


def records(frame: pd.DataFrame, columns: list[str]) -> list[dict]:
    return frame.loc[:, columns].to_dict(orient="records")


def main() -> None:
    df = pd.read_parquet(INPUT)
    base = [
        "case", "dataset", "inject_time", "time_start", "time_end",
        "n_timesteps", "normal_timesteps", "faulty_timesteps",
    ]
    checks = {
        "inject_time_before_start": df["inject_time"] < df["time_start"],
        "inject_time_after_end": df["inject_time"] > df["time_end"],
        "normal_plus_faulty_ne_timesteps": (
            df["normal_timesteps"] + df["faulty_timesteps"] != df["n_timesteps"]
        ),
        "non_positive_faulty_timesteps": df["faulty_timesteps"] <= 0,
        "non_positive_normal_timesteps": df["normal_timesteps"] <= 0,
        "has_logs_disagrees_n_logs": df["has_logs"] != df["n_logs"].gt(0),
        "has_traces_disagrees_n_traces": df["has_traces"] != df["n_traces"].gt(0),
    }
    result = {
        "scope": "DATASET-WIDE METADATA FACT",
        "row_count": int(len(df)),
        "checks": {
            name: {
                "count": int(mask.sum()),
                "rows": records(df.loc[mask], base),
            }
            for name, mask in checks.items()
        },
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
