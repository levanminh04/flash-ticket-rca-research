"""Controller launcher pins complete actual-use input sets before execution."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from .contract import W,P,begin_run,sha256,registry,write_json


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run_id');parser.add_argument('script');parser.add_argument('--stage',required=True)
    parser.add_argument('--audit-root',type=Path);parser.add_argument('--topology-root',type=Path)
    parser.add_argument('--pin-root',action='append',type=Path,default=[])
    parser.add_argument('--pin-file',action='append',type=Path,default=[])
    parser.add_argument('--rcd-report',type=Path);parser.add_argument('--child-python',type=Path)
    args,extra=parser.parse_known_args()
    gate=W/'results/task-e/continuation-resume-receipt.json'
    if json.loads(gate.read_text(encoding='utf-8'))['status']!='AUTO_RESUME_AUTHORIZED_DEVELOPMENT_ONLY':
        raise RuntimeError('Resume gate missing')
    inputs=[gate,W/'configs/task-e-td13-development.json',*args.pin_file]
    if args.audit_root:
        root=args.audit_root.resolve()
        inputs += [root/'run-contract.json',root/'loader-summary.json']
        inputs += sorted((root/'case-audits').glob('*.json'))
        inputs += sorted((root/'intermediates').rglob('*.npz'))
    if args.topology_root:
        root=args.topology_root.resolve()
        inputs += [root/'run-contract.json',root/'topology-summary.json']
        inputs += sorted((root/'topology').rglob('receipt.json'))
        inputs += sorted((root/'topology').rglob('graphs.npz'))
    for root in args.pin_root:
        inputs += [p for p in root.rglob('*') if p.is_file() and p.suffix in ('.json','.npz')]
    config=registry()
    if args.rcd_report:
        inputs.append(args.rcd_report)
        config.update(rcd_runtime_qualification_authorized=True,
                      rcd_source_manifest_sha256=sha256(W/'baselines/task-e-source-manifest.json'),
                      rcd_qualification_report={'path':str(args.rcd_report.resolve()),'sha256':sha256(args.rcd_report)})
    inputs=sorted(set(p.resolve() for p in inputs))
    sources=sorted((W/'scripts/task_e').glob('*.py'))+sorted((W/'tests/task_e').glob('*.py'))
    sources += [P/'docs/research-rca/task-d-method-and-experiment-specification.md',W/'baselines/task-e-source-manifest.json']
    run=W/'results/task-e'/args.run_id
    command=[str(args.child_python or sys.executable),str((W/args.script).resolve()),str(run),*extra]
    # Arguments for the child remain explicit: include them after -- in invoking
    # this launcher, since launcher's roots describe the separately pinned set.
    if '--' in command: command.remove('--')
    begin_run(args.run_id,command,sources,stage=args.stage,input_files=inputs,config=config,
              exposure='Exact development30 only; no final60 raw files or outcomes',
              output_schema='Stage-specific immutable JSON receipts and sealed lossless numeric predictions/intermediates')
    start=time.perf_counter()
    with (run/'stdout.log').open('x',encoding='utf-8') as out,(run/'stderr.log').open('x',encoding='utf-8') as err:
        process=subprocess.run(command,cwd=W,stdout=out,stderr=err)
    write_json(run/'execution.json',{'exit_code':process.returncode,'wall_seconds':time.perf_counter()-start},exclusive=True)
    print(run,process.returncode)
    print((run/'stdout.log').read_text(encoding='utf-8')[-5000:])
    print((run/'stderr.log').read_text(encoding='utf-8')[-10000:])
    raise SystemExit(process.returncode)


if __name__=='__main__': main()
