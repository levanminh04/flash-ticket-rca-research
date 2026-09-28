"""Trusted exact-development acquisition and pre-outcome actual-use audit."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.acquire import inspect_sources, acquire_development, development_metadata
from scripts.task_e.contract import DEV_IDS, opaque_handle
from scripts.task_e.loader import load_case, c1_bundle, c5_bundle
from scripts.task_e.input_adapters import rcd_bundle
from scripts.task_e.execution import save_json, save_npz, require_contract, failure, file_sha

C1_PROFILES = {'primary': (10, 300), 'bin5': (5, 300), 'bin20': (20, 300),
               'horizon180': (10, 180), 'horizon420': (10, 420)}
C5_PROFILES = {'primary': (5, 180, 24, 12), 'bin10': (10, 180, 12, 6),
               'prefix240': (5, 240, 32, 16)}


def read_acquired(receipt, row):
    index = {f['remote_path']: f for f in receipt['files']}
    paths, expected = {}, {}
    for modality in ('metrics', 'traces', 'logs'):
        obj = index.get(f"{row['case']}/{modality}.parquet")
        paths[modality] = obj['path'] if obj else None
        if obj:
            expected[modality] = obj
    return load_case(paths, row, expected_files=expected)


def main():
    run = Path(sys.argv[1])
    mode = sys.argv[2]
    require_contract(run, 'development')
    if mode == 'acquire':
        receipt = inspect_sources(W/'datasets/rcaeval/metadata/cases.parquet',
                                  W/'datasets/rcaeval/raw-samples', W/'datasets/rcaeval/task-e-development')
        save_json(run/'source-receipt.json', receipt)
        print(f"Pinned source: {receipt['planned_objects']} objects, {receipt['missing_objects']} missing, {receipt['missing_bytes']} bytes", flush=True)
        acquired = acquire_development(receipt, allow_download=True)
        save_json(run/'acquisition-receipt.json', acquired)
        print(f"Verified {acquired['verified_objects']} development objects", flush=True)
        return
    if mode != 'audit':
        raise ValueError('Unknown stage')
    receipt_path = Path(sys.argv[3])
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    rows = development_metadata(W/'datasets/rcaeval/metadata/cases.parquet')
    if set(row['case'] for row in rows) != set(DEV_IDS):
        raise ValueError('Not exact development30')
    summaries = []
    for row in rows:
        start = time.perf_counter()
        case, handle = row['case'], opaque_handle(row['case'])
        target = run/'intermediates'/handle
        report = {'case': case, 'handle': handle, 'metadata': row, 'profiles': {}}
        try:
            raw = read_acquired(receipt, row)
            report['physical'] = raw['audit']
            primary = None
            for profile, (width, horizon) in C1_PROFILES.items():
                try:
                    bundle = c1_bundle(raw, row['inject_time'], width, horizon)
                    if profile == 'primary':
                        primary = bundle
                    names = bundle['service_names']
                    report['profiles']['c1_'+profile] = {'status': 'MATERIALIZED',
                        'service_names': names, 'root_in_candidate': row['root_cause_service'] in names,
                        'audit': bundle['audit'], 'ref_shape': bundle['ref'].shape, 'query_shape': bundle['query'].shape}
                    save_npz(target/('c1_'+profile+'.npz'), **{k: bundle[k] for k in ('ref','query','adj','channel_types')})
                except Exception as exc:
                    report['profiles']['c1_'+profile] = failure(run, 'loader_c1_'+profile, case, exc)
            for profile, params in C5_PROFILES.items():
                try:
                    bundle = c5_bundle(raw, *params)
                    report['profiles']['c5_'+profile] = {'status': 'MATERIALIZED',
                        'service_names': bundle['service_names'], 's0': bundle['s0'],
                        'tau_relative': row['inject_time'] - bundle['s0'], 'audit': bundle['audit'],
                        'values_shape': bundle['values'].shape}
                    save_npz(target/('c5_'+profile+'.npz'), **{k: bundle[k] for k in
                             ('values','adj','channel_types','fit_service_mask','endpoints')})
                except Exception as exc:
                    report['profiles']['c5_'+profile] = failure(run, 'loader_c5_'+profile, case, exc)
            if primary is not None:
                rcd = rcd_bundle(raw, row['inject_time'], primary['service_names'])
                save_npz(target/'rcd.npz', values=rcd['values'])
                report['rcd'] = {k: v for k, v in rcd.items() if k != 'values'}
            report['status'] = 'AUDITED'
            del raw
        except Exception as exc:
            report['status'] = 'FAILURE'
            report['failure'] = failure(run, 'loader_case', case, exc)
        report['seconds'] = time.perf_counter() - start
        report['numeric_files'] = [{'path': str(p), 'sha256': file_sha(p), 'bytes': p.stat().st_size} for p in target.glob('*.npz')]
        save_json(run/'case-audits'/(handle+'.json'), report)
        summaries.append({'case': case, 'handle': handle, 'status': report['status'], 'seconds': report['seconds'],
                          'profile_statuses': {k:v.get('status','FAILURE') for k,v in report['profiles'].items()}})
        print(f"{len(summaries)}/30 {handle} {report['status']} {report['seconds']:.1f}s", flush=True)
    save_json(run/'loader-summary.json', {'planned': 30, 'cases': summaries,
              'source_receipt_sha256': file_sha(receipt_path), 'no_predictions': True})


if __name__ == '__main__':
    main()
