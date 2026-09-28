"""Independent TD §7.1 synthetic adapter/controller qualification.

Recovery scope: this file alone is owned by the reviewer; the coordinator owns
integrated_development.py. Initial source review found missing all-detector
denominators, missing-origin crashes, unsealed failure endpoints, unchecked hook
identity/duplicates, and incomplete source/cost provenance. Tests below express
the protocol expectations, not snapshots of any actual development outcomes.
Only the coordinator may execute this suite under a new pinned run contract.
No corpus file, final case, external process, or real model is used here.
"""
from __future__ import annotations

from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e import integrated_development as campaign
from scripts.task_e.contract import DEV_IDS, opaque_handle
from scripts.task_e.execution import file_sha, require_contract, save_json
from scripts.task_e.input_adapters import integrated_bundle
from scripts.task_e.loader import TRACE_FIELDS, LoaderError
from scripts.task_e.ranking import local_scores
from scripts.task_e.worker import decode_message

RUN = None
DETECTORS = tuple(f'{arm}-{modality}' for modality in ('MTL', 'MT')
                  for arm in ('G', 'L', 'ALL', 'TV'))
ORIGIN = 1_000_000
METRICS = ('rr', 'hit1', 'hit3', 'hit5', 'ndcg5')


def synthetic_raw(root='b', *, origin=ORIGIN):
    ticks = np.arange(1101)
    rows = []
    for tick in ticks:
        for service, span, parent in (('a', 'parent', ''), (root, 'child', 'parent')):
            rows.append(dict(zip(TRACE_FIELDS, ['clock', 'trace' + str(tick), span, service,
                'method', 'operation', parent, (origin + tick) * 1000,
                (origin + tick) * 1_000_000, 1, 0])))
    return {'metrics': pd.DataFrame({'time': origin + ticks, 'a_cpu': ticks.astype(float),
                                     root + '_cpu': ticks.astype(float) + 1}),
            'traces': pd.DataFrame(rows),
            'logs': pd.DataFrame({'timestamp': [origin + 50, origin + 350, origin + 399],
                                 'container_name': [root] * 3, 'message': ['x'] * 3})}


class QualifiedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if RUN is None:
            raise RuntimeError('Coordinator-created source-pinned run is required before fixtures')


class IntegratedAdapterTests(QualifiedTest):
    def test_exact_half_open_windows_reference_graph_and_future_invariance(self):
        raw = synthetic_raw()
        selected = integrated_bundle(raw, ORIGIN + 400)
        self.assertEqual(selected['service_names'], ['a', 'b'])
        self.assertEqual(selected['ref'].shape, (2, 12, 30))
        self.assertEqual(selected['query'].shape, (2, 12, 6))
        self.assertEqual(selected['ref'][0, 8, 0], 44.5)
        self.assertEqual(selected['ref'][0, 8, -1], 334.5)
        self.assertEqual(selected['query'][0, 8, 0], 344.5)
        self.assertEqual(selected['query'][0, 8, -1], 394.5)
        np.testing.assert_array_equal(selected['adj'], [[False, True], [False, False]])
        changed = deepcopy(raw)
        changed['metrics'].loc[changed['metrics'].time >= ORIGIN + 400, 'a_cpu'] = 1e100
        future = changed['traces'].startTimeMillis >= (ORIGIN + 400) * 1000
        changed['traces'].loc[future, 'serviceName'] = 'future-only'
        changed['logs'] = pd.concat([changed['logs'], pd.DataFrame({
            'timestamp': [ORIGIN + 400], 'container_name': ['future-only'], 'message': ['future']})])
        again = integrated_bundle(changed, ORIGIN + 400)
        for key in ('ref', 'query', 'adj', 'channel_types'):
            np.testing.assert_array_equal(again[key], selected[key])
        self.assertEqual(again['service_names'], selected['service_names'])
        with self.assertRaises(LoaderError):
            integrated_bundle(raw, ORIGIN + 359)
        self.assertEqual(integrated_bundle(raw, ORIGIN + 360)['ref'].shape[2], 30)

    def test_window_conflicts_are_shared_failure_while_outside_conflicts_are_ignored(self):
        raw = synthetic_raw()
        inside = raw['traces'].loc[(raw['traces'].startTimeMillis == (ORIGIN + 100) * 1000)
                                   & (raw['traces'].serviceName == 'a')].copy()
        inside['operationName'] = 'contradiction'
        bad = {**raw, 'traces': pd.concat([raw['traces'], inside])}
        with self.assertRaisesRegex(LoaderError, 'Conflicting'):
            integrated_bundle(bad, ORIGIN + 400)
        later = inside.copy()
        later['startTimeMillis'] = (ORIGIN + 400) * 1000
        outside = {**raw, 'traces': pd.concat([raw['traces'], later])}
        expected = integrated_bundle(raw, ORIGIN + 400)
        actual = integrated_bundle(outside, ORIGIN + 400)
        for key in ('ref', 'query', 'adj'):
            np.testing.assert_array_equal(actual[key], expected[key])

    def test_conflicting_metric_invalidates_both_windows_without_vetoing_other_modalities(self):
        raw = synthetic_raw()
        duplicate = raw['metrics'].loc[raw['metrics'].time == ORIGIN + 390].copy()
        duplicate['a_cpu'] = -500.
        raw['metrics'] = pd.concat([raw['metrics'], duplicate])
        bundle = integrated_bundle(raw, ORIGIN + 400)
        self.assertTrue(np.isnan(bundle['ref'][0, 8]).all())
        self.assertTrue(np.isnan(bundle['query'][0, 8]).all())
        self.assertTrue(np.isfinite(bundle['ref'][1, 8]).all())
        self.assertTrue(np.isfinite(bundle['query'][:, 10]).all())

    def test_log_absence_is_missing_and_no_reference_count_cannot_be_an_anomaly(self):
        raw = synthetic_raw()
        raw['logs'] = pd.DataFrame({'timestamp': [ORIGIN + 350],
                                   'container_name': ['b'], 'message': ['query-only']})
        bundle = integrated_bundle(raw, ORIGIN + 400)
        config = {'floor': .01, 'pool': 'max', 'fusion': 'availablemean', 'include_logs': True}
        local = local_scores(bundle['ref'], bundle['query'], bundle['channel_types'], config)
        self.assertEqual(local['diagnostics']['reference_min_bins'], 24)
        self.assertEqual(local['diagnostics']['query_min_bins'], 5)
        self.assertFalse(local['masks']['channels'][:, 11].any())
        self.assertEqual(local['diagnostics']['channel_reasons'][1][11], 'absent_reference_count')
        raw['logs'] = None
        missing = integrated_bundle(raw, ORIGIN + 400)
        self.assertTrue(np.isnan(missing['ref'][:, 11]).all())
        self.assertFalse(missing['audit']['log_ref']['loaded'])
        for key in ('ref', 'query'):
            np.testing.assert_array_equal(missing[key][:, :11], bundle[key][:, :11])

    def test_twentyfour_reference_five_query_gates_and_query_only_isolate(self):
        raw = synthetic_raw()
        raw['traces'] = raw['traces'].loc[(raw['traces'].serviceName == 'a') |
            (raw['traces'].startTimeMillis >= (ORIGIN + 340) * 1000)].copy()
        bundle = integrated_bundle(raw, ORIGIN + 400)
        self.assertEqual(bundle['service_names'], ['a', 'b'])
        self.assertFalse(bundle['adj'].any())
        config = {'floor': .01, 'pool': 'max', 'fusion': 'max', 'include_logs': True}
        result = local_scores(bundle['ref'], bundle['query'], bundle['channel_types'], config)
        self.assertEqual(result['diagnostics']['channel_reasons'][1][10], 'absent_reference_count')
        ref, query = bundle['ref'].copy(), bundle['query'].copy()
        ref[1, 8, 24:] = np.nan
        query[1, 8, 5:] = np.nan
        self.assertTrue(local_scores(ref, query, bundle['channel_types'], config)['masks']['channels'][1, 8])
        query[1, 8, 4] = np.nan
        self.assertFalse(local_scores(ref, query, bundle['channel_types'], config)['masks']['channels'][1, 8])
        query[1, 8, 4] = bundle['query'][1, 8, 4]
        ref[1, 8, 23] = np.nan
        self.assertFalse(local_scores(ref, query, bundle['channel_types'], config)['masks']['channels'][1, 8])


class FakeNumericWorker:
    calls = []
    behaviors = {}
    stderr = 'synthetic worker; no subprocess'

    def __init__(self, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def c1(self, ref, query, adj, channel_types, local, ranks):
        endpoint = int(round(float(query[0, 8, 0]) + 55.5))
        type(self).calls.append({'endpoint': endpoint, 'ref': ref.copy(), 'query': query.copy(),
                                'adj': adj.copy(), 'types': channel_types.copy(),
                                'local': deepcopy(local), 'ranks': deepcopy(ranks)})
        behavior = self.behaviors.get(endpoint)
        if behavior == 'raise':
            raise RuntimeError('Invented worker failure')
        scores = np.array([1., 2.])
        if behavior == 'short':
            scores = np.array([1.])
        elif behavior == 'nonfinite':
            scores = np.array([1., np.nan])
        elif behavior == 'wrong':
            scores = np.array([2., 1.])
        numeric = np.zeros((2, 12), dtype=bool)
        if behavior == 'numeric':
            numeric[0, 8] = True
        return {'evidence': {'local': np.array([1., 2.]),
                            'masks': {'channels': np.ones((2, 12), dtype=bool)},
                            'diagnostics': {'numerical_channel_failures': numeric}},
                'rankings': [{'scores': scores, 'diagnostics': {'residual_inf': 0.}}]}


def fixture_inputs(base, items, *, tau=600, missing_origins=()):
    audit = base / 'audit'
    paths = []
    for case in DEV_IDS:
        _, root, fault, _ = case.split('_')
        report = {'case': case, 'handle': opaque_handle(case),
                  'metadata': {'case': case, 'root_cause_service': root,
                               'fault': fault, 'inject_time': ORIGIN + tau},
                  'profiles': {'c5_primary': {'status': 'MATERIALIZED', 's0': ORIGIN}}}
        if case in missing_origins:
            report['profiles']['c5_primary'] = {'status': 'FAILURE', 'error': 'invented input failure'}
        path = audit / 'case-audits' / (opaque_handle(case) + '.json')
        save_json(path, report)
        paths.append(path)
    selected = base / 'selection.json'
    save_json(selected, {'local_config': {'floor': .01, 'pool': 'max', 'fusion': 'availablemean'},
                         'ppr_config': {'operator': 'ppr', 'direction': 'reverse', 'damping': .85}})
    hooks = base / 'hooks.json'
    save_json(hooks, {'schema': 'TD13-C5-DEVELOPMENT-v1', 'items': items,
                     'first_only_for_composed_metrics': True,
                     'no_R_or_external_comparators_per_trigger': True})
    acquisition = base / 'acquisition.json'
    save_json(acquisition, {'files': [], 'synthetic_only': True})
    paths += [selected, hooks, acquisition]
    contract = {'stage': 'development synthetic integrated controller',
                'source_files': [{'path': str(path.resolve()), 'sha256': file_sha(path)}
                                 for path in sorted((W / 'scripts/task_e').glob('*.py'))],
                'inputs': [{'path': str(path.resolve()), 'sha256': file_sha(path)} for path in paths]}
    return audit, acquisition, selected, hooks, contract


def hook(case, detector, triggers):
    return {'case': case, 'handle': opaque_handle(case), 'detector': detector, 'triggers': triggers,
            'first_post_injection_trigger': next((t for t in triggers if t > 600), None),
            'threshold_mode': 'OOF', 'profile': 'TD12-INTEGRATED-MTL'}


class IntegratedControllerTests(QualifiedTest):
    def setUp(self):
        FakeNumericWorker.calls = []
        FakeNumericWorker.behaviors = {}

    def execute(self, base, items, *, tau=600, missing_origins=(), check_evaluation=False):
        run = base / 'run'
        run.mkdir()
        audit, acquisition, selected, hooks, contract = fixture_inputs(
            base, items, tau=tau, missing_origins=missing_origins)
        # Use the actual file-backed admission path. The controller seals these
        # bytes, so a mocked loader alone is not a complete fixture contract.
        save_json(run / 'run-contract.json', contract)
        original_eval = campaign.tie_metrics
        checked_seals = []
        expected_seals = [run / 'seals' / f'{opaque_handle(case)}-{int(endpoint)}.json'
                          for case in DEV_IDS
                          for endpoint in sorted({t for item in items if item['case'] == case
                                                  for t in item['triggers']})]

        def after_seal(scores, root, *, failed=False):
            expected = expected_seals[len(checked_seals)]
            self.assertTrue(expected.is_file(), 'This exact endpoint must be sealed before evaluation')
            seal = json.loads(expected.read_text(encoding='utf-8'))
            self.assertEqual(seal['contract_sha256'], file_sha(run / 'run-contract.json'))
            self.assertTrue(seal['before_evaluation'])
            for artifact in seal['artifacts']:
                self.assertEqual(file_sha(artifact['path']), artifact['sha256'])
            checked_seals.append(str(expected))
            return original_eval(scores, root, failed=failed)

        argv = ['integrated_development.py', str(run), '--audit-root', str(audit),
                '--acquisition', str(acquisition), '--c1-selection', str(selected), '--c5-hook', str(hooks)]
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, 'argv', argv))
            stack.enter_context(patch.object(campaign, 'NumericWorker', FakeNumericWorker))
            stack.enter_context(patch.object(campaign, 'read_acquired', side_effect=lambda _, row:
                                            synthetic_raw(row['root_cause_service'])))
            if check_evaluation:
                stack.enter_context(patch.object(campaign, 'tie_metrics', side_effect=after_seal))
            stack.enter_context(redirect_stdout(io.StringIO()))
            campaign.main()
        result = json.loads((run / 'integrated-results.json').read_text(encoding='utf-8'))
        return run, result, checked_seals

    def assert_endpoint_sealed(self, run, case, endpoint):
        path = run / 'seals' / f'{opaque_handle(case)}-{endpoint}.json'
        self.assertTrue(path.is_file(), 'Missing immutable trigger receipt')
        seal = json.loads(path.read_text(encoding='utf-8'))
        self.assertTrue(seal['before_evaluation'])
        self.assertEqual(seal['profile'], 'TD12-INTEGRATED-MTL')
        self.assertEqual(seal['past_windows_relative'], [endpoint - 360, endpoint - 60, endpoint])
        self.assertIn('status', seal)
        self.assertIn('source_hashes', seal)
        self.assertIn('config', seal)
        identities = json.dumps(seal['source_hashes'], sort_keys=True)
        for source in (run.parent / 'hooks.json', run.parent / 'selection.json',
                       run.parent / 'acquisition.json',
                       run.parent / 'audit/case-audits' / (opaque_handle(case) + '.json')):
            self.assertIn(file_sha(source), identities)
        self.assertTrue(seal['artifacts'])
        for artifact in seal['artifacts']:
            self.assertEqual(file_sha(artifact['path']), artifact['sha256'])
        return seal

    def test_all_eight_detectors_keep_all_thirty_including_missing_tv_and_no_profile(self):
        case = DEV_IDS[0]
        with tempfile.TemporaryDirectory() as directory:
            run, result, _ = self.execute(Path(directory), [hook(case, 'G-MTL', [])],
                                           missing_origins=(DEV_IDS[1],))
            self.assertEqual(set(result['summary']), set(DETECTORS))
            self.assertEqual(set(result['cases']), set(DETECTORS))
            for detector in DETECTORS:
                self.assertEqual(set(result['cases'][detector]), set(DEV_IDS))
                self.assertEqual(result['summary'][detector]['planned_cases'], 30)
                self.assertEqual(sum(result['summary'][detector]['statuses'].values()), 30)
                self.assertEqual(result['summary'][detector]['metrics'], dict.fromkeys(METRICS, 0.))
            self.assertEqual(FakeNumericWorker.calls, [])
            self.assertEqual(len(list((run / 'case-results').glob('*.json'))), 30)

    def test_shared_trigger_runs_once_preserves_detectors_and_seals_before_gt(self):
        case = DEV_IDS[0]
        items = [hook(case, 'G-MTL', [600, 650, 950]), hook(case, 'L-MTL', [650, 950])]
        with tempfile.TemporaryDirectory() as directory:
            run, result, checked = self.execute(Path(directory), items, check_evaluation=True)
            self.assertEqual([row['endpoint'] for row in FakeNumericWorker.calls], [600, 650, 950])
            self.assertTrue(checked)
            for endpoint in (600, 650, 950):
                self.assert_endpoint_sealed(run, case, endpoint)
            for detector in ('G-MTL', 'L-MTL'):
                composition = result['cases'][detector][case]['composition']
                self.assertEqual(composition['endpoint'], 650)
                self.assertEqual(composition['metrics']['rr'], 1.)
                self.assertAlmostEqual(result['summary'][detector]['metrics']['rr'], 1 / 30)
            self.assertEqual(set(result['resources_seconds']), set(DEV_IDS))
            self.assertTrue(all(float(value) >= 0 for value in result['resources_seconds'].values()))
            for request in FakeNumericWorker.calls:
                self.assertTrue(request['local']['include_logs'])
                self.assertEqual(request['local']['fusion'], 'availablemean')
                self.assertEqual(request['ranks'], [{'operator': 'ppr', 'direction': 'reverse', 'damping': .85}])
                self.assertEqual(request['ref'].shape, (2, 12, 30))
                self.assertEqual(request['query'].shape, (2, 12, 6))
                self.assertEqual(set(request), {'endpoint', 'ref', 'query', 'adj', 'types', 'local', 'ranks'})

    def test_first_post_failure_is_zero_and_later_success_cannot_rescue(self):
        case = DEV_IDS[0]
        for behavior in ('raise', 'numeric', 'short', 'nonfinite'):
            with self.subTest(behavior=behavior), tempfile.TemporaryDirectory() as directory:
                FakeNumericWorker.calls = []
                FakeNumericWorker.behaviors = {650: behavior}
                run, result, _ = self.execute(Path(directory), [hook(case, 'G-MTL', [650, 950])],
                                               check_evaluation=True)
                outcome = result['cases']['G-MTL'][case]
                self.assertEqual(outcome['composition']['endpoint'], 650)
                self.assertEqual(outcome['composition']['metrics']['rr'], 0.)
                self.assertNotEqual(outcome['all_trigger_diagnoses'][0]['status'], 'VALID')
                self.assertEqual(outcome['all_trigger_diagnoses'][1]['metrics']['rr'], 1.)
                seal = self.assert_endpoint_sealed(run, case, 650)
                self.assert_endpoint_sealed(run, case, 950)
                if behavior != 'raise':
                    raw_artifacts = [item for item in seal['artifacts'] if
                        'raw' in Path(item['path']).name.lower() or 'raw' in Path(item['path']).parent.name.lower()]
                    self.assertTrue(raw_artifacts, 'Raw response must survive output validation failure')
                    raw_response = decode_message(Path(raw_artifacts[0]['path']).read_bytes())
                    if behavior == 'numeric':
                        self.assertTrue(raw_response['evidence']['diagnostics']['numerical_channel_failures'][0, 8])
                    elif behavior == 'short':
                        self.assertEqual(len(raw_response['rankings'][0]['scores']), 1)
                    else:
                        self.assertTrue(np.isnan(raw_response['rankings'][0]['scores'][1]))

    def test_tau_and_case_path_change_evaluation_only_with_identical_numeric_requests(self):
        case = DEV_IDS[0]
        FakeNumericWorker.behaviors = {650: 'wrong'}
        snapshots, metrics = [], []
        for tau in (600, 700):
            with tempfile.TemporaryDirectory() as directory:
                FakeNumericWorker.calls = []
                _, result, _ = self.execute(Path(directory), [hook(case, 'G-MTL', [650, 950])], tau=tau)
                snapshots.append(deepcopy(FakeNumericWorker.calls))
                metrics.append(result['cases']['G-MTL'][case]['composition'])
        self.assertEqual([row['endpoint'] for row in metrics], [650, 950])
        self.assertEqual([row['metrics']['rr'] for row in metrics], [.5, 1.])
        self.assertEqual(len(snapshots[0]), 2)
        for before, after in zip(*snapshots):
            for key in ('ref', 'query', 'adj', 'types'):
                np.testing.assert_array_equal(before[key], after[key])
            self.assertEqual(before['local'], after['local'])
            self.assertEqual(before['ranks'], after['ranks'])

    def test_first_post_before_history_gate_stays_zero_after_later_valid_trigger(self):
        case = DEV_IDS[0]
        with tempfile.TemporaryDirectory() as directory:
            run, result, _ = self.execute(Path(directory), [hook(case, 'G-MTL', [300, 350, 650])],
                                           tau=300, check_evaluation=True)
            composed = result['cases']['G-MTL'][case]['composition']
            self.assertEqual(composed['endpoint'], 350)
            self.assertEqual(composed['status'], 'INSUFFICIENT_HISTORY')
            self.assertEqual(composed['metrics']['rr'], 0.)
            self.assertEqual([call['endpoint'] for call in FakeNumericWorker.calls], [650])
            for endpoint in (300, 350, 650):
                self.assert_endpoint_sealed(run, case, endpoint)

    def test_missing_origin_with_trigger_is_explicit_input_failure_and_planned_zero(self):
        case = DEV_IDS[0]
        with tempfile.TemporaryDirectory() as directory:
            run, result, _ = self.execute(Path(directory), [hook(case, 'G-MTL', [650])],
                                           missing_origins=(case,), check_evaluation=True)
            self.assertEqual(result['cases']['G-MTL'][case]['composition']['metrics']['rr'], 0.)
            self.assertNotEqual(result['cases']['G-MTL'][case]['all_trigger_diagnoses'][0]['status'], 'VALID')
            self.assertEqual(FakeNumericWorker.calls, [])
            self.assert_endpoint_sealed(run, case, 650)

    def test_untrusted_hook_profile_mode_detector_order_duplicates_rejected_before_prediction(self):
        case = DEV_IDS[0]
        original = hook(case, 'G-MTL', [650, 950])
        bad_fields = [{'threshold_mode': 'FULL_REFIT_DESCRIPTIVE'}, {'profile': 'TD12-C1-MT'},
                      {'detector': 'UNREGISTERED'}, {'handle': 'wrong'},
                      {'triggers': [950, 650]}, {'triggers': [650, 650]},
                      {'triggers': [650.5]}, {'triggers': [True]}, {'triggers': [-1]}]
        for fields in bad_fields:
            with self.subTest(fields=fields), tempfile.TemporaryDirectory() as directory:
                FakeNumericWorker.calls = []
                with self.assertRaises((ValueError, RuntimeError)):
                    self.execute(Path(directory), [{**original, **fields}])
                self.assertEqual(FakeNumericWorker.calls, [])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises((ValueError, RuntimeError)):
                self.execute(Path(directory), [original, deepcopy(original)])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: test_integrated_campaign.py NEW_COORDINATOR_RUN')
    RUN = Path(sys.argv[1]).resolve()
    contract = require_contract(RUN, 'development')
    pins = {str(Path(row['path']).resolve()): row['sha256'] for row in contract['source_files']}
    required = [Path(__file__).resolve()] + [W / 'scripts/task_e' / name for name in (
        'integrated_development.py', 'input_adapters.py', 'calibration.py', 'ranking.py',
        'evaluator.py', 'loader.py', 'execution.py', 'contract.py', 'c1_development.py', 'worker.py')]
    for source in required:
        if pins.get(str(source)) != file_sha(source):
            raise SystemExit('Fixture source absent or changed since coordinator contract: ' + str(source))
    report = RUN / 'integrated-controller-fixture-report.json'
    if report.exists():
        raise SystemExit('Never overwrite a fixture run')
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    save_json(report, {'tests_run': result.testsRun, 'passed': result.wasSuccessful(),
        'failures': [{'test': str(test), 'traceback': error} for test, error in result.failures],
        'errors': [{'test': str(test), 'traceback': error} for test, error in result.errors],
        'seconds': time.perf_counter() - started,
        'scope': 'Synthetic TD7.1 adapter and mocked controller only; no corpus or external process'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
