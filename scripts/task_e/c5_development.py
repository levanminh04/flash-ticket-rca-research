"""Trusted, sealed development-only C5 campaign controller for TD-v1.3.

No raw telemetry acquisition happens here. Verified audit NPZ files supply
numeric arrays; the separate NumericWorker receives exact warmup then one bin.
Only after every case prediction artifact is sealed does trusted calibration
open its relative injection boundary for lambda/q selection or event metrics.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.boundary import NumericWorker
from scripts.task_e.calibration import (ARMS, LAMBDA_PRIORITY, EvaluationError,
    calibrate_threshold, event_diagnostics, fixed_eligible_forecast_loss, grouped_folds,
    normal_score_distribution, planned_regime_summary, regime_metrics, select_q,
    select_registered, weighted_cdf_inverse)
from scripts.task_e.contract import DEV_IDS, REVISION, TD_SHA256, opaque_handle, registry
from scripts.task_e.detection import create_event_state, event_step
from scripts.task_e.execution import failure, file_sha, plain, require_contract, save_json, save_npz
from scripts.task_e.worker import encode_message

SCHEMA = 'TD13-C5-DEVELOPMENT-v1'
PROFILES = {'primary': (5, 24, 12), 'bin10': (10, 12, 6), 'prefix240': (5, 32, 16)}
LAMBDAS = (.1, 1., 10.)
MODALITIES = ('MTL', 'MT')
CORE_SOURCES = ('c5_development.py', 'boundary.py', 'worker.py', 'detection.py',
                'ranking.py', 'calibration.py', 'contract.py', 'execution.py')


def config_id(config):
    return f"{config['arm']}-{config['modalities']}-lambda{config['lambda']:g}"


def registered_configs(floor, *, profile='primary', selected_lambda=None, **change):
    width, fit, cal = PROFILES[profile]
    if floor not in (.001, .01, .0001):
        raise ValueError('Unregistered relative floor')
    penalties = LAMBDAS if selected_lambda is None else (float(selected_lambda),)
    if any(penalty not in LAMBDAS for penalty in penalties):
        raise ValueError('Unregistered lambda')
    if set(change) - {'lag', 'residual_floor'}:
        raise ValueError('Unregistered configuration override')
    if change.get('lag', 1) not in (1, 3) or change.get('residual_floor', .01) not in (.001, .01, .1):
        raise ValueError('Unregistered lag/residual floor')
    return [{'arm': arm, 'modalities': modality, 'lambda': penalty, 'floor': floor,
             'bin_seconds': width, 'fit_bins': fit, 'cal_bins': cal, **change}
            for arm in ARMS for modality in MODALITIES for penalty in penalties]


def sensitivity_registry(floor, selected_lambda):
    """OFAT only; all alternatives fixed before any sensitivity output."""
    variants = []
    for profile in ('bin10', 'prefix240'):
        variants.append({'id': profile, 'profile': profile, 'dimension': 'bin_prefix',
                         'configs': registered_configs(floor, profile=profile, selected_lambda=selected_lambda)})
    variants.append({'id': 'lag3', 'profile': 'primary', 'dimension': 'lag',
                     'configs': registered_configs(floor, selected_lambda=selected_lambda, lag=3)})
    for value in (.001, .1):
        variants.append({'id': f'residual-floor-{value:g}', 'profile': 'primary',
                         'dimension': 'residual_floor', 'configs': registered_configs(
                             floor, selected_lambda=selected_lambda, residual_floor=value)})
    for value in (.0001, .001, .01):
        if value != floor:
            variants.append({'id': f'relative-floor-{value:g}', 'profile': 'primary',
                             'dimension': 'relative_floor',
                             'configs': registered_configs(value, selected_lambda=selected_lambda)})
    return variants


def _verify(path, pins):
    path = Path(path).resolve()
    expected = pins.get(str(path))
    if expected is None or file_sha(path) != expected:
        raise ValueError(f'Unpinned or changed pre-run input: {path}')
    return expected


def admitted_contract(run, mode):
    contract = require_contract(run, 'c5')
    if contract.get('td', {}).get('sha256') != TD_SHA256 or contract.get('dataset_revision') != REVISION:
        raise ValueError('Wrong TD or dataset revision')
    if mode not in contract['stage']:
        raise ValueError('C5 CLI mode differs from the pre-recorded stage')
    sources = {str(Path(item['path']).resolve()): item['sha256'] for item in contract['source_files']}
    for name in CORE_SOURCES:
        _verify(W / 'scripts/task_e' / name, sources)
    return contract, {str(Path(item['path']).resolve()): item['sha256'] for item in contract['inputs']}


def read_roster(audit_root, pins, mode):
    root = Path(audit_root).resolve()
    _verify(root / 'run-contract.json', pins)
    _verify(root / 'loader-summary.json', pins)
    audit_contract = require_contract(root, 'development')
    if (audit_contract.get('td', {}).get('sha256') != TD_SHA256
            or audit_contract.get('dataset_revision') != REVISION):
        raise ValueError('Cached numeric inputs have another TD version')
    summary = json.loads((root / 'loader-summary.json').read_text(encoding='utf-8'))
    if (summary.get('planned') != 30 or len(summary['cases']) != 30
            or {r['case'] for r in summary['cases']} != set(DEV_IDS)):
        raise ValueError('Loader audit is not complete exact development30')
    if mode not in ('smoke', 'full', 'sensitivity'):
        raise ValueError('Unknown development mode')
    planned = tuple(registry()['smoke_ids']) if mode == 'smoke' else tuple(DEV_IDS)
    reports = {}
    for case in planned:
        handle = opaque_handle(case)
        path = root / 'case-audits' / (handle + '.json')
        audit_sha = _verify(path, pins)
        report = json.loads(path.read_text(encoding='utf-8'))
        if report.get('case') != case or report.get('handle') != handle:
            raise ValueError('Case receipt does not match its issued development handle')
        report['_case_audit_sha256'] = audit_sha
        reports[case] = report
    return planned, reports


def load_numeric(audit_root, report, profile, pins):
    entry = report.get('profiles', {}).get('c5_' + profile, {})
    if entry.get('status') != 'MATERIALIZED':
        return None, {'status': 'INPUT_UNAVAILABLE', 'reason': entry}
    path = (Path(audit_root) / 'intermediates' / report['handle'] / ('c5_' + profile + '.npz')).resolve()
    matching = [item for item in report['numeric_files'] if Path(item['path']).resolve() == path]
    if len(matching) != 1 or _verify(path, pins) != matching[0]['sha256']:
        raise ValueError('Numeric cache identity differs from its audited source')
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != {'values', 'adj', 'channel_types', 'fit_service_mask', 'endpoints'}:
            raise ValueError('Unexpected fields in trusted numeric C5 cache')
        arrays = {name: archive[name].copy() for name in archive.files}
    width, fit, cal = PROFILES[profile]
    values = arrays['values']
    if (values.ndim != 3 or len(values) < fit + cal or values.dtype.kind not in 'fiu'
            or np.isinf(values).any() or arrays['fit_service_mask'].dtype != np.bool_):
        raise ValueError('Invalid C5 numeric values or fit membership')
    _, nodes, channels = values.shape
    if (arrays['adj'].shape != (nodes, nodes) or arrays['adj'].dtype != np.bool_
            or arrays['channel_types'].shape != (channels,)
            or arrays['channel_types'].dtype.kind not in 'iu'
            or not np.isin(arrays['channel_types'], (0, 1, 2)).all()
            or arrays['fit_service_mask'].shape != (nodes,)
            or np.diag(arrays['adj']).any()):
        raise ValueError('Invalid C5 graph, types, or service axes')
    expected_endpoints = np.arange(1, len(values) + 1, dtype=np.int64) * width
    if not np.array_equal(arrays['endpoints'], expected_endpoints):
        raise ValueError('C5 cache lacks the complete declared relative bin grid')
    graph_sha = hashlib.sha256(arrays['adj'].tobytes()).hexdigest()
    if graph_sha != entry['audit']['graph']['adjacency_sha256']:
        raise ValueError('Frozen graph differs from loader receipt')
    return arrays, {'status': 'MATERIALIZED', 'numeric_path': str(path), 'numeric_sha256': matching[0]['sha256'],
                    'case_audit_sha256': report['_case_audit_sha256'], 'profile': profile,
                    'cutoff': int(expected_endpoints[-1]), 'graph_sha256': graph_sha}


def assert_common_input_ids(models, configs):
    """Compare frozen input IDs before any scored prediction is emitted."""
    if len(models) != len(configs):
        raise ValueError('Worker returned an incomplete configuration roster')
    for modality in MODALITIES:
        indices = [i for i, cfg in enumerate(configs) if cfg['modalities'] == modality]
        reference = models[indices[0]]
        for index in indices[1:]:
            for field in ('E', 'model_mask', 'fit_target_mask', 'calibration_target_mask', 'centers', 'scales'):
                if not np.array_equal(reference[field], models[index][field], equal_nan=True):
                    raise ValueError(f'Input eligibility differs across arm/lambda: {field}')
    # MT and MTL share all M/T eligibility and scaling; no log veto of M/T.
    reference = models[0]
    shared = reference['channel_types'] != 2
    for model in models[1:]:
        for field in ('E', 'model_mask', 'centers', 'scales'):
            if not np.array_equal(reference[field][:, shared], model[field][:, shared], equal_nan=True):
                raise ValueError(f'MT/MTL common modality input differs: {field}')
    paired = {(cfg['arm'], cfg['lambda'], cfg['modalities']): model
              for cfg, model in zip(configs, models)}
    for cfg in configs:
        if cfg['modalities'] != 'MTL':
            continue
        mtl = paired[cfg['arm'], cfg['lambda'], 'MTL']
        mt = paired[cfg['arm'], cfg['lambda'], 'MT']
        for field in ('coefficients', 'intercepts', 'residual_centers', 'residual_scales'):
            if not np.array_equal(mtl[field][:, shared], mt[field][:, shared], equal_nan=True):
                raise ValueError(f'MT/MTL common model differs: {field}')
        for field in ('fit_target_mask', 'calibration_target_mask', 'calibration_errors', 'calibration_predictions'):
            if not np.array_equal(mtl[field][:, :, shared], mt[field][:, :, shared], equal_nan=True):
                raise ValueError(f'MT/MTL common model input/residual differs: {field}')


def assert_common_score_ids(results, configs, channel_types):
    if len(results) != len(configs):
        raise ValueError('Worker returned an incomplete scored configuration roster')
    for modality in MODALITIES:
        indices = [i for i, cfg in enumerate(configs) if cfg['modalities'] == modality]
        reference = results[indices[0]]
        for index in indices[1:]:
            for field in ('target_mask', 'z', 'tv_score', 'tv_channels', 'tv_edge_counts', 'local_magnitude'):
                left, right = reference[field], results[index][field]
                equal = left is right if left is None or right is None else np.array_equal(left, right, equal_nan=True)
                if not equal:
                    raise ValueError(f'Scored input/spatial evidence differs across arm/lambda: {field}')
    shared = np.asarray(channel_types) != 2
    paired = {(cfg['arm'], cfg['lambda'], cfg['modalities']): result
              for cfg, result in zip(configs, results)}
    for cfg in configs:
        if cfg['modalities'] == 'MTL':
            mtl, mt = (paired[cfg['arm'], cfg['lambda'], modality] for modality in MODALITIES)
            for field in ('target_mask', 'z', 'predictions', 'errors', 'residuals', 'tv_channels'):
                if not np.array_equal(mtl[field][:, shared] if field != 'tv_channels' else mtl[field][shared],
                                      mt[field][:, shared] if field != 'tv_channels' else mt[field][shared], equal_nan=True):
                    # A log-only TV overflow can invalidate the entire MTL TV
                    # spatial result while leaving every M/T forecast intact.
                    if field == 'tv_channels' and (mtl.get('tv_failure') or mt.get('tv_failure')):
                        continue
                    raise ValueError(f'MT/MTL common scored component differs: {field}')


def _capacity(models):
    result = []
    for model in models:
        diag = model['diagnostics']
        ridge = [item for row in diag['ridge'] for item in row if item is not None]
        result.append({'model_count': int(model['model_mask'].sum()), 'applicable_channels': int(model['E'].sum()),
            'fit_models': int(model['fit_model_mask'].sum()), 'singleton_scales': int(diag['singleton_scale'].sum()),
            'constant_scales': int(diag['constant_scale'].sum()), 'floor_scales': int(diag['scale_floor_used'].sum()),
            'residual_floor_scales': int(diag['residual_floor_used'].sum()),
            'residual_scales_min': float(np.nanmin(model['residual_scales'])) if model['model_mask'].any() else None,
            'residual_scales_max': float(np.nanmax(model['residual_scales'])) if model['model_mask'].any() else None,
            'effective_df_mean': float(np.mean([item['effective_ridge_df'] for item in ridge])) if ridge else None,
            'active_columns_mean': float(np.mean([item['active_columns'] for item in ridge])) if ridge else None,
            'centered_design_rank_mean': float(np.mean([item['centered_design_rank'] for item in ridge])) if ridge else None,
            'degrees': {key: {'min': int(value.min()) if value.size else 0, 'max': int(value.max()) if value.size else 0,
                             'empty_targets': int((value == 0).sum())} for key, value in model['degrees'].items()}})
    return result


def run_case(run, variant, case, report, arrays, source, configs, timeout):
    directory = Path(run) / 'predictions' / variant / report['handle']
    identity = {'schema': SCHEMA, 'variant': variant, 'handle': report['handle'],
                'source': source, 'configs': configs, 'contract_sha256': file_sha(Path(run) / 'run-contract.json')}
    if directory.exists():
        receipt = json.loads((directory / 'seal.json').read_text(encoding='utf-8'))
        if receipt['identity'] != identity or receipt['status'] not in ('COMPLETE', 'INPUT_UNAVAILABLE'):
            raise FileExistsError('Preserved partial/failed checkpoint needs a new run')
        for artifact in receipt['artifacts']:
            if file_sha(directory / artifact['file']) != artifact['sha256']:
                raise ValueError('Sealed C5 artifact changed')
        return {**receipt, 'reused_verified_checkpoint': True}
    directory.mkdir(parents=True, exist_ok=False)
    save_json(directory / 'start.json', identity)
    started = time.perf_counter()
    receipt = {'identity': identity, 'artifacts': [], 'failed_configs': [], 'tv_failures': [],
               'worker_input_contract': 'exact warmup then one bin; no labels/paths/epochs'}
    if arrays is None:
        receipt.update(status='INPUT_UNAVAILABLE', seconds=time.perf_counter() - started,
                       planned_failure=True, reason=source)
        save_json(directory / 'seal.json', receipt)
        return receipt
    width, fit, cal = configs[0]['bin_seconds'], configs[0]['fit_bins'], configs[0]['cal_bins']
    warmup = fit + cal
    ticks, nodes, channels = arrays['values'].shape
    remaining, count = ticks - warmup, len(configs)
    output = {key: np.full((count, remaining, nodes, channels), np.nan) for key in
              ('predictions', 'errors', 'residuals', 'z')}
    output['target_mask'] = np.zeros((count, remaining, nodes, channels), dtype=bool)
    output.update({key: np.full((count, remaining), np.nan) for key in ('scores', 'tv_scores', 'local_magnitude')})
    output['tv_channels'] = np.full((count, remaining, channels), np.nan)
    output['tv_edge_counts'] = np.zeros((count, remaining, channels), dtype=np.int64)
    output['scored_channels'] = np.zeros((count, remaining), dtype=np.int64)
    output['endpoints'] = arrays['endpoints'][warmup:].copy()
    fit_seconds = score_seconds = 0.
    completed_calls = 0
    # Exact controller-side inputs are retained; only the prefix and one next
    # bin at a time cross the worker API. No label or absolute clock is saved.
    save_npz(directory / 'numeric-input.npz', **arrays)
    try:
        with NumericWorker(timeout_seconds=timeout) as worker:
            receipt['worker_handshake'] = worker.ping()
            clock = time.perf_counter()
            fitted = worker.fit_c5(arrays['values'][:warmup], arrays['adj'], arrays['channel_types'],
                                   arrays['fit_service_mask'], configs)
            fit_seconds = time.perf_counter() - clock
            models = fitted['models']
            assert_common_input_ids(models, configs)
            with (directory / 'frozen-models.npz').open('xb') as stream:
                stream.write(encode_message(fitted))
            receipt['capacity'] = _capacity(models)
            for absolute_bin in range(warmup, ticks):
                clock = time.perf_counter()
                results = worker.score_c5(arrays['values'][absolute_bin], absolute_bin)['results']
                score_seconds += time.perf_counter() - clock
                relative = absolute_bin - warmup
                assert_common_score_ids(results, configs, arrays['channel_types'])
                for index, result in enumerate(results):
                    if result['endpoint'] != output['endpoints'][relative]:
                        raise ValueError('Worker chronological endpoint differs from admitted grid')
                    for key in ('predictions', 'errors', 'residuals', 'z', 'target_mask', 'tv_channels', 'scored_channels'):
                        output[key][index, relative] = result[key]
                    output['tv_edge_counts'][index, relative] = (-1 if result['tv_edge_counts'] is None
                                                                else result['tv_edge_counts'])
                    for source_key, target in (('score', 'scores'), ('tv_score', 'tv_scores'), ('local_magnitude', 'local_magnitude')):
                        output[target][index, relative] = result[source_key]
                    if result.get('tv_failure'):
                        receipt['tv_failures'].append({'config': index, 'bin': absolute_bin,
                                                       'endpoint': result['endpoint'], 'error': result['tv_failure']})
                completed_calls += 1
        receipt['status'] = 'COMPLETE'
    except Exception as exc:
        receipt.update(status='METHOD_FAILURE', error=failure(run, 'c5_' + variant, case, exc),
                       failed_configs=list(range(count)))
    # Persist partial arrays too. A failure never deletes or replaces an attempt.
    save_npz(directory / 'predictions.npz', **output)
    for path in (directory / 'predictions.npz', directory / 'frozen-models.npz', directory / 'numeric-input.npz'):
        if path.exists():
            receipt['artifacts'].append({'file': path.name, 'sha256': file_sha(path), 'bytes': path.stat().st_size})
    receipt.update(fit_seconds=fit_seconds, score_seconds=score_seconds,
                   seconds=time.perf_counter() - started, completed_score_bins=int(np.isfinite(output['scores']).any(axis=0).sum()),
                   planned_score_bins=remaining, prediction_sealed_before_evaluator=True)
    receipt['completed_worker_calls'] = completed_calls
    save_json(directory / 'seal.json', receipt)
    return receipt


def _load_sealed(run, variant, report):
    directory = Path(run) / 'predictions' / variant / report['handle']
    receipt = json.loads((directory / 'seal.json').read_text(encoding='utf-8'))
    if (receipt['identity']['variant'] != variant or receipt['identity']['handle'] != report['handle']
            or receipt['identity']['contract_sha256'] != file_sha(Path(run) / 'run-contract.json')):
        raise ValueError('Sealed prediction identity differs from its run/roster')
    for artifact in receipt['artifacts']:
        if file_sha(directory / artifact['file']) != artifact['sha256']:
            raise ValueError('Prediction/evidence changed after sealing')
    if receipt['status'] == 'INPUT_UNAVAILABLE':
        return receipt, None
    with np.load(directory / 'predictions.npz', allow_pickle=False) as saved:
        values = {name: saved[name].copy() for name in saved.files}
    return receipt, values


def seal_campaign_predictions(run, variants, planned, reports):
    """Commit every planned result before any evaluation starts."""
    entries = []
    for variant in variants:
        for case in planned:
            path = Path(run) / 'predictions' / variant['id'] / reports[case]['handle'] / 'seal.json'
            receipt = json.loads(path.read_text(encoding='utf-8'))
            entries.append({'variant': variant['id'], 'handle': reports[case]['handle'],
                            'seal_sha256': file_sha(path), 'status': receipt['status']})
    seal = {'schema': SCHEMA, 'contract_sha256': file_sha(Path(run) / 'run-contract.json'),
            'before_evaluation': True, 'entries': entries}
    save_json(Path(run) / 'predictions-seal.json', seal)
    return file_sha(Path(run) / 'predictions-seal.json')


def verify_campaign_seal(run, variant, planned, reports):
    manifest = json.loads((Path(run) / 'predictions-seal.json').read_text(encoding='utf-8'))
    if (manifest.get('before_evaluation') is not True
            or manifest['contract_sha256'] != file_sha(Path(run) / 'run-contract.json')):
        raise ValueError('Missing pre-evaluation campaign identity')
    entries = [entry for entry in manifest['entries'] if entry['variant'] == variant]
    if (len(entries) != len(planned)
            or {entry['handle'] for entry in entries} != {reports[case]['handle'] for case in planned}):
        raise ValueError('Sealed campaign omits or duplicates planned predictions')
    for entry in entries:
        path = Path(run) / 'predictions' / variant / entry['handle'] / 'seal.json'
        if file_sha(path) != entry['seal_sha256']:
            raise ValueError('Case seal changed after campaign predictions were sealed')


def _boundaries(report, profile, output, config):
    width = config['bin_seconds']
    warmup = width * (config['fit_bins'] + config['cal_bins'])
    detail = report['profiles'].get('c5_' + profile, {})
    if output is not None:
        ends = output['endpoints'].copy()
    else:
        duration = int(report['metadata']['time_end'] - report['metadata']['time_start'])
        ends = np.arange(warmup + width, duration + 1, width, dtype=np.int64)
    # Evaluator-only metadata is opened here, after run_case has sealed output.
    tau = detail.get('tau_relative', report['metadata']['inject_time'] - report['metadata']['time_start'])
    return {'scenario': (report['metadata']['root_cause_service'], report['metadata']['fault']),
            'starts': ends - width, 'ends': ends, 'tau': tau, 'warmup_end': warmup,
            'boundary_source': 'AUDITED_NUMERIC_GRID' if output is not None else 'NOMINAL_METADATA_GRID'}


def evaluation_inputs(run, variant, profile, planned, reports, configs):
    verify_campaign_seal(run, variant, planned, reports)
    losses = {}
    predictions = {penalty: {arm: {} for arm in ARMS} for penalty in LAMBDAS}
    score_cases = {config_id(cfg): {} for cfg in configs}
    tv_cases = {modality: {} for modality in MODALITIES}
    index = {config_id(cfg): i for i, cfg in enumerate(configs)}
    numeric_failure = False
    for case in planned:
        receipt, output = _load_sealed(run, variant, reports[case])
        bounds = _boundaries(reports[case], profile, output, configs[0])
        count = len(bounds['ends'])
        unavailable = receipt['status'] == 'INPUT_UNAVAILABLE'
        numeric_failure |= receipt['status'] == 'METHOD_FAILURE'
        for cfg in configs:
            cfg_id = config_id(cfg)
            scores = np.full(count, np.nan) if output is None else output['scores'][index[cfg_id]].copy()
            score_cases[cfg_id][case] = {**bounds, 'scores': scores,
                                        'failed': receipt['status'] != 'COMPLETE'}
        for modality in MODALITIES:
            representative = next(i for i, cfg in enumerate(configs) if cfg['arm'] == 'G' and cfg['modalities'] == modality)
            tv_failure = any(item['config'] == representative for item in receipt['tv_failures'])
            scores = np.full(count, np.nan) if output is None else output['tv_scores'][representative].copy()
            tv_cases[modality][case] = {**bounds, 'scores': scores,
                                        'failed': receipt['status'] != 'COMPLETE' or tv_failure,
                                        'tv_failure': tv_failure}
        if set(cfg['lambda'] for cfg in configs) == set(LAMBDAS):
            reference = index['G-MTL-lambda1']
            losses[case] = {**bounds, 'targets': np.full((count, 0, 1), np.nan) if unavailable else output['z'][reference].copy(),
                            'eligible': np.zeros((count, 0, 1), dtype=bool) if unavailable else output['target_mask'][reference].copy()}
            for penalty in LAMBDAS:
                for arm in ARMS:
                    predictions[penalty][arm][case] = (np.full((count, 0, 1), np.nan) if unavailable else
                        output['predictions'][index[f'{arm}-MTL-lambda{penalty:g}']].copy())
    return losses, predictions, score_cases, tv_cases, numeric_failure


def compact_lambda_selection(inputs, predictions, planned, variant='primary'):
    """Use the qualified MAE evaluator, release bulky transient IDs per arm.

    The exact IDs and errors remain reconstructible from sealed numeric arrays.
    Retaining all nine Python tuple copies through ten deletion fits is needless
    memory amplification, so only summaries survive each qualified loss call.
    """
    folds = grouped_folds(inputs, planned)
    if set(predictions) != set(LAMBDA_PRIORITY):
        raise EvaluationError('Require all three registered lambda candidates')
    details, objectives = {}, {}
    for penalty, arms in predictions.items():
        if set(arms) != set(ARMS):
            raise EvaluationError('Common lambda requires exactly G/L/ALL')
        arm_results = {}
        for arm in ARMS:
            detail = fixed_eligible_forecast_loss(inputs, arms[arm], planned)
            detail.pop('support_ids')
            detail.pop('bin_losses')
            detail['support_source'] = (f'predictions/{variant}/<handle>/predictions.npz '
                                       'target_mask+endpoints; starts>=warmup and ends<=tau')
            arm_results[arm] = detail
        objectives[penalty] = math.fsum(item['loss'] / len(ARMS) for item in arm_results.values())
        fold_losses = []
        for fold in folds:
            by_arm = {}
            for arm in ARMS:
                grouped = defaultdict(list)
                for case in fold['heldout_ids']:
                    if case in arm_results[arm]['case_losses']:
                        grouped[tuple(inputs[case]['scenario'])].append(arm_results[arm]['case_losses'][case])
                cell_means = [math.fsum(value / len(values) for value in values) for values in grouped.values()]
                by_arm[arm] = math.fsum(value / len(cell_means) for value in cell_means) if cell_means else None
            fold_losses.append({**fold, 'arm_losses': by_arm})
        details[penalty] = {'arms': arm_results, 'folds': fold_losses}
    return {'selected_lambda': select_registered(objectives, LAMBDA_PRIORITY),
            'objectives': objectives, 'details': details,
            'objective': 'MTL; equal eligible scenario/case/bin/channel; equal G/L/ALL'}


def leave_cell_lambda(inputs, predictions, planned, full_selection=None):
    # Deleting other cases cannot alter a case-local prefix model, mask or MAE.
    # Reaggregate the exact qualified per-case losses instead of materializing
    # the same millions of bin/channel tuples another ten times.
    qualified = full_selection or compact_lambda_selection(inputs, predictions, planned)
    results = []
    for scenario in sorted({tuple(inputs[case]['scenario']) for case in planned}):
        kept = tuple(case for case in planned if tuple(inputs[case]['scenario']) != scenario)
        try:
            grouped_folds({case: inputs[case] for case in kept}, kept)
            objectives = {}
            for penalty, detail in qualified['details'].items():
                arm_means = []
                for arm in ARMS:
                    case_losses = detail['arms'][arm]['case_losses']
                    eligible = [case for case in kept if case in case_losses]
                    if 5 * len(eligible) < 4 * len(kept):
                        raise EvaluationError(f'Forecast deletion eligibility gate: {len(eligible)}/{len(kept)}')
                    groups = defaultdict(list)
                    for case in eligible:
                        groups[tuple(inputs[case]['scenario'])].append(case_losses[case])
                    means = [math.fsum(value / len(values) for value in values) for values in groups.values()]
                    arm_means.append(math.fsum(value / len(means) for value in means))
                objectives[penalty] = math.fsum(value / len(ARMS) for value in arm_means)
            chosen = {'selected_lambda': select_registered(objectives, LAMBDA_PRIORITY), 'objectives': objectives}
            results.append({'excluded_scenario': scenario, 'status': 'VALID',
                            'selected_lambda': chosen['selected_lambda'], 'objectives': chosen['objectives'],
                            'margin': _selection_margin(chosen['objectives'], chosen['selected_lambda'], False)})
        except EvaluationError as exc:
            results.append({'excluded_scenario': scenario, 'status': 'INVALID',
                            'error_type': type(exc).__name__, 'error': str(exc)})
    winners = Counter(str(item['selected_lambda']) for item in results if item['status'] == 'VALID')
    return {'deletions': results, 'winner_counts': dict(winners), 'primary_registry_changed': False}


def leave_cell_cascade(lambda_diagnostic, inputs, score_cases, tv_cases, planned):
    """Each deletion uses its reselected lambda before refitting/selecting q."""
    results = []
    for deletion in lambda_diagnostic['deletions']:
        result = {**deletion, 'detectors': {}}
        if deletion['status'] == 'VALID':
            scenario = tuple(deletion['excluded_scenario'])
            kept = tuple(case for case in planned if tuple(inputs[case]['scenario']) != scenario)
            penalty = deletion['selected_lambda']
            for modality in MODALITIES:
                targets = [(f'{arm}-{modality}', score_cases[f'{arm}-{modality}-lambda{penalty:g}']) for arm in ARMS]
                targets.append((f'TV-{modality}', tv_cases[modality]))
                for detector, cases in targets:
                    try:
                        selected = select_q({case: cases[case] for case in kept}, kept)
                        result['detectors'][detector] = {'status': 'VALID', 'selected_q': selected['selected_q'],
                            'objectives': selected['objectives'],
                            'margin': _selection_margin(selected['objectives'], selected['selected_q'], True),
                            'full_threshold': selected['full_development_calibration']['threshold'],
                            'selected_folds': selected['details'][selected['selected_q']]['folds'],
                            'full_normal_support_ids': selected['full_development_calibration']['support_ids']}
                    except EvaluationError as exc:
                        result['detectors'][detector] = {'status': 'INVALID', 'error': str(exc)}
        results.append(result)
    counts = {detector: dict(Counter(str(row['detectors'][detector]['selected_q']) for row in results
              if row['detectors'].get(detector, {}).get('status') == 'VALID'))
              for detector in (f'{arm}-{modality}' for modality in MODALITIES for arm in (*ARMS, 'TV'))}
    return {'deletions': results, 'q_winner_counts': counts, 'primary_registry_changed': False,
            'policy': 'lambda reselected on kept MTL observations; q refitted/reselected at that lambda'}


def _selection_margin(objectives, selected, maximize):
    values = [float(value) for key, value in objectives.items() if float(key) != float(selected)]
    if not values:
        return None
    chosen = float(objectives[selected])
    return chosen - max(values) if maximize else min(values) - chosen


def leave_cell_q(cases, planned):
    results = []
    for scenario in sorted({tuple(cases[case]['scenario']) for case in planned}):
        kept = tuple(case for case in planned if tuple(cases[case]['scenario']) != scenario)
        try:
            chosen = select_q({case: cases[case] for case in kept}, kept)
            results.append({'excluded_scenario': scenario, 'status': 'VALID',
                            'selected_q': chosen['selected_q'], 'objectives': chosen['objectives'],
                            'margin': _selection_margin(chosen['objectives'], chosen['selected_q'], True),
                            'selected_folds': chosen['details'][chosen['selected_q']]['folds'],
                            'full_normal_support_ids': chosen['full_development_calibration']['support_ids']})
        except EvaluationError as exc:
            results.append({'excluded_scenario': scenario, 'status': 'INVALID',
                            'error_type': type(exc).__name__, 'error': str(exc)})
    return {'deletions': results, 'winner_counts': dict(Counter(str(item['selected_q']) for item in results
                    if item['status'] == 'VALID')), 'primary_registry_changed': False}


def fixed_q_evaluation(cases, planned, q):
    """Sensitivity refits each training CDF at the fixed selected primary q."""
    outcomes, folds = {}, []
    for fold in grouped_folds(cases, planned):
        distribution = normal_score_distribution({case: cases[case] for case in fold['train_ids']}, fold['train_ids'])
        threshold = weighted_cdf_inverse(distribution['values'], distribution['weights'], q)
        for case in fold['heldout_ids']:
            outcomes[case] = regime_metrics(cases[case], threshold)
        folds.append({**fold, 'threshold': threshold, 'normal_support_ids': distribution['support_ids'],
                      'case_coverage': distribution['case_coverage'], 'normal_endpoints': distribution['normal_endpoints']})
    return {'selected_q': q, 'q_held_fixed': True, 'folds': folds, 'cases': outcomes,
            'summary': planned_regime_summary(outcomes, planned),
            'full_development_calibration': calibrate_threshold(cases, planned, q)}


def replay_events(cases, planned, fold_reports, full_threshold, *, streak=3, refractory=300):
    thresholds = {case: fold['threshold'] for fold in fold_reports for case in fold['heldout_ids']}
    if set(thresholds) != set(planned):
        raise ValueError('Every planned case needs its held-out threshold')
    reports = {}
    for case in planned:
        record = cases[case]
        width = int(record['ends'][0] - record['starts'][0]) if len(record['ends']) else 5
        settings = {'bin_seconds': width, 'streak': streak, 'refractory_seconds': refractory}
        per_mode = {}
        for mode, threshold in (('OOF', thresholds[case]), ('FULL_REFIT_DESCRIPTIVE', full_threshold)):
            state = create_event_state(threshold, **settings)
            triggers = []
            for score, endpoint in zip(record['scores'], record['ends']):
                actual = np.nan if record.get('failed', False) else score
                if event_step(state, actual, int(endpoint))['trigger']:
                    triggers.append(int(endpoint))
            per_mode[mode] = {**event_diagnostics(triggers, record), 'threshold': threshold}
            if record.get('boundary_source') == 'NOMINAL_METADATA_GRID':
                # Missing inputs do not certify observed exposure duration.
                per_mode[mode].update(observed_normal_hours=None, scored_normal_hours=0.,
                    rate_per_observed_normal_hour=None, rate_per_scored_normal_hour=None,
                    duration_unavailable=True, boundary_source='NOMINAL_METADATA_GRID')
        reports[case] = per_mode
    return {'streak': streak, 'refractory_seconds': refractory, 'cases': reports,
            'interpretation': 'archival injection-regime replay; not operational FPR or onset truth'}


def _group_diagnostics(cases, outcomes, planned):
    groups = defaultdict(list)
    for case in planned:
        root, fault = cases[case]['scenario']
        for key in ('root:' + root, 'fault:' + fault, 'cell:' + root + '/' + fault):
            groups[key].append(case)
    return {group: planned_regime_summary({case: outcomes[case] for case in ids}, ids)
            for group, ids in sorted(groups.items())}


def evaluate_primary(run, planned, reports, configs, floor):
    inputs, predictions, score_cases, tv_cases, numeric_failure = evaluation_inputs(
        run, 'primary', 'primary', planned, reports, configs)
    if numeric_failure:
        raise EvaluationError('A primary configuration failed numerically; no lambda winner can be selected')
    chosen = compact_lambda_selection(inputs, predictions, planned)
    penalty = chosen['selected_lambda']
    chosen['margin'] = _selection_margin(chosen['objectives'], penalty, False)
    chosen['leave_cell_reselection'] = leave_cell_lambda(inputs, predictions, planned, chosen)
    save_json(Path(run) / 'lambda-selection.json', chosen)
    save_json(Path(run) / 'leave-cell-cascade.json', leave_cell_cascade(
        chosen['leave_cell_reselection'], inputs, score_cases, tv_cases, planned))
    selected = {'schema': SCHEMA, 'selected_lambda': penalty, 'floor': floor,
                'primary_registry_changed': False, 'detectors': {}, 'planned': len(planned),
                'interpretation': 'development selection; no final evaluation or production-performance claim'}
    hooks = []
    for modality in MODALITIES:
        targets = [(f'{arm}-{modality}', score_cases[f'{arm}-{modality}-lambda{penalty:g}']) for arm in ARMS]
        targets.append((f'TV-{modality}', tv_cases[modality]))
        for detector, cases in targets:
            try:
                report = select_q(cases, planned)
                q = report['selected_q']
                report['margin'] = _selection_margin(report['objectives'], q, True)
                report['leave_cell_reselection'] = leave_cell_q(cases, planned)
                selected_detail = report['details'][q]
                report['group_diagnostics'] = _group_diagnostics(cases, selected_detail['cases'], planned)
                save_json(Path(run) / 'evaluation' / (detector + '.json'), report)
                events = replay_events(cases, planned, selected_detail['folds'],
                                       report['full_development_calibration']['threshold'])
                save_json(Path(run) / 'events' / (detector + '.json'), events)
                selected['detectors'][detector] = {'status': 'VALID', 'selected_q': q,
                    'summary': selected_detail['summary'], 'q_objectives': report['objectives'],
                    'full_threshold': report['full_development_calibration']['threshold'],
                    'folds': [{key: value for key, value in fold.items() if key != 'normal_support_ids'}
                              for fold in selected_detail['folds']], 'margin': report['margin'],
                    'execution_failed_cases': sum(bool(record.get('tv_failure')) for record in cases.values())}
                if not detector.startswith('TV-'):
                    curve = {penalty: selected_detail['summary']['macro']['f1']}
                    diagnostic_errors = {}
                    for other_penalty in LAMBDAS:
                        if other_penalty == penalty:
                            continue
                        try:
                            diagnostic = fixed_q_evaluation(score_cases[f'{detector}-lambda{other_penalty:g}'], planned, q)
                            diagnostic['interpretation'] = 'registered lambda F1 diagnostic; primary q held fixed; no new selection'
                            save_json(Path(run) / 'lambda-f1-diagnostics' / f'{detector}-lambda{other_penalty:g}.json', diagnostic)
                            curve[other_penalty] = diagnostic['summary']['macro']['f1']
                        except EvaluationError as exc:
                            diagnostic_errors[other_penalty] = failure(run, 'lambda_f1_' + detector, 'planned30', exc)
                    selected['detectors'][detector]['lambda_f1_at_fixed_primary_q'] = curve
                    selected['detectors'][detector]['lambda_f1_diagnostic_errors'] = diagnostic_errors
                for case in planned:
                    hook = events['cases'][case]['OOF']
                    hooks.append({'detector': detector, 'case': case, 'handle': reports[case]['handle'],
                                  'triggers': hook['triggers'], 'first_post_injection_trigger': hook['first_post_injection_trigger'],
                                  'threshold_mode': 'OOF', 'profile': 'TD12-INTEGRATED-MTL'})
            except EvaluationError as exc:
                selected['detectors'][detector] = {'status': 'CALIBRATION_INVALID',
                    'error': failure(run, 'calibrate_' + detector, 'planned30', exc)}
    save_json(Path(run) / 'integrated-trigger-hook.json', {'schema': SCHEMA, 'items': hooks,
              'first_only_for_composed_metrics': True, 'no_R_or_external_comparators_per_trigger': True})
    save_json(Path(run) / 'c5-selection.json', selected)
    return selected


def _event_sensitivities(run, primary_run, planned, reports, configs, selected):
    _, _, score_cases, tv_cases, _ = evaluation_inputs(primary_run, 'primary', 'primary', planned, reports, configs)
    results = {}
    penalty = selected['selected_lambda']
    for detector, selection in selected['detectors'].items():
        if selection['status'] != 'VALID':
            continue
        modality = detector.rsplit('-', 1)[1]
        cases = tv_cases[modality] if detector.startswith('TV-') else score_cases[f'{detector}-lambda{penalty:g}']
        for streak, refractory in ((1, 300), (3, 300), (5, 300), (3, 60), (3, 600)):
            tag = f'{detector}-streak{streak}-refractory{refractory}'
            report = replay_events(cases, planned, selection['folds'], selection['full_threshold'],
                                   streak=streak, refractory=refractory)
            save_json(Path(run) / 'event-sensitivity' / (tag + '.json'), report)
            results[tag] = {'streak': streak, 'refractory_seconds': refractory,
                            'OOF_total_triggers': sum(len(item['OOF']['triggers']) for item in report['cases'].values()),
                            'OOF_post_censored': sum(item['OOF']['post_injection_censored'] for item in report['cases'].values())}
    return results


def evaluate_sensitivity(run, variants, planned, reports, selected):
    results = {}
    penalty = selected['selected_lambda']
    for variant in variants:
        _, _, score_cases, tv_cases, numeric_failure = evaluation_inputs(run, variant['id'], variant['profile'],
                                                                       planned, reports, variant['configs'])
        variant_results = {'dimension': variant['dimension'], 'profile': variant['profile'],
                           'numeric_failure': numeric_failure, 'detectors': {}, 'primary_registry_changed': False}
        for detector, selection in selected['detectors'].items():
            if selection['status'] != 'VALID':
                variant_results['detectors'][detector] = {'status': 'PRIMARY_CALIBRATION_INVALID'}
                continue
            modality = detector.rsplit('-', 1)[1]
            cases = tv_cases[modality] if detector.startswith('TV-') else score_cases[f'{detector}-lambda{penalty:g}']
            try:
                detail = fixed_q_evaluation(cases, planned, selection['selected_q'])
                detail['group_diagnostics'] = _group_diagnostics(cases, detail['cases'], planned)
                save_json(Path(run) / 'sensitivity-evaluation' / variant['id'] / (detector + '.json'), detail)
                events = replay_events(cases, planned, detail['folds'], detail['full_development_calibration']['threshold'])
                save_json(Path(run) / 'sensitivity-events' / variant['id'] / (detector + '.json'), events)
                delta = detail['summary']['macro']['f1'] - selection['summary']['macro']['f1']
                variant_results['detectors'][detector] = {'status': 'VALID', 'fixed_q': selection['selected_q'],
                    'summary': detail['summary'], 'f1_delta_from_primary': delta,
                    'full_threshold': detail['full_development_calibration']['threshold'],
                    'execution_failed_cases': sum(bool(record.get('tv_failure')) for record in cases.values())}
            except EvaluationError as exc:
                variant_results['detectors'][detector] = {'status': 'CALIBRATION_INVALID',
                    'error': failure(run, 'sensitivity_' + variant['id'] + '_' + detector, 'planned30', exc)}
        # Paired G-L and G-ALL signs are diagnostic only, not a new winner rule.
        for modality in MODALITIES:
            entries = variant_results['detectors']
            if all(entries.get(f'{arm}-{modality}', {}).get('status') == 'VALID' for arm in ARMS):
                g = entries[f'G-{modality}']['summary']['macro']['f1']
                variant_results[f'contrasts-{modality}'] = {f'G-minus-{arm}': g - entries[f'{arm}-{modality}']['summary']['macro']['f1']
                                                          for arm in ('L', 'ALL')}
                base = selected['detectors']
                base_g = base[f'G-{modality}']['summary']['macro']['f1']
                variant_results[f'sign-flips-{modality}'] = {
                    f'G-minus-{arm}': bool((g - entries[f'{arm}-{modality}']['summary']['macro']['f1'])
                                           * (base_g - base[f'{arm}-{modality}']['summary']['macro']['f1']) < 0)
                    for arm in ('L', 'ALL')}
        results[variant['id']] = variant_results
    return results


def _c1_floor(path, pins):
    _verify(path, pins)
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if 'local_config' not in value or 'ppr_config' not in value:
        raise ValueError('C1 selection must expose local_config and ppr_config')
    floor = value['local_config']['floor']
    if floor not in (.001, .01):
        raise ValueError('C5 primary floor must come from registered selected C1 local config')
    return float(floor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run')
    parser.add_argument('mode', choices=('smoke', 'full', 'sensitivity'))
    parser.add_argument('--audit-root', required=True)
    parser.add_argument('--c1-selection')
    parser.add_argument('--primary-run')
    parser.add_argument('--worker-timeout', type=float, default=300.)
    args = parser.parse_args()
    run = Path(args.run).resolve()
    contract, pins = admitted_contract(run, args.mode)
    planned, reports = read_roster(args.audit_root, pins, args.mode)
    if args.mode == 'smoke':
        floor = .01
    elif args.c1_selection:
        floor = _c1_floor(args.c1_selection, pins)
    else:
        raise ValueError('Full/sensitivity requires pre-pinned C1 local selection')
    primary_configs = registered_configs(floor)
    selected = None
    if args.mode == 'sensitivity':
        if not args.primary_run:
            raise ValueError('Sensitivity requires the completed primary C5 run')
        selection_path = Path(args.primary_run) / 'c5-selection.json'
        _verify(selection_path, pins)
        _verify(Path(args.primary_run) / 'run-contract.json', pins)
        _verify(Path(args.primary_run) / 'predictions-seal.json', pins)
        selected = json.loads(selection_path.read_text(encoding='utf-8'))
        if selected['floor'] != floor or selected['planned'] != 30:
            raise ValueError('Sensitivity does not match its primary selection')
        # Pin every source seal and prediction file before reusing event outputs.
        for case in planned:
            directory = Path(args.primary_run) / 'predictions/primary' / reports[case]['handle']
            _verify(directory / 'seal.json', pins)
            seal = json.loads((directory / 'seal.json').read_text(encoding='utf-8'))
            for item in seal['artifacts']:
                _verify(directory / item['file'], pins)
        variants = sensitivity_registry(floor, selected['selected_lambda'])
    else:
        variants = [{'id': 'primary', 'profile': 'primary', 'configs': primary_configs}]
    save_json(run / 'c5-plan.json', {'schema': SCHEMA, 'mode': args.mode, 'planned_cases': planned,
        'configs': variants, 'floor_source': 'smoke fixed feasibility .01; no selection' if args.mode == 'smoke' else args.c1_selection,
        'evaluation_opened_only_after_case_seal': True, 'no_final_cases': True})
    receipts = []
    for variant in variants:
        for ordinal, case in enumerate(planned, 1):
            arrays, source = load_numeric(args.audit_root, reports[case], variant['profile'], pins)
            receipt = run_case(run, variant['id'], case, reports[case], arrays, source,
                               variant['configs'], args.worker_timeout)
            receipts.append({'variant': variant['id'], 'case': case, 'handle': reports[case]['handle'],
                             'status': receipt['status'], 'seconds': receipt['seconds'],
                             'tv_failures': len(receipt['tv_failures'])})
            print(f"{variant['id']} {ordinal}/{len(planned)} {reports[case]['handle']} {receipt['status']} {receipt['seconds']:.1f}s", flush=True)
            del arrays
    campaign_seal = seal_campaign_predictions(run, variants, planned, reports)
    result = {'schema': SCHEMA, 'mode': args.mode, 'planned': len(planned), 'case_runs': receipts,
              'prediction_failures': sum(item['status'] == 'METHOD_FAILURE' for item in receipts),
              'input_unavailable': sum(item['status'] == 'INPUT_UNAVAILABLE' for item in receipts),
              'tv_failed_case_runs': sum(item['tv_failures'] > 0 for item in receipts),
              'predictions_seal_sha256': campaign_seal}
    calibration_invalid = False
    try:
        if args.mode == 'full':
            chosen = evaluate_primary(run, planned, reports, primary_configs, floor)
            result['selection'] = {'selected_lambda': chosen['selected_lambda'],
                                   'detector_statuses': {name: row['status'] for name, row in chosen['detectors'].items()}}
            calibration_invalid = any(row['status'] != 'VALID' or row.get('lambda_f1_diagnostic_errors')
                                      for row in chosen['detectors'].values())
        elif args.mode == 'sensitivity':
            diagnostics = evaluate_sensitivity(run, variants, planned, reports, selected)
            diagnostics['event_only'] = _event_sensitivities(run, args.primary_run, planned, reports,
                                                          primary_configs, selected)
            save_json(run / 'sensitivity-summary.json', diagnostics)
            calibration_invalid = any(row['status'] != 'VALID' for key, variant in diagnostics.items()
                                      if key != 'event_only' for row in variant['detectors'].values())
        else:
            result['selection'] = 'NOT PERFORMED; predetermined feasibility smoke only'
        result['status'] = 'COMPLETE' if not result['prediction_failures'] else 'INVALID_NUMERIC_EXECUTION'
        if calibration_invalid and not result['prediction_failures']:
            result['status'] = 'RETURN_TO_D_CALIBRATION_INVALID'
        elif result['tv_failed_case_runs'] and not result['prediction_failures']:
            result['status'] = 'COMPLETE_WITH_TV_EXECUTION_FAILURES'
    except EvaluationError as exc:
        result['status'] = 'RETURN_TO_D_OR_EXECUTION_REVIEW'
        result['evaluation_error'] = failure(run, 'c5_evaluation', 'planned', exc)
    save_json(run / 'c5-summary.json', result)
    print(json.dumps(plain(result), ensure_ascii=False), flush=True)
    if result['status'] != 'COMPLETE':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
