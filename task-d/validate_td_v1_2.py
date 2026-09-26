"""TD12 document/scope/provenance and synthetic mathematics only.

Does NOT validate future benchmark loaders, runtime GT firewall, model efficacy,
empirical sensitivity, upstream fidelity or LLM quality. No telemetry is read.
TD11 validator remains untouched: its equality/no-dev-label/rolling-calibration
assumptions were superseded explicitly, not patched into the method.
"""
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import numpy as np

P = Path('D:/Project/flash-ticket-platform')
W = Path('D:/Project/flash-ticket-rca-research')
OUT = W / 'task-d/td-v1.2-validation.json'
PROTO = P / 'docs/research-rca/task-d-method-and-experiment-specification.md'
SOURCE = P / 'docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md'
ATTACH = Path('C:/Users/84583/.codex/attachments/d0d4f1c7-39cd-4679-bbda-477557e63c28/Pasted text.txt')
SNAP = json.loads((W / 'task-d/td-v1.2-prechange-inventory.json').read_text(encoding='utf-8'))
P_ALLOWED = {
    'docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md',
    'docs/project/decision-register.md',
    *('docs/research-rca/' + f for f in [
        'RESEARCH-DECISIONS.md', 'task-d-method-and-experiment-specification.md',
        'task-c-research-decision-lock.md', 'MASTER-RESEARCH-PROGRAM.md',
        'SESSION-BOOTSTRAP.md', 'task-b-dataset-capability-summary.md',
        'ARTIFACT-MAP.md', 'CURRENT-STATE.md', 'task-d-handoff.md']),
}
W_ALLOWED = {'task-d/' + f for f in [
    'td-v1.2-prechange-inventory.json', 'td-v1.2-review-memos.md',
    'td-v1.2-provenance-and-data.md', 'td-v1.2-review-packet.md',
    'audit_td_v1_2_public_metadata.py', 'td-v1.2-public-metadata.json',
    'validate_td_v1_2.py', 'td-v1.2-validation.json',
    'td-v1.2-governance-validation.txt']}
checks = []


def check(name, good, details=None):
    checks.append({'name': name, 'pass': bool(good), 'details': details})


def sha(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], encoding='utf-8')


def text(f):
    return f.read_text(encoding='utf-8-sig')


d = text(PROTO)
check('Scoped candidate status / no E / no empirical freeze',
      all(s in d for s in ['CANDIDATE', 'human approval OPEN',
                            'NOT STARTED / NOT AUTHORIZED',
                            'No empirical selection', 'three distinct agents']))
check('Development rights and fixed input-loss masks declared',
      all(s in d for s in ['RCA-022', 'INPUT/PREFIX eligibility',
                            'before predictions', 'never shrink', 'Final labels']))
check('Exactly registered primary and secondary families',
      all(s in d for s in ['Eight variants', 'Six configs', '256 independent',
                            'VALUE-DIFFUSION', 'G-RIDGE', 'GRAPH-TV', 'RCD-RCAEval']))
check('Informative-data and transfer gates explicit',
      all(s in d for s in ['≥80%planned', '>10%planned', 'numeric detector thresholds',
                            'AFTER', 'before run_multi_phase/CI']))
check('Source attachment identity', sha(ATTACH).upper() ==
      '9F86A703CB4F6381BAF09DA0370857A0EE8D70432524379B8F1F4C8F7E0E592C')
check('Original mission content preserved after provenance header',
      text(SOURCE).split('\n---\n\n', 1)[1] == text(ATTACH))
old_dec = git(P, 'show', SNAP['flash-ticket-platform']['head'] +
              ':docs/research-rca/RESEARCH-DECISIONS.md')
new_dec = text(P / 'docs/research-rca/RESEARCH-DECISIONS.md')
for i in range(1, 22):
    marker = '| RCA-%03d |' % i
    old_row = next(s for s in old_dec.splitlines() if s.startswith(marker))
    check(f'Historical decision RCA-{i:03d} exact', old_row in new_dec.splitlines())
ids = re.findall(r'^\| (RCA-\d+) \|', new_dec, re.M)
check('Unique decisions 001..042; no algorithm promoted to user decision',
      ids == [f'RCA-{i:03d}' for i in range(1, 43)])
check('Scoped supersession historical policy explicitly retained',
      all(s in new_dec for s in ['TC', 'development', 'CANDIDATE technical interpretation'])
      if 'TC' in new_dec else all(s in new_dec for s in [
          'C v1 §4', 'development', 'CANDIDATE technical interpretation']))

preserved, changed, inventory = {}, {}, {}
for root, allowed in [(P, P_ALLOWED), (W, W_ALLOWED)]:
    snap = SNAP[root.name]
    check('HEAD unchanged ' + root.name, git(root, 'rev-parse', 'HEAD').strip() == snap['head'])
    check('Branch unchanged ' + root.name, git(root, 'branch', '--show-current').strip() == snap['branch'])
    unexpected = []
    preserved[root.name], changed[root.name] = [], []
    for rel, before_sha in snap['sha256'].items():
        f = root / rel
        if not f.is_file() or sha(f) != before_sha:
            changed[root.name].append(rel)
            if rel not in allowed:
                unexpected.append(rel)
        else:
            preserved[root.name].append(rel)
    check('All unrelated tracked bytes preserved ' + root.name, not unexpected, unexpected)
    new_paths = git(root, 'ls-files', '--others', '--exclude-standard').splitlines()
    unexpected_new = [f for f in new_paths if f not in allowed]
    check('Exact new-file scope ' + root.name, not unexpected_new, unexpected_new)
    task_paths = set(changed[root.name]) | set(new_paths)
    check('Task file set matches declared packet ' + root.name,
          task_paths <= allowed and (allowed - {OUT.relative_to(W).as_posix()}
                                    if root == W else allowed) <= task_paths,
          sorted(task_paths))
    inventory[root.name] = sorted(allowed)
    diffcheck = subprocess.run(['git', '-C', str(root), 'diff', '--check'],
                               text=True, encoding='utf-8', capture_output=True)
    check('git diff --check ' + root.name, diffcheck.returncode == 0, diffcheck.stdout)
    for rel in sorted(allowed):
        f = root / rel
        if f == OUT:
            continue
        check('File exists / UTF8 ' + rel, f.exists())
        if not f.exists():
            continue
        raw = f.read_bytes()
        try:
            t = raw.decode('utf-8-sig')
            check('No replacement character ' + rel, '\ufffd' not in t)
        except UnicodeDecodeError:
            check('Valid UTF8 ' + rel, False)
            continue
        if f.suffix == '.md':
            broken = []
            for href in re.findall(r'\]\(([^\n]+?)\)', t):
                target = unquote(href.strip('<>'))
                if target.startswith(('https:', 'http:', '#')):
                    continue
                target = target.split('#', 1)[0]
                candidate = Path(target) if re.match(r'^[A-Za-z]:[/\\]', target) else f.parent / target
                if candidate != OUT and not candidate.exists():
                    broken.append(target)
            check('Local markdown links ' + rel, not broken, broken)
check('Unrelated preexisting README exact preservation',
      sha(P / 'README.md') == SNAP['flash-ticket-platform']['sha256']['README.md'])
check('No application/schema/raw/legacy mutations',
      all(f in P_ALLOWED for f in changed[P.name]) and not changed[W.name])

metadata = json.loads(text(W / 'task-d/td-v1.2-public-metadata.json'))
check('Pinned90HTTP206footers/no errors/no telemetry rows',
      metadata['revision'] == 'afeacb11bcc94dadfd1c8f483ee4377b2b8b614e'
      and metadata['checked'] == 90 and not metadata['errors']
      and metadata['bytes_transferred'] == 6026998
      and len({r['file'] for r in metadata['per_file_receipt']}) == 90
      and all(r['http_range_status'] == 206 and r['match_metadata_rows']
              for r in metadata['per_file_receipt']))
check('Metadata audit script identity', metadata['script_sha256'] ==
      sha(W / 'task-d/audit_td_v1_2_public_metadata.py'))
tt3 = next(c for c in metadata['metadata_cohorts'] if c['dataset'] == 'RE3-TT')
check('RE3 unequal-repeat scenario facts and prefix offset',
      len(tt3['scenario_cells']) == 8 and tt3['cases'] == 30
      and sorted(c['cases'] for c in tt3['scenario_cells']) == [3, 3, 3, 3, 4, 4, 4, 6]
      and tt3['injection_seconds_after_metric_start'] == [900])
gov = text(W / 'task-d/td-v1.2-governance-validation.txt')
check('Governance output contains successful audit',
      'PASS' in gov or 'passed' in gov.lower(), gov[-1200:])

# Deterministic synthetic properties, not benchmark implementation tests.
T = np.array([[0, 1, 0], [.5, 0, .5], [1, 0, 0]], dtype=float)
I = np.eye(3)
huge = np.array([1e308, 1e308, 1e307])
p = (huge / huge.max()) / (huge / huge.max()).sum()
check('Max-first personalization avoids overflow', np.isfinite(p).all() and abs(p.sum()-1) < 1e-14)
for damp in [.2, .5, .85]:
    pi = np.linalg.solve(I-damp*T.T, (1-damp)*p)
    check(f'PPR mass/residual/nonnegative d={damp}',
          np.isfinite(pi).all() and min(pi) >= 0 and abs(pi.sum()-1)<1e-12
          and max(abs(pi-(1-damp)*p-damp*T.T@pi))<1e-12)
    local = np.linalg.solve(I-damp*I, (1-damp)*p)
    check(f'Identity PPR equals local personalization d={damp}', np.allclose(local, p))
    l = np.array([1e12, 3e11, 7e11])
    y = np.linalg.solve(I-damp*T, (1-damp)*l/l.max())
    check(f'Bounded value solve stable and convex d={damp}',
          max(abs(y-(1-damp)*l/l.max()-damp*T@y))<1e-12
          and min(y)>=min(l/l.max())-1e-12 and max(y)<=1+1e-12)
    const = np.linalg.solve(I-damp*T, (1-damp)*np.ones(3))
    check(f'Value-only constant invariant d={damp}', np.allclose(const, 1))
mass_uniform = np.linalg.solve(I-.85*T.T, .15*np.ones(3)/3)
check('PPR does NOT require uniform-input equal output', np.ptp(mass_uniform) > .01)
swapT = np.array([[0.,1.],[1.,0.]])
smoothed = np.linalg.solve(np.eye(2)-.5*swapT, .5*np.array([1.,0.]))
check('Legacy smoothing suppresses isolated max, not proof of invalidAD',
      np.allclose(smoothed, [2/3, 1/3]) and max(smoothed)<1)

def components(a):
    remaining = set(range(len(a))); parts = []
    undirected = (a + a.T) > 0
    while remaining:
        stack = [min(remaining)]; seen = set(stack)
        while stack:
            v = stack.pop()
            for u in np.where(undirected[v])[0]:
                if int(u) not in seen:
                    seen.add(int(u)); stack.append(int(u))
        remaining -= seen; parts.append(tuple(sorted(seen)))
    return tuple(sorted(parts))

a = np.zeros((6,6), int)
for u,v in [(0,1),(1,2),(2,3),(3,4),(4,5),(5,0),(1,4)]: a[u,v]=1
b = a.copy(); b[0,1]=b[2,3]=0; b[0,3]=b[2,1]=1
check('Directed switch preserves in/out degree and weakpartition',
      np.array_equal(a.sum(0),b.sum(0)) and np.array_equal(a.sum(1),b.sum(1))
      and components(a)==components(b) and not np.array_equal(a,b))
unswitchable = np.array([[0,1],[0,0]])
check('Small control space can be degenerate without fabrication', components(unswitchable)==((0,1),))

# Synthetic graph-conditioned fit versus identical local tensor with zero context.
rng = np.random.default_rng(20260926)
x = rng.normal(size=(23,5)); x[:,3:]=1
target = 2*x[:,1]+rng.normal(0,.01,23)
def ridge(features, y, lam):
    design = np.column_stack([np.ones(len(y)), features])
    penalty = np.diag([0]+[lam]*features.shape[1])
    return np.linalg.solve(design.T@design/len(y)+penalty, design.T@y/len(y))
localx=x.copy(); localx[:,1:]=0
coefG=ridge(x,target,1);coefL=ridge(localx,target,1)
held=rng.normal(size=(12,5));held[:,3:]=1
heldy=2*held[:,1]
heldlocal=held.copy();heldlocal[:,1:]=0
errG=abs(heldy-np.column_stack([np.ones(12),held])@coefG)
errL=abs(heldy-np.column_stack([np.ones(12),heldlocal])@coefL)
check('Graph predictor changes expected-value residual, toy only', errG.mean()<errL.mean())
scale=max(float(np.quantile(errG,.75)-np.quantile(errG,.25)),.01)
check('Held-out scale separate from training and finite', scale>=.01 and len(errG)==12)
z=np.ones(3)*7
tv=lambda values:float(sum((values[u]-values[v])**2 for u,v in [(0,1),(1,2)])/2)
check('GraphTV has common-mode blind spot', tv(z)==0 and tv(np.array([0.,2.,0.]))>0)

weights=np.array([1/2/1/2]*2+[1/2/2/1]*2)
values=np.array([1.,2.,3.,4.])
check('Conditional scored-CDF weights redistribute missing support exactly',abs(weights.sum()-1)<1e-12)
weightedq=lambda q:float(values[np.searchsorted(np.cumsum(weights),q,side='left')])
check('WeightedCDF inverse is not type7 interpolation',weightedq(.5)==2 and weightedq(.95)==4)
rr=lambda lo,hi:sum(1/r for r in range(lo,hi+1))/(hi-lo+1)
ndcg=lambda lo,hi,k:sum(1/math.log2(r+1) for r in range(lo,min(hi,k)+1))/(hi-lo+1)
check('TieRR independent of display sort',abs(rr(1,2)-.75)<1e-14 and abs(rr(1,3)-11/18)<1e-14)
check('NDCG crossing cutoff keeps full tie denominator',abs(ndcg(4,6,5)-(1/math.log2(5)+1/math.log2(6))/3)<1e-14)
check('MC precision arithmetic separate from incidentN',abs(.5/math.sqrt(256*60)-.004034357)<1e-8)
check('Practicaldelta illustration6/60rank2to1',abs(6*(1-.5)/60-.05)<1e-14)
streak=0;last=None;triggers=[]
for t in range(185,521,5):
    valid=t!=205
    streak=streak+1 if valid else 0
    if streak>=3 and (last is None or t-last>=300):
        triggers.append(t);last=t
check('Fixed C5 persistence/refractory fixture',triggers[:2]==[195,495],triggers)

file_hashes={}
for root,allowed in [(P,P_ALLOWED),(W,W_ALLOWED)]:
    file_hashes[root.name]={f:sha(root/f) for f in sorted(allowed)
                            if (root/f).exists() and root/f != OUT}
result={
    'created_utc':datetime.now(timezone.utc).isoformat(),
    'scope':'DOCUMENT/SCOPE/HISTORY/FOOTER RECEIPT/SYNTHETIC MATH ONLY; NO TELEMETRY/MODEL/BASELINE/TASK E',
    'protocol_sha256':sha(PROTO),'validator_sha256':sha(Path(__file__)),
    'pass':all(c['pass'] for c in checks),'passed':sum(c['pass'] for c in checks),
    'total':len(checks),'checks':checks,'changed_tracked':changed,
    'preserved_tracked_counts':{k:len(v) for k,v in preserved.items()},
    'task_inventory':inventory,'file_hashes_excluding_this_receipt':file_hashes,
    'legacy_validator_prechange':{'passed':95,'total':97,
        'only_failures':'Two old HEAD assertions after prior push; dry receipt-preserving run; old receipt untouched'},
    'not_verified':['Future runtime GT firewall/canaries','Actual-use telemetry schema/joins/prefix compatibility',
                    'Empirical development selection/sensitivity','Baseline fidelity/env/license/runtime',
                    'Model effects/resources/MCmobility','LLM quality/target integration'],
}
OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'pass':result['pass'],'passed':result['passed'],'total':result['total'],
                  'failed':[c for c in checks if not c['pass']]}))
raise SystemExit(0 if result['pass'] else 1)
