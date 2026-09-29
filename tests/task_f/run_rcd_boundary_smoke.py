"""Bounded real-runtime qualification of the Task F RCD comparator boundary.

The expensive completed development campaign is reused as sealed evidence.
This smoke only calls the already-qualified pinned environment on deterministic
synthetic frames and writes a new Task F receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from rca.comparators import RCD_ADAPTED, rcd_run
from rca.qualified_rcd import QualifiedRcdRunner, load_qualified_rcd


W = Path(__file__).resolve().parents[2]
P = Path(r"D:\Project\flash-ticket-platform")
MANIFEST = W / "configs/task-f-td13-frozen-release-v2.json"


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


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fixture_frame(shift: bool) -> pd.DataFrame:
    base = np.arange(300, dtype=np.float64)
    columns = {"time": np.arange(600, dtype=np.float64)}
    for index in range(6):
        values = ((base * (index + 1)) % (11 + 2 * index)) / (11 + 2 * index)
        columns[f"m{index:03d}"] = np.concatenate(
            [values, values + (30.0 if shift and index == 0 else 0.0)]
        )
    return pd.DataFrame(columns)


def frame_sha(frame: pd.DataFrame) -> str:
    return hashlib.sha256(np.ascontiguousarray(frame.to_numpy()).tobytes()).hexdigest()


def verify_contract(run_dir: Path) -> dict:
    contract = load_json(run_dir / "run-contract.json")
    supplied = contract.pop("contract_sha256")
    expected = hashlib.sha256(canonical(contract)).hexdigest()
    contract["contract_sha256"] = supplied
    if supplied != expected:
        raise RuntimeError("Task F run contract digest mismatch")
    if contract.get("schema") != "TD13-TASK-F-RCD-CORRECTIVE-CONTRACT-v2":
        raise RuntimeError("RCD corrective run-contract schema mismatch")
    if contract.get("run_id") != run_dir.name:
        raise RuntimeError("RCD corrective run-contract ID mismatch")
    if contract["frozen_manifest"] != {
        "path": "configs/task-f-td13-frozen-release-v2.json",
        "sha256": sha(MANIFEST),
    }:
        raise RuntimeError("RCD corrective manifest identity mismatch")
    if contract["td_sha256"] != sha(P / "docs/research-rca/task-d-method-and-experiment-specification.md"):
        raise RuntimeError("RCD corrective TD identity mismatch")
    for row in contract["source_files"]:
        if sha(W / row["path"]) != row["sha256"]:
            raise RuntimeError("RCD corrective source drift: " + row["path"])
    references = {row["path"]: row for row in contract["input_files"]}
    for relative in (
        "results/task-e/e27-018-rcd-real-qualification/run-contract.json",
        "results/task-e/e27-018-rcd-real-qualification/rcd-fixture-report.json",
        "results/task-e/e27-041-rcd-development-recovery/rcd-development-results.json",
        "results/task-f/f06-final-rcd-boundary/rcd-boundary-smoke.json",
    ):
        row = references[relative]
        if sha(W / relative) != row["sha256"]:
            raise RuntimeError(f"Qualified RCD reference drift: {relative}")
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    arguments = parser.parse_args()
    run_dir = Path(arguments.run_dir).resolve()
    try:
        run_dir.relative_to((W / "results/task-f").resolve())
    except ValueError as exc:
        raise SystemExit("Task F run directory must stay under results/task-f") from exc
    report_path = run_dir / "rcd-boundary-smoke.json"
    if report_path.exists():
        raise SystemExit("Never overwrite an existing RCD boundary attempt")
    started = time.perf_counter()
    receipt = {
        "schema": "TD13-TASK-F-RCD-BOUNDARY-SMOKE-v2",
        "scope": "SYNTHETIC BOUNDED RUNTIME QUALIFICATION; NO DEVELOPMENT RERUN; FINAL60 FORBIDDEN",
        "method": RCD_ADAPTED,
        "status": "FAIL",
        "runs": [],
        "failures": [],
        "firewall": {
            "development_telemetry_loaded": False,
            "final60_opened": False,
            "labels_or_root_fault_loaded": False,
        },
    }
    exit_code = 1
    try:
        contract = verify_contract(run_dir)
        receipt["run_id"] = contract["run_id"]
        receipt["contract_sha256"] = contract["contract_sha256"]
        qualified = load_qualified_rcd(workspace_root=W, project_root=P, manifest_path=MANIFEST)
        shifted = fixture_frame(True)
        identical = fixture_frame(False)
        first = rcd_run(shifted, seed=420, bins=5, qualified_rcd=qualified)
        second = rcd_run(shifted, seed=420, bins=5, qualified_rcd=qualified)
        empty = rcd_run(identical, seed=420, bins=5, qualified_rcd=qualified)
        unqualified = rcd_run(shifted, seed=420, bins=5, qualified_rcd=lambda *a, **k: {"ranks": ["m000"]})
        previous = load_json(W / "results/task-f/f06-final-rcd-boundary/rcd-boundary-smoke.json")
        previous_by_fixture = {row["fixture"]: row["result"] for row in previous["runs"]}
        if first != second or first["status"] != "SUCCESS" or first["ranks"] != ["m000"]:
            raise AssertionError("Qualified shifted RCD boundary is not exact/deterministic")
        if empty["status"] != "SUCCESS" or empty["ranks"] != []:
            raise AssertionError("Valid empty RCD ranking was not preserved as SUCCESS")
        if unqualified["status"] != "FAILURE" or unqualified["reason"] != "unqualified_rcd_runner":
            raise AssertionError("Unqualified RCD boundary did not fail explicitly")
        if first != previous_by_fixture["separated-shift"] or empty != previous_by_fixture["identical-halves"]:
            raise AssertionError("Corrective qualified RCD ranking changed relative to f06")
        original_identity = qualified._identity
        object.__setattr__(qualified, "_identity", original_identity + " ")
        tampered_identity = rcd_run(shifted, seed=420, bins=5, qualified_rcd=qualified)
        object.__setattr__(qualified, "_identity", original_identity)
        original_function = qualified._function
        object.__setattr__(qualified, "_function", lambda *a, **k: {"ranks": ["m000"]})
        tampered_function = rcd_run(shifted, seed=420, bins=5, qualified_rcd=qualified)
        object.__setattr__(qualified, "_function", original_function)
        forged_handle = object.__new__(QualifiedRcdRunner)
        object.__setattr__(forged_handle, "_identity", original_identity)
        object.__setattr__(forged_handle, "_function", original_function)
        forged_result = rcd_run(shifted, seed=420, bins=5, qualified_rcd=forged_handle)
        if any(row["reason"] != "unqualified_rcd_runner" for row in (tampered_identity, tampered_function, forged_result)):
            raise AssertionError("Tampered qualified runner was accepted")
        receipt["runs"] = [
            {
                "fixture": "separated-shift",
                "input_sha256": frame_sha(shifted),
                "seed": 420,
                "bins": 5,
                "result": first,
                "repeat_exact": True,
                "f06_result_exact": True,
            },
            {
                "fixture": "identical-halves",
                "input_sha256": frame_sha(identical),
                "seed": 420,
                "bins": 5,
                "result": empty,
                "valid_empty_is_success": True,
                "f06_result_exact": True,
            },
            {
                "fixture": "unqualified-callable",
                "input_sha256": frame_sha(shifted),
                "result": unqualified,
                "failure_visible": True,
            },
            {
                "fixture": "tampered-or-forged-qualified-handle",
                "input_sha256": frame_sha(shifted),
                "identity_result": tampered_identity,
                "function_result": tampered_function,
                "forged_handle_result": forged_result,
                "failure_visible": True,
            },
        ]
        receipt["qualified_runtime"] = {
            "python": sys.version,
            "executable_name": Path(sys.executable).name,
            "qualification_run_id": qualified.identity["qualification_run_id"],
            "qualification_receipt_sha256": qualified.identity["qualification_receipt_sha256"],
            "source_manifest_sha256": qualified.identity["source_manifest_sha256"],
            "packages": qualified.identity["packages"],
            "upstream_original_sha256": qualified.identity["original_rcd_sha256"],
            "adaptation_patch_sha256": qualified.identity["patch_sha256"],
            "patched_rcd_sha256": qualified.identity["patched_rcd_sha256"],
            "release_sha256": qualified.identity["release_sha256"],
        }
        receipt["completed_rcd_development_evidence"] = {
            "path": "results/task-e/e27-041-rcd-development-recovery/rcd-development-results.json",
            "sha256": sha(W / "results/task-e/e27-041-rcd-development-recovery/rcd-development-results.json"),
            "interpretation": "sealed bounded reuse; the 270-config development campaign was not rerun",
        }
        receipt["status"] = "PASS"
        exit_code = 0
    except Exception as exc:
        receipt["failures"].append(
            {
                "failure_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            }
        )
    receipt["wall_seconds"] = time.perf_counter() - started
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "report_sha256": sha(report_path)}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
