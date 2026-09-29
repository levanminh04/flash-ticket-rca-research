from __future__ import annotations

import copy
import unittest

import numpy as np

from rca.detection import (
    DetectorNumericalError,
    context_features,
    create_event_state,
    event_step,
    fit_detector,
    score_bin,
    spatial_scores,
)


def warmup(nodes=1, channels=1, bins=36):
    return np.full((bins, nodes, channels), 10.0, dtype=np.float64)


def fitted(values=None, adj=None, types=None, services=None, **config):
    values = warmup() if values is None else values
    _, nodes, channels = values.shape
    adjacency = np.zeros((nodes, nodes), dtype=bool) if adj is None else adj
    channel_types = np.zeros(channels, dtype=np.int64) if types is None else types
    fit_services = np.ones(nodes, dtype=bool) if services is None else services
    return fit_detector(values, adjacency, channel_types, fit_services, config)


class DetectionContractTests(unittest.TestCase):
    def test_01_scaler_membership_is_independent_of_own_model(self):
        values = warmup(3)
        values[:24:2, 2, 0] = np.nan
        adjacency = np.zeros((3, 3), dtype=bool)
        adjacency[0, 1:] = True
        state = fitted(values, adjacency)
        self.assertTrue(state["E"][2, 0])
        self.assertFalse(state["model_mask"][2, 0])
        features, audit = context_features(state, np.array([[[3.0], [np.nan], [10.0]]]))
        np.testing.assert_array_equal(features[0, 0], [3.0, 10.0, 0.0, 0.5, 0.0])
        self.assertEqual(audit["available_out"][0, 0], 1)

    def test_02_missing_neighbor_changes_numerator_not_frozen_degree(self):
        adjacency = np.zeros((3, 3), dtype=bool)
        adjacency[0, 1:] = True
        state = fitted(warmup(3), adjacency)
        features, _ = context_features(state, np.array([[[3.0], [np.nan], [10.0]]]))
        self.assertEqual(state["degrees"]["out"][0, 0], 2)
        np.testing.assert_array_equal(features[0, 0, [1, 3]], [10.0, 0.5])

    def test_03_empty_neighbor_pool_is_explicit_zero_coverage(self):
        state = fitted(warmup(2))
        features, _ = context_features(state, np.array([[[3.0], [10.0]]]))
        np.testing.assert_array_equal(features[0, 0], [3.0, 0.0, 0.0, 0.0, 0.0])
        self.assertEqual(state["degrees"]["out"][0, 0], 0)

    def test_04_g_l_all_feature_semantics_and_common_targets(self):
        values = warmup(3)
        adjacency = np.zeros((3, 3), dtype=bool)
        adjacency[0, 1] = True
        history = np.array([[[3.0], [4.0], [10.0]]])
        expected = {"G": [3.0, 4.0, 0.0, 1.0, 0.0], "L": [3.0, 0.0, 0.0, 0.0, 0.0], "ALL": [3.0, 7.0, 7.0, 1.0, 1.0]}
        masks = []
        for arm, row in expected.items():
            state = fitted(values, adjacency, arm=arm, **{"lambda": 10.0})
            features, _ = context_features(state, history)
            np.testing.assert_array_equal(features[0, 0], row)
            masks.append(state["model_mask"])
        for mask in masks[1:]:
            np.testing.assert_array_equal(mask, masks[0])

    def test_05_mt_mtl_common_channels_are_identical(self):
        values = warmup(2, 3)
        adjacency = np.array([[0, 1], [0, 0]], dtype=bool)
        mt = fitted(values, adjacency, types=[0, 1, 2], modalities="MT", **{"lambda": 10.0})
        mtl = fitted(values, adjacency, types=[0, 1, 2], modalities="MTL", **{"lambda": 10.0})
        for key in ("E", "model_mask", "centers", "scales", "coefficients", "residual_scales"):
            np.testing.assert_array_equal(mt[key][:, :2], mtl[key][:, :2])
        self.assertFalse(mt["model_mask"][:, 2].any())
        self.assertTrue(mtl["model_mask"][:, 2].all())

    def test_06_absolute_relative_and_residual_floors_are_distinct(self):
        values = np.zeros((36, 1, 1), dtype=float)
        state = fitted(values, types=[0], floor=0.0001, residual_floor=0.1)
        self.assertEqual(state["scales"][0, 0], 1e-12)
        self.assertEqual(state["residual_scales"][0, 0], 0.1)
        changed = fitted(values, types=[0], floor=0.01, residual_floor=0.1)
        self.assertEqual(changed["scales"][0, 0], 1e-12)

    def test_07_no_model_is_unavailable_not_healthy_zero(self):
        state = fitted(np.full((36, 2, 1), np.nan))
        result = score_bin(state, np.ones((2, 1)))
        self.assertTrue(np.isnan(result["score"]))
        self.assertEqual(result["scored_channels"], 0)

    def test_08_missing_lag_recovers_only_after_registered_history(self):
        for lag in (1, 3):
            state = fitted(lag=lag)
            self.assertTrue(np.isnan(score_bin(state, np.array([[np.nan]]))["score"]))
            for _ in range(lag):
                self.assertTrue(np.isnan(score_bin(state, np.array([[10.0]]))["score"]))
            self.assertEqual(score_bin(state, np.array([[10.0]]))["score"], 0.0)

    def test_09_graph_tv_no_edge_is_unavailable(self):
        state = fitted()
        self.assertTrue(np.isnan(spatial_scores(state, np.array([[2.0]]))["tv_score"]))
        adjacency = np.array([[0, 1], [0, 0]], dtype=bool)
        state = fitted(warmup(2), adjacency)
        self.assertEqual(spatial_scores(state, np.array([[1.0], [3.0]]))["tv_score"], 4.0)

    def test_10_fit_rejects_future_suffix_and_state_is_frozen(self):
        with self.assertRaises(ValueError):
            fitted(warmup(bins=37))
        state = fitted()
        frozen = {key: state[key].copy() for key in ("E", "adj", "centers", "scales", "coefficients", "residual_scales")}
        for value in (10.0, 11.0, np.nan, 9.0):
            score_bin(state, np.array([[value]]))
        for key, expected in frozen.items():
            np.testing.assert_array_equal(state[key], expected)

    def test_11_incremental_copy_replay_is_exact(self):
        first = fitted()
        score_bin(first, np.array([[11.0]]))
        second = copy.deepcopy(first)
        for value in (10.0, np.nan, 11.0, 10.0):
            left = score_bin(first, np.array([[value]]))
            right = score_bin(second, np.array([[value]]))
            for key in ("residuals", "errors", "target_mask", "features"):
                np.testing.assert_array_equal(left[key], right[key])

    def test_12_event_strict_threshold_nan_reset_and_refractory(self):
        state = create_event_state(5.0, refractory_seconds=60)
        self.assertFalse(event_step(state, 5.0, 185)["positive"])
        self.assertFalse(event_step(state, 6.0, 190)["trigger"])
        self.assertFalse(event_step(state, np.nan, 195)["available"])
        self.assertEqual(state["streak"], 0)
        triggers = []
        for endpoint in range(200, 271, 5):
            if event_step(state, 6.0, endpoint)["trigger"]:
                triggers.append(endpoint)
        self.assertEqual(triggers, [210, 270])

    def test_13_nonconsecutive_or_infinite_event_input_fails(self):
        state = create_event_state(5.0)
        event_step(state, 6.0, 185)
        with self.assertRaises(ValueError):
            event_step(state, 6.0, 195)
        with self.assertRaises(DetectorNumericalError):
            event_step(state, np.inf, 190)

    def test_14_service_permutation_is_equivariant(self):
        values = np.arange(36.0)[:, None, None] + np.array([1.0, 3.0, 7.0])[None, :, None]
        adjacency = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool)
        order = np.array([2, 0, 1])
        original = fitted(values, adjacency, arm="G", **{"lambda": 10.0})
        permuted = fitted(values[:, order], adjacency[np.ix_(order, order)], arm="G", **{"lambda": 10.0})
        current = np.array([[37.0], [39.0], [43.0]])
        left = score_bin(original, current)
        right = score_bin(permuted, current[order])
        np.testing.assert_allclose(right["residuals"], left["residuals"][order], atol=1e-9)
        np.testing.assert_array_equal(right["target_mask"], left["target_mask"][order])


if __name__ == "__main__":
    unittest.main()
