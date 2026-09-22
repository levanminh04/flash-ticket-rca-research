"""Audit resource observability in the six pinned RCAEval raw samples.

This script deliberately distinguishes literal telemetry labels from semantic
resource facts. A metric-column prefix or log container_name is recorded as
raw evidence, but is never promoted to a host, database, cache, broker, or
queue identity without a dedicated structured identity and relationship.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


DEFAULT_ROOT = Path(r"D:\Project\flash-ticket-rca-research")
METRIC_SUFFIXES = (
    "_latency-50",
    "_latency-90",
    "_diskio",
    "_workload",
    "_socket",
    "_error",
    "_load",
    "_latency",
    "_cpu",
    "_mem",
)
RESOURCE_LEXEMES = {
    "host": ("host", "hostname", "node", "instance"),
    "database": ("mongo", "mysql", "postgres", "database", "-db"),
    "cache": ("redis", "memcached", "cache"),
    "broker": ("rabbitmq", "kafka", "broker"),
    "queue_topic": ("queue", "topic"),
}
DIRECT_ID_FIELD_PATTERNS = {
    "host": ("host", "hostname", "node", "node_id", "instance"),
    "pod_container": (
        "pod",
        "pod_name",
        "pod_uid",
        "container",
        "container_id",
        "container_name",
        "docker_id",
    ),
    "database": ("db", "db_name", "database", "database_name", "db_system"),
    "logical_database": ("schema", "catalog", "database", "db_name"),
    "cache": ("cache", "redis", "memcached"),
    "broker": ("broker", "rabbitmq", "kafka"),
    "queue_topic": ("queue", "queue_name", "topic", "topic_name"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Defaults to audits/rcaeval/subagent-resource-observability-evidence.json.",
    )
    return parser.parse_args()


def metric_entity_prefix(column: str) -> str | None:
    for suffix in METRIC_SUFFIXES:
        if column.endswith(suffix):
            return column[: -len(suffix)]
    return None


def matching_lexemes(values: list[str], lexemes: tuple[str, ...]) -> list[str]:
    return sorted(value for value in values if any(term in value.lower() for term in lexemes))


def field_hits(fields: list[str], type_name: str) -> list[str]:
    exact = set(DIRECT_ID_FIELD_PATTERNS[type_name])
    return sorted(field for field in fields if field.lower() in exact)


def scan_message_tokens(messages: list[Any]) -> dict[str, int]:
    values = [str(value) for value in messages if value is not None]
    result: dict[str, int] = {}
    for resource_type, lexemes in RESOURCE_LEXEMES.items():
        count = sum(
            any(re.search(rf"(?i)(?<![\w-]){re.escape(term)}(?![\w-])", value) for term in lexemes)
            for value in values
        )
        result[resource_type] = count
    return result


def classify() -> dict[str, dict[str, Any]]:
    """Return classifications fixed by the evidence rule used in this audit."""
    return {
        "host": {
            "classification": "NOT SUPPORTED",
            "reason": "No structured host/node/hostname identifier field exists in any sampled Parquet schema.",
            "graph_node": "No",
            "uses_edge": "No",
        },
        "pod/container": {
            "classification": "ATTRIBUTE ONLY",
            "reason": "logs.parquet has a literal container_name column, but no pod UID, container ID, host/node, lifecycle, or telemetry relation that proves an instance-level node.",
            "graph_node": "No resource node; container_name may remain an attribute of a log row.",
            "uses_edge": "No",
        },
        "database": {
            "classification": "REQUIRES EXTERNAL MAPPING",
            "reason": "Metric and container labels contain lexical strings such as -mongo, -mysql, and -db, but the raw schema has no db.system, database identifier, endpoint, connection, or service-to-database relation.",
            "graph_node": "No database node from this dataset alone.",
            "uses_edge": "No; an external mapping would be required and must be separately governed.",
        },
        "logical_database": {
            "classification": "NOT SUPPORTED",
            "reason": "No schema/catalog/database-name field or logical-database identifier occurs in the sampled structured telemetry.",
            "graph_node": "No",
            "uses_edge": "No",
        },
        "cache": {
            "classification": "REQUIRES EXTERNAL MAPPING",
            "reason": "Literal redis/cache strings occur in labels or message text, but there is no cache-specific structured identity, endpoint, or service-to-cache relation.",
            "graph_node": "No cache node from this dataset alone.",
            "uses_edge": "No",
        },
        "broker": {
            "classification": "REQUIRES EXTERNAL MAPPING",
            "reason": "Literal rabbitmq/broker strings occur in labels or message text, but no broker ID, protocol attribute, producer/consumer field, or relation is present.",
            "graph_node": "No broker node from this dataset alone.",
            "uses_edge": "No",
        },
        "queue/topic": {
            "classification": "NOT SUPPORTED",
            "reason": "No queue name, topic name, producer/consumer, messaging destination, or message key is a structured field. queue-master is only a literal label, not a queue/topic identity.",
            "graph_node": "No",
            "uses_edge": "No",
        },
        "other": {
            "classification": "ATTRIBUTE ONLY",
            "reason": "Raw metrics have opaque literal series prefixes and logs have literal container_name values; neither includes a typed resource identity or a runtime USES relationship.",
            "graph_node": "No typed resource node; an opaque series label may only remain a feature/attribute under an explicit loader rule.",
            "uses_edge": "No",
        },
    }


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    raw_root = root / "datasets" / "rcaeval" / "raw-samples"
    manifest_path = raw_root / "raw-download-manifest.json"
    output = args.output or root / "audits" / "rcaeval" / "subagent-resource-observability-evidence.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    all_fields: set[str] = set()
    modal_schema: dict[str, set[tuple[str, str]]] = defaultdict(set)
    cases: dict[str, Any] = {}
    aggregate_metric_prefixes: set[str] = set()
    aggregate_containers: set[str] = set()
    lexical_prefixes: dict[str, set[str]] = defaultdict(set)
    log_message_token_total: Counter[str] = Counter()

    for case_entry in manifest["cases"]:
        case = case_entry["case"]
        case_data: dict[str, Any] = {"modalities": {}}
        for file_entry in case_entry["files"]:
            path = Path(file_entry["local_path"])
            if path.suffix != ".parquet":
                continue
            modality = path.stem
            parquet_file = pq.ParquetFile(path)
            schema = parquet_file.schema_arrow
            fields = [field.name for field in schema]
            all_fields.update(fields)
            modal_schema[modality].update((field.name, str(field.type)) for field in schema)
            modality_data: dict[str, Any] = {
                "rows": parquet_file.metadata.num_rows,
                "fields": [{"name": field.name, "type": str(field.type)} for field in schema],
            }
            if modality == "metrics":
                prefixes = sorted(
                    prefix
                    for column in fields
                    if (prefix := metric_entity_prefix(column)) is not None
                )
                unique_prefixes = sorted(set(prefixes))
                aggregate_metric_prefixes.update(unique_prefixes)
                lexical: dict[str, list[str]] = {}
                for resource_type, lexemes in RESOURCE_LEXEMES.items():
                    lexical[resource_type] = matching_lexemes(unique_prefixes, lexemes)
                    lexical_prefixes[resource_type].update(lexical[resource_type])
                modality_data["metric_entity_prefix_count"] = len(unique_prefixes)
                modality_data["resource_lexical_prefixes"] = lexical
            elif modality == "logs":
                table = parquet_file.read(columns=["container_name", "message"])
                columns = table.to_pydict()
                containers = sorted(
                    {str(value) for value in columns.get("container_name", []) if value is not None}
                )
                aggregate_containers.update(containers)
                modality_data["container_name_non_null_count"] = sum(
                    value is not None for value in columns.get("container_name", [])
                )
                modality_data["container_name_distinct_literals"] = containers
                modality_data["message_resource_token_row_counts"] = scan_message_tokens(
                    columns.get("message", [])
                )
                log_message_token_total.update(modality_data["message_resource_token_row_counts"])
            elif modality == "traces":
                modality_data["nested_or_map_fields"] = [
                    {"name": field.name, "type": str(field.type)}
                    for field in schema
                    if any(token in str(field.type).lower() for token in ("struct", "map", "list"))
                ]
            case_data["modalities"][modality] = modality_data
        cases[case] = case_data

    per_type_field_hits = {
        resource_type: field_hits(sorted(all_fields), resource_type)
        for resource_type in DIRECT_ID_FIELD_PATTERNS
    }
    result = {
        "scope": "RAW SAMPLE FINDING — six pinned cases only; resource type semantics are not inferred from lexical labels",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": manifest["source"],
        "integrity_precondition": {
            "manifest_path": str(manifest_path),
            "case_count": len(manifest["cases"]),
            "file_count": sum(len(case["files"]) for case in manifest["cases"]),
        },
        "all_structured_field_names": sorted(all_fields),
        "schema_by_modality": {
            modality: [
                {"name": name, "type": field_type}
                for name, field_type in sorted(fields, key=lambda item: item[0])
            ]
            for modality, fields in sorted(modal_schema.items())
        },
        "dedicated_identity_field_hits": per_type_field_hits,
        "metric_entity_prefixes": {
            "count": len(aggregate_metric_prefixes),
            "resource_lexical_prefixes": {
                resource_type: sorted(values) for resource_type, values in sorted(lexical_prefixes.items())
            },
        },
        "log_container_name_literals": {
            "count": len(aggregate_containers),
            "values": sorted(aggregate_containers),
            "message_resource_token_row_counts_across_log_files": dict(sorted(log_message_token_total.items())),
        },
        "cases": cases,
        "classifications": classify(),
        "decision_rule": {
            "observable_entity": "Requires a dedicated structured identity and a dataset-supported relationship; neither may be inferred from a lexical label or free-text message.",
            "attribute_only": "A literal raw column or metric-series prefix exists but does not establish a typed, stable runtime resource entity or a USES edge.",
            "requires_external_mapping": "Raw lexical labels suggest a type, but semantic type/identity and any relation require information outside the pinned raw data.",
            "not_supported": "No structured identifier or relation exists in the pinned raw schemas for the requested type.",
        },
        "re2_tt_pilot_implication": {
            "selected_case": "re2tt_ts-auth-service_cpu_1",
            "raw_modalities": sorted(cases["re2tt_ts-auth-service_cpu_1"]["modalities"]),
            "resource_graph": "NOT SUPPORTED from the selected RE2-TT raw data; use neither resource nodes nor USES edges in the first pilot.",
            "allowed": "Service/operation trace representation and metric-series features only under separate explicit rules; this script makes no claim that these form resource topology.",
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "classifications": result["classifications"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
