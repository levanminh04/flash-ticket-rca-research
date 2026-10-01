"""Known-answer synthetic projection and locked evaluator boundary checks."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.task_g import locked_evaluation as e
from scripts.task_g import locked_provenance as p


class EvaluationTests(unittest.TestCase):
    def rows(self):
        return [{'case': 'artificial-0', 'dataset': 'SYNTHETIC_ONLY', 'repetition': 0,
                 'root_cause_service': 'synthetic-node-0', 'fault': 'ARTIFICIAL',
                 'inject_time': 620, 'time_start': 0}]

    def test_exact_projection_maps_literal_and_real_relative_time(self):
        labels = e.parse_truth_projection(self.rows(), ['artificial-0'], {'artificial-0': 0})
        self.assertEqual(labels[0]['tau_relative'], 620)
        self.assertEqual(labels[0]['root_key'], e.source_api.candidate_key('synthetic-node-0'))

    def test_projection_preserves_order_without_dropping_missing_roots(self):
        rows = self.rows() + [{**self.rows()[0], 'case': 'artificial-1', 'root_cause_service': 'absent'}]
        labels = e.parse_truth_projection(rows[::-1], ['artificial-0', 'artificial-1'], {'artificial-0': 0, 'artificial-1': 0})
        self.assertEqual(labels[0]['root_key'], e.source_api.candidate_key('synthetic-node-0'))
        self.assertEqual(labels[1]['root_key'], e.source_api.candidate_key('absent'))

    def test_missing_duplicate_extra_or_answer_projection_rejected(self):
        cases = ([], self.rows() * 2, [{**self.rows()[0], 'answers': 'CLOSED'}],
                 [{key: value for key, value in self.rows()[0].items() if key != 'fault'}])
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(p.Error):
                e.parse_truth_projection(rows, ['artificial-0'], {'artificial-0': 0})

    def test_clock_units_origin_mismatch_future_repair_rejected(self):
        for field, value in (('inject_time', None), ('inject_time', 620.5), ('inject_time', -1),
                             ('time_start', 1), ('root_cause_service', ''), ('fault', None)):
            with self.subTest(field=field, value=value), self.assertRaises(p.Error):
                e.parse_truth_projection([{**self.rows()[0], field: value}], ['artificial-0'], {'artificial-0': 0})

    def test_all_durable_failures_precede_artificial_truth(self):
        for reason in ('TAMPER', 'MISSING', 'DUPLICATE', 'STALE', 'SOURCE', 'CONFIG', 'ANCHOR'):
            with (self.subTest(reason=reason), patch.object(p, 'verify_seal', side_effect=p.Error(reason)),
                  patch.object(e, '_read_preparation_truth') as reader):
                with self.assertRaises(p.Error): e.evaluate_preparation()
                reader.assert_not_called()

    def test_final_permission_and_verification_precede_fixed_truth(self):
        with (patch.object(p, 'verify_seal', side_effect=p.Error('FINAL_CLOSED')),
              patch.object(e, '_read_final_truth') as reader):
            with self.assertRaises(p.Error): e.evaluate_final()
        reader.assert_not_called()

    def test_reproduction_ignores_only_declared_runtime_values(self):
        left = {'scores': [1., 2.], 'mask': [True, False], 'wall_seconds': 4., 'costs': {'x_seconds': 3.}}
        right = {**left, 'wall_seconds': 7., 'costs': {'x_seconds': 9.}}
        self.assertEqual(e.scientific_view(left), e.scientific_view(right))
        self.assertNotEqual(e.scientific_view(left), e.scientific_view({**right, 'scores': [2., 1.]}))
        self.assertNotEqual(e.scientific_view(left), e.scientific_view({**right, 'mask': [False, True]}))

    def test_locked_ties_and_seed_metric_mean(self):
        ties = e.frozen.score_service_vector([1., 1.], 0, candidate_count=2)
        self.assertAlmostEqual(ties['rr'], .75)
        outputs = [{'seed': seed, 'bins': 5, 'status': 'SUCCESS', 'ranks': ranks}
                   for seed, ranks in zip((420, 421, 422), (['m0', 'm1'], ['m1', 'm0'], ['m0', 'm1']))]
        result = e.frozen.rcd_seed_metrics(outputs, {'m0': 0, 'm1': 1}, 2, 0)
        self.assertAlmostEqual(result['mean']['rr'], (1 + .5 + 1) / 3)

    def test_full60_orchestration_statistics_exact_frozen_without_models(self):
        # Synthetic-only helper rows test orchestration/statistics, issue no seal.
        import test_evaluation as fixtures
        payload, labels = fixtures._numeric_fixture()
        labels[2]['root_index'] = None
        for operator in ('primary', 'secondary'):
            payload['cases'][0]['c1'][operator]['R'][0].update(status='FAILURE', scores=None)
        expected = e.frozen.evaluate_numeric_fixture_payload(payload, labels)
        keys = [e.source_api.candidate_key('artificial-root'), e.source_api.candidate_key('artificial-other')]
        truth = {index: {**label, 'root_key': keys[0] if label['root_index'] is not None else e.source_api.candidate_key('absent')}
                 for index, label in labels.items()}
        bindings = {'candidate_ids': keys, 'integrated_candidate_ids': {name: {} for name in e.frozen.DETECTORS}}
        envelope = {'commitment': {'scope': 'ACTUAL_FINAL60'}, '_verified': {'case_inventories': 60, 'receipt_sha256': '0' * 64}}
        with patch.object(e, '_cases', return_value=iter((row, bindings) for row in payload['cases'])):
            result = e.evaluate_verified(envelope, truth)
        for name in ('primary', 'secondary', 'primary_verdict', 'case_metrics', 'contextual', 'c5', 'monte_carlo'):
            self.assertEqual(result[name], expected[name], name)

    def test_scientific_time_windows_are_not_ignored_as_runtime(self):
        left = {'conversion_provenance': {'conversion_costs': {'c1_conversion_seconds': 1.},
                'clock_windows': {'known_window_reference_seconds': 300}},
                'quality': {'explanation_support_conversion_seconds': 2., 'missing_channels': 0}}
        right = copy.deepcopy(left)
        right['conversion_provenance']['conversion_costs']['c1_conversion_seconds'] = 9.
        right['quality']['explanation_support_conversion_seconds'] = 10.
        self.assertEqual(e.scientific_view(left), e.scientific_view(right))
        right['quality']['missing_channels'] = 1
        self.assertNotEqual(e.scientific_view(left), e.scientific_view(right))
        self.assertNotEqual(e.scientific_view({'bin_seconds': 5}), e.scientific_view({'bin_seconds': 10}))
        self.assertNotEqual(e.scientific_view({'known_window_reference_seconds': 300}),
                            e.scientific_view({'known_window_reference_seconds': 200}))

    def test_replay_measures_admission_and_charges_each_predeclared_case(self):
        # Unqualified orchestration fixture: no actual source, truth, seal or model.
        from scripts.task_g import locked_campaign as c
        class Store:
            def get(self,ref):return {'scientific_roles':{}}
            def put(self,value):return {'synthetic_only_unqualified':True}
        with tempfile.TemporaryDirectory(dir=p.ROOT/'cache',prefix='synthetic-only-replay-unit-') as directory:
            path=Path(directory)
            saved={'synthetic_only_unqualified':True,'full_verification_before_truth':True}
            (path/'evaluation.json').write_text(json.dumps(saved))
            (path/'cache').mkdir()
            contract={'reproduction_policy':{'numeric_replay_ordinals':[0,29,59]}}
            envelope={'commitment':{'case_inventory_manifest':[{} for _ in range(60)]}}
            with (patch.object(p,'ROOT',path),patch.object(p,'require_final_authorization',return_value=({},contract)),
                  patch.object(p,'verify_seal',return_value=envelope),patch.object(e,'_read_final_truth',return_value={}),
                  patch.object(e,'evaluate_verified',return_value={'synthetic_only_unqualified':True}),
                  patch.object(e.source_api,'open_final_source',return_value=object()),
                  patch.object(e.time,'perf_counter',side_effect=[10.,12.5]),
                  patch.object(p,'ShardStore',return_value=Store()),patch.object(p,'exclusive'),
                  patch.object(c,'compute_case',return_value=({'scientific_roles':{}},None)) as compute):
                result=e.reproduce_final()
            self.assertEqual([call.args[1] for call in compute.call_args_list],[0,29,59])
            self.assertTrue(all(call.args[2]==2.5 for call in compute.call_args_list))
            self.assertEqual(result['cohort_admission_wall_seconds'],2.5)


if __name__ == '__main__': unittest.main()
