"""Trusted Task E control plane. Never import this module in a numeric worker.

It records scope and pre-run identity; it neither approves a method nor executes
data acquisition/models. All real-data entry points must validate DEV_IDS first.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

P = Path('D:/Project/flash-ticket-platform')
W = Path('D:/Project/flash-ticket-rca-research')
REVISION = 'afeacb11bcc94dadfd1c8f483ee4377b2b8b614e'
TD_SHA256 = '34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971'
METRIC_SUFFIXES = ('latency-90', 'latency-50', 'workload', 'diskio',
                  'latency', 'socket', 'error', 'load', 'cpu', 'mem')
DEV_CELLS = (
    ('ts-auth-service', 'cpu'), ('ts-auth-service', 'delay'),
    ('ts-order-service', 'disk'), ('ts-order-service', 'loss'),
    ('ts-route-service', 'mem'), ('ts-route-service', 'socket'),
    ('ts-train-service', 'cpu'), ('ts-train-service', 'delay'),
    ('ts-travel-service', 'disk'), ('ts-travel-service', 'loss'),
)
DEV_IDS = tuple(sorted(f're2tt_{root}_{fault}_{repeat}'
                      for root, fault in DEV_CELLS for repeat in (1, 2, 3)))
FOLDS = (
    (('ts-auth-service', 'cpu'), ('ts-order-service', 'disk')),
    (('ts-auth-service', 'delay'), ('ts-travel-service', 'loss')),
    (('ts-train-service', 'cpu'), ('ts-route-service', 'mem')),
    (('ts-train-service', 'delay'), ('ts-travel-service', 'disk')),
    (('ts-order-service', 'loss'), ('ts-route-service', 'socket')),
)


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            result.update(block)
    return result.hexdigest()


def require_dev(case_id: str) -> None:
    if case_id not in DEV_IDS:
        raise ValueError('Input is outside authorized TD12 development scope')


def opaque_handle(case_id: str) -> str:
    require_dev(case_id)
    return hashlib.sha256(('TD-v1|' + case_id).encode()).hexdigest()[:16]


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *args],
                                   encoding='utf-8').strip()


def write_json(path: Path, value: object, *, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def registry() -> dict:
    smoke = []
    for root, fault in DEV_CELLS:
        ids = [f're2tt_{root}_{fault}_{r}' for r in (1, 2, 3)]
        smoke.append(min(ids, key=opaque_handle))
    return {
        'schema': 'TD13-E-REGISTRY-v1', 'dataset_revision': REVISION,
        'td_sha256': TD_SHA256, 'development_ids': DEV_IDS,
        'development_cells': DEV_CELLS, 'folds': FOLDS,
        'smoke_rule': 'one minimum-issued-opaque-handle case per development cell',
        'smoke_ids': smoke,
        'local': {'floor': [0.001, 0.01], 'pool': ['max', 'q90'],
                  'fusion': ['max', 'availablemean'], 'temporal': 'q90'},
        'ppr': {'direction': ['reverse', 'undirected'], 'damping': [0.2, 0.5, 0.85]},
        'secondary_diffusion': {'direction': 'undirected', 'alpha': [0.2, 0.5, 0.85]},
        'R': {'chains': 256, 'proposals_per_edge': 200,
              'topology_only_sensitivity_budgets': [100, 200, 400]},
        'c5': {'arms': ['G', 'L', 'ALL'], 'modalities': ['MTL', 'MT'],
               'lambda': [0.1, 1, 10], 'q': [0.95, 0.975, 0.99],
               'neighbor_applicability': 'TD13 section7.0a scaler-only E; Vfit at F, cal-only isolates at H',
               'conflicting_span_policy': 'TD13 section7.0b event-time local trace mask; permanent key quarantine; no retroactive bins',
               'fit_bins': 24, 'cal_bins': 12, 'bin_seconds': 5,
               'min_fit_rows': 18, 'min_cal_rows': 9, 'lag': 1,
               'residual_floor': .01, 'streak': 3, 'refractory_seconds': 300},
        'sensitivity': {
            'mode': 'one-factor-at-a-time; diagnostic only; full list TD section8',
            'c1_bins': [5, 10, 20], 'c1_horizons': [180, 300, 420],
            'relative_floors': [0.0001, 0.001, 0.01],
            'c5_bin_prefix': [[5, 180], [10, 180], [5, 240]],
            'c5_lags': [1, 3], 'residual_floors': [0.001, 0.01, 0.1],
            'event_streaks': [1, 3, 5], 'refractory_seconds': [60, 300, 600],
            'rcd_bins': [3, 5, 7], 'rcd_seeds': [420, 421, 422]},
        'selection': 'NOT RUN; preserve TD section3 cascade and tie priorities',
        'final_evaluation': 'FORBIDDEN; no final IDs/materialized labels here',
    }


def begin_run(run_id: str, command: list[str], source_files: list[Path],
              *, stage: str, input_files: list[Path] | None = None,
              config: dict | None = None, exposure: str = 'SYNTHETIC ONLY',
              output_schema: str = 'fixture-report.json, stdout.log, stderr.log') -> Path:
    """Create immutable contract BEFORE the corresponding executable check."""
    if '/' in run_id or '\\' in run_id or not run_id:
        raise ValueError('run_id must be one directory component')
    protocol = P / 'docs/research-rca/task-d-method-and-experiment-specification.md'
    if sha256(protocol) != TD_SHA256:
        raise RuntimeError('TD baseline bytes changed; re-review before run')
    auth = P / 'docs/evidence/project-direction/2026-09-27-rca-c5-amendment-and-e-resume.md'
    if not auth.is_file():
        raise RuntimeError('Missing scoped human authorization source')
    run = W / 'results/task-e' / run_id
    run.mkdir(parents=True, exist_ok=False)
    identities = [{'path': str(f), 'sha256': sha256(f), 'bytes': f.stat().st_size}
                  for f in source_files]
    packages = {dist.metadata['Name']: dist.version
                for dist in importlib.metadata.distributions() if dist.metadata['Name']}
    contract = {
        'schema': 'TD13-E-RUN-v1', 'run_id': run_id, 'stage': stage,
        'created_before_execution_utc': datetime.now(timezone.utc).isoformat(),
        'authorization': {'source': str(auth), 'sha256': sha256(auth),
                          'decision_ids': [f'RCA-{number:03}' for number in range(49, 62)]},
        'td': {'path': str(protocol), 'sha256': TD_SHA256},
        'git': {root.name: {'head': git(root, 'rev-parse', 'HEAD'),
                           'branch': git(root, 'branch', '--show-current'),
                           'status': git(root, 'status', '--short')}
                for root in (P, W)},
        'source_files': identities, 'dataset_revision': REVISION,
        'inputs': [{'path': str(f), 'sha256': sha256(f)} for f in input_files or []],
        'command': command, 'python': sys.version, 'executable': sys.executable,
        'platform': platform.platform(), 'packages': packages,
        'hardware': {'cpu': 'Intel Core i5-1240P', 'physical_cores': 12,
                     'logical_processors': 16, 'ram_bytes': 16849293312},
        'seeds': {'fixtures': 'deterministic fixed arrays; PCG64 seeds explicit in code'},
        'config': config or {}, 'exposure': exposure,
        'output_schema': output_schema,
        'limitations': 'API/process isolation is not hostile-code OS filesystem sandboxing',
    }
    write_json(run / 'run-contract.json', contract, exclusive=True)
    write_json(run / 'source-manifest.json', {
        'schema': 'TD13-E-EXACT-SOURCE-v1', 'run_id': run_id,
        'files': [{**identity, 'utf8_snapshot': path.read_text(encoding='utf-8-sig')}
                  for path, identity in zip(source_files, identities)]}, exclusive=True)
    return run
