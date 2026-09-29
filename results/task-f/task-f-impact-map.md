# Task F impact map — frozen TD-v1.3 core release

Status: `COMPLETE — PASS / READY FOR PRE-G REVIEW`  
Authority: P `RCA-062–063` / U28F, 2026-09-28  
Purpose: implement and validate the reusable public-data RCA core without altering the frozen scientific method.

## Bootstrap identity

| Item | Verified value |
|---|---|
| P | `D:/Project/flash-ticket-platform`, branch `codex/rca-research-program`, bootstrap HEAD `576be4b6935c9a837e6f2bcc6356a89bfe61c6ac` |
| W | `D:/Project/flash-ticket-rca-research`, branch `main`, bootstrap HEAD `7ae411d45726d3cbc3ee10b0e70e9ca7a8c8b20a` |
| Executed/frozen TD-v1.3 | SHA256 `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971` |
| Task E source relationship | Current source raw bytes match the execution-time source manifests for C1/C5/integrated/RCD closure; documented line-ending snapshot differences are packaging-only |
| Existing unrelated change | P `README.md` was dirty before Task F and is excluded from this task |

## Primary mutation set

W:

- `src/rca/**`: F-owned reusable contracts, observation/numeric core, graph/ranking, C5, comparator boundary, packet, cache/provenance and orchestration.
- `tests/task_f/**`: scientific-contract, firewall, equivalence, canary and reproducibility tests.
- `configs/task-f-td13-frozen-release.json`: machine-extracted frozen release identity and selections.
- `results/task-f/**`: this map, validation receipts, representative development packets, run/equivalence/comparator evidence and independent review.

P:

- authority receipt and RCA decision registration;
- derived D/E/current/artifact status notices;
- `docs/research-rca/task-f-handoff.md` only after executable evidence exists.

## Read-only preservation set

- P canonical `docs/research-rca/task-d-method-and-experiment-specification.md` remains byte-identical.
- W `scripts/task_e/**`, `tests/task_e/**`, completed Task E configs/run directories, `results/task-e/**`, `results/task-d/**`, and `baselines/upstream/**` remain immutable reference evidence.
- Published Phase 1/2/assurance artifacts inform limitations only and cannot become runtime decision logic.
- final60 identities/telemetry/labels/graphs/features/predictions are not materialized or read.

## Implementation boundaries

- Machine-extract selected C1/C5 values and thresholds from sealed completed E artifacts; the registered development config is not treated as a selected release.
- Preserve mandatory contextual comparators `Local-MAX-MT`, `BARO-RANK-adapted-TD12`, and `RCD-RCAEval-adapted-TD12` as distinct roles.
- Preserve exact C1 common-evidence, zero-local all-tie, tie handling and R finite-perturbation semantics.
- Preserve exact C5 chronology, masks/membership, G/L/ALL capacity distinction, lag1, floors, thresholds/events and limitations.
- Packet/core path excludes root/fault/answer/root-presence/absolute-path/forbidden-tau/evaluator/final-outcome fields.
- No isolate/degree/reachability/travel×loss/auth gate, lag3 primary, floor replacement or other post-hoc rule.

## Validation and review plan

1. Frozen-manifest source/hash/canary validator.
2. Unit and scientific-contract fixtures for C1, R, C5, cache and packet firewall.
3. Relevant unmodified Task E regression suite.
4. Exact/tightly bounded E↔F equivalence on predetermined development smoke using only frozen selections.
5. Frozen-config end-to-end development validation and representative packets; no grid/reselection.
6. Bounded comparator runtime/equivalence checks using qualified environments/evidence; no 270-config rerun.
7. Governance audit, TD before/after hash, full P/W diff and evidence-integrity checks.
8. Fresh independent review of leakage, equivalence, graph controls, packet boundary and reproducibility.

## Stop conditions

Stop with evidence preserved for TD drift, conflicting selections, method ambiguity, material E/F mismatch, need for scientific-method or FlashTicket application change, required final60 access, overlapping unrelated changes, comparator fidelity failure, or unresolved higher-authority conflict.

## Explicit non-actions

No model/config search, no scientific reselection, no final campaign, no Task G/H/I, no FlashTicket application/API/schema/Saga mutation, and no commit/push.
