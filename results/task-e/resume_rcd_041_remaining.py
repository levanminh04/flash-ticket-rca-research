"""Resume only unsealed RCD041 work after preserving interrupted attempts."""
import json
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

W = Path('D:/Project/flash-ticket-rca-research')
sys.path.insert(0, str(W))
from scripts.task_e.rcd_recovery import (identity, validate_single, load_inputs,
    require_rcd_execution_contract, file_sha, save_json)


def main():
    run = W/'results/task-e/e27-041-rcd-development-recovery'
    previous = json.loads((run/'resume-01-execution.json').read_text())
    assert previous['exit_code'] != 0, 'Expected preserved interrupted-directory rejection'
    command = "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python' -and ($_.CommandLine -match 'rcd_recovery.py|scripts.task_e.rcd_single_worker') } | Select-Object -ExpandProperty ProcessId"
    active = subprocess.check_output(['powershell', '-NoProfile', '-Command', command], text=True).strip()
    assert not active, 'Do not launch while any original RCD worker/controller is active'
    contract = require_rcd_execution_contract(run)
    for entry in contract['source_files'] + contract['inputs']:
        assert file_sha(Path(entry['path'])) == entry['sha256'], entry['path']
    records = load_inputs(W/'results/task-e/e27-019-development-loader-audit', contract)
    by_handle = {r['handle']: r for r in records}
    verified = []
    for path in sorted(run.glob('chunks/*/*/seal.json')):
        seal = json.loads(path.read_text())
        record = by_handle[path.parent.parent.name]
        config = seal['identity']['config']
        assert seal['status'] == 'COMPLETE'
        assert seal['identity'] == identity(record, config, contract)
        for artifact in seal['artifacts']:
            assert file_sha(Path(artifact['path'])) == artifact['sha256']
        raw = next(Path(a['path']) for a in seal['artifacts']
                   if Path(a['path']).name in ('raw-response.jsonl', 'reused-result.json'))
        response = json.loads(raw.read_text())
        assert validate_single(response, record, config, contract) == seal['result']
        assert response['fidelity'] == seal['fidelity']
        verified.append({'path': str(path), 'sha256': file_sha(path)})
    assert len(verified) == 264
    preservation = json.loads((run/'abandoned-six-preservation-plan.json').read_text())
    for e in preservation['entries']:
        assert not Path(e['source']).exists()
        for a in e['files']:
            assert file_sha(Path(e['destination'])/a['name']) == a['sha256']
    assert not [p for p in run.glob('chunks/*/*/start.json') if not (p.parent/'seal.json').exists()]
    cmd = [str(W/'.venv/Scripts/python.exe'), '-B', 'scripts/task_e/rcd_recovery.py', str(run),
           '--audit-root', 'results/task-e/e27-019-development-loader-audit',
           '--previous-run', 'results/task-e/e27-034-rcd-development-full',
           '--timing-run', 'results/task-e/e27-039-rcd-timing-diagnostic', '--workers', '6']
    save_json(run/'resume-02-plan.json', {'created_before_execution_utc': datetime.now(timezone.utc).isoformat(),
        'command': cmd, 'source_contract_sha256': file_sha(run/'run-contract.json'),
        'verified_complete_chunks': verified, 'remaining_chunks': 6,
        'raw_seal_result_fidelity_equal': True, 'source_input_TD_config_unchanged': True,
        'abandoned_attempt_preservation_sha256': file_sha(run/'abandoned-six-preservation-plan.json'),
        'new_predictions_only': 'Six raw-empty interrupted train/cpu/1 configs; all264 COMPLETE return cache unchanged',
        'wrapper_sha256': file_sha(Path(__file__))})
    started = time.perf_counter()
    with (run/'resume-02.stdout.log').open('x', encoding='utf-8') as out, (run/'resume-02.stderr.log').open('x', encoding='utf-8') as err:
        result = subprocess.run(cmd, cwd=W, stdout=out, stderr=err)
    save_json(run/'resume-02-execution.json', {'exit_code': result.returncode,
        'wall_seconds': time.perf_counter()-started, 'reused_complete_chunks': 264,
        'command': cmd, 'ended_utc': datetime.now(timezone.utc).isoformat()})
    print('resume02 exit', result.returncode)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
