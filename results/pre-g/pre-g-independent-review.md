# Independent corrective PRE-G review and Task F re-review — 30/09/2026

**Current verdict: PASS_METADATA_ONLY_WITH_LIMITATIONS.** PG-ADV-01 and PG-ADV-02 are closed for ordinary callers after correction. Frozen Task F re-review is PASS with its existing limitations. This is technical evidence for Minh to consider authorizing Task G entry validation; it is not Task G/campaign authorization or scientific/five-reviewer approval.

## Historical challenge and authorized correction

The initial review below reported PASS on 29/09. A subsequent independent adversarial review in the current chat returned BLOCKED: (PG-ADV-01) synthetic rows could change scope/digest and rehash into qualified evaluator evidence; (PG-ADV-02) HF_ENDPOINT could redirect the default client to a fake descriptor API while the receipt claimed OFFICIAL_HF_API. Those findings superseded the initial qualification conclusion. Minh authorized the two proposed corrections and another Task F review on 30/09, recorded in U30PG/RCA-068–070. Both failed boundaries and the initial PASS history are preserved; this corrective result does not erase them.

## Reviewer /root/pre_g_fix_review — separate read-only agent

Actual independent execution: PRE-G suite 25/25 PASS with W .venv Python and -B; four source/test hashes match the correction contract registered before requalification. Ordinary-caller probes reject synthetic scope promotion plus rehash with arbitrary qualification digests, private sealing helper output, and copied issued qualification with altered ranks, owners, input, candidates or qualification digest. Both default evaluation and allow_synthetic_fixture=True reject forged qualified seals before scoring. Exact issued JSON roundtrip remains valid in the same interpreter; fresh-interpreter verify/evaluate rejects it. Test patches only created test-issued fixtures; they were not presented as production bypasses.

A real subprocess with HF_ENDPOINT pointing to a loopback fake descriptor server sent zero requests to that server. The qualifier used https://huggingface.co, returned PASS_METADATA_ONLY, 180 descriptors, declared bytes 1,309,388,082 and identity digest 2b51110896bf23f6f2264e85458b814c1cd7871c50e047d814aeda3943b32d94. No raw final60, explicit labels or outcomes were opened. Verdict: PASS_METADATA_ONLY_WITH_LIMITATIONS; no new ordinary-caller blocker found in the corrective code.

## Reviewer /root/task_f_rereview — separate read-only agent

Frozen Task F tests 70/70 PASS under W .venv Python 3.12; verifier v2 PASS on 44 references; Task E synthetic math/firewall 34/34 PASS. TD/manifests, all 12 v2 source hashes and 10 f09 references match; 11 scientific v1/v2 fields remain identical. Fresh pinned Python 3.9 synthetic execution gives SUCCESS for seeds 420/421/422, bins 5. Seed420 and valid-empty results match f06 exactly; lambda, cloned handle, tampered identity and second factory issuance are rejected. No file mutation, raw final60 access or campaign was performed. Verdict: PASS_FROZEN_TASK_F_WITH_LIMITATIONS; no new Task F blocker found.

## Current readiness and limitations

Ready for Minh to authorize opening G at entry validation and campaign preparation. Final campaign is not ready to execute immediately: actual-use raw source/schema/clock/joins/window/masks and adapter admission must pass at the authorized gate; durable trusted prediction provenance must be stored and verified before evaluator label opening; the actual G controller/firewall needs independent validity checking before run. PRE-G verifies current-interpreter issuance before using/scoring a supplied root_index; it does not prove the caller's earlier label-open order. The qualified registry rejects reopening in a fresh interpreter and is not durable or hostile-runtime attestation.

Task F adapter stays DEVELOPMENT_QUALIFIED__PRE_G_REQUALIFICATION_REQUIRED. Metadata case IDs can encode service/fault tokens and stay opaque controller locators. LFS descriptors do not certify local raw bytes or final conversion. E1 all-90 historical exposure and five-distinct-independent-reviewer OPEN / NOT FACTUALLY CERTIFIED remain. These reviewers do not certify that separate historical/formal requirement. No final efficacy or FlashTicket validation is claimed.

Machine evidence and current source hashes: results/pre-g/pre-g-readiness.json (v2); preregistered correction contract: results/pre-g/pre-g-run-contract.json (v2). The exact initial JSON receipts/contracts are retained as raw_utf8 snapshots with their original SHA256 values inside those v2 files.

---

## Historical initial review — 29/09/2026, qualification conclusion superseded

The following original text is preserved for provenance; read the current corrective verdict above.

# Independent PRE-G review — 29/09/2026

**Verdict: PASS — METADATA-LEVEL PRE-G ONLY, WITH EXPLICIT LIMITATIONS.** This review does not certify raw final-scope ingestion, final60 adapter behavior, final efficacy, or Task G authorization. It is one independent PRE-G review, not the historically required five-distinct-independent-reviewer certification.

## Reviewed boundary and evidence

- Authority: P `docs/evidence/project-direction/2026-09-29-rca-pre-g-authorization.md` and `RCA-064`–`RCA-067` authorize only source metadata/ingestion-contract qualification, adapter compatibility without row-level final60, and three-seed orchestration on synthetic/development evidence. The P readiness document and W run contract preserve that boundary.
- Frozen method/release: canonical TD-v1.3 SHA256 `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971` and Task F v2 manifest SHA256 `c46b870bccdae1198292abc5850a83a3fa7e7f702286ceeaa07258074391801d` independently rehashed; no tracked diff in W `src/rca/`, `scripts/task_e/`, or the v2 manifest. The frozen verifier reports PASS on 44 path/SHA references; adapter scope remains `DEVELOPMENT_QUALIFIED__PRE_G_REQUALIFICATION_REQUIRED`.
- Source: inspected `scripts/pre_g/source_qualification.py` and tests. It projects only `case`, `dataset`, `repetition`, `has_logs`, `has_traces` from the pinned local metadata; it does not request explicit label/outcome columns or raw telemetry rows. It derives 60 final locators/20 cells without publishing identifiers, then requests official object descriptors only. I independently reran the production `api=None` path: `PASS_METADATA_ONLY`, `OFFICIAL_HF_API`, 180 exact LFS descriptors at revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`, identity digest `2b51110896bf23f6f2264e85458b814c1cd7871c50e047d814aeda3943b32d94`. Injected APIs are marked `SYNTHETIC_TEST_ONLY`; the local raw-audit helper rejects non-`synthetic-` case IDs before file access.
- Controller: inspected `scripts/pre_g/controller_contract.py` and tests. Public caller-supplied outputs are sealed as `SYNTHETIC_UNQUALIFIED` and rejected by the evaluator unless an explicit fixture flag is used. The registered run path prechecks an issued `QualifiedRcdRunner`, imports the frozen comparator directly, calls seeds 420/421/422 with bins 5 on equal deep-copied 600-row frames, converts each exception to an explicit failed seed, and seals before evaluator-only root access. Metric-rank first-owner mapping, unknown-key coverage, one worst tie for unranked services, failed-seed zero, and arithmetic mean of three per-seed metrics are exercised. Path-like identifiers, malformed ranks, nonfinite vectors, and seal tampering fail closed in tests.
- Validation: I independently ran the PRE-G unit suite, **21/21 PASS**, and recomputed the four new source/test SHA256 values and run-contract SHA256; they match W `pre-g-readiness.json`. The execution receipt records Task F regression **70/70 PASS** and a bounded Python 3.9 qualified-runner smoke using a synthetic 600-row frame, with 3/3 registered seeds successful. Neither used final60 telemetry or labels in this PRE-G review.

## Limitation and next gate

The metadata `case` identifier is a source locator but structurally may encode service/fault tokens. The qualifier treats it as opaque and emits only counts/digests; this is **not** proof that the metadata layer contains zero inferable label information. Official LFS descriptors establish remote object identity only, not downloaded local bytes, Parquet row/schema/clock/join quality, feature availability, or final raw adapter compatibility. The controller's SHA seal detects modification but is not a durable Task G provenance/label-separation receipt; the synthetic fixture evaluation is not a final outcome. Historical E1 all-90 outcome exposure and the five-distinct-reviewer `OPEN / NOT FACTUALLY CERTIFIED` status remain disclosed.

**Required before any Task G campaign:** separate explicit authorization from Minh; actual-use final raw source/adapter checks at the authorized gate; durable prediction sealing and verification before evaluator label opening; stop on source, compatibility, or firewall failure. No final60 raw file, answer/label, outcome, prediction, or score was opened or produced for this review.
