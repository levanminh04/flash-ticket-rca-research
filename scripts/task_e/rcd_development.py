"""Trusted complete-development RCD controller; child receives numeric arrays only.

Run only with a new coordinator contract that pins this driver, the qualified
worker, the successful real fixture receipt, all 30 case audit JSON files and
every materialized RCD NPZ. Root labels/owners are read only by this controller.
Raw replies are saved exclusively before mapping or evaluation. No final inputs,
seed selection, exclusions, retries of failed cases, or overwritten receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import sys
import threading
import time

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.contract import DEV_IDS, opaque_handle
from scripts.task_e.evaluator import service_scores_from_metric_ranks, tie_metrics
from scripts.task_e.execution import failure, file_sha, save_json
from scripts.task_e.rcd_runtime import require_run_contract
from scripts.task_e.rcd_numeric_worker import _require_qualification

METRICS = ("rr", "hit1", "hit3", "hit5", "ndcg5")
SEEDS = (420, 421, 422)
BINS = (5, 3, 7)
CONFIGS = [{"seed": seed, "bins": bins} for bins in BINS for seed in SEEDS]
ENGINEERING_TIMEOUT_SECONDS = 300
SCHEMA = "TD13-RCD-DEVELOPMENT-v1"


class WorkerTransportError(RuntimeError):
    pass


class RawReceiptPendingError(WorkerTransportError):
    """Fatal: an exact raw receipt cannot yet be sealed, so never evaluate it."""


def read_pinned(path, contract):
    path = Path(path).resolve()
    pins = {str(Path(row["path"]).resolve()): row["sha256"] for row in contract["inputs"]}
    if pins.get(str(path)) != file_sha(path):
        raise ValueError("Actual input is absent from contract or changed: " + str(path))
    return path


def _require_owned_sources(contract):
    records = {str(Path(row["path"]).resolve()): row["sha256"]
               for row in contract["source_files"]}
    for name in ("rcd_development.py", "rcd_numeric_worker.py", "rcd_runtime.py",
                 "comparators.py", "ranking.py", "evaluator.py", "execution.py", "contract.py"):
        path = W / "scripts/task_e" / name
        if records.get(str(path)) != file_sha(path):
            raise ValueError("Controller source is not pinned: " + name)


def require_rcd_execution_contract(run):
    """Validate every qualification/authority identity before opening a child."""
    workspace, contract = require_run_contract(run)
    if workspace != W:
        raise ValueError("Unexpected RCD research workspace")
    _require_owned_sources(contract)
    authorization = contract["authorization"]
    if file_sha(authorization["source"]) != authorization["sha256"]:
        raise ValueError("Scoped authorization changed after contract creation")
    source_pins = {str(Path(row["path"]).resolve()): row["sha256"]
                   for row in contract["source_files"]}
    manifest = W / "baselines/task-e-source-manifest.json"
    if source_pins.get(str(manifest)) != file_sha(manifest):
        raise ValueError("RCD source manifest is not pinned among contract sources")
    pointer = contract["config"]["rcd_qualification_report"]
    report_path = read_pinned(pointer["path"], contract)
    if file_sha(report_path) != pointer["sha256"]:
        raise ValueError("Qualification report config/input pins disagree")
    read_pinned(report_path.parent / "run-contract.json", contract)
    _require_qualification(W, contract)
    return contract


def load_inputs(audit_root, contract):
    """Admit every planned case/cache before opening a numeric child."""
    audit_root = Path(audit_root).resolve()
    audit_root.relative_to(W / "results/task-e")
    audit_contract = json.loads(read_pinned(audit_root / "run-contract.json", contract).read_text(
        encoding="utf-8-sig"))
    if audit_contract["td"]["sha256"] != contract["td"]["sha256"]:
        raise ValueError("Audit belongs to a different TD revision")
    summary = json.loads(read_pinned(audit_root / "loader-summary.json", contract).read_text(
        encoding="utf-8-sig"))
    audited = summary.get("cases", [])
    if (summary.get("no_predictions") is not True or summary.get("planned") != 30
            or len(audited) != 30 or {row["case"] for row in audited} != set(DEV_IDS)):
        raise ValueError("Expected the complete preprediction development30 audit")
    admitted = []
    for case in DEV_IDS:
        handle = opaque_handle(case)
        audit_path = read_pinned(audit_root / "case-audits" / (handle + ".json"), contract)
        report = json.loads(audit_path.read_text(encoding="utf-8-sig"))
        if report.get("case") != case or report.get("handle") != handle:
            raise ValueError("Case audit identity differs from exact development allowlist")
        metadata = report["metadata"]
        if metadata.get("case") != case:
            raise ValueError("Case metadata identity differs from pinned audit")
        primary = report.get("profiles", {}).get("c1_primary", {})
        names = primary.get("service_names", [])
        if (type(names) is not list or any(type(name) is not str or not name for name in names)
                or len(names) != len(set(names))):
            raise ValueError("Malformed C1 candidate universe")
        rcd = report.get("rcd")
        entry = {"case": case, "handle": handle, "audit": report,
                 "audit_path": str(audit_path), "audit_sha256": file_sha(audit_path),
                 "values": None, "input_failure": None}
        if primary.get("status") != "MATERIALIZED" or not isinstance(rcd, dict):
            entry["input_failure"] = "AUDIT_C1_OR_RCD_INPUT_UNAVAILABLE"
            admitted.append(entry)
            continue
        numeric_path = read_pinned(audit_root / "intermediates" / handle / "rcd.npz", contract)
        audit_pins = {str(Path(row["path"]).resolve()): row["sha256"]
                      for row in report.get("numeric_files", [])}
        if audit_pins.get(str(numeric_path)) != file_sha(numeric_path):
            raise ValueError("RCD cache differs from its own audit receipt")
        with np.load(numeric_path, allow_pickle=False) as stored:
            if stored.files != ["values"]:
                raise ValueError("RCD cache must contain only values")
            values = stored["values"].copy()
        if (values.dtype.kind not in "iuf" or values.ndim != 2 or values.shape[0] != 600
                or not np.isfinite(values).all()):
            raise ValueError("RCD cache must be a finite nonobject600xM matrix")
        values = values.astype(np.float64, copy=False)
        if not np.isfinite(values).all():
            raise ValueError("RCD float64 conversion overflow")
        owners = rcd.get("owners")
        expected = {"m" + str(j) for j in range(values.shape[1])}
        if (type(owners) is not dict or set(owners) != expected
                or any(type(v) is not int or not 0 <= v < len(names) for v in owners.values())):
            raise ValueError("Exact numeric-column owner map differs from candidate universe")
        if rcd.get("audit", {}).get("eligible_columns") != values.shape[1]:
            raise ValueError("RCD eligibility count differs from numeric cache width")
        entry.update(values=values, numeric_path=str(numeric_path), numeric_sha256=file_sha(numeric_path))
        admitted.append(entry)
    if len(admitted) != 30 or {item["case"] for item in admitted} != set(DEV_IDS):
        raise ValueError("Every planned development case is required exactly once")
    return admitted


class RCDWorker:
    """One sequential process; stderr is an exclusive file, never an undrained pipe."""

    def __init__(self, run, session, *, timeout_seconds=ENGINEERING_TIMEOUT_SECONDS):
        self.run = Path(run).resolve()
        require_rcd_execution_contract(self.run)
        self.timeout_seconds = float(timeout_seconds)
        if not np.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("Worker request deadline must be positive")
        self.stderr_path = self.run / "worker-logs" / ("worker-%03d.stderr.log" % session)
        self.stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self.stderr_stream = self.stderr_path.open("xb")
        environment = dict(os.environ)
        for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
            environment.pop(key, None)
        environment.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                           NUMEXPR_NUM_THREADS="1", PYTHONUNBUFFERED="1", PYTHONHASHSEED="0")
        executable = W / "environments/task-e/rcd39/Scripts/python.exe"
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        try:
            self.process = subprocess.Popen(
                [str(executable), "-B", "-u", "-m", "scripts.task_e.rcd_numeric_worker", str(self.run)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr_stream,
                cwd=W, env=environment, **options)
        except BaseException:
            self.stderr_stream.close()
            raise
        self.closed = False
        self.raw_receipt_pending = False

    def exchange(self, request, raw_path):
        """Save exact child bytes before interpreting even malformed output."""
        line = json.dumps(request, allow_nan=False, separators=(",", ":"))
        return self.exchange_line(line, raw_path)

    def exchange_line(self, line, raw_path):
        """Line transport also permits adversarial raw-JSON synthetic fixtures."""
        if self.closed:
            raise WorkerTransportError("WORKER_CLOSED")
        if type(line) is not str or "\n" in line or "\r" in line:
            raise ValueError("Exactly one JSON transport line is required")
        payload = line.encode("utf-8") + b"\n"
        raw_path = Path(raw_path)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        # Reserve output before dispatch; a duplicate attempt cannot overwrite it.
        raw_stream = raw_path.open("xb")
        queue = Queue(maxsize=1)

        def transaction():
            raw = b""
            error = None
            try:
                self.process.stdin.write(payload)
                self.process.stdin.flush()
                raw = self.process.stdout.readline()
            except Exception as exc:
                error = type(exc).__name__
            finally:
                try:
                    raw_stream.write(raw)
                    raw_stream.flush()
                    os.fsync(raw_stream.fileno())
                except Exception as exc:
                    error = "RAW_RECEIPT_WRITE_" + type(exc).__name__
                finally:
                    raw_stream.close()
                    queue.put((raw, error))

        thread = threading.Thread(target=transaction, daemon=True)
        thread.start()
        try:
            raw, error = queue.get(timeout=self.timeout_seconds)
        except Empty:
            self.raw_receipt_pending = True
            try:
                self.process.kill()
                self.process.wait(timeout=10)
            except Exception:
                raise RawReceiptPendingError("ENGINEERING_TIMEOUT_CHILD_TEARDOWN_PENDING") from None
            thread.join(timeout=10)
            if thread.is_alive():
                raise RawReceiptPendingError("ENGINEERING_TIMEOUT_RAW_RECEIPT_PENDING") from None
            self.raw_receipt_pending = False
            raise WorkerTransportError("ENGINEERING_REQUEST_TIMEOUT_PENDING_REVIEW") from None
        if error or not raw:
            raise WorkerTransportError("WORKER_TRANSPORT_FAILURE:" + (error or "EMPTY_REPLY"))
        try:
            return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_reply_object,
                              parse_constant=_reject_reply_constant)
        except (UnicodeError, json.JSONDecodeError, ValueError):
            raise WorkerTransportError("MALFORMED_WORKER_JSON_SAVED") from None

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.raw_receipt_pending:
            # A stalled raw writer or pipe reader still owns these streams.
            # The child is dead; preserve the files and let process teardown
            # close handles rather than racing a late write or scoring it.
            self.stderr_stream.close()
            return
        try:
            if self.process.poll() is None:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=10)
        finally:
            for stream in (self.process.stdin, self.process.stdout):
                if not stream.closed:
                    stream.close()
            self.stderr_stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def _unique_reply_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate reply key")
        result[key] = value
    return result


def _reject_reply_constant(_value):
    raise ValueError("Nonfinite reply number")


def _zero_seed(seed, bins, reason):
    return {"seed": seed, "bins": bins, "status": "FAILURE", "ranks": None,
            "reason": reason, "error": None, "wall_seconds": None}


def validate_response(response, values, contract):
    if (type(response) is not dict or response.get("schema") != "TD13-RCD-NUMERIC-v1"
            or response.get("status") != "COMPLETE" or response.get("shape") != list(values.shape)
            or type(response.get("shape")) is not list
            or any(type(size) is not int for size in response["shape"])):
        raise WorkerTransportError("WORKER_RESPONSE_NOT_COMPLETE")
    expected_hash = hashlib.sha256(values.astype("<f8", copy=False).tobytes()).hexdigest()
    if response.get("input_numeric_sha256") != expected_hash:
        raise WorkerTransportError("WORKER_INPUT_ROUNDTRIP_MISMATCH")
    fidelity = response.get("fidelity", {})
    if (type(fidelity) is not dict
            or fidelity.get("report_sha256") != contract["config"]["rcd_qualification_report"]["sha256"]
            or fidelity.get("source_manifest_sha256") != contract["config"]["rcd_source_manifest_sha256"]
            or fidelity.get("worker_sha256") != file_sha(W / "scripts/task_e/rcd_numeric_worker.py")
            or fidelity.get("framework_init_executed") is not False
            or fidelity.get("method") != "RCD-RCAEval-adapted-TD12"):
        raise WorkerTransportError("WORKER_QUALIFICATION_IDENTITY_MISMATCH")
    results = response.get("results")
    if type(results) is not list or len(results) != 9:
        raise WorkerTransportError("MISSING_PLANNED_SEED_BIN_OUTPUTS")
    for item, config in zip(results, CONFIGS):
        if (type(item) is not dict
                or any(type(item.get(key)) is not int or item[key] != value for key, value in config.items())):
            raise WorkerTransportError("SEED_BIN_OUTPUT_ORDER_MISMATCH")
        if item.get("method") != "RCD-RCAEval-adapted-TD12":
            raise WorkerTransportError("UNEXPECTED_WORKER_METHOD")
        elapsed = item.get("wall_seconds")
        if type(elapsed) not in (int, float) or not np.isfinite(elapsed) or elapsed < 0:
            raise WorkerTransportError("INVALID_WORKER_COST")
        if item.get("status") == "FAILURE":
            if (item.get("ranks") is not None or item.get("metric_rank_indices") is not None
                    or type(item.get("reason")) is not str or not item["reason"]):
                raise WorkerTransportError("INVALID_FAILURE_OUTPUT")
        elif item.get("status") == "SUCCESS":
            ranks = item.get("ranks")
            if (type(ranks) is not list or any(type(key) is not str or not key for key in ranks)
                    or len(ranks) != len(set(ranks))):
                raise WorkerTransportError("INVALID_METRIC_RANK_OUTPUT")
            known = {"m" + str(index): index for index in range(values.shape[1])}
            indices = item.get("metric_rank_indices")
            if (type(indices) is not list
                    or any(type(index) is not int or not 0 <= index < values.shape[1] for index in indices)
                    or indices != [known[key] for key in ranks if key in known]):
                raise WorkerTransportError("INVALID_METRIC_RANK_INDICES")
            if (item.get("reason") is not None or item.get("error") is not None
                    or item.get("unknown_metric_keys") != [key for key in ranks if key not in known]):
                raise WorkerTransportError("INVALID_SUCCESS_COVERAGE")
        else:
            raise WorkerTransportError("UNKNOWN_SEED_STATUS")
    return results


def evaluate_seeds(results, audit):
    """Called only after exact raw predictions have been persisted."""
    names = audit.get("profiles", {}).get("c1_primary", {}).get("service_names", [])
    root = audit["metadata"]["root_cause_service"]
    root_index = names.index(root) if root in names else None
    owners = audit.get("rcd", {}).get("owners", {})
    evaluated = []
    for result in results:
        failed = result["status"] != "SUCCESS"
        scores, mapping = (np.zeros(len(names)), {"unknown_metric_keys": [], "ranked_services": 0})
        if not failed:
            scores, mapping = service_scores_from_metric_ranks(result["ranks"], owners, len(names))
        evaluated.append({**result, "mapping": mapping, "service_scores": scores.tolist(),
                          "metrics": tie_metrics(scores, root_index, failed=failed)})
    per_bin = {}
    for bins in BINS:
        group = [item for item in evaluated if item["bins"] == bins]
        if len(group) != 3 or {item["seed"] for item in group} != set(SEEDS):
            raise ValueError("All three seeds are required in each planned bin denominator")
        per_bin[str(bins)] = {
            "mean": {key: float(np.mean([item["metrics"][key] for item in group])) for key in METRICS},
            "seed_variation": {key: {"minimum": min(item["metrics"][key] for item in group),
                                      "maximum": max(item["metrics"][key] for item in group),
                                      "population_sd": float(np.std([item["metrics"][key] for item in group]))}
                               for key in METRICS},
            "success_seeds": sum(item["status"] == "SUCCESS" for item in group),
            "failure_seeds": sum(item["status"] != "SUCCESS" for item in group),
            "valid_empty_seeds": sum(item["status"] == "SUCCESS" and item["ranks"] == [] for item in group),
            "cost_seconds": sum(item["wall_seconds"] or 0. for item in group),
            "unknown_key_count": sum(len(item["mapping"]["unknown_metric_keys"]) for item in group),
        }
    return {"seeds": evaluated, "bins": per_bin, "candidate_count": len(names),
            "root_in_candidate": root_index is not None}


def summarize_cases(cases):
    if set(cases) != set(DEV_IDS):
        raise ValueError("No case exclusion from development30 summary")
    aggregates, groups = {}, {}
    for bins in BINS:
        key = str(bins)
        aggregates[key] = {"planned_cases": 30, "planned_seed_runs": 90,
                           "mean": {metric: float(np.mean([row["bins"][key]["mean"][metric]
                                                           for row in cases.values()])) for metric in METRICS},
                           "success_seed_runs": sum(row["bins"][key]["success_seeds"] for row in cases.values()),
                           "failure_seed_runs": sum(row["bins"][key]["failure_seeds"] for row in cases.values()),
                           "cost_seconds": sum(row["bins"][key]["cost_seconds"] for row in cases.values())}
        groups[key] = {}
        for dimension, index in (("root", 0), ("fault", 1), ("cell", None)):
            labels = sorted({tuple(row["cell"]) if index is None else row["cell"][index]
                             for row in cases.values()})
            grouping = []
            for label in labels:
                selected = [case for case, row in cases.items()
                            if (tuple(row["cell"]) if index is None else row["cell"][index]) == label]
                grouping.append({"label": label, "cases": selected, "planned_cases": len(selected),
                                 "mean": {metric: float(np.mean([cases[case]["bins"][key]["mean"][metric]
                                                                 for case in selected])) for metric in METRICS}})
            groups[key][dimension] = grouping
    return {"summary": aggregates, "groups": groups}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--audit-root", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    contract = require_rcd_execution_contract(run)
    if "development" not in contract.get("stage", "").lower():
        raise ValueError("Driver requires an explicit development run contract")
    records = load_inputs(args.audit_root, contract)
    save_json(run / "rcd-admission.json", {
        "planned_cases": list(DEV_IDS), "configs": CONFIGS,
        "inputs": [{key: value for key, value in record.items() if key not in ("values", "audit")}
                   for record in records],
        "timeout_seconds": ENGINEERING_TIMEOUT_SECONDS,
        "timeout_status": "Engineering per-case nine-config request limit; a hit is invalid execution pending timing-rule review",
        "qualification_report": contract["config"]["rcd_qualification_report"]})
    cases, invalid, worker, session = {}, [], None, 0
    try:
        for count, record in enumerate(records, 1):
            start = time.perf_counter()
            case, handle, report = record["case"], record["handle"], record["audit"]
            raw_path = run / "raw-responses" / (handle + ".jsonl")
            raw_artifacts = []
            transport_failure = record["input_failure"]
            if transport_failure:
                results = [_zero_seed(config["seed"], config["bins"], transport_failure) for config in CONFIGS]
                input_receipt = run / "raw-responses" / (handle + ".input-failure.json")
                save_json(input_receipt, {
                    "source": "pinned audit", "reason": transport_failure, "planned_results": results,
                    "numeric_worker_invoked": False})
                raw_artifacts.append(input_receipt)
            else:
                try:
                    if worker is None:
                        session += 1
                        worker = RCDWorker(run, session)
                    response = worker.exchange({"values": record["values"].tolist(), "configs": CONFIGS}, raw_path)
                    results = validate_response(response, record["values"], contract)
                except RawReceiptPendingError as exc:
                    failure(run, "rcd_raw_receipt_pending", case, exc)
                    save_json(run / "raw-receipt-pending.json", {
                        "status": "INVALID_RUN_EXECUTION_REVIEW_REQUIRED", "case": case,
                        "worker_session": session, "raw_path": str(raw_path),
                        "reason": str(exc), "predictions_evaluated": False,
                        "action": "Preserve this attempt; diagnose pending raw writer before a new contract/run"})
                    raise
                except Exception as exc:
                    transport_failure = str(exc)
                    invalid.append(failure(run, "rcd_execution", case, exc))
                    results = [_zero_seed(config["seed"], config["bins"], "EXECUTION_FAILURE:" + type(exc).__name__)
                               for config in CONFIGS]
                    failure_receipt = run / "raw-responses" / (handle + ".transport-failure.json")
                    save_json(failure_receipt, {
                        "reason": transport_failure, "planned_results": results, "worker_session": session,
                        "stderr_path": str(worker.stderr_path) if worker else None,
                        "existing_raw_reply": str(raw_path) if raw_path.exists() else None})
                    raw_artifacts.append(failure_receipt)
                    if worker is not None:
                        worker.close()
                        worker = None
                if raw_path.exists():
                    raw_artifacts.insert(0, raw_path)
            # Every success, input failure and transport failure is sealed before
            # translating a metric rank into an owner or opening evaluator GT.
            save_json(run / "seals" / (handle + ".json"), {
                "artifacts": [{"path": str(path), "sha256": file_sha(path), "bytes": path.stat().st_size}
                              for path in raw_artifacts],
                "before_owner_mapping_and_evaluation": True, "worker_session": session,
                "input_sha256": record.get("numeric_sha256"),
                "audit_sha256": record["audit_sha256"], "execution_failure": transport_failure})
            evaluated = evaluate_seeds(results, report)
            entry = {"case": case, "handle": handle,
                     "cell": [report["metadata"]["root_cause_service"], report["metadata"]["fault"]],
                     "input_failure": record["input_failure"], "execution_failure": transport_failure,
                     "input_coverage": report.get("rcd", {}).get("audit"),
                     "request_wall_seconds": time.perf_counter() - start, **evaluated}
            cases[case] = entry
            save_json(run / "case-results" / (handle + ".json"), entry)
            print("RCD development %d/30 %s %.2fs" % (count, handle, entry["request_wall_seconds"]), flush=True)
    finally:
        if worker is not None:
            worker.close()
    save_json(run / "rcd-development-results.json", {
        "schema": SCHEMA, "scope": "AUTHORIZED DEVELOPMENT30 ONLY; not final evaluation",
        "status": "INVALID_RUN_EXECUTION_REVIEW_REQUIRED" if invalid else "COMPLETED_DEVELOPMENT_EXECUTION",
        "primary_bins": 5, "sensitivity_bins": [3, 7], "seeds": list(SEEDS),
        "aggregation": "all three per-seed metrics; failed seeds0; no best seed; all30 cases retained",
        "timeout_seconds": ENGINEERING_TIMEOUT_SECONDS, "execution_failures": invalid,
        "cases": cases, **summarize_cases(cases)})
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
