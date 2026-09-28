"""Trusted pre-outcome TD13 topology diagnostics for the exact development30.

Only adjacency, an issued opaque handle and registered constants enter the
existing numeric perturbation method. No telemetry values or rankings are read.
Completed exclusive checkpoints can be verified and reused; partial/failed
checkpoints are preserved and require a new run for another attempt.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.contract import DEV_IDS, REVISION, TD_SHA256, opaque_handle
from scripts.task_e.execution import file_sha, plain, require_contract, save_json, save_npz
from scripts.task_e.ranking import perturb_graphs

REPRESENTATIONS = ('directed', 'undirected')
BUDGETS = (100, 200, 400)
CHAINS = 256
SCHEMA = 'TD13-DEVELOPMENT-TOPOLOGY-v1'


def _adjacency(value):
    a = np.asarray(value)
    if (a.ndim != 2 or a.shape[0] != a.shape[1] or a.dtype.kind not in 'biuf'
            or not np.isfinite(a).all() or not np.isin(a, (0, 1)).all()
            or np.diag(a).any()):
        raise ValueError('C1 cached adjacency must be finite, square, binary and loop-free')
    return a.astype(bool)


def _projection(adj, representation):
    if representation not in REPRESENTATIONS:
        raise ValueError('Unregistered topology representation')
    a = _adjacency(adj)
    return a if representation == 'directed' else a | a.T


def _graph_sha(adj):
    return hashlib.sha256(str(adj.shape).encode('ascii') + np.packbits(adj).tobytes()).hexdigest()


def _partition(adj):
    """Independent small-graph component check, including singleton isolates."""
    weak = adj | adj.T
    seen, components = set(), []
    for start in range(len(adj)):
        if start in seen:
            continue
        current, pending = set(), [start]
        while pending:
            node = pending.pop()
            if node in current:
                continue
            current.add(node)
            pending.extend(int(i) for i in np.flatnonzero(weak[node]) if int(i) not in current)
        seen.update(current)
        components.append(tuple(sorted(current)))
    return tuple(components)


def proposal_plan(adj):
    result = []
    for representation in REPRESENTATIONS:
        graph = _projection(adj, representation)
        edges = int(graph.sum()) if representation == 'directed' else int(np.triu(graph, 1).sum())
        for budget in BUDGETS:
            result.append({'representation': representation, 'budget': budget,
                           'edges': edges, 'chains': CHAINS,
                           'proposals_per_draw': budget * max(1, edges),
                           'total_proposals': CHAINS * budget * max(1, edges),
                           'uncompressed_graph_bytes': CHAINS * graph.size})
    return result


def verify_result(adj, handle, representation, budget, result):
    """Recompute degree/component/hash/seed receipts without using outcomes."""
    original = _projection(adj, representation)
    graphs = result['graphs']
    if (not isinstance(graphs, np.ndarray) or graphs.dtype != np.bool_
            or graphs.shape != (CHAINS, *original.shape)):
        raise ValueError('Every planned draw needs one boolean graph')
    receipts = result['per_draw']
    if len(receipts) != CHAINS or [r['draw'] for r in receipts] != list(range(CHAINS)):
        raise ValueError('Draw receipts must be complete and in issued order')
    edges = int(original.sum()) if representation == 'directed' else int(np.triu(original, 1).sum())
    proposals = budget * max(1, edges)
    components = _partition(original)
    isolates = ~(original.any(axis=0) | original.any(axis=1))
    for j, (graph, receipt) in enumerate(zip(graphs, receipts)):
        material = f'TD12|R|{handle}|{representation}|{j}'
        expected_seed = int.from_bytes(hashlib.sha256(material.encode()).digest()[:8], 'big')
        if (receipt['seed'] != expected_seed or receipt['proposals'] != proposals
                or receipt['hash'] != _graph_sha(graph) or receipt['invariants'] is not True):
            raise ValueError('Seed, budget, graph hash or invariant receipt differs')
        if (np.diag(graph).any() or not np.array_equal(graph.sum(0), original.sum(0))
                or not np.array_equal(graph.sum(1), original.sum(1))
                or _partition(graph) != components
                or not np.array_equal(~(graph.any(0) | graph.any(1)), isolates)
                or (representation == 'undirected' and not np.array_equal(graph, graph.T))):
            raise ValueError('Independent degree/component/isolate invariant failed')
        accepted = receipt['accepted']
        rejected = list(receipt['rejections'].values())
        if (type(accepted) is not int or accepted < 0
                or any(type(v) is not int or v < 0 for v in rejected)
                or accepted + sum(rejected) != proposals
                or receipt['acceptance_rate'] != accepted / proposals):
            raise ValueError('Proposal accounting differs from the fixed budget')
        overlap_count = int((graph & original).sum())
        if representation == 'undirected':
            overlap_count //= 2
        overlap = overlap_count / max(1, edges)
        changed = np.any(graph != original, axis=0) | np.any(graph != original, axis=1)
        changed_fraction = float(changed.mean()) if len(changed) else 0.
        if (receipt['retained_edge_fraction'] != overlap
                or receipt['changed_node_fraction'] != changed_fraction):
            raise ValueError('Overlap/change receipt differs from realized graph')
    distinct = len({r['hash'] for r in receipts})
    median_overlap = float(np.median([r['retained_edge_fraction'] for r in receipts]))
    summary = result['summary']
    expected = {'representation': representation, 'planned': CHAINS, 'completed': CHAINS,
                'failed': 0, 'budget': budget, 'edges': edges,
                'proposals_per_draw': proposals, 'distinct_final_graphs': distinct,
                'median_retained_edge_fraction': median_overlap,
                'mobile': distinct >= 32 and median_overlap <= .8, 'degenerate': distinct == 1}
    if any(summary.get(key) != value for key, value in expected.items()):
        raise ValueError('Topology summary differs from the 256 realized draws')
    return {**expected, 'total_proposals': CHAINS * proposals, 'isolates': int(isolates.sum()),
            'isolate_indices': np.flatnonzero(isolates).tolist(),
            'components': components, 'independent_invariants': True,
            'mean_acceptance_rate': float(np.mean([r['acceptance_rate'] for r in receipts]))}


def _verify_pinned(path, pins):
    path = Path(path).resolve()
    expected = pins.get(str(path))
    if expected is None or file_sha(path) != expected:
        raise ValueError(f'Input is absent from the pre-run contract or changed: {path}')
    return expected


def load_inputs(run, audit_root):
    """Use only provenance/adjacency fields from trusted case audit receipts."""
    contract = require_contract(run, 'topology')
    if contract.get('td', {}).get('sha256') != TD_SHA256 or contract.get('dataset_revision') != REVISION:
        raise ValueError('Wrong TD or dataset revision in topology contract')
    pins = {str(Path(item['path']).resolve()): item['sha256'] for item in contract['inputs']}
    audit_root = Path(audit_root).resolve()
    _verify_pinned(audit_root / 'run-contract.json', pins)
    _verify_pinned(audit_root / 'loader-summary.json', pins)
    audit_contract = require_contract(audit_root, 'development')
    if audit_contract.get('td', {}).get('sha256') != TD_SHA256:
        raise ValueError('Cached graphs use a different TD version')
    planned_handles = tuple(opaque_handle(case) for case in DEV_IDS)
    records = []
    for handle in planned_handles:
        receipt_path = audit_root / 'case-audits' / (handle + '.json')
        audit_sha = _verify_pinned(receipt_path, pins)
        report = json.loads(receipt_path.read_text(encoding='utf-8'))
        if report.get('handle') != handle:
            raise ValueError('Case receipt does not match the issued handle')
        source = {'case_audit_path': str(receipt_path), 'case_audit_sha256': audit_sha,
                  'audit_contract_sha256': file_sha(audit_root / 'run-contract.json')}
        profile = report.get('profiles', {}).get('c1_primary', {})
        if profile.get('status') != 'MATERIALIZED':
            records.append({'handle': handle, 'source': source, 'adj': None,
                            'input_failure': 'C1_PRIMARY_NOT_MATERIALIZED'})
            continue
        numeric_path = (audit_root / 'intermediates' / handle / 'c1_primary.npz').resolve()
        entries = [item for item in report['numeric_files']
                   if Path(item['path']).resolve() == numeric_path]
        if len(entries) != 1 or file_sha(numeric_path) != entries[0]['sha256']:
            raise ValueError('C1 numeric artifact is absent, ambiguous or hash-mismatched')
        if _verify_pinned(numeric_path, pins) != entries[0]['sha256']:
            raise ValueError('Pre-run cache identity differs from the case receipt')
        with np.load(numeric_path, allow_pickle=False) as cache:
            adjacency = _adjacency(cache['adj'])
        graph_audit = profile.get('audit', {}).get('graph', {})
        if hashlib.sha256(adjacency.tobytes()).hexdigest() != graph_audit.get('adjacency_sha256'):
            raise ValueError('Observed adjacency differs from its loader graph receipt')
        source.update(numeric_path=str(numeric_path), numeric_sha256=entries[0]['sha256'],
                      observed_adjacency_sha256=_graph_sha(adjacency))
        records.append({'handle': handle, 'source': source, 'adj': adjacency, 'input_failure': None})
    return records


def run_job(run, record, representation, budget):
    """One exclusive handle/representation/budget checkpoint; never retune/retry."""
    if record['handle'] not in {opaque_handle(case) for case in DEV_IDS}:
        raise ValueError('Unissued development handle')
    if representation not in REPRESENTATIONS or budget not in BUDGETS:
        raise ValueError('Unregistered topology job')
    run = Path(run)
    require_contract(run, 'topology')
    directory = run / 'topology' / record['handle'] / representation / str(budget)
    identity = {'schema': SCHEMA, 'handle': record['handle'], 'representation': representation,
                'budget': budget, 'chains': CHAINS, 'source': record['source'],
                'run_contract_sha256': file_sha(run / 'run-contract.json')}
    if directory.exists():
        saved = json.loads((directory / 'receipt.json').read_text(encoding='utf-8'))
        if saved.get('identity') != identity or saved.get('status') != 'COMPLETE':
            raise FileExistsError('Preserved incomplete/failed/different checkpoint; use a new run')
        graph_path = directory / 'graphs.npz'
        if file_sha(graph_path) != saved['graphs_sha256']:
            raise ValueError('Completed checkpoint graph file changed')
        with np.load(graph_path, allow_pickle=False) as archive:
            graphs = archive['graphs']
        verify_result(record['adj'], record['handle'], representation, budget,
                      {'graphs': graphs, 'per_draw': saved['per_draw'], 'summary': saved['method_summary']})
        return {**saved, 'reused_verified_checkpoint': True}
    directory.mkdir(parents=True, exist_ok=False)
    save_json(directory / 'start.json', identity)
    started = time.perf_counter()
    try:
        if record['input_failure']:
            result = {'identity': identity, 'status': 'INPUT_FAILURE',
                      'error': record['input_failure'], 'planned_draws': CHAINS,
                      'completed_draws': 0, 'no_predictions': True}
        else:
            generated = perturb_graphs(record['adj'], record['handle'], representation,
                                       count=CHAINS, budget=budget)
            checked = verify_result(record['adj'], record['handle'], representation, budget, generated)
            graph_path = directory / 'graphs.npz'
            save_npz(graph_path, graphs=generated['graphs'])
            result = {'identity': identity, 'status': 'COMPLETE', 'summary': checked,
                      'method_summary': plain(generated['summary']), 'per_draw': generated['per_draw'],
                      'graphs_sha256': file_sha(graph_path), 'planned_draws': CHAINS,
                      'completed_draws': CHAINS, 'no_predictions': True}
    except Exception as exc:
        result = {'identity': identity, 'status': 'FAILURE', 'error_type': type(exc).__name__,
                  'error': str(exc), 'planned_draws': CHAINS, 'completed_draws': 0,
                  'no_predictions': True}
    result['seconds'] = time.perf_counter() - started
    save_json(directory / 'receipt.json', result)
    return result


def run_case(run, record):
    return [run_job(run, record, representation, budget)
            for representation in REPRESENTATIONS for budget in BUDGETS]


def run_campaign(run, audit_root, workers=1):
    if type(workers) is not int or workers not in (1, 2):
        raise ValueError('Use one or two bounded independent-case processes')
    run = Path(run)
    records = load_inputs(run, audit_root)
    plan = {'schema': SCHEMA, 'planned_cases': len(records), 'planned_jobs': len(records) * 6,
            'planned_draws': len(records) * 6 * CHAINS, 'workers': workers,
            'cases': [{'handle': r['handle'], 'input_failure': r['input_failure'],
                       'jobs': proposal_plan(r['adj']) if r['adj'] is not None else []} for r in records],
            'no_predictions': True, 'timing': 'No empirical estimate before execution; counted proposals only'}
    plan['total_proposals_on_available_inputs'] = sum(j['total_proposals'] for r in plan['cases'] for j in r['jobs'])
    plan_path = run / 'topology-plan.json'
    if plan_path.exists():
        if json.loads(plan_path.read_text(encoding='utf-8')) != plan:
            raise ValueError('Existing exclusive topology plan differs')
    else:
        save_json(plan_path, plan)
    print(f"Topology only: {len(records)} cases, {plan['planned_jobs']} jobs, "
          f"{plan['total_proposals_on_available_inputs']} fixed proposals", flush=True)
    results = []
    if workers == 1:
        for record in records:
            results.extend(run_case(run, record))
            print(f"{len(results)//6}/30 topology cases checkpointed", flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            pending = [pool.submit(run_case, run, record) for record in records]
            for future in as_completed(pending):
                results.extend(future.result())
                print(f"{len(results)//6}/30 topology cases checkpointed", flush=True)
    results.sort(key=lambda r: (r['identity']['handle'], r['identity']['representation'], r['identity']['budget']))
    groups = []
    for representation in REPRESENTATIONS:
        for budget in BUDGETS:
            selected = [r for r in results if r['identity']['representation'] == representation
                        and r['identity']['budget'] == budget]
            complete = [r for r in selected if r['status'] == 'COMPLETE']
            mobile = sum(r['summary']['mobile'] for r in complete)
            groups.append({'representation': representation, 'budget': budget,
                           'planned_cases': 30, 'completed_cases': len(complete),
                           'failed_or_unavailable_cases': 30 - len(complete),
                           'mobile_cases': mobile, 'mobile_fraction_planned': mobile / 30,
                           'descriptive_80pct_planned_gate': mobile >= 24,
                           'not_final_stratified_gate': True})
    summary = {'schema': SCHEMA, 'planned_cases': 30, 'planned_jobs': 180,
               'planned_draws': 180 * CHAINS, 'groups': groups,
               'jobs': [{'handle': r['identity']['handle'], 'representation': r['identity']['representation'],
                         'budget': r['identity']['budget'], 'status': r['status'],
                         'completed_draws': r['completed_draws'], 'seconds': r['seconds']} for r in results],
               'all_jobs_complete': all(r['status'] == 'COMPLETE' for r in results),
               'no_predictions': True, 'no_root_stratum_evaluation': True,
               'interpretation': 'Development topology diagnostics only; not mixing proof, outcomes or final mobility qualification'}
    summary_path = run / 'topology-summary.json'
    if summary_path.exists():
        if json.loads(summary_path.read_text(encoding='utf-8')) != summary:
            raise ValueError('Existing exclusive topology summary differs')
    else:
        save_json(summary_path, summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run')
    parser.add_argument('--audit-root', required=True)
    parser.add_argument('--workers', type=int, default=1, choices=(1, 2))
    args = parser.parse_args()
    summary = run_campaign(args.run, args.audit_root, args.workers)
    raise SystemExit(0 if summary['all_jobs_complete'] else 1)


if __name__ == '__main__':
    main()
