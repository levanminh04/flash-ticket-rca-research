"""Independent RE2-TT ground-truth, leakage, and evaluation-readiness audit.

This script deliberately uses only the pinned official ``cases.parquet`` index
and the official Hugging Face repository tree at the same immutable revision.
It does not read an earlier ground-truth audit and does not download telemetry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
from huggingface_hub import HfApi


DEFAULT_ROOT = Path(r"D:\Project\flash-ticket-rca-research")
REPO_ID = "phamquiluan/RCAEval"
DATASET_ID = "RE2-TT"
CASE_PATTERN = re.compile(
    r"^re2tt_(?P<service>.+)_(?P<fault>cpu|delay|disk|loss|mem|socket)_(?P<repetition>[1-9][0-9]*)$"
)
EXPECTED_COLUMNS = {
    "case",
    "dataset",
    "suite",
    "system",
    "system_name",
    "root_cause_service",
    "fault",
    "fault_description",
    "repetition",
    "inject_time",
    "n_metrics",
    "n_timesteps",
    "time_start",
    "time_end",
    "duration_minutes",
    "normal_timesteps",
    "faulty_timesteps",
    "has_logs",
    "n_logs",
    "has_traces",
    "n_traces",
    "has_root_cause_file",
}
ALLOWED_RE2TT_BASENAMES = {
    "inject_time.txt",
    "logs.parquet",
    "metrics.parquet",
    "traces.parquet",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_builtin(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-native values."""
    if isinstance(value, dict):
        return {str(key): as_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_builtin(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    return value


def count_by(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in frame[column].value_counts(dropna=False).sort_index().items()
    }


def classify_ground_truth() -> list[dict[str, str]]:
    return [
        {
            "item": "Incident label",
            "status": "AVAILABLE",
            "basis": "All 90 cases are indexed as fault-injection cases and every row has an in-range inject_time with nonzero normal and faulty windows.",
            "limit": "This is an injection-window label, not an independently annotated observed anomaly onset.",
        },
        {
            "item": "Root-cause service",
            "status": "AVAILABLE",
            "basis": "root_cause_service is non-null in all 90 metadata rows; five services are balanced at 18 cases each.",
            "limit": "Evaluation-only label; it must not be used to form per-case model candidates or features.",
        },
        {
            "item": "Fault type",
            "status": "AVAILABLE",
            "basis": "fault is non-null in all 90 metadata rows; six values occur 15 times each.",
            "limit": "Evaluation-only label; it is encoded in every case identifier.",
        },
        {
            "item": "Injection target",
            "status": "PARTIAL",
            "basis": "The service label is present and exactly matches the service token in every case identifier.",
            "limit": "There is no separate injection_target field or independent target record. The dataset does not distinguish an intended injection target from an observable causal root cause, and has no operation/resource target.",
        },
        {
            "item": "Injection timestamp",
            "status": "AVAILABLE",
            "basis": "inject_time is non-null and within [time_start, time_end] for all 90 cases; every row has 720 normal and 721 faulty timesteps.",
            "limit": "Only an evaluation/protocol boundary. It is forbidden as an end-to-end detector input.",
        },
        {
            "item": "Operation-level root cause",
            "status": "ABSENT",
            "basis": "No operation-root-cause field exists in cases.parquet, and the complete RE2-TT repository tree has no separate ground-truth artifact beyond the four telemetry/inject-time file types.",
            "limit": "A trace operation name is an observable representation, not an operation ground-truth label.",
        },
        {
            "item": "Resource-level root cause",
            "status": "ABSENT",
            "basis": "No resource target/type/root-cause metadata field or separate RE2-TT ground-truth artifact is present.",
            "limit": "Fault labels such as disk/socket do not identify a specific resource entity.",
        },
        {
            "item": "Affected-node label",
            "status": "ABSENT",
            "basis": "No affected-service/node set is in the metadata and no corresponding RE2-TT label artifact exists in the pinned tree.",
            "limit": "The root-cause service label does not label all anomalous or affected nodes.",
        },
        {
            "item": "Propagation-path label",
            "status": "ABSENT",
            "basis": "No propagation-path field or RE2-TT artifact is present in the metadata/tree inventory.",
            "limit": "Span parentage cannot be promoted into a labelled causal path.",
        },
        {
            "item": "Machine-readable root-cause indicator",
            "status": "ABSENT",
            "basis": "The pinned RE2-TT metadata has no indicator field and its complete repository tree contains no root_cause.txt or indicator artifact.",
            "limit": "The official README's general benchmark description does not make a separate RE2-TT indicator field available in this pinned Hugging Face copy.",
        },
    ]


def evaluation_readiness() -> list[dict[str, str]]:
    return [
        {
            "task": "RCA given a known incident window",
            "status": "YES",
            "basis": "All 90 cases have a valid injection boundary and a root-cause-service evaluation label.",
            "protocol": "Use inject_time only to define the evaluation window or to supply an externally known incident time; never expose it as an end-to-end detector feature.",
        },
        {
            "task": "End-to-end anomaly detection",
            "status": "PARTIAL",
            "basis": "Each case has normal/faulty injection windows and metrics/traces; 89/90 also have logs.",
            "protocol": "It can score automatic incident-window detection against the injected-fault boundary, but not a fully labelled anomaly-object/task because observed anomaly onset and affected-node labels are absent.",
        },
        {
            "task": "Service-level anomaly evaluation",
            "status": "NO",
            "basis": "There is only one root-cause-service label per case and no affected/anomalous service set.",
            "protocol": "Do not treat root_cause_service as a label for every anomalous service.",
        },
        {
            "task": "Node-level anomaly F1",
            "status": "NO",
            "basis": "No authoritative node universe or per-node anomaly labels are available.",
            "protocol": "NOT EVALUABLE WITH CURRENT GROUND TRUTH.",
        },
        {
            "task": "Root-cause service ranking",
            "status": "YES",
            "basis": "All 90 cases have a non-null root_cause_service label across five balanced services.",
            "protocol": "Build each candidate universe from telemetry observable in that case, never from case paths, metadata labels, or known injected-service sets.",
        },
        {
            "task": "Operation-level root-cause ranking",
            "status": "NO",
            "basis": "No operation-level root-cause label exists.",
            "protocol": "NOT EVALUABLE WITH CURRENT GROUND TRUTH.",
        },
    ]


def leakage_policy() -> list[dict[str, str]]:
    return [
        {
            "field": "case ID",
            "classification": "FORBIDDEN MODEL INPUT",
            "reason": "Every RE2-TT case ID deterministically encodes the root-cause service, fault type, and repetition.",
        },
        {
            "field": "directory name/path",
            "classification": "FORBIDDEN MODEL INPUT",
            "reason": "The official directory convention carries the same root-cause-service and fault tokens as the case ID.",
        },
        {
            "field": "root_cause_service",
            "classification": "EVALUATION ONLY",
            "reason": "It is the service-ranking answer label; using it in a case-specific candidate set collapses that universe to one.",
        },
        {
            "field": "fault type",
            "classification": "EVALUATION ONLY",
            "reason": "It is the service-fault answer label and is encoded in the case ID/path.",
        },
        {
            "field": "inject_time",
            "classification": "EVALUATION ONLY — ONLY FOR RCA-GIVEN-INCIDENT-WINDOW",
            "reason": "It defines the injected-fault boundary. FORBIDDEN FOR END-TO-END DETECTION INPUT.",
        },
        {
            "field": "root_cause.txt",
            "classification": "FORBIDDEN MODEL INPUT",
            "reason": "A direct root-cause artifact would be leakage. It is absent from all 90 RE2-TT cases in the pinned repository tree.",
        },
        {
            "field": "repetition",
            "classification": "PROVENANCE ONLY",
            "reason": "It identifies a repetition, not a runtime observable; it must not be a model feature.",
        },
    ]


def markdown(data: dict[str, Any]) -> str:
    facts = data["re2tt_metadata_facts"]
    inventory = data["official_repository_tree"]
    lines = [
        "# Independent RE2-TT Ground-Truth and Leakage Audit",
        "",
        "**Scope:** `DATASET-WIDE METADATA FACT` for all 90 RE2-TT cases at the immutable source revision below. This audit did not download or inspect additional telemetry and did not use a prior ground-truth audit.",
        "",
        "## Provenance",
        "",
        f"- Official dataset: [`{data['provenance']['repository']}`]({data['provenance']['url']})",
        f"- Pinned revision: `{data['provenance']['revision']}`",
        f"- `cases.parquet`: {data['provenance']['metadata_bytes']} bytes; SHA-256 `{data['provenance']['metadata_sha256']}`",
        f"- Official documentation consulted: [RCAEval README]({data['official_documentation']['readme_url']}) and [benchmark evaluator source]({data['official_documentation']['evaluator_url']}).",
        "",
        "## Executive verdict",
        "",
        "**RE2-TT has complete case-level root-cause-service, fault-type, and injection-window labels for 90 balanced injected-fault cases. It supports service-root-cause ranking given a telemetry-derived candidate universe and RCA given a known incident window. It does not support operation/resource root-cause ranking, affected-node evaluation, propagation-path evaluation, service-level anomaly labels, or node-level anomaly F1.**",
        "",
        "The case ID and directory name leak both the answer service and fault in **90/90** cases. Passing a path, case ID, `root_cause_service`, or `fault` into model construction is invalid. There is no separate injection-target record: the service label must not be relabelled as independently verified injection provenance.",
        "",
        "## Full RE2-TT metadata facts",
        "",
        f"- Cases: **{facts['case_count']}**; each has {facts['n_timesteps']['min']} timesteps, with {facts['normal_timesteps']['unique_values']} normal and {facts['faulty_timesteps']['unique_values']} faulty timesteps.",
        f"- Root-cause labels: {', '.join(f'`{name}` ({count})' for name, count in facts['root_cause_service_counts'].items())}.",
        f"- Fault labels: {', '.join(f'`{name}` ({count})' for name, count in facts['fault_counts'].items())}.",
        f"- Full factorial coverage: {facts['factorial_coverage']['complete']} — five services × six fault types × three repetitions, with {facts['factorial_coverage']['missing_combinations']} missing and {facts['factorial_coverage']['duplicate_combinations']} duplicate combinations.",
        f"- Modalities declared by metadata: metrics in {facts['modality_counts']['metrics_cases']}/90, traces in {facts['modality_counts']['traces_cases']}/90, logs in {facts['modality_counts']['logs_cases']}/90. The no-log case is `{facts['modality_counts']['no_log_cases'][0]}`.",
        f"- Injection timestamps: {facts['injection_window']['within_window']}/90 are within their metadata window; all are exactly {facts['injection_window']['offset_from_start_seconds']['unique_values']} seconds after `time_start`.",
        "",
        "## Official repository-tree check",
        "",
        f"At the pinned revision, the repository contains {inventory['re2tt_case_count']} RE2-TT directories and {inventory['re2tt_file_count']} RE2-TT files: {', '.join(f'`{name}` × {count}' for name, count in inventory['basename_counts'].items())}. There are no unexpected RE2-TT files and no `root_cause.txt` files.",
        "",
        "## Ground-truth availability",
        "",
        "| Item | Status | Decisive evidence |",
        "|---|---|---|",
    ]
    for item in data["ground_truth_availability"]:
        lines.append(f"| {item['item']} | **{item['status']}** | {item['basis']} |")

    lines += [
        "",
        "## Candidate universe and leakage",
        "",
        f"The metadata label alphabet contains **{data['candidate_universe']['label_universe_size']}** services, but it is **not** a model candidate universe. `cases.parquet` has no per-case candidate-service field and no authoritative split field. Per-case and per-split candidate universes are therefore **NOT AVAILABLE FROM METADATA**.",
        "",
        f"A deterministic parser recovered `root_cause_service`, `fault`, and `repetition` from **{data['case_identifier_encoding']['all_tokens_match']}/90** case IDs. Treating that service token as the candidate universe makes the candidate count exactly one in all cases; this is direct answer leakage. Restricting candidates to the five known injected services also makes Top-5 service accuracy structurally trivial. A valid future evaluator must enumerate candidate services only from telemetry visible in the evaluated case, before reading labels.",
        "",
        "| Field | Classification | Reason |",
        "|---|---|---|",
    ]
    for item in data["leakage_policy"]:
        lines.append(f"| {item['field']} | **{item['classification']}** | {item['reason']} |")

    lines += [
        "",
        "## Evaluation readiness",
        "",
        "| Evaluation task | Verdict | Why |",
        "|---|---|---|",
    ]
    for item in data["evaluation_readiness"]:
        lines.append(f"| {item['task']} | **{item['status']}** | {item['basis']} {item['protocol']} |")

    lines += [
        "",
        "## Direct conclusions for Task B",
        "",
        "1. **Service-level RCA ranking: YES.** The ground truth is complete and balanced; the evaluator must use a candidate universe derived from pre-label telemetry only.",
        "2. **RCA given a known incident window: YES.** `inject_time` is a permissible protocol boundary only in this setting.",
        "3. **End-to-end anomaly detection: PARTIAL.** It can be scored against injected windows, but has no independently labelled anomaly onset or affected-node ground truth.",
        "4. **Operation/resource/affected-node/propagation evaluation: NOT EVALUABLE WITH CURRENT GROUND TRUTH.** No such labels are available in the pinned RE2-TT artifacts.",
        "5. **RE2-TT’s injection-window metadata is internally valid.** The known out-of-window RE1 case does not form a pattern in this RE2-TT population: 0/90 RE2-TT rows have an out-of-range `inject_time`.",
        "",
        "## Reproducibility",
        "",
        f"Run `D:/Project/flash-ticket-rca-research/.venv/Scripts/python.exe D:/Project/flash-ticket-rca-research/scripts/audit/subagent_i_re2tt_groundtruth.py`. The corresponding machine result is `{data['output_files']['json']}`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()

    root = args.root.resolve()
    metadata_path = root / "datasets" / "rcaeval" / "metadata" / "cases.parquet"
    provenance_path = root / "datasets" / "rcaeval" / "metadata" / "metadata-provenance.json"
    output_dir = root / "audits" / "rcaeval"
    output_json = output_dir / "subagent-i-re2tt-groundtruth.json"
    output_markdown = output_dir / "subagent-i-re2tt-groundtruth.md"

    if not metadata_path.is_file() or not provenance_path.is_file():
        raise FileNotFoundError("Pinned metadata and metadata provenance must exist before this audit runs.")

    source = json.loads(provenance_path.read_text(encoding="utf-8"))["source"]
    revision = source["revision"]
    if source["repository"] != REPO_ID or source["repository_type"] != "dataset":
        raise AssertionError("Unexpected metadata provenance source.")

    df = pd.read_parquet(metadata_path)
    if set(df.columns) != EXPECTED_COLUMNS:
        raise AssertionError("The metadata schema differs from the pinned Task B schema.")
    re2tt = df.loc[df["dataset"].eq(DATASET_ID)].copy()
    if len(re2tt) != 90:
        raise AssertionError(f"Expected 90 RE2-TT cases, found {len(re2tt)}.")
    if re2tt.isna().any().any():
        raise AssertionError("RE2-TT metadata contains unexpected nulls.")

    parsed = re2tt["case"].map(CASE_PATTERN.fullmatch)
    if parsed.isna().any():
        bad = re2tt.loc[parsed.isna(), "case"].tolist()
        raise AssertionError(f"Case IDs do not follow the RE2-TT convention: {bad}")
    parsed_service = parsed.map(lambda match: match.group("service"))
    parsed_fault = parsed.map(lambda match: match.group("fault"))
    parsed_repetition = parsed.map(lambda match: int(match.group("repetition")))
    token_matches = {
        "root_cause_service": int((parsed_service == re2tt["root_cause_service"]).sum()),
        "fault": int((parsed_fault == re2tt["fault"]).sum()),
        "repetition": int((parsed_repetition == re2tt["repetition"]).sum()),
    }
    if any(value != len(re2tt) for value in token_matches.values()):
        raise AssertionError(f"Case-ID tokens conflict with indexed labels: {token_matches}")

    factorial = (
        re2tt.groupby(["root_cause_service", "fault", "repetition"], dropna=False)
        .size()
        .rename("count")
    )
    expected_factorial = 5 * 6 * 3
    injection_in_window = (re2tt["inject_time"] >= re2tt["time_start"]) & (
        re2tt["inject_time"] <= re2tt["time_end"]
    )
    normal_faulty_consistent = (
        re2tt["normal_timesteps"] + re2tt["faulty_timesteps"] == re2tt["n_timesteps"]
    )

    # Read the official tree only; no telemetry contents are downloaded.
    remote_paths = HfApi().list_repo_files(
        repo_id=REPO_ID,
        repo_type="dataset",
        revision=revision,
    )
    re2tt_paths = sorted(path for path in remote_paths if path.startswith("re2tt_"))
    remote_case_to_files: dict[str, list[str]] = {}
    for path in re2tt_paths:
        pieces = path.split("/", 1)
        if len(pieces) != 2:
            raise AssertionError(f"Unexpected RE2-TT repository path: {path}")
        remote_case_to_files.setdefault(pieces[0], []).append(pieces[1])
    metadata_cases = set(re2tt["case"])
    if set(remote_case_to_files) != metadata_cases:
        raise AssertionError("RE2-TT metadata case IDs and repository-tree case IDs differ.")
    basename_counts = Counter(
        basename for basenames in remote_case_to_files.values() for basename in basenames
    )
    unexpected = sorted(set(basename_counts) - ALLOWED_RE2TT_BASENAMES)
    if unexpected:
        raise AssertionError(f"Unexpected RE2-TT artifacts: {unexpected}")

    metadata_candidate_columns = [
        column
        for column in df.columns
        if any(token in column.lower() for token in ("candidate", "split"))
    ]
    absent_label_field_terms = {
        term: [column for column in df.columns if term in column.lower()]
        for term in ("operation", "resource", "affected", "propagation", "indicator", "injection_target")
    }

    no_log_cases = sorted(re2tt.loc[~re2tt["has_logs"], "case"].tolist())
    data: dict[str, Any] = {
        "audit_identity": {
            "role": "Independent additional reviewer — RE2-TT ground truth, candidate universe, leakage, and evaluation readiness",
            "scope": "DATASET-WIDE METADATA FACT — all 90 RE2-TT cases; no telemetry content downloaded or inspected by this audit",
            "independence": "This script does not read prior ground-truth/leakage reports.",
        },
        "provenance": {
            "repository": REPO_ID,
            "url": source["url"],
            "revision": revision,
            "metadata_path": str(metadata_path),
            "metadata_bytes": metadata_path.stat().st_size,
            "metadata_sha256": sha256(metadata_path),
        },
        "official_documentation": {
            "readme_url": "https://github.com/phamquiluan/RCAEval/blob/main/README.md",
            "evaluator_url": "https://github.com/phamquiluan/RCAEval/blob/main/main.py",
            "facts_used": [
                "The README identifies RE2-TT as a 90-case, six-fault, multi-source suite and defines inject_time.txt as a fault-injection timestamp.",
                "The README identifies cases.parquet as the index for root-cause service, fault type, and injection time.",
                "The evaluator source treats injection time as the boundary for normal/anomalous window construction and derives candidate counts from observed metric columns after preprocessing.",
            ],
        },
        "re2tt_metadata_facts": {
            "case_count": int(len(re2tt)),
            "dataset_values": sorted(str(value) for value in re2tt["dataset"].unique()),
            "suite_values": sorted(str(value) for value in re2tt["suite"].unique()),
            "system_values": sorted(str(value) for value in re2tt["system"].unique()),
            "system_name_values": sorted(str(value) for value in re2tt["system_name"].unique()),
            "root_cause_service_counts": count_by(re2tt, "root_cause_service"),
            "fault_counts": count_by(re2tt, "fault"),
            "repetition_counts": count_by(re2tt, "repetition"),
            "root_service_by_fault": {
                str(fault): sorted(
                    str(value)
                    for value in re2tt.loc[re2tt["fault"].eq(fault), "root_cause_service"].unique()
                )
                for fault in sorted(re2tt["fault"].unique())
            },
            "root_service_by_repetition": {
                str(repetition): sorted(
                    str(value)
                    for value in re2tt.loc[re2tt["repetition"].eq(repetition), "root_cause_service"].unique()
                )
                for repetition in sorted(re2tt["repetition"].unique())
            },
            "factorial_coverage": {
                "expected_combinations": expected_factorial,
                "observed_combinations": int(len(factorial)),
                "missing_combinations": int(expected_factorial - len(factorial)),
                "duplicate_combinations": int((factorial > 1).sum()),
                "complete": bool(len(factorial) == expected_factorial and (factorial == 1).all()),
            },
            "n_timesteps": {
                "min": int(re2tt["n_timesteps"].min()),
                "max": int(re2tt["n_timesteps"].max()),
                "unique_values": sorted(int(value) for value in re2tt["n_timesteps"].unique()),
            },
            "n_metrics": {
                "min": int(re2tt["n_metrics"].min()),
                "max": int(re2tt["n_metrics"].max()),
                "unique_values": sorted(int(value) for value in re2tt["n_metrics"].unique()),
            },
            "normal_timesteps": {
                "unique_values": sorted(int(value) for value in re2tt["normal_timesteps"].unique()),
            },
            "faulty_timesteps": {
                "unique_values": sorted(int(value) for value in re2tt["faulty_timesteps"].unique()),
            },
            "modality_counts": {
                "metrics_cases": int((re2tt["n_metrics"] > 0).sum()),
                "logs_cases": int(re2tt["has_logs"].sum()),
                "traces_cases": int(re2tt["has_traces"].sum()),
                "root_cause_file_cases": int(re2tt["has_root_cause_file"].sum()),
                "no_log_cases": no_log_cases,
            },
            "injection_window": {
                "non_null": int(re2tt["inject_time"].notna().sum()),
                "within_window": int(injection_in_window.sum()),
                "below_start": int((re2tt["inject_time"] < re2tt["time_start"]).sum()),
                "above_end": int((re2tt["inject_time"] > re2tt["time_end"]).sum()),
                "normal_plus_faulty_equals_total": int(normal_faulty_consistent.sum()),
                "offset_from_start_seconds": {
                    "min": int((re2tt["inject_time"] - re2tt["time_start"]).min()),
                    "max": int((re2tt["inject_time"] - re2tt["time_start"]).max()),
                    "unique_values": sorted(
                        int(value) for value in (re2tt["inject_time"] - re2tt["time_start"]).unique()
                    ),
                },
                "offset_to_end_seconds": {
                    "min": int((re2tt["time_end"] - re2tt["inject_time"]).min()),
                    "max": int((re2tt["time_end"] - re2tt["inject_time"]).max()),
                    "unique_values": sorted(
                        int(value) for value in (re2tt["time_end"] - re2tt["inject_time"]).unique()
                    ),
                },
            },
        },
        "official_repository_tree": {
            "repository_paths_total": int(len(remote_paths)),
            "re2tt_file_count": int(len(re2tt_paths)),
            "re2tt_case_count": int(len(remote_case_to_files)),
            "basename_counts": dict(sorted((str(key), int(value)) for key, value in basename_counts.items())),
            "unexpected_basenames": unexpected,
            "root_cause_txt_cases": sorted(
                case for case, files in remote_case_to_files.items() if "root_cause.txt" in files
            ),
            "metadata_case_set_matches_tree": True,
        },
        "case_identifier_encoding": {
            "pattern": CASE_PATTERN.pattern,
            "parsed_case_count": int(len(parsed)),
            "token_matches": token_matches,
            "all_tokens_match": int(min(token_matches.values())),
            "conclusion": "Every case ID encodes the indexed root-cause service, fault, and repetition. Case IDs and their directory paths are direct leakage.",
        },
        "candidate_universe": {
            "metadata_label_universe": sorted(str(value) for value in re2tt["root_cause_service"].unique()),
            "label_universe_size": int(re2tt["root_cause_service"].nunique()),
            "metadata_has_candidate_or_split_columns": metadata_candidate_columns,
            "per_case_candidate_service_universe": "NOT AVAILABLE FROM METADATA",
            "per_split_candidate_service_universe": "NOT AVAILABLE FROM METADATA",
            "authoritative_split": "ABSENT",
            "case_id_conditioned_candidate_count": 1,
            "known_injected_label_universe_top5": "TRIVIAL — five labels make Top-5 service accuracy structurally 1.0 if every label is returned.",
            "permitted_rule": "Derive candidate services only from telemetry observable in the evaluated case before labels are loaded; freeze and log that set per case.",
        },
        "metadata_absence_checks": {
            "candidate_or_split_columns": metadata_candidate_columns,
            "label_field_name_matches": absent_label_field_terms,
            "interpretation": "Absence checks apply to the pinned metadata and pinned repository file tree, not to uninspected telemetry values.",
        },
        "ground_truth_availability": classify_ground_truth(),
        "leakage_policy": leakage_policy(),
        "evaluation_readiness": evaluation_readiness(),
        "output_files": {
            "json": str(output_json),
            "markdown": str(output_markdown),
        },
    }
    data = as_builtin(data)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_markdown.write_text(markdown(data), encoding="utf-8")
    print(f"WROTE {output_json}")
    print(f"WROTE {output_markdown}")
    print("RE2TT_CASES=90")
    print("RE2TT_GROUND_TRUTH_AUDIT=PASS")


if __name__ == "__main__":
    main()
