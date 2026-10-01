"""Fixed G31 numeric readiness execution; actual final campaign stays closed.

Only internally issued synthetic/development sources can create execution
handles. Numeric subprocesses receive detached arrays, pseudokeys and relative
clocks. Durable per-case checkpoints preserve completed work across interruption.
This boundary assumes an intact host; it does not sandbox a compromised process.
"""

from __future__ import annotations

import base64
import copy
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import weakref

WORKSPACE = Path(__file__).resolve().parents[2]
PROJECT = Path("D:/Project/flash-ticket-platform")
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
if str(WORKSPACE / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE / "src"))
if __name__ == "__main__":
    # Provenance imports this canonical module; script entry must retain the
    # same closed issuance registry rather than silently creating a second one.
    sys.modules["scripts.task_g.campaign"] = sys.modules[__name__]
RUN_ID = "g31-campaign-readiness"
DOMAIN = "FlashTicketRca/TD13/G31/READINESS/v1"
CONTRACT = WORKSPACE / "results/task-g" / RUN_ID / "run-contract.json"
MANIFEST = WORKSPACE / "configs/task-f-td13-frozen-release-v2.json"
RCD_IDENTITY = "38253ebbfaa53bdad20b66e655ade3fade363fdd9ef71ee2ab6df722ab4fac04"
THREADS = {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}
DETECTORS = ("G-MTL", "L-MTL", "ALL-MTL", "TV-MTL", "G-MT", "L-MT", "ALL-MT", "TV-MT")
SCIENTIFIC_KEYS = ("td", "dataset", "split", "exposure_ledger", "selections", "r_control", "comparators", "evaluator", "packet", "selection_policy", "final60_policy", "prohibited_runtime_rules")


class CampaignError(ValueError):
    """Sanitized failure of fixed readiness registration or execution."""


class CampaignExecution:
    __slots__ = ("__weakref__",)


class CaseExecution:
    __slots__ = ("__weakref__",)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _numeric_plain(value):
    import numpy as np
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: _numeric_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_numeric_plain(item) for item in value]
    return value


def prepare_conditions():
    """Derive scientific conditions from immutable F, never select by outputs."""
    from rca.contracts import load_frozen_config
    load_frozen_config(MANIFEST)
    manifest = json.loads(MANIFEST.read_bytes())
    conditions = {
        "scientific_objects": {key: manifest[key] for key in SCIENTIFIC_KEYS},
        "planned_final_cases": 60, "planned_final_cells": 20,
        "rankers": ["primary", "secondary"], "R_draws": 256,
        "RCD_seeds": [420, 421, 422], "RCD_bins": 5,
        "C5_detector_ids": list(DETECTORS), "method_selection_or_retuning": False,
    }
    return {"conditions": conditions, "sha256": _digest(conditions)}


def _context():
    from scripts.task_g.campaign_provenance import _registered_context
    from rca.release import verify_frozen_release
    context, contract = _registered_context()
    verify_frozen_release(MANIFEST, workspace_root=WORKSPACE, project_root=PROJECT)
    policy = contract["resource_policy"]
    if (policy["worker_count"] != 1 or policy["numeric_threads"] != 1
            or policy["thread_environment"] != THREADS
            or policy["development_timing_infrastructure_deadline_seconds"] != 900
            or policy.get("auxiliary_numeric_worker_deadline_seconds") != 900
            or policy["R_generation_included"] is not True
            or policy["secondary_reuses_same_realized_undirected_graphs"] is not True):
        raise CampaignError("REGISTERED_RESOURCE_POLICY_DRIFT")
    return context, contract


def _pack(array):
    import numpy as np
    array = np.ascontiguousarray(array)
    if array.dtype.kind not in "biuf" or np.isinf(array).any():
        raise CampaignError("INVALID_NUMERIC_ARRAY")
    return {"dtype": array.dtype.str, "shape": list(array.shape),
            "bytes_b64": base64.b64encode(array.tobytes()).decode("ascii")}


def _unpack(record):
    import numpy as np
    if type(record) is not dict or set(record) != {"dtype", "shape", "bytes_b64"}:
        raise CampaignError("NUMERIC_WIRE_SCHEMA_DRIFT")
    shape = record["shape"]
    if type(shape) is not list or len(shape) > 3 or any(type(v) is not int or v < 0 or v > 10000 for v in shape):
        raise CampaignError("NUMERIC_WIRE_SHAPE_INVALID")
    dtype = np.dtype(record["dtype"])
    if dtype.kind not in "biuf" or dtype.itemsize > 8:
        raise CampaignError("NUMERIC_WIRE_TYPE_INVALID")
    raw = base64.b64decode(record["bytes_b64"], validate=True)
    expected = math.prod(shape) * dtype.itemsize
    if expected > 64 * 1024 * 1024 or len(raw) != expected:
        raise CampaignError("NUMERIC_WIRE_SIZE_INVALID")
    array = np.frombuffer(raw, dtype=dtype).reshape(shape).copy()
    if np.isinf(array).any():
        raise CampaignError("NUMERIC_WIRE_INFINITY")
    return array


def _emit(value):
    sys.stdout.buffer.write(_canonical(value) + b"\n")
    sys.stdout.buffer.flush()


def _worker_guard():
    """No production issuance here; workers additionally verify stable bytes."""
    from scripts.task_g.campaign_source import _registered_context
    from rca.release import verify_frozen_release
    _registered_context()
    verify_frozen_release(MANIFEST, workspace_root=WORKSPACE, project_root=PROJECT)
    if any(os.environ.get(key) != value for key, value in THREADS.items()):
        raise CampaignError("NUMERIC_THREAD_LIMIT_DRIFT")


def _operator_scores(local, adjacency, selected):
    from rca.ranking import rank_scores
    return rank_scores(local, adjacency, operator=selected.operator,
                       direction=selected.direction, damping=selected.damping)["scores"].tolist()


def _numeric_c1_worker(wire):
    import numpy as np
    from rca.contracts import load_frozen_config
    from rca.ranking import local_scores, perturb_graphs
    from rca.comparators import local_max_scores, baro_scores
    _worker_guard()
    if set(wire) != {"mode", "ref", "query", "adj", "channel_types", "routing_handle"}:
        raise CampaignError("C1_WORKER_WIRE_SCHEMA_DRIFT")
    if wire["mode"] not in ("C1", "INTEGRATED"):
        raise CampaignError("C1_WORKER_MODE_INVALID")
    if len(wire["routing_handle"]) != 16 or any(ch not in "0123456789abcdef" for ch in wire["routing_handle"]):
        raise CampaignError("OPAQUE_ROUTING_HANDLE_INVALID")
    ref, query, adj, types = (_unpack(wire[key]) for key in ("ref", "query", "adj", "channel_types"))
    config = load_frozen_config(MANIFEST)
    started = time.perf_counter()
    local_config = dict(config.local)
    if wire["mode"] == "INTEGRATED":
        local_config["include_logs"] = True
    evidence = local_scores(ref, query, types, local_config)
    if np.asarray(evidence["diagnostics"]["numerical_channel_failures"]).any():
        raise CampaignError("SHARED_PREPROCESSING_NUMERICAL_FAILURE")
    local = evidence["local"]
    shared = time.perf_counter() - started
    operators = {"primary": config.primary_ppr, "secondary": config.secondary_diffusion}
    header = {"kind": "header", "local_evidence": local.tolist(), "c1": {}, "contextual": {},
              "costs": {"shared_preprocessing_seconds": shared, "rank_seconds": {}, "control_generation_seconds": 0.0}}
    for name, selected in operators.items():
        header["c1"][name] = {}
        header["costs"]["rank_seconds"][name] = {}
        for arm, graph in (("L", np.zeros_like(adj)), ("O", adj)):
            then = time.perf_counter()
            try:
                header["c1"][name][arm] = {"status": "SUCCESS", "scores": _operator_scores(local, graph, selected)}
            except Exception as exc:
                header["c1"][name][arm] = {"status": "FAILURE", "scores": None, "reason": type(exc).__name__}
            header["costs"]["rank_seconds"][name][arm] = time.perf_counter() - then
    if wire["mode"] == "INTEGRATED":
        _emit({"kind": "integrated", **header["c1"]["primary"]["O"], "local_evidence": local.tolist()})
        return
    for method, callable_ in (("Local-MAX-MT", lambda: local_max_scores(evidence["blocks"], evidence["masks"]["blocks"])),
                              ("BARO-RANK-adapted-TD12", lambda: baro_scores(ref, query, types))):
        try:
            result = callable_()
            if "diagnostics" in result and np.asarray(result["diagnostics"]["numerical_channel_failures"]).any():
                raise CampaignError("COMPARATOR_NUMERICAL_FAILURE")
            header["contextual"][method] = {"status": "SUCCESS", "scores": result["scores"].tolist()}
        except Exception as exc:
            header["contextual"][method] = {"status": "FAILURE", "scores": None, "reason": type(exc).__name__}
    _emit(header)
    then = time.perf_counter()
    control = perturb_graphs(adj, wire["routing_handle"], "undirected", count=256, budget=200)
    generation = time.perf_counter() - then
    totals = {name: 0.0 for name in operators}
    for draw, (graph, receipt) in enumerate(zip(control["graphs"], control["per_draw"], strict=True)):
        out = {"kind": "draw", "draw": draw, "graph": {
            **receipt, "status": "SUCCESS", "adjacency": graph.astype(int).tolist(),
            "graph_sha256": receipt["hash"]}, "rankers": {}}
        for name, selected in operators.items():
            then = time.perf_counter()
            try:
                ranking = {"status": "SUCCESS", "scores": _operator_scores(local, graph, selected)}
            except Exception as exc:
                ranking = {"status": "FAILURE", "scores": None, "reason": type(exc).__name__}
            duration = time.perf_counter() - then
            totals[name] += duration
            out["rankers"][name] = {**ranking, "draw": draw, "seed": receipt["seed"],
                                   "graph_sha256": receipt["hash"],
                                   "retained_edge_fraction": receipt["retained_edge_fraction"]}
        _emit(out)
    _emit({"kind": "done", "control_generation_seconds": generation,
           "R_rank_seconds": totals, "worker_numeric_seconds": time.perf_counter() - started,
           "control_summary": _numeric_plain(control["summary"])})


def _rcd_worker(wire):
    import numpy as np
    import pandas as pd
    from rca.qualified_rcd import load_qualified_rcd
    from rca.comparators import rcd_run
    _worker_guard()
    if set(wire) != {"values", "seed"} or wire["seed"] not in (420, 421, 422):
        raise CampaignError("RCD_WORKER_WIRE_SCHEMA_DRIFT")
    values = _unpack(wire["values"])
    if values.ndim != 2 or values.shape[0] != 600 or not np.isfinite(values).all():
        raise CampaignError("RCD_WORKER_INPUT_INVALID")
    runner = load_qualified_rcd(workspace_root=WORKSPACE, project_root=PROJECT, manifest_path=MANIFEST)
    if _digest(runner.identity) != RCD_IDENTITY:
        raise CampaignError("RCD_QUALIFIED_RUNNER_IDENTITY_DRIFT")
    frame = pd.DataFrame(values.copy(), columns=[f"m{i}" for i in range(values.shape[1])])
    frame.insert(0, "time", np.arange(600, dtype=float))
    result = rcd_run(frame.copy(deep=True), seed=wire["seed"], bins=5, qualified_rcd=runner)
    _emit({"kind": "rcd", "output": result, "qualification_identity_sha256": RCD_IDENTITY,
           "input_sha256": _digest(wire["values"])})


def _numeric_c5_worker(wire):
    import numpy as np
    from rca.pipeline import FrozenRcaPipeline
    from rca.observation import C5Observation
    _worker_guard()
    if set(wire) != {"warmup", "stream", "adj", "channel_types", "fit_mask", "endpoints"}:
        raise CampaignError("C5_WORKER_WIRE_SCHEMA_DRIFT")
    warmup, stream, adj, types, fit_mask, endpoints = (_unpack(wire[key]) for key in ("warmup", "stream", "adj", "channel_types", "fit_mask", "endpoints"))
    observation = C5Observation("0000000000000000", warmup, stream, tuple(types), adj, fit_mask,
        tuple(f"v{i}" for i in range(len(adj))), endpoints, {"numeric": _digest(wire)}, {}, {}, {})
    frozen = json.loads(MANIFEST.read_bytes())
    pipeline = FrozenRcaPipeline.from_manifest(MANIFEST,
        code_identity={row["path"]: row["sha256"] for row in frozen["implementation"]["source_files"]},
        release_id=frozen["implementation"]["release_id"])
    for detector in DETECTORS:
        then = time.perf_counter()
        result = pipeline.run_c5(observation, detector)
        bins = result.get("bins", [])
        row = {"kind": "c5", "detector": detector, "status": "SUCCESS" if result["status"] == "SUCCESS" else "FAILURE",
               "bins": [{"endpoint": int(item["endpoint"]),
                         "score": float(item["selected_system_score"]) if item["selected_system_score"] is not None and np.isfinite(item["selected_system_score"]) else None,
                         "trigger": bool(item["event"]["trigger"])} for item in bins],
               "wall_seconds": time.perf_counter() - then}
        _emit(row)


def _run_worker(mode, wire, deadline):
    """Fixed executables; preserve complete output lines even after timeout."""
    python = WORKSPACE / ("environments/task-e/rcd39/Scripts/python.exe" if mode == "rcd" else ".venv/Scripts/python.exe")
    environment = {**os.environ, **THREADS, "PYTHONPATH": str(WORKSPACE / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
    started = time.perf_counter()
    process = subprocess.Popen([str(python), "-B", str(Path(__file__).resolve()), "--numeric-worker", mode],
        cwd=WORKSPACE, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        output, errors = process.communicate(_canonical(wire), timeout=deadline)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        output, errors = process.communicate()
    rows = []
    for line in output.splitlines():
        try:
            rows.append(json.loads(line))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # A killed worker may have one incomplete final line; complete
            # draw records remain available. Never infer success from stderr.
            break
    return {"rows": rows, "exit_code": process.returncode, "timed_out": timed_out,
            "wall_seconds": time.perf_counter() - started,
            "stderr_sha256": hashlib.sha256(errors).hexdigest(), "stderr_bytes": len(errors)}


def _seed(route, draw):
    return int.from_bytes(hashlib.sha256(f"TD12|R|{route}|undirected|{draw}".encode()).digest()[:8], "big")


def _c1_wire(observation, mode="C1"):
    return {"mode": mode, "ref": _pack(observation.ref), "query": _pack(observation.query),
            "adj": _pack(observation.adjacency), "channel_types": _pack(observation.channel_types),
            "routing_handle": observation.handle}


def _assemble_c1(case, worker):
    count = len(case["c1"].node_ids)
    status = "TIMEOUT" if worker["timed_out"] else "FAILURE"
    arms = {name: {"L": {"status": status, "scores": None}, "O": {"status": status, "scores": None}, "R": []} for name in ("primary", "secondary")}
    graphs = [{"draw": draw, "seed": _seed(case["c1"].handle, draw), "status": status,
               "adjacency": None, "graph_sha256": None, "retained_edge_fraction": None} for draw in range(256)]
    for name in arms:
        arms[name]["R"] = [{"draw": draw, "seed": row["seed"], "status": status, "scores": None,
                            "graph_sha256": None, "retained_edge_fraction": None} for draw, row in enumerate(graphs)]
    header = next((row for row in worker["rows"] if row.get("kind") == "header"), None)
    done = next((row for row in worker["rows"] if row.get("kind") == "done"), None)
    local = [0.0] * count
    costs = {"worker_wall_seconds": worker["wall_seconds"], "timed_out": worker["timed_out"],
             "exit_code": worker["exit_code"], "stderr_sha256": worker["stderr_sha256"],
             "stderr_bytes": worker["stderr_bytes"], "timing_completed": done is not None and worker["exit_code"] == 0,
             "arm_wall_seconds": {name: {arm: None for arm in ("L", "O", "R")} for name in arms}}
    if header is not None:
        local = header["local_evidence"]
        for name in arms:
            arms[name].update(header["c1"][name])
        costs.update(header["costs"])
    seen = set()
    for row in worker["rows"]:
        if row.get("kind") != "draw":
            continue
        draw = row["draw"]
        if type(draw) is not int or draw in seen or not 0 <= draw < 256:
            raise CampaignError("WORKER_CONTROL_DRAW_INVALID")
        seen.add(draw)
        if row["graph"]["seed"] != graphs[draw]["seed"]:
            raise CampaignError("WORKER_CONTROL_SEED_DRIFT")
        graphs[draw] = row["graph"]
        for name in arms:
            arms[name]["R"][draw] = row["rankers"][name]
    if done is not None and header is not None:
        costs.update(done)
        costs.pop("kind", None)
        for name in arms:
            for arm in ("L", "O"):
                costs["arm_wall_seconds"][name][arm] = costs["shared_preprocessing_seconds"] + costs["rank_seconds"][name][arm]
            costs["arm_wall_seconds"][name]["R"] = costs["shared_preprocessing_seconds"] + done["control_generation_seconds"] + done["R_rank_seconds"][name]
    return {"ordinal": case["ordinal"], "cell_ordinal": case["cell_ordinal"], "repeat": case["repeat"],
            "candidate_count": count, "numeric_input_sha256": case["numeric_input_sha256"],
            "shared_preprocessing_failed": header is None, "local_evidence": local,
            "control_graphs": graphs, "c1": arms,
            "contextual": {} if header is None else header["contextual"], "c5": {}, "costs": costs}


def _run_rcd(case, deadline):
    values = _pack(case["rcd"]["values"])
    outputs = []
    costs = []
    for seed in (420, 421, 422):
        worker = _run_worker("rcd", {"values": values, "seed": seed}, deadline)
        cost = {key: worker[key] for key in ("wall_seconds", "timed_out", "exit_code", "stderr_sha256", "stderr_bytes")}
        rows = [row for row in worker["rows"] if row.get("kind") == "rcd"]
        if (worker["exit_code"] == 0 and len(rows) == 1
                and rows[0]["qualification_identity_sha256"] == RCD_IDENTITY
                and rows[0]["input_sha256"] == _digest(values)):
            result = rows[0]["output"]
            if result.get("seed") != seed or result.get("bins") != 5:
                raise CampaignError("RCD_WORKER_OUTPUT_DRIFT")
        else:
            result = {"seed": seed, "bins": 5, "status": "FAILURE", "ranks": None,
                      "reason": "TIMEOUT" if worker["timed_out"] else "WORKER_FAILURE", "error": None}
        outputs.append(result)
        costs.append({"seed": seed, **cost})
    return {"seed_outputs": outputs,
            "metric_owners": {f"m{i}": int(owner) for i, owner in enumerate(case["rcd"]["owners"])},
            "n_services": len(case["c1"].node_ids), "input_sha256": _digest(values),
            "qualification_identity_sha256": RCD_IDENTITY, "costs": costs}


def _run_c5(source, case, deadline):
    from scripts.task_g.campaign_source import integrated_observation
    observation = case["c5"]
    wire = {"warmup": _pack(observation.warmup_values), "stream": _pack(observation.stream_values),
            "adj": _pack(observation.adjacency), "channel_types": _pack(observation.channel_types),
            "fit_mask": _pack(observation.fit_service_mask), "endpoints": _pack(observation.relative_endpoints)}
    worker = _run_worker("c5", wire, deadline)
    outputs = {}
    thresholds = {row["id"]: row["threshold"] for row in json.loads(MANIFEST.read_bytes())["selections"]["c5"]["detectors"]}
    endpoints = observation.relative_endpoints.tolist()
    received = {row["detector"]: row for row in worker["rows"] if row.get("kind") == "c5"}
    for detector in DETECTORS:
        row = received.get(detector)
        success = row is not None and row["status"] == "SUCCESS" and [item["endpoint"] for item in row["bins"]] == endpoints
        scores = [item["score"] for item in row["bins"]] if success else [None] * len(endpoints)
        triggers = []
        if success:
            for item in row["bins"]:
                if not item["trigger"]:
                    continue
                endpoint = item["endpoint"]
                if endpoint < 360:
                    triggers.append({"endpoint": endpoint, "status": "INSUFFICIENT_HISTORY", "scores": None, "candidate_count": 0, "input_sha256": None})
                    continue
                one = integrated_observation(source, case["ordinal"], endpoint)
                one_wire = _c1_wire(one, "INTEGRATED")
                prediction = _run_worker("c1", one_wire, deadline)
                records = [item for item in prediction["rows"] if item.get("kind") == "integrated"]
                output = records[0] if len(records) == 1 and prediction["exit_code"] == 0 else {"status": "FAILURE", "scores": None}
                triggers.append({"endpoint": endpoint, "status": output["status"], "scores": output["scores"],
                                 "candidate_count": len(one.node_ids), "input_sha256": _digest(one_wire)})
        outputs[detector] = {"status": "SUCCESS" if success else "FAILURE", "threshold": thresholds[detector],
            "starts": [end - 5 for end in endpoints], "ends": endpoints, "scores": scores,
            "bin_statuses": ["SUCCESS" if value is not None else ("UNAVAILABLE" if success else "FAILURE") for value in scores],
            "triggers": triggers, "wall_seconds": None if row is None else row["wall_seconds"]}
    return outputs, {key: worker[key] for key in ("wall_seconds", "timed_out", "exit_code", "stderr_sha256", "stderr_bytes")}


def _timing_report(cases, summary):
    if len(cases) != 30:
        raise CampaignError("DEVELOPMENT30_TIMING_INCOMPLETE")
    measured = []
    for case in cases:
        if not case["costs"]["timing_completed"]:
            continue
        for ranker in ("primary", "secondary"):
            arms = case["c1"][ranker]
            for arm in ("L", "O", "R"):
                successful = all(row["status"] == "SUCCESS" for row in arms["R"]) if arm == "R" else arms[arm]["status"] == "SUCCESS"
                value = case["costs"]["arm_wall_seconds"][ranker][arm]
                if successful and type(value) in (int, float) and math.isfinite(value):
                    measured.append(value)
    if not measured:
        raise CampaignError("NO_MATCHED_SUCCESSFUL_DEVELOPMENT_TIMING")
    maximum = max(measured)
    return {"planned_cases": 30, "source_summary": summary, "cases": cases,
            "successful_measured_arm_count": len(measured),
            "maximum_successful_development_aggregate_case_walltime_across_arms": maximum,
            "derived_common_timeout_seconds": max(300.0, 10.0 * maximum),
            "R_generation_included": True, "secondary_same_graphs": True,
            "timing_only_no_outcomes": True}


def _apply_walltime_measurement(case, source_admission, execution_wall):
    """Matched full case budget, with a conservative measured cold-I/O bound.

    The fixed source issues the whole cohort in one cold read. Charging its
    measured full admission walltime to each case bounds the unavailable
    per-case cold allocation without claiming it was independently measured.
    All matched arms share the actual case worker/input walltime; numeric
    component costs remain separate, and never stand in for that walltime.
    """
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0
           for value in (source_admission, execution_wall)):
        raise CampaignError("INVALID_MATCHED_WALLTIME_MEASUREMENT")
    case["costs"]["arm_numeric_components_seconds"] = copy.deepcopy(case["costs"]["arm_wall_seconds"])
    case["costs"]["source_cold_admission_upper_bound_seconds"] = source_admission
    case["costs"]["input_and_worker_case_wall_seconds"] = execution_wall
    total = source_admission + execution_wall
    case["costs"]["matched_aggregate_case_wall_seconds"] = total
    case["costs"]["arm_wall_seconds"] = {
        name: {arm: total if case["costs"]["timing_completed"] else None for arm in ("L", "O", "R")}
        for name in ("primary", "secondary")}
    return case


@contextmanager
def _driver_lock():
    """OS releases this fixed exclusive driver lock even on process death."""
    from scripts.task_g.campaign_provenance import _require_regular_path
    path = CONTRACT.parent / "cache/driver.lock"
    _require_regular_path(path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise CampaignError("READINESS_DRIVER_ALREADY_RUNNING") from None
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def _bind_execution():
    executions = weakref.WeakKeyDictionary()
    case_executions = weakref.WeakKeyDictionary()
    context_reader = _context
    assemble = _assemble_c1
    runner = _run_worker
    rcd_runner, c5_runner = _run_rcd, _run_c5
    driver_lock = _driver_lock
    walltime_measurement = _apply_walltime_measurement

    def issue_case(kind, row, summary):
        context, _ = context_reader()
        handle = CaseExecution()
        case_executions[handle] = {"context": context, "payload": {
            "kind": kind, "ordinal": row["ordinal"], "numeric_input_sha256": row["numeric_input_sha256"],
            "case": copy.deepcopy(row), "source_summary": copy.deepcopy(summary)}}
        return handle

    def case_payload(handle):
        if type(handle) is not CaseExecution or handle not in case_executions:
            raise CampaignError("UNISSUED_CASE_EXECUTION")
        state = case_executions[handle]
        if context_reader()[0] != state["context"]:
            raise CampaignError("CASE_EXECUTION_CONTEXT_DRIFT")
        return copy.deepcopy(state["payload"])

    def payload(handle):
        if type(handle) is not CampaignExecution or handle not in executions:
            raise CampaignError("UNISSUED_CAMPAIGN_EXECUTION")
        state = executions[handle]
        if context_reader()[0] != state["context"]:
            raise CampaignError("CAMPAIGN_EXECUTION_CONTEXT_DRIFT")
        return copy.deepcopy(state["payload"])

    def run(kind):
        from scripts.task_g.campaign_source import make_synthetic_source, load_development_source, source_summary, case_count, get_case
        from scripts.task_g.campaign_provenance import commit_case_checkpoint, verify_case_checkpoint
        context, contract = context_reader()
        timing = kind == "development"
        if timing and contract["permissions"].get("development30_timing_only") is not True:
            raise CampaignError("DEVELOPMENT_TIMING_PERMISSION_CLOSED")
        if not timing and contract["resource_policy"]["common_L_O_R_timeout_seconds"] is None:
            raise CampaignError("MATCHED_DEVELOPMENT_TIMEOUT_REGISTRATION_REQUIRED")
        source_started = time.perf_counter()
        source = load_development_source() if timing else make_synthetic_source()
        source_admission = time.perf_counter() - source_started
        summary = source_summary(source)
        deadline = contract["resource_policy"]["development_timing_infrastructure_deadline_seconds"] if timing else contract["resource_policy"]["common_L_O_R_timeout_seconds"]
        auxiliary = contract["resource_policy"]["auxiliary_numeric_worker_deadline_seconds"]
        rows = []
        for ordinal in range(case_count(source)):
            case_started = time.perf_counter()
            case = get_case(source, ordinal)
            existing = verify_case_checkpoint(kind, ordinal, case["numeric_input_sha256"])
            if existing is not None:
                row = existing["case"]
                reused = True
            else:
                row = assemble(case, runner("c1", _c1_wire(case["c1"]), deadline))
                row = walltime_measurement(row, source_admission, time.perf_counter() - case_started)
                if timing:
                    row["contextual"] = {}
                else:
                    for method in ("Local-MAX-MT", "BARO-RANK-adapted-TD12"):
                        row["contextual"].setdefault(method, {"status": "FAILURE", "scores": None})
                    row["contextual"]["RCD"] = rcd_runner(case, auxiliary)
                    row["c5"], row["costs"]["c5_worker"] = c5_runner(source, case, auxiliary)
                commit_case_checkpoint(issue_case(kind, row, summary))
                reused = False
            rows.append(row)
            _emit({"phase": "DEVELOPMENT_TIMING_ONLY" if timing else "SYNTHETIC_CAMPAIGN_READINESS",
                   "completed": len(rows), "planned": case_count(source), "checkpoint_reused": reused})
        context_after, _ = context_reader()
        if context_after != context:
            raise CampaignError("READINESS_CONTEXT_CHANGED_DURING_EXECUTION")
        result = {"schema": "TD13-G31-NUMERIC-EXECUTION-v1", "run_id": RUN_ID, "domain": DOMAIN,
                  "phase": "CAMPAIGN_READINESS_ONLY", "trust_mode": "HOST_TRUSTED",
                  "scope": "DEVELOPMENT_TIMING_ONLY" if timing else "SYNTHETIC_CAMPAIGN_READINESS",
                  "prepared_conditions": contract["prepared_conditions"], "source_summary": summary,
                  "planned_case_count": len(rows), "cases": rows,
                  **{key: context[key] for key in ("source_snapshot_sha256", "permissions_sha256", "config_sha256")}}
        if timing:
            result["development_timing_report"] = _timing_report(rows, summary)
        else:
            development_source = load_development_source()
            development_rows = []
            for ordinal in range(case_count(development_source)):
                one = get_case(development_source, ordinal)
                checkpoint = verify_case_checkpoint("development", ordinal, one["numeric_input_sha256"])
                if checkpoint is None:
                    raise CampaignError("MATCHED_DEVELOPMENT_CHECKPOINT_MISSING")
                development_rows.append(checkpoint["case"])
            report = _timing_report(development_rows, source_summary(development_source))
            if contract["resource_policy"]["common_L_O_R_timeout_seconds"] != report["derived_common_timeout_seconds"]:
                raise CampaignError("REGISTERED_COMMON_TIMEOUT_DERIVATION_DRIFT")
            result["development_timing_report"] = report
        handle = CampaignExecution()
        executions[handle] = {"context": context, "payload": copy.deepcopy(result)}
        return handle

    def development():
        with driver_lock():
            return run("development")

    def synthetic():
        with driver_lock():
            return run("synthetic")

    def timing_summary(handle):
        value = payload(handle)
        if value["scope"] != "DEVELOPMENT_TIMING_ONLY":
            raise CampaignError("NOT_A_DEVELOPMENT_TIMING_EXECUTION")
        return {key: val for key, val in value["development_timing_report"].items() if key != "cases"}

    return development, synthetic, payload, case_payload, timing_summary


(run_development_timing, run_synthetic_readiness, _campaign_payload_for_provenance,
 _case_payload_for_checkpoint, development_timing_summary) = _bind_execution()
del _bind_execution


def run_final_campaign():
    _context()
    raise CampaignError("FINAL_TAU_PREDICTIONS_LABELS_AND_CAMPAIGN_PERMISSION_CLOSED")


def _main():
    if len(sys.argv) == 3 and sys.argv[1] == "--numeric-worker" and sys.argv[2] in ("c1", "c5", "rcd"):
        try:
            wire = json.loads(sys.stdin.buffer.read(64 * 1024 * 1024))
            {"c1": _numeric_c1_worker, "c5": _numeric_c5_worker, "rcd": _rcd_worker}[sys.argv[2]](wire)
        except Exception as exc:
            _emit({"kind": "worker_failure", "reason": type(exc).__name__})
            return 2
        return 0
    if len(sys.argv) == 2 and sys.argv[1] == "--development-timing":
        handle = run_development_timing()
        _emit(development_timing_summary(handle))
        return 0
    if len(sys.argv) == 2 and sys.argv[1] == "--synthetic-readiness":
        from scripts.task_g.campaign_provenance import commit_readiness
        _emit(commit_readiness(run_synthetic_readiness()))
        return 0
    raise CampaignError("ONLY_PREREGISTERED_READINESS_COMMANDS_AVAILABLE")


if __name__ == "__main__":
    raise SystemExit(_main())
