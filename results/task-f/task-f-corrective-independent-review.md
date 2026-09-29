# Independent Task F corrective assurance

Verdict: **PASS — TASK F CORRECTIVE CLOSURE READY FOR MINH TASK G AUTHORIZATION**
Mode: one fresh, read-only reviewer who did not implement the correction. The reviewer formed initial findings from the code and receipts before author handoff/status prose and made no file changes.

## Review sequence

The reviewer initially blocked f07 because an importable mutable issuance table let a fabricated `QualifiedRcdRunner` carry an arbitrary lambda to `rcd_run`, yielding `SUCCESS` with the RCD method label. On f08, the reviewer independently reached the closure-scoped `WeakKeyDictionary` through Python function introspection and repeated the arbitrary-function forgery without the factory. Both were classified **BLOCKED — IMPLEMENTATION DEFECT**; their runtime PASS receipts remain visible but did not justify closure. After the author removed the extensible registry and created f09, the same independent reviewer re-reviewed the final snapshot.

## Final f09 findings

1. `load_qualified_rcd` binds one exact runner after pinned v2/Task E source, patch, receipt, registered-parameter and runtime checks. `qualified_callable` requires object identity with that issued runner as well as intact function, identity, interpreter and code fingerprint. A second factory call is rejected.
2. A read-only Python 3.9 API probe rejected a plain function, lambda, callable object, direct constructor, forged handle before issuance, and a forged handle carrying the genuine issued function and identity after issuance. No ordinary API-level arbitrary-callable bypass was found. Hostile rewriting of private closure cells or module globals remains outside this in-process integrity boundary, as the source states.
3. f09's shifted and valid-empty success result objects are exactly equal to f06; valid empty ranking remains `SUCCESS`. f09 also records repeat determinism and rejection of a tampered real handle and cloned handle.
4. The reviewer independently reran the Task F suite: **70/70 PASS**. `verify_frozen_release` returned **PASS with 44 path/SHA references**. All 12 v2 source hashes and 10 f09 contract source/input hashes matched. v2 manifest SHA256 is `c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d`.
5. Canonical TD-v1.3 SHA256 remained `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`; v1 manifest SHA256 remained `18484bc4bb0c1d19e8f6936f12d8365a8ad69e16fffa2bf6ce5968189f0561e5`. The v1→v2 delta changes no scientific selection, split, evaluator or RCD parameter. The bounded f09 path uses synthetic fixtures and sealed Task E qualification evidence; no Task E campaign rerun or final60 access was found.

## Ruling and limits

There is no remaining blocking finding for the bounded Task F RCD qualification correction. Historical f07/f08 failures are preserved rather than retrospectively relabeled. This PASS is not Task G authorization, final60 permission, scientific improvement, final efficacy, FlashTicket validation or five-distinct-reviewer certification. Minh must separately authorize the PRE-G/Task G gate and its final-scope qualification work.
