"""Engineering recovery: exact seed-level checkpoints, no method/grid changes."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.rcd_development import (CONFIGS, load_inputs, require_rcd_execution_contract,
    validate_response, evaluate_seeds, summarize_cases)
from scripts.task_e.execution import save_json, file_sha

DEADLINE = 1800


def identity(record, config, contract):
    return {'case': record['case'], 'handle': record['handle'], 'config': config,
            'numeric_sha256': record['numeric_sha256'], 'audit_sha256': record['audit_sha256'],
            'TD': contract['td']['sha256'], 'method': contract['config']['rcd_source_manifest_sha256']}


def validate_single(response, record, config, contract):
    values = record['values']
    if (response.get('schema') != 'TD13-RCD-NUMERIC-v1' or response.get('status') != 'COMPLETE'
            or response.get('shape') != list(values.shape)
            or response.get('input_numeric_sha256') != hashlib.sha256(values.astype('<f8').tobytes()).hexdigest()
            or len(response.get('results', [])) != 1):
        raise ValueError('Malformed single numeric result')
    item = response['results'][0]
    if any(item.get(k) != v or type(item.get(k)) is not int for k, v in config.items()):
        raise ValueError('Wrong seed/bin identity')
    fidelity = response.get('fidelity', {})
    if (fidelity.get('report_sha256') != contract['config']['rcd_qualification_report']['sha256']
            or fidelity.get('source_manifest_sha256') != contract['config']['rcd_source_manifest_sha256']
            or fidelity.get('worker_sha256') != file_sha(W/'scripts/task_e/rcd_numeric_worker.py')
            or fidelity.get('framework_init_executed') is not False
            or fidelity.get('method') != 'RCD-RCAEval-adapted-TD12'
            or item.get('method') != 'RCD-RCAEval-adapted-TD12'):
        raise ValueError('Single result qualification mismatch')
    seconds = item.get('wall_seconds')
    if type(seconds) not in (int, float) or not np.isfinite(seconds) or seconds < 0:
        raise ValueError('Invalid per-configuration cost')
    if item.get('status') == 'FAILURE':
        if item.get('ranks') is not None or item.get('metric_rank_indices') is not None or not item.get('reason'):
            raise ValueError('Invalid failure record')
    elif item.get('status') == 'SUCCESS':
        ranks = item.get('ranks');indices = item.get('metric_rank_indices')
        known = {'m'+str(i):i for i in range(values.shape[1])}
        if (type(ranks) is not list or any(type(k) is not str or not k for k in ranks)
                or len(ranks) != len(set(ranks)) or type(indices) is not list
                or any(type(i) is not int for i in indices)
                or indices != [known[k] for k in ranks if k in known]
                or item.get('unknown_metric_keys') != [k for k in ranks if k not in known]
                or item.get('reason') is not None or item.get('error') is not None):
            raise ValueError('Invalid numeric metric-rank record')
    else:raise ValueError('Unknown single result status')
    return item


def job(run, record, config, contract, reuse=None):
    directory = run / 'chunks' / record['handle'] / f"bins{config['bins']}-seed{config['seed']}"
    ident = identity(record, config, contract)
    seal_path = directory / 'seal.json'
    if seal_path.exists():
        seal = json.loads(seal_path.read_text(encoding='utf-8'))
        if seal['identity'] != ident or seal['status'] != 'COMPLETE':
            raise ValueError('Preserved failed/different chunk needs explicit engineering review')
        for artifact in seal['artifacts']:
            if file_sha(artifact['path']) != artifact['sha256']:
                raise ValueError('Completed chunk changed')
        return seal
    if directory.exists():
        raise ValueError('Incomplete chunk directory preserved; new attempt required')
    directory.mkdir(parents=True)
    save_json(directory / 'start.json', ident)
    start = time.perf_counter()
    if reuse:
        response = reuse['response']
        raw = directory / 'reused-result.json'
        save_json(raw, response)
        item = validate_single(response, record, config, contract)
        receipt = {'identity': ident, 'status': 'COMPLETE', 'result': item,
                   'fidelity': response['fidelity'], 'reused_from': reuse['source'],
                   'artifacts': [{'path': str(raw), 'sha256': file_sha(raw)}], 'new_prediction': False}
    else:
        raw, stderr = directory / 'raw-response.jsonl', directory / 'stderr.log'
        env = dict(os.environ)
        for key in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP'):env.pop(key, None)
        env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   NUMEXPR_NUM_THREADS='1', PYTHONHASHSEED='0', PYTHONUNBUFFERED='1')
        command = [str(W/'environments/task-e/rcd39/Scripts/python.exe'), '-B', '-u',
                   '-m', 'scripts.task_e.rcd_single_worker', str(run)]
        options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
        status, error, item, fidelity = 'COMPLETE', None, None, None
        with raw.open('xb') as out, stderr.open('xb') as err:
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err, cwd=W, env=env, **options)
            try:
                payload = json.dumps({'values': record['values'].tolist(), 'config': config}, allow_nan=False).encode()
                child.communicate(payload, timeout=DEADLINE)
            except subprocess.TimeoutExpired:
                # Windows virtualenv may launch an interpreter child; end the
                # exact process tree only, never every Python process.
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'], capture_output=True)
                else:child.kill()
                child.communicate();status='EXECUTION_TIMEOUT';error='Per-config1800s engineering deadline'
        if status == 'COMPLETE':
            try:
                if child.returncode != 0:raise ValueError('Worker process exit ' + str(child.returncode))
                response = json.loads(raw.read_text(encoding='utf-8'))
                if response.get('single_worker_sha256') != file_sha(W/'scripts/task_e/rcd_single_worker.py'):
                    raise ValueError('Single worker source changed')
                item = validate_single(response, record, config, contract)
                fidelity = response['fidelity']
            except Exception as exc:status='EXECUTION_FAILURE';error=type(exc).__name__+': '+str(exc)
        receipt = {'identity': ident, 'status': status, 'result': item, 'fidelity': fidelity,
                   'error': error, 'new_prediction': True,
                   'artifacts': [{'path': str(p), 'sha256': file_sha(p)} for p in (raw, stderr)]}
    receipt.update(seconds=time.perf_counter()-start, before_evaluation=True)
    save_json(seal_path, receipt)
    return receipt


def reusable_previous(previous, records, contract):
    """Reuse only complete raw nine-config replies with exact pinned input identity."""
    index = {}
    pins = {str(Path(r['path']).resolve()): r['sha256'] for r in contract['inputs']}
    if not previous:return index
    for record in records:
        seal_path = previous / 'seals' / (record['handle'] + '.json')
        if not seal_path.exists():continue
        if pins.get(str(seal_path.resolve())) != file_sha(seal_path):raise ValueError('Unpinned previous seal')
        seal = json.loads(seal_path.read_text(encoding='utf-8'))
        if seal.get('execution_failure'):continue
        if seal['input_sha256'] != record['numeric_sha256'] or seal['audit_sha256'] != record['audit_sha256']:
            raise ValueError('Prior successful input mismatch')
        raw = previous / 'raw-responses' / (record['handle'] + '.jsonl')
        artifact = next(a for a in seal['artifacts'] if Path(a['path']).resolve() == raw.resolve())
        if file_sha(raw) != artifact['sha256']:raise ValueError('Prior complete raw reply changed')
        response = json.loads(raw.read_text(encoding='utf-8'))
        validate_response(response, record['values'], contract)
        for item in response['results']:
            index[record['case'],item['seed'],item['bins']] = {
                'response': {**response, 'results': [item]},
                'source': {'path': str(raw), 'sha256': file_sha(raw), 'seal_sha256': file_sha(seal_path)}}
    return index


def reusable_timing(timing, records, contract):
    """Recovered completed configs from the unchanged-engine timing observer."""
    if not timing:return {}
    pins = {str(Path(r['path']).resolve()):r['sha256'] for r in contract['inputs']}
    paths = [timing/'run-contract.json', timing/'timing-plan.json', timing/'timing-stacks.log', timing/'timing-result.json']
    for p in paths:
        if pins.get(str(p.resolve())) != file_sha(p):raise ValueError('Unpinned/finalizing timing evidence')
    old = json.loads(paths[0].read_text(encoding='utf-8'))
    plan = json.loads(paths[1].read_text(encoding='utf-8'))
    record = next(r for r in records if r['case'] == plan['case'])
    if old['td']['sha256'] != contract['td']['sha256'] or plan['input_sha256'] != record['numeric_sha256']:
        raise ValueError('Timing TD/input mismatch')
    for entry in old['source_files']:
        p = Path(entry['path'])
        if p.name in ('rcd_timing_diagnostic.py','rcd_numeric_worker.py','rcd_runtime.py','comparators.py'):
            if file_sha(p) != entry['sha256']:raise ValueError('Timing engine/observer source drift')
    # Provenance values authenticated against the same pinned qualification;
    # no ranks or timing values are inferred: each is read from a completed line.
    fidelity = {'report_sha256':contract['config']['rcd_qualification_report']['sha256'],
        'source_manifest_sha256':contract['config']['rcd_source_manifest_sha256'],
        'worker_sha256':file_sha(W/'scripts/task_e/rcd_numeric_worker.py'),
        'framework_init_executed':False,'method':'RCD-RCAEval-adapted-TD12',
        'reconstruction':'qualified bootstrap in pinned timing observer; exact completed stdout-to-stderr JSON lines'}
    values=record['values'];known={'m'+str(i):i for i in range(values.shape[1])};index={}
    for line in paths[2].read_text(encoding='utf-8').splitlines():
        if not line.startswith('{'):continue
        try:row=json.loads(line)
        except json.JSONDecodeError:continue
        if row.get('event')!='CONFIG_COMPLETE':continue
        item=row['result'];item={**item,'wall_seconds':row['seconds'],
            'metric_rank_indices':None if item['ranks'] is None else [known[k] for k in item['ranks'] if k in known]}
        cfg={'seed':item['seed'],'bins':item['bins']}
        if cfg not in CONFIGS:raise ValueError('Unexpected timing configuration')
        response={'schema':'TD13-RCD-NUMERIC-v1','status':'COMPLETE','shape':list(values.shape),
            'input_numeric_sha256':hashlib.sha256(values.astype('<f8').tobytes()).hexdigest(),
            'results':[item],'fidelity':fidelity}
        validate_single(response,record,cfg,contract)
        key=(record['case'],cfg['seed'],cfg['bins'])
        if key in index:raise ValueError('Duplicate timing completion')
        index[key]={'response':response,'source':{'path':str(paths[2]),'sha256':file_sha(paths[2]),'event':'CONFIG_COMPLETE',
            'timing_plan_sha256':file_sha(paths[1]),'timing_contract_sha256':file_sha(paths[0])}}
    return index


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run',type=Path)
    parser.add_argument('--audit-root',required=True,type=Path)
    parser.add_argument('--previous-run',type=Path)
    parser.add_argument('--timing-run',type=Path)
    parser.add_argument('--workers',type=int,choices=(1,2,4,6),default=6)
    args=parser.parse_args();run=args.run.resolve();contract=require_rcd_execution_contract(run)
    sources={str(Path(p['path']).resolve()):p['sha256'] for p in contract['source_files']}
    for name in ('rcd_recovery.py','rcd_single_worker.py'):
        if sources.get(str(W/'scripts/task_e'/name))!=file_sha(W/'scripts/task_e'/name):raise ValueError('Recovery source drift')
    records=load_inputs(args.audit_root,contract)
    reuse=reusable_previous(args.previous_run,records,contract)
    timing=reusable_timing(args.timing_run,records,contract)
    if set(reuse)&set(timing):raise ValueError('Ambiguous duplicate complete sources')
    reuse.update(timing)
    plan={'planned_cases':30,'configs':CONFIGS,'workers':args.workers,'per_config_deadline_seconds':DEADLINE,
          'prior_complete_chunks':len(reuse),'method_changed':False,'prediction_recipe':'identical qualified rcd_run; per-config process/checkpoint',
          'all_seed_metrics_averaged':True,'no_performance_based_exclusion':True}
    if (run/'recovery-plan.json').exists():
        if json.loads((run/'recovery-plan.json').read_text(encoding='utf-8'))!=plan:raise ValueError('Resume plan mismatch')
    else:save_json(run/'recovery-plan.json',plan)
    completed={}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending={pool.submit(job,run,r,cfg,contract,reuse.get((r['case'],cfg['seed'],cfg['bins']))):
                 (r['case'],cfg['seed'],cfg['bins']) for r in records for cfg in CONFIGS}
        for future in as_completed(pending):
            key=pending[future];completed[key]=future.result()
            print(f'RCD chunks {len(completed)}/270 {key} {completed[key]["status"]}',flush=True)
    cases={};invalid=[]
    for record in records:
        entries=[completed[record['case'],cfg['seed'],cfg['bins']] for cfg in CONFIGS]
        results=[]
        for entry,cfg in zip(entries,CONFIGS):
            if entry['status']=='COMPLETE':results.append(entry['result'])
            else:
                invalid.append({'case':record['case'],'config':cfg,'status':entry['status']})
                results.append({**cfg,'status':'FAILURE','ranks':None,'reason':entry['status'],'error':entry.get('error'),'wall_seconds':None})
        evaluated=evaluate_seeds(results,record['audit'])
        item={'case':record['case'],'handle':record['handle'],
              'cell':[record['audit']['metadata']['root_cause_service'],record['audit']['metadata']['fault']],
              'chunk_statuses':[e['status'] for e in entries],**evaluated}
        cases[record['case']]=item
        save_json(run/'case-results'/(record['handle']+'.json'),item)
    save_json(run/'rcd-development-results.json',{'status':'INVALID_RUN_EXECUTION_REVIEW_REQUIRED' if invalid else 'COMPLETED_DEVELOPMENT_EXECUTION',
        'scope':'DEVELOPMENT30; contextual adapted RCD; no final evaluation',
        'primary_bins':5,'sensitivity_bins':[3,7],'seeds':[420,421,422],
        'reuse_chunks':sum(not e['new_prediction'] for e in completed.values()),'execution_failures':invalid,
        'cases':cases,**summarize_cases(cases)})
    return 1 if invalid else 0


if __name__=='__main__':raise SystemExit(main())
