"""Qualified controller-side telemetry adapters for the frozen Task F core.

The numeric bundle builders are the exact Task E execution bytes.  This module
binds the imported callables to their recorded source files and qualification
receipts before any public telemetry is admitted.  Dataset file discovery and
ground truth remain outside this package.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


class AdapterQualificationError(RuntimeError):
    """A loader callable, source byte identity, or receipt is not qualified."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterQualificationError(f"Unreadable qualification JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise AdapterQualificationError("Qualification receipt must be a JSON object")
    return value


def _digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise AdapterQualificationError(f"Invalid SHA256 for {label}")
    return value


@dataclass(frozen=True)
class QualifiedTelemetryAdapter:
    """Exact Task E bundle functions plus immutable byte/receipt identity."""

    workspace_root: Path
    adapter_id: str
    scope: str
    source_files: Mapping[str, str]
    receipt_files: Mapping[str, str]

    def __post_init__(self) -> None:
        workspace = Path(self.workspace_root).resolve()
        if not workspace.is_dir() or not isinstance(self.adapter_id, str) or not self.adapter_id:
            raise AdapterQualificationError("Qualified adapter needs a workspace and ID")
        if self.scope != "DEVELOPMENT_QUALIFIED__PRE_G_REQUALIFICATION_REQUIRED":
            raise AdapterQualificationError("Unexpected Task F adapter qualification scope")
        sources = {str(path): _digest(digest, path) for path, digest in self.source_files.items()}
        receipts = {str(path): _digest(digest, path) for path, digest in self.receipt_files.items()}
        required = {
            "scripts/task_e/loader.py",
            "scripts/task_e/replay.py",
            "scripts/task_e/input_adapters.py",
        }
        if set(sources) != required or not receipts:
            raise AdapterQualificationError("Incomplete loader/replay/integrated source identity")
        for relative, digest in {**sources, **receipts}.items():
            path = (workspace / relative).resolve()
            try:
                path.relative_to(workspace)
            except ValueError as exc:
                raise AdapterQualificationError("Adapter identity escaped the workspace") from exc
            if not path.is_file() or _sha256(path) != digest:
                raise AdapterQualificationError(f"Qualified adapter source/receipt drift: {relative}")

        smoke_receipts = [
            _read_json(workspace / relative)
            for relative in receipts
            if relative.endswith("public-loader-smoke.json")
        ]
        if len(smoke_receipts) != 1 or smoke_receipts[0].get("status") != "PASS":
            raise AdapterQualificationError("C1/C5 public-loader qualification receipt is not PASS")
        execution_receipts = [
            _read_json(workspace / relative)
            for relative in receipts
            if relative.endswith("execution.json")
        ]
        if len(execution_receipts) != 1 or execution_receipts[0].get("exit_code") != 0:
            raise AdapterQualificationError("Integrated development qualification did not exit cleanly")

        from scripts.task_e.input_adapters import integrated_bundle
        from scripts.task_e.loader import c1_bundle, c5_bundle
        from scripts.task_e.replay import trace_replay

        callable_sources = {
            c1_bundle: "scripts/task_e/loader.py",
            c5_bundle: "scripts/task_e/loader.py",
            trace_replay: "scripts/task_e/replay.py",
            integrated_bundle: "scripts/task_e/input_adapters.py",
        }
        for function, relative in callable_sources.items():
            actual = Path(inspect.getsourcefile(function) or "").resolve()
            expected = (workspace / relative).resolve()
            if actual != expected or _sha256(actual) != sources[relative]:
                raise AdapterQualificationError(f"Imported callable is not the pinned byte identity: {function.__name__}")

        object.__setattr__(self, "workspace_root", workspace)
        object.__setattr__(self, "source_files", MappingProxyType(sources))
        object.__setattr__(self, "receipt_files", MappingProxyType(receipts))

    @classmethod
    def from_manifest(
        cls,
        manifest_path: str | Path,
        *,
        workspace_root: str | Path,
    ) -> "QualifiedTelemetryAdapter":
        manifest = _read_json(Path(manifest_path).resolve())
        try:
            row = manifest["implementation"]["qualified_development_loader"]
            sources = {
                item["path"]: item["sha256"] for item in row["source_files"]
            }
            receipts = {
                item["path"]: item["sha256"] for item in row["qualification_receipts"]
            }
            return cls(
                Path(workspace_root),
                str(row["adapter_id"]),
                str(row["scope"]),
                sources,
                receipts,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AdapterQualificationError("Frozen manifest lacks a complete adapter identity") from exc

    @property
    def identity(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "adapter_id": self.adapter_id,
                "scope": self.scope,
                "source_sha256": dict(self.source_files),
                "receipt_sha256": dict(self.receipt_files),
            }
        )

    def source_hashes(self, raw_telemetry: Mapping[str, Any]) -> Mapping[str, str]:
        """Derive verified modality identities from the trusted raw-loader audit."""
        try:
            modalities = raw_telemetry["audit"]["modalities"]
        except (KeyError, TypeError) as exc:
            raise AdapterQualificationError("Raw telemetry lacks a trusted source-identity audit") from exc
        result: dict[str, str] = {}
        for modality in ("metrics", "traces", "logs"):
            row = modalities.get(modality)
            if not isinstance(row, Mapping):
                raise AdapterQualificationError(f"Missing source audit for {modality}")
            status = row.get("status")
            if status == "LOADED":
                if row.get("source_identity_verified") is not True:
                    raise AdapterQualificationError(f"Unverified raw source identity: {modality}")
                result[modality] = _digest(row.get("sha256"), f"raw.{modality}")
            elif status == "MISSING":
                result[modality] = "MISSING"
            elif status == "CORRUPT_OR_UNSUPPORTED":
                result[modality] = "CORRUPT"
            else:
                raise AdapterQualificationError(f"Unknown raw source status: {modality}")
        return MappingProxyType(result)

    def _qualified(self, bundle: Mapping[str, Any], profile: str) -> dict[str, Any]:
        result = dict(bundle)
        audit = copy.deepcopy(dict(result.get("audit", {})))
        audit["qualification"] = {
            "status": "QUALIFIED",
            "adapter_id": self.adapter_id,
            "profile": profile,
            "scope": self.scope,
            "source_sha256": dict(self.source_files),
            "receipt_sha256": dict(self.receipt_files),
        }
        result["audit"] = audit
        return result

    def c1(self, raw_telemetry: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
        from scripts.task_e.loader import c1_bundle

        return self._qualified(c1_bundle(raw_telemetry, **kwargs), "TD12-C1-MT")

    def c5(self, raw_telemetry: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
        from scripts.task_e.loader import c5_bundle

        return self._qualified(c5_bundle(raw_telemetry, **kwargs), "TD13-C5-EVENT-TIME")

    def integrated(self, raw_telemetry: Mapping[str, Any], trigger_epoch: int) -> dict[str, Any]:
        from scripts.task_e.input_adapters import integrated_bundle

        return self._qualified(
            integrated_bundle(raw_telemetry, trigger_epoch),
            "TD12-INTEGRATED-MTL",
        )


__all__ = ["AdapterQualificationError", "QualifiedTelemetryAdapter"]
