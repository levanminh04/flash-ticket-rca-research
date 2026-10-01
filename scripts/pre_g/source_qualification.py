"""PRE-G metadata-only source qualification for the frozen RE2-TT release.

Case identifiers and remote paths exist only inside this trusted controller.
The public receipt contains counts and digests, never a final case roster,
answer, injection time, telemetry row, or model prediction. Importing this
module does not contact the network or read any dataset file.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping


REPO_ID = "phamquiluan/RCAEval"
OFFICIAL_ENDPOINT = "https://huggingface.co"
REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
METADATA_SHA256 = "c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb"
FROZEN_V2_SHA256 = "c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d"
TD_SHA256 = "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971"
METADATA_RELATIVE = Path("datasets/rcaeval/metadata/cases.parquet")
MANIFEST_RELATIVE = Path("configs/task-f-td13-frozen-release-v2.json")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_CASE_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_MODALITIES = ("metrics", "traces", "logs")


class SourceQualificationError(ValueError):
    """A PRE-G source, split, adapter, or provenance contract is invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _field(value: object, name: str) -> object:
    return value.get(name) if isinstance(value, Mapping) else getattr(value, name, None)


def _valid_digest(value: object) -> str:
    if not isinstance(value, str) or _HEX64.fullmatch(value) is None:
        raise SourceQualificationError("Invalid official SHA256 identity")
    return value


def _case_component(value: object) -> str:
    if (
        not isinstance(value, str)
        or _CASE_COMPONENT.fullmatch(value) is None
        or value in {".", ".."}
        or ".." in value
    ):
        raise SourceQualificationError("Invalid opaque case component")
    return value


def _read_frozen_contract(workspace: Path, project: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify the complete v2 release and its development-qualified converter."""
    manifest_path = workspace / MANIFEST_RELATIVE
    if not manifest_path.is_file() or _sha256(manifest_path) != FROZEN_V2_SHA256:
        raise SourceQualificationError("Frozen v2 release manifest drift")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest["dataset"]["revision"] != REVISION
            or manifest["td"]["sha256"] != TD_SHA256
            or manifest["implementation"]["release_id"] != "TASK-F-TD13-v2"
        ):
            raise SourceQualificationError("Frozen dataset, method, or release identity drift")
        registry_ref = manifest["dataset"]["development_registry_ref"]
        registry_path = (workspace / registry_ref["path"]).resolve()
        registry_path.relative_to(workspace)
        if _sha256(registry_path) != registry_ref["sha256"]:
            raise SourceQualificationError("Frozen development split registry drift")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (KeyError, TypeError, OSError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, SourceQualificationError):
            raise
        raise SourceQualificationError("Unreadable frozen split contract") from exc

    # Task F's verifier checks every referenced source byte and selected canary.
    from rca.adapters import QualifiedTelemetryAdapter
    from rca.release import verify_frozen_release

    if (
        Path(inspect.getsourcefile(QualifiedTelemetryAdapter) or "").resolve()
        != (workspace / "src/rca/adapters.py").resolve()
        or Path(inspect.getsourcefile(verify_frozen_release) or "").resolve()
        != (workspace / "src/rca/release.py").resolve()
    ):
        raise SourceQualificationError("Imported Task F verifier/adapter is not from the frozen workspace")
    try:
        verification = verify_frozen_release(
            manifest_path, workspace_root=workspace, project_root=project
        )
        adapter = QualifiedTelemetryAdapter.from_manifest(
            manifest_path, workspace_root=workspace
        )
    except Exception as exc:
        raise SourceQualificationError("Frozen v2 adapter/source qualification failed") from exc
    if verification.get("status") != "PASS" or adapter.scope != "DEVELOPMENT_QUALIFIED__PRE_G_REQUALIFICATION_REQUIRED":
        raise SourceQualificationError("Frozen adapter qualification scope drift")
    return manifest, registry


def _plan_final_metadata(rows: list[Mapping[str, object]], registry: Mapping[str, object]) -> dict[str, Any]:
    """Use opaque IDs only; group repeated cases without decoding root/fault."""
    selected = [row for row in rows if row.get("dataset") == "RE2-TT"]
    if len(selected) != 90:
        raise SourceQualificationError("Pinned RE2-TT metadata is not 90 cases")
    by_id: dict[str, Mapping[str, object]] = {}
    cells: dict[str, set[int]] = defaultdict(set)
    for row in selected:
        case = _case_component(row.get("case"))
        if case in by_id or row.get("has_traces") is not True or type(row.get("has_logs")) is not bool:
            raise SourceQualificationError("Duplicate case or invalid modality declaration")
        repetition = row.get("repetition")
        if type(repetition) is not int or repetition not in (1, 2, 3):
            raise SourceQualificationError("Invalid case repetition")
        cell, separator, suffix = case.rpartition("_")
        if not separator or not cell or suffix != str(repetition):
            raise SourceQualificationError("Opaque case/repetition mismatch")
        cells[cell].add(repetition)
        by_id[case] = row
    if len(cells) != 30 or any(repetitions != {1, 2, 3} for repetitions in cells.values()):
        raise SourceQualificationError("RE2-TT three-repeat cell contract drift")

    development = registry.get("development_ids")
    if not isinstance(development, list) or len(development) != 30:
        raise SourceQualificationError("Frozen development roster is not 30 cases")
    development_ids = {_case_component(case) for case in development}
    if len(development_ids) != 30 or not development_ids.issubset(by_id):
        raise SourceQualificationError("Frozen development roster does not match metadata")
    cell_scope: dict[str, set[str]] = defaultdict(set)
    for case in by_id:
        cell_scope[case.rpartition("_")[0]].add(
            "development" if case in development_ids else "final"
        )
    if any(len(scopes) != 1 for scopes in cell_scope.values()):
        raise SourceQualificationError("A three-repeat cell crosses the frozen split")
    final_ids = tuple(sorted(set(by_id) - development_ids))
    if len(final_ids) != 60 or Counter(next(iter(scope)) for scope in cell_scope.values()) != {
        "development": 10, "final": 20
    }:
        raise SourceQualificationError("Frozen 30/60 cell split drift")
    if sum(row["has_logs"] is False for row in selected) != 1:
        raise SourceQualificationError("Pinned RE2-TT log availability drift")
    paths = tuple(
        sorted(
            f"{case}/{modality}.parquet"
            for case in final_ids
            for modality in (("metrics", "traces", "logs") if by_id[case]["has_logs"] else ("metrics", "traces"))
        )
    )
    if len(paths) != 180:
        raise SourceQualificationError("Final telemetry object count drift")
    return {"final_ids": final_ids, "remote_paths": paths}


def _official_inventory(api: object, planned_paths: tuple[str, ...]) -> dict[str, Any]:
    """Get official object descriptors only; never download or open Parquet rows."""
    info = api.dataset_info(REPO_ID, revision=REVISION)
    if _field(info, "sha") != REVISION:
        raise SourceQualificationError("Official dataset revision differs from the pinned revision")
    objects = api.get_paths_info(
        REPO_ID, paths=list(planned_paths), repo_type="dataset", revision=REVISION
    )
    expected = set(planned_paths)
    verified: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in objects:
        relative = _field(item, "path")
        if not isinstance(relative, str) or relative not in expected or relative in seen:
            raise SourceQualificationError("Unexpected, non-telemetry, or duplicate source object")
        seen.add(relative)
        size = _field(item, "size")
        lfs_sha = _field(_field(item, "lfs"), "sha256")
        if type(size) is not int or size <= 0:
            raise SourceQualificationError("Missing or invalid official object size")
        verified.append({"path": relative, "bytes": size, "sha256": _valid_digest(lfs_sha)})
    if seen != expected:
        raise SourceQualificationError("Official source inventory is incomplete")
    verified.sort(key=lambda row: str(row["path"]))
    return {
        "objects": len(verified),
        "identity_sha256": hashlib.sha256(_canonical(verified)).hexdigest(),
        "total_official_bytes": sum(int(row["bytes"]) for row in verified),
    }


def qualify_final_source_metadata(
    *, workspace_root: str | Path, project_root: str | Path, api: object | None = None
) -> dict[str, object]:
    """Qualify final-scope metadata and official LFS descriptors, not raw cases.

    A PASS_METADATA_ONLY result does not certify local raw bytes, Parquet rows,
    schemas, feature availability, predictions, or final efficacy. The caller
    must not pass this public receipt to a numeric worker as an input manifest.
    """
    workspace, project = Path(workspace_root).resolve(), Path(project_root).resolve()
    manifest, registry = _read_frozen_contract(workspace, project)
    metadata_path = workspace / METADATA_RELATIVE
    if not metadata_path.is_file() or _sha256(metadata_path) != METADATA_SHA256:
        raise SourceQualificationError("Pinned cases metadata bytes are absent or different")
    # Projection matters: this file also holds fault/root and injection fields.
    import pyarrow.parquet as pq

    rows = pq.read_table(
        metadata_path,
        columns=["case", "dataset", "repetition", "has_logs", "has_traces"],
    ).to_pylist()
    plan = _plan_final_metadata(rows, registry)
    injected_api = api is not None
    if api is None:
        from huggingface_hub import HfApi

        # A default HfApi endpoint can inherit HF_ENDPOINT, including a mirror
        # or a local test server. Such a response is not official evidence.
        api = HfApi(endpoint=OFFICIAL_ENDPOINT, token=False)
        if api.endpoint != OFFICIAL_ENDPOINT:
            raise SourceQualificationError("Official metadata API origin is not pinned")
    inventory = _official_inventory(api, plan["remote_paths"])
    return {
        "schema": "PRE-G-FINAL-SOURCE-METADATA-v1",
        "status": "SYNTHETIC_TEST_ONLY" if injected_api else "PASS_METADATA_ONLY",
        "api_provenance": "INJECTED_TEST_API" if injected_api else "OFFICIAL_HF_API",
        "api_endpoint": None if injected_api else OFFICIAL_ENDPOINT,
        "source": {"repo_id": REPO_ID, "revision": REVISION},
        "metadata_sha256": METADATA_SHA256,
        "split": {
            "development_cases": 30,
            "final_cases": 60,
            "final_cells": 20,
            "final_case_ids_or_paths_disclosed": False,
            "final_case_ids_sha256": hashlib.sha256(
                ("\n".join(plan["final_ids"]) + "\n").encode("utf-8")
            ).hexdigest(),
        },
        "official_inventory": inventory,
        "frozen_conversion": {
            "manifest_sha256": FROZEN_V2_SHA256,
            "release_id": manifest["implementation"]["release_id"],
            "adapter_id": manifest["implementation"]["qualified_development_loader"]["adapter_id"],
            "adapter_evidence_scope": "DEVELOPMENT_ONLY",
            "final_source_relationship": "METADATA_IDENTITY_ONLY__RAW_COMPATIBILITY_UNVERIFIED",
        },
        "this_invocation": {
            "metadata_columns_read": ["case", "dataset", "repetition", "has_logs", "has_traces"],
            "download_api_invoked": False,
            "raw_parquet_opened": False,
            "explicit_root_fault_tau_columns_requested": False,
            "case_identifiers_kept_controller_only": True,
            "prediction_code_invoked": False,
        },
        "limitations": [
            "Object descriptors identify planned objects only; local final bytes and schemas were not checked.",
            "Task F conversion is qualified on development only; final raw compatibility remains a Task G entry check.",
            "Opaque case identifiers can encode scenario information and remain controller-only.",
        ] + (["Injected API inventory is a test fixture, not official source evidence."] if injected_api else []),
    }


def verify_local_telemetry_audit(
    *, source_root: str | Path, case_id: str,
    expected_objects: Mapping[str, Mapping[str, object]],
    raw_telemetry: Mapping[str, object],
) -> dict[str, str]:
    """Rehash a synthetic raw-source audit before admission.

    This PRE-G helper fails closed on non-synthetic case IDs, so it cannot be
    used as a final60 raw-ingestion entry point. It intentionally does not
    parse Parquet or certify row semantics.
    """
    case = _case_component(case_id)
    if not case.startswith("synthetic-"):
        raise SourceQualificationError("PRE-G local audit is synthetic-only")
    root = Path(source_root).resolve()
    try:
        audit = raw_telemetry["audit"]
        modalities = audit["modalities"]
    except (KeyError, TypeError) as exc:
        raise SourceQualificationError("Missing trusted raw-source audit") from exc
    if not isinstance(modalities, Mapping) or not isinstance(expected_objects, Mapping):
        raise SourceQualificationError("Malformed raw-source audit")
    allowed_paths = {f"{case}/{modality}.parquet" for modality in _MODALITIES}
    if not set(expected_objects).issubset(allowed_paths):
        raise SourceQualificationError("Expected objects include a non-telemetry path")
    if f"{case}/metrics.parquet" not in expected_objects or f"{case}/traces.parquet" not in expected_objects:
        raise SourceQualificationError("Metrics and traces are required source objects")
    result: dict[str, str] = {}
    for modality in _MODALITIES:
        relative = f"{case}/{modality}.parquet"
        row = modalities.get(modality)
        if not isinstance(row, Mapping):
            raise SourceQualificationError("Missing modality audit")
        if relative not in expected_objects:
            if modality != "logs" or row.get("status") != "MISSING":
                raise SourceQualificationError("Unplanned or falsely missing modality")
            result[modality] = "MISSING"
            continue
        identity = expected_objects[relative]
        expected_size, expected_sha = identity.get("bytes"), identity.get("sha256")
        if type(expected_size) is not int or expected_size <= 0:
            raise SourceQualificationError("Invalid expected source size")
        expected_sha = _valid_digest(expected_sha)
        unresolved = root / case / f"{modality}.parquet"
        resolved = unresolved.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise SourceQualificationError("Source path escaped its trusted root") from exc
        if resolved != unresolved or not resolved.is_file():
            raise SourceQualificationError("Source path is aliased or absent")
        actual_size, actual_sha = resolved.stat().st_size, _sha256(resolved)
        if actual_size != expected_size or actual_sha != expected_sha:
            raise SourceQualificationError("Local bytes differ from official source identity")
        if (
            row.get("status") != "LOADED"
            or row.get("source_identity_verified") is not True
            or row.get("sha256") != actual_sha
            or row.get("bytes") != actual_size
            or Path(str(row.get("path", ""))).resolve() != resolved
        ):
            raise SourceQualificationError("Caller raw audit is not independently verified")
        result[modality] = actual_sha
    return result


__all__ = [
    "SourceQualificationError",
    "qualify_final_source_metadata",
    "verify_local_telemetry_audit",
]
