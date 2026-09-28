"""Bounded input-boundary/loader fixtures. No dataset rows or network are read.

This is not an OS sandbox or a complete runtime leakage certification. Real
worker orchestration, calibrated C5 and cache paths remain unimplemented/held.
"""
from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e import acquire, loader
from scripts.task_e.contract import DEV_IDS, require_dev


def synthetic_raw():
    times = np.arange(601)
    metrics = pd.DataFrame({'time': times, 'service-a_cpu': np.where(times < 300, 10., 11.)})
    rows = []
    for t in range(0, 600, 10):
        rows.append({'time': str(t), 'traceID': f't{t}', 'spanID': f'p{t}',
                     'serviceName': 'service-a', 'methodName': 'm', 'operationName': 'op',
                     'parentSpanID': '', 'startTimeMillis': t*1000, 'startTime': t*1000000,
                     'duration': 1000, 'statusCode': 0})
        rows.append({**rows[-1], 'spanID': f'c{t}', 'serviceName': 'service-b',
                     'parentSpanID': f'p{t}', 'startTimeMillis': t*1000+1,
                     'startTime': t*1000000+1000})
    return {'metrics': metrics, 'traces': pd.DataFrame(rows), 'logs': None,
            'audit': {'metadata': {'root': 'deliberate-controller-only-canary'}}}


class InputBoundaryChecks(unittest.TestCase):
    def test_exact_development_allowlist_and_no_answers(self):
        self.assertEqual(len(DEV_IDS), 30)
        self.assertEqual(set(DEV_IDS), set(acquire.DEV_IDS))
        self.assertEqual(set(DEV_IDS), set(loader.DEV_IDS))
        self.assertEqual(len(acquire.ALLOWED_PATHS), 89)
        self.assertTrue(all(p.endswith('.parquet') for p in acquire.ALLOWED_PATHS))
        for case in ('re2tt_ts-auth-service_mem_1', 're3tt_ts-route-service_f2_1'):
            with self.assertRaises(ValueError):
                require_dev(case)

    def test_nondev_path_rejected_before_parquet(self):
        record = {'case': 're2tt_ts-auth-service_cpu_1'}
        nondev = W/'datasets/rcaeval/raw-samples/re3tt_ts-route-service_f2_1/metrics.parquet'
        with patch.object(loader.pq, 'read_table', side_effect=AssertionError('Must not open')) as read:
            with self.assertRaises(loader.LoaderError):
                loader.load_case({'metrics': nondev}, record,
                                 expected_files={'metrics': {'bytes': 1, 'sha256': '0'*64}})
            read.assert_not_called()

    def test_answer_modality_is_rejected(self):
        with self.assertRaises(loader.LoaderError):
            loader.load_case({'root_cause': 'root_cause.txt'},
                             {'case': 're2tt_ts-auth-service_cpu_1'}, expected_files={})

    def test_download_requires_explicit_call(self):
        with self.assertRaises(acquire.AcquisitionError):
            acquire.acquire_development({}, allow_download=False)

    def test_hash_mismatch_rejected_before_parquet(self):
        path = W/'datasets/rcaeval/raw-samples/re2tt_ts-auth-service_cpu_1/metrics.parquet'
        with patch.object(Path, 'is_file', return_value=True), \
             patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=1)), \
             patch.object(loader, '_sha256', return_value='1'*64), \
             patch.object(loader.pq, 'read_table', side_effect=AssertionError('Must not open')) as read:
            with self.assertRaises(loader.LoaderError):
                loader.load_case({'metrics': path}, {'case': 're2tt_ts-auth-service_cpu_1'},
                                 expected_files={'metrics': {'bytes': 1, 'sha256': '0'*64}})
            read.assert_not_called()

    def test_C1_half_open_grid_graph_and_future_suffix(self):
        raw = synthetic_raw()
        first = loader.c1_bundle(raw, 300)
        self.assertEqual(first['ref'].shape, (2, 12, 30))
        self.assertEqual(first['adj'].tolist(), [[False, True], [False, False]])
        self.assertTrue(np.all(first['ref'][0,8] == 10))
        self.assertTrue(np.all(first['query'][0,8] == 11))
        future = raw['traces'].iloc[0].copy()
        future['serviceName'] = 'future-only-service'
        future['startTimeMillis'] = 900000
        future['spanID'] = 'future'
        later = {**raw, 'traces': pd.concat([raw['traces'], pd.DataFrame([future])], ignore_index=True),
                 'audit': {'metadata': {'root': 'changed-label', 'case': 'changed-path'}}}
        second = loader.c1_bundle(later, 300)
        self.assertEqual(first['service_names'], second['service_names'])
        for key in ('ref', 'query', 'adj'):
            np.testing.assert_array_equal(first[key], second[key])

    def test_C1_bad_log_support_does_not_change_MT(self):
        raw = synthetic_raw()
        first = loader.c1_bundle(raw, 300)
        raw['logs'] = pd.DataFrame({'timestamp': [np.nan],
                                    'container_name': ['service-a'], 'message': ['bad-clock']})
        second = loader.c1_bundle(raw, 300)
        np.testing.assert_array_equal(first['ref'][:,:11], second['ref'][:,:11])
        np.testing.assert_array_equal(first['query'][:,:11], second['query'][:,:11])
        self.assertTrue(np.isnan(second['ref'][:,11]).all())

    def test_C1_finite_fractional_clocks_outside_window_leave_inputs_unchanged(self):
        raw = synthetic_raw()
        raw['logs'] = pd.DataFrame({'timestamp': [10, 310],
                                    'container_name': ['service-a']*2,
                                    'message': ['reference', 'query']})
        first = loader.c1_bundle(raw, 300)
        for modality, clock, multiplier in (('metrics', 'time', 1),
                                            ('traces', 'startTimeMillis', 1000),
                                            ('logs', 'timestamp', 1)):
            for timestamp in (-.5, 600*multiplier+.5):
                with self.subTest(modality=modality, timestamp=timestamp):
                    row = raw[modality].iloc[0].to_dict()
                    row[clock] = timestamp
                    changed = {**raw, modality: pd.concat(
                        [raw[modality], pd.DataFrame([row])], ignore_index=True)}
                    second = loader.c1_bundle(changed, 300)
                    self.assertEqual(first['service_names'], second['service_names'])
                    for key in ('ref', 'query', 'adj', 'channel_types'):
                        np.testing.assert_array_equal(first[key], second[key])

    def test_C1_inside_window_fractional_required_clocks_fail(self):
        for modality, clock, multiplier in (('metrics', 'time', 1),
                                            ('traces', 'startTimeMillis', 1000)):
            for timestamp in (.5, 300*multiplier+.5):
                with self.subTest(modality=modality, timestamp=timestamp):
                    raw = synthetic_raw()
                    row = raw[modality].iloc[0].to_dict()
                    row[clock] = timestamp
                    raw[modality] = pd.concat([raw[modality], pd.DataFrame([row])],
                                             ignore_index=True)
                    with self.assertRaisesRegex(loader.LoaderError, 'integral timestamp'):
                        loader.c1_bundle(raw, 300)

    def test_C1_unplaceable_required_clocks_are_not_silently_dropped(self):
        for modality, clock in (('metrics', 'time'), ('traces', 'startTimeMillis')):
            for timestamp in (np.nan, np.inf, -np.inf, 'unknown'):
                with self.subTest(modality=modality, timestamp=timestamp):
                    raw = synthetic_raw()
                    row = raw[modality].iloc[0].to_dict()
                    row[clock] = timestamp
                    raw[modality] = pd.concat([raw[modality], pd.DataFrame([row])],
                                             ignore_index=True)
                    with self.assertRaises(loader.LoaderError):
                        loader.c1_bundle(raw, 300)

    def test_C1_invalid_log_clock_is_explicit_support_failure(self):
        for timestamp in (.5, np.nan, np.inf, 'unknown'):
            with self.subTest(timestamp=timestamp):
                raw = synthetic_raw()
                first = loader.c1_bundle(raw, 300)
                raw['logs'] = pd.DataFrame({'timestamp': [timestamp],
                                            'container_name': ['service-a'],
                                            'message': ['invalid-clock']})
                second = loader.c1_bundle(raw, 300)
                np.testing.assert_array_equal(first['ref'][:,:11], second['ref'][:,:11])
                np.testing.assert_array_equal(first['query'][:,:11], second['query'][:,:11])
                self.assertTrue(np.isnan(second['ref'][:,11]).all())
                self.assertTrue(np.isnan(second['query'][:,11]).all())
                self.assertIn('error', second['audit']['log_ref'])
                self.assertIn('error', second['audit']['log_query'])

    def test_C1_conflict_failure_and_log_duplicates_counted(self):
        raw = synthetic_raw()
        row = raw['traces'].iloc[0].copy()
        row['duration'] = 2000
        raw['traces'] = pd.concat([raw['traces'], pd.DataFrame([row])], ignore_index=True)
        with self.assertRaises(loader.LoaderError):
            loader.c1_bundle(raw, 300)
        raw = synthetic_raw()
        raw['logs'] = pd.DataFrame({'timestamp': [10, 10], 'container_name': ['service-a']*2,
                                    'message': ['same']*2})
        bundle = loader.c1_bundle(raw, 300)
        self.assertAlmostEqual(bundle['ref'][0,11,1], np.log1p(2))

    def test_C5_archive_bundle_explicitly_unqualified(self):
        bundle = loader.c5_bundle(synthetic_raw())
        self.assertEqual(bundle['values'].shape[0], 120)
        self.assertIn('UNQUALIFIED', str(bundle['audit']))


if __name__ == '__main__':
    output_dir = Path(sys.argv[1])
    if not (output_dir/'run-contract.json').is_file():
        raise SystemExit('Pre-run contract required')
    start = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'schema': 'TD12-E-BOUNDARY-FIXTURE-v1', 'tests_run': result.testsRun,
              'failures': [{'test': str(t), 'traceback': e} for t,e in result.failures],
              'errors': [{'test': str(t), 'traceback': e} for t,e in result.errors],
              'seconds': time.perf_counter()-start,
              'scope': 'SYNTHETIC DATAFRAMES + mocked file checks; no real telemetry rows',
              'qualification': 'PARTIAL INPUT BOUNDARY ONLY',
              'not_run': ['full runtime worker isolation', 'C5 streaming/prefix conflict invariance',
                          'cache provenance', 'full development loader audit', 'evaluator-after-seal runtime']}
    (output_dir/'leakage-audit.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
