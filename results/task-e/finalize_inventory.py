"""Package existing Task E evidence; never execute models or alter their outputs."""
from pathlib import Path
import hashlib
import json
import subprocess
from datetime import datetime, timezone

W = Path('D:/Project/flash-ticket-rca-research')
P = Path('D:/Project/flash-ticket-platform')
R = W / 'results/task-e'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode('utf-8')


def purpose(path):
    rel = path.relative_to(P if path.is_relative_to(P) else W).as_posix()
    if rel.endswith('task-d-method-and-experiment-specification.md'):
        return 'Canonical TD13 membership/conflict clarification before development outcomes'
    if '/evidence/project-direction/' in rel:
        return 'Verbatim human authorization and scope evidence'
    if 'decision' in rel.lower() and path.is_relative_to(P):
        return 'Append atomic user authorization and canonical registration'
    if path.is_relative_to(P):
        return 'Derived research status, handoff or artifact routing; historical text retained'
    if rel.startswith('datasets/'):
        return 'Allowlisted development telemetry; physical source hash, not final60'
    if rel.startswith('baselines/upstream/'):
        return 'Pinned comparator source or declared patched copy'
    if rel.startswith('baselines/'):
        return 'Comparator source/fidelity/license pins or exact declared patch'
    if rel.startswith('task-d/'):
        return 'TD12 snapshot, TD13 rationale, independent review or prechange provenance'
    if rel.startswith('tests/'):
        return 'Executable bounded qualification fixture; saved receipts prove which version ran'
    if rel.startswith('configs/'):
        return 'Exact allowed development IDs, finite registry, folds, seeds and no-final scope'
    if rel.startswith('environments/'):
        return 'Pinned environment requirements or qualification plan; installed runtime excluded'
    if rel.startswith('scripts/task_e/'):
        return {
            'contract.py': 'Pre-run TD/source/input/environment/configuration provenance',
            'loader.py': 'Cutoff-specific telemetry admission, channels, graph and availability',
            'replay.py': 'Causal archival replay, conflict quarantine and immutable closed bins',
            'detection.py': 'Frozen G/L/ALL ridge forecasting, scales, masks and graph-TV',
            'ranking.py': 'Local evidence, PPR, diffusion, normalization and tie conventions',
            'calibration.py': 'Training-fold-only weighted thresholds and event evaluation',
            'evaluator.py': 'Planned-denominator ranking metrics and failure attribution',
            'c1_development.py': 'Local-first development selection, observed/control scoring and sensitivity',
            'c5_development.py': 'Registered forecasting/calibration campaign and OFAT/event sensitivities',
            'integrated_development.py': 'Past-only trigger diagnosis with first-post-only evaluation',
            'rcd_recovery.py': 'Exact unchanged RCD per-config execution/reuse/checkpoints and aggregation',
            'rcd_single_worker.py': 'One registered seed/bin numeric request to qualified upstream RCD',
            'rcd_timing_diagnostic.py': 'Preserved engineering timing/crash evidence without engine changes',
            'worker.py': 'Strict numeric model API and process entry point',
            'boundary.py': 'Dedicated numeric subprocess admission and response validation',
        }.get(path.name, 'Task E acquisition, execution, qualification or evidence/checkpoint helper')
    if rel == '.gitignore':
        return 'Exclude new raw telemetry, installed environments and large intermediates from Git'
    if path.name == 'source-manifest.json':
        return 'Exact declared source hashes and text snapshots; newline limitation disclosed'
    if path.name == 'run-contract.json':
        return 'Immutable contract recorded before corresponding execution'
    if path.name in ('seal.json', 'predictions-seal.json'):
        return 'Prediction/intermediate identity and integrity seal before evaluator use'
    if '/chunks/' in rel or '/attempt-history/' in rel:
        return 'Per-configuration RCD raw response, checkpoint or retained interrupted attempt'
    if path.suffix == '.npz':
        return 'Lossless saved numeric input/prediction/model/control artifact; no recomputation'
    if 'final-' in path.name:
        return 'Independent bounded audit, raw checks, initial findings or closure addendum'
    if 'continuation' in path.name:
        return 'Recovery scope/provenance checkpoint; not a new scientific run'
    if 'development-preflight' in path.name:
        return 'Coordinator A-J synthesis, 16 falsification answers and handoff evidence'
    return 'Task E execution evidence, logs, evaluation, resources or qualification receipt'


def main():
    final = json.loads((R/'e27-041-rcd-development-recovery/rcd-development-results.json').read_text())
    assert final['status'] == 'COMPLETED_DEVELOPMENT_EXECUTION'
    runs = []
    for d in sorted(R.glob('e27-*')):
        contract = d / 'run-contract.json'
        if not contract.exists():
            continue
        c = json.loads(contract.read_text(encoding='utf-8'))
        runs.append({'run': d.name, 'contract_path': str(contract), 'contract_sha256': sha(contract),
                     'command': c.get('command'), 'td': c.get('td'), 'config': c.get('config'),
                     'dataset_revision': c.get('dataset_revision'), 'executable': c.get('executable'),
                     'python': c.get('python'), 'packages': c.get('packages'),
                     'execution_receipts': [{'path': str(p), 'sha256': sha(p),
                         'value': json.loads(p.read_text())} for p in sorted(d.glob('*execution.json'))]})
    save(R/'development-preflight-reproducibility.json', {
        'scope': 'All existing Task E attempts, including failed and interrupted. Commands are history, not permission to rerun.',
        'warning': 'Never reuse an existing run directory for new execution. COMPLETE evidence is verified and reused, not recomputed.',
        'runs': runs})
    files = set()
    for root in (P, W):
        rels = git(root, 'diff', '--name-only', '-z').split('\0')
        rels += git(root, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')
        files.update(root/p for p in rels if p and (root/p).is_file() and not (root == P and p == 'README.md'))
    for directory in (R, W/'datasets/rcaeval/task-e-development'):
        files.update(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    exclusions = {'development-preflight-file-inventory.json', 'development-preflight-file-inventory.md',
                  'development-preflight-final-verification.json'}
    files = sorted(p for p in files if p.name not in exclusions)
    tracked = {root: set(git(root, 'ls-files', '-z').split('\0')) for root in (P, W)}
    old = json.loads((W/'task-d/td-v1.3-prechange-inventory.json').read_text())
    prior_paths = {str(Path(e['absolute_path']).resolve()) for e in old['prior_task_files']}
    entries = []
    for p in files:
        root = P if p.is_relative_to(P) else W
        rel = p.relative_to(root).as_posix()
        entries.append({'root': 'P' if root == P else 'W', 'path': str(p),
                        'relative_path': rel, 'bytes': p.stat().st_size,
                        'git_base_action': 'MODIFIED' if rel in tracked[root] else 'ADDED_LOCAL',
                        'present_in_pre_amendment_73_inventory': str(p.resolve()) in prior_paths,
                        'sha256': sha(p), 'purpose': purpose(p)})
    value = {'recorded_utc': datetime.now(timezone.utc).isoformat(),
             'scope': 'Entire current local D/E payload and ignored development data/numeric artifacts; not only latest resume edits.',
             'excluded': ['Installed virtualenv/runtime and caches', 'Unrelated P README (separately verified)',
                          'This inventory pair and final-verification receipt to avoid circular hashes'],
             'commit_push_performed': False, 'files': entries}
    save(R/'development-preflight-file-inventory.json', value)
    with (R/'development-preflight-file-inventory.md').open('x', encoding='utf-8', newline='\n') as f:
        f.write('# Exact local D/E file inventory\n\nEach row records the current file, purpose and SHA256; all original failed/interrupted attempts remain. Installed environments/caches, unrelated README and self-referential packaging files are excluded as declared in JSON. No commit/push.\n\n')
        f.write('| Root / relative path | Git-base action | Purpose | Bytes | SHA256 |\n|---|---|---|---:|---|\n')
        for e in entries:
            f.write(f"| {e['root']} / [{e['relative_path']}]({e['path'].replace(chr(92), '/')}) | {e['git_base_action']} | {e['purpose']} | {e['bytes']} | `{e['sha256']}` |\n")
    print(json.dumps({'files': len(entries), 'bytes': sum(e['bytes'] for e in entries)}))


if __name__ == '__main__':
    main()
