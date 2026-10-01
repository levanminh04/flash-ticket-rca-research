"""G32 bounded readiness computation and scientific reporting.

The final campaign is deliberately unavailable in this readiness domain.
Numeric workers accept detached arrays, relative endpoints and internal routing
indices. Actual final telemetry is conversion-only in final_source. The frozen
F mathematical functions, selections and failure semantics are unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import weakref
from contextlib import contextmanager

WORKSPACE = Path(__file__).resolve().parents[2]
PROJECT = Path("D:/Project/flash-ticket-platform")
for root in (WORKSPACE, WORKSPACE / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
if __name__ == "__main__":
    sys.modules["scripts.task_g.final_campaign"] = sys.modules[__name__]

from scripts.task_g import campaign as previous

RUN_ID = "g32-final-bridge-readiness"
DOMAIN = "FlashTicketRca/TD13/G32/BRIDGE-READINESS/v1"
PHASE = "FINAL_BRIDGE_READINESS_ONLY"
CONTRACT = WORKSPACE / "results/task-g" / RUN_ID / "run-contract.json"
MANIFEST = previous.MANIFEST
THREADS = previous.THREADS
DETECTORS = previous.DETECTORS
_pack, _unpack = previous._pack, previous._unpack
_canonical, _digest = previous._canonical, previous._digest


class FinalCampaignError(ValueError):
    """Sanitized G32 boundary failure."""


class ReadinessExecution:
    __slots__ = ("__weakref__",)


def _context():
    from scripts.task_g.final_provenance import registered_context
    return registered_context()


def _scientific_plain(value):
    """Lossless numeric arrays include NaN availability in a finite JSON wire."""
    import numpy as np
    from collections.abc import Mapping
    if isinstance(value, np.ndarray):
        if value.dtype.kind in "biuf":
            return _pack(value)
        return _scientific_plain(value.tolist())
    if isinstance(value, np.generic):
        return _scientific_plain(value.item())
    if isinstance(value, Mapping):
        return {str(key): _scientific_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_scientific_plain(item) for item in value]
    if type(value) is float and not math.isfinite(value):
        if math.isinf(value):
            raise FinalCampaignError("NONFINITE_SCIENTIFIC_INFINITY")
        return None
    return copy.deepcopy(value)


def _emit(value):
    sys.stdout.buffer.write(_canonical(value) + b"\n")
    sys.stdout.buffer.flush()


def _worker_guard():
    _context()
    if any(os.environ.get(key) != val for key, val in THREADS.items()):
        raise FinalCampaignError("NUMERIC_THREAD_POLICY_DRIFT")


def _graph_diagnostics(adjacency, config):
    import numpy as np
    from rca.ranking import rank_scores, _graph_hash
    adjacency = np.asarray(adjacency, dtype=bool)
    n = len(adjacency)
    reachable = adjacency.copy() | np.eye(n, dtype=bool)
    for pivot in range(n):
        reachable |= reachable[:, pivot, None] & reachable[None, pivot, :]
    uniform = {}
    for name, selected in (("primary", config.primary_ppr), ("secondary", config.secondary_diffusion)):
        try:
            rank = rank_scores(np.ones(n), adjacency, operator=selected.operator,
                               direction=selected.direction, damping=selected.damping)
            uniform[name] = {"status": "SUCCESS", **_scientific_plain(rank)}
        except Exception as exc:
            uniform[name] = {"status": "FAILURE", "reason": type(exc).__name__}
    return {"observed_adjacency": _pack(adjacency), "graph_sha256": _graph_hash(adjacency),
            "degrees": {"in": _pack(adjacency.sum(axis=0)), "out": _pack(adjacency.sum(axis=1)),
                        "undirected": _pack((adjacency | adjacency.T).sum(axis=1))},
            "reachability": _pack(reachable), "uniform_personalization": uniform}


def _numeric_c1_worker(wire):
    import numpy as np
    from rca.contracts import load_frozen_config
    from rca.ranking import local_scores, perturb_graphs, rank_scores
    from rca.comparators import local_max_scores, baro_scores
    _worker_guard()
    if set(wire) != {"mode", "ref", "query", "adj", "channel_types", "routing_handle"}:
        raise FinalCampaignError("C1_WORKER_WIRE_SCHEMA_DRIFT")
    if wire["mode"] not in ("C1", "INTEGRATED"):
        raise FinalCampaignError("C1_WORKER_MODE_INVALID")
    route = wire["routing_handle"]
    if type(route) is not str or len(route) != 16 or any(ch not in "0123456789abcdef" for ch in route):
        raise FinalCampaignError("INTERNAL_ROUTING_INDEX_INVALID")
    ref, query, adj, types = (_unpack(wire[key]) for key in ("ref", "query", "adj", "channel_types"))
    config = load_frozen_config(MANIFEST)
    started = time.perf_counter()
    local_config = dict(config.local)
    if wire["mode"] == "INTEGRATED":
        local_config["include_logs"] = True
    evidence = local_scores(ref, query, types, local_config)
    shared = time.perf_counter() - started
    # Preserve even failed numeric-channel diagnostics; finite zero is not success.
    scientific = {"input": {key: wire[key] for key in ("ref", "query", "adj", "channel_types")},
                  "evidence": _scientific_plain(evidence), **_graph_diagnostics(adj, config), "ranking": {}}
    if np.asarray(evidence["diagnostics"]["numerical_channel_failures"]).any():
        _emit({"kind": "scientific_failure", "reason": "SHARED_PREPROCESSING_NUMERICAL_FAILURE",
               "scientific_diagnostics": scientific, "shared_preprocessing_seconds": shared})
        return
    local = evidence["local"]
    operators = {"primary": config.primary_ppr, "secondary": config.secondary_diffusion}
    header = {"kind": "header", "local_evidence": local.tolist(), "c1": {}, "contextual": {},
              "scientific_diagnostics": scientific,
              "costs": {"shared_preprocessing_seconds": shared, "rank_seconds": {}, "control_generation_seconds": None}}
    for name, selected in operators.items():
        header["c1"][name] = {}; header["costs"]["rank_seconds"][name] = {}; scientific["ranking"][name] = {}
        for arm, graph in (("L", np.zeros_like(adj)), ("O", adj)):
            then = time.perf_counter()
            try:
                result = rank_scores(local, graph, operator=selected.operator,
                                     direction=selected.direction, damping=selected.damping)
                header["c1"][name][arm] = {"status": "SUCCESS", "scores": result["scores"].tolist()}
                scientific["ranking"][name][arm] = _scientific_plain(result)
            except Exception as exc:
                header["c1"][name][arm] = {"status": "FAILURE", "scores": None, "reason": type(exc).__name__}
                scientific["ranking"][name][arm] = {"status": "FAILURE", "reason": type(exc).__name__}
            header["costs"]["rank_seconds"][name][arm] = time.perf_counter() - then
    if wire["mode"] == "INTEGRATED":
        _emit({"kind": "integrated", **header["c1"]["primary"]["O"], "local_evidence": local.tolist(),
               "scientific_diagnostics": scientific, "costs": header["costs"]})
        return
    for method, callable_ in (("Local-MAX-MT", lambda: local_max_scores(evidence["blocks"], evidence["masks"]["blocks"])),
                              ("BARO-RANK-adapted-TD12", lambda: baro_scores(ref, query, types))):
        try:
            result = callable_()
            if "diagnostics" in result and np.asarray(result["diagnostics"]["numerical_channel_failures"]).any():
                raise FinalCampaignError("COMPARATOR_NUMERICAL_FAILURE")
            header["contextual"][method] = {"status": "SUCCESS", "scores": result["scores"].tolist()}
            scientific.setdefault("contextual", {})[method] = _scientific_plain(result)
        except Exception as exc:
            header["contextual"][method] = {"status": "FAILURE", "scores": None, "reason": type(exc).__name__}
    _emit(header)
    then = time.perf_counter()
    controls = perturb_graphs(adj, route, "undirected", count=256, budget=200)
    generation = time.perf_counter() - then
    totals = {name: 0.0 for name in operators}
    for draw, (graph, receipt) in enumerate(zip(controls["graphs"], controls["per_draw"], strict=True)):
        row = {"kind": "draw", "draw": draw, "graph": {**receipt, "status": "SUCCESS",
               "adjacency": graph.astype(int).tolist(), "graph_sha256": receipt["hash"]}, "rankers": {}}
        for name, selected in operators.items():
            then = time.perf_counter()
            try:
                result = rank_scores(local, graph, operator=selected.operator, direction=selected.direction, damping=selected.damping)
                rank = {"status": "SUCCESS", "scores": result["scores"].tolist(), "operator_diagnostics": _scientific_plain(result)}
            except Exception as exc:
                rank = {"status": "FAILURE", "scores": None, "reason": type(exc).__name__}
            totals[name] += time.perf_counter() - then
            row["rankers"][name] = {**rank, "draw": draw, "seed": receipt["seed"],
                                    "graph_sha256": receipt["hash"], "retained_edge_fraction": receipt["retained_edge_fraction"]}
        _emit(row)
    _emit({"kind": "done", "control_generation_seconds": generation, "R_rank_seconds": totals,
           "worker_numeric_seconds": time.perf_counter() - started, "control_summary": _scientific_plain(controls["summary"])})


def _numeric_c5_worker(wire):
    import numpy as np
    from rca.contracts import load_frozen_config
    from rca.detection import fit_detector, score_bin, create_event_state, event_step
    _worker_guard()
    expected_keys = {"warmup", "stream", "adj", "channel_types", "fit_mask", "endpoints"}
    if set(wire) != expected_keys:
        raise FinalCampaignError("C5_WORKER_WIRE_SCHEMA_DRIFT")
    warmup, stream, adj, types, fitmask, endpoints = (_unpack(wire[key]) for key in ("warmup", "stream", "adj", "channel_types", "fit_mask", "endpoints"))
    config = load_frozen_config(MANIFEST)
    profile = config.manifest["selections"]["c5"]["profile"]
    if not np.array_equal(endpoints, np.arange(len(warmup)+1, len(warmup)+len(stream)+1) * profile["bin_seconds"]):
        raise FinalCampaignError("C5_RELATIVE_ENDPOINT_GRID_DRIFT")
    for detector in DETECTORS:
        selected = config.detector(detector)
        cfg = {"arm": "G" if selected.arm == "TV" else selected.arm, "modalities": selected.modalities,
               "lambda": config.selected_lambda, "floor": profile["input_relative_floor"],
               "residual_floor": profile["residual_floor"], "lag": profile["lag"], "bin_seconds": profile["bin_seconds"],
               "fit_bins": profile["fit_bins"], "cal_bins": profile["calibration_bins"],
               "min_fit_rows": profile["min_fit_rows"], "min_cal_rows": profile["min_calibration_rows"]}
        rows = []; state = initial_state = None; fit_seconds = prediction_seconds = None
        fit_started = prediction_started = None
        started = time.perf_counter()
        try:
            then = fit_started = time.perf_counter()
            state = fit_detector(warmup, adj, types, fitmask, cfg)
            fit_seconds = time.perf_counter() - then
            event = create_event_state(selected.threshold, bin_seconds=profile["bin_seconds"],
                                       streak=profile["event_streak"], refractory_seconds=profile["refractory_seconds"])
            initial_state = _scientific_plain(state)
            then = prediction_started = time.perf_counter()
            for values, endpoint in zip(stream, endpoints, strict=True):
                result = score_bin(state, values)
                if result["endpoint"] != int(endpoint):
                    raise FinalCampaignError("C5_ENDPOINT_DRIFT")
                score = result["tv_score"] if selected.arm == "TV" else result["score"]
                result["selected_system_score"] = score
                result["event"] = event_step(event, score, int(endpoint))
                rows.append(_scientific_plain(result))
            prediction_seconds = time.perf_counter() - then
            status, reason = "SUCCESS", None
        except Exception as exc:
            status, reason = "FAILURE", type(exc).__name__
            if fit_seconds is None and fit_started is not None:
                fit_seconds = time.perf_counter() - fit_started
            if prediction_seconds is None and prediction_started is not None:
                prediction_seconds = time.perf_counter() - prediction_started
        _emit({"kind": "c5", "detector": detector, "status": status, "reason": reason,
               "threshold": selected.threshold, "state": initial_state, "bins": rows,
               "input": wire, "fit_seconds": fit_seconds, "prediction_seconds": prediction_seconds,
               "wall_seconds": time.perf_counter() - started})


def _run_worker(mode, wire, deadline):
    if mode == "rcd":
        return previous._run_worker(mode, wire, deadline)
    environment = {**os.environ, **THREADS, "PYTHONPATH": str(WORKSPACE / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    started = time.perf_counter()
    process = subprocess.Popen([str(WORKSPACE / ".venv/Scripts/python.exe"), "-B", str(Path(__file__).resolve()), "--numeric-worker", mode],
        cwd=WORKSPACE, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        output, errors = process.communicate(_canonical(wire), timeout=deadline)
    except subprocess.TimeoutExpired:
        timed_out = True; process.kill(); output, errors = process.communicate()
    rows = []
    if len(output) <= 128 * 1024 * 1024:
        for line in output.splitlines():
            try:
                rows.append(json.loads(line))
            except (json.JSONDecodeError, UnicodeDecodeError):
                break
    else:
        rows = [{"kind": "worker_failure", "reason": "BOUNDED_OUTPUT_SIZE_EXCEEDED"}]
    return {"rows": rows, "exit_code": process.returncode, "timed_out": timed_out,
            "wall_seconds": time.perf_counter() - started, "stderr_sha256": hashlib.sha256(errors).hexdigest(), "stderr_bytes": len(errors)}


def _c5_wire(observation):
    return {"warmup": _pack(observation.warmup_values), "stream": _pack(observation.stream_values),
            "adj": _pack(observation.adjacency), "channel_types": _pack(observation.channel_types),
            "fit_mask": _pack(observation.fit_service_mask), "endpoints": _pack(observation.relative_endpoints)}


def _assemble_c1(case, worker):
    row = previous._assemble_c1(case, worker)
    header = next((item for item in worker["rows"] if item.get("kind") == "header"), None)
    failure = next((item for item in worker["rows"] if item.get("kind") == "scientific_failure"), None)
    diagnostics = header["scientific_diagnostics"] if header else failure["scientific_diagnostics"] if failure else {
        "status": "UNAVAILABLE_WORKER_FAILURE", "input": previous._c1_wire(case["c1"]),
        "evidence": None, "observed_adjacency": _pack(case["c1"].adjacency),
        "graph_sha256": _graph_diagnostics(case["c1"].adjacency, _frozen_config())["graph_sha256"],
        "degrees": None, "reachability": None, "uniform_personalization": None, "ranking": None}
    row["scientific_diagnostics"] = {"c1": diagnostics, "c5": {},
        "quality": _scientific_plain(case.get("quality") or dict(case["c1"].quality) or
                                     {"source_metadata": case.get("source_metadata", {})}),
        "controller_bindings": {"candidate_ids": list(case["c1"].node_ids), "integrated_candidate_ids": {}}}
    row["costs"].update({"cold_io_seconds": None, "c5_fit_seconds": None, "c5_prediction_seconds": None,
                           "integrated_seconds": None, "receipt_write_seconds": None})
    if failure:
        row["costs"]["shared_preprocessing_seconds"] = failure["shared_preprocessing_seconds"]
    row["costs"].setdefault("shared_preprocessing_seconds", None)
    row["costs"].setdefault("control_generation_seconds", None)
    return row


def _run_rcd(case, deadline):
    # Frozen G31 path uses the genuine pinned three seeds and copied numeric input.
    if case["rcd"] is None or case["c1"] is None:
        return {"seed_outputs": [{"seed": seed, "bins": 5, "status": "FAILURE", "ranks": None,
            "reason": "NUMERIC_OBSERVATION_UNAVAILABLE", "error": None} for seed in (420, 421, 422)],
            "metric_owners": {}, "n_services": 0 if case["c1"] is None else len(case["c1"].node_ids),
            "input_sha256": _digest({"missing_numeric_observation": True}),
            "qualification_identity_sha256": previous.RCD_IDENTITY,
            "costs": [{"seed": seed, "wall_seconds": None, "timed_out": False, "exit_code": None,
                       "stderr_sha256": None, "stderr_bytes": None} for seed in (420, 421, 422)]}
    return previous._run_rcd(case, deadline)


def _frozen_config():
    from rca.contracts import load_frozen_config
    return load_frozen_config(MANIFEST)


def _run_c5(source, case, deadline):
    from scripts.task_g.final_source import integrated_observation
    observation = case["c5"]
    worker = (_run_worker("c5", _c5_wire(observation), deadline) if observation is not None else
              {"rows": [], "wall_seconds": None, "timed_out": False, "exit_code": None,
               "stderr_sha256": None, "stderr_bytes": None})
    endpoints = [] if observation is None else observation.relative_endpoints.tolist()
    thresholds = {item["id"]: item["threshold"] for item in json.loads(MANIFEST.read_bytes())["selections"]["c5"]["detectors"]}
    received = {}
    for item in worker["rows"]:
        if item.get("kind") == "c5":
            if item["detector"] in received:
                raise FinalCampaignError("DUPLICATE_C5_WORKER_OUTPUT")
            received[item["detector"]] = item
    outputs, diagnostics, bindings = {}, {}, {}
    integrated_durations = []; fit_durations = []; prediction_durations = []
    # Same past-only observation and frozen ranker at an equal endpoint: reuse
    # exact deterministic computation across detectors, retaining every trigger.
    integrated_cache = {}
    for detector in DETECTORS:
        saved = received.get(detector)
        prefix = [] if saved is None else saved["bins"]
        if [item["endpoint"] for item in prefix] != endpoints[:len(prefix)]:
            raise FinalCampaignError("C5_DIAGNOSTIC_PREFIX_DRIFT")
        success = saved is not None and saved["status"] == "SUCCESS" and len(prefix) == len(endpoints)
        scores = [item["selected_system_score"] for item in prefix] + [None] * (len(endpoints)-len(prefix))
        triggers = []
        bindings[detector] = {}
        if prefix:
            for item in prefix:
                if not item["event"]["trigger"]:
                    continue
                endpoint = item["endpoint"]
                if endpoint < 360:
                    triggers.append({"endpoint": endpoint, "status": "INSUFFICIENT_HISTORY", "scores": None, "candidate_count": 0, "input_sha256": None})
                    bindings[detector][str(endpoint)] = []
                    continue
                reused = endpoint in integrated_cache
                if not reused:
                    then = time.perf_counter()
                    try:
                        one = integrated_observation(source, case["ordinal"], endpoint)
                        one_wire = previous._c1_wire(one, "INTEGRATED")
                        predicted = _run_worker("c1", one_wire, deadline)
                        rows = [line for line in predicted["rows"] if line.get("kind") == "integrated"]
                        output = rows[0] if len(rows) == 1 and predicted["exit_code"] == 0 and not predicted["timed_out"] else {"status": "TIMEOUT" if predicted["timed_out"] else "FAILURE", "scores": None}
                        record = {"endpoint": endpoint, "status": output["status"], "scores": output["scores"],
                            "candidate_count": len(one.node_ids), "input_sha256": _digest(one_wire), "candidate_ids": list(one.node_ids),
                            "scientific_diagnostics": output.get("scientific_diagnostics"), "quality": _scientific_plain(dict(one.quality)),
                            "graph_provenance": _scientific_plain(dict(one.graph_provenance)),
                            "evidence_catalog": _scientific_plain(one.evidence_catalog)}
                    except Exception as exc:
                        record = {"endpoint": endpoint, "status": "FAILURE", "scores": None,
                            "candidate_count": 0, "candidate_ids": [], "input_sha256": None,
                            "reason": type(exc).__name__, "scientific_diagnostics": None,
                            "quality": None, "graph_provenance": None, "evidence_catalog": None}
                    duration = time.perf_counter() - then
                    integrated_durations.append(duration)
                    record["wall_seconds"] = duration
                    integrated_cache[endpoint] = record
                record = copy.deepcopy(integrated_cache[endpoint])
                record["reused_equal_endpoint_computation"] = reused
                bindings[detector][str(endpoint)] = list(record["candidate_ids"])
                triggers.append(record)
        failed_status = "TIMEOUT" if worker["timed_out"] else "FAILURE"
        outputs[detector] = {"status": "SUCCESS" if success else failed_status, "threshold": thresholds[detector],
            "starts": [end-5 for end in endpoints], "ends": endpoints, "scores": scores,
            "bin_statuses": ["SUCCESS" if val is not None else "UNAVAILABLE" if index < len(prefix) else failed_status for index, val in enumerate(scores)],
            "triggers": triggers, "wall_seconds": None if saved is None else saved["wall_seconds"]}
        diagnostics[detector] = {"status": "SUCCESS" if success else failed_status, "state": None if saved is None else saved["state"],
            "reason": "C5_OBSERVATION_UNAVAILABLE" if observation is None else "WORKER_OUTPUT_MISSING" if saved is None else saved.get("reason"),
            "bins": prefix, "input": {} if observation is None else _c5_wire(observation),
            "fit_seconds": None if saved is None else saved["fit_seconds"], "prediction_seconds": None if saved is None else saved["prediction_seconds"]}
        if saved and saved["fit_seconds"] is not None: fit_durations.append(saved["fit_seconds"])
        if saved and saved["prediction_seconds"] is not None: prediction_durations.append(saved["prediction_seconds"])
    costs = {"c5_worker": {key: worker[key] for key in ("wall_seconds", "timed_out", "exit_code", "stderr_sha256", "stderr_bytes")},
             "c5_fit_seconds": sum(fit_durations) if len(fit_durations) == 8 else None,
             "c5_prediction_seconds": sum(prediction_durations) if len(prediction_durations) == 8 else None,
             "c5_fit_partial_measured_seconds": sum(fit_durations) if fit_durations else None,
             "c5_prediction_partial_measured_seconds": sum(prediction_durations) if prediction_durations else None,
             "c5_fit_measured_detectors": len(fit_durations), "c5_prediction_measured_detectors": len(prediction_durations),
             "integrated_seconds": sum(integrated_durations) if integrated_durations else
                 0.0 if all(item["status"] == "SUCCESS" for item in outputs.values()) else None,
             "integrated_measured_calls": len(integrated_durations),
             "integrated_unique_endpoint_cache": True}
    return outputs, diagnostics, bindings, costs


def _compute_case(source, case, deadline, auxiliary):
    from scripts.task_g.final_source import SYNTHETIC_SCOPE
    if case.get("source_metadata", {}).get("scope") != SYNTHETIC_SCOPE:
        raise FinalCampaignError("ONLY_SYNTHETIC_NUMERIC_COMPUTATION_ALLOWED")
    started = time.perf_counter()
    assembly_case = case
    if case["c1"] is None:
        import numpy as np
        from types import SimpleNamespace
        assembly_case = {**case, "c1": SimpleNamespace(node_ids=(), adjacency=np.zeros((0, 0), dtype=bool),
            handle=hashlib.sha256(f"G32|missing|{case['ordinal']}".encode()).hexdigest()[:16],
            ref=np.empty((0, 0, 0)), query=np.empty((0, 0, 0)), channel_types=(), quality={})}
        worker = {"rows": [], "timed_out": False, "exit_code": None, "wall_seconds": None,
                  "stderr_sha256": None, "stderr_bytes": None}
    else:
        worker = _run_worker("c1", previous._c1_wire(case["c1"]), deadline)
    row = _assemble_c1(assembly_case, worker)
    if case["c1"] is None:
        row["scientific_diagnostics"]["c1"]["status"] = "UNAVAILABLE_SOURCE_OBSERVATION"
        row["scientific_diagnostics"]["c1"]["reason"] = "C1_OBSERVATION_UNAVAILABLE"
    row["costs"]["input_and_worker_case_wall_seconds"] = time.perf_counter() - started
    for method in ("Local-MAX-MT", "BARO-RANK-adapted-TD12"):
        row["contextual"].setdefault(method, {"status": "FAILURE", "scores": None})
    row["contextual"]["RCD"] = _run_rcd(case, auxiliary)
    row["c5"], row["scientific_diagnostics"]["c5"], bindings, costs = _run_c5(source, case, auxiliary)
    row["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"] = bindings
    row["costs"].update(costs)
    row["costs"]["cold_io_seconds"] = case.get("source_metadata", {}).get("conversion_costs", {}).get("cold_io_and_hash_seconds")
    row["scientific_diagnostics"]["controller_bindings"].update({
        "source_hashes": case.get("source_metadata", {}).get("source_hashes", {}) if case["c1"] is None else dict(case["c1"].source_hashes),
        "graph_provenance": None if case["c1"] is None else _scientific_plain(dict(case["c1"].graph_provenance)),
        "evidence_catalog": None if case["c1"] is None else _scientific_plain(dict(case["c1"].evidence_catalog)),
        "c5_candidate_ids": [] if case["c5"] is None else list(case["c5"].node_ids),
        "c5_quality": None if case["c5"] is None else _scientific_plain(dict(case["c5"].quality)),
        "c5_graph_provenance": None if case["c5"] is None else _scientific_plain(dict(case["c5"].graph_provenance)),
        "conversion_provenance": _scientific_plain(case.get("source_metadata", {}))})
    return row


@contextmanager
def _readiness_lock():
    """One bounded controller; a process death releases the operating-system lock."""
    path = CONTRACT.parent / "cache/driver.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    from scripts.task_g.final_provenance import _require_regular_path
    _require_regular_path(path, allow_missing=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0"); stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise FinalCampaignError("READINESS_CONTROLLER_ALREADY_RUNNING") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _write_cache_exclusive(path, payload):
    from scripts.task_g.final_provenance import _require_regular_path
    _require_regular_path(path, allow_missing=True)
    encoded = _canonical(payload)
    with path.open("xb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    if path.read_bytes() != encoded:
        raise FinalCampaignError("READINESS_CACHE_READBACK_FAILED")
    return {"path": str(path.relative_to(WORKSPACE)).replace("\\", "/"),
            "sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)}


def run_development_timing():
    """One locked30 pass measures the new full C1 diagnostic workload, no truth."""
    from scripts.task_g.final_source import load_development_source, get_case, source_summary, case_count
    context, contract = _context()
    if contract["permissions"].get("development30_timing_only") is not True:
        raise FinalCampaignError("DEVELOPMENT_TIMING_PERMISSION_CLOSED")
    with _readiness_lock():
        directory = CONTRACT.parent / "cache" / ("development-attempt-" + str(time.time_ns()))
        directory.mkdir()
        _write_cache_exclusive(directory / "attempt.json", {"scope": "DEVELOPMENT_TIMING_ONLY",
            "started_context": context, "planned_cases": 30, "outcomes_read": False,
            "workload": "FULL_G32_C1_DIAGNOSTICS_SAME_WORKER_AND_FROZEN_METHOD"})
        then = time.perf_counter()
        source = load_development_source()
        admission = time.perf_counter() - then
        if case_count(source) != 30:
            raise FinalCampaignError("EXACT_DEVELOPMENT30_REQUIRED")
        rows, artifacts = [], []
        for ordinal in range(30):
            then = time.perf_counter()
            case = get_case(source, ordinal)
            worker = _run_worker("c1", previous._c1_wire(case["c1"]),
                                 contract["resource_policy"]["development_timing_infrastructure_deadline_seconds"])
            row = _assemble_c1(case, worker)
            previous._apply_walltime_measurement(row, admission, time.perf_counter() - then)
            # C1-only timing never executes contextual comparator models/C5/RCD
            # beyond the two numeric contextual scores present in the C1 worker.
            row["contextual"] = {}; row["c5"] = {}
            rows.append(row)
            artifacts.append(_write_cache_exclusive(directory / f"case-{ordinal:02d}.json", row))
            _emit({"phase": "G32_DEVELOPMENT_TIMING_ONLY", "completed_cases": len(rows),
                   "planned_cases": 30, "timing_completed": row["costs"]["timing_completed"]})
        report = previous._timing_report(rows, source_summary(source))
        report.update(scope="DEVELOPMENT_TIMING_ONLY", context=context,
                      workload="FULL_G32_C1_DIAGNOSTICS_SAME_WORKER_AND_FROZEN_METHOD", case_artifacts=artifacts,
                      c5_rcd_seal_in_common_c1_timeout=False, final_prediction_qualified=False)
        if _context()[0] != context:
            raise FinalCampaignError("DEVELOPMENT_TIMING_CONTEXT_DRIFT")
        return _write_cache_exclusive(directory / "timing.json", report)


def _bind_readiness():
    issued = weakref.WeakKeyDictionary()
    context_reader = _context
    compute = _compute_case
    def run():
        from scripts.task_g.final_source import make_synthetic_source, get_case, case_count, source_summary
        context, contract = context_reader()
        source = make_synthetic_source()
        count = case_count(source)
        if not 1 <= count <= 3:
            raise FinalCampaignError("BOUNDED_DISTINCT_SYNTHETIC_CASE_COUNT_REQUIRED")
        directory = CONTRACT.parent / "cache" / ("synthetic-numeric-attempt-" + str(time.time_ns()))
        directory.mkdir(parents=True)
        _write_cache_exclusive(directory / "attempt.json", {"context": context,
            "scope": "SYNTHETIC_BRIDGE_READINESS", "planned_cases": count,
            "actual_models_or_truth": False, "orchestration_numeric_computations": 0})
        rows, checkpoints = [], []
        for ordinal in range(count):
            row = compute(source, get_case(source, ordinal), contract["resource_policy"]["common_L_O_R_timeout_seconds"],
                          contract["resource_policy"]["auxiliary_numeric_worker_deadline_seconds"])
            rows.append(row)
            checkpoints.append(_write_cache_exclusive(directory / f"case-{ordinal:02d}.json", row))
            _emit({"phase": "G32_DISTINCT_SYNTHETIC_NUMERIC_ONLY", "completed_computational_cases": len(rows), "planned_computational_cases": count})
        if context_reader()[0] != context:
            raise FinalCampaignError("CONTEXT_CHANGED_DURING_READINESS")
        handle = ReadinessExecution()
        issued[handle] = {"context": context, "payload": {"schema": "TD13-G32-BRIDGE-EXECUTION-v1", "run_id": RUN_ID,
            "domain": DOMAIN, "phase": PHASE, "trust_mode": "HOST_TRUSTED", "scope": "SYNTHETIC_BRIDGE_READINESS", "source_summary": source_summary(source),
            **{key: context[key] for key in ("source_snapshot_sha256", "permissions_sha256", "config_sha256")}, "planned_case_count": count, "cases": rows,
            "prepared_conditions": contract["prepared_conditions"], "final_prediction_qualified": False,
            "checkpoint_manifest": checkpoints,
            "orchestration_fixture": {"scope": "SYNTHETIC_ONLY_ORCHESTRATION", "planned_slots": 60,
                "ordinals": list(range(60)), "numerical_computations": 0, "final_prediction_qualified": False}}}
        return handle
    def payload(handle):
        if type(handle) is not ReadinessExecution or handle not in issued:
            raise FinalCampaignError("UNISSUED_READINESS_EXECUTION")
        state = issued[handle]
        if context_reader()[0] != state["context"]:
            raise FinalCampaignError("READINESS_EXECUTION_CONTEXT_DRIFT")
        return copy.deepcopy(state["payload"])
    return run, payload


run_synthetic_readiness, _readiness_payload_for_provenance = _bind_readiness()
del _bind_readiness


def run_final_campaign(*args, **kwargs):
    raise FinalCampaignError("FINAL_CAMPAIGN_PERMISSION_CLOSED__READINESS_DOMAIN_CANNOT_AUTHORIZE")


def _main():
    if len(sys.argv) == 3 and sys.argv[1] == "--numeric-worker" and sys.argv[2] in ("c1", "c5"):
        try:
            wire = json.loads(sys.stdin.buffer.read(64 * 1024 * 1024))
            {"c1": _numeric_c1_worker, "c5": _numeric_c5_worker}[sys.argv[2]](wire)
            return 0
        except Exception as exc:
            _emit({"kind": "worker_failure", "reason": type(exc).__name__})
            return 2
    if sys.argv[1:] == ["--synthetic-readiness"]:
        from scripts.task_g.final_provenance import commit_readiness
        with _readiness_lock():
            _emit(commit_readiness(run_synthetic_readiness()))
        return 0
    if sys.argv[1:] == ["--development-timing"]:
        _emit(run_development_timing())
        return 0
    raise FinalCampaignError("ONLY_REGISTERED_SYNTHETIC_READINESS_COMMAND_AVAILABLE")


if __name__ == "__main__":
    raise SystemExit(_main())
