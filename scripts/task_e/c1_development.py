"""Trusted C1 development controller. Numeric child never receives evaluation data."""
from __future__ import annotations
import argparse
import itertools
import json
import sys
import time
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W))
from scripts.task_e.boundary import NumericWorker
from scripts.task_e.contract import DEV_IDS, FOLDS, opaque_handle, registry
from scripts.task_e.execution import save_json,save_npz,require_contract,file_sha,failure
from scripts.task_e.evaluator import tie_metrics
from scripts.task_e.calibration import mean_planned_draw_metrics,select_registered

METRICS=('rr','hit1','hit3','hit5','ndcg5')
LOCAL=[{'floor':floor,'pool':pool,'fusion':fusion} for pool,fusion,floor in
       itertools.product(('max','q90'),('max','availablemean'),(.01,.001))]
RANKS=[{'operator':'ppr','direction':direction,'damping':d} for direction,d in
       itertools.product(('reverse','undirected'),(.85,.5,.2))]+[
       {'operator':'diffusion','direction':'undirected','damping':d} for d in (.85,.5,.2)]


def read_pinned(path,contract):
    path=Path(path).resolve()
    records={str(Path(x['path']).resolve()):x['sha256'] for x in contract['inputs']}
    if records.get(str(path))!=file_sha(path):
        raise RuntimeError('Unpinned or changed actual input: '+str(path))
    return path


def load_bundle(audit,handle,profile,contract):
    path=read_pinned(audit/'intermediates'/handle/('c1_'+profile+'.npz'),contract)
    report=json.loads(read_pinned(audit/'case-audits'/(handle+'.json'),contract).read_text(encoding='utf-8'))
    if report.get('handle')!=handle:
        raise RuntimeError('Case handle mismatch')
    entries=[x for x in report['numeric_files'] if Path(x['path']).resolve()==path]
    if len(entries)!=1 or entries[0]['sha256']!=file_sha(path):
        raise RuntimeError('Numeric bytes do not match loader receipt')
    with np.load(path,allow_pickle=False) as data:
        return {k:data[k].copy() for k in data.files}


def mean_metrics(cases):
    return {k:float(np.mean([v[k] for v in cases.values()])) for k in METRICS}


def evidence_quality(evidence,bundle):
    valid=evidence['masks']['channels'];constants=np.zeros(valid.shape,dtype=bool);floors=constants.copy()
    for i,j in np.argwhere(valid):
        a=bundle['ref'][i,j];a=a[np.isfinite(a)]
        constants[i,j]=bool(np.all(a==a[0]))
        iqr=float(np.quantile(a,.75,method='linear')-np.quantile(a,.25,method='linear'))
        floors[i,j]=evidence['diagnostics']['scales'][i,j]>iqr
    scores=evidence['channel_scores'][valid]
    return {'constant_channels':constants,'floor_used_channels':floors,
            'valid_channels_per_service':valid.sum(axis=1),'valid_metric_multiplicity':valid[:,:10].sum(axis=1),
            'channel_score_quantiles_50_90_99_max':np.quantile(scores,[.5,.9,.99,1.],method='linear') if scores.size else [],
            'unavailable_services':int((~evidence['masks']['local']).sum())}


def evaluate(scores,report,failed=False):
    names=report['profiles']['c1_primary'].get('service_names',[])
    root=report['metadata']['root_cause_service']
    index=names.index(root) if root in names else None
    return tie_metrics(scores,index,failed=failed)


def seal_auxiliary(run,relative,arrays):
    path=run/'predictions'/relative
    save_npz(path,**arrays)
    save_json(run/'seals'/(relative.replace('/','-')+'.json'),
              {'file':str(path),'sha256':file_sha(path),'before_evaluation':True})


def planned_failure(report):
    zero=tie_metrics([],None,failed=True)
    return {'cell':[report['metadata']['root_cause_service'],report['metadata']['fault']],
            'local':[dict(zero) for _ in LOCAL],
            'observed':{},
            'status':'SHARED_INPUT_FAILURE'}


def forecast_free_predictions(worker,bundle,configs=LOCAL):
    """Local-only stage: no observed graph ranking before L chooses theta."""
    results=[]
    for config in configs:
        result=worker.c1(bundle['ref'],bundle['query'],bundle['adj'],bundle['channel_types'],config)
        if np.any(result['evidence']['diagnostics']['numerical_channel_failures']):
            raise RuntimeError('C1 local numerical channel failure')
        identity=worker.rank(result['evidence']['local'],np.zeros_like(bundle['adj']),[
            {'operator':'ppr','direction':'reverse','damping':.85},
            {'operator':'diffusion','direction':'undirected','damping':.85}])['rankings']
        result['identity_local']=identity[0]['scores']
        result['identity_diffusion']=identity[1]['scores']
        result['identity_max_solver_residual']=max(item['diagnostics']['residual_inf'] for item in identity)
        results.append(result)
    return results


def local_selection(cases):
    ids=list(cases)
    local_curves={j:float(np.mean([cases[i]['local'][j]['rr'] for i in ids])) for j in range(8)}
    chosen=select_registered(local_curves,list(range(8)),maximize=True)
    ordered=sorted(local_curves.values(),reverse=True)
    return {'selected_local_index':chosen,'local_config':LOCAL[chosen],
            'local_oof_mrr':local_curves,'local_margin':ordered[0]-ordered[1]}


def selection(cases):
    ids=list(cases)
    local=local_selection(cases)
    chosen=local['selected_local_index'];local_curves=local['local_oof_mrr']
    graph_curves={j:float(np.mean([cases[i]['observed'][chosen][j]['rr'] for i in ids])) for j in range(9)}
    ppr=select_registered({j:graph_curves[j] for j in range(6)},list(range(6)),maximize=True)
    diffusion=select_registered({j:graph_curves[j] for j in range(6,9)},list(range(6,9)),maximize=True)
    folds=[]
    for number,cells in enumerate(FOLDS):
        held=[i for i in ids if tuple(cases[i]['cell']) in cells]
        folds.append({'fold':number+1,'heldout_ids':held,
                      'local_curves':{j:float(np.mean([cases[i]['local'][j]['rr'] for i in held])) for j in range(8)} if held else {},
                      'observed_curves':{j:float(np.mean([cases[i]['observed'][chosen][j]['rr'] for i in held])) for j in range(9)} if held else {}})
    ordered_o=sorted([graph_curves[j] for j in range(6)],reverse=True)
    ordered_d=sorted([graph_curves[j] for j in range(6,9)],reverse=True)
    return {'selected_local_index':chosen,'selected_ppr_index':ppr,'selected_diffusion_index':diffusion,
            'local_config':LOCAL[chosen],'ppr_config':RANKS[ppr],'diffusion_config':RANKS[diffusion],
            'local_oof_mrr':local_curves,'observed_oof_mrr':graph_curves,'folds':folds,
            'local_margin':local['local_margin'],'ppr_margin':ordered_o[0]-ordered_o[1],
            'diffusion_margin':ordered_d[0]-ordered_d[1],
            'objective':'absolute L-MRR then absolute O-MRR; OOF case models have no cross-case fitting',
            'selection_not_unbiased_evaluation':True}


def subgroup_effects(cases,left,right):
    effects={i:cases[i][left]['rr']-cases[i][right]['rr'] for i in cases}
    groups={}
    for dimension,position in (('root',0),('fault',1),('cell',None)):
        labels={str(v['cell'] if position is None else v['cell'][position]) for v in cases.values()}
        groups[dimension]={}
        for label in sorted(labels):
            included=[i for i,v in cases.items() if str(v['cell'] if position is None else v['cell'][position])==label]
            other=[i for i in cases if i not in included]
            groups[dimension][label]={'cases':included,'effect':float(np.mean([effects[i] for i in included])),
                                     'leaveout_effect':float(np.mean([effects[i] for i in other])) if other else None}
    return {'case_effects':effects,'mean':float(np.mean(list(effects.values()))),'groups':groups}


def observed_request_plan(local_plans):
    """Sparse O demand from already recorded L decisions; no O scores admitted."""
    requests={}
    for plan in local_plans:
        theta=plan['selected_local_index']
        for case in plan['planned_cases']:
            requests.setdefault(theta,{}).setdefault(case,[]).append(
                {'scope':plan['scope'],**({'omitted_cell':plan['omitted_cell']} if 'omitted_cell' in plan else {})})
    primary=local_plans[0]['selected_local_index']
    return requests,[primary]+sorted(set(requests)-{primary})


def smoke_or_full(run,audit,mode,topology,contract):
    ids=registry()['smoke_ids'] if mode=='smoke' else list(DEV_IDS)
    raw_results={};evaluations={};resources={};observed_seconds={i:0. for i in ids}
    with NumericWorker(timeout_seconds=300) as worker:
        save_json(run/'worker-isolation.json',worker.ping())
        for index,case in enumerate(ids):
            handle=opaque_handle(case);start=time.perf_counter()
            report=json.loads(read_pinned(audit/'case-audits'/(handle+'.json'),contract).read_text(encoding='utf-8'))
            if report.get('handle')!=handle or report.get('case')!=case:
                raise RuntimeError('Wrong case audit identity')
            if report.get('profiles',{}).get('c1_primary',{}).get('status')!='MATERIALIZED':
                raw_results[case]=(None,report,None)
                evaluations[case]=planned_failure(report)
                save_json(run/'input-failures'/(handle+'.json'),evaluations[case])
                resources[case]=time.perf_counter()-start
                continue
            try:
                bundle=load_bundle(audit,handle,'primary',contract)
                local_configs=LOCAL[:1] if mode=='smoke' else LOCAL
                results=forecast_free_predictions(worker,bundle,local_configs)
                arrays={'local':np.stack([r['evidence']['local'] for r in results]),
                        'identity_local':np.stack([r['identity_local'] for r in results]),
                        'identity_diffusion':np.stack([r['identity_diffusion'] for r in results]),
                        'metric_blocks':np.stack([r['evidence']['blocks']['metric'] for r in results]),
                        'trace_blocks':np.stack([r['evidence']['blocks']['trace'] for r in results]),
                        'masks':np.stack([r['evidence']['masks']['local'] for r in results]),
                        'channel_scores':np.stack([r['evidence']['channel_scores'] for r in results])}
                for field in ('centers','scales','reference_valid_bins','query_valid_bins','numerical_channel_failures'):
                    arrays[field]=np.stack([r['evidence']['diagnostics'][field] for r in results])
                arrays['channel_masks']=np.stack([r['evidence']['masks']['channels'] for r in results])
                arrays['block_masks']=np.array([[r['evidence']['masks']['blocks'][kind] for kind in ('metric','trace','log')] for r in results])
                save_json(run/'quality'/(handle+'.json'),{'channel_reasons':[r['evidence']['diagnostics']['channel_reasons'] for r in results],
                    'variants':[evidence_quality(r['evidence'],bundle) for r in results],
                    'selected_windows_from_loader':report['profiles']['c1_primary']['audit'],
                    'channel_types':bundle['channel_types']})
                path=run/'predictions'/(handle+'.npz');save_npz(path,**arrays)
                seal={'file':str(path),'sha256':file_sha(path),'before_evaluation':True,
                      'nodes':len(bundle['adj']),'edges':int(bundle['adj'].sum()),
                      'local_configs':local_configs,'stage':'LOCAL_EVIDENCE_AND_IDENTITY_ONLY',
                      'max_solver_residual':max(r['identity_max_solver_residual'] for r in results)}
                save_json(run/'seals'/(handle+'.json'),seal)
                raw_results[case]=(arrays,report,bundle)
                if mode=='smoke':
                    # Predetermined feasibility setting, never chosen using outcomes.
                    ranked=worker.rank(arrays['local'][0],bundle['adj'],RANKS)['rankings']
                    seal_auxiliary(run,handle+'-smoke-observed.npz',
                                   {'scores':np.array([item['scores'] for item in ranked])})
            except Exception as exc:
                failure(run,mode,case,exc)
                raise  # invalid implementation is fixed, never an apparent method loser
            resources[case]=time.perf_counter()-start
            print(f'C1 {mode} {index+1}/{len(ids)} {handle} {resources[case]:.2f}s',flush=True)
        if mode=='smoke':
            save_json(run/'smoke-report.json',{'status':'PASS','predetermined_ids':ids,'no_method_selection':True,
                      'resources_seconds':resources,'case_count':len(raw_results),
                      'fixed_feasibility_local_index':0,'fixed_feasibility_local_config':LOCAL[0],
                      'rank_configs':RANKS,
                      'input_failure_cases':[i for i,(a,_,_) in raw_results.items() if a is None]})
            return

        # Seal the entire L roster before evaluating the eight local variants.
        save_json(run/'local-stage-seal.json',{'before_evaluation':True,'planned_cases':ids,
            'entries':[{'case':case,'path':str(run/('input-failures' if raw_results[case][0] is None else 'seals')/(opaque_handle(case)+'.json')),
                        'sha256':file_sha(run/('input-failures' if raw_results[case][0] is None else 'seals')/(opaque_handle(case)+'.json'))}
                       for case in ids]})
        for case in ids:
            arrays,report,_=raw_results[case]
            if arrays is not None:
                evaluations[case]={'cell':[report['metadata']['root_cause_service'],report['metadata']['fault']],
                    'local':[evaluate(v,report) for v in arrays['identity_local']],'observed':{}}
        primary_local=local_selection(evaluations)
        local_plans=[{'scope':'primary','planned_cases':ids,**primary_local}]
        for cell in sorted({tuple(v['cell']) for v in evaluations.values()}):
            sub={i:v for i,v in evaluations.items() if tuple(v['cell'])!=cell}
            local_plans.append({'scope':'leave_cell','omitted_cell':cell,
                                'planned_cases':list(sub),**local_selection(sub)})
        save_json(run/'local-selection.json',{'objective':'absolute L-MRR only; no observed-graph outputs yet',
                                            'decisions':local_plans})
        # Demand is determined solely by the preceding L decisions. A deletion
        # may need another theta, but it never opens unrelated local x O cells.
        requests,theta_order=observed_request_plan(local_plans)
        save_json(run/'observed-execution-plan.json',{'source':'local-selection.json','rank_configs':RANKS,
            'ordered_requests':[{'local_index':theta,'cases':[{'case':case,'reasons':reasons}
                                for case,reasons in requests[theta].items()]} for theta in theta_order],
            'no_cartesian_search':True,'primary_before_conditional_leave_cell':True})
        for theta in theta_order:
            sealed_scores={}
            for case in requests[theta]:
                arrays,report,bundle=raw_results[case]
                if arrays is None:
                    zero=tie_metrics([],None,failed=True)
                    evaluations[case]['observed'][theta]=[dict(zero) for _ in RANKS]
                    continue
                start=time.perf_counter()
                try:
                    ranked=worker.rank(arrays['local'][theta],bundle['adj'],RANKS)['rankings']
                    scores=np.array([item['scores'] for item in ranked])
                    seal_auxiliary(run,opaque_handle(case)+f'-observed-local{theta}.npz',{'scores':scores})
                    sealed_scores[case]=scores
                except Exception as exc:
                    failure(run,f'observed-local{theta}',case,exc)
                    raise
                observed_seconds[case]+=time.perf_counter()-start
            # All requested O predictions for this theta exist before evaluation.
            for case,scores in sealed_scores.items():
                evaluations[case]['observed'][theta]=[evaluate(value,raw_results[case][1]) for value in scores]
        chosen=selection(evaluations)
        leave=[]
        for plan in local_plans[1:]:
            sub={i:evaluations[i] for i in plan['planned_cases']}
            leave.append({'omitted_cell':plan['omitted_cell'],'selection':selection(sub)})
        chosen['leave_cell_reselection']=leave
        chosen['leave_cell_winner_counts']={field:{str(k):sum(item['selection'][field]==k for item in leave)
            for k in sorted({item['selection'][field] for item in leave})}
            for field in ('selected_local_index','selected_ppr_index','selected_diffusion_index')}
        save_json(run/'selection.json',chosen)
        j=chosen['selected_local_index'];p=chosen['selected_ppr_index'];d=chosen['selected_diffusion_index']
        outcomes={}
        for case in ids:
            controls_start=time.perf_counter()
            handle=opaque_handle(case);arrays,report,bundle=raw_results[case]
            if arrays is None:
                zero=tie_metrics([],None,failed=True)
                controls={k:mean_planned_draw_metrics({i:None for i in range(256)}) for k in range(9)}
                outcomes[case]={'cell':evaluations[case]['cell'],
                    **{arm:dict(zero) for arm in ('L','O','R','Ldiffusion','diffusion','Rdiffusion','BARO','Local_MAX_MT')},
                    'R_all_configs':controls,'status':'SHARED_INPUT_FAILURE','local_all_tie':True,
                    'R_draw_metrics':{k:[[0.]*len(METRICS) for _ in range(256)] for k in range(9)},
                    'all_zero':True,'local_participating_services':0}
                save_json(run/'case-results'/(handle+'.json'),outcomes[case])
                continue
            local=arrays['local'][j]
            # BARO is a declared separate metric-only temporal-MAX adaptation.
            baro=worker.c1(bundle['ref'][:,:10],bundle['query'][:,:10],bundle['adj'],bundle['channel_types'][:10],
                           {'floor':chosen['local_config']['floor'],'pool':'max','fusion':'max','temporal':'max'})
            if np.any(baro['evidence']['diagnostics']['numerical_channel_failures']):
                raise RuntimeError('BARO numerical channel failure; preserve and review')
            maxmt=np.maximum(arrays['metric_blocks'][j],arrays['trace_blocks'][j])
            seal_auxiliary(run,handle+'-comparators.npz',{'baro':baro['evidence']['local'],'local_max_mt':maxmt})
            controls={};draw_metric_arrays={}
            for representation in ('directed','undirected'):
                path=read_pinned(topology/'topology'/handle/representation/'200'/'graphs.npz',contract)
                with np.load(path,allow_pickle=False) as saved: graphs=saved['graphs']
                configurations=RANKS[:3] if representation=='directed' else RANKS[3:]
                scored=worker.rank(local,graphs,configurations)['rankings']
                score_array=np.array([[r['scores'] for r in draw] for draw in scored])
                seal_auxiliary(run,handle+'-R-'+representation+'.npz',{'scores':score_array})
                for offset,config in enumerate(configurations):
                    configid=(0 if representation=='directed' else 3)+offset
                    draws={draw:evaluate(score_array[draw,offset],report) for draw in range(256)}
                    controls[configid]=mean_planned_draw_metrics(draws)
                    draw_metric_arrays[configid]=[[draws[draw][metric] for metric in METRICS] for draw in range(256)]
            uniform=worker.rank(np.ones(len(local)),bundle['adj'],RANKS)['rankings']
            reach=bundle['adj'].copy()
            for k in range(len(reach)):
                reach |= reach[:,k,None] & reach[None,k,:]
            save_npz(run/'intermediates'/(handle+'-uniform.npz'),scores=np.array([r['scores'] for r in uniform]),
                     in_degree=bundle['adj'].sum(axis=0),out_degree=bundle['adj'].sum(axis=1),reachability=reach)
            outcome={'cell':evaluations[case]['cell'],'L':evaluations[case]['local'][j],
                     'O':evaluations[case]['observed'][j][p],'diffusion':evaluations[case]['observed'][j][d],
                     'Ldiffusion':evaluate(arrays['identity_diffusion'][j],report),
                     'R':controls[p]['metrics'],'Rdiffusion':controls[d]['metrics'], 'R_all_configs':controls,
                     'R_draw_metrics':draw_metric_arrays,
                     'BARO':evaluate(baro['evidence']['local'],report),'Local_MAX_MT':evaluate(maxmt,report),
                     'local_all_tie':len(set(round(float(x),12) for x in (local/local.max() if len(local) and local.max()>0 else local)))<=1,
                     'empty_candidate_set':len(local)==0,
                     'all_zero':not np.any(local),'local_participating_services':int(arrays['masks'][j].sum())}
            outcomes[case]=outcome
            resources[case]={'local_evidence_identity_seconds':resources[case],
                             'observed_requested_configurations_seconds':observed_seconds[case],
                             'observed_requested_local_indices':[theta for theta in theta_order if case in requests[theta]],
                             'selected_control_comparator_diagnostics_seconds':time.perf_counter()-controls_start,
                             'aggregate_loader_audit_all_C1_C5_profiles_and_RCD_input_seconds':report['seconds']}
            save_json(run/'case-results'/(handle+'.json'),outcome)
            print('C1 controls '+handle,flush=True)
        summary={arm:mean_metrics({i:v[arm] for i,v in outcomes.items()}) for arm in
                 ('L','O','R','Ldiffusion','diffusion','Rdiffusion','BARO','Local_MAX_MT')}
        mc={}
        for label,configid in (('primary',p),('secondary_diffusion',d)):
            aggregate_draws=np.mean([v['R_draw_metrics'][configid] for v in outcomes.values()],axis=0)
            mc[label]={metric:{'measured_aggregate_draw_sd':float(np.std(aggregate_draws[:,k],ddof=1)),
                'measured_aggregate_mean_se':float(np.std(aggregate_draws[:,k],ddof=1)/16),
                'independent_case_variance_aggregate_se':float(np.sqrt(sum(v['R_all_configs'][configid]['mc'][metric]['se']**2 for v in outcomes.values()))/30),
                'interpretation':'conditional finite random-chain variation on fixed30cases; not incident uncertainty or mixing proof'} for k,metric in enumerate(METRICS)}
        precision=development_precision(outcomes)
        save_json(run/'c1-results.json',{'scope':'DEVELOPMENT30 not final evaluation','planned_cases':30,
                    'selection':chosen,'summary':summary,'cases':outcomes,
                    'O_minus_L':subgroup_effects(outcomes,'O','L'),'O_minus_R':subgroup_effects(outcomes,'O','R'),
                    'resources_seconds':resources,'aggregate_R_monte_carlo':mc,'development_precision':precision,
                    'all_registered_local_and_O_curves':evaluations})


def sensitivity(run,audit,selected,contract):
    chosen=json.loads(read_pinned(selected,contract).read_text(encoding='utf-8'))
    base=chosen['local_config'];rank=chosen['ppr_config']
    variants=[(p,{},p) for p in ('bin5','bin20','horizon180','horizon420')]
    variants += [(f'floor-{floor}',{'floor':floor},'primary') for floor in (.0001,.001,.01) if floor!=base['floor']]
    variants += [('temporal-max',{'temporal':'max'},'primary'),('old-cap20',{'cap':20},'primary'),
                 ('old-fixed-fusion',{},'primary')]
    reports={}
    with NumericWorker(timeout_seconds=300) as worker:
        for name,change,profile in variants:
            cases={};start=time.perf_counter()
            for case in DEV_IDS:
                handle=opaque_handle(case)
                report=json.loads(read_pinned(audit/'case-audits'/(handle+'.json'),contract).read_text(encoding='utf-8'))
                if report.get('handle')!=handle or report.get('case')!=case:
                    raise RuntimeError('Wrong case audit identity')
                if report.get('profiles',{}).get('c1_'+profile,{}).get('status')!='MATERIALIZED':
                    zero=tie_metrics([],None,failed=True)
                    cases[case]={'cell':[report['metadata']['root_cause_service'],report['metadata']['fault']],
                                 'L':dict(zero),'O':dict(zero),'available_services':0,'status':'SHARED_INPUT_FAILURE'}
                    continue
                bundle=load_bundle(audit,handle,profile,contract)
                result=worker.c1(bundle['ref'],bundle['query'],bundle['adj'],bundle['channel_types'],{**base,**change},[rank])
                if np.any(result['evidence']['diagnostics']['numerical_channel_failures']):
                    exc=RuntimeError('C1 sensitivity numerical channel failure')
                    failure(run,name,case,exc)
                    raise exc
                local=result['evidence']['local'];observed=result['rankings'][0]['scores']
                if name=='old-fixed-fusion':
                    local=(result['evidence']['blocks']['metric']+result['evidence']['blocks']['trace'])/2
                    observed=worker.rank(local,bundle['adj'],[rank])['rankings'][0]['scores']
                identity=worker.rank(local,np.zeros_like(bundle['adj']),[rank])['rankings'][0]['scores']
                e=result['evidence']
                seal_auxiliary(run,name+'/'+handle+'.npz',{'local':local,'identity_local':identity,'observed':observed,
                    'channel_scores':e['channel_scores'],'channel_masks':e['masks']['channels'],'local_mask':e['masks']['local'],
                    'centers':e['diagnostics']['centers'],'scales':e['diagnostics']['scales'],
                    'reference_valid_bins':e['diagnostics']['reference_valid_bins'],'query_valid_bins':e['diagnostics']['query_valid_bins']})
                names=report['profiles']['c1_'+profile]['service_names'];root=report['metadata']['root_cause_service']
                rootid=names.index(root) if root in names else None
                cases[case]={'cell':[root,report['metadata']['fault']],'L':tie_metrics(identity,rootid),'O':tie_metrics(observed,rootid),
                             'available_services':int(result['evidence']['masks']['local'].sum()),
                             'quality':evidence_quality(result['evidence'],bundle)}
            reports[name]={'config':{**base,**change},'profile':profile,'cases':cases,
                           'L':mean_metrics({i:v['L'] for i,v in cases.items()}),
                           'O':mean_metrics({i:v['O'] for i,v in cases.items()}),
                           'effect':subgroup_effects(cases,'O','L'),'seconds':time.perf_counter()-start}
            print('C1 sensitivity '+name,flush=True)
    save_json(run/'c1-sensitivity.json',{'mode':'registered OFAT; primary unchanged','variants':reports,
              'R_sensitivity':'separate topology-only100/200/400E contract; no outcome-adaptive budget'})


def development_precision(outcomes):
    cells=sorted({tuple(v['cell']) for v in outcomes.values()})
    rng=np.random.Generator(np.random.PCG64(20260926))
    draws=rng.integers(len(cells),size=(50000,len(cells)))
    result={}
    for comparator in ('L','R'):
        values=np.array([np.mean([v['O']['rr']-v[comparator]['rr'] for v in outcomes.values() if tuple(v['cell'])==cell]) for cell in cells])
        estimates=values[draws].mean(axis=1)
        bounds=np.quantile(estimates,[.0125,.9875],method='linear')
        sd=float(np.std(values,ddof=1))
        result['O-'+comparator]={'paired_cell_values':values,'cells':cells,'mean':float(values.mean()),
              'conditional_97_5pct_interval':bounds,'sd_paired_cells':sd,
              'optimistic_effect_for_80pct_individual_power_20cell_plan':.05+(2.2414027276+.8416212336)*sd/np.sqrt(20),
              'interval_entirely_above_study_delta':bool(bounds[0]>.05)}
    return {'bootstrap_draws':50000,'seed':20260926,'development_cells':len(cells),'contrasts':result,
            'limitations':'Selection-exposed development diagnostics, not final confirmatory inference or independent campaigns; family2 nominal conditional intervals'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('run');parser.add_argument('mode',choices=['smoke','full','sensitivity'])
    parser.add_argument('--audit-root',required=True,type=Path);parser.add_argument('--topology-root',type=Path)
    parser.add_argument('--selection',type=Path);args=parser.parse_args()
    run=Path(args.run);contract=require_contract(run,'development')
    if args.mode=='sensitivity':sensitivity(run,args.audit_root,args.selection,contract)
    else:smoke_or_full(run,args.audit_root,args.mode,args.topology_root,contract)


if __name__=='__main__':main()
