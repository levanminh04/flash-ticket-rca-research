"""Bounded engineering timing diagnosis of first planned failed RCD input.

No new method/seed selection: same nine requests, exact upstream runtime.
Observer writes per-config progress and timed stacks; never changes predictions.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.rcd_development import load_inputs, CONFIGS, require_rcd_execution_contract
from scripts.task_e.execution import save_json, file_sha

OBSERVER = '''import faulthandler,json,sys,time
from scripts.task_e import rcd_numeric_worker as worker
faulthandler.dump_traceback_later(60,repeat=True,file=sys.stderr)
original=worker.run_request
def observed(values,configs,runtime):
    loaded,np,pd,execute,metadata=runtime
    def timed(*args,**kwargs):
        start=time.perf_counter()
        print(json.dumps({'event':'CONFIG_START','seed':kwargs['seed'],'bins':kwargs['bins']}),file=sys.stderr,flush=True)
        result=execute(*args,**kwargs)
        print(json.dumps({'event':'CONFIG_COMPLETE','seconds':time.perf_counter()-start,'result':result}),file=sys.stderr,flush=True)
        return result
    return original(values,configs,(loaded,np,pd,timed,metadata))
worker.run_request=observed
sys.argv=['rcd_numeric_worker',sys.argv[1]]
raise SystemExit(worker.main())
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    parser.add_argument('--audit-root',type=Path,required=True)
    args=parser.parse_args();run=args.run.resolve()
    contract=require_rcd_execution_contract(run)
    record=load_inputs(args.audit_root,contract)[0]
    request={'values':record['values'].tolist(),'configs':CONFIGS}
    save_json(run/'timing-plan.json',{'case':record['case'],'handle':record['handle'],
        'input_sha256':record['numeric_sha256'],'case_rule':'first planned DEV_IDS, not selected by ranks',
        'deadline_seconds':900,'stack_interval_seconds':60,'method_changed':False,
        'interpretation':'engineering only; not replacement efficacy run; observe exact9-config request'})
    env=dict(os.environ)
    for key in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP'):env.pop(key,None)
    env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1',PYTHONUNBUFFERED='1',PYTHONHASHSEED='0')
    command=[str(W/'environments/task-e/rcd39/Scripts/python.exe'),'-B','-u','-c',OBSERVER,str(run)]
    start=time.perf_counter();timed_out=False
    options={'creationflags':subprocess.CREATE_NO_WINDOW} if os.name=='nt' else {}
    with (run/'raw-reply.jsonl').open('xb') as out,(run/'timing-stacks.log').open('xb') as err:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=W,env=env,**options)
        try:
            process.communicate((json.dumps(request,allow_nan=False)+'\n').encode(),timeout=900)
        except subprocess.TimeoutExpired:
            timed_out=True;process.kill();process.communicate()
    save_json(run/'timing-result.json',{'exit_code':process.returncode,'deadline_reached':timed_out,
        'seconds':time.perf_counter()-start,'no_evaluator_invoked':True,
        'artifacts':[{'path':str(run/name),'sha256':file_sha(run/name)} for name in ('raw-reply.jsonl','timing-stacks.log')]})


if __name__=='__main__':main()
