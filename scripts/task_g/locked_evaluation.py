"""G33 fixed post-seal truth source and streamed frozen TD-v1.3 evaluation."""
from __future__ import annotations

from collections import defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import time

from scripts.task_g import evaluation as frozen
from scripts.task_g import final_evaluation as fixture_evaluator
from scripts.task_g import final_source as source_api
from scripts.task_g import locked_provenance as provenance

Error = provenance.Error
TRUTH_COLUMNS = ('case', 'dataset', 'repetition', 'root_cause_service', 'fault', 'inject_time', 'time_start')


def parse_truth_projection(rows, planned_ids, observed_origins):
    """Same exact parser for a pinned artificial projection and future real60."""
    if type(rows) is not list or len(rows) != len(planned_ids) or len(set(planned_ids)) != len(planned_ids):
        raise Error('TRUTH_PROJECTION_DENOMINATOR_DRIFT')
    index = {}
    for row in rows:
        if type(row) is not dict or set(row) != set(TRUTH_COLUMNS) or row['case'] in index:
            raise Error('TRUTH_PROJECTION_FIELDS_OR_DUPLICATE_ROW')
        index[row['case']] = row
    if set(index) != set(planned_ids) or set(observed_origins) != set(planned_ids):
        raise Error('TRUTH_PROJECTION_ROSTER_OR_ORIGIN_DRIFT')
    results = {}
    for ordinal, identity in enumerate(planned_ids):
        row = index[identity]
        origin, tau = observed_origins[identity], row['inject_time']
        if (type(origin) is not int or type(tau) not in (int, float) or not math.isfinite(tau)
                or tau != int(tau) or tau < origin or row['time_start'] != origin
                or type(row['root_cause_service']) is not str or not row['root_cause_service']
                or type(row['fault']) is not str or not row['fault']):
            raise Error('TRUTH_LITERAL_OR_ACTUAL_CLOCK_UNQUALIFIABLE')
        results[ordinal] = {'root_key': source_api.candidate_key(row['root_cause_service']),
                            'tau_relative': tau - origin, 'root_stratum': row['root_cause_service'],
                            'fault_stratum': row['fault']}
    return results


def _read_preparation_truth():
    _, contract = provenance.registered_context()
    path = provenance.ROOT / 'cache/synthetic-truth-plan.json'
    if provenance.sha_file(path) != contract['synthetic_truth_plan_sha256']:
        raise Error('PREDECLARED_ARTIFICIAL_PROJECTION_DRIFT')
    plan = json.loads(path.read_bytes())
    if plan.get('scope') != 'PREDECLARED_ARTIFICIAL_ONLY':
        raise Error('ARTIFICIAL_SOURCE_SCOPE_REQUIRED')
    return parse_truth_projection(plan['rows'], plan['planned_ids'], plan['observed_origins'])


def _read_final_truth():
    """Only this fixed projection is allowed; no caller labels or oracle files."""
    _, contract = provenance.require_final_authorization()
    # A direct call to the fixed reader cannot open truth before durable seal.
    provenance.verify_seal(final=True)
    import pyarrow.parquet as pq
    from scripts.task_g import source_admission
    metadata = provenance.W / source_api.METADATA_REL
    if provenance.sha_file(metadata) != source_api.METADATA_SHA:
        raise Error('PINNED_FINAL_METADATA_DRIFT')
    _, registry = source_admission._read_frozen_contract(provenance.W, provenance.P)
    roster = pq.read_table(metadata, columns=list(source_api.ROSTER_PROJECTION)).to_pylist()
    plan = source_admission._plan_final_metadata(roster, registry)
    identities = plan['final_ids']
    roster_sha = hashlib.sha256(('\n'.join(identities) + '\n').encode()).hexdigest()
    if len(identities) != 60 or roster_sha != source_api.ROSTER_SHA:
        raise Error('FIXED_FINAL60_ROSTER_DRIFT')
    # Filtering before returning values limits the permitted truth to final60.
    rows = pq.read_table(metadata, columns=list(TRUTH_COLUMNS), filters=[('case', 'in', identities)]).to_pylist()
    origins = {}
    for identity in identities:
        path = source_admission._exact_local_path(provenance.W / source_api.RAW_REL, identity + '/metrics.parquet')
        parquet = pq.ParquetFile(path)
        if 'time' not in parquet.schema_arrow.names:
            raise Error('ACTUAL_METRIC_CLOCK_SCHEMA_DRIFT')
        values = parquet.read(columns=['time']).column('time')
        import pyarrow.compute as pc
        origin = pc.min(values).as_py()
        if type(origin) not in (int, float) or not math.isfinite(origin) or origin != int(origin):
            raise Error('ACTUAL_METRIC_ORIGIN_UNQUALIFIABLE')
        origins[identity] = int(origin)
    return parse_truth_projection(rows, identities, origins)


def _mapped(row, bindings, truth):
    label = truth[row['ordinal']]
    root = fixture_evaluator.literal_root_index(bindings['candidate_ids'], label['root_key'])
    triggers = {name: {endpoint: fixture_evaluator.literal_root_index(keys, label['root_key'])
                      for endpoint, keys in mapping.items()}
                for name, mapping in bindings['integrated_candidate_ids'].items()}
    return {**label, 'root_index': root, 'integrated_root_indices': triggers}


def _cases(envelope):
    store = provenance.ShardStore()
    for inventory in provenance.iter_case_inventories(envelope):
        roles = inventory['scientific_roles']
        yield store.get(roles['case/compact']), store.get(roles['case/controller-bindings'])


def evaluate_verified(envelope, truth):
    """Frozen per-case rules; hold metrics/statistics, never full diagnostics60."""
    final = envelope['commitment']['scope'] == 'ACTUAL_FINAL60'
    count = envelope['_verified']['case_inventories']
    if set(truth) != set(range(count)):
        raise Error('TRUTH_OR_PLANNED_DENOMINATOR_CHANGED')
    case_metrics, statistics = [], {'primary': [], 'secondary': []}
    contextual = {name: [] for name in ('Local-MAX-MT', 'BARO-RANK-adapted-TD12', 'RCD')}
    detectors = {name: {} for name in frozen.DETECTORS}
    mobility = defaultdict(lambda: {'planned': 0, 'mobile': 0})
    shared = starved = arm_failures = 0
    costs = []
    planned = []
    for row, bindings in _cases(envelope):
        label = _mapped(row, bindings, truth)
        planned.append({key: row[key] for key in ('ordinal', 'cell_ordinal', 'repeat')})
        root, candidates = label['root_index'], row['candidate_count']
        shared += row['shared_preprocessing_failed']; starved += frozen.signal_starved(row['local_evidence'], candidates)
        outcome = {'ordinal': row['ordinal'], 'root_in_candidate': root is not None, 'ranking': {}}
        for operator in ('primary', 'secondary'):
            arms = row['c1'][operator]
            ranking = {arm: frozen._score_record(arms[arm], root, candidates) for arm in ('L', 'O')}
            ranking['R'] = frozen.random_control_metrics(arms['R'], candidates, root)
            outcome['ranking'][operator] = ranking
            arm_failures += sum(arms[arm]['status'] != 'SUCCESS' for arm in ('L', 'O')) + ranking['R']['failed_draws']
            statistics[operator].append({'ordinal': row['ordinal'], 'cell_ordinal': row['cell_ordinal'], 'repeat': row['repeat'],
                'root_stratum': label['root_stratum'], 'fault_stratum': label['fault_stratum'],
                'L': ranking['L']['rr'], 'O': ranking['O']['rr'], 'R': ranking['R']['metrics']['rr']})
        if any(a['seed'] != b['seed'] or a['graph_sha256'] != b['graph_sha256']
               for a, b in zip(row['c1']['primary']['R'], row['c1']['secondary']['R'], strict=True)):
            raise Error('PRIMARY_SECONDARY_CONTROL_GRAPH_DRIFT')
        bucket = mobility[label['root_stratum']]; bucket['planned'] += 1
        bucket['mobile'] += outcome['ranking']['primary']['R']['mobile']
        for method in ('Local-MAX-MT', 'BARO-RANK-adapted-TD12'):
            contextual[method].append(frozen._score_record(row['contextual'][method], root, candidates))
        rcd = row['contextual']['RCD']
        if rcd['n_services'] != candidates:
            raise Error('RCD_CANNOT_REPAIR_CANDIDATE_UNIVERSE')
        contextual['RCD'].append(frozen.rcd_seed_metrics(rcd['seed_outputs'], rcd['metric_owners'], candidates, root))
        for name in frozen.DETECTORS:
            detectors[name][row['ordinal']] = frozen.c5_case_metrics(row['c5'][name], label['tau_relative'],
                trigger_root_indices=label['integrated_root_indices'][name])
        case_metrics.append(outcome); costs.append(row['costs'])
    if not final:
        return {'schema': 'TD13-G33-PREPARATION-EVALUATION-v1', 'planned_cases': count,
                'case_metrics': case_metrics, 'contextual': contextual, 'c5': detectors,
                'cost_summary': fixture_evaluator.cost_summary([{'ordinal': index, 'costs': value} for index, value in enumerate(costs)]),
                'scientific_verdict': 'NOT_APPLICABLE_SYNTHETIC_PREPARATION', 'final_efficacy': False,
                'verified_receipt_sha256': envelope['_verified']['receipt_sha256']}
    frozen._planned60(planned)
    summaries = {operator: frozen.paired_scenario_summary(items) for operator, items in statistics.items()}
    for operator in summaries:
        summaries[operator]['metrics'] = {arm: {metric: math.fsum(
            item['ranking'][operator][arm]['metrics'][metric] if arm == 'R' else item['ranking'][operator][arm][metric]
            for item in case_metrics) / 60 for metric in frozen.METRICS} for arm in ('L', 'O', 'R')}
        summaries[operator]['candidate_absent_cases'] = sum(not item['root_in_candidate'] for item in case_metrics)
    verdict = frozen.primary_verdict(summaries['primary'], shared_preprocessing_failures=shared,
        starved_cases=starved, arm_failures=arm_failures, mobility_by_root=dict(mobility))
    c5 = {}
    for name, records in detectors.items():
        summary = frozen.planned_regime_summary({ordinal: item['regime'] for ordinal, item in records.items()}, tuple(range(60)))
        events = [item['events'] for item in records.values()]
        observed = math.fsum(item['observed_normal_hours'] for item in events)
        scored = math.fsum(item['scored_normal_hours'] for item in events)
        pre = sum(item['pre_injection_triggers'] for item in events)
        c5[name] = {**summary, 'threshold': row['c5'][name]['threshold'],
            'unavailable_cases': sum(item['regime']['unavailable_case'] for item in records.values()),
            'failed_bins': sum(item['regime']['failed_bins'] for item in records.values()),
            'normal_observed_seconds': observed * 3600, 'normal_scored_seconds': scored * 3600,
            'pre_injection_triggers': pre, 'rate_per_observed_normal_hour': pre / observed if observed else None,
            'rate_per_scored_normal_hour': pre / scored if scored else None,
            'both_regime_scored_cases': sum(item['regime']['normal_scored'] > 0 and item['regime']['positive_scored'] > 0 for item in records.values()),
            'first_post_injection_censored_cases': sum(item['events']['post_injection_censored'] for item in records.values()),
            'composition_macro': {metric: math.fsum(item['composition']['metrics'][metric] for item in records.values()) / 60 for metric in frozen.METRICS},
            'cases': records}
    return {'schema': 'TD13-G33-FINAL-EVALUATION-v1', 'planned_cases': 60, 'primary': summaries['primary'],
            'secondary': summaries['secondary'], 'primary_verdict': verdict, 'case_metrics': case_metrics,
            'contextual': {name: {'mean': {metric: math.fsum(item['mean'][metric] if name == 'RCD' else item[metric]
                for item in records) / 60 for metric in frozen.METRICS},
                'planned_cases': 60,
                'failed_cases': sum(item['failed_seeds'] == 3 if name == 'RCD' else item['status'] == 'METHOD_FAILURE' for item in records),
                'failed_seeds': sum(item['failed_seeds'] for item in records) if name == 'RCD' else None,
                'unknown_key_count': sum(item['unknown_key_count'] for item in records) if name == 'RCD' else None,
                'cases': records} for name, records in contextual.items()},
            'c5': c5, 'cost_summary': fixture_evaluator.cost_summary([{'ordinal': index, 'costs': value} for index, value in enumerate(costs)]),
            'monte_carlo': {operator: {metric: {'aggregate_sd': math.sqrt(math.fsum(
                item['ranking'][operator]['R']['mc'][metric]['sd'] ** 2 for item in case_metrics)) / 60,
                'aggregate_se': math.sqrt(math.fsum(item['ranking'][operator]['R']['mc'][metric]['se'] ** 2
                for item in case_metrics)) / 60,
                'planned_cases': 60, 'planned_draws_per_case': 256} for metric in frozen.METRICS} for operator in summaries},
            'verified_receipt_sha256': envelope['_verified']['receipt_sha256'],
            'limitations': ['Previously studied benchmark; historical exposure retained.',
                           'Conditional scenario/draw uncertainty is not population confidence.',
                           'F development qualification, five-reviewer OPEN and FlashTicket validation unchanged.']}


def evaluate_preparation():
    envelope = provenance.verify_seal()
    truth = _read_preparation_truth()
    result = evaluate_verified(envelope, truth)
    result['full_verification_before_truth'] = True
    provenance.exclusive(provenance.ROOT / 'cache/preparation-evaluation.json', result)
    return result


def evaluate_final():
    envelope = provenance.verify_seal(final=True)
    truth = _read_final_truth()
    result = evaluate_verified(envelope, truth)
    result['full_verification_before_truth'] = True
    provenance.exclusive(provenance.ROOT / 'evaluation.json', result)
    return result


def scientific_view(value):
    """Predeclared replay comparison excludes duration/runtime metadata only."""
    excluded = {'costs', 'conversion_costs', 'explanation_support_conversion_seconds',
                'worker_measurements', 'context', '_verified', 'recorded_at_utc',
                'timing_completed', 'stderr_sha256', 'stderr_bytes', 'stdout_sha256', 'stdout_bytes',
                'wall_seconds', 'fit_seconds', 'prediction_seconds', 'detector_wall_seconds',
                'worker_numeric_seconds', 'control_generation_seconds', 'R_rank_seconds',
                'shared_preprocessing_seconds', 'reused_equal_endpoint_computation'}
    if type(value) is dict:
        return {key: scientific_view(item) for key, item in value.items()
                if key not in excluded}
    if type(value) is list:
        return [scientific_view(item) for item in value]
    return value


def reproduce_final():
    context, contract = provenance.require_final_authorization()
    envelope = provenance.verify_seal(final=True)
    truth = _read_final_truth()
    saved = json.loads((provenance.ROOT / 'evaluation.json').read_bytes())
    reproduction = evaluate_verified(envelope, truth)
    reproduction['full_verification_before_truth'] = True
    exact = saved == json.loads(provenance._canonical(reproduction))
    from scripts.task_g.locked_campaign import compute_case
    admission_started = time.perf_counter()
    source = source_api.open_final_source()
    admission_wall_seconds = time.perf_counter() - admission_started
    directory = provenance.ROOT / 'cache' / ('reproduction-' + str(time.time_ns()))
    directory.mkdir()
    store = provenance.ShardStore(); numeric_replays = []
    originals = list(envelope['commitment']['case_inventory_manifest'])
    for ordinal in contract['reproduction_policy']['numeric_replay_ordinals']:
        inventory, _ = compute_case(source, ordinal, admission_wall_seconds, contract, store, directory, 'ACTUAL_FINAL60')
        old = store.get(originals[ordinal])
        mismatches = []
        left, right = old['scientific_roles'], inventory['scientific_roles']
        if set(left) != set(right):
            mismatches.append('SCIENTIFIC_ROLE_SET')
        for role in sorted(set(left) & set(right)):
            if scientific_view(store.get(left[role])) != scientific_view(store.get(right[role])):
                mismatches.append(role)
        ref = store.put(inventory)
        provenance.exclusive(directory / f'case-{ordinal:02d}.json', {'inventory': ref, 'mismatches': mismatches})
        numeric_replays.append({'ordinal': ordinal, 'scientific_exact_equal': not mismatches, 'mismatches': mismatches, 'inventory': ref})
    result = {'schema': 'TD13-G33-REPRODUCTION-v1', 'context': context, 'durable_full60_verified': True,
              'evaluator_exact_equal': exact, 'numeric_replay_cases': numeric_replays,
              'cohort_admission_wall_seconds': admission_wall_seconds,
              'numeric_replay_cost_coverage': 'Measured full cohort admission charged conservatively per replay case, matching production C1 deadline and full wall scope.',
              'policy': contract['reproduction_policy'], 'outcome_selected_retry': False}
    provenance.exclusive(provenance.ROOT / 'reproduction.json', result)
    return result
