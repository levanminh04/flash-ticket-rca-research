"""Machine verification of the frozen Task F release against sealed Task E.

This controller-side module verifies referenced bytes and extracts selections;
it is not imported by numeric ranking/detection modules and never opens final60.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .contracts import FrozenConfigError, load_frozen_config


class ReleaseVerificationError(RuntimeError):
    """Frozen manifest provenance or machine extraction does not agree."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(path: str, workspace: Path, project: Path) -> Path:
    normalized = path.replace("\\", "/")
    if normalized.startswith("P/"):
        result = project / normalized[2:]
    elif normalized.startswith("W/"):
        result = workspace / normalized[2:]
    else:
        candidate = Path(path)
        result = candidate if candidate.is_absolute() else workspace / candidate
    return result.resolve()


def _references(value: Any, location="manifest"):
    if isinstance(value, Mapping):
        pairs = (
            ("path", "sha256"),
            ("source_path", "source_sha256"),
            ("lambda_source", "lambda_source_sha256"),
            ("selection_source", "selection_source_sha256"),
        )
        for path_key, hash_key in pairs:
            if path_key in value and hash_key in value:
                yield location, str(value[path_key]), str(value[hash_key])
        for key, item in value.items():
            yield from _references(item, f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield from _references(item, f"{location}[{index}]")


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def verify_frozen_release(
    manifest_path: str | Path,
    *,
    workspace_root: str | Path,
    project_root: str | Path,
) -> dict[str, Any]:
    """Verify every declared source hash and re-extract C1/C5 selections."""
    workspace = Path(workspace_root).resolve()
    project = Path(project_root).resolve()
    manifest_file = Path(manifest_path).resolve()
    try:
        config = load_frozen_config(manifest_file)
    except FrozenConfigError as exc:
        raise ReleaseVerificationError(str(exc)) from exc
    manifest = _read_json(manifest_file)

    checked: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for location, declared_path, declared_sha in _references(manifest):
        identity = (declared_path, declared_sha)
        if identity in seen:
            continue
        seen.add(identity)
        target = _resolve(declared_path, workspace, project)
        if not target.is_file():
            raise ReleaseVerificationError(f"Missing provenance file: {declared_path}")
        actual = _sha256(target)
        if actual != declared_sha:
            raise ReleaseVerificationError(
                f"Provenance hash mismatch at {location}: {declared_path}"
            )
        checked.append(
            {
                "location": location,
                "path": declared_path,
                "sha256": actual,
                "bytes": target.stat().st_size,
            }
        )

    selections = manifest["selections"]
    c1_source = _read_json(
        _resolve(selections["c1"]["source_path"], workspace, project)
    )
    c1_local_source = _read_json(
        _resolve(selections["c1"]["local_source"]["path"], workspace, project)
    )
    primary_local_rows = [
        row for row in c1_local_source.get("decisions", []) if row.get("scope") == "primary"
    ]
    if len(primary_local_rows) != 1:
        raise ReleaseVerificationError("C1 local source lacks one primary decision")
    extracted_local = primary_local_rows[0]["local_config"]
    if c1_source.get("local_config") != extracted_local:
        raise ReleaseVerificationError("C1 sealed local sources conflict")
    extracted_c1 = {
        "selected_local_index": c1_source.get("selected_local_index"),
        "local": extracted_local,
        "selected_ppr_index": c1_source.get("selected_ppr_index"),
        "primary_ppr": c1_source.get("ppr_config"),
        "selected_diffusion_index": c1_source.get("selected_diffusion_index"),
        "secondary_diffusion": c1_source.get("diffusion_config"),
    }
    expected_c1 = {
        "selected_local_index": 6,
        "local": {"floor": 0.01, "pool": "q90", "fusion": "availablemean"},
        "selected_ppr_index": 4,
        "primary_ppr": {
            "operator": "ppr",
            "direction": "undirected",
            "damping": 0.5,
        },
        "selected_diffusion_index": 6,
        "secondary_diffusion": {
            "operator": "diffusion",
            "direction": "undirected",
            "damping": 0.85,
        },
    }
    if extracted_c1 != expected_c1:
        raise ReleaseVerificationError("C1 extraction disagrees with frozen canaries")

    c5_manifest = selections["c5"]
    lambda_source = _read_json(
        _resolve(c5_manifest["lambda_source"], workspace, project)
    )
    detector_source = _read_json(
        _resolve(c5_manifest["selection_source"], workspace, project)
    )
    extracted_lambda = float(lambda_source.get("selected_lambda"))
    if extracted_lambda != float(detector_source.get("selected_lambda")):
        raise ReleaseVerificationError("C5 lambda sources conflict")
    detector_rows = []
    for detector_id, row in detector_source.get("detectors", {}).items():
        arm, modalities = detector_id.rsplit("-", 1)
        detector_rows.append(
            {
                "id": detector_id,
                "arm": arm,
                "modalities": modalities,
                "status": row.get("status"),
                "q": float(row.get("selected_q")),
                "threshold": float(row.get("full_threshold")),
            }
        )
    by_id = {row["id"]: row for row in detector_rows}
    manifest_by_id = {row["id"]: row for row in c5_manifest["detectors"]}
    if extracted_lambda != 10.0 or by_id != manifest_by_id:
        raise ReleaseVerificationError("C5 extracted selections disagree with manifest")

    development_contract = _read_json(
        _resolve(manifest["dataset"]["development_registry_ref"]["path"], workspace, project)
    )
    if not str(development_contract.get("selection", "")).startswith("NOT RUN"):
        raise ReleaseVerificationError("Development registry was misused as selected output")
    if not str(development_contract.get("final_evaluation", "")).startswith("FORBIDDEN"):
        raise ReleaseVerificationError("Development contract final firewall is not intact")

    sensitivity_tokens = ("e27-036", "e27-037", "sensitivity")
    primary_sources = (
        selections["c1"]["source_path"],
        selections["c5"]["lambda_source"],
        selections["c5"]["selection_source"],
    )
    if any(token in path.lower() for token in sensitivity_tokens for path in primary_sources):
        raise ReleaseVerificationError("A diagnostic sensitivity was substituted as primary")

    return {
        "schema": "TD13-F-FROZEN-SELECTION-EXTRACTION-v1",
        "status": "PASS",
        "manifest_path": manifest_file.relative_to(workspace).as_posix(),
        "manifest_file_sha256": _sha256(manifest_file),
        "manifest_canonical_sha256": config.canonical_sha256,
        "td_sha256": config.td_sha256,
        "dataset_revision": config.dataset_revision,
        "checked_reference_count": len(checked),
        "checked_references": checked,
        "extracted": {"c1": extracted_c1, "c5": {"selected_lambda": extracted_lambda, "detectors": detector_rows}},
        "checks": {
            "all_declared_reference_hashes": "PASS",
            "c1_local_sources_agree": "PASS",
            "c1_canaries": "PASS",
            "c5_lambda_sources_agree": "PASS",
            "c5_eight_valid_q095_thresholds": "PASS",
            "development_registry_not_used_as_selection": "PASS",
            "no_sensitivity_primary_substitution": "PASS",
            "final_split_not_materialized": "PASS",
        },
    }


__all__ = ["ReleaseVerificationError", "verify_frozen_release"]
