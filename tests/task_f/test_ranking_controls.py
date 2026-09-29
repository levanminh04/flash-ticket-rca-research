from __future__ import annotations

import inspect
import unittest

import numpy as np

from rca.ranking import local_scores, perturb_graphs, rank_scores

from _helpers import synthetic_c1


class RankingControlTests(unittest.TestCase):
    def test_01_zero_mass_is_all_tie_no_evidence(self):
        adjacency = np.array([[0, 1], [0, 0]])
        result = rank_scores(np.zeros(2), adjacency, "ppr", "undirected", 0.5)
        np.testing.assert_array_equal(result["scores"], np.zeros(2))
        self.assertTrue(result["diagnostics"]["no_evidence"])

    def test_02_zero_mass_is_not_uniform_ppr(self):
        result = rank_scores(np.zeros(3), np.ones((3, 3)) - np.eye(3), "ppr", "undirected", 0.5)
        self.assertEqual(float(result["scores"].sum()), 0.0)

    def test_03_isolate_self_loop_processing_stays_finite(self):
        adjacency = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]])
        result = rank_scores(np.array([1.0, 0.0, 2.0]), adjacency, "ppr", "undirected", 0.5)
        self.assertTrue(np.isfinite(result["scores"]).all())
        self.assertTrue(result["diagnostics"]["isolates"][2])
        self.assertEqual(result["diagnostics"]["transition"][2, 2], 1.0)

    def test_04_local_missingness_is_explicit_not_healthy_imputation(self):
        observation = synthetic_c1()
        ref = observation.ref.copy()
        query = observation.query.copy()
        ref[0, 0] = np.nan
        result = local_scores(ref, query, observation.channel_types, {"floor": .01, "pool": "q90", "fusion": "availablemean"})
        self.assertFalse(result["masks"]["channels"][0, 0])
        self.assertEqual(result["diagnostics"]["channel_reasons"][0][0], "insufficient_finite_bins")

    def test_05_common_local_vector_can_feed_all_arms(self):
        observation = synthetic_c1()
        evidence = local_scores(observation.ref, observation.query, observation.channel_types, {"floor": .01, "pool": "q90", "fusion": "availablemean"})
        local_before = evidence["local"].copy()
        rank_scores(evidence["local"], observation.adjacency, "ppr", "undirected", .5)
        controls = perturb_graphs(observation.adjacency, observation.handle, "undirected", 3, 2)
        for graph in controls["graphs"]:
            rank_scores(evidence["local"], graph, "ppr", "undirected", .5)
        np.testing.assert_array_equal(local_before, evidence["local"])

    def test_06_core_ranker_has_no_root_or_fault_parameter(self):
        parameters = inspect.signature(rank_scores).parameters
        self.assertNotIn("root", parameters)
        self.assertNotIn("fault", parameters)

    def test_07_undirected_control_is_seed_deterministic(self):
        adjacency = np.zeros((6, 6), dtype=bool)
        for source, target in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3), (1, 4), (2, 5)):
            adjacency[source, target] = True
        first = perturb_graphs(adjacency, "opaque", "undirected", 8, 5)
        second = perturb_graphs(adjacency, "opaque", "undirected", 8, 5)
        np.testing.assert_array_equal(first["graphs"], second["graphs"])
        self.assertEqual(first["per_draw"], second["per_draw"])

    def test_08_undirected_preserves_degree_and_component_partition(self):
        adjacency = np.zeros((7, 7), dtype=bool)
        for source, target in ((0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3), (4, 5)):
            adjacency[source, target] = True
        baseline = adjacency | adjacency.T
        result = perturb_graphs(adjacency, "opaque", "undirected", 10, 8)
        for graph in result["graphs"]:
            np.testing.assert_array_equal(graph.sum(axis=0), baseline.sum(axis=0))
            self.assertFalse(np.diag(graph).any())
            self.assertFalse(graph[6].any())

    def test_09_directed_preserves_in_out_and_weak_partition(self):
        adjacency = np.zeros((6, 6), dtype=bool)
        for source, target in ((0, 1), (2, 1), (2, 3), (4, 3), (4, 5), (0, 5), (2, 5), (4, 1)):
            adjacency[source, target] = True
        result = perturb_graphs(adjacency, "opaque", "directed", 10, 8)
        for graph in result["graphs"]:
            np.testing.assert_array_equal(graph.sum(axis=0), adjacency.sum(axis=0))
            np.testing.assert_array_equal(graph.sum(axis=1), adjacency.sum(axis=1))
            self.assertFalse(np.diag(graph).any())

    def test_10_unswitchable_graph_retains_all_draws(self):
        adjacency = np.array([[0, 1], [0, 0]], dtype=bool)
        result = perturb_graphs(adjacency, "opaque", "directed", 7, 3)
        self.assertEqual(result["summary"]["planned"], 7)
        self.assertEqual(result["summary"]["completed"], 7)
        self.assertTrue(result["summary"]["degenerate"])
        np.testing.assert_array_equal(result["graphs"], np.repeat(adjacency[None], 7, axis=0))

    def test_11_rejected_proposals_do_not_invent_edges(self):
        adjacency = np.array([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=bool)
        result = perturb_graphs(adjacency, "opaque", "directed", 4, 4)
        np.testing.assert_array_equal(result["graphs"], np.repeat(adjacency[None], 4, axis=0))

    def test_12_every_draw_counts_every_proposal(self):
        adjacency = np.array([[0, 1], [0, 0]], dtype=bool)
        result = perturb_graphs(adjacency, "opaque", "directed", 5, 200)
        for receipt in result["per_draw"]:
            self.assertEqual(receipt["accepted"] + sum(receipt["rejections"].values()), receipt["proposals"])
            self.assertEqual(receipt["proposals"], 200)


if __name__ == "__main__":
    unittest.main()
