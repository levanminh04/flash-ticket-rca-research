"""Independent bounded executable checks, not an empirical TD12 campaign.

The C5 counterexamples expose underspecification; neither alternative is adopted
as a method or chosen using data. Exact expected evaluator/solver values are
derived analytically rather than copied from implementation outputs.
"""
from __future__ import annotations

import json
import math
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.evaluator import (planned_mean, service_scores_from_metric_ranks,
                                     tie_metrics)
from scripts.task_e.ranking import local_scores, rank_scores, perturb_graphs
from scripts.task_e.comparators import baro_scores, rcd_run


def c5_counterexamples():
    prefix = np.column_stack((np.arange(24, dtype=float), np.arange(24, dtype=float)))
    prefix[::2, 1] = np.nan
    finite = np.isfinite(prefix)
    fit_pairs = np.sum(finite[1:] & finite[:-1], axis=0)
    normalizable = np.any(finite, axis=0)
    target_fit_eligible = fit_pairs >= 18
    current_z = np.array([np.nan, 10.0])

    def context(membership):
        available = membership & np.isfinite(current_z)
        return {'mean': float(np.mean(current_z[available])) if available.any() else 0.0,
                'coverage': float(available.sum() / membership.sum()) if membership.any() else 0.0,
                'applicable_degree': int(membership.sum())}

    a, b = context(normalizable), context(target_fit_eligible)
    assert a == {'mean': 10.0, 'coverage': 0.5, 'applicable_degree': 2}
    assert b == {'mean': 0.0, 'coverage': 0.0, 'applicable_degree': 1}
    return {
        'C5-APPLICABILITY': {
            'classification': 'D-SPEC AMBIGUITY — RETURN TO D',
            'source': 'TD12 section7 same-type applicable degree / model availability',
            'synthetic_only': True, 'data_files_read': [],
            'prefix_finite_counts': finite.sum(axis=0).tolist(),
            'prefix_valid_lag1_target_pairs': fit_pairs.tolist(),
            'interpretation_A': 'neighbor with a fit-prefix-defined scaler',
            'interpretation_B': 'neighbor whose own target has at least18fit rows',
            'A_context': a, 'B_context': b,
            'demonstrated': 'Same telemetry and graph produce different G/ALL inputs',
            'not_demonstrated': 'No trained detector benefit, F1, data prevalence or chosen winner',
            'adopted_interpretation': None,
        },
        'C5-CONFLICT': {
            'classification': 'D-SPEC AMBIGUITY — affected corrupted-bin handling',
            'source': 'TD12 section7 encountered-bin mask scope is unspecified',
            'synthetic_only': True,
            'evidence_kind': 'STATIC ILLUSTRATION; dictionaries below are stated, not loader outputs',
            'example': 'At time200s a conflicting span key in service0; service1 has20valid spans',
            'interpretation_A': {'service0_available': False, 'service1_available': False},
            'interpretation_B': {'service0_available': False, 'service1_available': True,
                                 'service1_log1p_count': math.log1p(20)},
            'illustrated': 'Possible mask scopes differ for service1; no competing loader execution',
            'adopted_interpretation': None,
        },
    }


class EvaluatorChecks(unittest.TestCase):
    def test_rank_one(self):
        result = tie_metrics([2, 1, 0], 0)
        for key in ('rr', 'hit1', 'hit3', 'hit5', 'ndcg5'):
            self.assertEqual(result[key], 1)

    def test_missing_and_failure_zero(self):
        for result in (tie_metrics([2, 1], None), tie_metrics([2, 1], 0, failed=True)):
            self.assertEqual(result['rr'], 0)
            self.assertEqual(result['ndcg5'], 0)

    def test_full_tie(self):
        result = tie_metrics([0] * 6, 4)
        self.assertAlmostEqual(result['rr'], sum(1/r for r in range(1, 7))/6)
        self.assertAlmostEqual(result['hit1'], 1/6)
        self.assertAlmostEqual(result['hit3'], 3/6)
        self.assertAlmostEqual(result['hit5'], 5/6)
        self.assertAlmostEqual(result['ndcg5'], sum(1/math.log2(r+1) for r in range(1, 6))/6)

    def test_partial_tie_crosses_cutoff(self):
        result = tie_metrics([9, 8, 7, 6, 5, 5, 5], 5)
        self.assertEqual((result['tie_start'], result['tie_end']), (5, 7))
        self.assertAlmostEqual(result['rr'], (1/5+1/6+1/7)/3)
        self.assertAlmostEqual(result['hit5'], 1/3)
        self.assertAlmostEqual(result['ndcg5'], 1/math.log2(6)/3)

    def test_planned_denominator(self):
        outcomes = {'a': {'rr': 1}, 'b': {'rr': 0}, 'c': {'rr': 0.5}}
        self.assertEqual(planned_mean(outcomes, ['a', 'b', 'c']), 0.5)
        with self.assertRaises(ValueError):
            planned_mean({'a': outcomes['a']}, ['a', 'b'])

    def test_uncapped_comparator_large_scores_do_not_become_false_ties(self):
        with np.errstate(over='ignore', invalid='ignore'):
            unsafe_old_rounding = np.round(np.array([1e308, 1e307]), 12)
        self.assertFalse(np.isfinite(unsafe_old_rounding).any())
        result = tie_metrics([1e308, 1e307], 0)
        self.assertEqual(result['rr'], 1)
        self.assertEqual(result['tie_end'], 1)
        partial = tie_metrics([1e308, 1e308, 1e307], 2)
        self.assertAlmostEqual(partial['rr'], 1/3)
        self.assertEqual((partial['tie_start'], partial['tie_end']), (3, 3))
        self.assertAlmostEqual(tie_metrics([1e308, 1e308], 0)['rr'], .75)
        self.assertAlmostEqual(tie_metrics([1., 1.+2e-13], 0)['rr'], .75)
        self.assertEqual(tie_metrics([1., 1.+2e-12], 0)['rr'], .5)

    def test_rcd_partial_empty_and_duplicate(self):
        scores, _ = service_scores_from_metric_ranks([], {}, 3)
        self.assertEqual(tie_metrics(scores, 0)['status'], 'VALID_TIE')
        scores, _ = service_scores_from_metric_ranks(['m1','m2','m3'],
                                                    {'m1': 1, 'm2': 1, 'm3': 0}, 3)
        self.assertEqual(scores.tolist(), [1, 2, 0])
        with self.assertRaises(ValueError):
            service_scores_from_metric_ranks(['m1', 'm1'], {'m1': 0}, 2)


class LocalAndGraphChecks(unittest.TestCase):
    def test_robust_deviation_type7(self):
        ref = np.array([[[-2., -1., 0., 1., 2.]]])
        query = np.array([[[0., 2., 4., 2., 0.]]])
        result = local_scores(ref, query, np.array([0]), {})
        # reference IQR2; query deviations0,1,2,1,0 -> type7q90=1.6
        self.assertAlmostEqual(float(result['local'][0]), 1.6)

    def test_available_modality_not_fixed_discount(self):
        ref = np.full((1, 2, 30), np.nan)
        query = ref.copy()
        ref[:, 0, :] = 10
        query[:, 0, :] = 11
        result = local_scores(ref, query, np.array([0, 1]),
                              {'floor': .01, 'fusion': 'availablemean'})
        self.assertAlmostEqual(float(result['local'][0]), 10.0)

    def test_query_only_count_is_unavailable(self):
        result = local_scores(np.zeros((1, 1, 30)), np.ones((1, 1, 30)),
                              np.array([1]), {})
        self.assertEqual(float(result['local'][0]), 0)

    def test_zero_and_positive_uniform_different_semantics(self):
        adj = np.array([[0, 1], [0, 0]], dtype=bool)
        zero = rank_scores(np.zeros(2), adj)
        self.assertTrue(np.all(np.asarray(zero['scores']) == 0))
        positive = rank_scores(np.ones(2), adj)
        self.assertFalse(np.allclose(positive['scores'], np.ones(2)/2))

    def test_two_node_ppr_closed_form(self):
        adj = np.array([[0, 1], [0, 0]], dtype=bool)
        for d in (.2, .5, .85):
            # reverse edge1->0; node0selfloop; p=[0,1] => pi=[d,1-d]
            result = rank_scores(np.array([0., 1.]), adj, damping=d)
            np.testing.assert_allclose(result['scores'], [d, 1-d], atol=1e-12)

    def test_isolate_and_large_values(self):
        local = np.array([1e308, 1e308, 1e307])
        result = rank_scores(local, np.zeros((3, 3), dtype=bool))
        np.testing.assert_allclose(result['scores'], [10/21, 10/21, 1/21], atol=1e-12)

    def test_value_diffusion_closed_form_and_constant(self):
        adj = np.array([[0, 1], [0, 0]], dtype=bool)
        for alpha in (.2, .5, .85):
            result = rank_scores(np.array([1., 0.]), adj, operator='diffusion',
                                 direction='undirected', damping=alpha)
            np.testing.assert_allclose(result['scores'], [1/(1+alpha), alpha/(1+alpha)], atol=1e-12)
            constant = rank_scores(np.ones(2), adj, operator='diffusion',
                                   direction='undirected', damping=alpha)
            np.testing.assert_allclose(constant['scores'], np.ones(2), atol=1e-12)

    def test_c5_ambiguity_is_reproducible(self):
        example = c5_counterexamples()['C5-APPLICABILITY']
        self.assertNotEqual(example['A_context'], example['B_context'])
        self.assertIsNone(example['adopted_interpretation'])

    def test_chain_star_mass_and_index_equivariance(self):
        for edges in ([(0,1),(1,2),(2,3)], [(0,1),(0,2),(0,3)]):
            adj = np.zeros((5, 5), dtype=bool)
            for u,v in edges:
                adj[u,v] = True
            local = np.array([1., 0., 3., 2., 4.])
            order = np.array([4, 2, 0, 3, 1])
            for direction in ('reverse', 'undirected'):
                original = rank_scores(local, adj, direction=direction)
                permuted = rank_scores(local[order], adj[np.ix_(order,order)], direction=direction)
                self.assertAlmostEqual(float(sum(original['scores'])), 1)
                np.testing.assert_allclose(permuted['scores'], original['scores'][order], atol=1e-12)

    def test_R_degree_components_and_draw_retention(self):
        adj = np.zeros((8, 8), dtype=bool)
        for u,v in ((0,1),(1,2),(2,3),(3,0),(0,2),(4,5),(5,6),(6,4)):
            adj[u,v] = True
        def component_sets(graph):
            unseen, output = set(range(len(graph))), set()
            weak = graph | graph.T
            while unseen:
                seen, todo = set(), [min(unseen)]
                while todo:
                    u = todo.pop()
                    if u in seen:
                        continue
                    seen.add(u)
                    todo.extend(int(v) for v in np.flatnonzero(weak[u]) if v not in seen)
                unseen -= seen
                output.add(frozenset(seen))
            return output
        for representation in ('directed','undirected'):
            baseline = adj if representation == 'directed' else adj | adj.T
            result = perturb_graphs(adj, 'fixture-fixed-handle', representation, count=4, budget=200)
            self.assertEqual(len(result['graphs']), 4)
            for graph, receipt in zip(result['graphs'], result['per_draw']):
                np.testing.assert_array_equal(graph.sum(axis=0), baseline.sum(axis=0))
                np.testing.assert_array_equal(graph.sum(axis=1), baseline.sum(axis=1))
                self.assertEqual(component_sets(graph), component_sets(baseline))
                self.assertEqual(receipt['accepted'] + sum(receipt['rejections'].values()), receipt['proposals'])
            repeated = perturb_graphs(adj, 'fixture-fixed-handle', representation, count=4, budget=200)
            np.testing.assert_array_equal(result['graphs'], repeated['graphs'])
        unswitchable = perturb_graphs(np.zeros((1,1), dtype=bool), 'fixture-empty',
                                      'directed', count=256, budget=200)
        self.assertEqual(unswitchable['summary']['completed'], 256)
        self.assertTrue(unswitchable['summary']['degenerate'])

    def test_R_accepts_a_legal_switch_instead_of_being_noop(self):
        # Directed diamond: switch(0,1),(2,3) to(0,3),(2,1) is legal;
        # the corresponding undirected diamond also has a legal switch.
        adj = np.zeros((4,4), dtype=bool)
        for u,v in ((0,1),(2,3),(0,2),(1,3)):
            adj[u,v] = True
        for representation in ('directed','undirected'):
            # Force one known legal proposal, then three shared-endpoint
            # rejections. Four stochastic chains need not have distinct finals;
            # the old uniqueness assertion was not a requirement of TD12.
            choices = [[0,2], [0,0], [0,0], [0,0]]
            if representation == 'undirected':
                choices = [pair + [0,0] for pair in choices]
            sequence = iter(value for proposal in choices for value in proposal)
            class FixedProposals:
                def integers(self, high):
                    value = next(sequence)
                    assert 0 <= value < high
                    return value
            with patch('scripts.task_e.ranking.np.random.Generator', return_value=FixedProposals()):
                result = perturb_graphs(adj, 'fixture-legal-diamond', representation, count=1, budget=1)
            expected = np.zeros((4,4), dtype=bool)
            for u,v in ((0,3),(2,1),(0,2),(1,3)):
                expected[u,v] = True
            if representation == 'undirected':
                expected |= expected.T
            np.testing.assert_array_equal(result['graphs'][0], expected)
            receipt = result['per_draw'][0]
            self.assertEqual(receipt['accepted'], 1)
            self.assertEqual(receipt['rejections']['shared_endpoint'], 3)
            self.assertEqual(receipt['proposals'], 4)

    def test_R_rejects_and_rolls_back_partition_breaking_switch(self):
        # In a directed4-cycle every four-endpoint switch splits the weak
        # component into two2-cycles. Mutation must be rejected and rolled back.
        adj = np.zeros((4,4), dtype=bool)
        for u,v in ((0,1),(1,2),(2,3),(3,0)):
            adj[u,v] = True
        result = perturb_graphs(adj, 'fixture-rollback', 'directed', count=4, budget=200)
        self.assertEqual(sum(r['accepted'] for r in result['per_draw']), 0)
        self.assertGreater(sum(r['rejections']['component_partition'] for r in result['per_draw']), 0)
        for graph in result['graphs']:
            np.testing.assert_array_equal(graph, adj)


class ComparatorInterfaceChecks(unittest.TestCase):
    def test_baro_downshift_and_spike(self):
        ref = np.full((1,1,30), 10.)
        down = np.full((1,1,30), 9.)
        self.assertAlmostEqual(float(baro_scores(ref, down, [0])['scores'][0]), 10.)
        spike = ref.copy()
        spike[0,0,7] = 20.
        self.assertAlmostEqual(float(baro_scores(ref, spike, [0])['scores'][0]), 100.)
        self.assertEqual(float(local_scores(ref, spike, [0], {})['local'][0]), 0.)

    def test_rcd_interface_exception_and_empty_are_distinct(self):
        import pandas as pd
        frame = pd.DataFrame({'time': np.arange(600), 'm0': np.ones(600)})
        def broken(*args, **kwargs):
            raise RuntimeError('deliberate fixture failure')
        failed = rcd_run(frame, upstream_rcd=broken)
        empty = rcd_run(frame, upstream_rcd=lambda *a, **k: {'ranks': []})
        self.assertEqual(failed['status'], 'FAILURE')
        self.assertEqual(empty['status'], 'SUCCESS')
        self.assertEqual(empty['ranks'], [])
        # These stubs test adapter semantics only, not qualified RCD execution.


if __name__ == '__main__':
    output_dir = Path(sys.argv[1])
    if not (output_dir/'run-contract.json').is_file():
        raise SystemExit('Pre-run contract required')
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'schema': 'TD12-E-FIXTURE-v1', 'scope': 'BOUNDED SYNTHETIC; not complete mission fixture suite',
              'tests_run': result.testsRun,
              'failures': [{'test': str(t), 'traceback': e} for t,e in result.failures],
              'errors': [{'test': str(t), 'traceback': e} for t,e in result.errors],
              'seconds': time.perf_counter()-start,
              'counterexamples': c5_counterexamples(),
              'not_run': ['complete C5 detector/event fixtures', 'real30development models',
                          'RCD qualified runtime', 'empirical sensitivity', 'full firewall']}
    (output_dir/'fixture-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
