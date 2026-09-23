# TD-v1.1 — Independent adversarial delta review

Reviewer: independent subagent td11_delta_review. Date: 2026-09-23. Owner of decisions: Minh. Intent: EXECUTE only this authorized review artifact; reviewed specification is FORMATION and remains CANDIDATE. This is neither human approval nor authorization for E.

## 1. Frozen first review pass — preserve this section

This pass was formed before reading the TD-v1.1 source-first review, reconciliation proposal, or the parent agent's proposed adjudication. It attacked the actual revised specification, not whether a checklist had been filled. No raw corpus was downloaded/read, no dependency installed, no baseline trained/run, no application changed. Synthetic standard-library calculations only.

Protocol reviewed: P/docs/research-rca/task-d-method-and-experiment-specification.md, TD-v1.1 DRAFT, byte SHA-256 **52f79f78340be790a5cc1d1eb2d068def6b397197d7208f4d5d4a2b1b558b9c5**. P HEAD/old comparator: **6bd04e625926e923301cc6bb1433682f01fd87fc**; old protocol git-blob SHA-256 **9822a92081fb5d958fde35b68d274906bd36ee66288017645a7ec6840a2c1c4d**. W HEAD **c7e47fdcc69c53876f7bd3f1a5e71ef89c59ccf6**. Both working trees were already dirty; parent-owned changes were left intact. P is D:/Project/flash-ticket-platform; W is D:/Project/flash-ticket-rca-research.

Direct read set for independent opinion: P/AGENTS.md; entire govern-capstone-work/SKILL.md and project-authority-and-gates.md; DT18; roles; lien-ket-rca; complete current TD-v1.1; git comparator/delta TD-v1.0; complete Task-C decision lock; RESEARCH-DECISIONS RCA-001–021; complete B capability digest and B CLOSED §12.1–12.20; advisor evidence 22/08 and new 23/09 including Minh's clarification; current Master program, current-state and D handoff; W Task-D exposure ledger. User request at C:/Users/84583/.codex/attachments/061cebbe-79ec-4ead-9ddd-64c59a4ad865/Pasted text.txt governed the 20 attacks below. Source-first v1.1 and reconciliation artifacts were intentionally withheld during this first pass. Any subsequently read historical comparison/review is supplementary, not the origin of this opinion.

### Independent verdict at this snapshot

**0 CRITICAL; 0 MAJOR established. 3 MINOR specification clarifications.** The revision fixes the material graph-before-alert mismatch with an actual changed operator and maintains the primary C1 contract. It does not demonstrate runtime, scientific benefit, all-log compatibility or full public-dataset extension completion. The three points below should be clarified in D so E receives exact invariance/evaluation obligations; they do not establish invalid scientific inference or require reopening C1.

| ID / severity | Exact evidence / counterexample | Concrete remedy | Owner / timing / first-pass disposition |
|---|---|---|---|
| DR11-01 MINOR | TD §10.2 defines a 60s query and 10s score endpoints; §10.6 labels a system-bin by start/end but never explicitly says the scored bin is the final 10s interval. Treating the full query as that bin would exclude up to six straddling bins instead of one near injection. | Bind score S_t to evaluation bin [t−10,t); state the 60s query is feature history, not the unit assigned injection-regime GT. Preserve per-incident/macro denominator and warmup/unavailable accounting. | D, before E implementation; OPEN clarification. |
| DR11-02 MINOR | TD §4.2 selects past log samples using SHA256(source_file_sha256 plus original_row_ordinal), whereas §§10.6/13.1 require future-suffix/packet invariance. A harmless future suffix changes the full file hash and hence the past sample set: a deterministic 12-row toy changed selected ordinals [1,4,5] to [0,3,1]. Numeric counts/scores are unaffected; exact evidence packet content is not prefix-stable. | Define future-invariance explicitly for numeric arrays, scores, decisions and rank with provenance fields excluded, and disclose retrospective hash-based sampling; or specify prefix-stable C5 sample identities/selection. Do not claim exact packet equality across changed raw-file versions while retaining this sampler. Packet immutability before/after LLM is a different invariant. | D before E; E/F tests the chosen distinction. OPEN clarification, not proven scoring leakage. |
| DR11-03 MINOR | TD §10.4 streak is an unbounded count, but §10.6 says crop comparison uses state after 380s. Under sustained exceedance, a long replay can have streak=39 while a cropped replay has streak=3 even when their trigger decisions are identical with carried last_trigger. The old §10 wording required decisions, not exact state equality. | Require behavioral alert/decision equality after enough identical history with carried refractory state; compare streak only as min(streak,3), or preserve full prior state if literal equality is required. Keep the grid origin explicit on crop. | D before E fixtures; OPEN clarification. |

### Required 20 invalidation attacks

| # | Attack / independent result | Exact support and limits |
|---:|---|---|
| 1 | C1 accidentally changed? **No primary contract change found.** | Stdlib extraction equality against old git content for five blocks: operational estimand; split/exposure/windows/numeric channels; solver/controls/baselines; inference/verdicts; RR/Hit tie metrics. New NDCG is disclosed secondary only. §5 direction rationale changed, projection/operator did not. |
| 2 | Graph before alert? **Yes by specification and toy mathematics.** | §§10.3–10.4: a→q=.5a+.5Pq→max(q)→threshold/persistence. a=(1,0), connected two-node P yields q≈(2/3,1/3), while identity yields a. With threshold .8 raw exceedance changes. Real performance NOT VERIFIED. |
| 3 | Explicit M/L/T roles? **Yes.** | §§4/10: numeric metric channels; span occurrence deviation; log-row volume deviation; raw text only packet support. Double log compression and no semantic log anomaly claim are explicit. |
| 4 | TRACE_STRUCTURE versus TRACE_EVIDENCE? **Separated.** | §10.1, candidate/graph rule §10.2, modality table §10.3. Candidate dependence on traces is also disclosed. |
| 5 | Hidden trace topology in metric-only arm? **No misleading label in protocol.** | C5-G-M is metric node evidence with trace-derived candidates/topology; §10.3 forbids trace-free caption. F/G captions must inherit this wording. |
| 6 | Log-to-edge mapping invented? **No.** | §§4.2/10.2 exact service/time node mapping; explicit exclusion of span/edge correlation. |
| 7 | Modality comparison interpretable? **Yes, conditionally.** | Fixed denominator3, common input mask/V/windows/P; M→MT→MTL measures nested addition under the same calibration policy. It does not estimate independent modality effects/interactions or ranker-only contribution. |
| 8 | Missing logs fair? **Defensible bounded rule, not invariance guarantee.** | Missing0+mask, no renormalization, no incident drop; thresholds fit separately on same dev endpoints. Logless MT and MTL raw scores can agree while thresholds/alerts differ. §10.6 acknowledges this. All-used-file compatibility remains E/F-owned. |
| 9 | Graph AD exceeds RE2-TT truth? **No in stated claims.** | B §12.9/12.12 and TD §10.6 limit truth to system-bin injection regimes; no node/path/onset/production claim. |
| 10 | P/R/F1 valid target? **Yes after DR11-01 precision fix.** | System-bin injection-regime agreement, not affected services or ranking; macro60/pooled descriptive, no bin-IID CI. Numerical failure selection and coverage must remain explicit. |
| 11 | NDCG useful/redundant? **Correctly secondary.** | §7 single binary root, tie-aware cutoff formula, failure0. Strict ranks transform rank; cutoff/discount can reverse aggregate ordering: MRR A=(1,6)=.58333>B=(2,3)=.41667, NDCG5 A=.5<B=.56546. Thus not independent truth or extra confirmatory support. |
| 12 | Experiment count exploded? **No.** | Primary unchanged 3 arms plus 2 context comparators; C5 has four configs with nested evidence and one matched local control. No parser sweep, GNN, C5 rewiring or full modality factorial. |
| 13 | Silent new RQ? **No.** | §§0/9/10.3 C1 primary preserved; C5 is supporting capability, all C5 comparisons descriptive and cannot rescue C1. |
| 14 | E must invent methodology? **No major gap found; three minor contract clarifications above.** | Formulas/window/channel masks/operators/calibration/alert state/profile/evaluator are otherwise specified. E/F owns implementation evidence and inadequate-calibration diagnosis, not silent method redesign. |
| 15 | Integrated pipeline meets advisor method guidance? **Specified path does; execution and multi-public extension remain incomplete.** | Graph-before-alert, node M/T/L, RCA, operation/log packet and downstream LLM exist in §§10–11. §15 extension gate prevents treating TT+FlashTicket as two public datasets. |
| 16 | DT18 aligned? **Yes in scope.** | §15.2 preserves actual distributed-system construction/evaluation, graph M/T/L, target transfer and UI/runtime responsibility. D neither implements nor approves system changes. |
| 17 | Provenance correct? **Yes at reviewed scope.** | New 23/09 receipt distinct from 22/08; original date/channel NOT VERIFIED; RCA-018–021 record Minh's clarification without treating old demo-only guidance as current scope. |
| 18 | Revision creates problems? **Minor invariance/evaluation precision risks captured above.** | State wording changed; larger C5 scope exposes inherited full-file-hash sampling to future-invariance tests. No established new severe leakage or label fitting. |
| 19 | Old D assumptions inconsistent? **C1 unchanged; superseded C5 made explicit.** | §§0/8/9/10/11 separate old primary M+T from triggered MTL. Current-state/handoff still v1.0 at review time are parent-owned pending propagation, not evidence to override D. |
| 20 | Fix merely relabeling? **No.** | Old metric-only detector now uses M/T/L, rolling observed P, separate local control and numeric graph-conditioned S before threshold. It is simple smoothing, not claimed GNN/structural anomaly detection. |

### Additional issues discovered beyond the prompt

DR11-01–03 are concrete implementation/invariance ambiguities found by this reviewer, beyond matching the requested feature list. No additional evidence-backed CRITICAL or MAJOR issue was found. These are not used to fabricate a reason to reopen human decisions.

### Observations and NOT VERIFIED items

- OBSERVATION, D/G: external runnable graph RCA/AD comparator is absent; current package answers the bounded within-method contrast and contextual comparison, not SOTA superiority. §6 and §1.1 disclose this. Adding a comparator is not required to rescue identifiability of C1.
- OBSERVATION, G/H: reference smoothing can suppress an isolated true failure and a rolling reference can absorb persistent faults. Reporting weak/negative C5 performance is a valid outcome; no post-result threshold/window rescue is authorized.
- NOT VERIFIED, E/F before freeze: actual all-file metric/log schemas and joins; dev calibration reachability, endpoint coverage, resources, numerical behavior, baseline pin/license/fidelity, and reference-window control mobility. D's toy checks do not close these.
- NOT VERIFIED, E/Minh then F/G/J: exact second public release, task/GT compatibility, scope and execution. §15 assigns an honest path; multi-public results are not already complete.
- NOT VERIFIED, G: every performance/effect estimate. H: FlashTicket independent healthy/fault truth and transfer. I: LLM faithfulness/usefulness and operational rank invariance. No runtime success is certified here.

### Evidence classification and authority

Text/hash/section-equality/math observations above are FACT within the checks' stated scope. C1/C2–C5/LLM roles and present scope clarification are USER_CONFIRMED via RCA-001–021. Technical choices remain CANDIDATE. Actual execution facts remain OPEN with their task owner. No decision was promoted and E remains **NO / NOT AUTHORIZED**.

## 2. Verification after response — append only

Pending revised snapshot and parent response. Preserve §1 verbatim; append exact hash, accepted/rejected remedies, verification and final disposition here.

### 2.1 Closure of DR11-01–03 — 2026-09-23

Re-read corrected TD §10.6 and checked against the first-pass findings. Corrected protocol byte SHA-256: **ee80e909f33288ca450f33c568e3ce4ff071510d82b588c556a42f95da8a8766**. The source remains CANDIDATE; changes were made by the protocol owner, not by this reviewer. First-pass snapshot above was preserved before reading the response.

| Finding | Actual revision | Independent verification | Final disposition |
|---|---|---|---|
| DR11-01 | §10.6 now explicitly attaches each endpoint score to the final [t−10,t) bin, not the full 60s query. | Direct text review plus deterministic exact-clause assertion. Injection-straddling exclusion now has one unambiguous unit. | **CLOSED — MINOR specification clarification**; E still must execute bin-boundary fixtures. |
| DR11-02 | §10.6 restricts future-suffix invariance to normalized numeric evidence, graph, score, decisions and ranks with fixed config/calibration/opaque case keys. A new retrospective-packet paragraph explicitly discloses changing excerpts/IDs under file rehash and forbids exact packet/prompt/explanation invariance claims. | Direct review confirms hash/text never enter detector/ranker, and packet immutability under LLM is kept distinct. The counterexample remains true but is now a disclosed limitation outside the asserted invariant. | **CLOSED — honest scope clarification**; no claim of prefix-stable online explanation. H owns any later versioned streaming adapter. |
| DR11-03 | §10.6 requires decision equality after identical history and carried last_trigger/refractory state; explicitly allows different unbounded streak values and explains the streak≥3 condition. | Direct review and exact-clause assertion. Sufficient history recovers the decision-relevant predicate; literal raw-state equality is no longer asserted. | **CLOSED — MINOR fixture contract clarification**; E/F must implement state/crop tests. |

Repeated all five C1 section-equality checks on the corrected snapshot: **5/5 true**. Additional corrected-clause checks: **5/5 true**. The earlier graph-before-threshold toy and NDCG calculations are mathematical specification checks, not measured research outcomes. The governance audit command was invoked from canonical P after the review artifact was written; no new scientific acceptance is inferred from that command or from repository hygiene.

Final independent disposition for this snapshot: **0 unresolved CRITICAL, 0 unresolved MAJOR, 0 unresolved MINOR findings from this review. Scientifically ready for Minh's human review at the specification level.** All E/F/G/H/I execution facts and the selected second-public-dataset extension remain OPEN exactly as identified above; no experiment or release is invented to close those items. The public-extension path assigns owners/scope acceptance without claiming that existing TT+FlashTicket work already meets multi-public empirical coverage.

Report-facing conclusions: C1 primary experiment unchanged; NDCG is descriptive; C5 now truly conditions the anomaly score on graph before alert; M/T/L are accounted for as available bounded evidence; nested modality comparisons are interpretable only under the declared operating policy; RE2-TT cannot yield node anomaly or production-onset truth; FlashTicket obligations remain under DT18. **Task E authorization: NO.**

Only this review file was created/modified by this reviewer. No decision status was promoted, no canonical protocol/status file edited, and no commit/push was performed. Later editorial status/header changes require a new recorded hash or a narrow final delta check; this closure does not certify unseen future edits.

### 2.2 Final REVIEW_READY snapshot — narrow hash verification, 2026-09-23

Final protocol byte SHA-256: **3810078976ed8466848ed04f812d2b3ed5e64281d1e16d4914ebb3fb621a7ee1**. A byte-level verification replaced only the single header phrase “REVIEW_READY after independent delta review TD-v1.1” with its exact prior Vietnamese DRAFT phrase in memory. The reconstructed bytes hashed to **ee80e909f33288ca450f33c568e3ce4ff071510d82b588c556a42f95da8a8766**, exactly the independently verified §2.1 snapshot. Therefore no scientific body or other byte changed between those snapshots. No file was rewritten for this comparison.

The §2.1 closure applies unchanged to this final snapshot. REVIEW_READY means prepared for Minh's human review, not human APPROVED, measured success, or authorization to execute E. **Task E: NO.**

Canonical finding identifiers in this review are **DR11-01, DR11-02, DR11-03**. Temporary parent reconciliation identifiers DV11-01/02/03 refer to the same findings in that order; derived handoff/reconciliation records should use DR11-01/02/03 to avoid competing IDs. Only this review artifact was appended in this follow-up.

### 2.3 Final editorial provenance correction — narrow verification, 2026-09-23

Final protocol byte SHA-256: **9a70e64db570916b9f02fcc81fab3f4bf7cef0313f5c2de213a9eb0a8d690f3c**. Independent byte-level check reversed only two editorial deltas in memory: (1) the header now identifies the prior continuation contract as historical authorization for TD-v1.0 and points to §0 for the current revision authorization; (2) one whitespace-only line before §11 no longer contains a trailing space. Reversing exactly those changes reconstructed **3810078976ed8466848ed04f812d2b3ed5e64281d1e16d4914ebb3fb621a7ee1**, the §2.2 snapshot.

Result: **PASS — no scientific change**. The provenance wording is clearer and does not add execution authority. The §2.1 finding closures and final scientific-review disposition apply unchanged. DR11-01–03 remain CLOSED. Technical design remains CANDIDATE, human approval remains OPEN, and **Task E: NO**. Only this review file was appended; no canonical file was edited by this reviewer.
