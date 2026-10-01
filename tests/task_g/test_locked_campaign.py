"""Purposeful synthetic numeric/transport tests, not final qualification."""
import copy
import io
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import numpy as np
from scripts.task_g import locked_campaign as c
from scripts.task_g import locked_provenance as p


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.directory = p.ROOT / 'cache' / ('unit-worker-' + secrets.token_hex(8))
        self.store = p.ShardStore(self.directory / 'shards')
        self.contract = {'resource_policy': {'numeric_worker_private_bytes_limit': 512 * 1024 * 1024}}

    def wire(self, bins=8):
        generator = np.random.default_rng(1042)
        warmup = generator.normal(size=(36, 2, 3))
        stream = generator.normal(size=(bins, 2, 3))
        warmup[:, :, 1:] = np.log1p(np.abs(warmup[:, :, 1:]) * 10)
        stream[:, :, 1:] = np.log1p(np.abs(stream[:, :, 1:]) * 10)
        return {key: c.numeric._pack(value) for key, value in {
            'warmup': warmup, 'stream': stream, 'adj': np.array([[0, 1], [0, 0]], bool),
            'channel_types': np.array([0, 1, 2]), 'fit_mask': np.ones(2, bool),
            'endpoints': np.arange(37, 37 + bins) * 5}.items()}

    def run_c5(self, wire):
        records = []
        with patch.object(c, '_worker_guard'), patch.object(c, '_emit', side_effect=records.append):
            c._c5_worker(wire)
        return records

    def test_all_eight_detectors_emit_state_each_bin_and_costs(self):
        records = self.run_c5(self.wire())
        for name in c.DETECTORS:
            chosen = [row for row in records if row['detector'] == name]
            self.assertEqual([row['kind'] for row in chosen], ['c5_state'] + ['c5_bin'] * 8 + ['c5_done'])
            self.assertEqual([row['index'] for row in chosen[1:-1]], list(range(8)))
            self.assertEqual(chosen[-1]['status'], 'SUCCESS')
            self.assertGreaterEqual(chosen[-1]['fit_seconds'], 0)
            self.assertGreaterEqual(chosen[-1]['prediction_seconds'], 0)

    def test_prefix_future_invariance_with_same_warmup_and_prefix(self):
        full = self.wire(12); short = copy.deepcopy(full)
        short['stream'] = c.numeric._pack(c.numeric._unpack(full['stream'])[:4])
        short['endpoints'] = c.numeric._pack(c.numeric._unpack(full['endpoints'])[:4])
        left, right = self.run_c5(short), self.run_c5(full)
        for name in c.DETECTORS:
            lrows = [row for row in left if row['detector'] == name and row['kind'] == 'c5_bin']
            rrows = [row for row in right if row['detector'] == name and row['kind'] == 'c5_bin'][:4]
            self.assertEqual(len(lrows), 4)
            self.assertEqual(len(rrows), 4)
            self.assertEqual(lrows, rrows)

    def test_c5_rejects_tau_ids_paths_answers_or_owner_fields(self):
        for key in ('tau', 'case_id', 'path', 'root', 'fault', 'answer', 'candidate_ids'):
            with self.subTest(key=key), patch.object(c, '_worker_guard'), self.assertRaises(p.Error):
                c._c5_worker({**self.wire(), key: 'CANARY_SYNTHETIC_ONLY'})

    def test_c5_rejects_stale_endpoint_grid(self):
        wire = self.wire(); wire['endpoints'] = c.numeric._pack(np.arange(37, 45) * 5 + 1)
        with patch.object(c, '_worker_guard'), self.assertRaises(p.Error): c._c5_worker(wire)

    def test_timeout_before_spawn_has_no_model_or_fabricated_zero_time(self):
        with patch.object(p, 'registered_context', return_value=({}, self.contract)), patch.object(c.subprocess, 'Popen') as spawn:
            result = c.stream_worker('c1', {'synthetic_only': True}, time.perf_counter() - 1,
                                     self.store, self.directory / 'attempt')
        spawn.assert_not_called(); self.assertTrue(result['timed_out'])
        self.assertEqual(result['rows'], []); self.assertIsNone(result['peak_worker_private_bytes'])
        self.assertGreater(result['wall_seconds'], 0)

    def test_actual_compute_is_gated_before_source_access(self):
        with (patch.object(p, 'require_final_authorization', side_effect=p.Error('CLOSED')),
              patch.object(c.source_api, 'get_case') as getter):
            with self.assertRaises(p.Error): c.compute_case(None, 0, 0., {}, self.store, self.directory, 'ACTUAL_FINAL60')
        getter.assert_not_called()

    def test_final_entry_is_real_route_with_early_permission_gate(self):
        with (patch.object(p, 'require_final_authorization', side_effect=p.Error('CLOSED')),
              patch.object(c.subprocess, 'Popen') as worker):
            with self.assertRaises(p.Error): c.run_final_campaign()
        worker.assert_not_called()

    def test_wrong_scope_or_caller_contract_cannot_reach_source(self):
        with (patch.object(p, 'registered_context', return_value=({}, {'registered': True})),
              patch.object(c.source_api, 'get_case') as getter):
            with self.assertRaises(p.Error): c.compute_case(None, 0, 0., {'registered': False}, self.store, self.directory, 'SYNTHETIC_G33_PREPARATION')
        getter.assert_not_called()

    def test_stream_partial_and_malformed_frames_keep_prefix_and_fail(self):
        class Monitor:
            def __init__(self, pid): self.pid = pid
            def sample(self, force=False): return {'peak_private_bytes': 100, 'observed_process_count': 2}
            def terminate(self): pass
            def close(self): pass
        class Process:
            def __init__(self, raw):
                self.stdin, self.stdout = io.BytesIO(), io.BytesIO(raw)
                self.pid, self.returncode = 1, 0
            def kill(self): self.returncode = -1
            def wait(self, timeout=None): return self.returncode
        first = p._canonical({'kind': 'header', 'synthetic_only_unqualified': True}) + b'\n'
        for suffix in (b'{"broken":', b'{ "kind":"done"}\n', b'x' * (p.MAX_FRAME + 2)):
            with (self.subTest(length=len(suffix)), patch.object(p, 'registered_context', return_value=({}, self.contract)),
                  patch.object(c.subprocess, 'Popen', return_value=Process(first + suffix)),
                  patch.object(c, 'WorkerTree', Monitor),
                  patch.object(c, 'resident_bytes', return_value=None)):
                result = c.stream_worker('c1', {}, time.perf_counter() + 10, self.store,
                                         self.directory / ('frame-' + secrets.token_hex(4)))
                self.assertEqual(len(result['rows']), 1)
                self.assertIsNotNone(result['failure_reason'])
                self.assertEqual(self.store.get(result['rows'][0]['reference'])['kind'], 'header')

    @unittest.skipUnless(os.name == 'nt', 'Windows qualified runtimes')
    def test_both_venv_numeric_children_are_measured_and_terminated(self):
        # Synthetic resource identity/timeout probe; no RCA model or oracle.
        for relative in ('.venv/Scripts/python.exe', 'environments/task-e/rcd39/Scripts/python.exe'):
            child = subprocess.Popen([str(c.W / relative), '-B', '-c',
                'import os,time; a=bytearray(24*1024**2); print(os.getpid(),flush=True); time.sleep(20)'],
                stdout=subprocess.PIPE, text=True)
            monitor = c.WorkerTree(child.pid)
            try:
                numeric_pid = int(child.stdout.readline())
                memory = monitor.sample(force=True)
                self.assertNotEqual(child.pid, numeric_pid)
                self.assertIn(numeric_pid, memory['observed_process_ids'])
                self.assertGreater(memory['peak_private_bytes'], 24 * 1024**2)
                self.assertEqual(memory['observed_process_count'], 2)
                with patch.object(c, '_memory_from_handle', return_value=None), self.assertRaises(p.Error):
                    monitor.sample(force=True)
                monitor.terminate()
                self.assertTrue(all(not monitor._active(handle) for handle in monitor.handles.values()))
                child.wait(timeout=5)
            finally:
                monitor.terminate(); monitor.close(); child.stdout.close()

    def test_worker_guard_uses_child_aggregate_and_keeps_numeric_prefix(self):
        class Process:
            def __init__(self):
                self.stdin = io.BytesIO()
                self.stdout = io.BytesIO(p._canonical({'kind':'header','synthetic_only':True}) + b'\n')
                self.pid, self.returncode = 1, 0
            def kill(self): self.returncode = -1
            def wait(self, timeout=None): return self.returncode
        class Monitor:
            def __init__(self, pid): self.calls = 0; self.terminated = self.closed = False
            def sample(self, force=False):
                self.calls += 1
                return {'peak_private_bytes': 100 if self.calls == 1 else 600 * 1024**2,
                        'observed_process_count': 2}
            def terminate(self): self.terminated = True
            def close(self): self.closed = True
        monitor = Monitor(1)
        with (patch.object(p, 'registered_context', return_value=({}, self.contract)),
              patch.object(c.subprocess, 'Popen', return_value=Process()),
              patch.object(c, 'WorkerTree', return_value=monitor),
              patch.object(c, 'resident_bytes', return_value=None)):
            result = c.stream_worker('c1', {}, time.perf_counter()+10, self.store, self.directory/'memory')
        self.assertEqual(result['failure_reason'], 'WORKER_MEMORY_BUDGET_EXCEEDED')
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['observed_worker_process_count'], 2)
        self.assertTrue(monitor.terminated and monitor.closed)

    def test_monitor_initialization_failure_closes_wire_before_waiting(self):
        class Process:
            def __init__(self): self.stdin, self.stdout, self.pid = io.BytesIO(), io.BytesIO(), 1
            def wait(self, timeout=None):
                if not self.stdin.closed: raise AssertionError('WIRE_NOT_CLOSED_BEFORE_CLEANUP')
                return 0
            def kill(self): raise AssertionError('DO_NOT_KILL_WAITING_REDIRECTOR_FIRST')
        process = Process()
        with (patch.object(p, 'registered_context', return_value=({}, self.contract)),
              patch.object(c.subprocess, 'Popen', return_value=process),
              patch.object(c, 'WorkerTree', side_effect=p.Error('COUNTER_UNAVAILABLE'))):
            with self.assertRaisesRegex(p.Error, 'INITIALIZATION_FAILED_NO_WIRE_SENT'):
                c.stream_worker('c1', {}, time.perf_counter()+10, self.store, self.directory/'initialization')
        self.assertTrue(process.stdin.closed and process.stdout.closed)

    def test_missing_controller_conversion_counter_blocks_numeric_worker(self):
        with (patch.object(p, 'registered_context', return_value=({}, self.contract)),
              patch.object(c.source_api, 'get_case', return_value={'synthetic_only_unqualified':True}),
              patch.object(c, 'resident_bytes', return_value=None),
              patch.object(c, 'stream_worker') as numeric_worker):
            contract = {**self.contract, 'resource_policy': {**self.contract['resource_policy'],
                        'development_timing_deadline_seconds':900.}}
            with patch.object(p, 'registered_context', return_value=({}, contract)):
                with self.assertRaisesRegex(p.Error, 'COUNTER_UNAVAILABLE_AFTER_CONVERSION'):
                    c.compute_case(None, 0, 0., contract, self.store, self.directory, 'DEVELOPMENT_TIMING_ONLY', c1_only=True)
        numeric_worker.assert_not_called()

    def test_signed_final_or_synthetic_cannot_skip_auxiliary_completeness(self):
        for scope, flag in (('ACTUAL_FINAL60',True), ('SYNTHETIC_G33_PREPARATION',True),
                            ('ACTUAL_FINAL60','false'), ('ACTUAL_FINAL60',None),
                            ('DEVELOPMENT_TIMING_ONLY',False)):
            with self.subTest(scope=scope,flag=flag), self.assertRaisesRegex(p.Error, 'FLAG_OR_SCOPE_DRIFT'):
                c.validate_case_inventory({'scope':scope,'C1_only_development_timing':flag}, self.store,{})
        with self.assertRaisesRegex(p.Error, 'EXTRA_DENOMINATORS'):
            c.validate_case_inventory({'scope':'DEVELOPMENT_TIMING_ONLY','C1_only_development_timing':True,
                'planned_RCD_seeds':[420,421,422],'planned_C5_detectors':[]}, self.store,{})

    def test_missing_controller_stream_counter_retains_prefix_and_terminates(self):
        class Process:
            def __init__(self):
                self.stdin=io.BytesIO();self.stdout=io.BytesIO(p._canonical({'kind':'header','synthetic_only':True})+b'\n')
                self.pid,self.returncode=1,0
            def kill(self):self.returncode=-1
            def wait(self,timeout=None):return self.returncode
        class Monitor:
            def __init__(self):self.terminated=False
            def sample(self,force=False):return {'peak_private_bytes':100,'observed_process_count':2}
            def terminate(self):self.terminated=True
            def close(self):pass
        monitor=Monitor();contract={'resource_policy':{**self.contract['resource_policy'],'controller_private_bytes_limit':3*1024**3}}
        with (patch.object(p,'registered_context',return_value=({},contract)),
              patch.object(c.subprocess,'Popen',return_value=Process()),
              patch.object(c,'WorkerTree',return_value=monitor),
              patch.object(c,'resident_bytes',side_effect=[{'private_bytes':100},None])):
            result=c.stream_worker('c1',{},time.perf_counter()+10,self.store,self.directory/'missing-controller')
        self.assertEqual(result['failure_reason'],'CONTROLLER_MEMORY_COUNTER_UNAVAILABLE')
        self.assertEqual(len(result['rows']),1);self.assertTrue(monitor.terminated)

    def test_postprocessing_timeout_preserves_numeric_evidence_but_fails_planned_outcome(self):
        arms = {'L': {'status': 'SUCCESS', 'scores': [1.]}, 'O': {'status': 'SUCCESS', 'scores': [1.]},
                'R': [{'draw': index, 'status': 'SUCCESS', 'scores': [1.]} for index in range(256)]}
        row = {'c1': {name: copy.deepcopy(arms) for name in ('primary', 'secondary')},
               'costs': {'matched_aggregate_case_wall_seconds': 10.1, 'timing_completed': True, 'timed_out': False}}
        before = self.store.put(copy.deepcopy(row['c1']))
        c._enforce_primary_postprocessing_budget(row, {'timed_out': False}, 10.)
        self.assertTrue(row['primary_postprocessing_budget_failure'])
        self.assertFalse(row['costs']['timing_completed'])
        self.assertEqual(len(row['c1']['primary']['R']), 256)
        self.assertTrue(all(item['status'] == 'TIMEOUT' and item['scores'] is None
                            for group in row['c1'].values() for item in (group['L'], group['O'], *group['R'])))
        self.assertEqual(self.store.get(before)['primary']['O']['status'], 'SUCCESS')

    def test_controller_conversion_provenance_is_complete_and_scope_bound(self):
        # Pure synthetic controller packet seam; no model, issuer or seal.
        metadata = {'scope': c.source_api.SYNTHETIC_SCOPE, 'conversion_only': True,
                    'conversion_costs': {'c1_conversion_seconds': 1.2}, 'source_hashes': {},
                    'conversion_failures': {}, 'numeric_inventory': {}, 'c1_quality': {},
                    'c5_quality': {}, 'rcd_quality': {}, 'clock_windows': {
                        'modalities': dict.fromkeys(('metrics','traces','logs'), {'declared_unit':'SYNTHETIC'}),
                        'source_of_window': 'VERIFIED_INJECT_TIME_PROJECTION_NOT_ORIGIN_OFFSET',
                        'c5_receives_timing_marker': False}}
        bindings = {'source_hashes': {}, 'conversion_provenance': metadata}
        c._validate_conversion_provenance(bindings, 'SYNTHETIC_G33_PREPARATION')
        ref = self.store.put(bindings)
        self.assertEqual(self.store.get(ref), bindings)
        for missing in ('clock_windows','numeric_inventory','rcd_quality','conversion_costs'):
            altered = {key:value for key,value in metadata.items() if key != missing}
            with self.subTest(missing=missing), self.assertRaises(p.Error):
                c._validate_conversion_provenance({**bindings,'conversion_provenance':altered}, 'SYNTHETIC_G33_PREPARATION')
        with self.assertRaises(p.Error): c._validate_conversion_provenance(bindings,'ACTUAL_FINAL60')
        with self.assertRaises(p.Error):
            c._validate_conversion_provenance({**bindings,'source_hashes':{'synthetic':'drift'}}, 'SYNTHETIC_G33_PREPARATION')
        development = {'conversion_provenance': {'scope':c.source_api.DEVELOPMENT_SCOPE,
            'conversion_only':True,'conversion_costs':{},'numeric_cache_verified':True}}
        c._validate_conversion_provenance(development,'DEVELOPMENT_TIMING_ONLY')

    def test_development_anonymous_ids_are_exact_and_do_not_enter_final_mapping(self):
        c._check_candidate_keys(['v0','v1'], 2, development=True)
        for keys, development in ((['v1','v0'], True), (['v0'], True), (['v0','v1'], False)):
            with self.subTest(keys=keys, development=development), self.assertRaises(p.Error):
                c._check_candidate_keys(keys, 2, development=development)

    def test_issued_binding_missing_extra_or_mismatch_stops_before_science(self):
        # Synthetic-only verifier seam; cannot issue/qualify a production run.
        metadata={'scope':c.source_api.SYNTHETIC_SCOPE,'conversion_only':True,'conversion_costs':{},
            'source_hashes':{},'conversion_failures':{},'numeric_inventory':{},'c1_quality':{},
            'c5_quality':{},'rcd_quality':{},'clock_windows':{
                'modalities':dict.fromkeys(('metrics','traces','logs'),{}),
                'source_of_window':'VERIFIED_INJECT_TIME_PROJECTION_NOT_ORIGIN_OFFSET',
                'c5_receives_timing_marker':False}}
        bindings={'quality':{'synthetic_only_unqualified':True},'candidate_ids':[],
            'source_hashes':{},'conversion_provenance':metadata,
            'integrated_candidate_ids':dict.fromkeys(c.DETECTORS,{})}
        expected={key:value for key,value in bindings.items() if key!='integrated_candidate_ids'}
        inventory={'scope':'SYNTHETIC_G33_PREPARATION','C1_only_development_timing':False,
            'schema':'TD13-G33-CASE-INVENTORY-v1','ordinal':0,'scientific_roles':{
                'case/compact':'row','case/controller-bindings':'bindings','C1/issued-bindings':'issued'}}
        for issued in ({}, {key:value for key,value in expected.items() if key!='conversion_provenance'},
                       {**expected,'extra_synthetic_field':True}, {**expected,'source_hashes':{'x':'drift'}}):
            with (self.subTest(keys=sorted(issued)),
                  patch.object(self.store,'get',side_effect=lambda ref: {
                      'row':{'ordinal':0,'candidate_count':0},'bindings':bindings,'issued':issued}[ref]),
                  self.assertRaisesRegex(p.Error,'BINDING_DRIFT_OR_INCOMPLETE')):
                c.validate_case_inventory(inventory,self.store,{})


if __name__ == '__main__': unittest.main()
