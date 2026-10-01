"""G33 streaming execution: identical frozen math, bounded durable records.

The final entry uses this same route after explicit final authorization. During
preparation only locked development timing and distinct synthetic sources run.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import weakref

W = Path(__file__).resolve().parents[2]
for folder in (W, W / 'src'):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
if __name__ == '__main__':
    sys.modules['scripts.task_g.locked_campaign'] = sys.modules[__name__]
from scripts.task_g import final_campaign as numeric
from scripts.task_g import final_source as source_api
from scripts.task_g import locked_provenance as provenance

Error = provenance.Error
DETECTORS = numeric.DETECTORS


def _memory_from_handle(handle):
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
            'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    counters = Counters(); counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        return None
    return {'working_set_bytes': counters.WorkingSetSize, 'private_bytes': counters.PrivateUsage,
            'peak_working_set_bytes': counters.PeakWorkingSetSize, 'peak_private_bytes': counters.PeakPagefileUsage}


def resident_bytes(pid):
    """Actual Windows working-set/private counters; unavailable stays missing."""
    if os.name != 'nt':
        return None
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return None
    try:
        return _memory_from_handle(handle)
    finally:
        kernel.CloseHandle(handle)


def _windows_process_parents():
    """Toolhelp lineage only; names and command lines never enter numeric data."""
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise Error('WORKER_PROCESS_LINEAGE_UNAVAILABLE')
    try:
        entry = Entry(); entry.dwSize = ctypes.sizeof(entry)
        if not kernel.Process32FirstW(snapshot, ctypes.byref(entry)):
            raise Error('WORKER_PROCESS_LINEAGE_UNAVAILABLE')
        parents = {}
        while True:
            parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
            if not kernel.Process32NextW(snapshot, ctypes.byref(entry)):
                if ctypes.get_last_error() != 18:  # ERROR_NO_MORE_FILES
                    raise Error('WORKER_PROCESS_LINEAGE_INCOMPLETE')
                break
        return parents
    finally:
        kernel.CloseHandle(snapshot)


class WorkerTree:
    """Track the venv redirector and numeric descendants, with stable handles.

    Sum per-process observed OS peaks conservatively. Sampling is an operational
    budget, not an OS allocation cap. A missing active counter fails closed.
    """
    def __init__(self, pid):
        if os.name != 'nt':
            raise Error('WINDOWS_WORKER_TREE_REQUIRED')
        from ctypes import wintypes
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.root = pid; self.handles = {}; self.created = {}; self.peaks = {}; self.cached = None; self.last = -math.inf
        self._add(pid)

    def _creation(self, handle):
        from ctypes import wintypes
        times = [wintypes.FILETIME() for _ in range(4)]
        if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise Error('WORKER_PROCESS_CREATION_TIME_UNAVAILABLE')
        return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime

    def _add(self, pid, parent=None):
        handle = self.kernel.OpenProcess(0x00100000 | 0x0400 | 0x0010 | 0x0001, False, pid)
        if not handle:
            raise Error('WORKER_PROCESS_HANDLE_UNAVAILABLE')
        try:
            created = self._creation(handle)
            if parent is not None and (created < self.created[parent]
                    or not self._active(self.handles[parent])
                    or _windows_process_parents().get(pid) != parent):
                raise Error('WORKER_PROCESS_IDENTITY_OR_LINEAGE_CHANGED')
        except Exception:
            self.kernel.CloseHandle(handle)
            raise
        self.handles[pid] = handle
        self.created[pid] = created

    def _active(self, handle):
        from ctypes import wintypes
        code = wintypes.DWORD()
        if not self.kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise Error('WORKER_PROCESS_STATE_UNAVAILABLE')
        return code.value == 259

    def _refresh(self):
        parents = _windows_process_parents()
        # Only live, handle-anchored parents can add children: no stale-PID reuse.
        active = {pid for pid, handle in self.handles.items() if self._active(handle)}
        while True:
            children = {pid for pid, parent in parents.items() if parent in active and pid not in self.handles}
            if not children:
                break
            for pid in children:
                self._add(pid, parents[pid])
                if self._active(self.handles[pid]):
                    active.add(pid)

    def sample(self, force=False):
        if not force and self.cached is not None and time.perf_counter() - self.last < .05:
            return self.cached
        self._refresh()
        current = 0
        for pid, handle in self.handles.items():
            if not self._active(handle):
                continue
            memory = _memory_from_handle(handle)
            if memory is None:
                raise Error('WORKER_MEMORY_MEASUREMENT_UNAVAILABLE')
            current += memory['private_bytes']
            self.peaks[pid] = max(self.peaks.get(pid, 0), memory['peak_private_bytes'])
        if not self.peaks:
            raise Error('WORKER_MEMORY_MEASUREMENT_UNAVAILABLE')
        self.cached = {'private_bytes': current, 'peak_private_bytes': sum(self.peaks.values()),
                       'observed_process_count': len(self.peaks), 'observed_process_ids': sorted(self.peaks)}
        self.last = time.perf_counter()
        return self.cached

    def terminate(self):
        # Discover current descendants before ending the redirector. Kill children
        # first, so timeout cannot leave an orphan computing after its driver dies.
        failures = []
        try:
            self._refresh()
        except Exception as exc:
            failures.append(str(exc))
        for pid, handle in reversed(list(self.handles.items())):
            try:
                if self._active(handle) and not self.kernel.TerminateProcess(handle, 1):
                    failures.append('WORKER_DESCENDANT_TERMINATION_FAILED')
                if self.kernel.WaitForSingleObject(handle, 5000) != 0:
                    failures.append('WORKER_DESCENDANT_WAIT_FAILED')
            except Exception as exc:
                failures.append(str(exc))
        if failures:
            raise Error('|'.join(failures))

    def close(self):
        for handle in self.handles.values():
            self.kernel.CloseHandle(handle)
        self.handles.clear()


def _worker_guard():
    provenance.registered_context()
    if any(os.environ.get(key) != value for key, value in numeric.THREADS.items()):
        raise Error('NUMERIC_THREADS_CHANGED')


def _emit(value):
    raw = provenance._canonical(value)
    if len(raw) > provenance.MAX_FRAME:
        raise Error('WORKER_FRAME_LIMIT_NO_TRUNCATION')
    sys.stdout.buffer.write(raw + b'\n'); sys.stdout.buffer.flush()


def _c5_worker(wire):
    """Frozen fit/score/event calls; each bin is emitted, never collected."""
    import numpy as np
    from rca.detection import fit_detector, score_bin, create_event_state, event_step
    _worker_guard()
    if set(wire) != {'warmup', 'stream', 'adj', 'channel_types', 'fit_mask', 'endpoints'}:
        raise Error('C5_NUMERIC_ONLY_WIRE_REQUIRED')
    warmup, stream, adj, types, fitmask, endpoints = (numeric._unpack(wire[key]) for key in
        ('warmup', 'stream', 'adj', 'channel_types', 'fit_mask', 'endpoints'))
    config = numeric._frozen_config()
    profile = config.manifest['selections']['c5']['profile']
    if not np.array_equal(endpoints, np.arange(len(warmup) + 1, len(warmup) + len(stream) + 1) * profile['bin_seconds']):
        raise Error('C5_ENDPOINT_GRID_DRIFT')
    for detector in DETECTORS:
        started = time.perf_counter(); fit_seconds = prediction_seconds = None
        completed = 0; state = None
        selected = config.detector(detector)
        cfg = {'arm': 'G' if selected.arm == 'TV' else selected.arm, 'modalities': selected.modalities,
               'lambda': config.selected_lambda, 'floor': profile['input_relative_floor'],
               'residual_floor': profile['residual_floor'], 'lag': profile['lag'],
               'bin_seconds': profile['bin_seconds'], 'fit_bins': profile['fit_bins'],
               'cal_bins': profile['calibration_bins'], 'min_fit_rows': profile['min_fit_rows'],
               'min_cal_rows': profile['min_calibration_rows']}
        try:
            then = time.perf_counter()
            state = fit_detector(warmup, adj, types, fitmask, cfg)
            fit_seconds = time.perf_counter() - then
            _emit({'kind': 'c5_state', 'detector': detector, 'state': numeric._scientific_plain(state),
                   'threshold': selected.threshold, 'fit_seconds': fit_seconds})
            event = create_event_state(selected.threshold, bin_seconds=profile['bin_seconds'],
                                       streak=profile['event_streak'], refractory_seconds=profile['refractory_seconds'])
            prediction_seconds = 0.0
            for index, (values, endpoint) in enumerate(zip(stream, endpoints, strict=True)):
                then = time.perf_counter()
                result = score_bin(state, values)
                if result['endpoint'] != int(endpoint):
                    raise Error('C5_ENDPOINT_DRIFT')
                result['selected_system_score'] = result['tv_score'] if selected.arm == 'TV' else result['score']
                result['event'] = event_step(event, result['selected_system_score'], int(endpoint))
                prediction_seconds += time.perf_counter() - then
                _emit({'kind': 'c5_bin', 'detector': detector, 'index': index,
                       'bin': numeric._scientific_plain(result)})
                completed += 1
            status, reason = 'SUCCESS', None
        except Exception as exc:
            status, reason = 'FAILURE', type(exc).__name__
        _emit({'kind': 'c5_done', 'detector': detector, 'status': status, 'reason': reason,
               'completed_bins': completed, 'fit_seconds': fit_seconds,
               'prediction_seconds': prediction_seconds, 'detector_wall_seconds': time.perf_counter() - started})


def stream_worker(mode, wire, absolute_deadline, store, directory):
    """Bounded two-frame queue; deadline includes encoding/startup/wire/spill."""
    started = time.perf_counter()
    context, contract = provenance.registered_context()
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    raw_input = provenance._bounded_encode(wire, provenance.MAX_INPUT)
    if raw_input is None:
        raise Error('NUMERIC_INPUT_FRAME_OVERFLOW')
    events = queue.Queue(maxsize=2)
    stopped = threading.Event()
    rows, failure = [], None
    stderr_path = directory / ('stderr-' + str(time.time_ns()) + '.log')
    stdout_path = directory / ('stdout-' + str(time.time_ns()) + '.ndjson')
    environment = {**os.environ, **numeric.THREADS, 'PYTHONPATH': str(W / 'src'), 'PYTHONDONTWRITEBYTECODE': '1'}
    executable = W / ('environments/task-e/rcd39/Scripts/python.exe' if mode == 'rcd' else '.venv/Scripts/python.exe')
    script = Path(numeric.previous.__file__) if mode == 'rcd' else Path(__file__)
    process = None; monitor = None; peak = 0; max_frame = 0; parsed_bytes = 0; process_count = None
    with stderr_path.open('xb') as errors, stdout_path.open('xb') as transcript:
        if time.perf_counter() >= absolute_deadline:
            failure = 'TIMEOUT_BEFORE_WORKER_START'
        else:
            process = subprocess.Popen([str(executable), '-B', str(script), '--numeric-worker', mode],
                cwd=W, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors)
            try:
                monitor = WorkerTree(process.pid)
            except Exception as exc:
                # No sender has started, so the fixed worker never received a
                # numeric wire. EOF makes it exit without model computation;
                # let the redirector wait for that child before closing it.
                process.stdin.close()
                try:
                    process.wait(timeout=10)
                    reason = 'WORKER_MONITOR_INITIALIZATION_FAILED_NO_WIRE_SENT'
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait()
                    reason = 'WORKER_MONITOR_INITIALIZATION_FAILED_CLEANUP_UNVERIFIED_NO_WIRE_SENT'
                process.stdout.close()
                raise Error(reason) from exc
            def send():
                try:
                    process.stdin.write(raw_input); process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            def receive():
                try:
                    while True:
                        line = process.stdout.readline(provenance.MAX_FRAME + 2)
                        if not line:
                            break
                        while not stopped.is_set():
                            try:
                                events.put(line, timeout=.05); break
                            except queue.Full:
                                pass
                        if stopped.is_set():
                            break
                        if len(line) > provenance.MAX_FRAME + 1 or not line.endswith(b'\n'):
                            break
                finally:
                    while not stopped.is_set():
                        try:
                            events.put(None, timeout=.05); break
                        except queue.Full:
                            pass
            sender = threading.Thread(target=send, daemon=True)
            receiver = threading.Thread(target=receive, daemon=True)
            sender.start(); receiver.start()
            while True:
                if time.perf_counter() >= absolute_deadline:
                    failure = 'TIMEOUT'; break
                try:
                    memory = monitor.sample()
                except Exception as exc:
                    failure = str(exc); break
                peak = max(peak, memory['peak_private_bytes'])
                process_count = memory['observed_process_count']
                if memory['peak_private_bytes'] > contract['resource_policy']['numeric_worker_private_bytes_limit']:
                    failure = 'WORKER_MEMORY_BUDGET_EXCEEDED'; break
                controller_memory = resident_bytes(os.getpid())
                limit = contract['resource_policy'].get('controller_private_bytes_limit')
                if limit is not None:
                    if controller_memory is None:
                        failure = 'CONTROLLER_MEMORY_COUNTER_UNAVAILABLE'; break
                    if controller_memory['private_bytes'] > limit:
                        failure = 'CONTROLLER_MEMORY_BUDGET_EXCEEDED'; break
                try:
                    line = events.get(timeout=min(.05, max(.001, absolute_deadline - time.perf_counter())))
                except queue.Empty:
                    continue
                if line is None:
                    break
                transcript.write(line); transcript.flush(); os.fsync(transcript.fileno())
                if len(line) > provenance.MAX_FRAME + 1 or not line.endswith(b'\n'):
                    failure = 'OVERSIZED_OR_PARTIAL_FRAME'; break
                try:
                    row = provenance.decode(line[:-1])
                    ref = store.put(row)
                except Exception as exc:
                    failure = type(exc).__name__; break
                rows.append({'reference': ref, 'kind': row.get('kind'), 'detector': row.get('detector'),
                             'index': row.get('index'), 'draw': row.get('draw')})
                max_frame = max(max_frame, len(line) - 1); parsed_bytes += len(line) - 1
            if failure:
                try:
                    monitor.terminate()
                except Exception as exc:
                    failure += '|' + str(exc)
                process.kill()
            stopped.set()
            try:
                process.wait(timeout=max(.001, absolute_deadline - time.perf_counter()))
            except subprocess.TimeoutExpired:
                failure = 'TIMEOUT'
                try:
                    monitor.terminate()
                except Exception as exc:
                    failure += '|' + str(exc)
                process.kill(); process.wait()
            try:
                final_memory = monitor.sample(force=True)
                peak = max(peak, final_memory['peak_private_bytes'])
                process_count = final_memory['observed_process_count']
                if process_count < 2:
                    failure = failure or 'NUMERIC_DESCENDANT_NEVER_MEASURED'
                if peak > contract['resource_policy']['numeric_worker_private_bytes_limit']:
                    failure = failure or 'WORKER_MEMORY_BUDGET_EXCEEDED'
            except Exception as exc:
                failure = failure or str(exc)
            finally:
                monitor.close()
            sender.join(timeout=1)
            receiver.join(timeout=1)
            process.stdout.close()
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
        transcript.flush(); os.fsync(transcript.fileno())
    return {'rows': rows, 'exit_code': None if process is None else process.returncode,
            'timed_out': failure is not None and failure.startswith('TIMEOUT'), 'failure_reason': failure,
            'wall_seconds': time.perf_counter() - started, 'stderr_sha256': provenance.sha_file(stderr_path),
            'stderr_bytes': stderr_path.stat().st_size, 'stdout_sha256': provenance.sha_file(stdout_path),
            'stdout_bytes': stdout_path.stat().st_size, 'maximum_frame_bytes': max_frame,
            'parsed_json_bytes': parsed_bytes, 'peak_worker_private_bytes': peak or None,
            'memory_measurement': 'WINDOWS_WORKER_TREE_SUM_OBSERVED_OS_PEAKS_POLLED_50MS_NOT_A_HARD_OS_CAP',
            'observed_worker_process_count': process_count,
            'queued_frame_limit': 2, 'context_sha256': provenance._digest(context)}


def _primary(case, worker, store, source_admission, primary_wall):
    rows = [store.get(item['reference']) for item in worker['rows']]
    fake = case
    if case['c1'] is None:
        import numpy as np
        fake = {**case, 'c1': SimpleNamespace(node_ids=(), adjacency=np.zeros((0, 0), bool),
                handle=hashlib.sha256(f'G32|missing|{case["ordinal"]}'.encode()).hexdigest()[:16],
                ref=np.empty((0, 0, 0)), query=np.empty((0, 0, 0)), channel_types=(), quality={})}
    row = numeric._assemble_c1(fake, {**worker, 'rows': rows})
    if case['c1'] is None:
        row['scientific_diagnostics']['c1'].update(status='UNAVAILABLE_SOURCE_OBSERVATION', reason='C1_OBSERVATION_UNAVAILABLE')
    for group in row['c1'].values():
        for draw in group['R']:
            draw.pop('operator_diagnostics', None)
    for graph in row['control_graphs']:
        graph.pop('adjacency', None)
    return row


def _worker_summary(worker):
    return {key: value for key, value in worker.items() if key != 'rows'}


def _enforce_primary_postprocessing_budget(row, worker, timeout):
    """Late controller completion is a planned failure; retain numeric shards."""
    late = row['costs']['matched_aggregate_case_wall_seconds'] > timeout and not worker['timed_out']
    row['primary_postprocessing_budget_failure'] = late
    if late:
        for group in row['c1'].values():
            for item in (group['L'], group['O'], *group['R']):
                item.update(status='TIMEOUT', scores=None, reason='AGGREGATE_C1_POSTPROCESSING_TIMEOUT')
        row['costs']['timing_completed'] = False
        row['costs']['timed_out'] = True
        row['costs']['arm_wall_seconds'] = {name: dict.fromkeys(('L', 'O', 'R')) for name in ('primary', 'secondary')}


def _add_worker_roles(roles, prefix, worker):
    seen = set()
    for index, row in enumerate(worker['rows']):
        allowed = {'C1': {'header', 'draw', 'done', 'scientific_failure', 'worker_failure'},
                   'C5': {'c5_state', 'c5_bin', 'c5_done', 'worker_failure'}}
        expected = allowed.get(prefix, {'rcd', 'worker_failure'} if prefix.startswith('RCD/')
                               else {'integrated', 'scientific_failure', 'worker_failure'})
        if row['kind'] not in expected or (prefix == 'C5' and row['kind'] != 'worker_failure'
                                         and row['detector'] not in DETECTORS):
            raise Error('UNREGISTERED_SCIENTIFIC_WORKER_KIND')
        suffix = (str(row['draw']) if row['kind'] == 'draw' else
                  str(row['index']) if row['kind'] == 'c5_bin' else row['kind'])
        role = '/'.join(filter(None, (prefix, row.get('detector'), row['kind'], suffix)))
        if role in seen or role in roles:
            raise Error('DUPLICATE_SCIENTIFIC_WORKER_SLOT')
        roles[role] = row['reference']; seen.add(role)


def _rcd(case, contract, store, directory, roles):
    if case['rcd'] is None or case['c1'] is None:
        return numeric._run_rcd(case, contract['resource_policy']['auxiliary_worker_deadline_seconds'])
    packed = numeric._pack(case['rcd']['values'])
    roles['RCD/input'] = store.put({'values': packed, 'owners': case['rcd']['owners']})
    outputs, costs = [], []
    for seed in (420, 421, 422):
        worker = stream_worker('rcd', {'values': packed, 'seed': seed},
            time.perf_counter() + contract['resource_policy']['auxiliary_worker_deadline_seconds'], store, directory)
        _add_worker_roles(roles, f'RCD/{seed}', worker)
        records = [store.get(item['reference']) for item in worker['rows'] if item['kind'] == 'rcd']
        successful = worker['exit_code'] == 0 and not worker['failure_reason'] and len(records) == 1
        if successful:
            record = records[0]
            successful = (record['qualification_identity_sha256'] == numeric.previous.RCD_IDENTITY
                          and record['input_sha256'] == provenance._digest(packed)
                          and record['output']['seed'] == seed and record['output']['bins'] == 5)
        outputs.append(records[0]['output'] if successful else {'seed': seed, 'bins': 5, 'status': 'FAILURE',
                       'ranks': None, 'reason': worker['failure_reason'] or 'WORKER_FAILURE', 'error': None})
        costs.append({'seed': seed, **_worker_summary(worker)})
    return {'seed_outputs': outputs, 'metric_owners': {f'm{index}': int(owner) for index, owner in enumerate(case['rcd']['owners'])},
            'n_services': len(case['c1'].node_ids), 'input_sha256': provenance._digest(packed),
            'qualification_identity_sha256': numeric.previous.RCD_IDENTITY, 'costs': costs}


def compute_case(source, ordinal, source_admission, contract, store, directory, scope, *, c1_only=False):
    current_context, current_contract = (provenance.require_final_authorization() if scope == 'ACTUAL_FINAL60'
                                         else provenance.registered_context())
    if current_contract != contract or (c1_only and scope != 'DEVELOPMENT_TIMING_ONLY'):
        raise Error('COMPUTATION_CONTEXT_OR_SCOPE_DRIFT')
    start = time.perf_counter()
    writes_before = store.write_seconds
    timeout = contract['resource_policy']['development_timing_deadline_seconds'] if c1_only else contract['resource_policy']['common_L_O_R_timeout_seconds']
    if type(timeout) not in (int, float) or timeout <= 0:
        raise Error('MATCHING_DEVELOPMENT_TIMEOUT_NOT_REGISTERED')
    deadline = start + max(0., timeout - source_admission)
    case = source_api.get_case(source, ordinal)
    conversion_memory = resident_bytes(os.getpid())
    if conversion_memory is None:
        raise Error('CONTROLLER_MEMORY_COUNTER_UNAVAILABLE_AFTER_CONVERSION')
    if conversion_memory['private_bytes'] > contract['resource_policy']['controller_private_bytes_limit']:
        raise Error('CONTROLLER_CONVERSION_MEMORY_BUDGET_EXCEEDED')
    expected = source_api.DEVELOPMENT_SCOPE if c1_only else source_api.ACTUAL_SCOPE if scope == 'ACTUAL_FINAL60' else source_api.SYNTHETIC_SCOPE
    if case['source_metadata']['scope'] != expected:
        raise Error('SOURCE_SCOPE_NOT_ISSUED_FOR_THIS_RUN')
    roles = {}
    if case['c1'] is None:
        worker = {'rows': [], 'exit_code': None, 'timed_out': False, 'wall_seconds': None,
                  'stderr_sha256': None, 'stderr_bytes': None, 'failure_reason': 'C1_OBSERVATION_UNAVAILABLE'}
    else:
        wire = numeric.previous._c1_wire(case['c1'])
        roles['C1/input'] = store.put(wire)
        worker = stream_worker('c1', wire, deadline, store, directory)
        _add_worker_roles(roles, 'C1', worker)
    row = _primary(case, worker, store, source_admission, time.perf_counter() - start)
    row['c1_wire_sha256'] = None if case['c1'] is None else provenance._digest(wire)
    c1_diag = row['scientific_diagnostics']['c1']
    roles['C1/scientific'] = store.put(c1_diag)
    row.pop('scientific_diagnostics')
    bindings = {'candidate_ids': [] if case['c1'] is None else list(case['c1'].node_ids),
                'c5_candidate_ids': [] if case['c5'] is None else list(case['c5'].node_ids),
                'integrated_candidate_ids': {name: {} for name in DETECTORS},
                'quality': numeric._scientific_plain(case.get('quality') or
                    (dict(case['c1'].quality) if case['c1'] is not None else {
                        'source_scope': case['source_metadata']['scope'],
                        'conversion_failures': case['source_metadata'].get('conversion_failures', {})})),
                'source_hashes': case['source_metadata'].get('source_hashes', {}) if case['c1'] is None
                                 else dict(case['c1'].source_hashes),
                'conversion_provenance': numeric._scientific_plain(case['source_metadata']),
                'graph_provenance': None if case['c1'] is None else numeric._scientific_plain(dict(case['c1'].graph_provenance)),
                'evidence_catalog': None if case['c1'] is None else numeric._scientific_plain(case['c1'].evidence_catalog),
                'c5_quality': None if case['c5'] is None else numeric._scientific_plain(dict(case['c5'].quality)),
                'c5_graph_provenance': None if case['c5'] is None else numeric._scientific_plain(dict(case['c5'].graph_provenance))}
    roles['C1/issued-bindings'] = store.put({key: value for key, value in bindings.items()
                                          if key not in ('c5_quality', 'c5_graph_provenance', 'integrated_candidate_ids')})
    roles['C1/numeric-results'] = store.put({key: copy.deepcopy(row[key]) for key in
        ('c1', 'control_graphs', 'local_evidence', 'shared_preprocessing_failed')})
    numeric.previous._apply_walltime_measurement(row, source_admission, time.perf_counter() - start)
    _enforce_primary_postprocessing_budget(row, worker, timeout)
    details = {'C1': _worker_summary(worker), 'C5': None, 'integrated': {},
               'controller_after_conversion': conversion_memory}
    if not c1_only:
        for method in ('Local-MAX-MT', 'BARO-RANK-adapted-TD12'):
            row['contextual'].setdefault(method, {'status': 'FAILURE', 'scores': None})
        row['contextual']['RCD'] = _rcd(case, contract, store, directory, roles)
        observation = case['c5']
        endpoints = [] if observation is None else observation.relative_endpoints.tolist()
        c5wire = {} if observation is None else numeric._c5_wire(observation)
        roles['C5/input'] = store.put(c5wire)
        c5worker = (stream_worker('c5', c5wire,
                    time.perf_counter() + contract['resource_policy']['auxiliary_worker_deadline_seconds'], store, directory)
                    if observation is not None else {'rows': [], 'exit_code': None, 'timed_out': False,
                    'wall_seconds': None, 'failure_reason': 'C5_OBSERVATION_UNAVAILABLE'})
        _add_worker_roles(roles, 'C5', c5worker)
        details['C5'] = _worker_summary(c5worker)
        thresholds = {item['id']: item['threshold'] for item in contract['prepared_conditions']['scientific_objects']['selections']['c5']['detectors']}
        integrated = {}; measured_fit = []; measured_prediction = []
        for detector in DETECTORS:
            records = [item for item in c5worker['rows'] if item['detector'] == detector]
            prefix = [store.get(item['reference'])['bin'] for item in records if item['kind'] == 'c5_bin']
            if [item['endpoint'] for item in prefix] != endpoints[:len(prefix)]:
                raise Error('C5_COMMITTED_PREFIX_DRIFT')
            done = next((store.get(item['reference']) for item in records if item['kind'] == 'c5_done'), None)
            success = done is not None and done['status'] == 'SUCCESS' and len(prefix) == len(endpoints)
            status = 'SUCCESS' if success else 'TIMEOUT' if c5worker['timed_out'] else 'FAILURE'
            scores = [item['selected_system_score'] for item in prefix] + [None] * (len(endpoints) - len(prefix))
            triggers = []
            for item in prefix:
                if not item['event']['trigger']:
                    continue
                endpoint = item['endpoint']
                if endpoint < 360:
                    result = {'endpoint': endpoint, 'status': 'INSUFFICIENT_HISTORY', 'scores': None,
                              'candidate_count': 0, 'input_sha256': None, 'candidate_ids': []}
                else:
                    if endpoint not in integrated:
                        then = time.perf_counter()
                        integrated_deadline = then + contract['resource_policy']['integrated_end_to_end_deadline_seconds']
                        known_keys, known_wire_digest = [], None
                        try:
                            one = source_api.integrated_observation(source, ordinal, endpoint)
                            known_keys = list(one.node_ids)
                            one_wire = numeric.previous._c1_wire(one, 'INTEGRATED')
                            known_wire_digest = provenance._digest(one_wire)
                            roles[f'integrated/{endpoint}/input'] = store.put(one_wire)
                            roles[f'integrated/{endpoint}/bindings'] = store.put({
                                'quality': numeric._scientific_plain(dict(one.quality)),
                                'graph_provenance': numeric._scientific_plain(dict(one.graph_provenance)),
                                'evidence_catalog': numeric._scientific_plain(one.evidence_catalog),
                                'candidate_ids': known_keys})
                            predicted = stream_worker('c1', one_wire, integrated_deadline, store, directory)
                            _add_worker_roles(roles, f'integrated/{endpoint}', predicted)
                            outputs = [store.get(item['reference']) for item in predicted['rows'] if item['kind'] == 'integrated']
                            output = outputs[0] if len(outputs) == 1 and predicted['exit_code'] == 0 and not predicted['failure_reason'] else {
                                'status': 'TIMEOUT' if predicted['timed_out'] else 'FAILURE', 'scores': None}
                            result = {'endpoint': endpoint, 'status': output['status'], 'scores': output['scores'],
                                      'candidate_count': len(one.node_ids), 'candidate_ids': list(one.node_ids),
                                      'input_sha256': provenance._digest(one_wire)}
                            details['integrated'][str(endpoint)] = _worker_summary(predicted)
                            if time.perf_counter() >= integrated_deadline:
                                result.update(status='TIMEOUT', scores=None, reason='INTEGRATED_END_TO_END_TIMEOUT')
                        except Error:
                            raise
                        except Exception as exc:
                            result = {'endpoint': endpoint, 'status': 'FAILURE', 'scores': None,
                                      'candidate_count': len(known_keys), 'candidate_ids': known_keys, 'input_sha256': known_wire_digest,
                                      'reason': type(exc).__name__}
                        result['wall_seconds'] = time.perf_counter() - then
                        integrated[endpoint] = result
                    result = copy.deepcopy(integrated[endpoint])
                    result['reused_equal_endpoint_computation'] = any(
                        str(endpoint) in mapping for mapping in bindings['integrated_candidate_ids'].values())
                bindings['integrated_candidate_ids'][detector][str(endpoint)] = result.pop('candidate_ids')
                triggers.append(result)
            row['c5'][detector] = {'status': status, 'threshold': thresholds[detector],
                'starts': [end - 5 for end in endpoints], 'ends': endpoints, 'scores': scores,
                'bin_statuses': ['SUCCESS' if value is not None else 'UNAVAILABLE' if index < len(prefix) else status
                                 for index, value in enumerate(scores)], 'triggers': triggers,
                'wall_seconds': None if done is None else done['detector_wall_seconds']}
            if done and done['fit_seconds'] is not None: measured_fit.append(done['fit_seconds'])
            if done and done['prediction_seconds'] is not None: measured_prediction.append(done['prediction_seconds'])
            del prefix
        row['costs'].update(c5_fit_seconds=sum(measured_fit) if len(measured_fit) == 8 else None,
            c5_prediction_seconds=sum(measured_prediction) if len(measured_prediction) == 8 else None,
            c5_fit_partial_measured_seconds=sum(measured_fit) if measured_fit else None,
            c5_prediction_partial_measured_seconds=sum(measured_prediction) if measured_prediction else None,
            integrated_seconds=sum(result['wall_seconds'] for result in integrated.values()) if integrated else None)
    else:
        row['contextual'] = {}; row['c5'] = {}
    roles['case/controller-bindings'] = store.put(bindings)
    row['costs'].update(cold_io_seconds=case['source_metadata'].get('conversion_costs', {}).get('cold_io_and_hash_seconds'),
                        scientific_shard_write_seconds=store.write_seconds - writes_before,
                        cost_components_overlap=True, case_end_to_end_wall_seconds=time.perf_counter() - start)
    roles['case/compact'] = store.put(row)
    details['controller_after_case'] = resident_bytes(os.getpid())
    if details['controller_after_case'] is None:
        raise Error('CONTROLLER_MEMORY_COUNTER_UNAVAILABLE_AFTER_CASE')
    if details['controller_after_case']['private_bytes'] > contract['resource_policy']['controller_private_bytes_limit']:
        raise Error('CONTROLLER_CASE_MEMORY_BUDGET_EXCEEDED')
    inventory = {'schema': 'TD13-G33-CASE-INVENTORY-v1', 'ordinal': ordinal, 'scope': scope,
                 'context': provenance.registered_context()[0], 'scientific_roles': roles,
                 'worker_measurements': details, 'C1_only_development_timing': c1_only,
                 'planned_C1_draws': 256, 'planned_RCD_seeds': [] if c1_only else [420, 421, 422],
                 'planned_C5_detectors': [] if c1_only else list(DETECTORS)}
    return inventory, row


def _check_candidate_keys(keys, count, development=False):
    if development:
        if keys != [f'v{index}' for index in range(count)]:
            raise Error('LOCKED_DEVELOPMENT_ANONYMOUS_UNIVERSE_DRIFT')
    else:
        provenance.bridge._pseudokeys(keys, count)


def _validate_conversion_provenance(bindings, scope):
    """Retain issued per-case clocks/quality/costs in the controller packet."""
    metadata = bindings.get('conversion_provenance')
    expected = (source_api.DEVELOPMENT_SCOPE if scope == 'DEVELOPMENT_TIMING_ONLY' else
                source_api.ACTUAL_SCOPE if scope == 'ACTUAL_FINAL60' else source_api.SYNTHETIC_SCOPE)
    if (type(metadata) is not dict or metadata.get('scope') != expected
            or metadata.get('conversion_only') is not True
            or type(metadata.get('conversion_costs')) is not dict):
        raise Error('ISSUED_CONVERSION_PROVENANCE_MISSING_OR_SCOPE_DRIFT')
    if scope == 'DEVELOPMENT_TIMING_ONLY':
        if metadata.get('numeric_cache_verified') is not True:
            raise Error('DEVELOPMENT_CACHE_PROVENANCE_MISSING')
    else:
        for name in ('source_hashes', 'clock_windows', 'conversion_failures', 'numeric_inventory',
                     'c1_quality', 'c5_quality', 'rcd_quality'):
            if type(metadata.get(name)) is not dict:
                raise Error('PER_CASE_CONVERSION_PROVENANCE_INCOMPLETE')
        clocks = metadata['clock_windows']
        if (type(clocks.get('modalities')) is not dict or set(clocks['modalities']) != {'metrics', 'traces', 'logs'}
                or clocks.get('source_of_window') != 'VERIFIED_INJECT_TIME_PROJECTION_NOT_ORIGIN_OFFSET'
                or clocks.get('c5_receives_timing_marker') is not False):
            raise Error('CONVERSION_CLOCK_OR_WINDOW_PROVENANCE_MISSING')
        if metadata['source_hashes'] != bindings['source_hashes']:
            raise Error('CONVERSION_SOURCE_HASH_BINDING_DRIFT')


def validate_case_inventory(inventory, store, contract):
    """Hydrate one C1 or one detector at a time, never a whole-case packet."""
    scope = inventory.get('scope')
    development = scope == 'DEVELOPMENT_TIMING_ONLY'
    if (scope not in ('DEVELOPMENT_TIMING_ONLY', 'SYNTHETIC_G33_PREPARATION', 'ACTUAL_FINAL60')
            or type(inventory.get('C1_only_development_timing')) is not bool
            or inventory['C1_only_development_timing'] is not development):
        raise Error('DEVELOPMENT_ONLY_FLAG_OR_SCOPE_DRIFT')
    if development and (inventory.get('planned_RCD_seeds') != [] or inventory.get('planned_C5_detectors') != []):
        raise Error('DEVELOPMENT_TIMING_EXTRA_DENOMINATORS')
    roles = inventory['scientific_roles']
    if development and any(role.startswith(('C5/', 'RCD/', 'integrated/')) for role in roles):
        raise Error('DEVELOPMENT_TIMING_EXTRA_SCIENTIFIC_ROLES')
    row = store.get(roles['case/compact'])
    bindings = store.get(roles['case/controller-bindings'])
    if inventory.get('schema') != 'TD13-G33-CASE-INVENTORY-v1' or not bindings.get('quality'):
        raise Error('SCIENTIFIC_INVENTORY_OR_QUALITY_MISSING')
    if row['ordinal'] != inventory['ordinal'] or len(bindings['candidate_ids']) != row['candidate_count']:
        raise Error('CASE_OR_CANDIDATE_BINDING_DRIFT')
    bridge = provenance.bridge
    bridge.historical._no_oracles(bindings)
    _validate_conversion_provenance(bindings, scope)
    if type(bindings.get('integrated_candidate_ids')) is not dict or set(bindings['integrated_candidate_ids']) != set(DETECTORS):
        raise Error('EIGHT_TRIGGER_UNIVERSE_MAPS_REQUIRED')
    _check_candidate_keys(bindings['candidate_ids'], row['candidate_count'],
                          inventory['scope'] == 'DEVELOPMENT_TIMING_ONLY' and inventory['C1_only_development_timing'])
    base_roles = {'case/compact', 'case/controller-bindings', 'C1/scientific', 'C1/input', 'C1/issued-bindings', 'C1/numeric-results', 'C5/input', 'RCD/input'}
    issued_binding = store.get(roles['C1/issued-bindings'])
    expected_issued_binding = {key: value for key, value in bindings.items()
        if key not in ('c5_quality', 'c5_graph_provenance', 'integrated_candidate_ids')}
    if issued_binding != expected_issued_binding:
        raise Error('C1_SOURCE_OR_LITERAL_BINDING_DRIFT_OR_INCOMPLETE')
    for role, reference in roles.items():
        if role in base_roles:
            continue
        full = store.get(reference)
        bridge.historical._no_oracles(full)
        if role.startswith('C1/'):
            prefix = 'C1'
        elif role.startswith('C5/'):
            prefix = 'C5'
        elif role.startswith('RCD/'):
            prefix = '/'.join(role.split('/')[:2])
        elif role.startswith('integrated/'):
            prefix = '/'.join(role.split('/')[:2])
            if role.endswith(('/input', '/bindings')):
                continue
        else:
            raise Error('UNREGISTERED_OR_STALE_SCIENTIFIC_ROLE')
        expected_role = {}
        _add_worker_roles(expected_role, prefix, {'rows': [{'reference': reference, 'kind': full.get('kind'),
            'draw': full.get('draw'), 'index': full.get('index'), 'detector': full.get('detector')}]})
        if set(expected_role) != {role}:
            raise Error('SCIENTIFIC_ROLE_CONTENT_DRIFT')
    prepared = contract['prepared_conditions']['scientific_objects']['selections']
    c1 = store.get(roles['C1/scientific'])
    if 'C1/input' in roles:
        wire = store.get(roles['C1/input'])
        if row.get('c1_wire_sha256') != provenance._digest(wire):
            raise Error('C1_NUMERIC_INPUT_BINDING_DRIFT')
        if any(c1['input'].get(key) != wire[key] for key in ('ref', 'query', 'adj', 'channel_types')):
            raise Error('C1_DIAGNOSTIC_INPUT_DRIFT')
        if any(draw['seed'] != numeric.previous._seed(wire['routing_handle'], draw['draw']) for draw in row['control_graphs']):
            raise Error('FROZEN_CONTROL_SEED_RECIPE_DRIFT')
    enriched = copy.deepcopy(row)
    numeric_results = store.get(roles['C1/numeric-results'])
    if row.get('primary_postprocessing_budget_failure'):
        if any(item['status'] != 'TIMEOUT' or item['scores'] is not None
               for group in row['c1'].values() for item in (group['L'], group['O'], *group['R'])):
            raise Error('POSTPROCESSING_TIMEOUT_WAS_PROMOTED_TO_SUCCESS')
        enriched.update(copy.deepcopy(numeric_results))
    elif any(row[key] != value for key, value in numeric_results.items()):
        raise Error('NUMERIC_COMPACT_OUTCOME_DRIFT')
    for draw in enriched['control_graphs']:
        ref = roles.get(f'C1/draw/{draw["draw"]}')
        if ref is not None:
            full = store.get(ref)
            if full['graph']['seed'] != draw['seed'] or full['graph']['graph_sha256'] != draw['graph_sha256']:
                raise Error('CONTROL_SEED_OR_GRAPH_BINDING_DRIFT')
            draw['adjacency'] = full['graph']['adjacency']
    bridge.historical._validate_c1(enriched)
    for name, group in enriched['c1'].items():
        for draw in group['R']:
            if draw['status'] == 'SUCCESS':
                ref = roles.get(f'C1/draw/{draw["draw"]}')
                if ref is None:
                    raise Error('MISSING_PLANNED_R_SCIENTIFIC_SHARD')
                full = store.get(ref)
                if full['rankers'][name]['scores'] != draw['scores']:
                    raise Error('CONTROL_COMPACT_SCORE_DRIFT')
                compact_full = {key: value for key, value in full['rankers'][name].items() if key != 'operator_diagnostics'}
                if compact_full != draw:
                    raise Error('CONTROL_STATUS_OR_OPERATOR_BINDING_DRIFT')
                draw['operator_diagnostics'] = full['rankers'][name]['operator_diagnostics']
                provenance.bridge.historical._graph(full['graph'], row['candidate_count'])
    bridge._validate_c1_diagnostics(c1, enriched, prepared['c1'])
    bridge._validate_costs(row['costs'])
    if inventory['planned_C1_draws'] != 256 or any(len(group['R']) != 256 for group in row['c1'].values()):
        raise Error('CONTROL_DENOMINATOR_CHANGED')
    if development:
        return
    if inventory['planned_RCD_seeds'] != [420, 421, 422] or inventory['planned_C5_detectors'] != list(DETECTORS):
        raise Error('BASELINE_OR_DETECTOR_DENOMINATOR_CHANGED')
    bridge.historical._validate_contextual(row)
    bridge.historical._validate_c5(row, contract['prepared_conditions'])
    wire = store.get(roles['C5/input'])
    selection = prepared['c5']
    for detector in DETECTORS:
        state_ref = roles.get(f'C5/{detector}/c5_state/c5_state')
        state = None if state_ref is None else store.get(state_ref)['state']
        prefix = []
        for index in range(len(row['c5'][detector]['ends'])):
            ref = roles.get(f'C5/{detector}/c5_bin/{index}')
            if ref is None:
                break
            item = store.get(ref)
            if item['index'] != index or item['detector'] != detector:
                raise Error('C5_BIN_REFERENCE_ORDER_DRIFT')
            prefix.append(item['bin'])
        expected_prefix = sum(value in ('SUCCESS', 'UNAVAILABLE') for value in row['c5'][detector]['bin_statuses'])
        if len(prefix) != expected_prefix:
            raise Error('C5_SCIENTIFIC_PREFIX_MISSING')
        bin_roles = {name for name in roles if name.startswith(f'C5/{detector}/c5_bin/')}
        if bin_roles != {f'C5/{detector}/c5_bin/{index}' for index in range(len(prefix))}:
            raise Error('C5_DUPLICATE_STALE_OR_NONPREFIX_BIN')
        done_ref = roles.get(f'C5/{detector}/c5_done/c5_done')
        if done_ref:
            done = store.get(done_ref)
            if done['completed_bins'] != len(prefix) or (row['c5'][detector]['status'] == 'SUCCESS' and done['status'] != 'SUCCESS'):
                raise Error('C5_DONE_OR_PREFIX_BINDING_DRIFT')
        record = {'input': wire, 'state': state, 'bins': prefix, 'status': row['c5'][detector]['status'],
                  'reason': 'C5_OBSERVATION_UNAVAILABLE' if wire == {} else 'WORKER_FAILURE'}
        bridge._validate_c5_state(record, row['c5'][detector], detector, selection)
        expected_triggers = [item['endpoint'] for item in prefix if item['event']['trigger']]
        if expected_triggers != [item['endpoint'] for item in row['c5'][detector]['triggers']]:
            raise Error('TRIGGER_WAS_DROPPED_OR_INVENTED')
        if set(bindings['integrated_candidate_ids'][detector]) != {str(value) for value in expected_triggers}:
            raise Error('TRIGGER_UNIVERSE_MISSING_OR_STALE')
        for trigger in row['c5'][detector]['triggers']:
            endpoint = trigger['endpoint']
            keys = bindings['integrated_candidate_ids'][detector][str(endpoint)]
            bridge._pseudokeys(keys, trigger['candidate_count'])
            if trigger['status'] == 'SUCCESS':
                full = store.get(roles[f'integrated/{endpoint}/integrated/integrated'])
                input_wire = store.get(roles[f'integrated/{endpoint}/input'])
                if trigger['input_sha256'] != provenance._digest(input_wire) or full['scores'] != trigger['scores']:
                    raise Error('INTEGRATED_INPUT_OR_SCORE_BINDING_DRIFT')
                bridge._validate_c1_diagnostics(full['scientific_diagnostics'], trigger, prepared['c1'], integrated=True)
                integrated_binding = store.get(roles[f'integrated/{endpoint}/bindings'])
                if (integrated_binding['candidate_ids'] != keys
                        or any(type(integrated_binding.get(name)) is not dict or not integrated_binding[name]
                               for name in ('quality', 'graph_provenance', 'evidence_catalog'))):
                    raise Error('INTEGRATED_LITERAL_UNIVERSE_DRIFT')
        del prefix, state
    rcd = row['contextual']['RCD']
    if 'RCD/input' in roles:
        issued = store.get(roles['RCD/input'])
        if rcd['input_sha256'] != provenance._digest(issued['values']) or rcd['metric_owners'] != {
                f'm{index}': owner for index, owner in enumerate(issued['owners'])}:
            raise Error('RCD_NUMERIC_OR_LITERAL_OWNER_BINDING_DRIFT')
        for item in rcd['seed_outputs']:
            if item['status'] == 'SUCCESS':
                full = store.get(roles[f'RCD/{item["seed"]}/rcd/rcd'])
                if full['output'] != item or full['input_sha256'] != rcd['input_sha256']:
                    raise Error('RCD_SEED_OUTPUT_BINDING_DRIFT')


class Execution:
    __slots__ = ('__weakref__',)


@contextmanager
def _driver_lock():
    """Exclusive OS lock, automatically released on controller death."""
    path = provenance.ROOT / 'cache/driver.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    provenance.bridge._require_regular_path(path, allow_missing=True)
    with path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        import msvcrt
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise Error('G33_CONTROLLER_ALREADY_RUNNING') from exc
        try:
            yield
        finally:
            stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def _one_driver(function):
    def wrapped(*args, **kwargs):
        with _driver_lock():
            return function(*args, **kwargs)
    return wrapped


def _bind_runs():
    issued = weakref.WeakKeyDictionary()
    compute = compute_case
    synthetic_factory, actual_factory = source_api.make_synthetic_source, source_api.open_final_source
    def run(final=False):
        context, contract = provenance.require_final_authorization() if final else provenance.registered_context()
        scope = 'ACTUAL_FINAL60' if final else 'SYNTHETIC_G33_PREPARATION'
        target = provenance.ROOT / ('predictions-seal.json' if final else 'cache/preparation-seal.json')
        if target.exists():
            raise Error('COMPLETE_SEAL_EXISTS_NO_MODEL_RERUN')
        then = time.perf_counter()
        source = actual_factory() if final else synthetic_factory()
        admission = time.perf_counter() - then
        count = 60 if final else 3
        if source_api.case_count(source) != count:
            raise Error('EXACT_REGISTERED_CASE_COUNT_REQUIRED')
        directory = provenance.ROOT / 'cache' / ('final-attempt' if final else 'synthetic-attempt')
        directory.mkdir(exist_ok=True)
        attempt_value = {'scope': scope, 'context': context, 'planned_cases': count,
                         'truth_read': False, 'reproduction_policy': contract['reproduction_policy']}
        attempt_path = directory / 'attempt.json'
        if attempt_path.exists():
            if provenance.decode(attempt_path.read_bytes()) != attempt_value:
                raise Error('STALE_ATTEMPT_RECOVERY_FORBIDDEN')
            attempt = {'path': attempt_path.relative_to(W).as_posix(),
                       'sha256': provenance.sha_file(attempt_path), 'bytes': attempt_path.stat().st_size}
        else:
            attempt = provenance.exclusive(attempt_path, attempt_value)
        store = provenance.ShardStore(); manifests = []
        for ordinal in range(count):
            checkpoint = directory / f'case-{ordinal:02d}.json'
            if checkpoint.exists():
                saved = provenance.decode(checkpoint.read_bytes())
                if saved['context'] != context:
                    raise Error('STALE_CASE_CHECKPOINT')
                store.verify(saved['inventory'])
                existing = store.get(saved['inventory'])
                for reference in existing['scientific_roles'].values():
                    store.verify(reference)
                validate_case_inventory(existing, store, contract)
                manifests.append(saved['inventory'])
                continue
            began = directory / f'case-{ordinal:02d}-began.json'
            if began.exists():
                raise Error('INTERRUPTED_PARTIAL_CASE_PRESERVED_REQUIRES_RECOVERY_DECISION')
            provenance.exclusive(began, {'ordinal': ordinal, 'context': context, 'no_outcome_selected_retry': True})
            inventory, _ = compute(source, ordinal, admission, contract, store, directory, scope)
            validate_case_inventory(inventory, store, contract)
            ref = store.put(inventory)
            provenance.exclusive(checkpoint, {'context': context, 'inventory': ref})
            manifests.append(ref)
            _emit({'phase': scope, 'completed_case_inventories': len(manifests), 'planned_cases': count})
        if provenance.registered_context()[0] != context:
            raise Error('CONTEXT_CHANGED_DURING_EXECUTION')
        handle = Execution()
        issued[handle] = {'scope': scope, 'context': context, 'case_inventory_manifest': manifests,
                          'source_summary': source_api.source_summary(source), 'attempt_manifest': attempt}
        return handle
    def payload(handle):
        if type(handle) is not Execution or handle not in issued:
            raise Error('UNISSUED_G33_EXECUTION')
        return copy.deepcopy(issued[handle])
    return _one_driver(lambda: run(False)), _one_driver(lambda: run(True)), payload


run_synthetic_readiness, run_final_campaign, _issued_execution_for_provenance = _bind_runs()
del _bind_runs


@_one_driver
def run_development_timing():
    context, contract = provenance.registered_context()
    if contract['permissions'].get('development30_timing_only') is not True:
        raise Error('DEVELOPMENT_TIMING_CLOSED')
    directory = provenance.ROOT / 'cache' / ('development-' + str(time.time_ns()))
    directory.mkdir(parents=True)
    provenance.exclusive(directory / 'attempt.json', {'context': context, 'planned_cases': 30, 'outcomes_read': False})
    then = time.perf_counter(); source = source_api.load_development_source(); admission = time.perf_counter() - then
    store = provenance.ShardStore(); records = []; checkpoints = []
    for ordinal in range(30):
        inventory, row = compute_case(source, ordinal, admission, contract, store, directory, 'DEVELOPMENT_TIMING_ONLY', c1_only=True)
        validate_case_inventory(inventory, store, contract)
        reference = store.put(inventory)
        checkpoints.append(provenance.exclusive(directory / f'case-{ordinal:02d}.json', {'context': context, 'inventory': reference}))
        records.append({'ordinal': ordinal, 'c1': row['c1'], 'costs': row['costs']})
        _emit({'phase': 'G33_DEVELOPMENT_TIMING_ONLY', 'completed_cases': len(records), 'planned_cases': 30})
    report = numeric.previous._timing_report(records, source_api.source_summary(source))
    report.update(context=context, case_checkpoints=checkpoints,
                  workload='G33_STREAMED_C1_FROZEN_MATH_FULL_WALL', actual_models_or_labels=False)
    return provenance.exclusive(directory / 'timing.json', report)


def _main():
    if len(sys.argv) == 3 and sys.argv[1] == '--numeric-worker' and sys.argv[2] in ('c1', 'c5'):
        try:
            _worker_guard()
            raw = sys.stdin.buffer.read(provenance.MAX_INPUT + 1)
            if len(raw) > provenance.MAX_INPUT:
                raise Error('INPUT_FRAME_LIMIT')
            wire = provenance.decode(raw)
            if sys.argv[2] == 'c1':
                numeric._numeric_c1_worker(wire)
            else:
                _c5_worker(wire)
            return 0
        except Exception as exc:
            _emit({'kind': 'worker_failure', 'reason': type(exc).__name__})
            return 2
    if sys.argv[1:] == ['--development-timing']:
        _emit(run_development_timing()); return 0
    if sys.argv[1:] == ['--synthetic-readiness']:
        then = time.perf_counter()
        result = provenance.commit_execution(run_synthetic_readiness())
        _emit({'verified': result['_verified'], 'external_run_and_commit_wall_seconds': time.perf_counter() - then}); return 0
    if sys.argv[1:] == ['--final-campaign']:
        result = provenance.commit_execution(run_final_campaign()); _emit(result['_verified']); return 0
    raise Error('ONLY_REGISTERED_FIXED_COMMANDS_ALLOWED')


if __name__ == '__main__':
    raise SystemExit(_main())
