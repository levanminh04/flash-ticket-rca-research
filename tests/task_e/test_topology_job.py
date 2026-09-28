"""Synthetic topology controller fixtures; coordinator contract required to run."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.contract import DEV_IDS, REVISION, TD_SHA256, opaque_handle
from scripts.task_e.execution import file_sha, require_contract, save_json, save_npz
from scripts.task_e.ranking import perturb_graphs
from scripts.task_e.topology_development import (CHAINS, load_inputs, proposal_plan, run_job,
                                                 verify_result, _verify_pinned)


class TopologyJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.handle = opaque_handle(DEV_IDS[0])
        cls.adj = np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], dtype=bool)
        cls.result = perturb_graphs(cls.adj, cls.handle, 'directed', count=CHAINS, budget=100)

    def test_fixed_plan_counts_both_projections_and_all_budgets(self):
        # Two reciprocal observed edges + one directed edge: 3 directed, 2 undirected.
        adj = np.array([[0, 1, 0], [1, 0, 1], [0, 0, 0]], dtype=bool)
        jobs = proposal_plan(adj)
        self.assertEqual(len(jobs), 6)
        self.assertEqual([j['edges'] for j in jobs], [3, 3, 3, 2, 2, 2])
        self.assertEqual([j['total_proposals'] for j in jobs],
                         [256*300, 256*600, 256*1200, 256*200, 256*400, 256*800])
        empty = proposal_plan(np.zeros((0, 0), dtype=bool))
        self.assertEqual(sum(j['total_proposals'] for j in empty), 256 * 2 * 700)

    def test_degenerate_graph_preserves_every_draw_and_isolate(self):
        report = verify_result(self.adj, self.handle, 'directed', 100, self.result)
        self.assertEqual(report['total_proposals'], 25600)
        self.assertEqual(report['distinct_final_graphs'], 1)
        self.assertEqual(report['median_retained_edge_fraction'], 1.)
        self.assertEqual(report['isolates'], 1)
        self.assertEqual(report['isolate_indices'], [2])
        self.assertFalse(report['mobile'])
        self.assertTrue(report['degenerate'])
        self.assertTrue(all(r['accepted'] == 0 and r['rejections']['insufficient_edges'] == 100
                            for r in self.result['per_draw']))

    def test_changed_seed_graph_or_accounting_rejected(self):
        for field, value in [('seed', 0), ('hash', 'fake'), ('proposals', 99), ('accepted', 1)]:
            bad = copy.deepcopy(self.result)
            bad['per_draw'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_result(self.adj, self.handle, 'directed', 100, bad)
        bad = copy.deepcopy(self.result)
        bad['graphs'][0, 0, 1] = False
        with self.assertRaises(ValueError):
            verify_result(self.adj, self.handle, 'directed', 100, bad)

    def _run(self, directory):
        run = Path(directory)
        save_json(run/'run-contract.json', {'stage': 'synthetic topology qualification'})
        return run

    def _record(self):
        return {'handle': self.handle, 'adj': self.adj, 'source': {'synthetic': True},
                'input_failure': None}

    def test_exclusive_checkpoint_reuses_without_numeric_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory)
            with patch('scripts.task_e.topology_development.perturb_graphs', return_value=self.result) as method:
                first = run_job(run, self._record(), 'directed', 100)
                self.assertEqual(method.call_count, 1)
                self.assertEqual(method.call_args.args[1:], (self.handle, 'directed'))
                self.assertEqual(method.call_args.kwargs, {'count': 256, 'budget': 100})
            receipt = run/'topology'/self.handle/'directed'/'100'/'receipt.json'
            old = file_sha(receipt)
            with patch('scripts.task_e.topology_development.perturb_graphs', side_effect=AssertionError('No rerun')):
                second = run_job(run, self._record(), 'directed', 100)
            self.assertTrue(second['reused_verified_checkpoint'])
            self.assertEqual(first['graphs_sha256'], second['graphs_sha256'])
            self.assertEqual(file_sha(receipt), old)

    def test_partial_checkpoint_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory)
            target = run/'topology'/self.handle/'directed'/'100'
            target.mkdir(parents=True)
            save_json(target/'start.json', {'interrupted': True})
            old = file_sha(target/'start.json')
            with self.assertRaises((FileExistsError, FileNotFoundError)):
                run_job(run, self._record(), 'directed', 100)
            self.assertEqual(file_sha(target/'start.json'), old)

    def test_failure_receipt_keeps_all_256_planned_and_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory)
            with patch('scripts.task_e.topology_development.perturb_graphs', side_effect=RuntimeError('fixture')):
                failed = run_job(run, self._record(), 'directed', 100)
            self.assertEqual((failed['status'], failed['planned_draws'], failed['completed_draws']),
                             ('FAILURE', 256, 0))
            with self.assertRaises(FileExistsError):
                run_job(run, self._record(), 'directed', 100)

    def test_input_failure_never_calls_numeric_method(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory)
            record = {**self._record(), 'adj': None, 'input_failure': 'C1_PRIMARY_NOT_MATERIALIZED'}
            with patch('scripts.task_e.topology_development.perturb_graphs', side_effect=AssertionError('No graph')):
                result = run_job(run, record, 'directed', 100)
            self.assertEqual(result['status'], 'INPUT_FAILURE')
            self.assertEqual(result['completed_draws'], 0)

    def test_run_contract_and_frozen_file_identity_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'input.json'
            save_json(path, {'version': 1})
            pins = {str(path.resolve()): file_sha(path)}
            self.assertEqual(_verify_pinned(path, pins), pins[str(path.resolve())])
            with self.assertRaises(ValueError):
                _verify_pinned(path, {})
            path.write_text('changed', encoding='utf-8')
            with self.assertRaises(ValueError):
                _verify_pinned(path, pins)
            with self.assertRaises(FileNotFoundError):
                run_job(Path(directory), self._record(), 'directed', 100)

    def test_unissued_handle_or_unregistered_budget_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self._run(directory)
            with self.assertRaises(ValueError):
                run_job(run, {**self._record(), 'handle': 'unissued'}, 'directed', 100)
            with self.assertRaises(ValueError):
                run_job(run, self._record(), 'directed', 201)

    def _audit_inputs(self, directory, *, omit_numeric_pin=False, wrong_handle=False):
        # The fixture intentionally supplies no labels, names, telemetry values
        # or metadata. Only one graph is materialized; all30 remain planned.
        audit, run = Path(directory)/'audit', Path(directory)/'run'
        paths = [audit/'run-contract.json', audit/'loader-summary.json']
        save_json(paths[0], {'stage': 'development audit', 'td': {'sha256': TD_SHA256}})
        save_json(paths[1], {'planned': 30})
        for case in DEV_IDS:
            handle = opaque_handle(case)
            profile, files = {'status': 'INPUT_FAILURE'}, []
            if handle == self.handle:
                numeric = audit/'intermediates'/handle/'c1_primary.npz'
                save_npz(numeric, adj=self.adj)
                if not omit_numeric_pin:
                    paths.append(numeric)
                files = [{'path': str(numeric), 'sha256': file_sha(numeric)}]
                profile = {'status': 'MATERIALIZED', 'audit': {'graph': {
                    'adjacency_sha256': hashlib.sha256(self.adj.tobytes()).hexdigest()}}}
            receipt = audit/'case-audits'/(handle+'.json')
            save_json(receipt, {'handle': 'other' if wrong_handle and handle == self.handle else handle,
                               'profiles': {'c1_primary': profile}, 'numeric_files': files})
            paths.append(receipt)
        save_json(run/'run-contract.json', {'stage': 'development topology',
            'td': {'sha256': TD_SHA256}, 'dataset_revision': REVISION,
            'inputs': [{'path': str(p), 'sha256': file_sha(p)} for p in paths]})
        return run, audit

    def test_exact30_label_free_cache_admission_and_missing_input_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            run, audit = self._audit_inputs(directory)
            records = load_inputs(run, audit)
            self.assertEqual(len(records), 30)
            valid = [r for r in records if r['input_failure'] is None]
            self.assertEqual(len(valid), 1)
            np.testing.assert_array_equal(valid[0]['adj'], self.adj)
            self.assertEqual(sum(r['adj'] is None for r in records), 29)
            self.assertEqual(set(valid[0]), {'handle', 'source', 'adj', 'input_failure'})

    def test_cache_requires_its_own_pin_and_exact_receipt_handle(self):
        for options in ({'omit_numeric_pin': True}, {'wrong_handle': True}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                run, audit = self._audit_inputs(directory, **options)
                with self.assertRaises(ValueError):
                    load_inputs(run, audit)


if __name__ == '__main__':
    output = Path(sys.argv[1])
    require_contract(output, 'topology')
    started = time.perf_counter()
    outcome = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    save_json(output/'topology-fixture-report.json', {
        'schema': 'TD13-TOPOLOGY-CONTROLLER-FIXTURES-v1', 'tests_run': outcome.testsRun,
        'failures': [{'test': str(t), 'traceback': e} for t, e in outcome.failures],
        'errors': [{'test': str(t), 'traceback': e} for t, e in outcome.errors],
        'seconds': time.perf_counter()-started, 'no_raw_telemetry_or_outcomes': True})
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
