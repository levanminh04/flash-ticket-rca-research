# Task F corrective closure — RCD qualification boundary

Status: **TASK F CORRECTIVE CLOSURE COMPLETE — READY FOR MINH TASK G AUTHORIZATION**
Scope: bounded implementation correction only; no Task G authorization, scientific amendment, Task E campaign rerun, or final60 access.

## Adjudicated finding

The published v1 `rca.comparators.rcd_run` accepted any `callable(upstream_rcd)`. The module function was directly importable, and a plain function could return `SUCCESS` under the `RCD-RCAEval-adapted-TD12` method label. The f06 runner used `load_pinned_rcd` correctly, but qualification was a caller convention, not an enforced core boundary. This was a **blocking Task F implementation/qualification defect**, not a TD-v1.3 or Task E scientific defect.

## Corrective release

- Historical published v1: W commit `e70f40f5549574ac4518436cc476087f8cf2d9f6`; `configs/task-f-td13-frozen-release.json` SHA256 `18484bc4bb0c1d19e8f6936f12d8365a8ad69e16fffa2bf6ce5968189f0561e5`. It remains unchanged and valid as historical release evidence.
- Successor v2: `configs/task-f-td13-frozen-release-v2.json` SHA256 `c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d`; 12 ordered source files, source-manifest SHA256 `129de4d2ef146ed1277e7c87be458d63b40f14d0fdb13341d3b8632c6909c1d3`; predecessor commit and manifest are explicit.
- `load_qualified_rcd` checks v2 release integrity, predecessor identity, exact Task E source/patch/original and patched RCD hashes, qualification report and run contract, registered parameters, Python 3.9 interpreter/runtime and package provenance before issuing one runner in the isolated process. `rcd_run` admits only that exact runner and checks its function, identity, interpreter and code fingerprint. Ordinary caller-supplied functions, callable objects, cloned handles and tampered handles fail explicitly.
- v1→v2 changes are schema/status, implementation/source identity, predecessor linkage and an RCD qualification-contract reference. TD, dataset, split, C1/C5 selections, comparator scientific settings, evaluator, packet, R control and final60 policy compare exactly with v1. No RCD algorithm, upstream revision, adaptation, seed/bin, gamma, localization, dataset argument, input frame contract or ranking semantics changed.

## Attempts and validation

| Attempt | Bounded runtime | Independent review | Interpretation |
|---|---|---|---|
| `f07-qualified-rcd-boundary` | PASS | BLOCKED — importable mutable issuance table allowed a fake callable | Preserved attempt; not closure evidence |
| `f08-qualified-rcd-boundary-repair` | PASS | BLOCKED — closure-exposed mutable registry could be forged without factory | Preserved attempt; not closure evidence |
| `f09-qualified-rcd-boundary-single-issuance` | PASS | PASS | Final corrective evidence |

The f09 run contract SHA256 is `1289987792d6d69fb1aad102b4bd7d34500b6d1a262f87966a2c6a703de5f5de`; receipt SHA256 is `3ce326cd22c08763d3e7725df9c9a8282de0fd4d3768af6817609648cde149ea`. It ran from the generated contract under the pinned Python 3.9 environment with synthetic shifted and valid-empty fixtures only. Both complete success result objects equal f06 exactly; repeat execution is exact; lambda, tampered identity/function and a cloned genuine handle fail with `unqualified_rcd_runner`. The sealed 270-configuration Task E RCD development evidence was referenced, not rerun.

- Author Task F suite: **70/70 PASS** under W `.venv` Python 3.12; fresh independent rerun: **70/70 PASS**. Focused qualification and release tests pass.
- `verify_frozen_release`: **PASS**, 44 declared path/SHA references checked; all 12 source hashes and all 10 f09 contract source/input hashes match. Scientific v1/v2 canaries pass.
- Canonical TD-v1.3 SHA256 before and after: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`. v1 manifest and f01–f06/Task E evidence were not modified. f07/f08 receipts were not overwritten.
- No development telemetry was loaded for the corrective smoke. No final60 IDs, data, labels, features, predictions or outcomes were opened or materialized; Task G/H/I were not started. No commit or push was made.

## Boundary and next gate

This is an ordinary in-process integrity contract, not a sandbox against hostile code that rewrites private Python closure cells or module globals. The independent reviewer found no bypass through the public callable/handle API. Qualified development ingestion remains development-only; final-scope source/adapter qualification and the G controller's three-seed aggregation, owner mapping, worst-tie padding and evaluator scoring remain for a separately authorized PRE-G/Task G gate. Five-distinct-independent-reviewer certification remains `OPEN / NOT FACTUALLY CERTIFIED`. This closure does not approve a final campaign, final60 access, efficacy claim or FlashTicket transfer.
