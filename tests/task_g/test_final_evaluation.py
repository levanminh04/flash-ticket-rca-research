"""Known-answer synthetic evaluator probes and lazy-truth negative boundaries."""
from __future__ import annotations

import copy
import math
import sys
import types
import unittest
from unittest.mock import patch

from scripts.task_g import final_evaluation as evaluation
from scripts.task_g import final_provenance as provenance
from tests.task_g import test_evaluation as historical_fixtures
from tests.task_g import test_final_provenance as seal_fixtures


def payload(count=1):
    return {"phase": provenance.PHASE, "scope": "SYNTHETIC_BRIDGE_READINESS",
        "source_summary": {"source_kind": "THREE_DISTINCT_ARTIFICIAL_ARCHIVES"},
        "planned_case_count": count, "cases": [seal_fixtures.synthetic_case(j) for j in range(count)],
        "_verified_context": {"permissions": {**dict.fromkeys(provenance._FINAL_PERMISSIONS, False), "synthetic_evaluation": True},
            "receipt_sha256": "a" * 64, "final_prediction_qualified": False}}


class LazyAndMappingTests(unittest.TestCase):
    def test_literal_mapping_preserves_missing_and_trigger_local_universe(self):
        one = payload()["cases"][0]
        detector = evaluation.DETECTORS[0]
        row = one["c5"][detector]
        row["triggers"] = [{"endpoint": 360, "candidate_count": 2}]
        mapping = one["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"]
        mapping[detector] = {"360": seal_fixtures.KEYS[::-1]}
        mapped = evaluation.map_synthetic_truth([one], {0: {"root_key": seal_fixtures.KEYS[0], "tau_relative": 182.5}})[0]
        self.assertEqual(mapped["root_index"], 0)
        self.assertEqual(mapped["integrated_root_indices"][detector]["360"], 1)
        self.assertIsNone(evaluation.literal_root_index(seal_fixtures.KEYS, "v0"))
        self.assertIsNone(evaluation.literal_root_index(seal_fixtures.KEYS, "owner:fixture0"))
        self.assertIsNone(evaluation.literal_root_index(seal_fixtures.KEYS, None))
        for keys, root in ((["a", "a"], "a"), ([], True), (["a"], 0), ([None], None)):
            with self.subTest(keys=keys, root=root), self.assertRaises(evaluation.EvaluationError):
                evaluation.literal_root_index(keys, root)

    def test_fresh_durable_verification_completes_before_one_truth_callback(self):
        calls = []
        def verify():
            calls.append("fresh durable verification")
            return payload(2)
        def truth():
            calls.append("artificial truth")
            return {j: {"root_key": seal_fixtures.KEYS[0], "tau_relative": 180.} for j in range(2)}
        with patch.object(provenance, "require_verified_readiness_execution", side_effect=verify):
            result = evaluation.evaluate_readiness(truth)
        self.assertEqual(calls, ["fresh durable verification", "artificial truth"])
        self.assertEqual(result["planned_cases"], 2)
        self.assertFalse(result["final_prediction_qualified"])

    def test_verifier_failure_scope_final_permission_and_completeness_never_open_truth(self):
        mutators = [lambda p: p.update(phase="FINAL_CAMPAIGN"),
            lambda p: p["source_summary"].update(source_kind="ACTUAL_ADMITTED_TELEMETRY"),
            lambda p: p["source_summary"].update(source_kind="DEVELOPMENT_NUMERIC_CACHE"),
            lambda p: p["_verified_context"]["permissions"].update(final_root_fault=True),
            lambda p: p["_verified_context"].update(final_prediction_qualified=True),
            lambda p: p["cases"].clear(), lambda p: p.update(planned_case_count=2),
            lambda p: p["cases"][0]["scientific_diagnostics"]["controller_bindings"].update(candidate_ids=[]),
            lambda p: p["cases"][0]["scientific_diagnostics"]["controller_bindings"]["integrated_candidate_ids"].clear()]
        for mutate in mutators:
            one = payload()
            mutate(one)
            calls = []
            with patch.object(provenance, "require_verified_readiness_execution", return_value=one), self.subTest(mutate=mutate), self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate_readiness(lambda: calls.append("truth"))
            self.assertEqual(calls, [])
        calls = []
        with patch.object(provenance, "require_verified_readiness_execution", side_effect=provenance.FinalProvenanceError("synthetic tamper")), self.assertRaises(provenance.FinalProvenanceError):
            evaluation.evaluate_readiness(lambda: calls.append("truth"))
        self.assertEqual(calls, [])

    def test_artificial_truth_exact_ordinals_fields_and_absent_root_denominator(self):
        one = payload(2)
        truth = {0: {"root_key": seal_fixtures.KEYS[0], "tau_relative": 180.}, 1: {"root_key": "missing", "tau_relative": 180.}}
        result = evaluation.evaluate_bounded_synthetic_payload(one, truth)
        self.assertEqual(result["case_metrics"][1]["ranking"]["primary"]["O"]["rr"], 0.)
        self.assertFalse(result["case_metrics"][1]["root_in_candidate"])
        for bad in ({0: truth[0]}, {**truth, 2: truth[0]}, {0: {**truth[0], "answer": "forbidden"}, 1: truth[1]},
                    {0: {**truth[0], "tau_relative": math.nan}, 1: truth[1]}):
            with self.subTest(bad=bad), self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate_bounded_synthetic_payload(one, bad)

    def test_final_gate_always_rejects_and_orchestration_scope_explicit(self):
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate_final(lambda: self.fail("actual truth cannot open"))
        fixture, labels = historical_fixtures._numeric_fixture()
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate_numeric_fixture_payload(fixture, labels)
        fixture["scope"] = "SYNTHETIC_ONLY_ORCHESTRATION"
        result = evaluation.evaluate_numeric_fixture_payload(fixture, labels)
        self.assertEqual(len(result["case_metrics"]), 60)
        self.assertIn("NO_NUMERIC_COMPUTATIONS", result["evidence_scope"])
        self.assertFalse(result["final_prediction_qualified"])


class LockedKnownAnswerTests(unittest.TestCase):
    def test_tie_boundary_failed_missing_roots_keep_locked_scores(self):
        metrics = evaluation.score_service_vector([3., 2., 2., 2., 2., 2.], 1)
        self.assertEqual((metrics["tie_start"], metrics["tie_end"]), (2, 6))
        self.assertAlmostEqual(metrics["rr"], sum(1 / j for j in range(2, 7)) / 5)
        self.assertEqual(metrics["hit3"], 2 / 5)
        self.assertEqual(metrics["hit5"], 4 / 5)
        self.assertEqual(evaluation.score_service_vector(None, 0, candidate_count=2, failed=True)["rr"], 0.)
        self.assertEqual(evaluation.score_service_vector([1., 2.], None)["rr"], 0.)

    def test_exact_three_rcd_seeds_bins_and_average_seed_metric(self):
        outputs = [{"seed": 420, "bins": 5, "status": "SUCCESS", "ranks": ["m0", "m1"]},
            {"seed": 421, "bins": 5, "status": "SUCCESS", "ranks": ["m1", "m0"]},
            {"seed": 422, "bins": 5, "status": "FAILURE", "ranks": None}]
        result = evaluation.rcd_seed_metrics(outputs, {"m0": 0, "m1": 1}, 2, 0)
        self.assertEqual(result["mean"]["rr"], .5)
        self.assertEqual(result["failed_seeds"], 1)
        for mutation in (lambda x: x[0].update(seed=421), lambda x: x[1].update(bins=4), lambda x: x.pop()):
            bad = copy.deepcopy(outputs)
            mutation(bad)
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.rcd_seed_metrics(bad, {"m0": 0, "m1": 1}, 2, 0)

    def test_256_control_mean_metrics_failed_draw_stays_denominator(self):
        draws = historical_fixtures._draws()
        self.assertEqual(evaluation.random_control_metrics(draws, 2, 0)["metrics"]["rr"], .75)
        draws[-1].update(status="TIMEOUT", scores=None)
        result = evaluation.random_control_metrics(draws, 2, 0)
        self.assertEqual(result["metrics"]["rr"], (128 + 127 * .5) / 256)
        self.assertEqual(result["failed_draws"], 1)

    def test_c5_straddler_excluded_and_early_trigger_failure_retained(self):
        row = seal_fixtures.synthetic_case()["c5"][evaluation.DETECTORS[0]]
        result = evaluation.c5_case_metrics(row, 182.5, trigger_root_indices={"195": None})
        self.assertEqual(result["regime"]["excluded_straddle_bins"], 1)
        self.assertEqual(result["diagnostic_triggers"][0]["status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(result["diagnostic_triggers"][0]["metrics"]["rr"], 0.)
        self.assertEqual(result["composition"]["metrics"]["rr"], 0.)

    def test_paired_scenario_known_constant_effect_keeps20scenario_bootstrap(self):
        rows = historical_fixtures._rows(local=.2, observed=.6, random=.4)
        result = evaluation.paired_scenario_summary(rows)
        self.assertEqual(result["planned_cases"], 60)
        self.assertEqual(result["planned_cells"], 20)
        self.assertEqual(result["bootstrap"]["draws"], 50_000)
        self.assertEqual(result["bootstrap"]["seed"], 20260926)
        self.assertEqual(result["bootstrap"]["unit"], "paired scenario blocks with all three repeats/all arms")
        self.assertEqual(result["bootstrap"]["quantiles"], [.0125, .9875])
        for contrast, effect in (("delta_L", .4), ("delta_R", .2)):
            record = result["contrasts"][contrast]
            self.assertAlmostEqual(record["point"], effect)
            self.assertAlmostEqual(record["lower"], effect)
            self.assertAlmostEqual(record["upper"], effect)


class TypedCostTests(unittest.TestCase):
    def test_missing_cost_coverage_and_metadata_not_coerced_to_seconds(self):
        cases = payload(2)["cases"]
        cases[0]["costs"]["c5_fit_seconds"] = 2.
        result = evaluation.cost_summary(cases)
        self.assertEqual(result["components"]["c5_fit_seconds"]["reported_cases"], 1)
        self.assertEqual(result["components"]["c5_fit_seconds"]["missing_cases"], 1)
        self.assertEqual(result["components"]["c5_fit_seconds"]["total"], 2.)
        self.assertIsNone(result["components"]["c5_prediction_seconds"]["total"])
        self.assertEqual(result["components"]["arm_wall_seconds.primary.L"]["total"], .2)
        self.assertNotIn("exit_code", result["components"])
        self.assertEqual(result["unaggregated"]["exit_code"]["value_types"], ["int"])

    def test_bad_durations_and_duplicate_case_denominator_reject(self):
        for value in (True, "2", -1., math.nan, math.inf, {}, [1.]):
            one = payload()["cases"]
            one[0]["costs"]["c5_fit_seconds"] = value
            with self.subTest(value=value), self.assertRaises(evaluation.EvaluationError):
                evaluation.cost_summary(one)
        one = payload(2)["cases"]
        one[1] = one[0]
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.cost_summary(one)


if __name__ == "__main__":
    unittest.main()
