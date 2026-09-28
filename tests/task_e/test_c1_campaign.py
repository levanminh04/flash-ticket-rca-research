"""Synthetic C1 selection/controller fixtures; no real data or child models."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e import c1_development as campaign
from scripts.task_e.contract import DEV_IDS, opaque_handle
from scripts.task_e.execution import file_sha, require_contract, save_json, save_npz


def measurements(local, observed, cell=('ts-auth-service', 'cpu')):
    return {'cell': list(cell), 'local': [{'rr': float(value)} for value in local],
            'observed': [[{'rr': float(value)} for value in row] for row in observed]}


class SelectionTests(unittest.TestCase):
    def test_O_demand_uses_only_L_deletion_winners_and_their_kept_cases(self):
        cases={}
        first_cell=DEV_IDS[0].split('_')[1:3]
        for case in DEV_IDS:
            _,root,fault,_=case.split('_')
            # Global theta0 .60 vs theta1 .54. Delete the first cell:
            # theta0 becomes .555..., theta1 .60; other deletions keep theta0.
            local=[1.,0.]+[0.]*6 if [root,fault]==first_cell else [.5555555555555556,.6]+[0.]*6
            cases[case]={'cell':[root,fault],'local':[{'rr':value} for value in local]}
        primary=campaign.local_selection(cases)
        self.assertEqual(primary['selected_local_index'],0)
        plans=[{'scope':'primary','planned_cases':list(cases),**primary}]
        for cell in sorted({tuple(v['cell']) for v in cases.values()}):
            kept={i:v for i,v in cases.items() if tuple(v['cell'])!=cell}
            plans.append({'scope':'leave_cell','omitted_cell':cell,'planned_cases':list(kept),
                          **campaign.local_selection(kept)})
        requests,order=campaign.observed_request_plan(plans)
        self.assertEqual(order,[0,1])
        self.assertEqual(set(requests[0]),set(DEV_IDS))
        expected={i for i in DEV_IDS if i.split('_')[1:3]!=first_cell}
        self.assertEqual(set(requests[1]),expected)
        self.assertEqual(sum(map(len,requests.values())),57)
        self.assertTrue(all(reason['scope']=='leave_cell' and list(reason['omitted_cell'])==first_cell
                            for reasons in requests[1].values() for reason in reasons))

    def test_absolute_L_is_selected_before_graph_gain(self):
        # Config0 L=.9/O=.9; config1 L=.1/O=1 would maximize gain, but is forbidden.
        local = [.9, .1, .2, .2, .2, .2, .2, .2]
        observed = np.full((8, 9), .5)
        observed[0] = [.8, .9, .7, .6, .5, .4, 1., .8, .7]
        observed[1] = 1.
        selected = campaign.selection({'a': measurements(local, observed)})
        self.assertEqual(selected['selected_local_index'], 0)
        self.assertEqual(selected['selected_ppr_index'], 1)
        self.assertEqual(selected['selected_diffusion_index'], 6)
        self.assertEqual(selected['local_margin'], .7)
        self.assertEqual(selected['ppr_config']['operator'], 'ppr')

    def test_registered_local_and_rank_tie_priority(self):
        selected = campaign.selection({'a': measurements([1.]*8, np.ones((8, 9)))})
        self.assertEqual(selected['selected_local_index'], 0)
        self.assertEqual(selected['local_config'], {'floor': .01, 'pool': 'max', 'fusion': 'max'})
        self.assertEqual(selected['ppr_config'], {'operator': 'ppr', 'direction': 'reverse', 'damping': .85})
        self.assertEqual(selected['selected_diffusion_index'], 6)
        # Improvement below the 1e-12 tie boundary cannot defeat the preferred ID.
        observed = np.full((8, 9), .5)
        observed[:, 1] += 5e-13
        selected = campaign.selection({'a': measurements([1.]*8, observed)})
        self.assertEqual(selected['selected_ppr_index'], 0)

    def test_fold_rosters_keep_each_three_repeat_cell_together(self):
        cases = {}
        for case in DEV_IDS:
            _, root, fault, _ = case.split('_')
            cases[case] = measurements([.5]*8, np.full((8, 9), .5), (root, fault))
        selected = campaign.selection(cases)
        held = [case for fold in selected['folds'] for case in fold['heldout_ids']]
        self.assertEqual(sorted(held), sorted(DEV_IDS))
        for fold in selected['folds']:
            self.assertEqual(len(fold['heldout_ids']), 6)
            cells = {tuple(cases[case]['cell']) for case in fold['heldout_ids']}
            self.assertEqual(len(cells), 2)
            self.assertTrue(all(sum(tuple(cases[case]['cell']) == cell for case in fold['heldout_ids']) == 3
                                for cell in cells))


class FakeNumericWorker:
    calls = []
    rank_calls = []
    last_control = None
    last_observed = False

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def ping(self):
        return {'fixture': True, 'no_external_process': True}

    def c1(self, ref, query, adj, types, config, ranks=None):
        self.calls.append({**deepcopy(config), 'received_types': list(types), 'rank_config_count':len(ranks or [])})
        n = len(adj)
        local = np.array([3., 2., 1.])[:n]
        evidence = {'local': local, 'blocks': {'metric': local, 'trace': local/2},
                    'masks': {'local': np.ones(n, dtype=bool),
                              'channels': np.ones((n, len(types)), dtype=bool),
                              'blocks': {kind: np.ones(n, dtype=bool) for kind in ('metric', 'trace', 'log')}},
                    'channel_scores': np.ones((n, len(types))),
                    'diagnostics': {'numerical_channel_failures': np.zeros((n, len(types)), dtype=bool),
                        'centers': np.ones((n, len(types))), 'scales': np.full((n, len(types)), .01),
                        'reference_valid_bins': np.full((n, len(types)), ref.shape[2]),
                        'query_valid_bins': np.full((n, len(types)), query.shape[2]),
                        'reference_min_bins': int(np.ceil(.8*ref.shape[2])),
                        'query_min_bins': int(np.ceil(.8*query.shape[2])),
                        'channel_reasons': [['available']*len(types) for _ in range(n)],
                        'config': deepcopy(config)}}
        return {'evidence': evidence, 'rankings': [{'scores': local/local.sum(),
                'diagnostics': {'residual_inf': 0.}} for _ in (ranks or [])]}

    def rank(self, local, graphs, configs):
        self.rank_calls.append({'local':local.copy(),'graph_dimensions':graphs.ndim,'configs':deepcopy(configs)})
        if graphs.ndim == 2:
            type(self).last_control = None
            type(self).last_observed = len(configs)==9 and not np.all(local==1)
            scaled = local/local.max() if len(local) and local.max() > 0 else local
            return {'rankings': [{'scores': (scaled/scaled.sum() if scaled.sum() else scaled)
                                 if cfg['operator'] == 'ppr' else scaled,
                                 'diagnostics': {'residual_inf': 0.}}
                                for cfg in configs]}
        type(self).last_control = 'directed' if len(configs) == 3 else 'undirected'
        # Half rank1, half rank3. Mean per-draw RR=2/3, mean-score RR=1/2.
        return {'rankings': [[{'scores': (np.array([3., 2., 1.]) if j < 128 else
                              np.array([0., 2., 1.]))[:len(local)]}
                             for _ in configs] for j in range(len(graphs))]}


def fixture_roster(base, *, profiles=('primary',), failed=None, alternate_names=(), empty_cases=()):
    """Create only invented numeric arrays plus their real trusted-input receipts."""
    audit, topology = base/'audit', base/'topology'
    failed = failed or set()
    paths = []
    for case in DEV_IDS:
        handle = opaque_handle(case)
        _, root, fault, _ = case.split('_')
        report = {'handle': handle, 'case': case,
                  'metadata': {'root_cause_service': root, 'fault': fault},
                  'profiles': {}, 'numeric_files': [], 'seconds': .01}
        for profile in profiles:
            names = ['other', root, 'third'] if profile in alternate_names else [root, 'other', 'third']
            if case in empty_cases:
                names = []
            nodes = len(names)
            if (case, profile) in failed:
                report['profiles']['c1_'+profile] = {'status': 'FAILURE', 'error': 'invented corrupt input'}
                continue
            numeric = audit/'intermediates'/handle/('c1_'+profile+'.npz')
            bins = {'bin5': 60, 'bin20': 15, 'horizon180': 18, 'horizon420': 42}.get(profile, 30)
            save_npz(numeric, ref=np.ones((nodes, 12, bins)), query=np.ones((nodes, 12, bins)),
                     adj=np.zeros((nodes, nodes), dtype=bool), channel_types=np.array([0]*10+[1, 2]))
            report['profiles']['c1_'+profile] = {'status': 'MATERIALIZED', 'service_names': names,
                                               'audit': {'synthetic': True}}
            report['numeric_files'].append({'path': str(numeric), 'sha256': file_sha(numeric)})
            paths.append(numeric)
        reportpath = audit/'case-audits'/(handle+'.json')
        save_json(reportpath, report)
        paths.append(reportpath)
        for representation in ('directed', 'undirected'):
            graphfile = topology/'topology'/handle/representation/'200'/'graphs.npz'
            nodes = 0 if case in empty_cases else 3
            save_npz(graphfile, graphs=np.zeros((256, nodes, nodes), dtype=bool))
            paths.append(graphfile)
    contract = {'inputs': [{'path': str(path), 'sha256': file_sha(path)} for path in paths]}
    return audit, topology, contract


class ControllerTests(unittest.TestCase):
    def setUp(self):
        FakeNumericWorker.calls = []
        FakeNumericWorker.rank_calls = []
        FakeNumericWorker.last_control = None
        FakeNumericWorker.last_observed = False

    def test_forecast_free_predictions_uses_real_numeric_result_schema(self):
        bundle = {'ref': np.ones((3, 12, 30)), 'query': np.ones((3, 12, 30)),
                  'adj': np.zeros((3, 3), dtype=bool), 'channel_types': np.array([0]*10+[1, 2])}
        results = campaign.forecast_free_predictions(FakeNumericWorker(), bundle)
        self.assertEqual(len(results), 8)

    def test_numeric_channel_failure_cannot_be_a_low_scoring_candidate(self):
        class Failed(FakeNumericWorker):
            def c1(self, *args, **kwargs):
                result = super().c1(*args, **kwargs)
                result['evidence']['diagnostics']['numerical_channel_failures'][0, 0] = True
                return result
        bundle = {'ref': np.ones((3, 12, 30)), 'query': np.ones((3, 12, 30)),
                  'adj': np.zeros((3, 3), dtype=bool), 'channel_types': np.array([0]*10+[1, 2])}
        with self.assertRaises(RuntimeError):
            campaign.forecast_free_predictions(Failed(), bundle)

    def test_full_mocked_roster_R_metric_mean_BARO_and_immutable_primary_seals(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = base/'run'
            audit, topology, contract = fixture_roster(base)
            original_evaluate = campaign.evaluate
            original_rank = FakeNumericWorker.rank
            checked = set()
            checked_auxiliary = set()

            def after_seal(scores, report, failed=False):
                # Every primary local/O prediction must already have its hash seal.
                handle = report['handle']
                seal_path = run/'seals'/(handle+'.json')
                if handle not in checked:
                    self.assertTrue(seal_path.is_file())
                    seal = json.loads(seal_path.read_text(encoding='utf-8'))
                    self.assertEqual(file_sha(seal['file']), seal['sha256'])
                    self.assertTrue(seal['before_evaluation'])
                    self.assertTrue((run/'local-stage-seal.json').is_file())
                    checked.add(handle)
                if FakeNumericWorker.last_control:
                    auxiliary = run/'seals'/(handle+'-R-'+FakeNumericWorker.last_control+'.npz.json')
                    if auxiliary not in checked_auxiliary:
                        self.assertTrue(auxiliary.is_file(), 'R must be sealed before its first evaluation')
                        checked_auxiliary.add(auxiliary)
                elif FakeNumericWorker.last_observed:
                    auxiliary=run/'seals'/(handle+'-observed-local0.npz.json')
                    if auxiliary not in checked_auxiliary:
                        self.assertTrue(auxiliary.is_file(),'O must be sealed before its first evaluation')
                        checked_auxiliary.add(auxiliary)
                return original_evaluate(scores, report, failed)

            def after_local_choice(worker, local, graphs, configs):
                if graphs.ndim == 2 and len(configs) == 9 and not np.all(local == 1):
                    self.assertTrue((run/'local-selection.json').is_file())
                    self.assertTrue((run/'observed-execution-plan.json').is_file())
                return original_rank(worker, local, graphs, configs)

            with patch.object(campaign, 'NumericWorker', FakeNumericWorker), \
                    patch.object(campaign, 'evaluate', after_seal), \
                    patch.object(FakeNumericWorker, 'rank', after_local_choice):
                campaign.smoke_or_full(run, audit, 'full', topology, contract)
            output = json.loads((run/'c1-results.json').read_text(encoding='utf-8'))
            self.assertEqual(output['planned_cases'], 30)
            self.assertEqual(len(output['cases']), 30)
            self.assertEqual(len(checked), 30)
            self.assertAlmostEqual(output['summary']['R']['rr'], 2/3)
            self.assertAlmostEqual(output['summary']['Rdiffusion']['rr'], 2/3)
            for record in output['cases'].values():
                for control in record['R_all_configs'].values():
                    self.assertEqual(control['planned_draws'], 256)
                    self.assertEqual(control['failed_draws'], 0)
            baro = [cfg for cfg in FakeNumericWorker.calls if cfg.get('temporal') == 'max']
            self.assertEqual(len(baro), 30)
            self.assertTrue(all(cfg['pool'] == 'max' and cfg['fusion'] == 'max' for cfg in baro))
            self.assertTrue(all(cfg['received_types'] == [0]*10 for cfg in baro))
            self.assertTrue(all(call['rank_config_count'] == 0 for call in FakeNumericWorker.calls))
            observed_calls=[call for call in FakeNumericWorker.rank_calls
                            if call['graph_dimensions']==2 and len(call['configs'])==9
                            and not np.all(call['local']==1)]
            self.assertEqual(len(observed_calls), 30, 'All tied L choices need one theta, not 8 x 9 O')
            observed_plan=json.loads((run/'observed-execution-plan.json').read_text(encoding='utf-8'))
            self.assertEqual([v['local_index'] for v in observed_plan['ordered_requests']], [0])
            self.assertEqual(output['selection']['leave_cell_winner_counts']['selected_local_index'], {'0': 10})
            self.assertEqual(len(output['selection']['leave_cell_reselection']), 10)
            self.assertTrue(all(len(record['selection']['local_oof_mrr']) == 8
                                and len(record['selection']['observed_oof_mrr']) == 9
                                for record in output['selection']['leave_cell_reselection']))
            for case in DEV_IDS:
                handle = opaque_handle(case)
                self.assertTrue((run/'seals'/(handle+'-comparators.npz.json')).is_file())
                with np.load(run/'predictions'/(handle+'.npz'), allow_pickle=False) as saved:
                    self.assertTrue({'identity_local', 'identity_diffusion', 'channel_masks',
                        'centers', 'scales', 'reference_valid_bins', 'query_valid_bins',
                        'numerical_channel_failures'}.issubset(saved.files))
                with np.load(run/'intermediates'/(handle+'-uniform.npz'), allow_pickle=False) as saved:
                    self.assertFalse(saved['reachability'].any())
                self.assertEqual(output['resources_seconds'][case][
                    'aggregate_loader_audit_all_C1_C5_profiles_and_RCD_input_seconds'], .01)
                with self.assertRaises(FileExistsError):
                    campaign.seal_auxiliary(run, handle+'-comparators.npz', {'baro': [0.]})
            # Bernoulli mixture of RR1 and RR1/3: unbiased variance=(1/9)*256/255.
            expected_sd = np.sqrt((1/9)*256/255)
            expected_se = np.sqrt((1/9)*256/255)/np.sqrt(256*30)
            for label in ('primary', 'secondary_diffusion'):
                result = output['aggregate_R_monte_carlo'][label]['rr']
                self.assertAlmostEqual(result['independent_case_variance_aggregate_se'], expected_se)
                # Mock draws coincide across cases deliberately; realized SD differs
                # from the independence-based variance estimate and both are retained.
                self.assertAlmostEqual(result['measured_aggregate_draw_sd'], expected_sd)
                self.assertAlmostEqual(result['measured_aggregate_mean_se'], expected_sd/16)

    def test_shared_input_failure_remains_in_all_thirty_denominators(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            run = base/'run'
            audit, topology, contract = fixture_roster(base, failed={(DEV_IDS[0], 'primary')})
            with patch.object(campaign, 'NumericWorker', FakeNumericWorker):
                campaign.smoke_or_full(run, audit, 'full', topology, contract)
            output = json.loads((run/'c1-results.json').read_text(encoding='utf-8'))
            self.assertEqual(set(output['cases']), set(DEV_IDS))
            failed = output['cases'][DEV_IDS[0]]
            self.assertEqual(failed['status'], 'SHARED_INPUT_FAILURE')
            for arm in ('L', 'O', 'R', 'diffusion', 'Rdiffusion', 'BARO', 'Local_MAX_MT'):
                self.assertEqual(failed[arm]['rr'], 0.)
            self.assertAlmostEqual(output['summary']['L']['rr'], 29/30)
            self.assertAlmostEqual(output['summary']['R']['rr'], (29/30)*(2/3))
            self.assertTrue(all(control['failed_draws'] == 256
                                for control in failed['R_all_configs'].values()))
            self.assertAlmostEqual(output['selection']['local_oof_mrr']['0'], 29/30)

    def test_identity_L_and_empty_graph_O_keep_same_rounded_near_ties(self):
        class NearTie(FakeNumericWorker):
            def c1(self, *args, **kwargs):
                result = super().c1(*args, **kwargs)
                local = np.array([1e12, 1e12+.1, 0.])
                result['evidence']['local'] = local
                for ranking in result['rankings']:
                    ranking['scores'] = local/local.sum()
                return result

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            audit, topology, contract = fixture_roster(base)
            with patch.object(campaign, 'NumericWorker', NearTie):
                campaign.smoke_or_full(base/'run', audit, 'full', topology, contract)
            output = json.loads((base/'run'/'c1-results.json').read_text(encoding='utf-8'))
            # Both positive normalized masses round to .5: E[1/r] across ranks1,2=.75.
            # Raw evidence would instead put the root second and yield .5.
            self.assertAlmostEqual(output['summary']['L']['rr'], .75)
            self.assertAlmostEqual(output['summary']['O']['rr'], .75)
            self.assertEqual(output['O_minus_L']['mean'], 0.)

    def test_empty_candidate_set_is_retained_as_root_absent_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            audit, topology, contract = fixture_roster(base, empty_cases={DEV_IDS[0]})
            with patch.object(campaign, 'NumericWorker', FakeNumericWorker):
                campaign.smoke_or_full(base/'run', audit, 'full', topology, contract)
            output = json.loads((base/'run'/'c1-results.json').read_text(encoding='utf-8'))
            empty = output['cases'][DEV_IDS[0]]
            self.assertEqual(len(output['cases']), 30)
            self.assertEqual(empty['L']['status'], 'ROOT_ABSENT')
            self.assertEqual(empty['L']['rr'], 0.)
            self.assertEqual(empty['R']['rr'], 0.)
            self.assertTrue(empty['local_all_tie'])
            self.assertTrue(empty['all_zero'])
            self.assertTrue(empty['empty_candidate_set'])
            self.assertEqual(empty['local_participating_services'], 0)
            self.assertAlmostEqual(output['summary']['L']['rr'], 29/30)

    def test_BARO_numeric_failure_stops_instead_of_becoming_a_zero_baseline(self):
        class FailedBaro(FakeNumericWorker):
            def c1(self, *args, **kwargs):
                result = super().c1(*args, **kwargs)
                config = args[4]
                if config.get('temporal') == 'max':
                    result['evidence']['diagnostics']['numerical_channel_failures'][0, 0] = True
                return result

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            audit, topology, contract = fixture_roster(base)
            with patch.object(campaign, 'NumericWorker', FailedBaro), \
                    self.assertRaisesRegex(RuntimeError, 'BARO numerical'):
                campaign.smoke_or_full(base/'run', audit, 'full', topology, contract)
            self.assertFalse((base/'run'/'c1-results.json').exists())

    def test_smoke_uses_predetermined_ten_and_never_evaluates(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            audit, topology, contract = fixture_roster(base)
            with patch.object(campaign, 'NumericWorker', FakeNumericWorker), \
                    patch.object(campaign, 'evaluate', side_effect=AssertionError('Smoke opened labels')):
                campaign.smoke_or_full(base/'run', audit, 'smoke', topology, contract)
            output = json.loads((base/'run'/'smoke-report.json').read_text(encoding='utf-8'))
            self.assertEqual(output['predetermined_ids'], campaign.registry()['smoke_ids'])
            self.assertEqual(output['case_count'], 10)
            self.assertEqual(output['fixed_feasibility_local_index'], 0)
            self.assertEqual(len(FakeNumericWorker.calls), 10)
            self.assertTrue(all(call['rank_config_count']==0 for call in FakeNumericWorker.calls))
            self.assertFalse((base/'run'/'selection.json').exists())

    def test_bundle_requires_both_contract_pin_and_loader_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            audit, _, contract = fixture_roster(base)
            handle = opaque_handle(DEV_IDS[0])
            numeric = audit/'intermediates'/handle/'c1_primary.npz'
            campaign.load_bundle(audit, handle, 'primary', contract)
            with self.assertRaisesRegex(RuntimeError, 'Unpinned'):
                campaign.load_bundle(audit, handle, 'primary', {'inputs': []})
            numeric.write_bytes(b'changed bytes, never opened as an array')
            with self.assertRaisesRegex(RuntimeError, 'Unpinned or changed'):
                campaign.load_bundle(audit, handle, 'primary', contract)
            for record in contract['inputs']:
                if Path(record['path']) == numeric:
                    record['sha256'] = file_sha(numeric)
            with self.assertRaisesRegex(RuntimeError, 'loader receipt'):
                campaign.load_bundle(audit, handle, 'primary', contract)


class SensitivityTests(unittest.TestCase):
    def test_numerical_failure_preserves_receipt_and_stops_sensitivity(self):
        class Broken(FakeNumericWorker):
            def c1(self, *args, **kwargs):
                result = super().c1(*args, **kwargs)
                result['evidence']['diagnostics']['numerical_channel_failures'][0, 0] = True
                return result

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            audit, _, contract = fixture_roster(base, profiles=('primary', 'bin5'))
            selected = base/'selected.json'
            save_json(selected, {'local_config': {'floor': .01, 'pool': 'max', 'fusion': 'max'},
                                 'ppr_config': {'operator': 'ppr', 'direction': 'reverse', 'damping': .85}})
            contract['inputs'].append({'path': str(selected), 'sha256': file_sha(selected)})
            run = base/'run'
            run.mkdir()
            with patch.object(campaign, 'NumericWorker', Broken), \
                    self.assertRaisesRegex(RuntimeError, 'sensitivity numerical'):
                campaign.sensitivity(run, audit, selected, contract)
            receipt = json.loads((run/'failures.jsonl').read_text(encoding='utf-8'))
            self.assertEqual(receipt['case'], DEV_IDS[0])
            self.assertEqual(receipt['stage'], 'bin5')
            self.assertFalse((run/'c1-sensitivity.json').exists())

    def test_full_ofat_registry_signed_effects_profile_names_and_failure_denominator(self):
        class NegativeGraph(FakeNumericWorker):
            def c1(self, *args, **kwargs):
                result = super().c1(*args, **kwargs)
                for ranking in result['rankings']:
                    ranking['scores'] = np.array([1., 2., 3.])/6
                return result

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            profiles = ('primary', 'bin5', 'bin20', 'horizon180', 'horizon420')
            audit, _, contract = fixture_roster(base, profiles=profiles,
                failed={(DEV_IDS[0], 'bin20')}, alternate_names={'bin5'})
            chosen = {'local_config': {'floor': .01, 'pool': 'max', 'fusion': 'max'},
                      'ppr_config': {'operator': 'ppr', 'direction': 'reverse', 'damping': .85}}
            selected = base/'selected.json'
            save_json(selected, chosen)
            contract['inputs'].append({'path': str(selected), 'sha256': file_sha(selected)})
            with patch.object(campaign, 'NumericWorker', NegativeGraph):
                campaign.sensitivity(base/'run', audit, selected, contract)
            output = json.loads((base/'run'/'c1-sensitivity.json').read_text(encoding='utf-8'))
            variants = output['variants']
            self.assertEqual(set(variants), {'bin5', 'bin20', 'horizon180', 'horizon420',
                'floor-0.0001', 'floor-0.001', 'temporal-max', 'old-cap20', 'old-fixed-fusion'})
            self.assertTrue(all(set(v['cases']) == set(DEV_IDS) for v in variants.values()))
            self.assertEqual(variants['bin5']['L']['rr'], .5)
            self.assertEqual(variants['bin5']['effect']['mean'], 0.)
            self.assertAlmostEqual(variants['bin20']['L']['rr'], 29/30)
            self.assertAlmostEqual(variants['bin20']['effect']['mean'], -(29/30)*(2/3))
            self.assertAlmostEqual(variants['temporal-max']['effect']['mean'], -2/3)
            self.assertEqual(set(variants['temporal-max']['effect']['groups']), {'root', 'fault', 'cell'})
            self.assertEqual(json.loads(selected.read_text(encoding='utf-8')), chosen)
            for variant, result in variants.items():
                for case, record in result['cases'].items():
                    if record.get('status') != 'SHARED_INPUT_FAILURE':
                        self.assertTrue((base/'run'/'seals'/(variant+'-'+opaque_handle(case)+'.npz.json')).is_file())
                        self.assertEqual(record['quality']['valid_metric_multiplicity'], [10, 10, 10])
                        self.assertTrue(np.all(record['quality']['constant_channels']))
                        self.assertTrue(np.all(record['quality']['floor_used_channels']))
                        with np.load(base/'run'/'predictions'/variant/(opaque_handle(case)+'.npz'),
                                     allow_pickle=False) as saved:
                            self.assertTrue({'channel_scores', 'channel_masks', 'local_mask', 'centers',
                                'scales', 'reference_valid_bins', 'query_valid_bins'}.issubset(saved.files))


class PrecisionTests(unittest.TestCase):
    def test_bootstrap_preserves_all_three_repeats_as_one_cell(self):
        outcomes = {}
        for case in DEV_IDS:
            _, root, fault, repeat = case.split('_')
            observed = int(repeat)/4
            outcomes[case] = {'cell': [root, fault], 'O': {'rr': observed},
                              'L': {'rr': .25}, 'R': {'rr': observed-.125}}
        result = campaign.development_precision(outcomes)
        self.assertEqual(result['development_cells'], 10)
        self.assertEqual(result['bootstrap_draws'], 50000)
        # Each cell's O-L is .25 although incident effects vary 0/.25/.5.
        # Resampling individual incidents would spuriously widen this interval.
        for name, expected in (('O-L', .25), ('O-R', .125)):
            contrast = result['contrasts'][name]
            self.assertEqual(contrast['mean'], expected)
            np.testing.assert_array_equal(contrast['conditional_97_5pct_interval'], [expected, expected])
            self.assertEqual(contrast['sd_paired_cells'], 0.)
            self.assertEqual(contrast['optimistic_effect_for_80pct_individual_power_20cell_plan'], .05)


if __name__ == '__main__':
    output = Path(sys.argv[1])
    require_contract(output, 'development')
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    save_json(output/'c1-controller-fixture-report.json', {
        'tests_run': result.testsRun,
        'failures': [{'test': str(t), 'traceback': e} for t, e in result.failures],
        'errors': [{'test': str(t), 'traceback': e} for t, e in result.errors],
        'seconds': time.perf_counter()-started,
        'scope': 'Synthetic controller and arithmetic expectations; no raw data, child model process or outcomes'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
