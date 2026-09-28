"""Append-only recovery inventory; reads receipts, never model data or outcomes."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.execution import file_sha, save_json
from scripts.task_e.contract import P, TD_SHA256


def main():
    label = sys.argv[1]
    if not label.replace('-', '').isalnum():
        raise ValueError('Simple checkpoint label required')
    root = W / 'results/task-e'
    runs = []
    for run in sorted(root.glob('e27-*')):
        if not run.is_dir():
            continue
        artifacts = []
        for pattern in ('*report.json', '*summary.json', '*results.json', '*selection.json', '*verification.json'):
            for path in sorted(run.glob(pattern)):
                artifacts.append({'path': str(path), 'sha256': file_sha(path), 'bytes': path.stat().st_size})
        execution = run / 'execution.json'
        runs.append({'run': run.name,
                     'execution': json.loads(execution.read_text(encoding='utf-8')) if execution.exists() else
                     {'state': 'NO_EXECUTION_RECEIPT; inspect older log/fixture receipt or running process'},
                     'contract_sha256': file_sha(run / 'run-contract.json') if (run / 'run-contract.json').exists() else None,
                     'artifacts': artifacts,
                     'case_checkpoint_count': len(list((run / 'case-results').glob('*.json'))),
                     'C5_case_variant_seals': len(list((run / 'predictions').rglob('seal.json')))})
    files = sorted((W / 'scripts/task_e').glob('*.py')) + sorted((W / 'tests/task_e').glob('*.py'))
    files += [root / 'continuation-live-handoff.md', root / 'continuation-plan.md',
              P / 'docs/research-rca/task-d-method-and-experiment-specification.md']
    output = root / ('continuation-recovery-checkpoint-' + label + '.json')
    save_json(output, {'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'td_sha256': TD_SHA256, 'final60_authorized': False,
        'agent_status_is_not_completion_evidence': True,
        'resume_entry': str(root / 'continuation-live-handoff.md'),
        'runs': runs, 'files': [{'path': str(p), 'sha256': file_sha(p), 'bytes': p.stat().st_size} for p in files],
        'reuse_rule': 'Verify complete source/input/config/TD and output hashes; reuse finished checkpoints; preserve failures/partial attempts; never infer completion from missing execution receipt.'})
    print(output)


if __name__ == '__main__':
    main()
