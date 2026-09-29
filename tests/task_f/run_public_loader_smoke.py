"""Qualify the injected public-telemetry loader boundary on one dev smoke.

The development case is predeclared by the registry's minimum-issued-handle
rule.  This script reuses the exact Task E loader/replay bytes and verified raw
public telemetry; it does not acquire data, enumerate final60, select a method,
or write to any completed Task E directory.
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

from rca import FrozenRcaPipeline, QualifiedTelemetryAdapter
from rca.observation import admit_c1_bundle
from rca.packet import validate_packet
from scripts.task_e.loader import c1_bundle, c5_bundle, load_case


W = Path(__file__).resolve().parents[2]
P = Path(r"D:\Project\flash-ticket-platform")
MANIFEST = W / "configs/task-f-td13-frozen-release.json"
REGISTRY = W / "configs/task-e-td13-development.json"
AUDIT = W / "results/task-e/e27-019-development-loader-audit/case-audits/45e43770afa33cef.json"
SOURCE_MANIFEST = W / "results/task-e/e27-019-development-loader-audit/source-manifest.json"
C1 = W / "results/task-e/e27-033-c1-development-full"
C5 = W / "results/task-e/e27-035-c5-development-full"
CASE = "re2tt_ts-auth-service_cpu_3"
HANDLE = "45e43770afa33cef"


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


def reference(path: Path, role: str) -> dict[str, object]:
    return {
        "path": path.resolve().relative_to(W.resolve()).as_posix(),
        "sha256": sha(path),
        "bytes": path.stat().st_size,
        "role": role,
    }


def code_identity() -> dict[str, str]:
    return {
        path.relative_to(W).as_posix(): sha(path)
        for path in sorted((W / "src/rca").glob("*.py"))
    }


def source_relationship() -> list[dict[str, object]]:
    historical = load_json(SOURCE_MANIFEST)
    rows = {Path(row["path"]).resolve(): row for row in historical["files"]}
    results = []
    for path in (W / "scripts/task_e/loader.py", W / "scripts/task_e/replay.py"):
        row = rows[path.resolve()]
        current = sha(path)
        snapshot = hashlib.sha256(row["utf8_snapshot"].encode("utf-8")).hexdigest()
        classification = (
            "EXECUTION_BYTES_EXACT"
            if current == row["sha256"] == snapshot
            else "UNKNOWN_MATERIAL_DRIFT"
        )
        results.append(
            {
                "path": path.relative_to(W).as_posix(),
                "execution_sha256": row["sha256"],
                "current_sha256": current,
                "utf8_snapshot_sha256": snapshot,
                "classification": classification,
            }
        )
    return results


def prepare(run_dir: Path) -> int:
    if run_dir.exists():
        raise SystemExit("Never overwrite an existing public-loader validation attempt")
    registry = load_json(REGISTRY)
    if registry["smoke_ids"][0] != CASE or len(registry["development_ids"]) != 30:
        raise SystemExit("Predetermined development smoke rule/allowlist drift")
    audit = load_json(AUDIT)
    if audit["case"] != CASE or audit["handle"] != HANDLE:
        raise SystemExit("Predetermined case/opaque-handle mapping drift")
    relationship = source_relationship()
    if any(row["classification"] != "EXECUTION_BYTES_EXACT" for row in relationship):
        raise SystemExit("Task E loader/replay source relationship is not exact")

    raw_files = []
    for modality in ("metrics", "traces", "logs"):
        row = audit["physical"]["modalities"][modality]
        path = Path(row["path"])
        if not row["source_identity_verified"] or sha(path) != row["expected_sha256"]:
            raise SystemExit(f"Raw public telemetry identity drift: {modality}")
        raw_files.append(reference(path, f"verified-public-{modality}"))
    sources = [
        reference(Path(__file__), "public-loader-validation-runner"),
        reference(MANIFEST, "frozen-release-manifest"),
        reference(REGISTRY, "development-only-registry"),
        reference(AUDIT, "controller-only-case-audit"),
        reference(SOURCE_MANIFEST, "historical-execution-source-manifest"),
        reference(W / "scripts/task_e/loader.py", "exact-qualified-task-e-loader"),
        reference(W / "scripts/task_e/replay.py", "exact-qualified-task-e-replay"),
        reference(W / f"results/task-e/e27-019-development-loader-audit/intermediates/{HANDLE}/c1_primary.npz", "sealed-c1-numeric-input"),
        reference(C1 / "predictions" / f"{HANDLE}.npz", "sealed-c1-local-output"),
        reference(C1 / "predictions" / f"{HANDLE}-observed-local6.npz", "sealed-c1-graph-output"),
        reference(C5 / "predictions/primary" / HANDLE / "numeric-input.npz", "sealed-c5-numeric-input"),
        reference(C5 / "predictions/primary" / HANDLE / "predictions.npz", "sealed-c5-output"),
    ]
    sources.extend(reference(path, "task-f-release-source") for path in sorted((W / "src/rca").glob("*.py")))
    contract = {
        "schema": "TD13-TASK-F-PUBLIC-LOADER-SMOKE-CONTRACT-v1",
        "run_id": run_dir.name,
        "scope": "ONE PREDECLARED DEVELOPMENT SMOKE; RAW PUBLIC TELEMETRY; FINAL60 FORBIDDEN",
        "status": "PLANNED",
        "case": CASE,
        "opaque_handle": HANDLE,
        "smoke_rule": registry["smoke_rule"],
        "td_sha256": load_json(MANIFEST)["td"]["sha256"],
        "frozen_manifest_file_sha256": sha(MANIFEST),
        "frozen_manifest_canonical_sha256": hashlib.sha256(canonical(load_json(MANIFEST))).hexdigest(),
        "source_relationship": relationship,
        "source_files": sources,
        "raw_input_files": raw_files,
        "release_code_identity": code_identity(),
        "command": (
            "$env:PYTHONPATH='src;.'; .\\.venv\\Scripts\\python.exe -u "
            f"tests/task_f/run_public_loader_smoke.py --mode run --run-dir {run_dir.relative_to(W).as_posix()}"
        ),
        "firewall": {
            "final60_enumerated": False,
            "final60_loaded": False,
            "root_fault_tau_passed_to_core": False,
            "tau_use": "controller-only loader window argument; absent from admitted observation and packet",
        },
    }
    contract["contract_sha256"] = hashlib.sha256(canonical(contract)).hexdigest()
    run_dir.mkdir(parents=True)
    with (run_dir / "run-contract.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(contract, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": "PLANNED", "contract_sha256": contract["contract_sha256"]}))
    return 0


def verify_contract(run_dir: Path) -> dict:
    contract = load_json(run_dir / "run-contract.json")
    supplied = contract.pop("contract_sha256")
    expected = hashlib.sha256(canonical(contract)).hexdigest()
    contract["contract_sha256"] = supplied
    if supplied != expected:
        raise RuntimeError("Public-loader run contract digest mismatch")
    for row in contract["source_files"] + contract["raw_input_files"]:
        path = W / row["path"]
        if not path.is_file() or sha(path) != row["sha256"]:
            raise RuntimeError(f"Public-loader declared input drift: {row['path']}")
    return contract


def exact_bundle(actual: dict, expected_path: Path, keys: tuple[str, ...]) -> None:
    with np.load(expected_path, allow_pickle=False) as expected:
        for key in keys:
            np.testing.assert_array_equal(actual[key], expected[key])


def run(run_dir: Path) -> int:
    report_path = run_dir / "public-loader-smoke.json"
    if report_path.exists():
        raise SystemExit("Never overwrite an existing public-loader smoke receipt")
    started = time.perf_counter()
    receipt = {
        "schema": "TD13-TASK-F-PUBLIC-LOADER-SMOKE-v1",
        "scope": "RAW PUBLIC DEVELOPMENT TELEMETRY TO TASK F PACKET; NOT EFFICACY; FINAL60 FORBIDDEN",
        "status": "FAIL",
        "failures": [],
        "firewall": {
            "final60_opened": False,
            "oracle_metadata_passed_to_core": False,
            "absolute_case_path_in_packet": False,
            "absolute_epoch_in_packet": False,
        },
    }
    exit_code = 1
    try:
        contract = verify_contract(run_dir)
        receipt["run_id"] = contract["run_id"]
        receipt["contract_sha256"] = contract["contract_sha256"]
        audit = load_json(AUDIT)
        paths = {}
        expected = {}
        raw_hashes = {}
        for modality in ("metrics", "traces", "logs"):
            row = audit["physical"]["modalities"][modality]
            paths[modality] = row["path"] if row["present"] else None
            if row["present"]:
                expected[modality] = {
                    "sha256": row["expected_sha256"],
                    "bytes": row["expected_bytes"],
                }
                raw_hashes[modality] = row["expected_sha256"]
            else:
                raw_hashes[modality] = "MISSING"
        raw = load_case(paths, audit["metadata"], expected_files=expected)
        core = FrozenRcaPipeline.from_manifest(
            MANIFEST,
            code_identity=contract["release_code_identity"],
            release_id="TASK-F-TD13-v1",
        )
        tau = int(audit["metadata"]["inject_time"])
        adapter = QualifiedTelemetryAdapter.from_manifest(MANIFEST, workspace_root=W)
        c1_loaded = adapter.c1(raw, tau=tau, bin_seconds=10, horizon=300)
        exact_bundle(
            c1_loaded,
            W / f"results/task-e/e27-019-development-loader-audit/intermediates/{HANDLE}/c1_primary.npz",
            ("ref", "query", "adj", "channel_types"),
        )

        c1_result = core.run_public_c1(
            raw,
            qualified_adapter=adapter,
            loader_kwargs={"tau": tau, "bin_seconds": 10, "horizon": 300},
            handle=HANDLE,
            include_structural_control=False,
        )
        if c1_result["status"] != "SUCCESS" or not validate_packet(c1_result["packet"]):
            raise RuntimeError("Raw public C1 boundary did not produce a valid packet")
        with np.load(C1 / "predictions" / f"{HANDLE}.npz", allow_pickle=False) as expected_c1:
            np.testing.assert_array_equal(c1_result["L_scores"], expected_c1["local"][6])
        with np.load(C1 / "predictions" / f"{HANDLE}-observed-local6.npz", allow_pickle=False) as expected_c1:
            np.testing.assert_array_equal(c1_result["O"]["scores"], expected_c1["scores"][4])

        c5_loaded = adapter.c5(
            raw,
            bin_seconds=5,
            warmup_seconds=180,
            fit_bins=24,
            cal_bins=12,
            cutoff_seconds=1440,
        )
        exact_bundle(
            c5_loaded,
            C5 / "predictions/primary" / HANDLE / "numeric-input.npz",
            ("values", "adj", "channel_types", "fit_service_mask", "endpoints"),
        )

        c5_result = core.run_public_c5(
            raw,
            "G-MTL",
            qualified_adapter=adapter,
            loader_kwargs={
                "bin_seconds": 5,
                "warmup_seconds": 180,
                "fit_bins": 24,
                "cal_bins": 12,
                "cutoff_seconds": 1440,
            },
            handle=HANDLE,
        )
        if c5_result["status"] != "SUCCESS" or not validate_packet(c5_result["packet"]):
            raise RuntimeError("Raw public C5 boundary did not produce a valid packet")
        with np.load(C5 / "predictions/primary" / HANDLE / "predictions.npz", allow_pickle=False) as expected_c5:
            predictions = np.stack([row["predictions"] for row in c5_result["bins"]])
            residuals = np.stack([row["residuals"] for row in c5_result["bins"]])
            scores = np.array([row["score"] for row in c5_result["bins"]])
            np.testing.assert_array_equal(predictions, expected_c5["predictions"][2])
            np.testing.assert_array_equal(residuals, expected_c5["residuals"][2])
            np.testing.assert_array_equal(scores, expected_c5["scores"][2])
        integrated_result = core.run_public_c5(
            raw,
            "L-MTL",
            qualified_adapter=adapter,
            loader_kwargs={
                "bin_seconds": 5,
                "warmup_seconds": 180,
                "fit_bins": 24,
                "cal_bins": 12,
                "cutoff_seconds": 1440,
            },
            handle=HANDLE,
        )
        exact_integrated = []
        for endpoint in (630, 1125):
            integrated_bundle = adapter.integrated(raw, int(c5_loaded["s0"]) + endpoint)
            integrated_observation = admit_c1_bundle(
                integrated_bundle,
                handle=HANDLE,
                source_hashes=adapter.source_hashes(raw),
            )
            row = core.run_integrated(
                integrated_observation,
                relative_endpoint=endpoint,
            )
            if row["status"] != "SUCCESS":
                raise AssertionError("Integrated diagnosis did not complete")
            scores = np.empty(row["ranking"]["candidate_count"], dtype=np.float64)
            for ranked in row["ranking"]["rows"]:
                scores[ranked["candidate_index"]] = ranked["score"]
            with np.load(
                W / f"results/task-e/e27-038-integrated-development/predictions/{HANDLE}-{row['relative_endpoint']}.npz",
                allow_pickle=False,
            ) as expected_integrated:
                np.testing.assert_array_equal(scores, expected_integrated["scores"])
            exact_integrated.append(row)
        if not all(validate_packet(packet) for packet in integrated_result["trigger_packets"]):
            raise AssertionError("Integrated trigger packet validation failed")
        serialized = canonical({
            "c1": c1_result["packet"],
            "c5": c5_result["packet"],
            "integrated": integrated_result["trigger_packets"],
        })
        lowered = serialized.lower()
        forbidden_tokens = (
            b"root_cause", b"fault_label", b"inject_time", b"event_ms",
            b"first_seen_ms", b"first_conflict_ms", b"case_path",
        )
        if any(token in lowered for token in forbidden_tokens):
            raise AssertionError("Oracle/controller-only metadata leaked into public-loader packets")
        receipt.update(
            {
                "status": "PASS",
                "case_selection": "predeclared first registry smoke identity; not score-selected",
                "opaque_handle": HANDLE,
                "source_relationship": contract["source_relationship"],
                "raw_source_hashes": raw_hashes,
                "C1": {
                    "numeric_bundle": "EXACT_MATCH_TO_SEALED_E",
                    "L_O": "EXACT_MATCH_TO_SEALED_E",
                    "packet_sha256": c1_result["packet"]["packet_sha256"],
                },
                "C5_G_MTL": {
                    "numeric_bundle": "EXACT_MATCH_TO_SEALED_E",
                    "predictions_residuals_scores": "EXACT_MATCH_TO_SEALED_E",
                    "packet_sha256": c5_result["packet"]["packet_sha256"],
                },
                "C5_L_MTL_INTEGRATED": {
                    "sealed_equivalence_endpoints": [630, 1125],
                    "integrated_scores": "EXACT_MATCH_TO_SEALED_E",
                    "frozen_full_threshold_trigger_endpoints": [
                        row["relative_endpoint"] for row in integrated_result["integrated_diagnoses"]
                    ],
                    "trigger_packets": "VALID_AND_CONTROLLER_CLOCK_FIREWALL_PASS",
                },
                "qualified_loader_boundary": "PASS; adapter binds exact Task E execution bytes and receipts before admission",
            }
        )
        exit_code = 0
    except Exception as exc:
        receipt["failures"].append(
            {"failure_type": type(exc).__name__, "traceback": traceback.format_exc()}
        )
    receipt["wall_seconds"] = time.perf_counter() - started
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "report_sha256": sha(report_path)}))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("prepare", "run"), required=True)
    parser.add_argument("--run-dir", required=True)
    arguments = parser.parse_args()
    run_dir = Path(arguments.run_dir).resolve()
    try:
        run_dir.relative_to((W / "results/task-f").resolve())
    except ValueError as exc:
        raise SystemExit("Task F run directory must stay under results/task-f") from exc
    return prepare(run_dir) if arguments.mode == "prepare" else run(run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
