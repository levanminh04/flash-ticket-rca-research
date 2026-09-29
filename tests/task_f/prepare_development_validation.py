"""Create a write-once Task F development-validation contract.

The contract materializes only the registered development30 allowlist and the
already-sealed artifacts needed for implementation validation.  It never
enumerates, downloads, or opens final60 material.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path


W = Path(__file__).resolve().parents[2]
P = Path(r"D:\Project\flash-ticket-platform")
TD = P / "docs/research-rca/task-d-method-and-experiment-specification.md"
REGISTRY = W / "configs/task-e-td13-development.json"
MANIFEST = W / "configs/task-f-td13-frozen-release.json"
V2_MANIFEST = W / "configs/task-f-td13-frozen-release-v2.json"
AUDITS = W / "results/task-e/e27-019-development-loader-audit/case-audits"
C1 = W / "results/task-e/e27-033-c1-development-full"
C5 = W / "results/task-e/e27-035-c5-development-full"
EXPECTED_TD = "34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(W.resolve()).as_posix()
    except ValueError:
        return "P/" + resolved.relative_to(P.resolve()).as_posix()


def reference(path: Path, role: str) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": relative(path),
        "sha256": sha(path),
        "bytes": path.stat().st_size,
        "role": role,
    }


def git_value(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def environment_lock() -> dict[str, object]:
    packages = sorted(
        {
            (
                (distribution.metadata.get("Name") or "UNKNOWN").lower(),
                distribution.version,
            )
            for distribution in importlib.metadata.distributions()
        }
    )
    material = {
        "python": sys.version,
        "executable_name": Path(sys.executable).name,
        "platform": platform.platform(),
        "packages": [{"name": name, "version": version} for name, version in packages],
    }
    material["canonical_sha256"] = hashlib.sha256(canonical(material)).hexdigest()
    return material


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def create_rcd_corrective_contract(run_dir: Path) -> int:
    """Prepare a new bounded attempt using pinned evidence, not telemetry."""
    if run_dir.exists():
        raise SystemExit("Never overwrite an existing Task F corrective attempt")
    manifest = load_json(V2_MANIFEST)
    if manifest["implementation"]["release_id"] != "TASK-F-TD13-v2":
        raise SystemExit("Expected Task F v2 successor release")
    source_files = [
        reference(W / relative, "corrective-source")
        for relative in (
            "src/rca/__init__.py",
            "src/rca/comparators.py",
            "src/rca/qualified_rcd.py",
            "scripts/task_e/rcd_runtime.py",
            "tests/task_f/prepare_development_validation.py",
            "tests/task_f/run_rcd_boundary_smoke.py",
        )
    ]
    input_files = [
        reference(W / relative, "immutable-qualification-evidence")
        for relative in (
            "results/task-e/e27-018-rcd-real-qualification/run-contract.json",
            "results/task-e/e27-018-rcd-real-qualification/rcd-fixture-report.json",
            "results/task-e/e27-041-rcd-development-recovery/rcd-development-results.json",
            "results/task-f/f06-final-rcd-boundary/rcd-boundary-smoke.json",
        )
    ]
    contract = {
        "schema": "TD13-TASK-F-RCD-CORRECTIVE-CONTRACT-v2",
        "run_id": run_dir.name,
        "scope": "BOUNDED SYNTHETIC RCD QUALIFICATION ONLY; NO DEVELOPMENT TELEMETRY OR FINAL60",
        "status": "PLANNED",
        "td_sha256": EXPECTED_TD,
        "frozen_manifest": {"path": relative(V2_MANIFEST), "sha256": sha(V2_MANIFEST)},
        "predecessor_release": manifest["predecessor_release"],
        "source_files": source_files,
        "input_files": input_files,
        "registered_parameters": next(row["primary"] for row in manifest["comparators"] if row["id"] == "RCD-RCAEval-adapted-TD12"),
        "expected_interpreter": "environments/task-e/rcd39/Scripts/python.exe; Python 3.9",
        "command": (
            "$env:PYTHONPATH='src;.'; .\\environments\\task-e\\rcd39\\Scripts\\python.exe -u "
            f"tests/task_f/run_rcd_boundary_smoke.py --run-dir {relative(run_dir)}"
        ),
        "firewall": {
            "development_telemetry_loaded": False,
            "final60_enumerated_or_loaded": False,
            "labels_or_root_fault_loaded": False,
        },
        "repository_state": {
            "P_branch": git_value(P, "branch", "--show-current"),
            "P_head": git_value(P, "rev-parse", "HEAD"),
            "W_branch": git_value(W, "branch", "--show-current"),
            "W_head": git_value(W, "rev-parse", "HEAD"),
            "working_tree_identity": "per-file SHA256 in source_files and frozen_manifest",
        },
    }
    contract["contract_sha256"] = hashlib.sha256(canonical(contract)).hexdigest()
    run_dir.mkdir(parents=True)
    with (run_dir / "run-contract.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(contract, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"run_id": run_dir.name, "contract_sha256": contract["contract_sha256"]}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--rcd-only", action="store_true")
    arguments = parser.parse_args()
    run_dir = Path(arguments.run_dir).resolve()
    try:
        run_dir.relative_to((W / "results/task-f").resolve())
    except ValueError as exc:
        raise SystemExit("Task F run directory must stay under results/task-f") from exc
    if run_dir.exists():
        raise SystemExit("Never overwrite an existing Task F validation attempt")
    if sha(TD) != EXPECTED_TD:
        raise SystemExit("Frozen TD-v1.3 hash drift; validation contract not created")
    if arguments.rcd_only:
        return create_rcd_corrective_contract(run_dir)

    registry = load_json(REGISTRY)
    development_ids = list(registry["development_ids"])
    if len(development_ids) != 30 or len(set(development_ids)) != 30:
        raise SystemExit("Registered development30 allowlist is not exactly 30 unique IDs")
    if registry.get("final_evaluation") != "FORBIDDEN; no final IDs/materialized labels here":
        raise SystemExit("Development registry final-evaluation firewall changed")
    allowed = set(development_ids)

    audit_by_case: dict[str, tuple[str, Path]] = {}
    for path in sorted(AUDITS.glob("*.json")):
        row = load_json(path)
        case = row.get("case")
        if case in allowed:
            audit_by_case[case] = (row.get("handle"), path)
    if set(audit_by_case) != allowed:
        raise SystemExit("Development case-audit mapping differs from registered allowlist")
    handles = [audit_by_case[case][0] for case in development_ids]
    if any(not isinstance(handle, str) or not handle for handle in handles):
        raise SystemExit("Missing opaque handle in development case-audit mapping")
    if len(set(handles)) != 30:
        raise SystemExit("Development opaque handles are not unique")

    source_files = [
        reference(TD, "frozen-executed-protocol"),
        reference(MANIFEST, "task-f-frozen-release-manifest"),
        reference(REGISTRY, "development-only-registry"),
        reference(W / "results/task-f/frozen-selection-extraction.json", "selection-extraction-receipt"),
        reference(C1 / "local-selection.json", "sealed-c1-selection"),
        reference(C1 / "selection.json", "sealed-c1-selection"),
        reference(C1 / "observed-execution-plan.json", "sealed-c1-plan"),
        reference(C1 / "run-contract.json", "historical-c1-contract"),
        reference(C5 / "lambda-selection.json", "sealed-c5-selection"),
        reference(C5 / "c5-selection.json", "sealed-c5-selection"),
        reference(C5 / "predictions-seal.json", "historical-c5-seal"),
        reference(C5 / "run-contract.json", "historical-c5-contract"),
        reference(Path(__file__), "validation-contract-author"),
        reference(W / "tests/task_f/run_development_validation.py", "validation-runner"),
        reference(W / "tests/task_f/run_rcd_boundary_smoke.py", "rcd-boundary-runner"),
    ]
    source_files.extend(
        reference(path, "task-f-release-source")
        for path in sorted((W / "src/rca").glob("*.py"))
    )

    input_files: list[dict[str, object]] = []
    first_smoke_case = registry["smoke_ids"][0]
    first_smoke_handle = audit_by_case[first_smoke_case][0]
    for case in development_ids:
        handle, audit_path = audit_by_case[case]
        c1_input = W / f"results/task-e/e27-019-development-loader-audit/intermediates/{handle}/c1_primary.npz"
        c1_predictions = C1 / "predictions"
        c5_predictions = C5 / "predictions/primary" / handle
        input_files.extend(
            [
                reference(audit_path, "development-loader-audit-controller-only"),
                reference(c1_input, "sealed-c1-numeric-input"),
                reference(c1_predictions / f"{handle}.npz", "sealed-c1-local-output"),
                reference(c1_predictions / f"{handle}-observed-local6.npz", "sealed-c1-graph-output"),
                reference(c1_predictions / f"{handle}-comparators.npz", "sealed-c1-comparator-output"),
                reference(c5_predictions / "numeric-input.npz", "sealed-c5-numeric-input"),
                reference(c5_predictions / "predictions.npz", "sealed-c5-output"),
                reference(c5_predictions / "start.json", "sealed-c5-config-order"),
                reference(c5_predictions / "seal.json", "sealed-c5-case-receipt"),
            ]
        )
        if handle == first_smoke_handle:
            input_files.append(
                reference(c1_predictions / f"{handle}-R-undirected.npz", "sealed-c1-r-control-output")
            )

    rcd_qualification = W / "results/task-e/e27-018-rcd-real-qualification"
    input_files.extend(
        [
            reference(rcd_qualification / "run-contract.json", "qualified-rcd-runtime-contract"),
            reference(rcd_qualification / "rcd-fixture-report.json", "qualified-rcd-runtime-evidence"),
            reference(W / "results/task-e/e27-041-rcd-development-recovery/rcd-development-results.json", "sealed-rcd-development-qualification"),
        ]
    )

    run_id = run_dir.name
    contract = {
        "schema": "TD13-TASK-F-DEVELOPMENT-VALIDATION-CONTRACT-v1",
        "run_id": run_id,
        "scope": "DEVELOPMENT30 IMPLEMENTATION VALIDATION ONLY; NOT EFFICACY; FINAL60 FORBIDDEN",
        "status": "PLANNED",
        "td_sha256": EXPECTED_TD,
        "frozen_manifest": {
            "path": relative(MANIFEST),
            "file_sha256": sha(MANIFEST),
            "canonical_sha256": hashlib.sha256(canonical(load_json(MANIFEST))).hexdigest(),
        },
        "dataset_revision": registry["dataset_revision"],
        "development_allowlist": development_ids,
        "development_allowlist_sha256": hashlib.sha256(canonical(development_ids)).hexdigest(),
        "opaque_handles_by_development_id": dict(zip(development_ids, handles, strict=True)),
        "smoke_rule": registry["smoke_rule"],
        "smoke_ids": list(registry["smoke_ids"]),
        "predetermined_major_mode_smoke": first_smoke_case,
        "source_files": source_files,
        "input_files": input_files,
        "environment_lock": environment_lock(),
        "repository_state": {
            "P_branch": git_value(P, "branch", "--show-current"),
            "P_head": git_value(P, "rev-parse", "HEAD"),
            "W_branch": git_value(W, "branch", "--show-current"),
            "W_head": git_value(W, "rev-parse", "HEAD"),
            "working_tree_identity": "explicit per-file hashes above; untracked Task F release",
        },
        "commands": {
            "development_validation": (
                "$env:PYTHONPATH='src;.'; .\\.venv\\Scripts\\python.exe -u "
                f"tests/task_f/run_development_validation.py --run-dir {relative(run_dir)}"
            ),
            "rcd_boundary_smoke": (
                "$env:PYTHONPATH='src;.'; .\\environments\\task-e\\rcd39\\Scripts\\python.exe -u "
                f"tests/task_f/run_rcd_boundary_smoke.py --run-dir {relative(run_dir)}"
            ),
        },
        "registered_seeds": {
            "R": "first64bits-big-endian SHA256(TD12|R|opaque_handle|representation|draw)",
            "R_draws": 256,
            "R_proposals_per_edge": 200,
            "RCD_smoke_seed": 420,
            "RCD_smoke_bins": 5,
        },
        "cache_contract": {
            "profiles": ["c1-primary", "c5-primary"],
            "relative_cutoffs": {"c1-primary": [300, 600], "c5-primary": 1440},
            "full_case_cache_as_prefix": "FORBIDDEN",
        },
        "planned_outputs": [
            "development-validation.json",
            "rcd-boundary-smoke.json",
            "packets/<opaque>-c1.json",
            "packets/<opaque>-c5-G-MTL.json",
            "cache/<identity>.json",
            "cache/<identity>.npz",
        ],
        "precontract_attempts": [
            {
                "attempt": 1,
                "status": "FAILED_BEFORE_RUN_CONTRACT",
                "failure_type": "KeyError",
                "cause": "preparer incorrectly expected canonical_sha256 to be embedded in the manifest instead of deriving it from canonical JSON",
                "effect": "no run directory or validation artifact was created; no numeric pipeline executed",
                "correction": "derive the same canonical JSON digest used by src/rca/contracts.py",
            }
        ],
        "firewall": {
            "final60_enumerated": False,
            "final60_telemetry_loaded": False,
            "final_labels_loaded": False,
            "ground_truth_passed_to_core": False,
            "case_audit_use": "controller mapping + service identities/status only; metadata/root/fault/tau excluded",
        },
    }
    contract["contract_sha256"] = hashlib.sha256(canonical(contract)).hexdigest()
    run_dir.mkdir(parents=True)
    with (run_dir / "run-contract.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(contract, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"run_id": run_id, "contract_sha256": contract["contract_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
