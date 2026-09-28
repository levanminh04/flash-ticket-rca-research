"""Actual isolated-process RCD protocol plus independent evaluator fixtures.

No fixture executes until the coordinator supplies a contract with successful
real RCD qualification pin and unchanged source snapshots. No corpus data read.
"""
from __future__ import annotations

import json
import copy
import hashlib
from pathlib import Path
import sys
import time
import unittest

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.execution import file_sha, save_json
from scripts.task_e.rcd_development import (CONFIGS, RCDWorker, WorkerTransportError,
    evaluate_seeds, validate_response, require_rcd_execution_contract)
from scripts.task_e.rcd_numeric_worker import RequestError, parse_request

RUN = None
CONTRACT = None


def grid():
    base = np.arange(300, dtype=np.float64) % 11 / 11
    return np.c_[np.r_[base, base + 30], np.r_[base, base]]


class RCDWorkerFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if RUN is None or CONTRACT is None:
            raise RuntimeError("A new coordinator contract must precede every fixture")
        require_rcd_execution_contract(RUN)

    def test_actual_worker_protocol_and_metadata_exclusion(self):
        self.assertIsNotNone(RUN, "Coordinator contract must precede execution")
        request = {"values": grid().tolist(), "configs": CONFIGS}
        self.assertEqual(set(request), {"values", "configs"})
        with RCDWorker(RUN, 1) as worker:
            raw = RUN / "worker-fixtures" / "valid.jsonl"
            response = worker.exchange(request, raw)
            self.assertTrue(raw.is_file())
            self.assertEqual(json.loads(raw.read_text()), response)
            results = validate_response(response, grid(), CONTRACT)
            self.assertEqual(len(results), 9)
            for result in results:
                self.assertEqual(result["status"], "SUCCESS", result)
                self.assertEqual(result["ranks"], ["m0"])
                self.assertEqual(result["metric_rank_indices"], [0])
            forbidden = {**request, "service_names": ["forbidden-controller-name"]}
            rejected = worker.exchange(forbidden, RUN / "worker-fixtures" / "rejected-name-field.jsonl")
            self.assertEqual(rejected["status"], "REQUEST_FAILURE")
            self.assertEqual(rejected["reason"], "request_fields_must_be_values_and_configs")
            # A rejected request must not poison a subsequent valid transport.
            again = worker.exchange(request, RUN / "worker-fixtures" / "valid-repeat.jsonl")
            repeated = validate_response(again, grid(), CONTRACT)
            self.assertEqual([result["ranks"] for result in results], [result["ranks"] for result in repeated])
            self.assertEqual(response["input_numeric_sha256"], again["input_numeric_sha256"])
            save_json(RUN / "worker-fixtures" / "roundtrip-receipt.json", {
                "real_process": True, "all_nine_configs": True, "bad_field_rejected": True,
                "only_request_fields": sorted(request), "stderr_path": str(worker.stderr_path),
                "qualification_sha256": response["fidelity"]["report_sha256"],
                "raw_response_sha256": file_sha(raw)})

    def test_actual_worker_rejects_untrusted_malformed_and_out_of_range(self):
        request = {"values": grid().tolist(), "configs": CONFIGS}
        invalid = [("malformed", "{", "invalid_json"),
                   ("duplicate", '{"values":[],"values":[],"configs":[]}', "duplicate_json_key"),
                   ("nan", '{"values":[NaN],"configs":[]}', "nonfinite_json_number"),
                   ("overflow", json.dumps({**request, "values": [[10 ** 400]] * 600}),
                    "nonfinite_or_out_of_float64_range")]
        for field in ("root_cause_service", "inject_time", "path", "metadata", "owners",
                      "service_names", "metric_names", "old_predictions"):
            invalid.append((field, json.dumps({**request, field: "must-not-reach-model"}),
                            "request_fields_must_be_values_and_configs"))
        invalid.extend([
            ("missing-config", json.dumps({**request, "configs": CONFIGS[:-1]}),
             "all_nine_registered_seed_bin_configs_required"),
            ("duplicate-config", json.dumps({**request, "configs": [CONFIGS[0]] * 9}),
             "all_nine_configs_must_occur_once"),
            ("unregistered-seed", json.dumps({**request, "configs": [{"seed": 423, "bins": 5}] + CONFIGS[1:]}),
             "unregistered_seed_or_bins"),
            ("string-value", json.dumps({**request, "values": [["root-name"]] * 600}),
             "grid_requires_numbers_without_objects_strings_or_booleans"),
        ])
        receipts = []
        with RCDWorker(RUN, 2) as worker:
            for name, line, reason in invalid:
                with self.subTest(name=name):
                    raw = RUN / "worker-fixtures" / ("invalid-" + name + ".jsonl")
                    reply = worker.exchange_line(line, raw)
                    self.assertEqual(reply, {"schema": "TD13-RCD-NUMERIC-v1",
                                            "status": "REQUEST_FAILURE", "reason": reason, "results": None})
                    receipts.append({"name": name, "reason": reason, "raw_sha256": file_sha(raw)})
        save_json(RUN / "worker-fixtures" / "rejection-receipt.json", {
            "real_process": True, "rejections": receipts,
            "model_predictions_for_rejected_requests": False})

    def test_actual_worker_valid_empty_rank_and_no_eligible_columns(self):
        base = np.arange(300, dtype=np.float64) % 11 / 11
        identical = np.c_[np.r_[base, base], np.r_[base, base]]
        with RCDWorker(RUN, 3) as worker:
            raw = RUN / "worker-fixtures" / "empty-rank.jsonl"
            response = worker.exchange({"values": identical.tolist(), "configs": CONFIGS}, raw)
            results = validate_response(response, identical, CONTRACT)
            self.assertEqual(len(results), 9)
            for result in results:
                self.assertEqual(result["status"], "SUCCESS", result)
                self.assertEqual(result["ranks"], [])
                self.assertEqual(result["metric_rank_indices"], [])
            empty = np.empty((600, 0), dtype=np.float64)
            raw_zero = RUN / "worker-fixtures" / "no-eligible-columns.jsonl"
            response_zero = worker.exchange({"values": empty.tolist(), "configs": CONFIGS}, raw_zero)
            zero_results = validate_response(response_zero, empty, CONTRACT)
            self.assertEqual(len(zero_results), 9)
            for result in zero_results:
                self.assertEqual(result["status"], "FAILURE", result)
                self.assertEqual(result["reason"], "no_eligible_columns")
                self.assertIsNone(result["ranks"])
                self.assertIsNone(result["metric_rank_indices"])
            save_json(RUN / "worker-fixtures" / "empty-receipt.json", {
                "real_process": True, "all_nine_valid_empty": True,
                "all_nine_no_eligible_failure": True,
                "empty_rank_raw_sha256": file_sha(raw), "no_eligible_raw_sha256": file_sha(raw_zero)})

    def test_strict_json_shape_and_config_validation(self):
        request = {"values": grid().tolist(), "configs": CONFIGS}
        numeric, configs = parse_request(json.dumps(request))
        self.assertEqual(len(numeric), 600)
        self.assertEqual(len(configs), 9)
        mutations = [
            {**request, "path": "forbidden"},
            {**request, "values": request["values"][:-1]},
            {**request, "configs": CONFIGS[:-1]},
            {**request, "configs": [CONFIGS[0]] * 9},
            {**request, "configs": [{"seed": 423, "bins": 5}] + CONFIGS[1:]},
            {**request, "configs": [{"seed": 420, "bins": True}] + CONFIGS[1:]},
            {**request, "configs": [{"seed": 420, "bins": 5, "label": 0}] + CONFIGS[1:]},
            {**request, "values": [[True, 0]] * 600},
            {**request, "values": [["1", 0]] * 600},
            {**request, "values": [[None, 0]] * 600},
            {**request, "values": [[{}, 0]] * 600},
            {**request, "values": [[10 ** 400, 0]] * 600},
            {**request, "values": [[0], [0, 0]] * 300},
        ]
        for modified in mutations:
            with self.subTest(fields=sorted(modified)), self.assertRaises(RequestError):
                parse_request(json.dumps(modified))
        for text in ('{', '[]', 'null', '{"values":[],"values":[],"configs":[]}',
                     '{"values": [NaN], "configs": []}', '{"values": [Infinity], "configs": []}'):
            with self.assertRaises(RequestError):
                parse_request(text)

    def test_response_rejects_malformed_status_cost_and_rank_indices(self):
        values = grid()
        response = {"schema": "TD13-RCD-NUMERIC-v1", "status": "COMPLETE", "shape": list(values.shape),
                    "input_numeric_sha256": hashlib.sha256(values.astype("<f8").tobytes()).hexdigest(),
                    "fidelity": {"report_sha256": CONTRACT["config"]["rcd_qualification_report"]["sha256"],
                                 "source_manifest_sha256": CONTRACT["config"]["rcd_source_manifest_sha256"],
                                 "worker_sha256": file_sha(W / "scripts/task_e/rcd_numeric_worker.py"),
                                 "method": "RCD-RCAEval-adapted-TD12", "framework_init_executed": False},
                    "results": [{**config, "method": "RCD-RCAEval-adapted-TD12", "status": "SUCCESS",
                                 "ranks": ["m0"], "metric_rank_indices": [0], "unknown_metric_keys": [],
                                 "reason": None, "error": None, "wall_seconds": 1.} for config in CONFIGS]}
        self.assertEqual(len(validate_response(response, values, CONTRACT)), 9)
        bad_result_fields = [
            {"seed": 423}, {"seed": 420.0}, {"status": "UNKNOWN"}, {"wall_seconds": -1.},
            {"wall_seconds": float("nan")}, {"wall_seconds": True},
            {"ranks": ["m0", "m0"]}, {"ranks": [None]}, {"ranks": float("nan")},
            {"metric_rank_indices": [-1]}, {"metric_rank_indices": [2]},
            {"metric_rank_indices": [False]}, {"metric_rank_indices": [0.0]},
            {"metric_rank_indices": [1]}, {"metric_rank_indices": [0, 0]},
            {"unknown_metric_keys": ["m0"]}, {"reason": "not-a-success"},
            {"status": "FAILURE", "ranks": None, "metric_rank_indices": [0], "reason": "failure"},
        ]
        for fields in bad_result_fields:
            changed = copy.deepcopy(response)
            changed["results"][0].update(fields)
            with self.subTest(fields=fields), self.assertRaises(WorkerTransportError):
                validate_response(changed, values, CONTRACT)
        for fields in ({"results": []}, {"results": [None] * 9}, {"shape": [600, True]},
                       {"fidelity": None}, {"input_numeric_sha256": "wrong"}):
            with self.subTest(fields=fields), self.assertRaises(WorkerTransportError):
                validate_response({**response, **fields}, values, CONTRACT)
        # Unknown opaque keys are an explicit coverage diagnostic, as TD §6
        # requires; they cannot fabricate a service or a numeric rank index.
        unknown = copy.deepcopy(response)
        unknown["results"][0].update(ranks=["unknown", "m0"], unknown_metric_keys=["unknown"])
        self.assertEqual(validate_response(unknown, values, CONTRACT)[0]["metric_rank_indices"], [0])

    def test_service_first_occurrence_unknowns_empty_tie_and_failure0(self):
        audit = {"profiles": {"c1_primary": {"service_names": ["a", "b", "c"]}},
                 "metadata": {"root_cause_service": "a"},
                 "rcd": {"owners": {"m0": 0, "m1": 0, "m2": 2}}}
        results = []
        for config in CONFIGS:
            seed = config["seed"]
            results.append({**config, "status": "FAILURE" if seed == 422 else "SUCCESS",
                            "ranks": None if seed == 422 else ([] if seed == 421 else ["unknown", "m2", "m0", "m1"]),
                            "reason": "fixture_failure" if seed == 422 else None,
                            "wall_seconds": 1.})
        outcome = evaluate_seeds(results, audit)
        # seed420: root service second => RR1/2. seed421: uniform tie of3
        # => (1+1/2+1/3)/3=11/18. seed422 fails =>0. Mean =10/27.
        for bins in (3, 5, 7):
            row = outcome["bins"][str(bins)]
            self.assertAlmostEqual(row["mean"]["rr"], 10 / 27)
            self.assertEqual(row["failure_seeds"], 1)
            self.assertEqual(row["valid_empty_seeds"], 1)
            self.assertEqual(row["unknown_key_count"], 1)
        ranked = outcome["seeds"][0]
        self.assertEqual(ranked["service_scores"], [1., 0., 2.])
        self.assertEqual(ranked["mapping"]["ranked_services"], 2)
        missing_root = {**audit, "metadata": {"root_cause_service": "absent"}}
        missing = evaluate_seeds(results, missing_root)
        self.assertFalse(missing["root_in_candidate"])
        self.assertTrue(all(row["mean"]["rr"] == 0 for row in missing["bins"].values()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: test_rcd_worker.py NEW_COORDINATOR_RUN")
    RUN = Path(sys.argv[1]).resolve()
    CONTRACT = require_rcd_execution_contract(RUN)
    if any((RUN / name).exists() for name in ("worker-fixtures", "worker-logs", "rcd-worker-fixture-report.json")):
        raise SystemExit("Never reuse a worker fixture attempt; create a new coordinator contract")
    pins = {str(Path(row["path"]).resolve()): row["sha256"] for row in CONTRACT["source_files"]}
    for source in (Path(__file__).resolve(), W / "scripts/task_e/rcd_development.py",
                   W / "scripts/task_e/rcd_numeric_worker.py", W / "scripts/task_e/evaluator.py"):
        if pins.get(str(source)) != file_sha(source):
            raise SystemExit("Fixture/controller/worker/evaluator source is not pinned")
    started = time.perf_counter()
    outcome = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    save_json(RUN / "rcd-worker-fixture-report.json", {
        "tests_run": outcome.testsRun, "passed": outcome.wasSuccessful(),
        "failures": [{"test": str(t), "traceback": e} for t, e in outcome.failures],
        "errors": [{"test": str(t), "traceback": e} for t, e in outcome.errors],
        "seconds": time.perf_counter() - started, "scope": "SYNTHETIC_ONLY; no corpus data"})
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
