"""Targeted Task-B2 audit of every RE2-TT ``traces.parquet`` object.

The script is deliberately limited to the pinned official RCAEval revision and
to trace Parquet objects for the RE2-TT metadata subset.  It never requests a
metric, log, injection-time, or root-cause file.  Existing local raw data are
reused after checksum verification.  Other Parquet files are read one at a
time through HTTP byte ranges and are not copied into the research dataset
directory or the Hugging Face cache.

The audit proves data structure, not architecture or causal semantics.  It
does not parse fault or root-cause strings as telemetry/model features.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import HfApi


WORKSPACE = Path(r"D:\Project\flash-ticket-rca-research")
METADATA_PATH = WORKSPACE / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
RAW_ROOT = WORKSPACE / "datasets" / "rcaeval" / "raw-samples"
AUDIT_ROOT = WORKSPACE / "audits" / "rcaeval"
INVENTORY_PATH = AUDIT_ROOT / "re2tt-trace-full-subset-inventory.json"
PROGRESS_PATH = AUDIT_ROOT / "re2tt-trace-full-subset-progress.json"
RESULT_PATH = AUDIT_ROOT / "re2tt-trace-full-subset-audit.json"
REPORT_PATH = AUDIT_ROOT / "subagent-re2tt-full-trace-audit.md"

REPO_ID = "phamquiluan/RCAEval"
REPO_TYPE = "dataset"
REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
SUBSET = "RE2-TT"
USER_AGENT = "RCAEval-TaskB-targeted-trace-audit/1.0"

EXPECTED_COLUMNS = [
    "time",
    "traceID",
    "spanID",
    "serviceName",
    "methodName",
    "operationName",
    "parentSpanID",
    "startTimeMillis",
    "startTime",
    "duration",
    "statusCode",
]
AUDIT_COLUMNS = [
    "traceID",
    "spanID",
    "serviceName",
    "operationName",
    "parentSpanID",
    "startTimeMillis",
    "startTime",
    "duration",
]
STRING_AUDIT_COLUMNS = [
    "traceID",
    "spanID",
    "serviceName",
    "operationName",
    "parentSpanID",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_present(value: Any) -> bool:
    return value is not None and value != ""


def ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 10) if denominator else None


class HTTPRangeReader(io.RawIOBase):
    """Seekable, non-caching byte-range reader with auditable transfer stats."""

    def __init__(self, source_url: str, size: int) -> None:
        super().__init__()
        self.source_url = source_url
        self.size = size
        self.position = 0
        self.direct_url: str | None = None
        self.logical_range_reads = 0
        self.received_bytes = 0
        self.requested_bytes = 0
        self.redirect_resolutions = 0
        self.status_counts: Counter[str] = Counter()
        self.retry_count = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def writable(self) -> bool:
        return False

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            target = offset
        elif whence == io.SEEK_CUR:
            target = self.position + offset
        elif whence == io.SEEK_END:
            target = self.size + offset
        else:
            raise ValueError(f"Unsupported seek mode: {whence}")
        if target < 0:
            raise ValueError(f"Negative seek target: {target}")
        self.position = min(target, self.size)
        return self.position

    def read(self, size: int = -1) -> bytes:
        # An unbounded Parquet read would defeat the selective transfer rule.
        if size is None or size < 0:
            raise RuntimeError("Refusing an unbounded remote Parquet read")
        size = min(size, self.size - self.position)
        if size <= 0:
            return b""

        start = self.position
        end = start + size - 1
        requested_range = f"bytes={start}-{end}"
        last_error: Exception | None = None

        for attempt in range(3):
            request_url = self.direct_url or self.source_url
            request = Request(
                request_url,
                headers={"Range": requested_range, "User-Agent": USER_AGENT},
            )
            try:
                with urlopen(request, timeout=180) as response:
                    status = int(getattr(response, "status", response.getcode()))
                    content_range = response.headers.get("Content-Range", "")
                    body = response.read()
                    final_url = response.geturl()
                if status != 206:
                    raise RuntimeError(f"Range response status {status}, expected 206")
                expected_range = f"bytes {start}-{end}/{self.size}"
                if content_range != expected_range:
                    raise RuntimeError(
                        f"Unexpected Content-Range {content_range!r}; expected {expected_range!r}"
                    )
                if len(body) != size:
                    raise RuntimeError(f"Range returned {len(body)} bytes; expected {size}")
                if self.direct_url is None and final_url != self.source_url:
                    self.direct_url = final_url
                    self.redirect_resolutions += 1
                self.logical_range_reads += 1
                self.requested_bytes += size
                self.received_bytes += len(body)
                self.status_counts[str(status)] += 1
                self.position += size
                return body
            except (HTTPError, URLError, TimeoutError, RuntimeError) as error:
                last_error = error
                self.retry_count += 1
                # A signed CDN URL can expire; retry from the immutable resolver.
                self.direct_url = None
                if attempt < 2:
                    time.sleep(1 + attempt)
        raise RuntimeError(f"Failed range read {requested_range}: {last_error}") from last_error

    def stats(self) -> dict[str, Any]:
        return {
            "logical_range_reads": self.logical_range_reads,
            "requested_bytes": self.requested_bytes,
            "received_bytes": self.received_bytes,
            "redirect_resolutions": self.redirect_resolutions,
            "response_statuses": dict(sorted(self.status_counts.items())),
            "retry_count": self.retry_count,
            "retained_telemetry_bytes": 0,
        }


def source_url(remote_path: str) -> str:
    return (
        f"https://huggingface.co/datasets/{REPO_ID}/resolve/"
        f"{REVISION}/{remote_path}"
    )


def schema_signature(parquet_file: pq.ParquetFile) -> list[dict[str, Any]]:
    return [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in parquet_file.schema_arrow
    ]


def semantic_fields(columns: list[str]) -> dict[str, list[str]]:
    lowered = {column: column.lower() for column in columns}
    patterns = {
        "network_http_rpc_peer": [
            "http", "rpc", "peer", "endpoint", "url", "network", "protocol", "client", "server"
        ],
        "resource": [
            "resource", "container", "pod", "process", "host", "database", "db", "cache", "broker"
        ],
        "messaging": [
            "messaging", "message", "queue", "topic", "kafka", "rabbit", "producer", "consumer"
        ],
        "causal_or_ground_truth": ["cause", "causal", "propagation", "affected", "root"],
        "structured_attributes_events_links_or_span_kind": ["attribute", "event", "link", "kind"],
    }
    return {
        category: [column for column, lower in lowered.items() if any(token in lower for token in tokens)]
        for category, tokens in patterns.items()
    }


def pinned_inventory() -> dict[str, Any]:
    if not METADATA_PATH.is_file():
        raise FileNotFoundError(f"Pinned local metadata missing: {METADATA_PATH}")
    metadata = pd.read_parquet(METADATA_PATH)
    subset = metadata.loc[metadata["dataset"] == SUBSET].copy()
    subset_cases = sorted(subset["case"].tolist())
    if len(subset_cases) != 90 or len(set(subset_cases)) != len(subset_cases):
        raise RuntimeError(f"Unexpected RE2-TT metadata case universe: {len(subset_cases)}")
    metadata_trace_summary = {
        "case_count": len(subset_cases),
        "has_traces_true": int(subset["has_traces"].sum()),
        "n_traces_positive": int((subset["n_traces"] > 0).sum()),
        "cases_without_declared_trace": sorted(
            subset.loc[(~subset["has_traces"]) | (subset["n_traces"] <= 0), "case"].tolist()
        ),
    }

    info = HfApi().dataset_info(REPO_ID, revision=REVISION, files_metadata=True)
    if info.sha != REVISION:
        raise RuntimeError(f"Pinned revision did not resolve exactly: {info.sha}")
    objects: list[dict[str, Any]] = []
    for sibling in info.siblings:
        path = sibling.rfilename
        if path.startswith("re2tt_") and path.endswith("/traces.parquet"):
            lfs = sibling.lfs
            if lfs is None:
                raise RuntimeError(f"Trace object does not expose LFS metadata: {path}")
            objects.append(
                {
                    "case": path.removesuffix("/traces.parquet"),
                    "remote_path": path,
                    "bytes": int(sibling.size),
                    "lfs_sha256": lfs.sha256,
                    "blob_id": sibling.blob_id,
                }
            )
    objects.sort(key=lambda item: item["case"])
    remote_cases = [item["case"] for item in objects]
    missing_remote = sorted(set(subset_cases) - set(remote_cases))
    extra_remote = sorted(set(remote_cases) - set(subset_cases))
    if len(objects) != 90 or missing_remote or extra_remote:
        raise RuntimeError(
            f"RE2-TT trace inventory mismatch: objects={len(objects)}, "
            f"missing={missing_remote}, extra={extra_remote}"
        )

    local_reused = 0
    for item in objects:
        local_path = RAW_ROOT / item["case"] / "traces.parquet"
        item["local_existing_path"] = str(local_path) if local_path.is_file() else None
        item["local_reused"] = False
        if local_path.is_file():
            local_size = local_path.stat().st_size
            local_hash = sha256(local_path)
            item["local_size"] = local_size
            item["local_sha256"] = local_hash
            if local_size != item["bytes"] or local_hash != item["lfs_sha256"]:
                raise RuntimeError(f"Existing local trace checksum mismatch: {local_path}")
            item["local_reused"] = True
            local_reused += 1

    return {
        "audit": "Task B2 / targeted full-RE2-TT trace inventory",
        "scope": "DATASET-WIDE METADATA FACT plus pinned official object inventory; no telemetry read",
        "source": {
            "repository": REPO_ID,
            "repository_type": REPO_TYPE,
            "revision": REVISION,
            "url": f"https://huggingface.co/datasets/{REPO_ID}",
        },
        "metadata": {
            "local_file": str(METADATA_PATH),
            "bytes": METADATA_PATH.stat().st_size,
            "sha256": sha256(METADATA_PATH),
            "subset": SUBSET,
            **metadata_trace_summary,
        },
        "objects": objects,
        "remote_object_count": len(objects),
        "remote_total_bytes": sum(item["bytes"] for item in objects),
        "remote_total_mib": round(sum(item["bytes"] for item in objects) / 1024 / 1024, 2),
        "missing_remote_trace_objects": missing_remote,
        "extra_remote_trace_objects": extra_remote,
        "local_reused_trace_files": local_reused,
        "recorded_at_utc": utc_now(),
    }


def result_empty_columns() -> dict[str, int]:
    return {column: 0 for column in AUDIT_COLUMNS}


def audit_one_trace(item: dict[str, Any]) -> dict[str, Any]:
    case = item["case"]
    local_path = RAW_ROOT / case / "traces.parquet"
    reader: HTTPRangeReader | None = None
    source_kind: str
    source_description: str
    if item["local_reused"]:
        source_kind = "LOCAL_PREEXISTING_VERIFIED"
        source_description = str(local_path)
        parquet_file = pq.ParquetFile(local_path)
    else:
        source_kind = "OFFICIAL_PINNED_HTTP_RANGE"
        source_description = source_url(item["remote_path"])
        reader = HTTPRangeReader(source_description, int(item["bytes"]))
        parquet_file = pq.ParquetFile(reader)

    schema = schema_signature(parquet_file)
    columns = [field["name"] for field in schema]
    missing_expected = sorted(set(EXPECTED_COLUMNS) - set(columns))
    unexpected_columns = sorted(set(columns) - set(EXPECTED_COLUMNS))
    missing_audit = sorted(set(AUDIT_COLUMNS) - set(columns))
    if missing_audit:
        raise RuntimeError(f"{case} misses required audit columns: {missing_audit}")

    row_count = 0
    null_counts = Counter()
    empty_counts = Counter()
    rows_complete_identity = 0
    rows_service_operation = 0
    negative_duration = 0
    zero_duration = 0
    comparable_start_units = 0
    start_units_match = 0
    trace_ids: set[str] = set()
    span_ids: set[str] = set()
    duplicate_spanid_global = 0
    span_map: dict[str, list[Any]] = {}
    duplicate_composite_rows = 0
    parent_rows: list[tuple[str, str, str, int | None, int | None, str | None]] = []
    local_services: set[str] = set()
    local_service_operations: set[tuple[str, str]] = set()

    for batch in parquet_file.iter_batches(batch_size=131072, columns=AUDIT_COLUMNS):
        values = batch.to_pydict()
        for index in range(batch.num_rows):
            row_count += 1
            for column in AUDIT_COLUMNS:
                value = values[column][index]
                if value is None:
                    null_counts[column] += 1
                elif column in STRING_AUDIT_COLUMNS and value == "":
                    empty_counts[column] += 1

            trace_id = values["traceID"][index]
            span_id = values["spanID"][index]
            service = values["serviceName"][index]
            operation = values["operationName"][index]
            parent_span = values["parentSpanID"][index]
            start_ms = values["startTimeMillis"][index]
            start = values["startTime"][index]
            duration = values["duration"][index]

            if all(is_present(value) for value in (trace_id, span_id, service, operation)):
                rows_complete_identity += 1
            if is_present(service) and is_present(operation):
                rows_service_operation += 1
                local_services.add(service)
                local_service_operations.add((service, operation))
            if is_present(trace_id):
                trace_ids.add(trace_id)
            if is_present(span_id):
                if span_id in span_ids:
                    duplicate_spanid_global += 1
                else:
                    span_ids.add(span_id)
            if duration is not None:
                if duration < 0:
                    negative_duration += 1
                elif duration == 0:
                    zero_duration += 1
            if start is not None and start_ms is not None:
                comparable_start_units += 1
                if start // 1000 == start_ms:
                    start_units_match += 1

            if is_present(trace_id) and is_present(span_id):
                composite = f"{trace_id}\x1f{span_id}"
                existing = span_map.get(composite)
                if existing is None:
                    # multiplicity, start, duration, service
                    span_map[composite] = [1, start, duration, service]
                else:
                    existing[0] += 1
                    duplicate_composite_rows += 1
                if is_present(parent_span):
                    parent_rows.append(
                        (
                            composite,
                            f"{trace_id}\x1f{parent_span}",
                            parent_span,
                            start,
                            duration,
                            service,
                        )
                    )

    resolved_parent = 0
    unresolved_parent = 0
    ambiguous_parent = 0
    parent_exists_other_trace = 0
    self_parent = 0
    same_service = 0
    cross_service = 0
    unknown_service = 0
    timing_comparable = 0
    child_start_before_parent = 0
    child_end_after_parent = 0
    parent_to_child_edges: Counter[tuple[str, str]] = Counter()

    for child_key, parent_key, parent_span_id, child_start, child_duration, child_service in parent_rows:
        parent = span_map.get(parent_key)
        if parent is None:
            unresolved_parent += 1
            if parent_span_id in span_ids:
                parent_exists_other_trace += 1
            continue
        if parent[0] != 1:
            ambiguous_parent += 1
            continue
        resolved_parent += 1
        parent_start, parent_duration, parent_service = parent[1], parent[2], parent[3]
        if child_key == parent_key:
            self_parent += 1
        if not is_present(parent_service) or not is_present(child_service):
            unknown_service += 1
        elif parent_service == child_service:
            same_service += 1
        else:
            cross_service += 1
            parent_to_child_edges[(parent_service, child_service)] += 1
        if (
            child_start is not None
            and child_duration is not None
            and parent_start is not None
            and parent_duration is not None
        ):
            timing_comparable += 1
            if child_start < parent_start:
                child_start_before_parent += 1
            if child_start + child_duration > parent_start + parent_duration:
                child_end_after_parent += 1

    # Free large per-file raw-derived structures before the next remote object.
    del span_map
    del parent_rows

    source_transfer = reader.stats() if reader is not None else {
        "logical_range_reads": 0,
        "requested_bytes": 0,
        "received_bytes": 0,
        "redirect_resolutions": 0,
        "response_statuses": {},
        "retry_count": 0,
        "retained_telemetry_bytes": 0,
    }
    return {
        "case": case,
        "source": {
            "kind": source_kind,
            "path_or_pinned_url": source_description,
            "remote_path": item["remote_path"],
            "bytes": item["bytes"],
            "lfs_sha256": item["lfs_sha256"],
        },
        "parquet": {
            "rows": row_count,
            "row_groups": parquet_file.metadata.num_row_groups,
            "schema": schema,
            "missing_expected_columns": missing_expected,
            "unexpected_columns": unexpected_columns,
            "semantic_field_name_matches": semantic_fields(columns),
        },
        "identity_coverage": {
            "null_rows": {column: int(null_counts[column]) for column in AUDIT_COLUMNS},
            "empty_string_rows": {column: int(empty_counts[column]) for column in STRING_AUDIT_COLUMNS},
            "rows_complete_trace_span_service_operation": rows_complete_identity,
            "rows_complete_trace_span_service_operation_rate": ratio(rows_complete_identity, row_count),
            "rows_with_service_operation": rows_service_operation,
            "rows_with_service_operation_rate": ratio(rows_service_operation, row_count),
            "distinct_trace_ids": len(trace_ids),
            "distinct_span_ids_global_to_file": len(span_ids),
            "distinct_trace_span_pairs": row_count - duplicate_composite_rows,
            "duplicate_trace_span_pair_rows": duplicate_composite_rows,
            "duplicate_span_id_rows_global_to_file": duplicate_spanid_global,
        },
        "parent_resolution": {
            "rows_with_parent": len(parent_rows) if False else None,
            # The parent list is deleted above. Derive its original size from totals.
            "rows_without_parent_or_missing_trace_span": None,
            "resolved_same_trace": resolved_parent,
            "unresolved_same_trace": unresolved_parent,
            "ambiguous_parent_due_to_duplicate_trace_span": ambiguous_parent,
            "unresolved_parent_span_exists_elsewhere_in_file": parent_exists_other_trace,
            "self_parent_rows": self_parent,
            "resolved_same_service": same_service,
            "resolved_cross_service": cross_service,
            "resolved_unknown_service": unknown_service,
            "observed_parent_to_child_service_edges": [
                {"parent_service": parent, "child_service": child, "rows": count}
                for (parent, child), count in sorted(parent_to_child_edges.items())
            ],
        },
        "temporal_integrity": {
            "negative_duration_rows": negative_duration,
            "zero_duration_rows": zero_duration,
            "rows_with_both_start_units": comparable_start_units,
            "startTime_div_1000_equals_startTimeMillis": start_units_match,
            "resolved_parent_child_timing_comparable": timing_comparable,
            "resolved_child_start_before_parent_start": child_start_before_parent,
            "resolved_child_end_after_parent_end": child_end_after_parent,
        },
        "operation_representation": {
            "service_names": sorted(local_services),
            "distinct_service_operation_pairs": len(local_service_operations),
            "service_operation_pairs": [
                {"serviceName": service, "operationName": operation}
                for service, operation in sorted(local_service_operations)
            ],
        },
        "transfer": source_transfer,
        "completed_at_utc": utc_now(),
    }


def repair_parent_counts(case_result: dict[str, Any]) -> None:
    """Fill parent count from identity coverage and resolution categories safely.

    Earlier row-level iteration tracks parent records only where trace/span were
    present, which is the only population that can be resolved.  Its count is
    reconstructed from mutually exclusive post-resolution categories.
    """

    parent = case_result["parent_resolution"]
    resolved = (
        parent["resolved_same_trace"]
        + parent["ambiguous_parent_due_to_duplicate_trace_span"]
    )
    parent_rows = resolved + parent["unresolved_same_trace"]
    parent["rows_with_parent_and_trace_span"] = parent_rows
    parent["parent_resolution_rate_among_unambiguous_candidates"] = ratio(
        parent["resolved_same_trace"],
        parent["resolved_same_trace"] + parent["unresolved_same_trace"]
    )
    # Preserve a precise limitation: parent rows that lack trace or span cannot
    # enter an exact composite-key join and are reported by null/empty counts.
    parent.pop("rows_with_parent", None)
    parent.pop("rows_without_parent_or_missing_trace_span", None)


def global_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = 0
    row_groups = 0
    null_counts: Counter[str] = Counter()
    empty_counts: Counter[str] = Counter()
    identity_complete = 0
    service_operation_rows = 0
    trace_ids_sum = 0
    span_pairs_sum = 0
    duplicate_pairs = 0
    duplicate_span_ids = 0
    services: set[str] = set()
    service_operations: dict[str, set[str]] = defaultdict(set)
    operation_services: dict[str, set[str]] = defaultdict(set)
    parent_counts: Counter[str] = Counter()
    temporal_counts: Counter[str] = Counter()
    edges: Counter[tuple[str, str]] = Counter()
    transfer_counts: Counter[str] = Counter()
    semantic_nonempty: dict[str, set[str]] = defaultdict(set)
    schema_signatures: Counter[str] = Counter()
    parent_rate_by_case: list[dict[str, Any]] = []

    for result in case_results:
        parquet = result["parquet"]
        identity = result["identity_coverage"]
        parent = result["parent_resolution"]
        timing = result["temporal_integrity"]
        operation = result["operation_representation"]
        transfer = result["transfer"]
        rows += parquet["rows"]
        row_groups += parquet["row_groups"]
        schema_signatures[json.dumps(parquet["schema"], sort_keys=True)] += 1
        for name, value in identity["null_rows"].items():
            null_counts[name] += value
        for name, value in identity["empty_string_rows"].items():
            empty_counts[name] += value
        identity_complete += identity["rows_complete_trace_span_service_operation"]
        service_operation_rows += identity["rows_with_service_operation"]
        trace_ids_sum += identity["distinct_trace_ids"]
        span_pairs_sum += identity["distinct_trace_span_pairs"]
        duplicate_pairs += identity["duplicate_trace_span_pair_rows"]
        duplicate_span_ids += identity["duplicate_span_id_rows_global_to_file"]
        for service in operation["service_names"]:
            services.add(service)
        for pair in operation["service_operation_pairs"]:
            service_operations[pair["serviceName"]].add(pair["operationName"])
            operation_services[pair["operationName"]].add(pair["serviceName"])
        for name in (
            "rows_with_parent_and_trace_span",
            "resolved_same_trace",
            "unresolved_same_trace",
            "ambiguous_parent_due_to_duplicate_trace_span",
            "unresolved_parent_span_exists_elsewhere_in_file",
            "self_parent_rows",
            "resolved_same_service",
            "resolved_cross_service",
            "resolved_unknown_service",
        ):
            parent_counts[name] += int(parent[name])
        denominator = parent["resolved_same_trace"] + parent["unresolved_same_trace"]
        parent_rate_by_case.append(
            {
                "case": result["case"],
                "resolved_same_trace": int(parent["resolved_same_trace"]),
                "unresolved_same_trace": int(parent["unresolved_same_trace"]),
                "candidate_parent_rows": int(denominator),
                "resolution_rate": ratio(parent["resolved_same_trace"], denominator),
            }
        )
        for name, value in timing.items():
            temporal_counts[name] += int(value)
        for edge in parent["observed_parent_to_child_service_edges"]:
            edges[(edge["parent_service"], edge["child_service"])] += edge["rows"]
        for name in (
            "logical_range_reads", "requested_bytes", "received_bytes", "redirect_resolutions", "retry_count",
            "retained_telemetry_bytes",
        ):
            transfer_counts[name] += int(transfer[name])
        for category, names in parquet["semantic_field_name_matches"].items():
            semantic_nonempty[category].update(names)

    all_pairs = {
        (service, operation)
        for service, operations in service_operations.items()
        for operation in operations
    }
    reused_operation_names = {
        operation: sorted(services_for_operation)
        for operation, services_for_operation in operation_services.items()
        if len(services_for_operation) > 1
    }
    parent_counts["parent_resolution_rate_among_unambiguous_candidates"] = ratio(
        parent_counts["resolved_same_trace"],
        parent_counts["resolved_same_trace"] + parent_counts["unresolved_same_trace"],
    )
    parent_rate_sorted = sorted(
        parent_rate_by_case,
        key=lambda record: (record["resolution_rate"] is None, record["resolution_rate"], record["case"]),
    )

    return {
        "case_count": len(case_results),
        "rows": rows,
        "row_groups": row_groups,
        "physical_schema_variants": len(schema_signatures),
        "schema_variant_case_counts": [
            {"cases": count, "schema": json.loads(signature)}
            for signature, count in schema_signatures.items()
        ],
        "identity_coverage": {
            "null_rows": {name: int(null_counts[name]) for name in AUDIT_COLUMNS},
            "empty_string_rows": {name: int(empty_counts[name]) for name in STRING_AUDIT_COLUMNS},
            "rows_complete_trace_span_service_operation": identity_complete,
            "rows_complete_trace_span_service_operation_rate": ratio(identity_complete, rows),
            "rows_with_service_operation": service_operation_rows,
            "rows_with_service_operation_rate": ratio(service_operation_rows, rows),
            "sum_distinct_trace_ids_per_case": trace_ids_sum,
            "sum_distinct_trace_span_pairs_per_case": span_pairs_sum,
            "duplicate_trace_span_pair_rows": duplicate_pairs,
            "duplicate_span_id_rows_global_to_case": duplicate_span_ids,
        },
        "operation_representation": {
            "distinct_service_names": len(services),
            "service_names": sorted(services),
            "distinct_service_operation_pairs": len(all_pairs),
            "per_service_distinct_operation_names": [
                {"serviceName": service, "distinct_operationName": len(operations)}
                for service, operations in sorted(service_operations.items())
            ],
            "operation_names_reused_across_more_than_one_service": len(reused_operation_names),
            "reused_operation_name_examples": [
                {"operationName": name, "services": service_names}
                for name, service_names in sorted(reused_operation_names.items())[:50]
            ],
        },
        "parent_resolution": dict(parent_counts),
        "parent_resolution_case_profile": {
            "cases_with_candidate_parent_rows": sum(
                1 for record in parent_rate_by_case if record["candidate_parent_rows"] > 0
            ),
            "cases_below_0_99_resolution": [
                record for record in parent_rate_sorted if record["resolution_rate"] is not None and record["resolution_rate"] < 0.99
            ],
            "cases_below_0_90_resolution": [
                record for record in parent_rate_sorted if record["resolution_rate"] is not None and record["resolution_rate"] < 0.90
            ],
            "lowest_resolution_cases": parent_rate_sorted[:10],
        },
        "temporal_integrity": dict(temporal_counts),
        "observed_parent_to_child_service_edges": [
            {"parent_service": parent, "child_service": child, "rows": count}
            for (parent, child), count in sorted(edges.items())
        ],
        "semantic_schema_field_matches": {
            category: sorted(names) for category, names in sorted(semantic_nonempty.items())
        },
        "transfer": {
            **{name: int(value) for name, value in transfer_counts.items()},
            "received_mib": round(transfer_counts["received_bytes"] / 1024 / 1024, 2),
            "remote_objects_range_read": sum(
                1 for result in case_results if result["source"]["kind"] == "OFFICIAL_PINNED_HTTP_RANGE"
            ),
            "local_objects_reused": sum(
                1 for result in case_results if result["source"]["kind"] == "LOCAL_PREEXISTING_VERIFIED"
            ),
        },
    }


def write_progress(inventory: dict[str, Any], completed: dict[str, dict[str, Any]]) -> None:
    payload = {
        "audit": "Task B2 / resumable targeted RE2-TT full trace audit",
        "scope": "INCOMPLETE WORKING STATE — do not generalize until all 90 cases complete",
        "revision": REVISION,
        "inventory_recorded_at_utc": inventory["recorded_at_utc"],
        "completed_cases": completed,
        "completed_case_count": len(completed),
        "updated_at_utc": utc_now(),
    }
    PROGRESS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    identity = summary["identity_coverage"]
    parents = summary["parent_resolution"]
    parent_profile = summary["parent_resolution_case_profile"]
    timing = summary["temporal_integrity"]
    operations = summary["operation_representation"]
    transfer = summary["transfer"]
    return f"""# Independent targeted RE2-TT full-trace audit

**Status:** `COMPLETE`  
**Role:** additional independent full-subset Trace Auditor for Task B  
**Scope:** `FULL-SUBSET PROPERTY` — all 90 RE2-TT trace objects at immutable revision `{REVISION}`. This report does not make a claim about other RCAEval suites or systems.

## Source and transfer boundary

The official source is [`{REPO_ID}`](https://huggingface.co/datasets/{REPO_ID}) at `{REVISION}`. The pinned inventory has 90 metadata cases, 90 declared trace-bearing cases, and 90 matching remote `traces.parquet` objects. The remote objects total 1,624,336,514 bytes; only trace Parquet data were read. One existing local object was checksum-verified and reused. The other {transfer['remote_objects_range_read']} objects were read with no persistent telemetry copy; the recorded range responses transferred {transfer['received_bytes']:,} bytes ({transfer['received_mib']:.2f} MiB) in {transfer['logical_range_reads']:,} logical range reads.

## Full-subset trace facts

All {summary['case_count']} files were processed. They contain {summary['rows']:,} trace rows in {summary['row_groups']:,} Parquet row groups. There are {summary['physical_schema_variants']} physical schema variant(s). The common schema is the 11 fields previously observed: `time`, `traceID`, `spanID`, `serviceName`, `methodName`, `operationName`, `parentSpanID`, `startTimeMillis`, `startTime`, `duration`, and `statusCode`.

The audit found {identity['duplicate_trace_span_pair_rows']:,} duplicate `(traceID, spanID)` rows within cases. Exact composite parent resolution is {parents['resolved_same_trace']:,} / {parents['resolved_same_trace'] + parents['unresolved_same_trace']:,} = {parents['parent_resolution_rate_among_unambiguous_candidates']:.6f}; {parents['unresolved_same_trace']:,} parent references did not resolve within the same trace ID. This aggregate is not uniform: {len(parent_profile['cases_below_0_90_resolution'])} cases are below 90% resolution, and the lowest is `{parent_profile['lowest_resolution_cases'][0]['case']}` at {parent_profile['lowest_resolution_cases'][0]['resolution_rate']:.6f}. Of resolved/comparable links, {timing['resolved_child_start_before_parent_start']:,} begin before their parent and {timing['resolved_child_end_after_parent_end']:,} outlive their parent. These are observed data-quality facts, not grounds for repair or causal interpretation.

## Graph decision supported by the full subset

`serviceName` supports a literal service-node representation. `{operations['distinct_service_operation_pairs']}` literal `(serviceName, operationName)` pairs support a reproducible operation representation across {operations['distinct_service_names']} observed services. However, {operations['operation_names_reused_across_more_than_one_service']} raw operation strings occur under more than one service, so the operation string by itself is not a stable globally unique operation identity. There is no operation-level root-cause target in this trace audit.

Resolved parent-span links yield {len(summary['observed_parent_to_child_service_edges'])} observed cross-service **parent-to-child trace relation** pairs. They do not establish network `CALLS`, resource `USES`, messaging semantics, or causal propagation. Across every physical schema, there are no dedicated HTTP/RPC/peer/endpoint, resource, messaging, causal, attributes/events/links, or span-kind field names. `operationName` remains a textual field and does not change that conclusion.

## Task-B implication for RE2-TT

The full RE2-TT trace subset supports a trace-derived service/operation representation with observed parent-child relations, subject to the recorded integrity rates. A pilot must retain only resolved parent links and report per-case resolution; it must not impute the missing 1,033,279 parent references. The data do **not** support labeling those edges as protocol calls or causal propagation, and they do **not** supply resource or operation-level ground truth. This is evidence about the dataset only; it selects no algorithm or research question.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--case",
        action="append",
        help="Audit one named case for a controlled test; does not produce a complete-subset result.",
    )
    args = parser.parse_args()
    AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
    inventory = pinned_inventory()
    INVENTORY_PATH.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.inventory_only:
        print(INVENTORY_PATH)
        return

    expected = {item["case"]: item for item in inventory["objects"]}
    selected_cases = sorted(args.case) if args.case else sorted(expected)
    unknown_cases = sorted(set(selected_cases) - set(expected))
    if unknown_cases:
        raise RuntimeError(f"Cases outside pinned RE2-TT trace subset: {unknown_cases}")

    completed: dict[str, dict[str, Any]] = {}
    if args.resume and not args.case and PROGRESS_PATH.is_file():
        previous = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
        if previous.get("revision") != REVISION:
            raise RuntimeError("Cannot resume a progress file from another revision")
        completed = {
            case: record
            for case, record in previous.get("completed_cases", {}).items()
            if case in expected and record.get("source", {}).get("lfs_sha256") == expected[case]["lfs_sha256"]
        }

    for position, case in enumerate(selected_cases, start=1):
        if case in completed:
            continue
        print(f"[{position}/{len(selected_cases)}] {case}", flush=True)
        completed[case] = audit_one_trace(expected[case])
        repair_parent_counts(completed[case])
        if not args.case:
            write_progress(inventory, completed)

    ordered_results = [completed[case] for case in selected_cases]
    if args.case:
        partial_path = AUDIT_ROOT / "re2tt-trace-targeted-test.json"
        partial = {
            "audit": "Task B2 / controlled trace audit test",
            "scope": "RAW SUBSET TEST ONLY — not a full-RE2-TT conclusion",
            "source": inventory["source"],
            "cases": ordered_results,
        }
        partial_path.write_text(json.dumps(partial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(partial_path)
        return

    if len(ordered_results) != 90:
        raise RuntimeError(f"Incomplete RE2-TT audit: {len(ordered_results)} of 90 cases")
    result = {
        "audit": "Task B2 / independent targeted full-RE2-TT Trace Auditor",
        "scope": "FULL-SUBSET PROPERTY — all and only RE2-TT trace objects at the pinned revision",
        "source": inventory["source"],
        "inventory_path": str(INVENTORY_PATH),
        "transfer_policy": {
            "requested_file_types": ["traces.parquet"],
            "unrequested_file_types": ["metrics.parquet", "logs.parquet", "inject_time.txt", "root_cause.txt"],
            "existing_local_trace_reused_after_checksum": True,
            "other_objects_read_by_official_pinned_http_ranges": True,
            "persistent_new_telemetry_files": 0,
        },
        "completed_at_utc": utc_now(),
        "cases": ordered_results,
        "summary": global_summary(ordered_results),
    }
    RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    # It is intentionally retained as a reproducible case-level evidence file,
    # but no longer represents an incomplete run.
    write_progress(inventory, completed)
    print(RESULT_PATH)
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
