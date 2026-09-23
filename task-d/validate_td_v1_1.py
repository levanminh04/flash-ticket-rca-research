"""TD-v1.1 document and synthetic-math checks only; never read telemetry/run RCA."""
import hashlib
import json
import math
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

P = Path("D:/Project/flash-ticket-platform")
W = Path("D:/Project/flash-ticket-rca-research")
BASE_P = "6bd04e625926e923301cc6bb1433682f01fd87fc"
BASE_W = "c7e47fdcc69c53876f7bd3f1a5e71ef89c59ccf6"
PROTO = "docs/research-rca/task-d-method-and-experiment-specification.md"
SOURCE = "docs/evidence/advisor-direction/2026-09-23-huong-dan-do-minh-cung-cap.md"
checks = []


def check(name, value, detail=None):
    checks.append({"name": name, "pass": bool(value), "detail": detail})


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], encoding="utf-8"
    ).replace("\r\n", "\n")


def read(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


old = git(P, "show", BASE_P + ":" + PROTO)
new = read(P / PROTO)
# Compare substantive contracts, permitting only explicitly disclosed insertions.
check("C1 estimands exactly preserved",
      section(old, "**C1 operationalized:", "## 2.") ==
      section(new, "**C1 operationalized:", "### 1.1"))
for name, start, end in [
    ("exposure and grouped split", "## 3.", "## 4."),
    ("Mode A windows, V and numeric evidence", "## 4.", "### 4.2"),
    ("C1 solver, rewiring and external baseline formulas",
     "Nếu degree d_v>0", "## 7."),
]:
    check("C1 unchanged: " + name, section(old, start, end) == section(new, start, end))
old7 = section(old, "## 7.", "## 8.")
new7 = section(new, "## 7.", "## 8.")
new7 = re.sub(r"\n\*\*TD-v1\.1 secondary NDCG@5:\*\*.*?\n\nCase-weighted",
              "\nCase-weighted", new7, flags=re.S)
check("C1 primary metrics, inference and verdict unchanged", old7 == new7)
# All pre-existing human statements retained verbatim, append only.
old_dec = git(P, "show", BASE_P + ":docs/research-rca/RESEARCH-DECISIONS.md")
new_dec = read(P / "docs/research-rca/RESEARCH-DECISIONS.md")
for i in range(1, 18):
    marker = "| RCA-%03d |" % i
    check("RCA-%03d row preserved" % i,
          next(x for x in old_dec.splitlines() if x.startswith(marker)) ==
          next(x for x in new_dec.splitlines() if x.startswith(marker)))

preserved_p = [
    "AGENTS.md",
    "docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md",
    "docs/evidence/advisor-direction/2026-08-22-dinh-huong-de-tai.md",
    "docs/research-rca/task-c-research-decision-lock.md",
    "docs/research-rca/task-c-independent-research-shortlist.md",
    "docs/research-rca/task-b-dataset-capability-summary.md",
]
preserved_w = [
    "dataset-audit/TASK-B-RCAEval-audit.md",
    "task-d/task-d-evidence-ledger.md",
    "task-d/task-d-exposure-ledger.md",
    "task-d/task-d-independent-review.md",
    "task-d/task-d-validation.json",
    "task-d/task-d-governance-validation.txt",
    "task-d/validate-task-d.py",
]
for root, base, files in [(P, BASE_P, preserved_p), (W, BASE_W, preserved_w)]:
    for rel in files:
        check("Preserved historical/authority file: " + rel,
              git(root, "diff", base, "--", rel) == "")
check("Unowned README exact bytes preserved",
      sha(P / "README.md") ==
      "3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274")

request_path = Path(
    "C:/Users/84583/.codex/attachments/"
    "061cebbe-79ec-4ead-9ddd-64c59a4ad865/Pasted text.txt"
)
request = read(request_path)
quote = request.split('\n"Đề tài này', 1)[1].split('"\n\nEND QUOTE.', 1)[0]
quote = "Đề tài này" + quote
source_quote = section(read(P / SOURCE), "## 1. Nguyên văn\n\n",
                       "\n\n## 2. Quyền diễn giải")
check("Advisor quote exact text preserved (newline normalization only)",
      quote == source_quote)
check("Human clarification separated from advisor quote",
      "## 3. Xác nhận hiện hành của Minh" in read(P / SOURCE))
check("Unknown original date and channel retained",
      "NOT VERIFIED" in read(P / SOURCE))

a_rel = "docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md"
a_old = git(P, "show", BASE_P + ":" + a_rel)
a_new = re.sub(r"> \*\*Nguồn bổ sung TD-v1\.1, 23/09/2026:\*\*.*?\n\n",
               "", read(P / a_rel), flags=re.S)
check("Task A only added provenance notice; original retained", a_old == a_new)

# Independent mathematical fixtures, no experimental data/model code.
def ndcg(a, b, k=5):
    return sum(1 / math.log2(r + 1) for r in range(a, min(b, k) + 1)) / (b-a+1)


def rr(ranks):
    return sum(1/r for r in ranks) / len(ranks)


def solve(a, matrix):
    q = list(a)
    for _ in range(100):
        nxt = [.5*a[i] + .5*sum(x*y for x, y in zip(row, q))
               for i, row in enumerate(matrix)]
        change = max(abs(x-y) for x, y in zip(q, nxt))
        q = nxt
        if change < 1e-12:
            return q
    raise AssertionError("synthetic solver did not converge")


check("NDCG rank one", ndcg(1, 1) == 1)
check("NDCG rank six is zero", ndcg(6, 6) == 0)
check("NDCG tie straddling cutoff retains full denominator",
      math.isclose(ndcg(4, 7), (1/math.log2(5)+1/math.log2(6))/4))
check("NDCG tied first two expected discount",
      math.isclose(ndcg(1, 2), (1+1/math.log2(3))/2))
check("MRR and NDCG aggregate ordering can differ",
      rr([1, 6]) > rr([2, 3]) and
      (ndcg(1, 1)+ndcg(6, 6))/2 < (ndcg(2, 2)+ndcg(3, 3))/2)
identity = [[1., 0.], [0., 1.]]
swap = [[0., 1.], [1., 0.]]
check("Identity exactly preserves local vector", solve([1., 0.], identity) == [1., 0.])
q = solve([1., 0.], swap)
check("Graph score analytically two-thirds peak",
      math.isclose(q[0], 2/3, abs_tol=1e-11) and math.isclose(q[1], 1/3, abs_tol=1e-11))
check("Same evidence/threshold graph changes raw anomaly decision",
      max(solve([1., 0.], identity)) > .8 and max(q) < .8)
check("Constant evidence unaffected by graph", solve([2., 2.], swap) == [2., 2.])
for a in ([0., 0.], [2., 1.], [5., 20.], [1e-5, 3.]):
    q = solve(a, swap)
    check("Smoothing stays in local convex range " + repr(a),
          min(a)-1e-11 <= min(q) and max(q) <= max(a)+1e-11)
m, t, g = 2., 3., 0.
check("Missing log yields same MT/MTL raw vector with fixed denominator",
      (m+t)/3 == (m+t+g)/3)
check("Different calibrated thresholds can break missing-log alert equality",
      ((m+t)/3 > 1.) != ((m+t+g)/3 > 2.))

def q7(values, p):
    x = sorted(values)
    pos = (len(x)-1)*p
    lo = int(pos)
    frac = pos-lo
    return x[lo]*(1-frac) + x[min(lo+1, len(x)-1)]*frac


def calibration_ok(values):
    threshold = q7(values, .99)
    return (len(values) >= 100 and max(values) > min(values)
            and math.isfinite(threshold) and any(x > threshold for x in values))


check("Constant calibration rejected", not calibration_ok([1.] * 100))
check("q99 maximum tie calibration rejected", not calibration_ok([0.] * 98 + [1.] * 2))
check("Varying calibration has reachable strict exceedance", calibration_ok(list(range(100))))
streak, last, emitted = 0, -math.inf, []
for endpoint in range(360, 701, 10):
    score = None if endpoint == 390 else 3
    streak = streak+1 if score is not None and score > 2 else 0
    if streak >= 3 and endpoint >= last+300:
        emitted.append(endpoint)
        last = endpoint
check("Persistence/gap/refractory fixture", emitted == [380, 680])
check("First trigger fails history; later trigger does not repair it",
      emitted[0] < 600 <= emitted[1])
check("Injection-bin boundary convention",
      (600-10 < 595 < 600) and (610-10 >= 595) and (590 <= 595))
# Past log sampling depends on source hash: explicitly a packet limitation.
def sample(file_hash):
    return sorted(range(12),
                  key=lambda n: hashlib.sha256((file_hash+"|"+str(n)).encode()).digest())[:3]


check("Full-file-hash sampled excerpts need not be prefix stable",
      sample("old-file") != sample("future-suffix-file"))

allowed_p = [
    SOURCE, PROTO, "docs/research-rca/task-d-handoff.md",
    "docs/research-rca/CURRENT-STATE.md", "docs/research-rca/ARTIFACT-MAP.md",
    "docs/research-rca/MASTER-RESEARCH-PROGRAM.md", a_rel,
    "docs/research-rca/RESEARCH-DECISIONS.md", "docs/project/decision-register.md",
]
allowed_w = [
    "task-d/td-v1.1-source-first-review.md",
    "task-d/td-v1.1-reconciliation-evidence.md",
    "task-d/td-v1.1-delta-review.md",
    "task-d/validate_td_v1_1.py",
    "task-d/td-v1.1-validation.json",
    "task-d/td-v1.1-governance-validation.txt",
]
all_files = [(P, x) for x in allowed_p] + [(W, x) for x in allowed_w
               if x != "task-d/td-v1.1-validation.json"]
broken_links = []
hashes = {}
for root, rel in all_files:
    path = root / rel
    check("Expected artifact exists: " + rel, path.exists())
    if not path.exists():
        continue
    hashes[str(path)] = sha(path)
    text = read(path)
    check("UTF8/no replacement bytes: " + rel, "\ufffd" not in text)
    if path.suffix == ".md":
        for dest in re.findall(r"\]\(([^)\n]+)\)", text):
            dest = unquote(dest.strip("<>").split("#")[0])
            if not dest or re.match(r"(https?|mailto|codex|app):", dest):
                continue
            candidate = Path(dest) if re.match(r"^[A-Za-z]:[/\\]", dest) else path.parent / dest
            # This receipt is produced after validation; its self-reference is
            # checked by the final successful write, not by a prior stale file.
            output_path = W / "task-d/td-v1.1-validation.json"
            if not candidate.exists() and candidate.resolve() != output_path.resolve():
                broken_links.append({"source": str(path), "target": dest})
check("Local Markdown links resolve", not broken_links, broken_links)
for root, allowed in [(P, set(allowed_p) | {"README.md"}), (W, set(allowed_w))]:
    changed = git(root, "diff", "--name-only").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    check("Exact allowed mutation scope " + str(root), set(changed+untracked) <= allowed,
          sorted(set(changed+untracked)))
    check("HEAD unchanged " + str(root), git(root, "rev-parse", "HEAD").strip() ==
          (BASE_P if root == P else BASE_W))
    result = subprocess.run(["git", "-C", str(root), "diff", "--check"], capture_output=True, text=True)
    check("Tracked diff whitespace " + str(root), result.returncode == 0, result.stdout)
receipt = {
    "version": "TD-v1.1",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "Document preservation and small synthetic mathematics only",
    "pass": all(c["pass"] for c in checks),
    "checks_passed": sum(c["pass"] for c in checks),
    "checks_total": len(checks),
    "checks": checks,
    "artifact_sha256": hashes,
    "request_sha256": sha(request_path),
    "limits": [
        "No raw telemetry or corpus read by this validator.",
        "No RCA implementation, baseline, training or empirical performance validation.",
        "No source license/runtime/loader/all-log compatibility verified.",
        "Reviewer closure and human acceptance are separate from these checks.",
        "Receipt does not hash itself; creating it cannot recursively certify itself.",
    ],
}
with (W / "task-d/td-v1.1-validation.json").open(
    "w", encoding="utf-8", newline="\n"
) as output:
    output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"pass": receipt["pass"], "passed": receipt["checks_passed"],
                  "total": len(checks), "failed": [c for c in checks if not c["pass"]]},
                 ensure_ascii=False, indent=2))
raise SystemExit(0 if receipt["pass"] else 1)
