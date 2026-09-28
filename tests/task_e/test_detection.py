"""TD13 analytic C5 fixtures; run only after a coordinator source snapshot.

Expected values are derived from the specification, independent of numerical
outputs. No raw telemetry, external resources or outcome labels are used.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import time
import unittest

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.detection import (DetectorNumericalError, _ridge, context_features,
                                     create_event_state, event_step, fit_detector,
                                     score_bin, spatial_scores)


def constant_warmup(nodes=1, channels=1, bins=36):
    return np.full((bins, nodes, channels), 10., dtype=np.float64)


def fitted(values=None, adj=None, types=None, services=None, **config):
    values = constant_warmup() if values is None else values
    _, nodes, channels = values.shape
    adj = np.zeros((nodes, nodes), dtype=bool) if adj is None else adj
    types = np.zeros(channels, dtype=np.int64) if types is None else types
    services = np.ones(nodes, dtype=bool) if services is None else services
    return fit_detector(values, adj, types, services, config)


class MembershipChecks(unittest.TestCase):
    def test_scaler_without_own_model_remains_neighbor(self):
        values = constant_warmup(3)
        values[:24:2, 2, 0] = np.nan
        adj = np.zeros((3, 3), dtype=bool)
        adj[0, 1:] = True
        state = fitted(values, adj)
        self.assertTrue(state["E"][2, 0])
        self.assertFalse(state["model_mask"][2, 0])
        self.assertEqual(state["diagnostics"]["fit_rows"][2, 0], 0)
        history = np.array([[[3.], [np.nan], [10.]]])
        feature, audit = context_features(state, history)
        np.testing.assert_array_equal(feature[0, 0], [3., 10., 0., .5, 0.])
        self.assertEqual(state["degrees"]["out"][0, 0], 2)
        self.assertEqual(audit["available_out"][0, 0], 1)

    def test_own_model_missing_bin_changes_numerator_only(self):
        adj = np.zeros((3, 3), dtype=bool)
        adj[0, 1:] = True
        state = fitted(constant_warmup(3), adj)
        self.assertTrue(state["model_mask"].all())
        for observed, expected in (([4., 10.], [7., 1.]),
                                   ([np.nan, 10.], [10., .5]),
                                   ([np.nan, np.nan], [0., 0.])):
            feature, _ = context_features(state, np.array([[[3.], [observed[0]], [observed[1]]]]))
            np.testing.assert_array_equal(feature[0, 0, [1, 3]], expected)
            self.assertEqual(state["degrees"]["out"][0, 0], 2)

    def test_absent_fit_cannot_join_later(self):
        values = constant_warmup(3)
        values[:24, 2, 0] = np.nan
        adj = np.zeros((3, 3), dtype=bool)
        adj[0, 1:] = True
        state = fitted(values, adj)
        self.assertFalse(state["E"][2, 0])
        feature, _ = context_features(state, np.array([[[3.], [4.], [100.]]]))
        np.testing.assert_array_equal(feature[0, 0], [3., 4., 0., 1., 0.])
        self.assertEqual(state["degrees"]["out"][0, 0], 1)

    def test_singleton_scaler_and_empty_membership(self):
        values = constant_warmup(2)
        values[:24, 1, 0] = np.nan
        values[0, 1, 0] = 10.
        state = fitted(values)
        self.assertTrue(state["E"][1, 0])
        self.assertTrue(state["diagnostics"]["singleton_scale"][1, 0])
        self.assertFalse(state["model_mask"][1, 0])
        self.assertAlmostEqual(state["scales"][1, 0], .1)
        feature, _ = context_features(state, np.array([[[3.], [10.]]]))
        np.testing.assert_array_equal(feature[0, 0], [3., 0., 0., 0., 0.])
        self.assertEqual(state["degrees"]["out"][0, 0], 0)

    def test_calibration_only_node_is_padded_absent(self):
        state = fitted(constant_warmup(3), services=np.array([True, True, False]), arm="ALL")
        self.assertFalse(state["E"][2].any())
        self.assertFalse(state["model_mask"][2].any())
        feature, _ = context_features(state, np.array([[[3.], [4.], [100.]]]))
        np.testing.assert_array_equal(feature[0, 0], [3., 4., 4., 1., 1.])
        self.assertEqual(state["degrees"]["all"][0, 0], 1)

    def test_fit_calibration_input_gates_and_coefficients(self):
        values = constant_warmup(2)
        values[24:28, 1, 0] = np.nan
        state = fitted(values)
        self.assertTrue(state["fit_model_mask"][1, 0])
        self.assertFalse(state["model_mask"][1, 0])
        self.assertEqual(state["diagnostics"]["calibration_rows"][1, 0], 7)
        complete = fitted(constant_warmup(2))
        np.testing.assert_array_equal(state["coefficients"], complete["coefficients"])
        np.testing.assert_array_equal(state["E"], complete["E"])

    def test_g_l_all_and_common_input_ids(self):
        values = constant_warmup(3)
        adj = np.zeros((3, 3), dtype=bool)
        adj[0, 1] = True
        history = np.array([[[3.], [4.], [10.]]])
        expectations = {"G": [3., 4., 0., 1., 0.], "L": [3., 0., 0., 0., 0.],
                        "ALL": [3., 7., 7., 1., 1.]}
        masks = []
        for arm in expectations:
            for penalty in (.1, 1., 10.):
                state = fitted(values, adj, **{"arm": arm, "lambda": penalty})
                feature, _ = context_features(state, history)
                np.testing.assert_array_equal(feature[0, 0], expectations[arm])
                masks.append(state["model_mask"])
        for mask in masks:
            np.testing.assert_array_equal(mask, masks[0])

    def test_channels_have_independent_denominators(self):
        values = constant_warmup(3, 3)
        values[:, 2, 1] = 0.  # no positive fit trace count
        values[:, 1, 2] = np.nan  # no logs for this service
        adj = np.zeros((3, 3), dtype=bool)
        adj[0, 1:] = True
        state = fitted(values, adj, types=[0, 1, 2])
        history = np.array([[[3., 3., 3.], [4., 2., np.nan], [10., np.nan, 6.]]])
        feature, _ = context_features(state, history)
        np.testing.assert_array_equal(feature[0, :, 1], [7., 2., 6.])
        np.testing.assert_array_equal(feature[0, :, 3], [1., 1., 1.])
        np.testing.assert_array_equal(state["degrees"]["out"][0], [2, 1, 1])

    def test_mt_mtl_common_channels_unchanged(self):
        values = constant_warmup(2, 3)
        adj = np.array([[0, 1], [0, 0]], dtype=bool)
        mt = fitted(values, adj, types=[0, 1, 2], modalities="MT")
        mtl = fitted(values, adj, types=[0, 1, 2], modalities="MTL")
        for key in ("E", "model_mask", "centers", "scales", "coefficients", "residual_scales"):
            np.testing.assert_array_equal(mt[key][:, :2], mtl[key][:, :2])
        current = np.array([[10.1, 10.2, 100.], [10., 10., 20.]])
        a, b = score_bin(mt, current), score_bin(mtl, current)
        np.testing.assert_array_equal(a["errors"][:, :2], b["errors"][:, :2])
        np.testing.assert_array_equal(a["residuals"][:, :2], b["residuals"][:, :2])
        self.assertFalse(mt["model_mask"][:, 2].any())
        self.assertTrue(mtl["model_mask"][:, 2].all())

    def test_service_permutation_equivariance(self):
        values = np.arange(36., dtype=float)[:, None, None] + np.array([1., 3., 7.])[None, :, None]
        adj = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool)
        order = np.array([2, 0, 1])
        for arm in ("G", "L", "ALL"):
            original = fitted(values, adj, arm=arm)
            changed = fitted(values[:, order], adj[np.ix_(order, order)], arm=arm)
            first = score_bin(original, np.array([[37.], [39.], [43.]]))
            second = score_bin(changed, np.array([[37.], [39.], [43.]])[order])
            np.testing.assert_allclose(second["residuals"], first["residuals"][order], atol=1e-9)
            np.testing.assert_array_equal(second["target_mask"], first["target_mask"][order])


class NumericalForecastChecks(unittest.TestCase):
    def test_mean_mse_ridge_and_unpenalized_intercept(self):
        coefficient, intercept, audit = _ridge(np.array([[-1.], [1.]]), np.array([-2., 2.]), 1.)
        # beta = sum(x*y)/(sum(x*x)+n*lambda) = 4/(2+2) = 1.
        self.assertAlmostEqual(coefficient[0], 1.)
        self.assertAlmostEqual(intercept, 0.)
        self.assertAlmostEqual(audit["effective_ridge_df"], 1.5)
        self.assertEqual(audit["design_rank_with_intercept"], 2)
        coefficient, intercept, audit = _ridge(np.zeros((5, 3)), np.full(5, 7.), 10.)
        np.testing.assert_array_equal(coefficient, np.zeros(3))
        self.assertEqual(intercept, 7.)
        self.assertEqual(audit["effective_ridge_df"], 1.)

    def test_perfect_forecast_constant_residual_scale_and_spike(self):
        state = fitted()
        self.assertTrue(state["model_mask"].all())
        self.assertAlmostEqual(state["residual_scales"][0, 0], .01)
        perfect = score_bin(state, np.array([[10.]]))
        self.assertEqual(perfect["endpoint"], 185)
        self.assertEqual(perfect["score"], 0.)
        spike = score_bin(state, np.array([[10.1]]))
        # center10, scale.1 => z1; fitted constant prediction0; residual1/.01.
        self.assertAlmostEqual(spike["predictions"][0, 0], 0.)
        self.assertAlmostEqual(spike["errors"][0, 0], 1.)
        self.assertAlmostEqual(spike["score"], 100.)

    def test_missing_own_target_and_lag_recovery(self):
        for lag in (1, 3):
            state = fitted(lag=lag)
            self.assertTrue(np.isnan(score_bin(state, np.array([[np.nan]]))["score"]))
            for _ in range(lag):
                result = score_bin(state, np.array([[10.]]))
                self.assertFalse(result["target_mask"].any())
                self.assertTrue(np.isnan(result["score"]))
            self.assertEqual(score_bin(state, np.array([[10.]]))["score"], 0.)

    def test_no_models_is_unavailable_not_zero(self):
        state = fitted(np.full((36, 2, 1), np.nan))
        result = score_bin(state, np.ones((2, 1)))
        self.assertTrue(np.isnan(result["score"]))
        self.assertEqual(result["scored_channels"], 0)

    def test_numeric_failure_does_not_shrink_mask_or_advance(self):
        state = fitted()
        original = state["model_mask"].copy()
        state["coefficients"][0, 0, 0] = np.inf
        with self.assertRaises(DetectorNumericalError):
            score_bin(state, np.array([[10.]]))
        np.testing.assert_array_equal(state["model_mask"], original)
        self.assertEqual(state["bins_seen"], 36)

    def test_fit_rejects_future_suffix_and_preserves_frozen_parameters(self):
        with self.assertRaises(ValueError):
            fitted(constant_warmup(bins=37))
        state = fitted()
        frozen = {key: state[key].copy() for key in
                  ("E", "adj", "centers", "scales", "coefficients", "residual_centers", "residual_scales")}
        for value in (10., 11., np.nan, 9., 10.):
            score_bin(state, np.array([[value]]))
        for key, expected in frozen.items():
            np.testing.assert_array_equal(state[key], expected)

    def test_incremental_state_copy_replay_equivalence(self):
        state = fitted()
        score_bin(state, np.array([[11.]]))
        restored = copy.deepcopy(state)
        for value in (10., np.nan, 11., 10., 10.):
            a = score_bin(state, np.array([[value]]))
            b = score_bin(restored, np.array([[value]]))
            for key in ("residuals", "errors", "target_mask", "features"):
                np.testing.assert_array_equal(a[key], b[key])
            self.assertEqual(a["endpoint"], b["endpoint"])

    def test_registered_prefix_sensitivities(self):
        for width, fit, cal, minimum in ((5, 24, 12, 18), (10, 12, 6, 8), (5, 32, 16, 24)):
            state = fitted(constant_warmup(bins=fit+cal), bin_seconds=width,
                           fit_bins=fit, cal_bins=cal)
            self.assertEqual(state["config"]["min_fit_rows"], minimum)
            self.assertTrue(state["model_mask"].all())
            self.assertEqual(score_bin(state, np.array([[10.]]))["endpoint"], (fit+cal+1)*width)

    def test_spatial_energy_common_mode_and_isolate(self):
        adj = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], dtype=bool)
        state = fitted(constant_warmup(3), adj)
        equal = spatial_scores(state, np.array([[2.], [2.], [100.]]))
        self.assertEqual(equal["tv_score"], 0.)
        self.assertEqual(equal["local_magnitude"], 100.)
        different = spatial_scores(state, np.array([[1.], [3.], [100.]]))
        self.assertEqual(different["tv_score"], 4.)
        missing = spatial_scores(state, np.array([[1.], [np.nan], [100.]]))
        self.assertTrue(np.isnan(missing["tv_score"]))
        self.assertEqual(missing["tv_edge_counts"][0], 0)
        self.assertTrue(np.isnan(spatial_scores(fitted(), np.array([[2.]]))["tv_score"]))

    def test_tv_overflow_is_explicit_and_does_not_veto_finite_forecast(self):
        adj = np.array([[0, 1], [0, 0]], dtype=bool)
        state = fitted(constant_warmup(2), adj)
        result = score_bin(state, np.array([[1e160], [10.]]))
        self.assertTrue(np.isfinite(result['score']))
        self.assertAlmostEqual(result['score'] / 1e163, 1.)
        self.assertIsNotNone(result['tv_failure'])
        self.assertTrue(np.isnan(result['tv_score']))
        self.assertEqual(state['bins_seen'], 37)


class EventChecks(unittest.TestCase):
    def test_threshold_equality_streak_reset_and_first_trigger(self):
        state = create_event_state(5.)
        self.assertFalse(event_step(state, 5., 185)["positive"])
        self.assertFalse(event_step(state, 6., 190)["trigger"])
        self.assertFalse(event_step(state, np.nan, 195)["available"])
        self.assertEqual(state["streak"], 0)
        self.assertFalse(event_step(state, 6., 200)["trigger"])
        self.assertFalse(event_step(state, 6., 205)["trigger"])
        self.assertTrue(event_step(state, 6., 210)["trigger"])
        first = create_event_state(5.)
        events = [event_step(first, 6., t)["trigger"] for t in (185, 190, 195)]
        self.assertEqual(events, [False, False, True])

    def test_refractory_boundary(self):
        state = create_event_state(5., refractory_seconds=60)
        triggers = [t for t in range(185, 261, 5) if event_step(state, 6., t)["trigger"]]
        self.assertEqual(triggers, [195, 255])

    def test_nonconsecutive_and_infinite_score_fail(self):
        state = create_event_state(5.)
        event_step(state, 6., 185)
        with self.assertRaises(ValueError):
            event_step(state, 6., 195)
        with self.assertRaises(DetectorNumericalError):
            event_step(state, np.inf, 190)

    def test_one_missing_channel_does_not_reset_valid_system_streak(self):
        detector = fitted(constant_warmup(1, 2))
        events = create_event_state(5.)
        results = []
        for first in (10., np.nan, np.nan):
            scored = score_bin(detector, np.array([[first, 10.1]]))
            results.append(event_step(events, scored["score"], scored["endpoint"]))
        self.assertEqual([result["trigger"] for result in results], [False, False, True])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: test_detection.py <existing-run-directory>")
    output_dir = Path(sys.argv[1])
    if not (output_dir / "run-contract.json").is_file():
        raise SystemExit("Pre-run contract required")
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"schema": "TD13-C5-NUMERIC-FIXTURES-v1", "tests_run": result.testsRun,
              "failures": [{"test": str(test), "traceback": trace} for test, trace in result.failures],
              "errors": [{"test": str(test), "traceback": trace} for test, trace in result.errors],
              "seconds": time.perf_counter() - start,
              "scope": "Analytic synthetic numeric detector/event fixtures; no actual development outcomes",
              "not_qualified": ["loader trace chronology", "worker/process firewall", "threshold calibration",
                                "actual development availability or accuracy"]}
    (output_dir / "detection-fixture-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
