"""Real pinned RCD qualification on deterministic synthetic data only.

Execute this file with a coordinator-created run directory. No numeric import,
model call, or fixture generation occurs before its contract is validated.
Expected outcomes follow exact independence/repeated halves and separated shift,
not snapshots of this implementation. No corpus input or label file is opened.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.rcd_runtime import file_sha256, load_pinned_rcd, require_run_contract

RUN_DIR = None
RECEIPTS = []
PROVENANCE = None


def fixture_frame(shift=True):
    # The 300 rows in each half have identical nonshifted observations, so every
    # discretized nonshifted column is exactly independent of the F indicator.
    # m000's +30 shift separates its support in both halves for every bins value.
    base = np.arange(300, dtype=np.float64)
    columns = {"time": np.arange(600, dtype=np.float64)}
    for index in range(6):
        values = ((base * (index + 1)) % (11 + 2 * index)) / (11 + 2 * index)
        columns["m%03d" % index] = np.concatenate(
            [values, values + (30.0 if shift and index == 0 else 0.0)])
    return pd.DataFrame(columns)


@contextmanager
def observe_real_ci(module, allowed, *, inject_exception=False):
    """Inspect CausalGraph.ci_test, then call its unchanged statistical body.

    Do not wrap module.CI_TEST: upstream identity checks for chisq select discrete
    cardinality handling, so replacing that callable would alter the method.
    """
    graph_class = module.SkeletonDiscovery.CausalGraph
    original = graph_class.ci_test
    observations = []

    def observed(graph, i, j, conditioning):
        labels = [graph.labels[k] for k in range(graph.data.shape[1])]
        assert len(labels) == graph.data.shape[1]
        assert len(labels) == len(set(labels))
        assert "time" not in labels and labels[-1] == "F-node"
        assert set(labels) <= set(allowed) | {"F-node"}
        assert graph.data.shape[0] == 600
        assert graph.is_discrete and graph.test is module.CI_TEST
        assert np.isfinite(graph.data).all()
        assert np.array_equal(graph.data[:, -1], np.r_[np.zeros(300), np.ones(300)])
        observation = {"labels": labels, "shape": list(graph.data.shape),
                       "matrix_sha256": hashlib.sha256(graph.data.tobytes()).hexdigest(),
                       "i": int(i), "j": int(j),
                       "conditioning": [int(k) for k in conditioning]}
        observations.append(observation)
        if inject_exception:
            raise RuntimeError("Deliberate qualification CI failure")
        p_value = original(graph, i, j, conditioning)
        assert np.isfinite(p_value) and 0 <= p_value <= 1
        observation["p_value"] = float(p_value)
        return p_value

    with patch.object(graph_class, "ci_test", observed):
        yield observations


class RCDRuntimeQualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global np, pd, rcd_run, PROVENANCE
        if RUN_DIR is None:
            raise RuntimeError("Run this script with a coordinator run contract")
        _, contract = require_run_contract(RUN_DIR, W)
        sources = {str(Path(row["path"]).resolve()): row["sha256"]
                   for row in contract["source_files"]}
        if sources.get(str(Path(__file__).resolve())) != file_sha256(__file__):
            raise RuntimeError("Qualification test absent or changed since run contract")
        cls.loaded = load_pinned_rcd(RUN_DIR, W)
        PROVENANCE = cls.loaded.provenance
        import numpy as numpy_module
        import pandas as pandas_module
        from scripts.task_e.comparators import rcd_run as adapter
        np, pd, rcd_run = numpy_module, pandas_module, adapter

    def invoke(self, frame, seed, bins, *, name, inject_exception=False):
        metric_keys = [key for key in frame.columns if key != "time"]
        start = time.perf_counter()
        with observe_real_ci(self.loaded.module, metric_keys,
                             inject_exception=inject_exception) as calls:
            result = rcd_run(frame, seed=seed, bins=bins, upstream_rcd=self.loaded.rcd)
        receipt = {"fixture": name, "seed": seed, "bins": bins,
                   "execution": "sequential; pinned wrapper resets numpy seed",
                   "input_sha256": hashlib.sha256(frame.to_numpy().tobytes()).hexdigest(),
                   "result": result, "ci_call_count": len(calls), "ci_calls": calls,
                   "wall_seconds": time.perf_counter() - start}
        RECEIPTS.append(receipt)
        self.assertGreater(len(calls), 0, "A real CI boundary must be reached")
        return result, calls

    def test_three_seeds_registered_bins_real_ci_and_repeat_determinism(self):
        for bins in (3, 5, 7):
            for seed in (420, 421, 422):
                with self.subTest(seed=seed, bins=bins):
                    first, first_ci = self.invoke(fixture_frame(), seed, bins, name="separated-shift")
                    second, second_ci = self.invoke(fixture_frame(), seed, bins, name="separated-shift-repeat")
                    self.assertEqual(first["status"], "SUCCESS", first)
                    self.assertEqual(first["ranks"], ["m000"])
                    self.assertEqual(first["unknown_metric_keys"], [])
                    self.assertNotIn("time", first["ranks"])
                    self.assertEqual(first, second)
                    self.assertEqual(first_ci, second_ci)

    def test_real_valid_empty_is_success(self):
        result, _ = self.invoke(fixture_frame(shift=False), 420, 5, name="identical-halves")
        self.assertEqual(result["status"], "SUCCESS", result)
        self.assertEqual(result["ranks"], [])
        self.assertIsNone(result["reason"])

    def test_real_ci_exception_is_failure_not_empty_ranking(self):
        result, _ = self.invoke(fixture_frame(), 420, 5, name="injected-CI-exception",
                                inject_exception=True)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["reason"], "upstream_exception")
        self.assertEqual(result["error"], "RuntimeError")
        self.assertIsNone(result["ranks"])

    def test_runtime_is_exact_bare_implementation(self):
        self.assertFalse(PROVENANCE["framework_init_executed"])
        self.assertFalse(any(key == "RCAEval.e2e" or key.startswith("RCAEval.e2e.")
                             for key in sys.modules))
        self.assertEqual(len(PROVENANCE["customized_installed_files"]), 4)
        self.assertEqual(self.loaded.module.LOCAL_ALPHA, .01)
        self.assertEqual(self.loaded.module.START_ALPHA, .001)
        self.assertEqual(self.loaded.module.ALPHA_STEP, .1)
        self.assertEqual(self.loaded.module.ALPHA_LIMIT, 1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: test_rcd_runtime.py COORDINATOR_RUN_DIRECTORY")
    RUN_DIR = Path(sys.argv[1]).resolve()
    require_run_contract(RUN_DIR, W)
    report = RUN_DIR / "rcd-fixture-report.json"
    if report.exists():
        raise SystemExit("Never overwrite an existing qualification attempt")
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    with report.open("x", encoding="utf-8") as stream:
        json.dump({"tests_run": result.testsRun, "passed": result.wasSuccessful(),
                   "seconds": time.perf_counter() - start, "provenance": PROVENANCE,
                   "numeric_runs": RECEIPTS,
                   "failures": [{"test": str(t), "traceback": e} for t, e in result.failures],
                   "errors": [{"test": str(t), "traceback": e} for t, e in result.errors],
                   "scope": "SYNTHETIC QUALIFICATION ONLY; no development/final data",
                   "limitations": "Runtime/fidelity qualification is not efficacy or paper reproduction"},
                  stream, indent=2, allow_nan=False)
        stream.write("\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)
