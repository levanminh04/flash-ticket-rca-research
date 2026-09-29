from __future__ import annotations

import unittest

import numpy as np

from rca.comparators import baro_scores, local_max_scores
from rca.detection import fit_detector as f_fit_detector, score_bin as f_score_bin
from rca.ranking import local_scores, perturb_graphs, rank_scores
from scripts.task_e.detection import fit_detector as e_fit_detector, score_bin as e_score_bin
from scripts.task_e.ranking import local_scores as e_local_scores, rank_scores as e_rank_scores

from _helpers import HANDLE, W, c1_numeric_path, c5_observation, pipeline


class TaskEEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with np.load(c1_numeric_path(), allow_pickle=False) as stored:
            cls.c1 = {key: stored[key].copy() for key in stored.files}
        cls.c1_prediction_dir = W / "results" / "task-e" / "e27-033-c1-development-full" / "predictions"

    def test_01_randomized_c1_reference_functions_are_exact(self):
        rng = np.random.default_rng(20260928)
        for _ in range(12):
            ref = rng.normal(size=(5, 3, 8))
            query = rng.normal(size=(5, 3, 6))
            ref[:, 1:] = np.abs(ref[:, 1:])
            query[:, 1:] = np.abs(query[:, 1:])
            adjacency = rng.integers(0, 2, size=(5, 5))
            np.fill_diagonal(adjacency, 0)
            config = {"floor": .01, "pool": "q90", "fusion": "availablemean"}
            left = local_scores(ref, query, [0, 1, 2], config)
            right = e_local_scores(ref, query, [0, 1, 2], config)
            np.testing.assert_array_equal(left["local"], right["local"])
            for operator, direction, damping in (("ppr", "undirected", .5), ("diffusion", "undirected", .85)):
                a = rank_scores(left["local"], adjacency, operator, direction, damping)
                b = e_rank_scores(right["local"], adjacency, operator, direction, damping)
                np.testing.assert_array_equal(a["scores"], b["scores"])

    def test_02_c1_sealed_local_evidence_is_exact(self):
        evidence = local_scores(self.c1["ref"], self.c1["query"], self.c1["channel_types"], {"floor": .01, "pool": "q90", "fusion": "availablemean"})
        with np.load(self.c1_prediction_dir / f"{HANDLE}.npz", allow_pickle=False) as stored:
            np.testing.assert_array_equal(evidence["local"], stored["local"][6])
            np.testing.assert_array_equal(evidence["channel_scores"], stored["channel_scores"][6])
            np.testing.assert_array_equal(evidence["masks"]["channels"], stored["channel_masks"][6])
            np.testing.assert_array_equal(evidence["diagnostics"]["scales"], stored["scales"][6])

    def test_03_c1_sealed_observed_and_secondary_are_exact(self):
        evidence = local_scores(self.c1["ref"], self.c1["query"], self.c1["channel_types"], {"floor": .01, "pool": "q90", "fusion": "availablemean"})
        with np.load(self.c1_prediction_dir / f"{HANDLE}-observed-local6.npz", allow_pickle=False) as stored:
            primary = rank_scores(evidence["local"], self.c1["adj"], "ppr", "undirected", .5)
            secondary = rank_scores(evidence["local"], self.c1["adj"], "diffusion", "undirected", .85)
            np.testing.assert_array_equal(primary["scores"], stored["scores"][4])
            np.testing.assert_array_equal(secondary["scores"], stored["scores"][6])

    def test_04_c1_contextual_comparators_are_exact(self):
        evidence = local_scores(self.c1["ref"], self.c1["query"], self.c1["channel_types"], {"floor": .01, "pool": "q90", "fusion": "availablemean"})
        with np.load(self.c1_prediction_dir / f"{HANDLE}-comparators.npz", allow_pickle=False) as stored:
            np.testing.assert_array_equal(local_max_scores(evidence["blocks"], evidence["masks"]["blocks"])["scores"], stored["local_max_mt"])
            np.testing.assert_array_equal(baro_scores(self.c1["ref"], self.c1["query"], self.c1["channel_types"])["scores"], stored["baro"])

    def test_05_c1_all_256_selected_r_draw_scores_are_exact(self):
        evidence = local_scores(self.c1["ref"], self.c1["query"], self.c1["channel_types"], {"floor": .01, "pool": "q90", "fusion": "availablemean"})
        controls = perturb_graphs(self.c1["adj"], HANDLE, "undirected", 256, 200)
        actual = np.stack([rank_scores(evidence["local"], graph, "ppr", "undirected", .5)["scores"] for graph in controls["graphs"]])
        with np.load(self.c1_prediction_dir / f"{HANDLE}-R-undirected.npz", allow_pickle=False) as stored:
            np.testing.assert_array_equal(actual, stored["scores"][:, 1])
        self.assertEqual(controls["summary"]["planned"], 256)

    def test_06_randomized_c5_reference_functions_are_exact(self):
        rng = np.random.default_rng(29)
        values = rng.normal(5, 1, size=(36, 4, 3))
        values[:, :, 1:] = np.abs(values[:, :, 1:])
        adjacency = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0]], dtype=bool)
        config = {"arm": "G", "modalities": "MTL", "lambda": 10.0}
        left = f_fit_detector(values, adjacency, [0, 1, 2], np.ones(4, bool), config)
        right = e_fit_detector(values, adjacency, [0, 1, 2], np.ones(4, bool), config)
        for current in rng.normal(5, 1, size=(6, 4, 3)):
            current[:, 1:] = np.abs(current[:, 1:])
            a, b = f_score_bin(left, current), e_score_bin(right, current)
            for key in ("predictions", "errors", "residuals", "z", "target_mask", "tv_channels", "tv_edge_counts"):
                np.testing.assert_array_equal(a[key], b[key])
            self.assertEqual(a["score"], b["score"])

    def test_07_all_frozen_c5_modes_match_sealed_smoke_outputs(self):
        observation = c5_observation()
        core = pipeline()
        path = W / "results" / "task-e" / "e27-035-c5-development-full" / "predictions" / "primary" / HANDLE / "predictions.npz"
        mapping = {"G-MTL": 2, "G-MT": 5, "L-MTL": 8, "L-MT": 11, "ALL-MTL": 14, "ALL-MT": 17, "TV-MTL": 2, "TV-MT": 5}
        with np.load(path, allow_pickle=False) as sealed:
            for detector_id, index in mapping.items():
                with self.subTest(detector_id=detector_id):
                    result = core.run_c5(observation, detector_id)
                    self.assertEqual(result["status"], "SUCCESS")
                    if detector_id.startswith("TV-"):
                        actual = np.array([row["tv_score"] for row in result["bins"]])
                        np.testing.assert_array_equal(actual, sealed["tv_scores"][index])
                    else:
                        predictions = np.stack([row["predictions"] for row in result["bins"]])
                        residuals = np.stack([row["residuals"] for row in result["bins"]])
                        masks = np.stack([row["target_mask"] for row in result["bins"]])
                        scores = np.array([row["score"] for row in result["bins"]])
                        np.testing.assert_array_equal(predictions, sealed["predictions"][index])
                        np.testing.assert_array_equal(residuals, sealed["residuals"][index])
                        np.testing.assert_array_equal(masks, sealed["target_mask"][index])
                        np.testing.assert_array_equal(scores, sealed["scores"][index])


if __name__ == "__main__":
    unittest.main()
