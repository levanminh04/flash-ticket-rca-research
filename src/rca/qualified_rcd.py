"""Controller-side admission for the pinned Task E RCD implementation.

An issued runner binds the verified release, source, qualification receipt and
runtime to one loaded function.  This is an integrity boundary for ordinary
callers, not a sandbox against hostile code already executing in this process.
"""

from __future__ import annotations

import hashlib
import json
import marshal
import sys
from pathlib import Path
from types import FunctionType


_RUN_ID = "e27-018-rcd-real-qualification"
_REPORT = "results/task-e/e27-018-rcd-real-qualification/rcd-fixture-report.json"
_REPORT_SHA = "8238a708c315b3c0ce0c59aeff6622489c96e4a33bcb60f0222bca1eab2ec123"
_CONTRACT = "results/task-e/e27-018-rcd-real-qualification/run-contract.json"
_CONTRACT_SHA = "5e0f4e4b90f9a654411a5a2edd8d22c56275080e6020a1f8d31a03e8b095d408"
_V1_SHA = "18484bc4bb0c1d19e8f6936f12d8365a8ad69e16fffa2bf6ce5968189f0561e5"
_V1_COMMIT = "e70f40f5549574ac4518436cc476087f8cf2d9f6"
class RcdQualificationError(RuntimeError):
    """The requested RCD source or qualification evidence is not pinned."""


class QualifiedRcdRunner:
    """Immutable handle issued only after pinned source and receipt admission."""

    __slots__ = ("_function", "_identity", "__weakref__")

    def __init__(self):
        raise TypeError("Use load_qualified_rcd to obtain an issued runner")

    def __setattr__(self, name, value):
        raise AttributeError("QualifiedRcdRunner is immutable")

    @property
    def identity(self):
        return json.loads(self._identity)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _checked_file(workspace: Path, relative: str, expected: str) -> Path:
    path = (workspace / relative).resolve()
    path.relative_to(workspace)
    if not path.is_file() or _sha(path) != expected:
        raise RcdQualificationError("Pinned RCD evidence mismatch: " + relative)
    return path


def _pinned_manifest(manifest_path: Path, workspace: Path, project: Path):
    from .release import verify_frozen_release

    if manifest_path.resolve() != (workspace / "configs/task-f-td13-frozen-release-v2.json").resolve():
        raise RcdQualificationError("RCD requires the Task F v2 release manifest")
    verification = verify_frozen_release(manifest_path, workspace_root=workspace, project_root=project)
    if verification["status"] != "PASS":
        raise RcdQualificationError("Task F v2 release verification failed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    implementation = manifest["implementation"]
    predecessor = manifest["predecessor_release"]
    if implementation["release_id"] != "TASK-F-TD13-v2" or predecessor != {
        "commit": _V1_COMMIT,
        "manifest": {"path": "configs/task-f-td13-frozen-release.json", "sha256": _V1_SHA},
    }:
        raise RcdQualificationError("Task F v2 predecessor identity mismatch")
    rows = [row for row in manifest["comparators"] if row.get("id") == "RCD-RCAEval-adapted-TD12"]
    if len(rows) != 1:
        raise RcdQualificationError("RCD comparator identity is not unique")
    row = rows[0]
    expected = {
        "bins": 5,
        "seeds": [420, 421, 422],
        "gamma": 5,
        "localized": True,
        "dk_select_useful": False,
        "dataset": None,
    }
    if row.get("primary") != expected:
        raise RcdQualificationError("RCD registered execution parameters changed")
    if row.get("qualification_report") != {"path": _REPORT, "sha256": _REPORT_SHA}:
        raise RcdQualificationError("RCD qualification receipt identity changed")
    if row.get("qualification_contract") != {"path": _CONTRACT, "sha256": _CONTRACT_SHA}:
        raise RcdQualificationError("RCD qualification contract identity changed")
    return manifest, row, verification


def _verify_evidence_identity(row, source):
    from scripts.task_e import rcd_runtime

    expected = {
        "upstream_revision": rcd_runtime.RCAEVAL_REVISION,
        "original_lineage_revision": rcd_runtime.ORIGINAL_REVISION,
        "source_manifest_sha256": "f63c6224168d82613ef0a0b1d7c99f18fc94613895b4346528a3a80ba29b2c68",
        "patch_sha256": rcd_runtime.PATCH_SHA256,
        "original_rcd_sha256": rcd_runtime.ORIGINAL_SHA256,
        "patched_rcd_sha256": rcd_runtime.PATCHED_SHA256,
    }
    if any(row.get(key) != value for key, value in expected.items()):
        raise RcdQualificationError("RCD release source/patch identity mismatch")
    for key in ("source_manifest_sha256", "patch_sha256", "original_rcd_sha256", "patched_rcd_sha256"):
        if source.get(key) != expected[key]:
            raise RcdQualificationError("RCD qualification receipt source/patch mismatch")
    if row.get("qualification_report") != {"path": _REPORT, "sha256": _REPORT_SHA}:
        raise RcdQualificationError("RCD qualification receipt identity mismatch")
    if row.get("qualification_contract") != {"path": _CONTRACT, "sha256": _CONTRACT_SHA}:
        raise RcdQualificationError("RCD qualification contract identity mismatch")


def _admit_pinned(*, workspace_root, project_root, manifest_path):
    """Return the verified bare function and its evidence-bound identity."""
    from scripts.task_e import rcd_runtime

    workspace = Path(workspace_root).resolve()
    project = Path(project_root).resolve()
    manifest_file = Path(manifest_path).resolve()
    try:
        manifest, row, verification = _pinned_manifest(manifest_file, workspace, project)
        report_path = _checked_file(workspace, _REPORT, _REPORT_SHA)
        _checked_file(workspace, _CONTRACT, _CONTRACT_SHA)
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
        source = report["provenance"]
        _verify_evidence_identity(row, source)
        if report.get("passed") is not True or report.get("tests_run") != 4:
            raise RcdQualificationError("RCD qualification receipt is not PASS")
        if source.get("run_id") != _RUN_ID or source.get("framework_init_executed") is not False:
            raise RcdQualificationError("RCD qualification provenance mismatch")
        if source.get("source_manifest_sha256") != _sha(workspace / "baselines/task-e-source-manifest.json"):
            raise RcdQualificationError("RCD source manifest drift")
        if source.get("packages") != rcd_runtime.PINNED_PACKAGES:
            raise RcdQualificationError("RCD qualification package lock mismatch")
        successful = {
            (run.get("seed"), run.get("bins"))
            for run in report.get("numeric_runs", [])
            if run.get("fixture") == "separated-shift" and run.get("result", {}).get("status") == "SUCCESS"
        }
        if successful != {(seed, bins) for seed in (420, 421, 422) for bins in (3, 5, 7)}:
            raise RcdQualificationError("RCD qualification did not cover registered seeds/bins")
        loaded = rcd_runtime.load_pinned_rcd(workspace / "results/task-e" / _RUN_ID, workspace)
        provenance = loaded.provenance
        for key in ("source_manifest_sha256", "patch_sha256", "original_rcd_sha256", "patched_rcd_sha256"):
            if provenance.get(key) != source.get(key):
                raise RcdQualificationError("Loaded RCD differs from qualification receipt: " + key)
        if provenance.get("run_id") != _RUN_ID or provenance.get("packages") != source.get("packages"):
            raise RcdQualificationError("Loaded RCD runtime provenance mismatch")
        if Path(provenance["executable"]).resolve() != Path(sys.executable).resolve():
            raise RcdQualificationError("Loaded RCD interpreter identity mismatch")
        if provenance.get("python") != sys.version or provenance.get("python") != source.get("python"):
            raise RcdQualificationError("Loaded RCD Python runtime differs from qualification")
        if Path(source["executable"]).resolve() != Path(sys.executable).resolve():
            raise RcdQualificationError("RCD qualification interpreter differs from current runtime")
        identity = {
            "release_id": manifest["implementation"]["release_id"],
            "release_sha256": verification["manifest_file_sha256"],
            "td_sha256": verification["td_sha256"],
            "upstream_revision": row["upstream_revision"],
            "original_lineage_revision": row["original_lineage_revision"],
            "source_manifest_sha256": row["source_manifest_sha256"],
            "patch_sha256": row["patch_sha256"],
            "original_rcd_sha256": row["original_rcd_sha256"],
            "patched_rcd_sha256": row["patched_rcd_sha256"],
            "qualification_run_id": _RUN_ID,
            "qualification_receipt_sha256": _REPORT_SHA,
            "qualification_contract_sha256": _CONTRACT_SHA,
            "python": sys.version,
            "executable": str(Path(sys.executable).resolve()),
            "packages": provenance["packages"],
            "parameters": row["primary"],
        }
        return loaded.rcd, identity
    except RcdQualificationError:
        raise
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as exc:
        raise RcdQualificationError("Pinned RCD qualification failed: " + type(exc).__name__) from exc


def _function_fingerprint(function):
    if type(function) is not FunctionType:
        return None
    material = (
        marshal.dumps(function.__code__)
        + repr(function.__defaults__).encode("utf-8")
        + repr(function.__kwdefaults__).encode("utf-8")
    )
    return hashlib.sha256(material).hexdigest()


def _bound_api():
    # The Task E loader itself is one-shot per isolated interpreter. Bind the
    # exact object issued by that one admission, not an extensible registry.
    issued_runner = None
    issued_function = None
    issued_identity = None
    issued_fingerprint = None
    admit = _admit_pinned

    def load_qualified_rcd(*, workspace_root, project_root, manifest_path):
        """Issue only the function returned by the pinned Task E admission."""
        nonlocal issued_runner, issued_function, issued_identity, issued_fingerprint
        if issued_runner is not None:
            raise RcdQualificationError("Pinned RCD runner is already issued in this interpreter")
        function, identity = admit(
            workspace_root=workspace_root,
            project_root=project_root,
            manifest_path=manifest_path,
        )
        fingerprint = _function_fingerprint(function)
        if fingerprint is None:
            raise RcdQualificationError("Pinned RCD did not return a Python function")
        runner = object.__new__(QualifiedRcdRunner)
        encoded_identity = _canonical(identity).decode("utf-8")
        object.__setattr__(runner, "_function", function)
        object.__setattr__(runner, "_identity", encoded_identity)
        issued_runner = runner
        issued_function = function
        issued_identity = encoded_identity
        issued_fingerprint = fingerprint
        return runner

    def qualified_callable(runner):
        """Return the issued function only while its handle and code are intact."""
        if type(runner) is not QualifiedRcdRunner or runner is not issued_runner:
            return None
        try:
            identity = json.loads(runner._identity)
            intact = runner._function is issued_function and runner._identity == issued_identity
            intact = intact and identity["executable"] == str(Path(sys.executable).resolve())
            intact = intact and _function_fingerprint(issued_function) == issued_fingerprint
        except (AttributeError, KeyError, TypeError, ValueError):
            return None
        return issued_function if intact else None

    return load_qualified_rcd, qualified_callable


load_qualified_rcd, qualified_callable = _bound_api()
del _bound_api


__all__ = ["QualifiedRcdRunner", "RcdQualificationError", "load_qualified_rcd"]
