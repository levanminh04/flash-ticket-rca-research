"""Analytic TD-v1.3 evaluator fixtures; execution requires a recorded run.

Expected fractions/counts below are arithmetic consequences of the specification,
not copies of implementation output. No data files, model fits, or network I/O.
"""
from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.calibration import (
    ARMS, CoverageError, EvaluationError, calibrate_threshold, event_diagnostics,
    first_trigger_composition, fixed_eligible_forecast_loss, grouped_folds,
    leave_one_cell_reselection, mean_planned_draw_metrics, normal_score_distribution,
    planned_regime_summary, regime_metrics, select_lambda, select_q,
    select_registered, weighted_cdf_inverse,
)
from scripts.task_e.evaluator import tie_metrics


def score_case(scenario, normal=25, positive=5, *, score=0.0, failed=False):
    starts = 180 + 5 * np.arange(normal + positive, dtype=float)
    values = np.full(normal + positive, score, dtype=float)
    values[normal:] = 10.0
    return {"scenario": scenario, "starts": starts, "ends": starts + 5,
            "tau": 180 + normal * 5, "scores": values, "failed": failed}


def small_folds():
    return tuple((f"s{2 * k}", f"s{2 * k + 1}") for k in range(5))


def forecast_case(scenario, losses, *, mask=None):
    target = np.zeros(np.asarray(losses).shape, dtype=float)
    return {"scenario": scenario, "starts": 180 + 5 * np.arange(len(target)),
            "ends": 185 + 5 * np.arange(len(target)), "tau": 1000.0,
            "targets": target, "eligible": np.ones_like(target, dtype=bool) if mask is None else mask}


class CalibrationTests(unittest.TestCase):
    def test_discrete_inverse_is_not_interpolated_percentile(self):
        # Half the mass at0 and half at10: inverse(.5)=0, inverse(.5001)=10.
        self.assertEqual(weighted_cdf_inverse([0, 10], [Fraction(1, 2)] * 2, .5), 0)
        self.assertEqual(weighted_cdf_inverse([0, 10], [Fraction(1, 2)] * 2, .5001), 10)
        self.assertEqual(weighted_cdf_inverse([0, 10], [Fraction(95, 100), Fraction(5, 100)], .95), 0)

    def test_hierarchy_weights_scenario_case_endpoint_not_volume(self):
        # ScenarioA: one20-bin case at0 and one60-bin case at10. ScenarioB:
        # one20-bin case at20. Scenario masses=.5/.5, case masses=.25/.25/.5.
        cases = {"a": score_case("A", 20, 0, score=0),
                 "b": score_case("A", 60, 0, score=10),
                 "c": score_case("B", 20, 0, score=20)}
        pool = normal_score_distribution(cases, tuple(cases))
        masses = {key: sum(w for w, support in zip(pool["weights"], pool["support_ids"])
                           if support[0] == key) for key in cases}
        self.assertEqual(masses, {"a": Fraction(1, 4), "b": Fraction(1, 4), "c": Fraction(1, 2)})
        self.assertEqual(calibrate_threshold(cases, tuple(cases), .5)["threshold"], 10)

    def test_exact_endpoint_and_case_coverage_gates(self):
        cases = {str(i): score_case(str(i), 25, 0) for i in range(5)}
        cases["4"]["scores"][:] = np.nan
        pool = normal_score_distribution(cases, tuple(cases))
        self.assertEqual((pool["normal_endpoints"], pool["case_coverage"]), (100, .8))
        cases["0"]["scores"][0] = np.nan
        with self.assertRaises(CoverageError):
            normal_score_distribution(cases, tuple(cases))
        cases["0"] = score_case("0", 100, 0)
        cases["3"]["scores"][:] = np.nan
        with self.assertRaises(CoverageError):
            normal_score_distribution(cases, tuple(cases))

    def test_fixed_ids_hierarchy_and_nonfinite_prediction_rejected(self):
        # A case: bin0 two channels errors0,4=>2; bin1 one channel8=>8;
        # equal-bin mean5. B case error1=>1. Equal-scenario objective3.
        mask = np.array([[True, True], [True, False]])
        inputs = {"a": forecast_case("A", [[0, 4], [8, 0]], mask=mask),
                  "b": forecast_case("B", [[1, 1]])}
        predictions = {"a": np.array([[0., 4.], [8., np.nan]]), "b": np.array([[1., 1.]])}
        self.assertEqual(fixed_eligible_forecast_loss(inputs, predictions, tuple(inputs))["loss"], 3)
        predictions["a"][0, 0] = np.nan
        with self.assertRaises(EvaluationError):
            fixed_eligible_forecast_loss(inputs, predictions, tuple(inputs))

    def test_forecast_missing_cases_stay_coverage_denominator(self):
        inputs = {str(i): forecast_case(str(i), [[2.]]) for i in range(5)}
        predictions = {str(i): np.array([[2.]]) for i in range(5)}
        inputs["4"]["eligible"][:] = False
        result = fixed_eligible_forecast_loss(inputs, predictions, tuple(inputs))
        self.assertEqual((result["loss"], result["eligible_cases"], result["planned_cases"]), (2, 4, 5))
        inputs["3"]["eligible"][:] = False
        with self.assertRaises(CoverageError):
            fixed_eligible_forecast_loss(inputs, predictions, tuple(inputs))

    def test_forecast_ignores_post_injection_ids_not_finite_predictions(self):
        record = forecast_case("A", [[0.], [0.]])
        record["tau"] = 185.0
        result = fixed_eligible_forecast_loss({"a": record}, {"a": np.array([[2.], [np.nan]])}, ("a",))
        self.assertEqual(result["loss"], 2)
        self.assertEqual(result["support_ids"]["a"], [(0, 0)])

    def test_five_fold_lambda_joint_arm_objective_and_ties(self):
        inputs = {str(i): forecast_case(f"s{i}", [[0.]]) for i in range(10)}
        predictions = {lam: {arm: {i: np.array([[2.]]) for i in inputs} for arm in ARMS}
                       for lam in (.1, 1., 10.)}
        result = select_lambda(inputs, predictions, tuple(inputs), folds=small_folds())
        self.assertEqual(result["selected_lambda"], 1.)
        self.assertEqual(result["objectives"], {.1: 2., 1.: 2., 10.: 2.})
        self.assertEqual(select_registered({1.: 2., 10.: 1., .1: 1.}, (1., 10., .1)), 10.)
        self.assertEqual(select_registered({1.: 1. + 5e-13, 10.: 1.}, (1., 10., .1)), 1.)
        # One arm cannot be omitted: lambda1 losses2,2,9 average13/3;
        # lambda10/.1 remain2, so the declared tie priority selects10.
        predictions[1.]["ALL"] = {i: np.array([[9.]]) for i in inputs}
        result = select_lambda(inputs, predictions, tuple(inputs), folds=small_folds())
        self.assertAlmostEqual(result["objectives"][1.], 13 / 3)
        self.assertEqual(result["selected_lambda"], 10.)

    def test_regime_strict_threshold_straddle_and_undefined(self):
        # Bins [180,185)normal (equal threshold=>TN), [185,190)straddle,
        # [190,195)positive TP, [195,200)positive unavailable: P=R=F1=1.
        record = {"scenario": "A", "starts": [180, 185, 190, 195],
                  "ends": [185, 190, 195, 200], "tau": 187., "scores": [2., 100., 3., np.nan]}
        result = regime_metrics(record, 2.)
        self.assertEqual((result["tp"], result["tn"], result["fp"], result["fn"]), (1, 1, 0, 0))
        self.assertEqual((result["planned_bins"], result["scored_bins"], result["excluded_straddle_bins"]), (3, 2, 1))
        self.assertEqual(result["f1"], 1.)
        record["scores"] = [0., 0., np.nan, np.nan]
        result = regime_metrics(record, 2.)
        self.assertEqual(result["f1"], 0.)
        self.assertTrue(result["f1_undefined"])

    def test_failed_case_retained_in_macro_and_missing_record_rejected(self):
        cases = {"a": score_case("A"), "b": score_case("B", failed=True)}
        outcomes = {key: regime_metrics(record, 1) for key, record in cases.items()}
        summary = planned_regime_summary(outcomes, tuple(cases))
        self.assertEqual(summary["macro"]["f1"], .5)
        self.assertEqual((summary["planned_cases"], summary["scored_cases"], summary["failed_cases"]), (2, 1, 1))
        with self.assertRaises(EvaluationError):
            planned_regime_summary({"a": outcomes["a"]}, ("a", "b"))

    def test_q_selection_train_only_support_higher_q_tie(self):
        cases = {str(i): score_case(f"s{i}") for i in range(10)}
        result = select_q(cases, tuple(cases), folds=small_folds())
        self.assertEqual(result["selected_q"], .99)
        self.assertEqual(result["objectives"], {.95: 1., .975: 1., .99: 1.})
        for fold in result["details"][.99]["folds"]:
            train = set(fold["train_ids"])
            self.assertTrue(all(row[0] in train for row in fold["normal_support_ids"]))
            self.assertFalse(train & set(fold["heldout_ids"]))
        self.assertEqual(result["full_development_calibration"]["threshold"], 0.)

    def test_all_undefined_q_objectives_return_instead_of_selecting(self):
        # Normal-only zero-score cases satisfy threshold availability but have
        # no positive reference/prediction support for the F1 objective.
        cases = {str(i): score_case(f"s{i}", positive=0) for i in range(10)}
        with self.assertRaises(CoverageError):
            select_q(cases, tuple(cases), folds=small_folds())

    def test_full_256_draw_metric_mean_and_explicit_failed_draw(self):
        # 128 rank1 +128 rank3 =>meanRR2/3. Mean scores [1.5,2,1]
        # rank root second =>RR.5, so averaging scores is demonstrably wrong.
        first = tie_metrics([3, 2, 1], 0)
        second = tie_metrics([0, 2, 1], 0)
        draws = {i: first if i < 128 else second for i in range(256)}
        result = mean_planned_draw_metrics(draws)
        self.assertAlmostEqual(result["metrics"]["rr"], 2 / 3)
        self.assertEqual(tie_metrics([1.5, 2, 1], 0)["rr"], .5)
        draws = {i: first for i in range(256)}
        draws[255] = None
        self.assertEqual(mean_planned_draw_metrics(draws)["metrics"]["rr"], 255 / 256)
        del draws[254]
        with self.assertRaises(EvaluationError):
            mean_planned_draw_metrics(draws)

    def test_first_trigger_cannot_be_rescued_by_later_rank(self):
        perfect = dict.fromkeys(("rr", "hit1", "hit3", "hit5", "ndcg5"), 1.)
        triggers = [{"endpoint": 300., "status": "VALID", "metrics": perfect},
                    {"endpoint": 700., "status": "VALID", "metrics": perfect}]
        result = first_trigger_composition(triggers, 200.)
        self.assertEqual(result["status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(result["metrics"]["rr"], 0.)
        triggers[0] = {"endpoint": 400., "status": "METHOD_FAILURE"}
        self.assertEqual(first_trigger_composition(triggers, 200.)["metrics"]["rr"], 0.)
        self.assertEqual(first_trigger_composition([], 200.)["status"], "NO_POST_INJECTION_TRIGGER")

    def test_event_boundary_rates_and_censoring_explicit(self):
        record = score_case("A", 2, 2, score=2.)
        result = event_diagnostics([190., 195.], record)
        self.assertEqual(result["pre_injection_triggers"], 1)
        self.assertEqual(result["first_post_injection_delay"], 5)
        self.assertEqual(result["rate_per_observed_normal_hour"], 360.)
        self.assertTrue(event_diagnostics([190.], record)["post_injection_censored"])

    def test_input_infinity_is_not_unavailable(self):
        record = score_case("A")
        record["scores"][0] = np.inf
        with self.assertRaises(EvaluationError):
            regime_metrics(record, 0.)

    def test_fold_disjointness_and_leave_cell_refits_callback(self):
        cases = {str(i): score_case(f"s{i}") for i in range(10)}
        folds = grouped_folds(cases, tuple(cases), small_folds())
        self.assertEqual(sorted(i for f in folds for i in f["heldout_ids"]), sorted(cases))
        calls = []
        def selection(subset, kept):
            calls.append(tuple(kept))
            return {"selected_q": .99, "n": len(subset)}
        result = leave_one_cell_reselection(cases, tuple(cases), selection)
        self.assertEqual(len(calls), 10)
        self.assertTrue(all(len(call) == 9 for call in calls))
        self.assertFalse(result["primary_registry_changed"])


if __name__ == "__main__":
    import json
    import time
    output = Path(sys.argv[1])
    if not (output / 'run-contract.json').is_file():
        raise SystemExit('Pre-run contract required')
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (output / 'calibration-fixture-report.json').write_text(json.dumps({
        'tests_run': result.testsRun, 'seconds': time.perf_counter() - start,
        'failures': [{'test': str(t), 'traceback': e} for t, e in result.failures],
        'errors': [{'test': str(t), 'traceback': e} for t, e in result.errors],
    }, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
