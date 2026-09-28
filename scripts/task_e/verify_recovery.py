"""Verify finished topology checkpoints without creating any new graph draw."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from scripts.task_e.execution import save_json, file_sha, require_contract
from scripts.task_e.topology_development import load_inputs, run_job, REPRESENTATIONS, BUDGETS


def main():
    run = Path(sys.argv[1])
    old = W / 'results/task-e/e27-022-development-topology'
    audit = W / 'results/task-e/e27-019-development-loader-audit'
    contract = require_contract(run, 'recovery')
    pins = {str(Path(r['path']).resolve()): r['sha256'] for r in contract['inputs']}
    for path, digest in pins.items():
        if file_sha(path) != digest:
            raise ValueError('Pinned recovery input changed: ' + path)
    previous = require_contract(old, 'topology')
    for item in previous['source_files']:
        if Path(item['path']).name in ('topology_development.py', 'ranking.py', 'contract.py', 'execution.py'):
            if file_sha(item['path']) != item['sha256']:
                raise ValueError('Topology implementation changed since generation')
    verified = []
    for record in load_inputs(old, audit):
        for representation in REPRESENTATIONS:
            for budget in BUDGETS:
                directory = old / 'topology' / record['handle'] / representation / str(budget)
                # Never enter the generator branch of run_job during recovery.
                if not (directory / 'receipt.json').is_file() or not (directory / 'graphs.npz').is_file():
                    raise ValueError('Missing checkpoint: ' + str(directory))
                result = run_job(old, record, representation, budget)
                if result.get('reused_verified_checkpoint') is not True:
                    raise AssertionError('Recovery must not generate a graph')
                verified.append({'handle': record['handle'], 'representation': representation,
                                 'budget': budget, 'graphs_sha256': result['graphs_sha256'],
                                 'receipt_sha256': file_sha(directory / 'receipt.json'),
                                 'draws': result['completed_draws']})
        print(f'{len(verified)//6}/30 existing topology cases verified; no regeneration', flush=True)
    save_json(run / 'recovery-verification.json', {
        'recorded_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'VERIFIED_REUSE', 'completed_cases': len(verified)//6,
        'completed_jobs': len(verified), 'verified_draws': sum(r['draws'] for r in verified),
        'new_graph_draws': 0, 'actual_RCA_predictions_executed': False,
        'checks': 'Pinned bytes; TD/source identity; seed/budget; every degree/component/isolate; proposal accounting; graph hashes/overlap/mobility.',
        'checkpoints': verified})


if __name__ == '__main__':
    main()
