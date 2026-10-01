"""Analytic TD13 metric/statistical fixtures; no telemetry/oracle files."""

from __future__ import annotations

import copy
import math
import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

from scripts.task_g import evaluation as evaluation


def _draws():
    return [{"draw": j, "seed": j, "status": "SUCCESS", "scores": [100., 0.] if j < 128 else [0., 1.],
             "graph_sha256": f"{j % 64:064x}", "retained_edge_fraction": .5} for j in range(256)]


def _rows(*, local=.4, observed=.8, random=.3):
    return [{"ordinal": j, "cell_ordinal": j // 3, "repeat": j % 3,
             "root_stratum": "root" + str((j // 3) % 5), "fault_stratum": "fault" + str((j // 3) % 6),
             "L": local, "O": observed, "R": random} for j in range(60)]


def _mobility(mobile=12):
    return {"root" + str(j): {"planned": 12, "mobile": mobile} for j in range(5)}


def _c5(scores, *, threshold=1., status="SUCCESS"):
    ends = list(range(185, 185 + len(scores) * 5, 5))
    return {"status": status, "threshold": threshold, "starts": [end - 5 for end in ends], "ends": ends,
            "scores": scores, "bin_statuses": ["SUCCESS" if score is not None else "UNAVAILABLE" for score in scores], "triggers": []}


def _numeric_fixture():
    thresholds = {name: float(j + 1) for j, name in enumerate(evaluation.DETECTORS)}
    cases, labels = [], {}
    for ordinal in range(60):
        controls = [{"draw": j, "seed": j, "status": "SUCCESS", "scores": [0., 1.],
                     "graph_sha256": f"{j % 64:064x}", "retained_edge_fraction": .5} for j in range(256)]
        condition = {"L": {"status": "SUCCESS", "scores": [1., 0.]},
                     "O": {"status": "SUCCESS", "scores": [0., 1.]}, "R": controls}
        cases.append({"ordinal": ordinal, "cell_ordinal": ordinal // 3, "repeat": ordinal % 3,
            "candidate_count": 2, "local_evidence": [1., 2.], "shared_preprocessing_failed": False,
            "c1": {"primary": copy.deepcopy(condition), "secondary": copy.deepcopy(condition)},
            "contextual": {"Local-MAX-MT": {"status": "FAILURE", "scores": None},
                           "BARO-RANK-adapted-TD12": {"status": "FAILURE", "scores": None},
                           "RCD": {"n_services": 2, "metric_owners": {"m0": 0}, "seed_outputs": [
                               {"seed": seed, "bins": 5, "status": "FAILURE", "ranks": None} for seed in evaluation.SEEDS]}},
            "c5": {name: _c5([0.], threshold=thresholds[name]) for name in evaluation.DETECTORS}, "costs": {}})
        labels[ordinal] = {"root_index": 0, "root_stratum": "root" + str((ordinal // 3) % 5),
                           "fault_stratum": "fault" + str((ordinal // 3) % 6), "tau_relative": 180., "integrated_root_indices": {}}
    payload = {"cases": cases, "phase": "CAMPAIGN_READINESS_ONLY", "scope": "SYNTHETIC_CAMPAIGN_READINESS",
               "source_summary": {"source_kind": "SYNTHETIC_NUMERIC"},
               "prepared_conditions": {"scientific_objects": {"selections": {"c5": {"detectors": [
                   {"id": name, "threshold": threshold} for name, threshold in thresholds.items()]}}}},
               "_verified_context": {"receipt_sha256": "0" * 64, "final_prediction_qualified": False,
                   "permissions": {**dict.fromkeys(evaluation._FINAL_PERMISSIONS, False), "synthetic_evaluation": True}}}
    return payload, labels


def _assembled_costs(*, exit_code=0):
    """Actual C1 assembly interface from synthetic records; never run a worker."""
    from scripts.task_g import campaign

    case = {"ordinal": 0, "cell_ordinal": 0, "repeat": 0,
            "numeric_input_sha256": "1" * 64,
            "c1": types.SimpleNamespace(node_ids=("v0", "v1"), handle="0" * 16)}
    header = {"kind": "header", "local_evidence": [1., 2.],
              "c1": {name: {} for name in ("primary", "secondary")}, "contextual": {},
              "costs": {"shared_preprocessing_seconds": 1., "control_generation_seconds": 0.,
                        "rank_seconds": {"primary": {"L": .1, "O": .2},
                                         "secondary": {"L": .3, "O": .4}}}}
    done = {"kind": "done", "control_generation_seconds": 2.,
            "R_rank_seconds": {"primary": 1., "secondary": 1.5}, "worker_numeric_seconds": 6.5,
            "control_summary": {"representation": "undirected", "planned": 256,
                "completed": 256, "failed": 0, "budget": 200, "edges": 1,
                "proposals_per_draw": 200, "partition": [0, 0], "component_sizes": {"0": 2},
                "distinct_final_graphs": 1, "median_retained_edge_fraction": 1.,
                "mobile": False, "degenerate": True}}
    worker = {"rows": [header, done], "wall_seconds": 7.5, "exit_code": exit_code,
              "timed_out": False, "stderr_sha256": "a" * 64, "stderr_bytes": 123}
    costs = campaign._assemble_c1(case, worker)["costs"]
    costs["c5_worker"] = {"wall_seconds": 4., "timed_out": False, "exit_code": -1,
                          "stderr_sha256": "b" * 64, "stderr_bytes": 17,
                          "diagnostics": {"fit_seconds": .5, "status": "FAILURE"}}
    return costs


class CostSummaryTests(unittest.TestCase):
    def test_actual_assembly_metadata_and_signed_exit_codes_reach_readiness(self):
        payload, labels = _numeric_fixture()
        for case in payload["cases"]:
            case["costs"] = _assembled_costs(exit_code=-1 if case["ordinal"] % 2 else 0)
        original = copy.deepcopy(payload["cases"])
        calls = []
        def verified():
            calls.append("verified")
            return payload
        def callback():
            calls.append("labels")
            return labels
        module = types.SimpleNamespace(require_verified_readiness_execution=verified)
        with patch.dict(sys.modules, {"scripts.task_g.campaign_provenance": module}):
            result = evaluation.evaluate_readiness(callback)
        self.assertEqual(calls, ["verified", "labels"])
        self.assertEqual(payload["cases"], original)
        self.assertEqual(result["costs"], [case["costs"] for case in original])
        summary = result["cost_summary"]
        self.assertEqual(summary["planned_cases"], 60)
        for path, expected in (("worker_wall_seconds", 7.5),
                               ("rank_seconds.primary.L", .1),
                               ("R_rank_seconds.secondary", 1.5),
                               ("c5_worker.wall_seconds", 4.),
                               ("c5_worker.diagnostics.fit_seconds", .5)):
            component = summary["components"][path]
            self.assertEqual((component["reported_cases"], component["missing_cases"]), (60, 0))
            self.assertEqual(component["unit"], "seconds")
            self.assertAlmostEqual(component["total"], expected * 60)
            self.assertAlmostEqual(component["mean_over_reported"], expected)
        for path in ("timed_out", "timing_completed", "exit_code", "stderr_sha256", "stderr_bytes",
                     "control_summary.partition", "control_summary.mobile", "control_summary.planned",
                     "c5_worker.exit_code", "c5_worker.diagnostics.status"):
            self.assertNotIn(path, summary["components"])
            self.assertEqual(summary["unaggregated"][path]["reported_cases"], 60)
            self.assertEqual(summary["unaggregated"][path]["missing_cases"], 0)

    def test_new_numeric_component_family_and_unknown_fields_stay_typed(self):
        cases = _rows()
        for case in cases:
            case["costs"] = {"arm_numeric_components_seconds": {
                name: {arm: 2. for arm in ("L", "O", "R")} for name in ("primary", "secondary")},
                "unregistered_numeric": -3, "resource_note": None,
                "nested": {"prediction_seconds": .25, "topology": [0, 1]}}
        summary = evaluation._cost_summary(cases)
        self.assertEqual(summary["components"]["arm_numeric_components_seconds.primary.R"]["total"], 120.)
        self.assertEqual(summary["components"]["nested.prediction_seconds"]["total"], 15.)
        for path in ("unregistered_numeric", "resource_note", "nested.topology"):
            self.assertNotIn(path, summary["components"])
            self.assertEqual(summary["unaggregated"][path]["reported_cases"], 60)

    def test_all_missing_or_partial_durations_are_explicit_without_zero_imputation(self):
        cases = _rows()
        for case in cases:
            case["costs"] = {"worker_wall_seconds": None, "arm_wall_seconds": {
                name: {arm: None for arm in ("L", "O", "R")} for name in ("primary", "secondary")}}
        cases[0]["costs"]["worker_wall_seconds"] = 2.
        cases[1]["costs"].pop("worker_wall_seconds")
        cases[2]["costs"]["arm_wall_seconds"].pop("primary")
        summary = evaluation._cost_summary(cases)
        partial = summary["components"]["worker_wall_seconds"]
        self.assertEqual((partial["reported_cases"], partial["missing_cases"]), (1, 59))
        self.assertEqual((partial["total"], partial["maximum"], partial["mean_over_reported"]), (2., 2., 2.))
        for path, component in summary["components"].items():
            if path == "worker_wall_seconds":
                continue
            self.assertEqual((component["reported_cases"], component["missing_cases"]), (0, 60))
            self.assertEqual((component["total"], component["maximum"], component["mean_over_reported"]), (None, None, None))
        empty = evaluation._cost_summary(_rows())
        self.assertEqual((empty["reported_cost_receipt_cases"], empty["missing_cost_receipt_cases"]), (0, 60))

    def test_malformed_duration_values_reject_at_every_registered_depth(self):
        for value in (True, np.bool_(False), "1", -1., math.nan, math.inf, [1.], {"value": 1.}):
            for cost in ({"worker_wall_seconds": value},
                         {"c5_worker": {"wall_seconds": value}},
                         {"arm_wall_seconds": {"primary": {"L": value}}},
                         {"arm_numeric_components_seconds": {"secondary": {"R": value}}},
                         {"rank_seconds": {"primary": {"O": value}}},
                         {"R_rank_seconds": {"secondary": value}}):
                with self.subTest(value=value, cost=cost), self.assertRaises(evaluation.EvaluationError):
                    cases = _rows()
                    cases[0]["costs"] = cost
                    evaluation._cost_summary(cases)

    def test_cost_schema_and_planned_denominator_fail_closed(self):
        for cost in ([], None, {"rank_seconds": []}, {"arm_wall_seconds": {"primary": []}},
                     {"bad": {1: "metadata"}}):
            cases = _rows()
            cases[0]["costs"] = cost
            with self.subTest(cost=cost), self.assertRaises(evaluation.EvaluationError):
                evaluation._cost_summary(cases)
        cases = _rows()
        with self.assertRaises(evaluation.EvaluationError):
            evaluation._cost_summary(cases[:-1])
        cases[-1] = cases[0]
        with self.assertRaises(evaluation.EvaluationError):
            evaluation._cost_summary(cases)


class TieMetricTests(unittest.TestCase):
    def test_tie_denominator_extends_beyond_top5(self):
        result = evaluation.score_service_vector([3., 2., 2., 2., 2., 2.], 1)
        self.assertAlmostEqual(result["rr"], sum(1 / j for j in range(2, 7)) / 5)
        self.assertEqual((result["tie_start"], result["tie_end"]), (2, 6))
        self.assertEqual(result["hit1"], 0.)
        self.assertEqual(result["hit3"], 2 / 5)
        self.assertEqual(result["hit5"], 4 / 5)
        self.assertAlmostEqual(result["ndcg5"], sum(1 / math.log2(j + 1) for j in range(2, 6)) / 5)

    def test_all_tie_is_valid_while_failure_and_absent_root_are_zero(self):
        self.assertEqual(evaluation.score_service_vector([0., 0., 0.], 0)["status"], "VALID_TIE")
        self.assertAlmostEqual(evaluation.score_service_vector([0., 0., 0.], 0)["rr"], 11 / 18)
        self.assertEqual(evaluation.score_service_vector(None, 0, candidate_count=3, failed=True)["rr"], 0.)
        self.assertEqual(evaluation.score_service_vector([1., 2.], None)["rr"], 0.)

    def test_malformed_numeric_is_rejected_before_absent_root(self):
        for scores in ([np.nan], [np.inf], ["1"], [[1.]], [True]):
            with self.subTest(scores=scores), self.assertRaises(evaluation.EvaluationError):
                evaluation.score_service_vector(scores, None)
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.score_service_vector([1.], True)

    def test_rcd_first_owner_unknown_and_worst_tie_failed_seed_zero(self):
        outputs = [{"seed": 420, "bins": 5, "status": "SUCCESS", "ranks": ["INTERNAL_UNKNOWN_SENTINEL", "a", "b", "a2"]},
                   {"seed": 421, "bins": 5, "status": "SUCCESS", "ranks": ["b"]},
                   {"seed": 422, "bins": 5, "status": "FAILURE", "ranks": None}]
        result = evaluation.rcd_seed_metrics(outputs, {"a": 0, "a2": 0, "b": 1}, 3, 0)
        self.assertEqual(result["per_seed"][0]["metrics"]["rr"], 1.)
        self.assertAlmostEqual(result["per_seed"][1]["metrics"]["rr"], 5 / 12)
        self.assertAlmostEqual(result["mean"]["rr"], 17 / 36)
        self.assertEqual(result["unknown_key_count"], 1)
        self.assertNotIn("INTERNAL_UNKNOWN_SENTINEL", repr(result))
        self.assertEqual(result["failed_seeds"], 1)

    def test_rcd_empty_success_one_complete_worst_tie_and_bad_outputs(self):
        rows = [{"seed": seed, "bins": 5, "status": "SUCCESS", "ranks": []} for seed in evaluation.SEEDS]
        self.assertEqual(evaluation.rcd_seed_metrics(rows, {}, 2, 0)["mean"]["rr"], .75)
        for mutate in (lambda item: item.update(seed=421), lambda item: item.update(bins=3), lambda item: item.update(ranks=["x", "x"])):
            malformed = copy.deepcopy(rows)
            mutate(malformed[0])
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.rcd_seed_metrics(malformed, {}, 2, 0)

    def test_random_mean_metric_not_metric_of_mean_scores(self):
        draws = _draws()
        result = evaluation.random_control_metrics(draws, 2, 0)
        self.assertEqual(result["metrics"]["rr"], .75)
        self.assertEqual(evaluation.score_service_vector(np.mean([row["scores"] for row in draws], axis=0), 0)["rr"], 1.)
        self.assertAlmostEqual(result["mc"]["rr"]["sd"], math.sqrt(256 * .25 ** 2 / 255))
        self.assertAlmostEqual(result["mc"]["rr"]["se"], result["mc"]["rr"]["sd"] / 16)
        self.assertTrue(result["mobile"])

    def test_failed_random_draw_zero_stays_in_256_denominator(self):
        draws = _draws()
        draws[-1].update(status="TIMEOUT", scores=None)
        result = evaluation.random_control_metrics(draws, 2, 0)
        self.assertEqual(result["metrics"]["rr"], (128 + 127 * .5) / 256)
        self.assertEqual(result["failed_draws"], 1)
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.random_control_metrics(draws[:-1], 2, 0)
        draws[-1]["draw"] = 254
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.random_control_metrics(draws, 2, 0)

    def test_generation_failures_need_no_fabricated_graph_and_stay_zero(self):
        draws = _draws()
        for row in draws:
            row.update(status="TIMEOUT", scores=None, graph_sha256=None, retained_edge_fraction=None)
        result = evaluation.random_control_metrics(draws, 2, 0)
        self.assertEqual(result["metrics"]["rr"], 0.)
        self.assertEqual(result["failed_draws"], 256)
        self.assertEqual(result["generated_graphs"], 0)
        self.assertEqual(result["distinct_final_graphs"], 0)
        self.assertIsNone(result["median_retained_edge_fraction"])
        self.assertFalse(result["mobile"])
        for index in range(16):
            draws[index] = _draws()[index]
        result = evaluation.random_control_metrics(draws, 2, 0)
        self.assertEqual(result["metrics"]["rr"], 16 / 256)
        self.assertEqual(result["generated_graphs"], 16)
        self.assertEqual(result["unmaterialized_graphs"], 240)
        self.assertEqual(result["distinct_final_graphs"], 16)
        self.assertFalse(result["mobile"])


class ScenarioAndVerdictTests(unittest.TestCase):
    def test_constant_paired_effects_exact_intervals_deletions_and_support(self):
        result = evaluation.paired_scenario_summary(_rows())
        for name, expected in (("delta_L", .4), ("delta_R", .5)):
            self.assertAlmostEqual(result["contrasts"][name]["point"], expected)
            self.assertAlmostEqual(result["contrasts"][name]["lower"], expected)
            self.assertAlmostEqual(result["contrasts"][name]["upper"], expected)
            self.assertEqual(len(result["contrasts"][name]["leaveouts"]["root"]), 5)
            self.assertEqual(len(result["contrasts"][name]["leaveouts"]["fault"]), 6)
        self.assertEqual(result["bootstrap"]["draws"], 50_000)
        self.assertEqual(result["bootstrap"]["seed"], 20260926)
        verdict = evaluation.primary_verdict(result, shared_preprocessing_failures=0, starved_cases=0, arm_failures=0, mobility_by_root=_mobility())
        self.assertEqual(verdict["verdict"], "BOUNDED_SUPPORT")

    def test_bootstrap_samples_cells_together_not_incidents(self):
        rows = _rows(local=0., observed=0., random=0.)
        for row in rows:
            row["O"] = 1. if row["cell_ordinal"] < 10 else 0.
        result = evaluation.paired_scenario_summary(rows)
        # Half of20 whole scenario blocks are1, so each draw is Binomial(20,.5)/20.
        self.assertEqual(result["contrasts"]["delta_L"]["point"], .5)
        self.assertEqual(result["contrasts"]["delta_L"]["lower"], .25)
        self.assertEqual(result["contrasts"]["delta_L"]["upper"], .75)
        self.assertEqual(result["contrasts"]["delta_L"]["lower"], result["contrasts"]["delta_R"]["lower"])

    def test_exact_denominators_and_strata_reject_silent_exclusion(self):
        rows = _rows()
        for malformed in (rows[:-1], [rows[0]] + rows[1:-1] + [rows[0]]):
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.paired_scenario_summary(malformed)
        rows[0]["repeat"] = 1
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.paired_scenario_summary(rows)

    def test_repeat_ranges_and_stability_reported(self):
        rows = _rows(local=0., random=0.)
        for row in rows:
            row["O"] = [.1, .2, .3][row["repeat"]]
        result = evaluation.paired_scenario_summary(rows)
        self.assertAlmostEqual(result["contrasts"]["delta_L"]["point"], .2)
        self.assertEqual(result["contrasts"]["delta_L"]["scenario_scatter"][0]["repeat_min"], .1)
        self.assertEqual(result["contrasts"]["delta_L"]["scenario_scatter"][0]["repeat_max"], .3)

    def test_informative_gate_boundaries_and_invalid_first(self):
        summary = evaluation.paired_scenario_summary(_rows())
        params = {"shared_preprocessing_failures": 6, "starved_cases": 47, "arm_failures": 0, "mobility_by_root": _mobility()}
        self.assertEqual(evaluation.primary_verdict(summary, **params)["verdict"], "BOUNDED_SUPPORT")
        for name, value in (("shared_preprocessing_failures", 7), ("starved_cases", 48), ("arm_failures", 1)):
            with self.subTest(name=name):
                self.assertEqual(evaluation.primary_verdict(summary, **{**params, name: value})["verdict"], "INCONCLUSIVE")
        self.assertEqual(evaluation.primary_verdict(summary, **params, invalidity_reasons=("LEAKAGE",))["verdict"], "INVALID")

    def test_mobility_whole_sample_and_each_root_thresholds(self):
        summary = evaluation.paired_scenario_summary(_rows())
        params = {"shared_preprocessing_failures": 0, "starved_cases": 0, "arm_failures": 0}
        mobility = _mobility()
        mobility["root0"]["mobile"] = 6
        mobility["root1"]["mobile"] = 6
        self.assertEqual(evaluation.primary_verdict(summary, **params, mobility_by_root=mobility)["verdict"], "BOUNDED_SUPPORT")
        mobility["root0"]["mobile"] = 5
        self.assertEqual(evaluation.primary_verdict(summary, **params, mobility_by_root=mobility)["verdict"], "INCONCLUSIVE")

    def test_valid_negative_does_not_require_positive_leaveouts(self):
        summary = evaluation.paired_scenario_summary(_rows(local=.9, observed=.4, random=.8))
        result = evaluation.primary_verdict(summary, shared_preprocessing_failures=0, starved_cases=0, arm_failures=0, mobility_by_root=_mobility())
        self.assertEqual(result["verdict"], "BOUNDED_NEGATIVE_FOR_FROZEN_PRIMARY")
        self.assertFalse(summary["contrasts"]["delta_L"]["all_deletion_effects_positive"])

    def test_local_ceiling_is_not_an_inconclusive_veto(self):
        summary = evaluation.paired_scenario_summary(_rows(local=1., observed=1., random=1.))
        result = evaluation.primary_verdict(summary, shared_preprocessing_failures=0, starved_cases=0, arm_failures=0, mobility_by_root=_mobility())
        self.assertEqual(result["verdict"], "BOUNDED_NEGATIVE_FOR_FROZEN_PRIMARY")

    def test_starvation_uses_normalized_ties_and_emptyV(self):
        self.assertTrue(evaluation.signal_starved([], 0))
        self.assertTrue(evaluation.signal_starved([0., 0.], 2))
        self.assertTrue(evaluation.signal_starved([1e12, 1e12 + .25], 2))
        self.assertFalse(evaluation.signal_starved([1., 2.], 2))


class DetectionAndFirewallTests(unittest.TestCase):
    def test_straddler_excluded_unavailable_not_negative_both_normal_durations(self):
        result = evaluation.c5_case_metrics(_c5([0., 2., None, 4., 3., 0.]), 197.5)
        bins = result["regime"]
        self.assertEqual((bins["tp"], bins["fp"], bins["fn"], bins["tn"]), (1, 1, 1, 1))
        self.assertEqual(bins["f1"], .5)
        self.assertEqual(bins["excluded_straddle_bins"], 1)
        self.assertEqual(bins["unavailable_bins"], 1)
        self.assertEqual((bins["normal_observed_seconds"], bins["normal_scored_seconds"]), (15., 10.))

    def test_trigger_at_tau_pre_and_continuous_streak_not_reset(self):
        record = _c5([2.] * 64)
        record["triggers"] = [{"endpoint": 195, "status": "INSUFFICIENT_HISTORY", "scores": None, "candidate_count": 0},
                              {"endpoint": 495, "status": "SUCCESS", "scores": [1., 0.], "candidate_count": 2}]
        result = evaluation.c5_case_metrics(record, 195, trigger_root_indices={"495": 0})
        self.assertEqual(result["events"]["pre_injection_triggers"], 1)
        self.assertEqual(result["events"]["first_post_injection_trigger"], 495)
        self.assertEqual(result["events"]["first_post_injection_delay"], 300.)
        self.assertEqual(result["composition"]["metrics"]["rr"], 1.)

    def test_later_correct_diagnosis_cannot_rescue_first_failure(self):
        record = _c5([None] * 35 + [2.] * 70)
        record["triggers"] = [{"endpoint": 370, "status": "FAILURE", "scores": None, "candidate_count": 2},
                              {"endpoint": 670, "status": "SUCCESS", "scores": [1., 0.], "candidate_count": 2}]
        result = evaluation.c5_case_metrics(record, 360, trigger_root_indices={"670": 0})
        self.assertEqual(result["composition"]["endpoint"], 370.)
        self.assertEqual(result["composition"]["metrics"]["rr"], 0.)

    def test_first_post_insufficient_history_and_absent_trigger_zero(self):
        record = _c5([2.] * 3)
        record["triggers"] = [{"endpoint": 195, "status": "INSUFFICIENT_HISTORY", "scores": None, "candidate_count": 0}]
        self.assertEqual(evaluation.c5_case_metrics(record, 190)["composition"]["status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(evaluation.c5_case_metrics(_c5([0.]), 180)["composition"]["metrics"]["rr"], 0.)

    def test_strict_threshold_missing_bin_and_missing_trigger_rejected(self):
        self.assertEqual(evaluation.c5_case_metrics(_c5([1.] * 3), 190)["events"]["triggers"], [])
        malformed = _c5([0., None])
        malformed["ends"][-1] = 195
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.c5_case_metrics(malformed, 190)
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.c5_case_metrics(_c5([2.] * 3), 190)

    def test_failed_detector_scores_zero_retains_duration(self):
        result = evaluation.c5_case_metrics(_c5([0., 2.], status="FAILURE"), 190)
        self.assertEqual(result["regime"]["f1"], 0.)
        self.assertEqual(result["regime"]["normal_observed_seconds"], 10.)
        self.assertEqual(result["regime"]["normal_scored_seconds"], 0.)

    def test_unavailable_case_is_not_counted_as_method_failure_or_healthy(self):
        result = evaluation.c5_case_metrics(_c5([None, None], status="UNAVAILABLE"), 190)
        self.assertTrue(result["regime"]["unavailable_case"])
        self.assertFalse(result["regime"]["failed"])
        self.assertEqual(result["regime"]["scored_bins"], 0)
        self.assertEqual(result["regime"]["f1"], 0.)

    def test_complete60_eight_detectors_and_external_failures_do_not_veto(self):
        payload, labels = _numeric_fixture()
        result = evaluation.evaluate_numeric_fixture_payload(payload, labels)
        self.assertFalse(result["final_prediction_qualified"])
        self.assertEqual(result["primary_verdict"]["verdict"], "BOUNDED_NEGATIVE_FOR_FROZEN_PRIMARY")
        self.assertEqual(result["primary"]["headline"], {"L": 1., "O": .5, "R": .5})
        self.assertEqual(set(result["c5"]), set(evaluation.DETECTORS))
        self.assertTrue(all(item["planned_cases"] == 60 for item in result["c5"].values()))
        self.assertEqual(result["contextual"]["RCD"]["mean"]["rr"], 0.)

    def test_lazy_callback_only_after_verified_scope_permissions_and_matrix(self):
        payload, labels = _numeric_fixture()
        calls = []
        def verified():
            calls.append("verified")
            return payload
        def callback():
            calls.append("labels")
            return labels
        module = types.SimpleNamespace(require_verified_readiness_execution=verified)
        with patch.dict(sys.modules, {"scripts.task_g.campaign_provenance": module}):
            result = evaluation.evaluate_readiness(callback)
        self.assertEqual(calls, ["verified", "labels"])
        self.assertTrue(result["durable_verification_before_label_callback"])
        for change in (lambda: payload.update(scope="FINAL_CAMPAIGN"),
                       lambda: payload["_verified_context"]["permissions"].update(final_labels=True),
                       lambda: payload["_verified_context"]["permissions"].update(synthetic_evaluation=False),
                       lambda: payload["source_summary"].update(source_kind="FINAL_TELEMETRY")):
            payload, _ = _numeric_fixture()
            calls.clear()
            change()
            with patch.dict(sys.modules, {"scripts.task_g.campaign_provenance": module}), self.assertRaises(evaluation.EvaluationError):
                evaluation.evaluate_readiness(callback)
            self.assertEqual(calls, ["verified"])

    def test_verifier_failure_and_final_entrypoint_never_call_labels(self):
        calls = []
        def fail():
            raise ValueError("broken durable receipt")
        module = types.SimpleNamespace(require_verified_readiness_execution=fail)
        with patch.dict(sys.modules, {"scripts.task_g.campaign_provenance": module}), self.assertRaises(ValueError):
            evaluation.evaluate_readiness(lambda: calls.append("labels"))
        with self.assertRaises(evaluation.EvaluationError):
            evaluation.evaluate_final(lambda: calls.append("labels"))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
