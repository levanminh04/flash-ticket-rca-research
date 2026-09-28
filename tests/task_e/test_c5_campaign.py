"""Analytic C5 controller qualification; synthetic inputs and no child models.

Expected values below follow declared arithmetic, chronology and fixed rosters.
The numeric-model implementation is intentionally not used as an oracle.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e import c5_development as campaign
from scripts.task_e.calibration import EvaluationError, select_q
from scripts.task_e.contract import DEV_IDS, REVISION, TD_SHA256, opaque_handle, registry
from scripts.task_e.execution import file_sha, require_contract, save_json, save_npz


def scenario(case):
    _, root, fault, _ = case.split('_')
    return root, fault


def score_roster(high=1.):
    # Twenty normal bins, one highest normal observation, two positive bins.
    # q=.95 -> 0, producing TP2/FP1/F1=.8. q=.975/.99 -> high, F1=1.
    ends = np.arange(185, 295, 5, dtype=np.int64)
    return {case: {'scenario': scenario(case), 'starts': ends-5, 'ends': ends,
                   'tau': 280, 'warmup_end': 180,
                   'scores': np.array([0.]*19+[high]+[2*high]*2)} for case in DEV_IDS}


def model(config, channel_types):
    applicable = np.ones((1, 3), dtype=bool)
    if config['modalities'] == 'MT':
        applicable[:, 2] = False
    finite = np.where(applicable, 0., np.nan)
    finite_one = np.where(applicable, 1., np.nan)
    fit_mask = np.broadcast_to(applicable, (24, 1, 3)).copy()
    cal_mask = np.broadcast_to(applicable, (12, 1, 3)).copy()
    return {'E': applicable, 'model_mask': applicable, 'fit_model_mask': applicable,
            'fit_target_mask': fit_mask, 'calibration_target_mask': cal_mask,
            'centers': finite, 'scales': finite_one, 'channel_types': channel_types,
            'coefficients': np.broadcast_to(finite[:, :, None], (1, 3, 5)).copy(),
            'intercepts': finite, 'residual_centers': finite, 'residual_scales': finite_one,
            'calibration_errors': np.broadcast_to(finite, (12, 1, 3)).copy(),
            'calibration_predictions': np.broadcast_to(finite, (12, 1, 3)).copy(),
            'degrees': {'out': np.zeros((1, 3), dtype=np.int64)},
            'diagnostics': {'ridge': [[None]*3], 'singleton_scale': np.zeros((1, 3), dtype=bool),
                            'constant_scale': applicable, 'scale_floor_used': applicable,
                            'residual_floor_used': applicable}}


class FakeWorker:
    calls = []
    tv_failure = False
    fail_at = None

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def ping(self):
        return {'synthetic_worker': True}

    def fit_c5(self, warmup, adj, channel_types, fit_services, configs):
        self.configs = configs
        self.calls.append(('fit', warmup.copy()))
        return {'next_bin_index': len(warmup), 'models': [model(cfg, channel_types) for cfg in configs]}

    def score_c5(self, values, index):
        self.calls.append(('score', index, values.copy()))
        if index == self.fail_at:
            raise RuntimeError('synthetic declared worker failure')
        results = []
        for config in self.configs:
            available = np.ones((1, 3), dtype=bool)
            if config['modalities'] == 'MT':
                available[:, 2] = False
            z = np.where(available, values, np.nan)
            component = np.where(available, 0., np.nan)
            failed_tv = self.tv_failure and config['modalities'] == 'MTL'
            results.append({'endpoint': (index+1)*5, 'target_mask': available, 'z': z,
                'predictions': component, 'errors': component, 'residuals': component,
                'score': 0., 'tv_score': np.nan if failed_tv else 0.,
                'tv_channels': np.full(3, np.nan) if failed_tv else np.where(available[0], 0., np.nan),
                'tv_edge_counts': None if failed_tv else np.zeros(3, dtype=np.int64),
                'scored_channels': int(available.sum()), 'local_magnitude': float(np.nanmax(z)),
                'tv_failure': 'synthetic TV overflow' if failed_tv else None})
        return {'results': results}


class TVFailedWorker(FakeWorker):
    tv_failure = True


class MidReplayFailedWorker(FakeWorker):
    fail_at = 37


class RegistryAndAdmissionTests(unittest.TestCase):
    def test_primary_exact_18_and_ofat_seven_without_hidden_cartesian_search(self):
        configs = campaign.registered_configs(.01)
        self.assertEqual(len(configs), 18)
        self.assertEqual({(c['arm'], c['modalities'], c['lambda']) for c in configs},
                         {(a, m, p) for a in ('G', 'L', 'ALL') for m in ('MTL', 'MT') for p in (.1, 1., 10.)})
        variants = campaign.sensitivity_registry(.01, 1.)
        self.assertEqual([v['id'] for v in variants], ['bin10', 'prefix240', 'lag3',
            'residual-floor-0.001', 'residual-floor-0.1', 'relative-floor-0.0001', 'relative-floor-0.001'])
        for variant in variants:
            self.assertEqual(len(variant['configs']), 6)
            self.assertEqual({c['lambda'] for c in variant['configs']}, {1.})
        with self.assertRaises(ValueError):
            campaign.registered_configs(.01, q=.97)

    def test_c1_actual_selection_schema_and_pinned_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'selection.json'
            save_json(path, {'local_config': {'floor': .001, 'pool': 'max', 'fusion': 'max'},
                             'ppr_config': {'operator': 'ppr', 'direction': 'reverse', 'damping': .85}})
            pins = {str(path.resolve()): file_sha(path)}
            self.assertEqual(campaign._c1_floor(path, pins), .001)
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'changed'):
                campaign._c1_floor(path, pins)

    def test_smoke_is_exact_predetermined_ten_and_requires_all_thirty_audit_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            save_json(root/'run-contract.json', {'stage': 'development-audit',
                'td': {'sha256': TD_SHA256}, 'dataset_revision': REVISION})
            save_json(root/'loader-summary.json', {'planned': 30, 'cases': [{'case': c} for c in DEV_IDS]})
            paths = [root/'run-contract.json', root/'loader-summary.json']
            for case in DEV_IDS:
                path = root/'case-audits'/(opaque_handle(case)+'.json')
                save_json(path, {'case': case, 'handle': opaque_handle(case)})
                paths.append(path)
            pins = {str(p.resolve()): file_sha(p) for p in paths}
            planned, _ = campaign.read_roster(root, pins, 'smoke')
            self.assertEqual(tuple(registry()['smoke_ids']), planned)
            self.assertEqual(len(planned), 10)
            self.assertEqual(len({scenario(c) for c in planned}), 10)
            broken = {'planned': 30, 'cases': [{'case': c} for c in DEV_IDS]+[{'case': DEV_IDS[0]}]}
            (root/'loader-summary.json').write_text(json.dumps(broken), encoding='utf-8')
            pins[str((root/'loader-summary.json').resolve())] = file_sha(root/'loader-summary.json')
            with self.assertRaisesRegex(ValueError, 'exact development30'):
                campaign.read_roster(root, pins, 'full')

    def test_numeric_cache_requires_audit_hash_graph_and_exact_grid(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handle = opaque_handle(DEV_IDS[0])
            path = root/'intermediates'/handle/'c5_primary.npz'
            arrays = {'values': np.ones((38, 1, 3)), 'adj': np.zeros((1, 1), dtype=bool),
                      'channel_types': np.array([0, 1, 2]), 'fit_service_mask': np.ones(1, dtype=bool),
                      'endpoints': np.arange(1, 39)*5}
            save_npz(path, **arrays)
            digest = file_sha(path)
            report = {'handle': handle, '_case_audit_sha256': 'audit-pin',
                'numeric_files': [{'path': str(path), 'sha256': digest}],
                'profiles': {'c5_primary': {'status': 'MATERIALIZED', 'audit': {'graph': {
                    'adjacency_sha256': hashlib.sha256(arrays['adj'].tobytes()).hexdigest()}}}}}
            loaded, _ = campaign.load_numeric(root, report, 'primary', {str(path.resolve()): digest})
            np.testing.assert_array_equal(loaded['endpoints'], arrays['endpoints'])
            with self.assertRaisesRegex(ValueError, 'Unpinned'):
                campaign.load_numeric(root, report, 'primary', {})
            report['profiles']['c5_primary']['audit']['graph']['adjacency_sha256'] = 'wrong'
            with self.assertRaisesRegex(ValueError, 'Frozen graph'):
                campaign.load_numeric(root, report, 'primary', {str(path.resolve()): digest})


class AnalyticCalibrationTests(unittest.TestCase):
    def test_joint_lambda_uses_input_mask_normal_bins_and_registered_tie(self):
        ends = np.array([185, 190, 195])
        inputs = {case: {'scenario': scenario(case), 'starts': ends-5, 'ends': ends,
                  'warmup_end': 180, 'tau': 190, 'targets': np.zeros((3, 1, 2)),
                  'eligible': np.ones((3, 1, 2), dtype=bool)} for case in DEV_IDS}
        predictions = {}
        for penalty in (.1, 1., 10.):
            predictions[penalty] = {}
            for arm, error in zip(('G', 'L', 'ALL'), (1., 2., 3.)):
                arrays = {}
                for case in DEV_IDS:
                    value = np.full((3, 1, 2), error if penalty != .1 else 4.)
                    value[2] = 1e100  # Post-injection errors cannot affect lambda.
                    arrays[case] = value
                predictions[penalty][arm] = arrays
        chosen = campaign.compact_lambda_selection(inputs, predictions, DEV_IDS)
        self.assertEqual(chosen['objectives'], {.1: 4., 1.: 2., 10.: 2.})
        self.assertEqual(chosen['selected_lambda'], 1.)
        self.assertNotIn('support_ids', chosen['details'][1.]['arms']['G'])
        predictions[1.]['G'][DEV_IDS[0]][0, 0, 0] = np.nan
        with self.assertRaisesRegex(EvaluationError, 'Nonfinite prediction'):
            campaign.compact_lambda_selection(inputs, predictions, DEV_IDS)

    def test_q_fold_support_and_hand_calculated_f1(self):
        cases = score_roster()
        chosen = select_q(cases, DEV_IDS)
        self.assertEqual(chosen['selected_q'], .99)
        self.assertEqual(chosen['objectives'], {.95: .8, .975: 1., .99: 1.})
        fixed = campaign.fixed_q_evaluation(cases, DEV_IDS, .95)
        self.assertAlmostEqual(fixed['summary']['macro']['f1'], .8)
        self.assertEqual(fixed['full_development_calibration']['threshold'], 0.)
        for fold in fixed['folds']:
            self.assertEqual(len(fold['train_ids']), 24)
            self.assertEqual(len(fold['heldout_ids']), 6)
            self.assertEqual(fold['normal_endpoints'], 480)
            self.assertEqual({i[0] for i in fold['normal_support_ids']}, set(fold['train_ids']))
            self.assertTrue(all(i[2] <= 280 for i in fold['normal_support_ids']))

    def test_forecast_hierarchy_does_not_pool_unequal_channel_counts(self):
        ends = np.array([185, 190])
        inputs = {case: {'scenario': scenario(case), 'starts': ends-5, 'ends': ends,
                  'tau': 190, 'targets': np.zeros((2, 1, 2)),
                  'eligible': np.ones((2, 1, 2), dtype=bool)} for case in DEV_IDS}
        base = {case: np.ones((2, 1, 2)) for case in DEV_IDS}
        inputs[DEV_IDS[0]]['eligible'][0, 0, 1] = False
        base[DEV_IDS[0]][:, 0] = [[2., 1e100], [6., 10.]]
        predictions = {p: {arm: deepcopy(base) for arm in ('G', 'L', 'ALL')} for p in (.1, 1., 10.)}
        chosen = campaign.compact_lambda_selection(inputs, predictions, DEV_IDS)
        # Special case: mean(bin1=2, bin2=mean(6,10)=8)=5.
        # Its cell=(5+1+1)/3=7/3, overall=(7/3+9)/10=17/15.
        self.assertEqual(chosen['details'][1.]['arms']['G']['case_losses'][DEV_IDS[0]], 5.)
        self.assertAlmostEqual(chosen['objectives'][1.], 17/15)
        self.assertEqual(chosen['selected_lambda'], 1.)

    def test_lambda_deletion_reaggregation_reselects_and_rechecks_coverage(self):
        ends = np.array([185])
        inputs = {case: {'scenario': scenario(case), 'starts': ends-5, 'ends': ends,
                  'tau': 185, 'targets': np.zeros((1, 1, 1)),
                  'eligible': np.ones((1, 1, 1), dtype=bool)} for case in DEV_IDS}
        special = scenario(DEV_IDS[0])
        predictions = {p: {arm: {case: np.full((1, 1, 1),
            4. if p == .1 else 2. if p == 10. else 20. if scenario(case) == special else 1.)
            for case in DEV_IDS} for arm in ('G', 'L', 'ALL')} for p in (.1, 1., 10.)}
        chosen = campaign.compact_lambda_selection(inputs, predictions, DEV_IDS)
        self.assertEqual(chosen['selected_lambda'], 10.)
        deletion = campaign.leave_cell_lambda(inputs, predictions, DEV_IDS, chosen)
        dropped = next(row for row in deletion['deletions'] if tuple(row['excluded_scenario']) == special)
        self.assertEqual(dropped['selected_lambda'], 1.)
        self.assertEqual(dropped['objectives'], {.1: 4., 1.: 1., 10.: 2.})
        # Exactly 24/30 cases pass primary support. Deleting a fully supported
        # cell leaves 21/27 (<80%) and must not manufacture a deletion winner.
        for case in DEV_IDS[-6:]:
            inputs[case]['eligible'][:] = False
        chosen = campaign.compact_lambda_selection(inputs, predictions, DEV_IDS)
        deletion = campaign.leave_cell_lambda(inputs, predictions, DEV_IDS, chosen)
        dropped = next(row for row in deletion['deletions'] if tuple(row['excluded_scenario']) == special)
        self.assertEqual(dropped['status'], 'INVALID')
        self.assertIn('21/27', dropped['error'])

    def test_leave_cell_q_refit_uses_reselected_lambda(self):
        inputs = score_roster()
        score_cases = {f'{arm}-{modality}-lambda{penalty:g}': score_roster(penalty)
                       for arm in ('G', 'L', 'ALL') for modality in ('MTL', 'MT') for penalty in (.1, 1., 10.)}
        deletion = {'deletions': [{'excluded_scenario': scenario(DEV_IDS[0]),
                                  'status': 'VALID', 'selected_lambda': 10.}]}
        report = campaign.leave_cell_cascade(deletion, inputs, score_cases,
            {modality: score_roster(2.) for modality in ('MTL', 'MT')}, DEV_IDS)
        detail = report['deletions'][0]['detectors']
        self.assertEqual(detail['G-MTL']['selected_q'], .99)
        self.assertEqual(detail['G-MTL']['full_threshold'], 10.)
        self.assertEqual(detail['TV-MTL']['full_threshold'], 2.)
        self.assertFalse(report['primary_registry_changed'])

    def test_events_keep_tau_endpoint_pre_injection_and_continuous_refractory(self):
        ends = np.arange(185, 505, 5)
        cases = {'case': {'scenario': ('root', 'fault'), 'starts': ends-5, 'ends': ends,
                          'tau': 195, 'warmup_end': 180, 'scores': np.full(len(ends), 2.)}}
        events = campaign.replay_events(cases, ('case',), [{'heldout_ids': ['case'], 'threshold': 1.}], 1.)
        result = events['cases']['case']['OOF']
        self.assertEqual(result['triggers'], [195., 495.])
        self.assertEqual(result['pre_injection_triggers'], 1)
        self.assertEqual(result['first_post_injection_delay'], 300.)
        self.assertEqual(result['observed_normal_hours'], 15/3600)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        FakeWorker.calls = []

    def fixture(self, root):
        save_json(root/'run-contract.json', {'stage': 'c5-full-synthetic'})
        case = DEV_IDS[0]
        report = {'handle': opaque_handle(case), 'metadata': {'time_start': 1000, 'time_end': 1195,
                  'inject_time': 1190, 'root_cause_service': scenario(case)[0], 'fault': scenario(case)[1]},
                  'profiles': {'c5_primary': {'tau_relative': 190}}}
        arrays = {'values': np.ones((39, 1, 3)), 'adj': np.zeros((1, 1), dtype=bool),
                  'channel_types': np.array([0, 1, 2]), 'fit_service_mask': np.ones(1, dtype=bool),
                  'endpoints': np.arange(1, 40)*5}
        return case, report, arrays, campaign.registered_configs(.01)

    def test_fit_receives_only_warmup_then_exact_sequential_bins_and_seals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case, report, arrays, configs = self.fixture(root)
            arrays['values'][36:] = 7.
            with patch.object(campaign, 'NumericWorker', FakeWorker):
                receipt = campaign.run_case(root, 'primary', case, report, arrays, {'pin': 'source'}, configs, 1.)
            self.assertEqual(receipt['status'], 'COMPLETE')
            self.assertEqual(FakeWorker.calls[0][0], 'fit')
            self.assertEqual(FakeWorker.calls[0][1].shape, (36, 1, 3))
            self.assertTrue((FakeWorker.calls[0][1] == 1).all())
            self.assertEqual([c[1] for c in FakeWorker.calls[1:]], [36, 37, 38])
            artifact = root/'predictions'/'primary'/report['handle']
            self.assertEqual({p['file'] for p in receipt['artifacts']},
                             {'predictions.npz', 'frozen-models.npz', 'numeric-input.npz'})
            with self.assertRaises(FileNotFoundError):
                campaign.evaluation_inputs(root, 'primary', 'primary', (case,), {case: report}, configs)
            campaign.seal_campaign_predictions(root, [{'id': 'primary'}], (case,), {case: report})
            _, _, scores, _, failed = campaign.evaluation_inputs(root, 'primary', 'primary', (case,), {case: report}, configs)
            self.assertFalse(failed)
            np.testing.assert_array_equal(scores['G-MTL-lambda1'][case]['ends'], [185, 190, 195])
            with (artifact/'predictions.npz').open('ab') as stream:
                stream.write(b'changed')
            with self.assertRaisesRegex(ValueError, 'changed after sealing'):
                campaign._load_sealed(root, 'primary', report)

    def test_tv_failure_remains_separate_from_valid_forecast(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case, report, arrays, configs = self.fixture(root)
            with patch.object(campaign, 'NumericWorker', TVFailedWorker):
                receipt = campaign.run_case(root, 'primary', case, report, arrays, {}, configs, 1.)
            self.assertEqual(receipt['status'], 'COMPLETE')
            self.assertEqual(len(receipt['tv_failures']), 27)  # Nine MTL configs x three bins.
            campaign.seal_campaign_predictions(root, [{'id': 'primary'}], (case,), {case: report})
            _, _, scores, tv, failed = campaign.evaluation_inputs(root, 'primary', 'primary', (case,), {case: report}, configs)
            self.assertFalse(failed)
            self.assertFalse(scores['G-MTL-lambda1'][case]['failed'])
            self.assertTrue(tv['MTL'][case]['failed'])
            self.assertFalse(tv['MT'][case]['failed'])
            with np.load(root/'predictions/primary'/report['handle']/'predictions.npz') as saved:
                self.assertTrue((saved['tv_edge_counts'][0] == -1).all())

    def test_failure_retains_partial_arrays_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case, report, arrays, configs = self.fixture(root)
            with patch.object(campaign, 'NumericWorker', MidReplayFailedWorker):
                receipt = campaign.run_case(root, 'primary', case, report, arrays, {}, configs, 1.)
            self.assertEqual(receipt['status'], 'METHOD_FAILURE')
            self.assertEqual(receipt['completed_worker_calls'], 1)
            self.assertEqual(receipt['failed_configs'], list(range(18)))
            with self.assertRaises(FileExistsError):
                campaign.run_case(root, 'primary', case, report, arrays, {}, configs, 1.)

    def test_mt_mtl_component_residual_drift_is_rejected(self):
        configs = campaign.registered_configs(.01)
        worker = FakeWorker()
        fitted = worker.fit_c5(np.ones((36, 1, 3)), np.zeros((1, 1), dtype=bool), np.array([0, 1, 2]),
                              np.ones(1, dtype=bool), configs)
        campaign.assert_common_input_ids(fitted['models'], configs)
        results = worker.score_c5(np.ones((1, 3)), 36)['results']
        results[3]['residuals'][0, 0] = 1.
        with self.assertRaisesRegex(ValueError, 'common scored component'):
            campaign.assert_common_score_ids(results, configs, np.array([0, 1, 2]))

    def test_lambda_f1_diagnostic_failure_does_not_replace_primary_selection(self):
        scores = {f'{arm}-{modality}-lambda{penalty:g}': score_roster()
                  for arm in ('G', 'L', 'ALL') for modality in ('MTL', 'MT') for penalty in (.1, 1., 10.)}
        reports = {case: {'handle': opaque_handle(case)} for case in DEV_IDS}
        chosen = {'selected_lambda': 1., 'objectives': {.1: 3., 1.: 1., 10.: 2.}, 'details': {}}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(campaign, 'evaluation_inputs', return_value=(
                    {}, {}, scores, {m: score_roster() for m in ('MTL', 'MT')}, False)), \
                    patch.object(campaign, 'compact_lambda_selection', return_value=chosen), \
                    patch.object(campaign, 'leave_cell_lambda', return_value={'deletions': []}), \
                    patch.object(campaign, 'leave_cell_cascade', return_value={'deletions': []}), \
                    patch.object(campaign, 'leave_cell_q', return_value={'deletions': []}), \
                    patch.object(campaign, 'fixed_q_evaluation', side_effect=EvaluationError('diagnostic coverage')):
                selected = campaign.evaluate_primary(Path(directory), DEV_IDS, reports,
                                                       campaign.registered_configs(.01), .01)
            self.assertEqual(selected['detectors']['G-MTL']['status'], 'VALID')
            self.assertEqual(selected['detectors']['G-MTL']['selected_q'], .99)
            self.assertEqual(set(selected['detectors']['G-MTL']['lambda_f1_diagnostic_errors']), {.1, 10.})
            self.assertEqual(selected['detectors']['TV-MTL']['status'], 'VALID')


if __name__ == '__main__':
    output = Path(sys.argv[1])
    require_contract(output, 'development')
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    save_json(output/'c5-controller-fixture-report.json', {
        'tests_run': result.testsRun,
        'failures': [{'test': str(t), 'traceback': e} for t, e in result.failures],
        'errors': [{'test': str(t), 'traceback': e} for t, e in result.errors],
        'seconds': time.perf_counter()-started,
        'scope': 'Synthetic controller and analytic expectations; no raw data or child model execution'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
