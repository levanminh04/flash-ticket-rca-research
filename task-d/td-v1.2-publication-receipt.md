# TD-v1.2 — Publication receipt and review handoff

Owner: Minh. Recorded 2026-09-26 16:20 UTC. This receipt records actual successful payload pushes and identifies the supplementary handoff files. Publication is not method approval; Task E remains NOT STARTED / NOT AUTHORIZED.

## 1. Destinations and payloads actually verified

| Repo | Branch | BEFORE | Pushed payload AFTER |
|---|---|---|---|
| [P — flash-ticket-platform](https://github.com/levanminh04/flash-ticket-platform/tree/codex/rca-research-program) | codex/rca-research-program | fa27a9d32873d957818ac389b8d3fc8f4e98b185 | [735695b9cc10bff03e4c7d738a0b59764de694dd](https://github.com/levanminh04/flash-ticket-platform/commit/735695b9cc10bff03e4c7d738a0b59764de694dd) |
| [W — flash-ticket-rca-research](https://github.com/levanminh04/flash-ticket-rca-research/tree/main) | main | 38a0d0362e1e51a56ba3a6334a7f7c13a036f603 | [592184c6fd7b4da90f501a6339d01701a4776b62](https://github.com/levanminh04/flash-ticket-rca-research/commit/592184c6fd7b4da90f501a6339d01701a4776b62) |

Both pushes returned success. Subsequent git ls-remote checks for the exact branch refs returned the same full SHAs as local HEAD. No force push or history rewrite. P README was excluded; W was clean after its payload commit.

Review the scientific changes at these immutable payload commits. Branches also receive publication/navigation handoff changes below; reviewers should capture actual branch tips and distinguish those from scientific revisions.

## 2. Exact payload inventory — 20 files

### P — 11 files, 1 new / 10 modified

| Root-relative file | Action / purpose |
|---|---|
| [docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md) | NEW: full mission và provenance |
| [docs/project/decision-register.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/project/decision-register.md) | MODIFIED: route đến phân sổ RCA |
| [docs/research-rca/RESEARCH-DECISIONS.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/RESEARCH-DECISIONS.md) | MODIFIED: append RCA-022–042, giữ lịch sử |
| [docs/research-rca/task-d-method-and-experiment-specification.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/task-d-method-and-experiment-specification.md) | MODIFIED: canonical TD-v1.2 |
| [docs/research-rca/task-c-research-decision-lock.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/task-c-research-decision-lock.md) | MODIFIED: TC-P2-v1.1 và scoped development rights |
| [docs/research-rca/MASTER-RESEARCH-PROGRAM.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/MASTER-RESEARCH-PROGRAM.md) | MODIFIED: MRP-v1.2 và selection/freeze/public roles |
| [docs/research-rca/SESSION-BOOTSTRAP.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/SESSION-BOOTSTRAP.md) | MODIFIED: resume đúng current policy |
| [docs/research-rca/task-b-dataset-capability-summary.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/task-b-dataset-capability-summary.md) | MODIFIED: historical-policy notice; facts B giữ nguyên |
| [docs/research-rca/ARTIFACT-MAP.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/ARTIFACT-MAP.md) | MODIFIED: routes evidence mới |
| [docs/research-rca/CURRENT-STATE.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/CURRENT-STATE.md) | MODIFIED: status/blocker; cập nhật publication riêng sau payload |
| [docs/research-rca/task-d-handoff.md](https://github.com/levanminh04/flash-ticket-platform/blob/735695b9cc10bff03e4c7d738a0b59764de694dd/docs/research-rca/task-d-handoff.md) | MODIFIED: contracts, OPEN owners và next action |

### W — 9 new files

| Root-relative file | Action / purpose |
|---|---|
| [task-d/td-v1.2-prechange-inventory.json](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-prechange-inventory.json) | NEW: prechange hashes/state |
| [task-d/td-v1.2-review-memos.md](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-review-memos.md) | NEW: initial/ring/delta review và independence limits |
| [task-d/td-v1.2-provenance-and-data.md](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-provenance-and-data.md) | NEW: 38 component rows và task compatibility |
| [task-d/td-v1.2-review-packet.md](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-review-packet.md) | NEW: A–J packet, exact file inventory |
| [task-d/audit_td_v1_2_public_metadata.py](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/audit_td_v1_2_public_metadata.py) | NEW: bounded metadata audit source |
| [task-d/td-v1.2-public-metadata.json](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-public-metadata.json) | NEW: 90-footer receipt và public pins |
| [task-d/validate_td_v1_2.py](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/validate_td_v1_2.py) | NEW: document/scope/synthetic-math validator |
| [task-d/td-v1.2-validation.json](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-validation.json) | NEW: prepublication 126/126 checks/hashes/limits |
| [task-d/td-v1.2-governance-validation.txt](https://github.com/levanminh04/flash-ticket-rca-research/blob/592184c6fd7b4da90f501a6339d01701a4776b62/task-d/td-v1.2-governance-validation.txt) | NEW: prepublication governance output |

## 3. Supplementary publication handoff — three file operations

- **P/docs/research-rca/CURRENT-STATE.md:** publication notice and route to the single independent-review prompt. This file was already in the payload and is updated again; no new method decision.
- **W/task-d/td-v1.2-independent-review-prompt.md:** NEW, one standalone prompt to assess and criticize the changes just pushed. Both GitHub repos, correct branches, BEFORE/AFTER, two relative roots P/W, full inventory, deep-reading/source-first requirements and subagent cross-review are explicit.
- **W/task-d/td-v1.2-publication-receipt.md:** NEW, this receipt.

Across scientific payload and supplementary handoff: **22 unique files — 11 in P and 11 in W**. CURRENT-STATE appears in two commits, so total file operations are 23. No two-prompt draft is published.

The supplementary commit SHAs are discoverable from branch history; this receipt does not embed its own commit SHA, avoiding a circular identity. The publisher verifies final branch tips against remote refs after pushing the handoff.

## 4. Validation and preservation

- Before publication: archived TD-v1.2 receipt reports **126/126 PASS** for document/history/scope/hash/links/synthetic mathematics.
- Archived governance output: PASS with one impact-map warning, explained by U26 authorization and original file scope.
- Payload hashes were checked against the receipt before staging.
- Staged whitespace checks passed in P; W uses a temporary core.whitespace check recognizing CRLF endings while retaining ordinary whitespace checks. Historical CRLF receipts were not rewritten merely to make their bytes LF.
- Git normalized CRLF to LF for the P mission text. Only that payload file differs from its prepublication byte hash; normalized text is identical. All other 19 payload Git blob SHA-256 values match prepublication working-file hashes.
- No archived receipt was rerun or overwritten after publication. Hardcoded roots, prechange HEAD and untracked-file scope assumptions in original validators remain historical, not portable live assertions.
- No empirical selection/sensitivity, baseline training/reproduction, model benefit, runtime firewall or target/LLM evaluation is implied by publication.

Supplementary handoff checks: staged whitespace checks PASS; the singular prompt contains no local drive paths. Same-reviewer subagent critique found and closed an exposure-order contradiction: technical/authority/data diff is read before initial opinion, reviewer verdicts and remaining diff afterward; complete diff coverage remains required. Governance audit of the publication notice completed PASS with 0 warnings (changed_files=2, including the unrelated README). No new independent-review assurance is claimed by this prompt-quality check.

P README remains uncommitted with SHA-256 3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274. No application/API/schema/raw/legacy mutation or unrelated commit.

### Immutable payload Git blob SHA-256

Hashes below are computed from git show COMMIT:PATH bytes, not from GitHub-rendered text.

| Repo / file | SHA-256 |
|---|---|
| flash-ticket-platform/docs/evidence/project-direction/2026-09-26-rca-task-d-redesign.md | a265d1ded1434926ff8504bc5d93cd419a5efe2beb5d3c3acfc53670dc8deb5f |
| flash-ticket-platform/docs/project/decision-register.md | ad9fc43fb900b966f611c4210e95edf522c87cf985c764cf1bd54f66d9834d12 |
| flash-ticket-platform/docs/research-rca/ARTIFACT-MAP.md | ef2d5dda35bcf0105ed183d59a7b127e36b2ef05c86ee864a8b0a585719d15cc |
| flash-ticket-platform/docs/research-rca/CURRENT-STATE.md | 088d4f227a1c81e5cb4a63bacae1f8012e84ac01d77a8b4d171d86a424b576db |
| flash-ticket-platform/docs/research-rca/MASTER-RESEARCH-PROGRAM.md | 1690993ca62fbe3d7591d1c4f13bc352e3963aa276657268e559ee214d07f290 |
| flash-ticket-platform/docs/research-rca/RESEARCH-DECISIONS.md | 3c368455af658693b15162a66bdbbbf663f416f61a98c520d438d1d5fcee56f7 |
| flash-ticket-platform/docs/research-rca/SESSION-BOOTSTRAP.md | d73568e391df007d082731ab8c9c6e78358c34d02e367ae117a46e8d71abf001 |
| flash-ticket-platform/docs/research-rca/task-b-dataset-capability-summary.md | fa8d9fd2fcc060221b146bc3ae90982efe306c07c1943fcce341ee166b28198c |
| flash-ticket-platform/docs/research-rca/task-c-research-decision-lock.md | 922854439f1bf3d7df04b5db62c55911430ed618061e8e362b9fb7f31ed2d7f1 |
| flash-ticket-platform/docs/research-rca/task-d-handoff.md | e4edee8561233eca727f02d9aacf060171f5cc25cbcf39b28043036003e88409 |
| flash-ticket-platform/docs/research-rca/task-d-method-and-experiment-specification.md | 985f1c5fc983422272dfbde8b69ed5ff98ee4fdd1631af075d03788c3770ad54 |
| flash-ticket-rca-research/task-d/audit_td_v1_2_public_metadata.py | db5b65a33c78288370676c3b6e927a8464a9247c5238781353e3cab35bfa660d |
| flash-ticket-rca-research/task-d/td-v1.2-governance-validation.txt | 4d46ea17fd214244b957e5bca5064c8fbb481c5efe7678ce47b648b41e2656d1 |
| flash-ticket-rca-research/task-d/td-v1.2-prechange-inventory.json | b3bd19a0052a42b9ed98a7d1716283d917fabab0593f3a5f55c13d5373249c94 |
| flash-ticket-rca-research/task-d/td-v1.2-provenance-and-data.md | 9797c70a0eda28b031034a7ff9028e330fad1d5c2b6bdd42ae3189646b0d796a |
| flash-ticket-rca-research/task-d/td-v1.2-public-metadata.json | fa582ab3628056aaf98b327a8947c581748312c3d37c47fd370ff07a1ede4586 |
| flash-ticket-rca-research/task-d/td-v1.2-review-memos.md | 2171e227274171c096c856f4f042a1e6c2fa02d427092a71f38b303e34799845 |
| flash-ticket-rca-research/task-d/td-v1.2-review-packet.md | c3f2f73f3518e3c9be5fe7b9a10548b9cf6b6b9e7ef71f4fa1d137cef75e6a29 |
| flash-ticket-rca-research/task-d/td-v1.2-validation.json | a2c2fd9630e15df10275caf7126c4b69ac95b9595088b4c152d3956f5e6e4090 |
| flash-ticket-rca-research/task-d/validate_td_v1_2.py | 67db8f29d75c14dfdfa5b0c12c347e5406dcf6c2b471e71a3bc0ce734ba66417 |

## 5. What the next agent is asked to do

Use [the one review prompt](td-v1.2-independent-review-prompt.md). Purpose: **independent assessment and criticism of the changes just pushed**. It is not a redesign or Task E assignment.

Resolve paths with only P=flash-ticket-platform/ and W=flash-ticket-rca-research/. Earlier local/uncommitted/not-pushed statements in the immutable prepublication packet/handoff are historical snapshots; this receipt and live CURRENT-STATE own the later publication facts.

C1 primary/C5 first-class, candidate method status, development/final firewall, DT18 obligations and human approval remain unchanged. Five-distinct-reviewer assurance is still OPEN; the earlier three agents/five roles are not relabeled as five independent reviewers.
