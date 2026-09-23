"""Small Task-D document and synthetic-math checks. No dataset/model execution."""
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

P = Path('D:/Project/flash-ticket-platform')
W = Path('D:/Project/flash-ticket-rca-research')
OUT = W / 'task-d/task-d-validation.json'
checks = []


def check(name, condition, detail=None):
    checks.append({'name': name, 'pass': bool(condition), 'detail': detail})
    if not condition:
        raise AssertionError(name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def rr(a, b):
    return sum(1 / r for r in range(a, b + 1)) / (b - a + 1)


def hit(a, b, k):
    return max(0, min(b, k) - a + 1) / (b - a + 1)


check('tie RR ranks1-2', rr(1, 2) == .75)
check('tie Hit1 ranks1-2', hit(1, 2, 1) == .5)
check('rank2 RR', rr(2, 2) == .5)
check('uniform3 tie RR', math.isclose(rr(1, 3), 11 / 18))
# Root has scores .9/.1, other .1/.9: per-seed mean RR=.75;
# mean scores tie -> .75 here; use three candidates to distinguish the policies.
# Seed1 root rank1, seed2 root rank3 -> mean RR=2/3.
# Mean scores [.5,.6,.4] -> root rank2 RR=.5.
check('seed averaging is metric averaging', not math.isclose((1 + 1/3)/2, .5))


def transition(n, edges):
    rows = [[] for _ in range(n)]
    for a, b in edges:
        rows[a].append(b)
        rows[b].append(a)
    return [r if r else [i] for i, r in enumerate(rows)]


def mix(local, rows):
    q = local[:]
    for _ in range(100):
        nxt = [.5 * local[v] + .5 * sum(q[u] for u in rows[v])/len(rows[v])
               for v in range(len(local))]
        if max(abs(a-b) for a, b in zip(nxt, q)) < 1e-12:
            return nxt
        q = nxt
    raise AssertionError('synthetic solver did not converge')


n = 7  # six-node cycle plus an isolate
edges = {(0,1),(1,2),(2,3),(3,4),(4,5),(0,5)}
changed = (edges - {(0,1),(3,4)}) | {(0,3),(1,4)}
rows = transition(n, edges)
rows_r = transition(n, changed)
local = [1., .1, .7, .2, .3, .4, .8]
identity = mix(local, [[i] for i in range(n)])
q = mix(local, rows)
qr = mix(local, rows_r)
check('identity arm returns identical local scores', identity == local)
check('constant input cannot create centrality ranking',
      all(abs(x-.4) < 1e-12 for x in mix([.4]*n, rows)))
check('isolate score retained', q[6] == local[6])
check('toy degree-preserving control', [len(x) for x in rows] == [len(x) for x in rows_r])
check('toy mixing differs with adjacency', max(abs(a-b) for a,b in zip(q,qr)) > 1e-6)
check('toy scores stay in input convex hull', min(q) >= min(local) and max(q) <= max(local))
perm = [3, 1, 6, 0, 4, 2, 5]
lp = [0.] * n
for old, new in enumerate(perm):
    lp[new] = local[old]
ep = {tuple(sorted((perm[a],perm[b]))) for a,b in edges}
qp = mix(lp, transition(n, ep))
check('coupled service permutation equivariance',
      all(abs(q[i]-qp[perm[i]]) < 1e-12 for i in range(n)))

streak, last_trigger = 0, -math.inf
triggers = []
positives = []
for t in range(360, 701, 10):
    score = None if t == 390 else 3
    above = score is not None and score > 2
    if above:
        positives.append(t)
    streak = streak + 1 if above else 0
    if streak >= 3 and t >= last_trigger + 300:
        triggers.append((t, 'INSUFFICIENT_HISTORY' if t < 600 else 'AVAILABLE'))
        last_trigger = t
check('C5 sustained-gap-refractory fixture', triggers ==
      [(380, 'INSUFFICIENT_HISTORY'), (680, 'AVAILABLE')], triggers)
check('C5 bin prediction separate from trigger', len(positives) == 34 and len(triggers) == 2)

p_paths = [
    'docs/research-rca/task-d-method-and-experiment-specification.md',
    'docs/research-rca/task-d-handoff.md',
    'docs/research-rca/CURRENT-STATE.md',
    'docs/research-rca/ARTIFACT-MAP.md',
    'docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md',
]
w_paths = [
    'task-d/task-d-evidence-ledger.md', 'task-d/task-d-exposure-ledger.md',
    'task-d/task-d-independent-review.md',
    'dataset-audit/TASK-B2B-RE2TT-MULTIMODAL-SCOPE.md',
    'task-d/validate-task-d.py',
]
documents = [P / s for s in p_paths] + [W / s for s in w_paths if s.endswith('.md')]
for path in documents:
    content = path.read_text(encoding='utf-8-sig')
    check('UTF8/nonempty ' + path.name, bool(content.strip()))
    check('no merge marker ' + path.name, not re.search(r'^(<<<<<<<|=======|>>>>>>>)', content, re.M))

# New delivery links, not every historical link in preserved A/MAP.
for path in documents[:3] + [W/'task-d/task-d-evidence-ledger.md']:
    for raw in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
        target = raw.strip('<>').split('#')[0]
        if not target or target.startswith(('http:', 'https:', 'mailto:')):
            continue
        target = re.sub(r':\d+$', '', target)
        resolved = Path(target) if re.match(r'^[A-Za-z]:/', target) else path.parent/target
        if resolved.resolve() == OUT.resolve():
            continue  # This invocation creates its own linked receipt after all checks.
        check('local link ' + path.name + ' -> ' + target, resolved.exists())

check('preexisting README preserved', sha(P/'README.md') ==
      '3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274')
for root, allowed in [(P, set(p_paths + ['README.md'])),
                      (W, set(w_paths + ['task-d/task-d-validation.json',
                                        'task-d/task-d-governance-validation.txt']))]:
    tracked = git(root, 'diff', '--name-only').splitlines()
    untracked = git(root, 'ls-files', '--others', '--exclude-standard').splitlines()
    check('authorized changed file set ' + root.name,
          set(tracked+untracked) <= allowed, sorted(set(tracked+untracked)))
    subprocess.run(['git', '-C', str(root), 'diff', '--check'], check=True)

protected = [P/'docs/research-rca/task-c-research-decision-lock.md',
             P/'docs/research-rca/RESEARCH-DECISIONS.md',
             P/'docs/research-rca/MASTER-RESEARCH-PROGRAM.md',
             P/'docs/research-rca/task-b-dataset-capability-summary.md',
             W/'dataset-audit/TASK-B-RCAEval-audit.md']
check('C lock preserved', sha(protected[0]) == 'e9ada986553ea150958d6355a57ccd140a55c80a62b84f5b4665e5d3dc258c98')
check('master preserved', sha(protected[2]) == 'e40abfdf4b61e81074f9c522897481ce543575d25658e7b1117dc279014e331a')
check('B digest preserved', sha(protected[3]) == '18a71ea34e0d3f5d5e11bbdeae3439536bd80d6aaa7f22172b4ab0ee0ef3a45b')
check('B CLOSED preserved', sha(protected[4]) == 'be40d10e359dc7de670d537c9c7000819161ed2739dc0a6280f69219a716c38a')
result = {
    'date_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'Task-D document and synthetic-math validation only; not RCA execution, full loader validation, raw rehash or scientific approval',
    'heads': {str(r): git(r, 'rev-parse', 'HEAD') for r in [P,W]},
    'checks': checks,
    'all_passed': all(c['pass'] for c in checks),
    'artifacts_sha256': {str(f): sha(f) for f in documents + [Path(__file__)]},
    'protected_sha256': {str(f): sha(f) for f in protected},
    'synthetic_scores_only': {'local': local, 'observed_toy': q, 'rewired_toy': qr},
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
assert OUT.exists() and json.loads(OUT.read_text(encoding='utf-8'))['all_passed']
print(json.dumps({'passed': len(checks), 'output': str(OUT)}, ensure_ascii=False))
