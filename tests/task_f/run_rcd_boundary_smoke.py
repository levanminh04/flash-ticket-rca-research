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
from scripts.task_e.rcd_runtime import load_pinned_rcd


W = Path(__file__).resolve().parents[2]
QUALIFICATION = W / "results/task-e/e27-018-rcd-real-qualification"


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
    source = next(
        row
        for row in contract["source_files"]
        if row["path"] == "tests/task_f/run_rcd_boundary_smoke.py"
    )
    if source["sha256"] != sha(Path(__file__)):
        raise RuntimeError("RCD boundary runner changed after run-contract creation")
    references = {row["path"]: row for row in contract["input_files"]}
    for relative in (
        "results/task-e/e27-018-rcd-real-qualification/run-contract.json",
        "results/task-e/e27-018-rcd-real-qualification/rcd-fixture-report.json",
        "results/task-e/e27-041-rcd-development-recovery/rcd-development-results.json",
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
        "schema": "TD13-TASK-F-RCD-BOUNDARY-SMOKE-v1",
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
        loaded = load_pinned_rcd(QUALIFICATION, W)
        shifted = fixture_frame(True)
        identical = fixture_frame(False)
        first = rcd_run(shifted, seed=420, bins=5, upstream_rcd=loaded.rcd)
        second = rcd_run(shifted, seed=420, bins=5, upstream_rcd=loaded.rcd)
        empty = rcd_run(identical, seed=420, bins=5, upstream_rcd=loaded.rcd)
        unqualified = rcd_run(shifted, seed=420, bins=5, upstream_rcd=None)
        if first != second or first["status"] != "SUCCESS" or first["ranks"] != ["m000"]:
            raise AssertionError("Qualified shifted RCD boundary is not exact/deterministic")
        if empty["status"] != "SUCCESS" or empty["ranks"] != []:
            raise AssertionError("Valid empty RCD ranking was not preserved as SUCCESS")
        if unqualified["status"] != "FAILURE" or unqualified["reason"] != "unqualified_upstream_callable":
            raise AssertionError("Unqualified RCD boundary did not fail explicitly")
        receipt["runs"] = [
            {
                "fixture": "separated-shift",
                "input_sha256": frame_sha(shifted),
                "seed": 420,
                "bins": 5,
                "result": first,
                "repeat_exact": True,
            },
            {
                "fixture": "identical-halves",
                "input_sha256": frame_sha(identical),
                "seed": 420,
                "bins": 5,
                "result": empty,
                "valid_empty_is_success": True,
            },
            {
                "fixture": "unqualified-callable",
                "input_sha256": frame_sha(shifted),
                "result": unqualified,
                "failure_visible": True,
            },
        ]
        receipt["qualified_runtime"] = {
            "python": sys.version,
            "executable_name": Path(sys.executable).name,
            "qualification_run_id": loaded.provenance["run_id"],
            "packages": loaded.provenance["packages"],
            "upstream_original_sha256": loaded.provenance["original_rcd_sha256"],
            "adaptation_patch_sha256": loaded.provenance["patch_sha256"],
            "patched_rcd_sha256": loaded.provenance["patched_rcd_sha256"],
            "framework_init_executed": loaded.provenance["framework_init_executed"],
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
