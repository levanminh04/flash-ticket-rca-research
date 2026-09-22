"""Conservative raw-sample audit of logs and cross-modal join evidence.

This is a deterministic fallback check after the independent log reviewer was
interrupted by the execution quota. It never treats unstructured message text
or shared time as a direct identity join.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from io import StringIO
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(r"D:\Project\flash-ticket-rca-research")
RAW_ROOT = ROOT / "datasets" / "rcaeval" / "raw-samples"
PLAN = ROOT / "audits" / "rcaeval" / "raw-sample-plan.json"
OUTPUT = ROOT / "audits" / "rcaeval" / "main-log-multimodal-evidence.json"
HEX_TOKEN = re.compile(r"(?<![0-9a-fA-F])([0-9a-fA-F]{16,32})(?![0-9a-fA-F])")


def schema_columns(path: Path) -> list[dict]:
    return [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in pq.ParquetFile(path).schema_arrow
    ]


def min_max(values: list) -> dict | None:
    values = [value for value in values if value is not None]
    return {"min": min(values), "max": max(values)} if values else None


def trace_identity_and_time(path: Path) -> dict:
    pf = pq.ParquetFile(path)
    names = set(pf.schema_arrow.names)
    selected = [name for name in ("traceID", "spanID", "time", "startTime", "startTimeMillis") if name in names]
    time_fields = [name for name in ("time", "startTime", "startTimeMillis") if name in names]
    identity = {
        "trace_ids": set(),
        "span_ids": set(),
        "time_values": {name: [] for name in time_fields},
    }
    for batch in pf.iter_batches(columns=selected, batch_size=131072):
        data = batch.to_pydict()
        identity["trace_ids"].update(str(value) for value in data.get("traceID", []) if value is not None)
        identity["span_ids"].update(str(value) for value in data.get("spanID", []) if value is not None)
        for name in time_fields:
            identity["time_values"][name].extend(
                value for value in data.get(name, []) if value is not None
            )
    return {
        "schema_columns": schema_columns(path),
        "trace_id_count": len(identity["trace_ids"]),
        "span_id_count": len(identity["span_ids"]),
        "time_ranges": {
            name: min_max(values) for name, values in identity["time_values"].items()
        },
        "trace_ids": identity["trace_ids"],
        "span_ids": identity["span_ids"],
    }


def log_evidence(path: Path, trace: dict | None) -> dict:
    table = pq.read_table(path)
    data = table.to_pydict()
    timestamps = data.get("timestamp", [])
    containers = data.get("container_name", [])
    messages = data.get("message", [])
    token_counter: Counter[str] = Counter()
    for message in messages:
        if message:
            token_counter.update(token.lower() for token in HEX_TOKEN.findall(str(message)))

    record = {
        "schema_columns": schema_columns(path),
        "row_count": len(messages),
        "timestamp_range": min_max(timestamps),
        "null_counts": {
            "timestamp": sum(value is None for value in timestamps),
            "container_name": sum(value is None for value in containers),
            "message": sum(value is None for value in messages),
        },
        "distinct_container_name": len({value for value in containers if value is not None}),
        "top_container_name": Counter(value for value in containers if value is not None).most_common(20),
        "dedicated_trace_or_span_column": False,
        "dedicated_exception_column": False,
        "unstructured_hex_token_occurrences": sum(token_counter.values()),
        "unstructured_hex_token_distinct": len(token_counter),
    }
    if trace is None:
        record["log_trace_join"] = "NOT SUPPORTED — no traces.parquet in this raw sample"
    else:
        matching_trace_tokens = set(token_counter).intersection(
            {value.lower() for value in trace["trace_ids"]}
        )
        matching_span_tokens = set(token_counter).intersection(
            {value.lower() for value in trace["span_ids"]}
        )
        record["log_trace_join"] = {
            "classification": "TIME-WINDOW APPROXIMATION",
            "why_not_direct": "logs.parquet has no dedicated traceID/spanID column; any identity is embedded in unstructured message text",
            "message_tokens_matching_trace_ids": len(matching_trace_tokens),
            "message_tokens_matching_span_ids": len(matching_span_tokens),
            "timestamp_overlap_is_not_identity": True,
        }
    return record


def root_cause_file_evidence(case_dir: Path) -> dict | None:
    root_file = case_dir / "root_cause.txt"
    if not root_file.exists():
        return None
    fields = next(csv.reader(StringIO(root_file.read_text(encoding="utf-8").strip())))
    result = {
        "file_exists": True,
        "field_count": len(fields),
        "container_field": fields[2] if len(fields) > 2 else None,
        "contains_full_log_message": len(fields) > 3,
        "must_be_excluded_from_model_input": True,
    }
    log_path = case_dir / "logs.parquet"
    if log_path.exists() and len(fields) > 3:
        messages = pq.read_table(log_path, columns=["message"])["message"].to_pylist()
        result["exact_message_matches_in_logs"] = sum(value == fields[3] for value in messages)
    return result


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    results = []
    for item in plan["cases"]:
        case_dir = RAW_ROOT / item["case"]
        metrics_path = case_dir / "metrics.parquet"
        logs_path = case_dir / "logs.parquet"
        traces_path = case_dir / "traces.parquet"
        trace = trace_identity_and_time(traces_path) if traces_path.exists() else None
        if trace is not None:
            # Identity sets are used only during this audit; do not persist them.
            trace_summary = {key: value for key, value in trace.items() if key not in {"trace_ids", "span_ids"}}
        else:
            trace_summary = None
        metrics_time = pq.read_table(metrics_path, columns=["time"])["time"].to_pylist()
        results.append(
            {
                "case": item["case"],
                "metrics_time_range": min_max(metrics_time),
                "logs": log_evidence(logs_path, trace) if logs_path.exists() else None,
                "traces": trace_summary,
                "metrics_to_logs_join": "TIME-WINDOW APPROXIMATION" if logs_path.exists() else "NOT SUPPORTED",
                "metrics_to_traces_join": "TIME-WINDOW APPROXIMATION" if traces_path.exists() else "NOT SUPPORTED",
                "metric_entity_join": "SERVICE-LEVEL ONLY — metric names are wide-column tokens, not a shared identity key",
                "root_cause_file": root_cause_file_evidence(case_dir),
            }
        )
    output = {
        "scope": "RAW SAMPLE FINDING — six planned cases only",
        "reviewer_status": "MAIN-AGENT FALLBACK; independent Subagent E interrupted by execution quota",
        "cases": results,
    }
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "case_count": len(results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
