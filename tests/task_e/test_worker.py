"""Numeric process/cache/firewall checks, executed only with a saved contract.

Fixtures use synthetic arrays and temporary cache files. No dataset, metadata,
labels or network source is opened. The child is a real separate Python process;
the checks do not claim a hostile-code OS sandbox or data-semantic truth oracle.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.boundary import (CacheIdentityError, NumericWorker, WorkerError,
                                     cache_identity, read_numeric_cache, write_numeric_cache)
from scripts.task_e.worker import (NumericSession, ProtocolError, decode_message,
                                   encode_message, validate_request)


def inputs(nodes=2):
    warmup = np.ones((36, nodes, 1), dtype=np.float64)
    adj = np.zeros((nodes, nodes), dtype=bool)
    for index in range(nodes - 1):
        adj[index, index + 1] = True
    return warmup, adj, np.array([0], dtype=np.int64), np.ones(nodes, dtype=bool)


def request():
    warmup, adj, types, mask = inputs()
    return {"op": "fit_c5", "warmup": warmup, "adj": adj, "channel_types": types,
            "fit_service_mask": mask, "configs": [{"arm": "G"}]}


def identity(**changes):
    params = {"source_hashes": {"metrics": "a" * 64, "traces": "b" * 64, "logs": "MISSING"},
              "td_hash": "c" * 64, "code_hashes": {"loader": "d" * 64, "detector": "e" * 64},
              "config": {"bin_seconds": 5, "fit_bins": 24, "cal_bins": 12},
              "profile": "TD13-C5-EVENT-TIME", "cutoff": 180}
    params.update(changes)
    return cache_identity(**params)


def equal_outputs(test, first, second):
    for key in ("score", "endpoint", "start", "scored_channels", "tv_score", "local_magnitude"):
        np.testing.assert_equal(first[key], second[key])
    for key in ("residuals", "errors", "predictions", "target_mask", "z", "tv_channels", "tv_edge_counts"):
        np.testing.assert_array_equal(first[key], second[key])
    test.assertEqual(first.get("tv_failure"), second.get("tv_failure"))


class StrictProtocolChecks(unittest.TestCase):
    def test_forbidden_labels_paths_tau_epochs_names_and_extra_fields(self):
        for field, value in (("label", 1), ("root", "service-a"), ("fault", "cpu"),
                             ("path", "answer-bearing/path"), ("tau", 720),
                             ("epoch", 1_700_000_000), ("service_names", ["answer"]),
                             ("metadata", {"answer": 0})):
            with self.subTest(field=field):
                changed = {**request(), field: value}
                with self.assertRaises(ProtocolError):
                    validate_request(changed)
                with self.assertRaises(ProtocolError):
                    NumericSession().dispatch(changed)

    def test_nested_configuration_cannot_smuggle_metadata(self):
        for field in ("label", "path", "tau", "case_id", "root"):
            changed = request()
            changed["configs"] = [{"arm": "G", field: "hidden"}]
            with self.assertRaises(ValueError):
                validate_request(changed)

    def test_objects_strings_infinite_values_and_nonboolean_masks_are_rejected(self):
        for value in (np.ones((36, 2, 1), dtype=object),
                      np.full((36, 2, 1), "10"), np.full((36, 2, 1), np.inf)):
            with self.subTest(dtype=value.dtype):
                with self.assertRaises(ProtocolError):
                    validate_request({**request(), "warmup": value})
        with self.assertRaises(ProtocolError):
            validate_request({**request(), "fit_service_mask": np.ones(2)})

    def test_future_suffix_and_mixed_prefix_grids_are_rejected(self):
        with self.assertRaises(ProtocolError):
            validate_request({**request(), "warmup": np.ones((37, 2, 1))})
        with self.assertRaises(ProtocolError):
            validate_request({**request(), "configs": [{}, {"fit_bins": 32, "cal_bins": 16}]})

    def test_wire_roundtrip_never_needs_pickle_and_keeps_missing_mask(self):
        msg = request()
        msg["warmup"][3, 0, 0] = np.nan
        restored = decode_message(encode_message(msg))
        validate_request(restored)
        np.testing.assert_array_equal(msg["warmup"], restored["warmup"])
        self.assertEqual(restored["configs"], msg["configs"])
        with self.assertRaises(ProtocolError):
            encode_message({"values": np.array([object()], dtype=object)})

    def test_worker_import_source_has_no_controller_loader_evaluator_or_cache(self):
        tree = ast.parse((W / "scripts/task_e/worker.py").read_text(encoding="utf-8"))
        imported = []
        for statement in ast.walk(tree):
            if isinstance(statement, ast.ImportFrom):
                imported.append(statement.module or "")
            elif isinstance(statement, ast.Import):
                imported.extend(alias.name for alias in statement.names)
        forbidden = ("loader", "replay", "contract", "boundary", "evaluator", "calibration", "acquire")
        self.assertFalse(any(name.startswith("scripts.task_e.") and
                             name.rsplit(".", 1)[-1] in forbidden for name in imported))


class ActualProcessChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.worker = NumericWorker(timeout_seconds=60)

    @classmethod
    def tearDownClass(cls):
        cls.worker.close()

    def test_child_is_distinct_process_and_has_no_controller_imports(self):
        self.assertNotEqual(self.worker.pid, os.getpid())
        result = self.worker.ping()
        self.assertIn("scripts.task_e.detection", result["project_modules"])
        for name in ("boundary", "loader", "replay", "evaluator", "contract", "calibration", "acquire"):
            self.assertNotIn("scripts.task_e." + name, result["project_modules"])
        self.assertIn("NOT_HOSTILE_OS_SANDBOX", result["isolation"])

    def test_child_independently_rejects_bad_fields_before_fit(self):
        # Bypass the parent's validator deliberately to exercise the child guard.
        bad = {**request(), "tau": 720}
        payload = encode_message(bad)
        self.worker.process.stdin.write(struct.pack("!Q", len(payload)))
        self.worker.process.stdin.write(payload)
        self.worker.process.stdin.flush()
        response = self.worker._receive()
        self.assertFalse(response["ok"])
        self.assertEqual(response["error_type"], "ProtocolError")

    def test_constant_prefix_has_exact_analytic_normal_score(self):
        warmup, adj, types, mask = inputs()
        fitted = self.worker.fit_c5(warmup, adj, types, mask, [{"arm": "G"}])
        frozen = fitted["models"][0]
        self.assertEqual(fitted["next_bin_index"], 36)
        np.testing.assert_array_equal(frozen["model_mask"], np.ones((2, 1), dtype=bool))
        np.testing.assert_array_equal(frozen["coefficients"], np.zeros((2, 1, 5)))
        np.testing.assert_array_equal(frozen["centers"], np.ones((2, 1)))
        np.testing.assert_array_equal(frozen["scales"], np.full((2, 1), .01))
        result = self.worker.score_c5(np.ones((2, 1)), 36)["results"][0]
        self.assertEqual(result["score"], 0.)
        self.assertEqual(result["endpoint"], 185)
        self.assertEqual(result["tv_score"], 0.)
        self.assertEqual(result["scored_channels"], 2)

    def test_spike_analytic_residual_and_missing_current_masks(self):
        self.worker.fit_c5(*inputs(), [{"arm": "L"}])
        result = self.worker.score_c5(np.array([[1.1], [np.nan]]), 36)["results"][0]
        self.assertAlmostEqual(result["score"], 1000., places=8)
        self.assertAlmostEqual(result["z"][0, 0], 10., places=10)
        np.testing.assert_array_equal(result["target_mask"], [[True], [False]])
        self.assertTrue(np.isnan(result["predictions"][1, 0]))
        self.assertTrue(np.isnan(result["tv_score"]))

    def test_only_one_bin_and_strict_next_relative_index_are_admitted(self):
        self.worker.fit_c5(*inputs(), [{}])
        for index in (35, 37, 1_700_000_000):
            with self.assertRaises(WorkerError):
                self.worker.score_c5(np.ones((2, 1)), index)
        with self.assertRaises(ProtocolError):
            self.worker.score_c5(np.ones((2, 2, 1)), 36)
        correct = self.worker.score_c5(np.ones((2, 1)), 36)
        self.assertEqual(correct["results"][0]["endpoint"], 185)
        with self.assertRaises(WorkerError):
            self.worker.score_c5(np.ones((2, 1)), 36)

    def test_multiconfig_states_share_exact_target_ids_and_frozen_values(self):
        configs = [{"arm": arm, "modalities": modality, "lambda": penalty}
                   for arm in ("G", "L", "ALL") for modality in ("MT", "MTL")
                   for penalty in (.1, 1., 10.)]
        fitted = self.worker.fit_c5(*inputs(), configs)
        self.assertEqual(len(fitted["models"]), 18)
        for model in fitted["models"]:
            np.testing.assert_array_equal(model["E"], fitted["models"][0]["E"])
            np.testing.assert_array_equal(model["fit_target_mask"], fitted["models"][0]["fit_target_mask"])
            np.testing.assert_array_equal(model["calibration_target_mask"], fitted["models"][0]["calibration_target_mask"])
        scored = self.worker.score_c5(np.ones((2, 1)), 36)
        self.assertEqual(len(scored["results"]), 18)
        self.assertTrue(all(result["score"] == 0. for result in scored["results"]))

    def test_fresh_process_repeat_and_unsent_future_have_identical_prefix_output(self):
        first_fit = self.worker.fit_c5(*inputs(), [{}])
        first = self.worker.score_c5(np.ones((2, 1)), 36)["results"][0]
        arbitrary_future = np.full((250, 2, 1), 999.)
        self.assertEqual(arbitrary_future.shape[0], 250)  # never sent to child
        with NumericWorker(timeout_seconds=60) as other:
            second_fit = other.fit_c5(*inputs(), [{}])
            second = other.score_c5(np.ones((2, 1)), 36)["results"][0]
        equal_outputs(self, first, second)
        self.assertEqual(first_fit["models"][0]["frozen_numeric_sha256"],
                         second_fit["models"][0]["frozen_numeric_sha256"])

    def test_joint_permutation_preserves_mapped_C5_results(self):
        warmup, adj, types, mask = inputs(3)
        current = np.array([[1.1], [1.], [1.2]])
        self.worker.fit_c5(warmup, adj, types, mask, [{"arm": "G"}])
        original = self.worker.score_c5(current, 36)["results"][0]
        order = np.array([2, 0, 1])
        self.worker.fit_c5(warmup[:, order], adj[np.ix_(order, order)], types, mask[order], [{"arm": "G"}])
        mapped = self.worker.score_c5(current[order], 36)["results"][0]
        self.assertEqual(original["score"], mapped["score"])
        for field in ("errors", "predictions", "target_mask", "z", "residuals"):
            np.testing.assert_array_equal(mapped[field], original[field][order])

    def test_C1_and_batch_rank_have_closed_form_expected_values(self):
        ref = np.full((2, 1, 30), 10.)
        query = ref.copy()
        query[1] = 11.
        adj = np.array([[False, True], [False, False]])
        result = self.worker.c1(ref, query, adj, np.array([0]), {},
                                [{"operator": "ppr", "direction": "reverse", "damping": .85}])
        np.testing.assert_allclose(result["evidence"]["local"], [0., 10.])
        np.testing.assert_allclose(result["rankings"][0]["scores"], [.85, .15])
        batch = self.worker.rank(result["evidence"]["local"], np.stack([adj, np.zeros_like(adj)]),
                                 [{"damping": .85}])["rankings"]
        np.testing.assert_allclose(batch[0][0]["scores"], [.85, .15])
        np.testing.assert_allclose(batch[1][0]["scores"], [0., 1.])


class ExactCacheChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="td13-numeric-cache-")
        self.root = Path(self.temporary.name)
        warmup, adj, types, mask = inputs()
        self.arrays = {"warmup": warmup, "adj": adj, "channel_types": types, "fit_service_mask": mask}

    def tearDown(self):
        self.temporary.cleanup()

    def test_roundtrip_and_repeat_write_preserve_exact_arrays(self):
        ident = identity()
        first = write_numeric_cache(self.root, ident, self.arrays)
        second = write_numeric_cache(self.root, ident, self.arrays)
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        restored = read_numeric_cache(self.root, ident)
        for key in self.arrays:
            np.testing.assert_array_equal(restored[key], self.arrays[key])

    def test_profile_source_td_code_config_and_cutoff_each_change_identity(self):
        original = identity()
        changed = [identity(profile="TD13-C1-MT"), identity(cutoff=185),
                   identity(source_hashes={"metrics": "f" * 64}), identity(td_hash="f" * 64),
                   identity(code_hashes={"loader": "f" * 64}), identity(config={"bin_seconds": 10})]
        self.assertTrue(all(item["key"] != original["key"] for item in changed))
        write_numeric_cache(self.root, original, self.arrays)
        for item in changed:
            with self.assertRaises(FileNotFoundError):
                read_numeric_cache(self.root, item)

    def test_stale_manifest_wrong_bytes_and_numeric_tamper_are_rejected(self):
        ident = identity()
        receipt = write_numeric_cache(self.root, ident, self.arrays)
        path = Path(receipt["manifest_path"])
        saved = path.read_text(encoding="utf-8")
        manifest = json.loads(saved)
        manifest["identity"]["cutoff"] = 185
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(CacheIdentityError):
            read_numeric_cache(self.root, ident)
        path.write_text(saved, encoding="utf-8")
        data = Path(receipt["data_path"])
        with data.open("ab") as out:
            out.write(b"tamper")
        with self.assertRaises(CacheIdentityError):
            read_numeric_cache(self.root, ident)

    def test_same_identity_cannot_overwrite_different_numeric_values(self):
        ident = identity()
        write_numeric_cache(self.root, ident, self.arrays)
        changed = {**self.arrays, "warmup": self.arrays["warmup"] + 1}
        with self.assertRaises(CacheIdentityError):
            write_numeric_cache(self.root, ident, changed)

    def test_object_cache_and_absent_provenance_are_rejected(self):
        with self.assertRaises(CacheIdentityError):
            write_numeric_cache(self.root, identity(), {"objects": np.array(["path"], dtype=object)})
        with self.assertRaises(CacheIdentityError):
            identity(source_hashes={})
        with self.assertRaises(CacheIdentityError):
            identity(code_hashes={})

    def test_raw_and_cache_actual_process_outputs_are_identical(self):
        ident = identity()
        write_numeric_cache(self.root, ident, self.arrays)
        cached = read_numeric_cache(self.root, ident)
        with NumericWorker(timeout_seconds=60) as worker:
            worker.fit_c5(self.arrays["warmup"], self.arrays["adj"], self.arrays["channel_types"],
                           self.arrays["fit_service_mask"], [{}])
            first = worker.score_c5(np.array([[1.1], [1.]]), 36)["results"][0]
            worker.fit_c5(cached["warmup"], cached["adj"], cached["channel_types"], cached["fit_service_mask"], [{}])
            second = worker.score_c5(np.array([[1.1], [1.]]), 36)["results"][0]
        equal_outputs(self, first, second)


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    if not (directory / "run-contract.json").is_file():
        raise SystemExit("Pre-run contract required")
    started = time.perf_counter()
    outcome = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    report = {"schema": "TD13-NUMERIC-PROCESS-CACHE-FIXTURE-v1", "tests_run": outcome.testsRun,
              "failures": [{"test": str(t), "traceback": e} for t, e in outcome.failures],
              "errors": [{"test": str(t), "traceback": e} for t, e in outcome.errors],
              "seconds": time.perf_counter() - started,
              "scope": "SYNTHETIC ACTUAL CHILD PROCESS + EXACT NUMERIC CACHE",
              "limitation": "API/process boundary is not a hostile-code OS filesystem sandbox"}
    (directory / "worker-cache-report.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
