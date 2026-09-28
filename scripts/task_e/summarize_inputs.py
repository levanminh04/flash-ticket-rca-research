"""Read-only aggregation of completed input receipts; no model predictions."""
import json
from pathlib import Path
import sys
import numpy as np
W=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(W))
from scripts.task_e.execution import save_json,require_contract,file_sha
from scripts.task_e.c1_development import read_pinned
from scripts.task_e.contract import DEV_IDS,opaque_handle


def main():
    run=Path(sys.argv[1]);audit=Path(sys.argv[2]);contract=require_contract(run,'development')
    cases=[]
    for case in DEV_IDS:
        handle=opaque_handle(case)
        r=json.loads(read_pinned(audit/'case-audits'/(handle+'.json'),contract).read_text(encoding='utf-8'))
        c1=r['profiles']['c1_primary'];c5=r['profiles']['c5_primary'];a=c1['audit']
        path=read_pinned(audit/'intermediates'/handle/'c1_primary.npz',contract)
        with np.load(path,allow_pickle=False) as z:
            ref=z['ref'];query=z['query'];adj=z['adj']
        eligible=(np.isfinite(ref).sum(axis=-1)>=24)&(np.isfinite(query).sum(axis=-1)>=24)
        eligible[:,10:] &= np.any(np.isfinite(ref[:,10:])&(ref[:,10:]>0),axis=-1)
        constants=np.zeros(eligible.shape,dtype=bool)
        for i,j in np.argwhere(eligible):
            vals=ref[i,j][np.isfinite(ref[i,j])]
            constants[i,j]=np.all(vals==vals[0])
        p=r['physical']['modalities']
        cases.append({'case':case,'handle':handle,'root_in_candidate':c1['root_in_candidate'],
            'C1_nodes':len(adj),'C1_edges':int(adj.sum()),'C1_isolates':a['graph']['isolates'],
            'C1_parent_resolution':a['graph']['resolved_selected_parents']/max(1,a['graph']['nonnull_selected_parents']),
            'C1_metric_eligible':int(eligible[:,:10].sum()),'C1_trace_eligible':int(eligible[:,10].sum()),
            'C1_log_eligible_context_only':int(eligible[:,11].sum()),'C1_constant_metric_channels':int(constants[:,:10].sum()),
            'C1_metric_multiplicity_per_service':eligible[:,:10].sum(axis=1),
            'C1_query_only_services':a['query_only_services'],
            'C1_trace_duplicates':a['identical_trace_duplicates_collapsed'],
            'C5_nodes':len(c5['service_names']),'C5_fit_nodes':len(c5['audit']['fit_services']),
            'C5_edges':c5['audit']['graph']['edges'],'C5_shape':c5['values_shape'],
            'C5_trace_quarantined_keys':len(c5['audit']['trace']['quarantined_keys']),
            'C5_trace_masked_service_bins':c5['audit']['trace']['masked_service_bins'],
            'log_status':p['logs']['status'],'log_rows':p['logs'].get('rows',0),
            'log_nulls':p['logs'].get('nulls',{}),'log_duplicate_rows':p['logs'].get('full_row_duplicates',0),
            'log_ref_mapped_rows':a['log_ref']['mapped_rows'],'log_ref_unmapped_rows':a['log_ref']['unmapped_rows'],
            'RCD_eligible':r['rcd']['audit']['eligible_columns'],'seconds':r['seconds']})
    save_json(run/'actual-use-input-summary.json',{'planned':30,'audited':len(cases),
        'root_in_candidate_cases':sum(c['root_in_candidate'] for c in cases),
        'observed_conflict_cases':sum(c['C5_trace_quarantined_keys']>0 for c in cases),
        'cases':cases,'no_model_outputs':True,'final60_accessed':False,
        'interpretation':'Exact development input compatibility; not topology utility or rank efficacy'})
    print('Input summary recorded for30 cases')


if __name__=='__main__':main()
