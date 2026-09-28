"""Trusted post-trigger development composition; every diagnosis uses past only."""
from __future__ import annotations
import argparse
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.contract import DEV_IDS, opaque_handle
from scripts.task_e.execution import save_json, save_npz, require_contract, file_sha, failure
from scripts.task_e.c1_development import read_pinned
from scripts.task_e.audit_development import read_acquired
from scripts.task_e.input_adapters import integrated_bundle
from scripts.task_e.boundary import NumericWorker
from scripts.task_e.worker import encode_message
from scripts.task_e.evaluator import tie_metrics
from scripts.task_e.calibration import first_trigger_composition, RANK_METRICS

DETECTORS = tuple(f'{arm}-{mode}' for arm in ('G', 'L', 'ALL', 'TV') for mode in ('MT', 'MTL'))
PROFILE = 'TD12-INTEGRATED-MTL'


def validate_hooks(hooks):
    if hooks.get('schema') != 'TD13-C5-DEVELOPMENT-v1':
        raise ValueError('Unregistered C5 hook schema')
    by_case = defaultdict(dict)
    for item in hooks['items']:
        case, detector = item['case'], item['detector']
        if (case not in DEV_IDS or item['handle'] != opaque_handle(case)
                or detector not in DETECTORS or detector in by_case[case]
                or item.get('threshold_mode') != 'OOF' or item.get('profile') != PROFILE):
            raise ValueError('Unapproved or duplicate trigger identity/profile/mode')
        endpoints = item['triggers']
        if (not isinstance(endpoints, list) or any(type(t) not in (int, float)
                or not math.isfinite(t) or t < 0 or t != int(t) for t in endpoints)
                or any(b <= a for a, b in zip(endpoints, endpoints[1:]))):
            raise ValueError('Trigger clocks must be ordered distinct finite nonnegative integers')
        first = item.get('first_post_injection_trigger')
        if first is not None and (type(first) not in (int, float) or first not in endpoints):
            raise ValueError('First trigger is not a member of the declared events')
        by_case[case][detector] = item
    return by_case


def zero_composition(status, endpoint=None):
    return {'status': status, 'endpoint': endpoint, 'metrics': dict.fromkeys(RANK_METRICS, 0.)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    parser.add_argument('--audit-root', required=True, type=Path)
    parser.add_argument('--acquisition', required=True, type=Path)
    parser.add_argument('--c1-selection', required=True, type=Path)
    parser.add_argument('--c5-hook', required=True, type=Path)
    args = parser.parse_args()
    run = args.run
    contract = require_contract(run, 'development')
    sources, objects = {}, []
    for name, path in (('hook', args.c5_hook), ('selection', args.c1_selection), ('acquisition', args.acquisition)):
        path = read_pinned(path, contract)
        sources[name] = file_sha(path)
        objects.append(json.loads(path.read_text(encoding='utf-8')))
    hooks, selection, acquired = objects
    by_case = validate_hooks(hooks)
    local = {**selection['local_config'], 'include_logs': True}
    rank = selection['ppr_config']
    outcomes = {d: {} for d in DETECTORS}
    resources = {}
    with NumericWorker(timeout_seconds=300) as worker:
        for case in DEV_IDS:
            start = time.perf_counter()
            handle = opaque_handle(case)
            audit_path = read_pinned(args.audit_root / 'case-audits' / (handle + '.json'), contract)
            report = json.loads(audit_path.read_text(encoding='utf-8'))
            if report['case'] != case or report['handle'] != handle:
                raise ValueError('Wrong audit case')
            profile = report.get('profiles', {}).get('c5_primary', {})
            origin = profile.get('s0') if profile.get('status') == 'MATERIALIZED' else None
            if origin is not None and (type(origin) not in (int, float) or not math.isfinite(origin)):
                raise ValueError('Nonfinite C5 clock origin')
            tau = report['metadata']['inject_time'] - origin if origin is not None else None
            items = by_case[case]
            # The full event list is authoritative. Recompute first-post only in
            # the evaluator; a derived hook summary never selects model inputs.
            endpoints = sorted({int(t) for item in items.values() for t in item['triggers']})
            source_hashes = {**sources, 'audit': file_sha(audit_path)}
            for entry in acquired.get('files', []):
                if entry['remote_path'].startswith(case + '/'):
                    source_hashes[entry['remote_path']] = entry['sha256']
            raw, raw_error = None, None
            if origin is not None and any(t >= 360 for t in endpoints):
                try:
                    raw = read_acquired(acquired, report['metadata'])
                except Exception as exc:
                    raw_error = failure(run, 'integrated_input', case, exc)
            diagnoses = {}
            for endpoint in endpoints:
                trigger_start = time.perf_counter()
                name = f'{handle}-{endpoint}'
                result, bundle, error = None, None, None
                status, artifacts = 'VALID', []
                if origin is None or raw_error:
                    status = 'INPUT_FAILURE'
                    error = raw_error or {'type': 'MissingC5Origin', 'message': 'C5 primary profile unavailable'}
                elif endpoint < 360:
                    status = 'INSUFFICIENT_HISTORY'
                else:
                    try:
                        bundle = integrated_bundle(raw, origin + endpoint)
                        result = worker.c1(bundle['ref'], bundle['query'], bundle['adj'],
                                           bundle['channel_types'], local, [rank])
                    except Exception as exc:
                        status = 'METHOD_FAILURE'
                        error = failure(run, 'integrated', case, exc)
                # Evidence-write errors abort: lost evidence is never a method failure.
                if result is not None:
                    reply_path = run / 'raw-replies' / (name + '.bin')
                    reply_path.parent.mkdir(parents=True, exist_ok=True)
                    with reply_path.open('xb') as stream:
                        stream.write(encode_message(result))
                    artifacts.append({'path': str(reply_path), 'sha256': file_sha(reply_path),
                                      'role': 'lossless re-encoding of complete returned numeric reply'})
                    if np.any(result['evidence']['diagnostics']['numerical_channel_failures']):
                        status = 'METHOD_FAILURE'
                        error = {'type': 'NumericChannelFailure', 'message': 'Invalid integrated local channel'}
                    predicted = result['rankings'][0]['scores']
                    if (np.asarray(predicted).shape != (len(bundle['service_names']),)
                            or not np.isfinite(predicted).all()):
                        status = 'METHOD_FAILURE'
                        error = {'type': 'NumericRankingFailure', 'message': 'Nonfinite or wrong-width integrated scores'}
                    target = run / 'predictions' / (name + '.npz')
                    save_npz(target, scores=predicted, local=result['evidence']['local'],
                             ref=bundle['ref'], query=bundle['query'], adj=bundle['adj'],
                             channel_mask=result['evidence']['masks']['channels'])
                    artifacts.append({'path': str(target), 'sha256': file_sha(target), 'role': 'numeric prediction and input'})
                status_path = run / 'trigger-status' / (name + '.json')
                save_json(status_path, {'status': status, 'endpoint': endpoint, 'error': error,
                                       'seconds_before_evaluation': time.perf_counter() - trigger_start})
                artifacts.append({'path': str(status_path), 'sha256': file_sha(status_path), 'role': 'execution status'})
                seal_path = run / 'seals' / (name + '.json')
                save_json(seal_path, {'status': status, 'artifacts': artifacts, 'source_hashes': source_hashes,
                          'contract_sha256': file_sha(run / 'run-contract.json'), 'td': contract.get('td'),
                          'code': contract.get('source_files', []), 'config': {'local': local, 'rank': rank},
                          'relative_endpoint': endpoint, 'profile': PROFILE, 'before_evaluation': True,
                          'past_windows_relative': [endpoint - 360, endpoint - 60, endpoint],
                          'history_available': endpoint >= 360,
                          'seconds_before_evaluation': time.perf_counter() - trigger_start})
                if status == 'VALID':
                    root = report['metadata']['root_cause_service']
                    names = bundle['service_names']
                    root_index = names.index(root) if root in names else None
                    metrics = tie_metrics(predicted, root_index)
                else:
                    metrics = tie_metrics([], None, failed=True)
                diagnoses[endpoint] = {'endpoint': endpoint, 'status': status, 'metrics': metrics,
                                       'seal': str(seal_path), 'seal_sha256': file_sha(seal_path), 'error': error}
                if bundle is not None:
                    diagnoses[endpoint].update(quality=bundle['audit'],
                                               candidate_names_controller_only=bundle['service_names'])
            for detector in DETECTORS:
                item = items.get(detector)
                records = [diagnoses[int(t)] for t in item['triggers']] if item else []
                if item is None or (origin is None and not records):
                    composition = zero_composition('DETECTOR_UNAVAILABLE')
                elif origin is None:
                    composition = zero_composition('INPUT_FAILURE')
                else:
                    composition = first_trigger_composition(records, tau)
                outcomes[detector][case] = {'composition': composition, 'all_trigger_diagnoses': records,
                    'hook_first_post_summary': item.get('first_post_injection_trigger') if item else None,
                    'hook_first_post_summary_matches_recomputed':
                        item.get('first_post_injection_trigger') == composition['endpoint'] if item and tau is not None else None}
            resources[case] = time.perf_counter() - start
            save_json(run / 'case-results' / (handle + '.json'), {
                'case': case, 'diagnoses': diagnoses, 'detectors': {d: outcomes[d][case] for d in DETECTORS},
                'seconds': resources[case], 'source_hashes': source_hashes})
            print(f'Integrated {handle}: {len(endpoints)} unique triggers {resources[case]:.1f}s', flush=True)
            del raw
    summaries = {}
    for detector, cases in outcomes.items():
        summaries[detector] = {'planned_cases': len(DEV_IDS),
            'metrics': {m: float(np.mean([v['composition']['metrics'][m] for v in cases.values()])) for m in RANK_METRICS},
            'statuses': {s: sum(v['composition']['status'] == s for v in cases.values())
                         for s in {v['composition']['status'] for v in cases.values()}}}
    save_json(run / 'integrated-results.json', {'scope': 'development OOF detector-trigger composition; not primary C1',
              'summary': summaries, 'cases': outcomes, 'resources_seconds': resources,
              'rule': 'first post-injection trigger only; absent/insufficient/failure0; later triggers cannot rescue'})


if __name__ == '__main__':
    main()
