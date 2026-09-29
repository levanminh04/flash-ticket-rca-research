"""Validate the frozen Task F core against sealed development30 outputs.

This is implementation validation, not selection or efficacy evaluation.  It
uses one frozen configuration on all 30 development cases, plus the
predeclared first smoke identity for every major mode and R-control replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path
from types import MappingProxyType

import numpy as np

from rca import FrozenRcaPipeline
from rca.cache import cache_identity, read_numeric_cache, write_numeric_cache
from rca.observation import C1Observation, C5Observation
from rca.packet import validate_packet


W = Path(__file__).resolve().parents[2]
P = Path(r"D:\Project\flash-ticket-platform")
MANIFEST = W / "configs/task-f-td13-frozen-release.json"
AUDITS = W / "results/task-e/e27-019-development-loader-audit/case-audits"
C1 = W / "results/task-e/e27-033-c1-development-full"
C5 = W / "results/task-e/e27-035-c5-development-full"


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


def plain(value):
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def resolve_contract_path(label: str) -> Path:
    if label.startswith("P/"):
        return P / label[2:]
    return W / label


def verify_contract(path: Path) -> dict:
    contract = load_json(path)
    supplied = contract.pop("contract_sha256")
    expected = hashlib.sha256(canonical(contract)).hexdigest()
    contract["contract_sha256"] = supplied
    if supplied != expected:
        raise RuntimeError("Task F validation contract digest mismatch")
    if contract.get("status") != "PLANNED" or len(contract.get("development_allowlist", [])) != 30:
        raise RuntimeError("Task F validation contract is not a planned development30 run")
    if any("final60" in row["path"].lower() for group in ("source_files", "input_files") for row in contract[group]):
        raise RuntimeError("Final60 path is forbidden in Task F validation contract")
    for group in ("source_files", "input_files"):
        for row in contract[group]:
            file_path = resolve_contract_path(row["path"])
            if not file_path.is_file() or sha(file_path) != row["sha256"]:
                raise RuntimeError(f"Declared {group} identity drift: {row['path']}")
    return contract


def array_hashes(**arrays) -> dict[str, str]:
    result = {}
    for name, value in arrays.items():
        contiguous = np.ascontiguousarray(np.asarray(value))
        material = contiguous.dtype.str.encode() + canonical(list(contiguous.shape)) + contiguous.tobytes()
        result[name] = hashlib.sha256(material).hexdigest()
    return result


def exact(actual, expected, label: str) -> None:
    try:
        np.testing.assert_array_equal(actual, expected)
    except AssertionError as exc:
        raise AssertionError(f"Exact E/F mismatch for {label}") from exc


def code_identity(contract: dict) -> dict[str, str]:
    return {
        row["path"]: row["sha256"]
        for row in contract["source_files"]
        if row["role"] == "task-f-release-source"
    }


def case_controller(case: str, handle: str) -> tuple[dict, tuple[str, ...], tuple[str, ...], str]:
    path = AUDITS / f"{handle}.json"
    audit = load_json(path)
    if audit.get("case") != case or audit.get("handle") != handle:
        raise RuntimeError("Controller case/opaque-handle mapping mismatch")
    c1_profile = audit["profiles"]["c1_primary"]
    c5_profile = audit["profiles"]["c5_primary"]
    return (
        {
            "loader_status": audit.get("status"),
            "c1_profile_status": c1_profile.get("status"),
            "c5_profile_status": c5_profile.get("status"),
        },
        tuple(c1_profile["service_names"]),
        tuple(c5_profile["service_names"]),
        sha(path),
    )


def c1_observation(case: str, handle: str) -> tuple[C1Observation, Path]:
    quality, c1_nodes, _, audit_sha = case_controller(case, handle)
    path = W / f"results/task-e/e27-019-development-loader-audit/intermediates/{handle}/c1_primary.npz"
    with np.load(path, allow_pickle=False) as stored:
        observation = C1Observation(
            handle=handle,
            ref=stored["ref"],
            query=stored["query"],
            channel_types=tuple(stored["channel_types"]),
            adjacency=stored["adj"],
            node_ids=c1_nodes,
            source_hashes=MappingProxyType({"numeric": sha(path), "case_audit": audit_sha}),
            graph_provenance=MappingProxyType(
                {"reference_only": True, "case_audit_sha256": audit_sha}
            ),
            quality=MappingProxyType(quality),
            evidence_catalog=MappingProxyType({}),
        )
    return observation, path


def c5_observation(case: str, handle: str) -> tuple[C5Observation, Path]:
    quality, _, c5_nodes, audit_sha = case_controller(case, handle)
    path = C5 / "predictions/primary" / handle / "numeric-input.npz"
    with np.load(path, allow_pickle=False) as stored:
        values = stored["values"].copy()
        observation = C5Observation(
            handle=handle,
            warmup_values=values[:36],
            stream_values=values[36:],
            channel_types=tuple(stored["channel_types"]),
            adjacency=stored["adj"],
            fit_service_mask=stored["fit_service_mask"],
            node_ids=c5_nodes,
            relative_endpoints=stored["endpoints"][36:],
            source_hashes=MappingProxyType({"numeric": sha(path), "case_audit": audit_sha}),
            graph_provenance=MappingProxyType(
                {"fit_graph_frozen": True, "case_audit_sha256": audit_sha}
            ),
            quality=MappingProxyType(quality),
            evidence_catalog=MappingProxyType({}),
        )
    return observation, path


def selected_indices() -> tuple[int, int, int, int]:
    selection = load_json(C1 / "selection.json")
    local_index = int(selection["selected_local_index"])
    ppr_index = int(selection["selected_ppr_index"])
    diffusion_index = int(selection["selected_diffusion_index"])
    plan = load_json(C1 / "observed-execution-plan.json")
    undirected = [row for row in plan["rank_configs"] if row["direction"] == "undirected"]
    r_index = next(
        index
        for index, row in enumerate(undirected)
        if row["operator"] == "ppr" and row["damping"] == 0.5
    )
    return local_index, ppr_index, diffusion_index, r_index


def c5_config_index(handle: str, arm: str, modalities: str) -> int:
    start = load_json(C5 / "predictions/primary" / handle / "start.json")
    return next(
        index
        for index, row in enumerate(start["configs"])
        if row["arm"] == arm
        and row["modalities"] == modalities
        and float(row["lambda"]) == 10.0
    )


def validate_c1(core, case: str, handle: str, indices) -> tuple[dict, dict, C1Observation]:
    started = time.perf_counter()
    observation, input_path = c1_observation(case, handle)
    result = core.run_c1(observation, include_structural_control=False)
    if result["status"] != "SUCCESS" or not validate_packet(result["packet"]):
        raise RuntimeError("Task F C1 did not return a valid successful packet")
    local_index, ppr_index, diffusion_index, _ = indices
    prediction_dir = C1 / "predictions"
    with np.load(prediction_dir / f"{handle}.npz", allow_pickle=False) as expected:
        exact(result["L_scores"], expected["local"][local_index], "C1 local")
    with np.load(prediction_dir / f"{handle}-observed-local{local_index}.npz", allow_pickle=False) as expected:
        exact(result["O"]["scores"], expected["scores"][ppr_index], "C1 observed PPR")
        exact(result["secondary"]["scores"], expected["scores"][diffusion_index], "C1 secondary diffusion")
    with np.load(prediction_dir / f"{handle}-comparators.npz", allow_pickle=False) as expected:
        exact(result["comparators"]["Local-MAX-MT"]["scores"], expected["local_max_mt"], "Local-MAX-MT")
        exact(result["comparators"]["BARO-RANK-adapted-TD12"]["scores"], expected["baro"], "BARO adapted")
    hashes = array_hashes(
        L=result["L_scores"],
        O=result["O"]["scores"],
        diffusion=result["secondary"]["scores"],
        local_max=result["comparators"]["Local-MAX-MT"]["scores"],
        baro=result["comparators"]["BARO-RANK-adapted-TD12"]["scores"],
    )
    record = {
        "status": "EXACT_MATCH",
        "input_sha256": sha(input_path),
        "output_hashes": hashes,
        "packet_sha256": result["packet"]["packet_sha256"],
        "seconds": time.perf_counter() - started,
    }
    return record, result, observation


def validate_c5(core, case: str, handle: str, detector_id: str = "G-MTL") -> tuple[dict, dict, C5Observation]:
    started = time.perf_counter()
    observation, input_path = c5_observation(case, handle)
    result = core.run_c5(observation, detector_id)
    if result["status"] != "SUCCESS" or not validate_packet(result["packet"]):
        raise RuntimeError("Task F C5 did not return a valid successful packet")
    arm, modalities = detector_id.split("-", 1)
    source_arm = "G" if arm == "TV" else arm
    index = c5_config_index(handle, source_arm, modalities)
    prediction_path = C5 / "predictions/primary" / handle / "predictions.npz"
    with np.load(prediction_path, allow_pickle=False) as expected:
        if arm == "TV":
            scores = np.array([row["tv_score"] for row in result["bins"]])
            exact(scores, expected["tv_scores"][index], f"C5 {detector_id} TV scores")
            hashes = array_hashes(scores=scores)
        else:
            predictions = np.stack([row["predictions"] for row in result["bins"]])
            errors = np.stack([row["errors"] for row in result["bins"]])
            residuals = np.stack([row["residuals"] for row in result["bins"]])
            masks = np.stack([row["target_mask"] for row in result["bins"]])
            scores = np.array([row["score"] for row in result["bins"]])
            exact(predictions, expected["predictions"][index], f"C5 {detector_id} predictions")
            exact(errors, expected["errors"][index], f"C5 {detector_id} errors")
            exact(residuals, expected["residuals"][index], f"C5 {detector_id} residuals")
            exact(masks, expected["target_mask"][index], f"C5 {detector_id} masks")
            exact(scores, expected["scores"][index], f"C5 {detector_id} scores")
            hashes = array_hashes(
                predictions=predictions,
                errors=errors,
                residuals=residuals,
                masks=masks,
                scores=scores,
            )
    for packet in result["trigger_packets"]:
        validate_packet(packet)
    record = {
        "status": "EXACT_MATCH",
        "detector_id": detector_id,
        "sealed_config_index": index,
        "input_sha256": sha(input_path),
        "output_hashes": hashes,
        "packet_sha256": result["packet"]["packet_sha256"],
        "trigger_packet_count": len(result["trigger_packets"]),
        "seconds": time.perf_counter() - started,
    }
    return record, result, observation


def write_packet(path: Path, packet: dict) -> dict[str, object]:
    validate_packet(packet)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(packet, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    return {"path": path.relative_to(W).as_posix(), "sha256": sha(path), "bytes": path.stat().st_size}


def cache_canary(core, run_dir: Path, c1_obs: C1Observation, c1_result: dict, c5_obs: C5Observation, c5_result: dict) -> dict:
    cache_dir = run_dir / "cache"
    code_hashes = code_identity(verify_contract(run_dir / "run-contract.json"))
    c1_identity = cache_identity(
        source_hashes=c1_obs.source_hashes,
        td_hash=core.config.td_sha256,
        code_hashes=code_hashes,
        config=plain(core.config.manifest["selections"]["c1"]),
        profile="c1-primary",
        cutoff=[300, 600],
    )
    c1_arrays = {
        "ref": c1_obs.ref,
        "query": c1_obs.query,
        "adj": c1_obs.adjacency.astype(np.uint8),
        "channel_types": np.asarray(c1_obs.channel_types, dtype=np.int64),
    }
    c1_write = write_numeric_cache(cache_dir, c1_identity, c1_arrays)
    c1_restored = read_numeric_cache(cache_dir, c1_identity)
    for key in c1_arrays:
        exact(c1_restored[key], c1_arrays[key], f"C1 cache {key}")
    c1_cached_obs = C1Observation(
        c1_obs.handle,
        c1_restored["ref"],
        c1_restored["query"],
        tuple(c1_restored["channel_types"]),
        c1_restored["adj"].astype(bool),
        c1_obs.node_ids,
        c1_obs.source_hashes,
        c1_obs.graph_provenance,
        c1_obs.quality,
        c1_obs.evidence_catalog,
    )
    c1_cached_result = core.run_c1(c1_cached_obs, include_structural_control=False)
    exact(c1_cached_result["L_scores"], c1_result["L_scores"], "C1 raw/cache L")
    exact(c1_cached_result["O"]["scores"], c1_result["O"]["scores"], "C1 raw/cache O")
    if c1_cached_result["packet"]["packet_sha256"] != c1_result["packet"]["packet_sha256"]:
        raise AssertionError("C1 raw/cache packet identity mismatch")

    c5_identity = cache_identity(
        source_hashes=c5_obs.source_hashes,
        td_hash=core.config.td_sha256,
        code_hashes=code_hashes,
        config=plain(core.config.manifest["selections"]["c5"]),
        profile="c5-primary",
        cutoff=1440,
    )
    c5_arrays = {
        "values": np.concatenate((c5_obs.warmup_values, c5_obs.stream_values)),
        "adj": c5_obs.adjacency.astype(np.uint8),
        "fit_service_mask": c5_obs.fit_service_mask,
        "channel_types": np.asarray(c5_obs.channel_types, dtype=np.int64),
        "endpoints": np.concatenate(
            (
                np.arange(1, len(c5_obs.warmup_values) + 1, dtype=np.int64) * 5,
                c5_obs.relative_endpoints,
            )
        ),
    }
    c5_write = write_numeric_cache(cache_dir, c5_identity, c5_arrays)
    c5_restored = read_numeric_cache(cache_dir, c5_identity)
    for key in c5_arrays:
        exact(c5_restored[key], c5_arrays[key], f"C5 cache {key}")
    c5_cached_obs = C5Observation(
        c5_obs.handle,
        c5_restored["values"][:36],
        c5_restored["values"][36:],
        tuple(c5_restored["channel_types"]),
        c5_restored["adj"].astype(bool),
        c5_restored["fit_service_mask"],
        c5_obs.node_ids,
        c5_restored["endpoints"][36:],
        c5_obs.source_hashes,
        c5_obs.graph_provenance,
        c5_obs.quality,
        c5_obs.evidence_catalog,
    )
    c5_cached_result = core.run_c5(c5_cached_obs, "G-MTL")
    exact(
        np.array([row["score"] for row in c5_cached_result["bins"]]),
        np.array([row["score"] for row in c5_result["bins"]]),
        "C5 raw/cache scores",
    )
    if c5_cached_result["packet"]["packet_sha256"] != c5_result["packet"]["packet_sha256"]:
        raise AssertionError("C5 raw/cache packet identity mismatch")

    records = {}
    for label, identity, written in (
        ("c1", c1_identity, c1_write),
        ("c5", c5_identity, c5_write),
    ):
        data_path = Path(written["data_path"])
        manifest_path = Path(written["manifest_path"])
        records[label] = {
            "identity_key": identity["key"],
            "data_sha256": sha(data_path),
            "manifest_sha256": sha(manifest_path),
            "reused": written["reused"],
        }
    return {"status": "EXACT_RAW_CACHE_MATCH", "entries": records}


def process_resources(started_wall: float, started_cpu: float) -> dict[str, object]:
    result: dict[str, object] = {
        "wall_seconds": time.perf_counter() - started_wall,
        "process_cpu_seconds": time.process_time() - started_cpu,
        "logical_cpu_count": os.cpu_count(),
    }
    try:
        import psutil

        memory = psutil.Process().memory_info()
        result["rss_bytes_at_receipt"] = memory.rss
        result["vms_bytes_at_receipt"] = memory.vms
    except (ImportError, OSError):
        result["memory_measurement"] = "UNAVAILABLE"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    arguments = parser.parse_args()
    run_dir = Path(arguments.run_dir).resolve()
    try:
        run_dir.relative_to((W / "results/task-f").resolve())
    except ValueError as exc:
        raise SystemExit("Task F run directory must stay under results/task-f") from exc
    report_path = run_dir / "development-validation.json"
    if report_path.exists():
        raise SystemExit("Never overwrite an existing Task F validation attempt")
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    contract = verify_contract(run_dir / "run-contract.json")
    core = FrozenRcaPipeline.from_manifest(
        MANIFEST,
        code_identity=code_identity(contract),
        release_id="TASK-F-TD13-v1",
    )
    indices = selected_indices()
    cases: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    retained: dict[str, tuple] = {}

    for case in contract["development_allowlist"]:
        handle = contract["opaque_handles_by_development_id"][case]
        row: dict[str, object] = {"development_id": case, "opaque_handle": handle}
        try:
            c1_record, c1_result, c1_obs = validate_c1(core, case, handle, indices)
            row["C1"] = c1_record
            c5_record, c5_result, c5_obs = validate_c5(core, case, handle)
            row["C5_G_MTL"] = c5_record
            row["status"] = "EXACT_MATCH"
            if case == contract["predetermined_major_mode_smoke"]:
                retained[case] = (c1_result, c1_obs, c5_result, c5_obs)
        except Exception as exc:
            row["status"] = "FAILURE"
            row["failure_type"] = type(exc).__name__
            failures.append(
                {
                    "development_id": case,
                    "opaque_handle": handle,
                    "failure_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                }
            )
        cases.append(row)

    major_modes: list[dict[str, object]] = []
    r_control: dict[str, object] = {"status": "NOT_RUN"}
    cache_result: dict[str, object] = {"status": "NOT_RUN"}
    reproducibility: dict[str, object] = {"status": "NOT_RUN"}
    packet_artifacts: list[dict[str, object]] = []
    smoke_case = contract["predetermined_major_mode_smoke"]
    if smoke_case in retained:
        c1_result, c1_obs, c5_result, c5_obs = retained[smoke_case]
        smoke_handle = c1_obs.handle
        try:
            for detector_id in (
                "G-MTL",
                "G-MT",
                "L-MTL",
                "L-MT",
                "ALL-MTL",
                "ALL-MT",
                "TV-MTL",
                "TV-MT",
            ):
                record, _, _ = validate_c5(core, smoke_case, smoke_handle, detector_id)
                major_modes.append(record)

            structural = core.run_c1(c1_obs, include_structural_control=True)
            if structural["status"] != "SUCCESS":
                raise RuntimeError("C1 structural control failed")
            _, _, _, r_index = indices
            with np.load(C1 / "predictions" / f"{smoke_handle}-R-undirected.npz", allow_pickle=False) as expected:
                exact(structural["R_scores"], expected["scores"][:, r_index], "C1 all 256 selected R draws")
            rejection_totals: dict[str, int] = {}
            for draw in structural["R"]["per_draw"]:
                for reason, count in draw["rejections"].items():
                    rejection_totals[reason] = rejection_totals.get(reason, 0) + int(count)
            r_control = {
                "status": "EXACT_MATCH",
                "opaque_handle": smoke_handle,
                "draws": structural["R"]["summary"]["planned"],
                "proposals_per_draw": structural["R"]["summary"]["proposals_per_draw"],
                "proposal_attempts": sum(int(draw["proposals"]) for draw in structural["R"]["per_draw"]),
                "accepted": sum(int(draw["accepted"]) for draw in structural["R"]["per_draw"]),
                "rejections": rejection_totals,
                "scores_sha256": array_hashes(scores=structural["R_scores"])["scores"],
                "interpretation": "registered finite perturbation mobility only; not a mixing/spectrum/path/kernel/centrality proof",
            }

            repeated_c1 = core.run_c1(c1_obs, include_structural_control=False)
            repeated_c5 = core.run_c5(c5_obs, "G-MTL")
            reproducibility = {
                "status": "EXACT_REPEAT",
                "C1_packet_sha256": repeated_c1["packet"]["packet_sha256"],
                "C5_packet_sha256": repeated_c5["packet"]["packet_sha256"],
            }
            if repeated_c1["packet"]["packet_sha256"] != c1_result["packet"]["packet_sha256"]:
                raise AssertionError("C1 repeated packet differs")
            if repeated_c5["packet"]["packet_sha256"] != c5_result["packet"]["packet_sha256"]:
                raise AssertionError("C5 repeated packet differs")
            cache_result = cache_canary(core, run_dir, c1_obs, c1_result, c5_obs, c5_result)
            packet_artifacts.append(
                write_packet(run_dir / "packets" / f"{smoke_handle}-c1.json", structural["packet"])
            )
            representative_c5 = (
                c5_result["trigger_packets"][0]
                if c5_result["trigger_packets"]
                else c5_result["packet"]
            )
            packet_artifacts.append(
                write_packet(
                    run_dir / "packets" / f"{smoke_handle}-c5-G-MTL.json",
                    representative_c5,
                )
            )
        except Exception as exc:
            failures.append(
                {
                    "development_id": smoke_case,
                    "opaque_handle": contract["opaque_handles_by_development_id"][smoke_case],
                    "failure_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                }
            )

    report = {
        "schema": "TD13-TASK-F-DEVELOPMENT-VALIDATION-v1",
        "run_id": contract["run_id"],
        "scope": contract["scope"],
        "contract_sha256": contract["contract_sha256"],
        "td_sha256": contract["td_sha256"],
        "frozen_manifest": contract["frozen_manifest"],
        "release_code_identity": code_identity(contract),
        "development_allowlist_sha256": contract["development_allowlist_sha256"],
        "planned_cases": 30,
        "completed_cases": sum(row.get("status") == "EXACT_MATCH" for row in cases),
        "cases": cases,
        "major_mode_smoke": {
            "predeclared_case": smoke_case,
            "results": major_modes,
        },
        "r_control": r_control,
        "raw_cache_equivalence": cache_result,
        "repeat_reproducibility": reproducibility,
        "packet_artifacts": packet_artifacts,
        "failures": failures,
        "failure_policy": "all 30 planned cases retained; no silent skip or healthy-zero substitution",
        "firewall": {
            "final60_opened": False,
            "ground_truth_passed_to_core": False,
            "packet_oracle_fields": False,
            "validation_inputs": "registered development30 sealed numeric artifacts only",
        },
        "resources": process_resources(started_wall, started_cpu),
        "status": "PASS" if not failures and len(cases) == 30 else "FAIL",
    }
    with report_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "completed_cases": report["completed_cases"],
                "failures": len(failures),
                "report_sha256": sha(report_path),
                "seconds": report["resources"]["wall_seconds"],
            }
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
