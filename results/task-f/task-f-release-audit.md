# Task F release audit — author evidence index

Status: `PASS — TASK F RELEASE READY FOR PRE-G REVIEW`  
Scope: frozen TD-v1.3 public-data RCA core only. This is not an efficacy result, a final60 run, or authority to open Task G/H/I.

## Frozen identities

- Canonical TD-v1.3 SHA256 before and after implementation: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`.
- Task F frozen manifest: `configs/task-f-td13-frozen-release.json`.
- Manifest file SHA256: `18484bc4bb0c1d19e8f6936f12d8365a8ad69e16fffa2bf6ce5968189f0561e5`.
- Manifest canonical SHA256: `444406473da6e322579902958da5910133d3ad4c996f1aa170fe4dd2cc8d3570`.
- Ordered `src/rca/*.py` source-manifest SHA256: `383bf61c076eefd288b410a3f2bcbc4f20a7b78dd2cde3e06968bf6d0a5b3197`.
- Machine extraction/hash verification: `PASS`, 41 declared references verified.
- Development selection was extracted from sealed Task E outputs; no sensitivity result was substituted and no selection was rerun.

## Implementation boundary

- `src/rca/` implements immutable release contracts, C1 local evidence and L/O/R, exact finite R controls, C5 G/L/ALL/TV replay, mandatory contextual comparators, cache identity, packet sealing/firewall, and orchestration.
- `rca.adapters.QualifiedTelemetryAdapter` accepts no arbitrary callable. It verifies exact Task E loader/replay/integrated-adapter bytes and preserved qualification receipts before admission.
- Raw source hashes are derived from the trusted loader audit. Absolute paths, `s0`, conflict/event epochs, trace-key fingerprints and controller identity do not enter the observation or packet.
- Every frozen C5 trigger invokes TD12-INTEGRATED-MTL past-only diagnosis. A trigger before 360 relative seconds remains recorded as `INSUFFICIENT_HISTORY`; later triggers run the selected PPR without R or contextual comparators.
- Completed `scripts/task_e/**`, `tests/task_e/**`, `results/task-e/**`, `results/task-d/**`, and upstream baselines were not modified.

## Validation evidence

### Current release

- Task F unit/contract/equivalence suite: `65/65 PASS`.
- Frozen manifest verifier: `PASS`; C1 canaries, C5 lambda/eight detector thresholds, comparator roster, implementation bytes, adapter bytes/receipts and final-split firewall verified.
- `f04-qualified-public-loader-and-integrated-smoke`: `PASS` on the predeclared development smoke case. Raw telemetry produced exact sealed C1 L/O, exact sealed C5 predictions/residuals/scores, and exact integrated ranking scores at registered endpoints 630 and 1125. Trigger packets passed controller-clock/oracle firewall validation.
- `f05-final-development-validation`: `PASS`, 30/30 planned development cases, zero failures. The one frozen configuration reproduced C1 evidence/ranking, all eight C5 modes on the predeclared smoke, all 256 R draws and 2,713,600 registered proposals, exact raw/cache arrays, exact repeat packet hashes, and valid representative packets.
- `f06-final-rcd-boundary`: `PASS` in the declared Python 3.9 environment. Qualified shifted and valid-empty fixtures were deterministic; an unqualified callable failed explicitly. The 270-config development campaign was not rerun.

### Preserved attempts and interpretation

- `f01`, `f02`, and `f03` remain immutable earlier implementation/validation receipts.
- `f05-final-development-validation/rcd-boundary-smoke.json` is a visible failed attempt caused solely by invoking the RCD boundary under the default Python 3.12 environment. It was not overwritten. `f06` reran the same bounded smoke with the contract-declared Python 3.9 environment and passed.
- A duplicate broad Task E test invocation was interrupted when it entered campaign-style sensitivity work; no completed Task E output was written or replaced.
- Relevant unchanged Task E unit/contract regressions executed earlier in this Task F session passed 144 tests. Four campaign/coordinator harness modules require run contracts/CLI arguments and were not misclassified as semantic unit-test failures.

## Canaries and negative controls

- zero local mass remains common all-tie/no-evidence; there is no uniform PPR fallback;
- joint service permutation, metadata/candidate remap, future-suffix invariance and C5 time-translation canaries pass;
- raw/cache equality and repeat reproducibility pass;
- packet rank/score mutation, unresolved evidence, oracle fields and absolute paths are rejected;
- unqualified C5 bundle and arbitrary callable admission are rejected;
- early C5 trigger at 195 seconds is retained as `INSUFFICIENT_HISTORY` and does not load an integrated window;
- no isolate/degree/reachability/travel×loss/auth gate, lag3-primary substitution, or replacement for the registered `1e-12` fallback was introduced.

## Firewall and non-actions

- Validation inputs were development30 sealed numerics or the predeclared development raw smoke only.
- final60 IDs, telemetry, labels, graphs, features, predictions and outcomes were not materialized or opened.
- No Task G/H/I work and no FlashTicket application/API/schema/Saga change occurred.
- No algorithm, threshold, q, lambda, damping, floor, window or split was selected or changed.
- No commit or push was performed.

## Independent assurance and remaining gate

Fresh independent read-only review returned `PASS — TASK F RELEASE READY FOR PRE-G REVIEW` with no CRITICAL or blocking MAJOR finding. The development-only adapter requalification before G, G-side RCD aggregation/evaluator contract, mandatory packet validation, the frozen `1e-12` limitation and historical five-distinct-reviewer OPEN status remain explicit. This evidence does not authorize Task G.
