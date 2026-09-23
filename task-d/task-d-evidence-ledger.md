# Task D — Evidence ledger

- Status: `DRAFT`; literature verification is evidence, not protocol approval.
- Verification dates: 2026-09-22–23 (Asia/Saigon).
- Intent/class: `EXECUTE` within the authorized Task D evidence deliverable; `FORMATION`.
- Scope of this section: bounded primary-source checks of MicroRCA, MicroRank, Eadro, DéjàVu, TORAI and BARO against the already selected C1 question. No renewed Task A survey, dataset download, package installation, baseline execution or outcome claim.
- C1 input constraint supplied to this verification: known-window root-service ranking on RE2-TT; matched telemetry, local evidence and candidate universe; observed parent–child service relations tested against matched local and structural controls; root/fault labels are evaluation-only.
- Authority: this workspace stores evidence. Durable project decisions remain in the canonical repository; this file adds no `DECIDED` or `USER_CONFIRMED` methodological choice.
- Evidence notation: `FACT` means directly checked source content, with its scope. `CANDIDATE` means interpretation or eligibility assessment. `OPEN — NOT VERIFIED` identifies an unresolved check, not a negative result.

## 1. Bounded verification and source provenance

Read inputs: canonical `AGENTS.md`, the complete governance skill and authority/gates reference, current DT18 mission and roles, Task A methods/gap sections, and `task-c/task-c-targeted-verification.md`. Task C's correction to MicroRank window interpretation takes precedence over the uncorrected shorthand in Task A for this evidence assessment. No prior program audit or reviewer list was read. This verifier is a source checker, not the independent methodology reviewer.

Only author papers, author repositories and publisher metadata support the statements below. Search results from third-party summaries were not adopted as evidence. Retrieval failures are recorded rather than replaced by inferred paper contents.

| ID | Primary source and exact locator | Verification scope |
|---|---|---|
| D-L01 | [Eadro author paper](https://arxiv.org/html/2302.05092), §IV-B–C, §V-G/Table IV | Full relevant method and graph-ablation passages read |
| D-L02 | [DéjàVu author PDF](https://netman.aiops.org/wp-content/uploads/2022/11/DejaVu-paper.pdf), §5.2.2/Table 3; §5.3.1/Fig. 9; §5.5/Fig. 15 | Graph ablation and edge-removal passages read; supervision and unit semantics checked |
| D-L03 | [TORAI v2](https://arxiv.org/html/2604.13522v2), §3.2–3.5; §4.7/Table 9; §4.9; §7 | Component ablation, blind-spot experiment and official artifact route read |
| D-L04 | [BARO v1](https://arxiv.org/html/2405.09330v1), §3.4/Algorithm 1, especially line 19 | Ranking formula read directly; known-window ranking separable from detector |
| D-L05 | [MicroRank official paper file](https://github.com/IntelligentDDS/MicroRank/blob/main/WWW2021_MicroRank.pdf), §5.4.3–5.4.4 | File exists; present PDF extraction failed. Exact paper-ablation facts below retain Task C's earlier verified provenance, not a new successful read |
| D-L06 | [MicroRCA publisher record](https://doi.org/10.1109/NOMS47738.2020.9110353) and [official repository](https://github.com/elastisys/MicroRCA) | Publisher abstract and official code read. Official linked [HAL PDF](https://hal.inria.fr/hal-02441640/document) returned an anti-bot page; exact experimental ablation not re-verified |

### 1.1 Artifact revision observations

These are source-location observations, **not execution pins**. GitHub commit pages resolved these abbreviated revisions during the check. A complete 40-character commit SHA, source byte hash, dependency lock and successful execution are `OPEN — NOT VERIFIED`. Branch names alone must not be used as immutable pins in Task E/F.

| Artifact | Observed commit-page resolution | Code actually read |
|---|---|---|
| MicroRCA | [de334b2](https://github.com/elastisys/MicroRCA/commit/de334b2) | `master/MicroRCA.py` |
| MicroRank | [efd85e8](https://github.com/IntelligentDDS/MicroRank/commit/efd85e8) | Abbreviated-revision raw files: `preprocess_data.py`, `anormaly_detector.py`, `pagerank.py`, `online_rca.py` |
| Eadro | [82ff9c9](https://github.com/BEbillionaireUSD/Eadro/commit/82ff9c9) | `main/codes/model.py` and repository README |
| DéjàVu | [d1f082b](https://github.com/NetManAIOps/DejaVu/commit/d1f082b) | `master/README.md`; paper is the source for ablation details |
| TORAI/RCAEval | [eeadab4](https://github.com/phamquiluan/RCAEval/commit/eeadab4), resolved from `fse26` | `fse26/RCAEval/e2e/torai.py`, `fse26/README.md` |
| BARO | [e35f4ec](https://github.com/phamquiluan/baro/commit/e35f4ec) | Abbreviated-revision `baro/root_cause_analysis.py`; repository README |

Shell GitHub API/raw retrieval and `git ls-remote` failed with connection resets. Web retrieval recovered readable official code and abbreviated commit pages, but not complete execution provenance. No repository was cloned and no retrieved program was executed. Web raw-text locators can omit blank lines; function names and statements below are authoritative locators, not guessed GitHub line numbers.

## 2. Closest prior controls and what they establish

### D-C01 — Eadro

**FACT — paper:** §V-G/Table IV compares the complete model with removal of each telemetry modality and with `w/o G`, which replaces graph attention by an FC layer. §IV-B constructs service relations from historical traces, fuses local modality representations and applies graph message passing. §IV-C learns detection and localization jointly with labeled outcomes. The graph ablation retains the modalities and service-localization task; it changes the representation learner. This is direct precedent for graph contribution, not just multimodal contribution. [D-L01](https://arxiv.org/html/2302.05092)

**CANDIDATE — comparison to C1:** Eadro is a close conceptual ablation, but its cited experiment does not establish identical frozen local evidence, matched parameter counts or a degree-preserving structural null. Keeping modalities is weaker than holding derived local representations fixed. Same service-task scope is supported; an explicit audit of identical per-case candidate lists is not reported by this passage. C1 cannot claim novelty merely from graph-versus-no-graph or metrics/logs/traces fusion.

**FACT — artifact:** [codes/model.py](https://raw.githubusercontent.com/BEbillionaireUSD/Eadro/main/codes/model.py), `GraphModel`, `MultiSourceEncoder`, `MainModel`, contains GATv2, modality encoders and cross-entropy losses using fault indices. **CANDIDATE — eligibility:** original supervised Eadro is ineligible under C1's evaluation-only root-label rule. A separate supervised label-budget study would change the current contract. Its code publication is not proof of successful RE2-TT reproduction.

### D-C02 — DéjàVu

**FACT — paper:** §5.2.2/Table 3 removes the feature aggregator and feeds unit-local features directly to the final classifier (`w/o AGG`). §5.3.1/Fig. 9 randomly removes FDG edges per failure, then trains and evaluates again, repeated ten times. Heavy edge removal can be worse than omitting aggregation. The task uses supervised historical faulty failure-unit labels; units combine a component and metric group. The cited experiments already investigate graph contribution and incomplete relations. [D-L02](https://netman.aiops.org/wp-content/uploads/2022/11/DejaVu-paper.pdf)

**CANDIDATE — comparison to C1:** removing aggregation changes model capacity; re-training after edge removal does not freeze local features. Random deletion changes edge count/degrees, so it does not isolate observed edge identity from degree structure. The same failure-unit problem is retained, but it differs from C1 service-level candidates. The paper does not establish C1's full matched-information contrast. Unseen-failure evaluation is also prior work (§5.5), not standalone novelty for C1.

**FACT — artifact:** [README](https://raw.githubusercontent.com/NetManAIOps/DejaVu/master/README.md), “Usage” and “Datasets”, identifies `graph.yml`/`graphs/*.yml`, `metrics.csv`, and labeled `faults.csv`, with training/validation/testing failures. **CANDIDATE — eligibility:** original DéjàVu is ineligible for the primary evaluation-only-label contract; failure-unit-to-service adaptation would also require an explicit mapping. It remains required closest-work discussion.

### D-C03 — TORAI

**FACT — paper:** §4.7/Table 9 compares full TORAI with SeverityScorer, CausalRanker and FineGrainer separately. SeverityScorer ranks by mean modality severity; full TORAI adds severity clustering and within-cluster causal ranking. §3 does not require an observed service call graph. §4.9 varies removed service traces. TORAI is unsupervised with respect to root labels, but needs a supplied anomaly boundary. [D-L03](https://arxiv.org/html/2604.13522v2)

**CANDIDATE — comparison to C1:** this is a particularly close local-score-versus-structural-reasoning precedent. The ablation changes multiple pipeline components, not just observed parent–child edges. It has no neural capacity-matching issue of the Eadro kind, but estimator/algorithm complexity still changes. Trace deletion changes available local telemetry as well as visibility; it does not hold C1's local evidence constant. No degree-preserving observed-relation null is established by the checked passages.

**FACT — artifact:** [fse26/torai.py](https://raw.githubusercontent.com/phamquiluan/RCAEval/fse26/RCAEval/e2e/torai.py) consumes modality time series, scores them and aggregates indicators to service names (including `fine2coarse_addup`); README lists TORAI and RCAEval datasets. **CANDIDATE — eligibility:** a conditional named unsupervised comparator, pending exact pin, adapter/preprocessing audit and execution. TORAI is **call-graph-free**, not graph-free: its causal stage uses learned structure. Its output comparison would contextualize C1, not identify the value of observed relations by itself.

### D-C04 — MicroRank

**FACT — carried verification, not fresh PDF read:** Task C TV-04 records direct extraction of the official 12-page PDF, SHA-256 `6d9cd4fcffdecd1dc186750a900ff7c4630b30b53d0173ada8bddb8488954608`. That check locates graph-weight variation at §5.4.3, trace-count variation at §5.4.4/Fig. 13, and component overhead at §5.5. It also corrects Task A: flushing a five-minute detection window does not establish a mandatory five-minute post-alert collection wait. Exact graph-weight variant names/values are `OPEN — NOT VERIFIED` in this new pass; do not invent a complete ablation inventory. [Official paper location](https://github.com/IntelligentDDS/MicroRank/blob/main/WWW2021_MicroRank.pdf)

**FACT — fresh code read:** [pagerank.py at efd85e8](https://raw.githubusercontent.com/IntelligentDDS/MicroRank/efd85e8/pagerank.py), `trace_pagerank`/`pageRank`, receives operation-call and trace-coverage relations and computes operation weights. [online_rca.py](https://raw.githubusercontent.com/IntelligentDDS/MicroRank/efd85e8/online_rca.py), `calculate_spectrum_without_delay_list`, converts normal/abnormal weights and counts into spectrum scores; the module also queries data at import and contains an online loop. [preprocess_data.py](https://raw.githubusercontent.com/IntelligentDDS/MicroRank/efd85e8/preprocess_data.py), `get_operation_slo`/`get_operation_duration_data`, expects Jaeger-style documents, hardcodes `frontend` server spans as roots, takes the first parent reference, subtracts child durations and scales durations by 1000. Its operation naming truncates a path to its final segment.

**CANDIDATE — comparison and eligibility:** paper and code give strong prior for trace-structure-weighted ranking. They do not establish C1's fixed multimodal local-evidence/candidate contrast. A MicroRank-derived offline comparator is conditionally feasible, but the original entry point is not ready for RE2-TT. Task E must isolate pure functions, replace retrieval/root assumptions with a declared adapter, verify units and complete-trace handling, preserve operation identity, and declare service aggregation plus absent-service ranks. This is an adapted comparator unless fidelity is proven. Never import the online entry point as a harmless library. Root/fault labels may only reach its evaluator; normal-window statistics do not require root labels.

### D-C05 — MicroRCA

**FACT — publisher/artifact:** the [publisher abstract](https://doi.org/10.1109/NOMS47738.2020.9110353) describes service/machine graph-based ranking from performance and resource evidence. The [official README](https://github.com/elastisys/MicroRCA) requires call response times plus container/host resource data. In [MicroRCA.py](https://raw.githubusercontent.com/elastisys/MicroRCA/master/MicroRCA.py), `anomaly_subgraph` constructs and reverses a weighted graph, computes personalization and calls PageRank. The main driver changes the anomaly threshold when the injected `target` is payment/shipping and the `fault_type` is not latency; it filters output to seven hardcoded service targets. These are source-code observations, not measured effects.

**CANDIDATE — comparison and eligibility:** the core suggests an unsupervised graph ranker, but the published driver is **ineligible unchanged** for C1: known target/fault type affects scoring before evaluation, and its fixed target list is not the shared candidate universe. A label-blind adapter and compatible service–host evidence are required. Substituting trace-only relations for deployment relations changes the method and must be named as an adaptation. This is not the cheapest necessary primary comparator for C1.

**OPEN — NOT VERIFIED:** exact paper graph-on/off or structural-control experiment and its section/table. The official PDF route was blocked; Task A's older description is context, not fresh proof that a particular ablation exists or is absent. No absence claim is made.

### D-C06 — BARO as graph-free comparator

**FACT — paper:** §3.4/Algorithm 1, line 19 scores each post-boundary sample by absolute median-centered deviation divided by normal IQR, then takes the maximum. This ranker is graph-free. [D-L04](https://arxiv.org/html/2405.09330v1)

**FACT — artifact discrepancy:** [root_cause_analysis.py at e35f4ec](https://raw.githubusercontent.com/phamquiluan/baro/e35f4ec/baro/root_cause_analysis.py), `robust_scorer` DataFrame path uses `RobustScaler` then `max(zscores)` without absolute value. It separately preprocesses normal/anomalous segments and intersects retained columns. Its `robust_scorer_dict` path instead uses `abs(max(post_data) - median) / IQR`, integer-index quantiles, denominator 1 for zero IQR, and skips metrics with fewer than four normal points or no post points. Neither formula generally equals the paper's maximum absolute deviation. The [README](https://github.com/phamquiluan/baro), “Data format”/“Basic usage example”, exposes RobustScorer separately and returns metric ranks.

**CANDIDATE — eligibility:** BARO's ranking stage is a suitable conditional named graph-free comparator with the same known boundary. Specify either a source-pinned artifact path or an explicitly labeled paper-formula implementation; do not silently fix code and call it an exact reproduction. C1 still requires a separate **matched local baseline** using exactly its shared evidence, because BARO is metric-only and its default filtering can change candidates. Metric-to-service aggregation, zero-IQR behavior, missing data and candidate completion belong in the adapter contract. BARO detector results are outside known-window C1; no AD performance follows from a ranker comparison.

## 3. Adjudication boundaries for the C1 literature claim

`CANDIDATE` interpretation from the six checks:

1. Graph/no-graph usefulness, graph weighting, incomplete topology, multimodal fusion and generalization all have relevant precedent. They are not new merely because C1 measures them on RE2-TT.
2. The defensible comparison remains narrower: conditional ranking value of **observed parent–child relations**, beyond exactly matched local evidence and controlled structural alternatives on the same cases and complete candidate universe.
3. The checked studies do not establish that exact conjunction of controls. This bounded observation does **not** prove no prior work exists, confer world-first novelty, or predict positive results.
4. External named comparators and C1's matched local/structural controls serve different purposes. Different feature processing, supervision or eligible cases in an external method cannot be used to attribute a gain specifically to observed relations.
5. Runnable eligibility is conditional documentary assessment only. No method has been installed, executed or shown to run on the selected release in this check.

## 4. Open execution-provenance items handed to Task E

| ID | State | Required evidence / owner | Consequence until resolved |
|---|---|---|---|
| D-O01 | `OPEN — NOT VERIFIED` | Full immutable source revisions, file hashes and dependency versions for selected baselines; Task E implementation owner | Short hashes above locate inspected source but are not a reproducibility lock |
| D-O02 | `OPEN — NOT VERIFIED` | Exporter/converter provenance or authoritative schema proving `duration` units for the **pinned RE2-TT archive**; Task E data/adapter validation | `floor(startTime/1000)=startTimeMillis` establishes only a start-field relation, not duration units or span completion. Do not infer RE2-TT duration semantics from MicroRank's different dataset |
| D-O03 | `OPEN — NOT VERIFIED` | Exact BARO formula/path selection and adapter tests; Task E owner | Keep paper-formula and artifact variants distinct; no silent substitution |
| D-O04 | `OPEN — NOT VERIFIED` | MicroRank root/span/reference/operation normalization and service ranking completion; Task E owner | Comparator remains adapted/conditional; no unmodified runnable claim |
| D-O05 | `OPEN — NOT VERIFIED` | Fresh accessible MicroRCA experimental paper and exact MicroRank weight-ablation definitions if needed for final report wording | Use the limited evidence above; no invented table or absence statement |

For D-O02, this pass inspected official RCAEval README/code routes but did not locate a release-bound export chain that proves the archive's duration unit. No raw trace was downloaded. Archive-start-window duration ratios may avoid asserting a physical unit when mathematically scale-invariant, but they do not prove completion-time availability; any cutoff claim needs its own validated semantics.

## 5. Verification handoff for this section

- Changed only this evidence-ledger file. No material decision state changed; all eligibility and gap implications remain `CANDIDATE` or `OPEN`.
- Assumed C1 scope as supplied; did not reopen candidate selection or extend the search universe.
- Verified primary passages and source functions, recorded failed retrievals, inspected the complete new file and checked for unresolved placeholders/conflict markers.
- Canonical governance audit completed with exit 0 and zero warnings on 2026-09-23. It reported two changed canonical files owned outside this subtask; that audit does not by itself validate this external-workspace literature ledger, which was separately read back in full.
- No baseline execution, dataset download or installation was performed. No performance numbers were imported as expected C1 outcomes.
- Formal-report material: closest graph controls, the limits of what they isolate, supervised-baseline exclusion under the current label rule, named-adapter provenance, and the BARO paper/artifact discrepancy.
- The parent Task D author may append the Pre-D adjudication and full-package validation below; this source checker has not reviewed or approved that adjudication.

## 6. Pre-D gate — main adjudication, 2026-09-23

**PRE-D = READY WITH D-OWNED CONDITIONS.** This judgment followed source reading and persistence of the independent review §§1–7, before that reviewer received F01–F12. No missing RQ, target, authority or corrupt input blocks specification. The new user execution contract (identical attachments on 22/23 September; SHA-256 `61bc0d003b97d1a74e5d96fad68945444d4571baf43e0729c898e09ef6bda96e`) authorizes D and explicitly stops before E. The master and C historical waiting notices do not override that current instruction.

| Finding | Main disposition | Source-based adjudication / smallest action |
|---|---|---|
| F01 relation utility could collapse to arbitrary A/B | SPECIFY_IN_D | C lock §1 already requires matched nuisance controls; not a C defect. TD §§1/4/5 defines common local scores and identity/observed/degree-component-preserving operators, with limits on smoothing identification |
| F02 data are not untouched | SPECIFY_IN_D | Master §2 already assigns exposure ledger to D. Narrow E1 §§2–3 check adds **historical output/metric/design exposure**, stronger than schema-only audit. Keep historical raw-revision equivalence OPEN; TD §3 bans untouched-test wording |
| F03 supervised comparators | RESOLVED_ALREADY | C lock §4 and EC-07 prohibit root/fault fitting. TD §6 operationalizes eligibility; no policy change or new human decision |
| F04 fixed schedule | SPECIFY_IN_D | B §12.10/C lock explicitly separate known-window oracle from detector. TD §10 must define label-blind rolling references/calibration and anti-shortcut checks; no midpoint-derived healthy reference |
| F05 all89 raw joins unknown | DEFER_TO_E / DEFER_TO_F | D §§4/13 defines checks; actual corpus validation before G. B sample-scope is already correct. No pre-D download/rerun |
| F06 A §M provenance | FIX_BEFORE_D (minimal report-facing notice) | Compared A §M, actual 22/08 letter, DT18, EC-09 and RCA-010/011. C already quarantines for its own use, so not fatal; direct readers of A still see misleading attribution. Add explicit notice immediately at §M; preserve table/history and DRAFT approval state |
| F07 closest-work verification | SPECIFY_IN_D | Bounded checks §§1–4 above; no Task A restart and no literature-wide absence/novelty claim |
| F08 dependent factorial cases | SPECIFY_IN_D | B §12.4 and C lock preserve unit. TD §§3/7 locks scenario split, repeat aggregation and conditional uncertainty limits |
| F09 answer-bearing paths | SPECIFY_IN_D | B §12.10 already bans; TD §2 defines evaluator/worker/packet separation and canaries. Enforcement still E/F, not asserted leak-free today |
| F10 detector contract | SPECIFY_IN_D | C5 mandatory capability retained; TD §10 injection-regime endpoints separate from C1 and H operational validation |
| F11 no fresh67M scan by reviewer | NO_ACTION | Not evidence of B error. B CLOSED and machine evidence adequate for D. No raw re-audit or claim of independent full scan |
| F12 duplicate governance | NO_ACTION beyond minimal layout | One canonical protocol/handoff; W owns source/exposure/review evidence; existing CURRENT/MAP only derived updates; no new decision register/roadmap |
| Additional status mismatch | FIX_BEFORE_D | B2B scope header still EXECUTING, while authoritative B §12.2–5/20 records completed one-case retrieval/verification. Correct header only, with dated closure link; no all89 claim |
| Additional historical outcomes | SPECIFY_IN_D | E1 exposure found by main and independently reconciled by reviewer; record limitation without reopening E1 method or importing its metrics/fusion choices |
| Additional duration semantics | SPECIFY_IN_D | B trace schema cannot establish duration units/completion. Core TD uses metric + trace occurrence counts, no duration/status semantics. Duration proof only required if a later selected adapter consumes it |

No source-based reason to change Task A work COMPLETE/document DRAFT distinction, C1 choice, Task B CLOSED, original advisor letter, C lock or RESEARCH-DECISIONS. C old “not started” lines remain explicitly historical; CURRENT owns live state. Pre-D risk acknowledgment is sufficient to start D, but does not certify the final protocol until its independent objections are adjudicated.

### Impact map actually authorized

Source first: P `task-a-ban-do-bang-chung-doc-lap.md` notice; W `dataset-audit/TASK-B2B-RE2TT-MULTIMODAL-SCOPE.md` status correction. New authoritative protocol P `task-d-method-and-experiment-specification.md`, then P `task-d-handoff.md`, `ARTIFACT-MAP.md`, `CURRENT-STATE.md`. Execution evidence W `task-d/task-d-{evidence-ledger,exposure-ledger,independent-review}.md`; small deterministic validation script/results in the same folder. This follows the exact output set and conditional minimal remediation authorized in user §§6/31/36. No decision promotion, application/API/schema changes, commits, pushes or external publication. P README preexisting edit is preserved (working-file SHA-256 `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`).

Input HEADs: P `e0bc0d9daad732948faaeb7b54fcc4cb02aa0142`, W `ec418ac4f7fd87d4e0ae159aa9559b8549bb909a`; no relevant HEAD delta. Input document hashes are in independent review §1 and exposure ledger §5. No old snapshot or raw hashes were rewritten to match new notices.

### Disposition of literature execution OPENs after TD drafting

TD §6.1 selects **paper-equation BARO component adaptation**; this closes D-O03's design choice as CANDIDATE, while source pin/fixture execution remains E. MicroRank is deferred, so D-O04 is not an E-core blocker. Core TD avoids duration; D-O02 remains OPEN only for future duration-consuming adapters. Exact inaccessible paper ablations D-O05 limit literature wording, not implementation of the specified L/O/R experiment. No unsupported claim is needed to close D.

## 7. Final independent review — main adjudication

The same independent methodology reviewer attacked the full first draft through20 lenses (review §11, draft hash `ca7004757cc463304b32b4a4f42c1989a9f1e4947b40c82ed46beca40b385038`). **0 CRITICAL, 5 MAJOR, 6 MINOR**. Main accepted the evidenced defects below and corrected the canonical protocol; no poll/vote was used. The reviewer then re-read the corrections, preserving the initial objections, and closed all11 in review §13 against final TD-v1.0 hash **`9822a92081fb5d958fde35b68d274906bd36ee66288017645a7ec6840a2c1c4d`**. Review receipt hash at closure: `e3e06ba54cb105943bb8f28f406e8f70e18b9bf077453de36a182c598eaedba0`.

| Finding | Main decision and exact correction | Why sufficient within D |
|---|---|---|
| DREV-01 MAJOR: caseID-derived seeds contradicted provenance canary; regenerated finite controls not exactly permutation-equivariant | ACCEPTED/RESOLVED, TD§2: pinned execution handles/seed draws stay fixed when mutable labels/paths change; service permutation couples realized adjacencies | Tests actual label-free core, not an impossible comparison of independent random draws; seed provenance remains explicit |
| DREV-02 MAJOR: C5 had event triggers but undefined per-bin predictions | ACCEPTED/RESOLVED, TD§10: raw strict-threshold indicator feeds bin metrics; valid-channel rule, unavailable bins, zero-denominator/coverage convention separate from persistence/refractory events | One executable endpoint definition, no retrospective choice of high-recall alert state |
| DREV-03 MAJOR: capped score plus q99=1 could make detector mathematically unable to trigger | ACCEPTED/RESOLVED, TD§10: C5 uses uncapped abs/scale q90, distinct from capped C1 evidence; record threshold ties/range | Removes structural upper-bound impossibility; does not claim actual recall or tune with labels |
| DREV-04 MAJOR: pending diagnosis cannot recover missing past; crop/restart omitted persistence state | ACCEPTED/RESOLVED, TD§10/13.1: exact streak/refractory transitions, immediate insufficient-history failure, first post-injection trigger accounting, contiguous diagnostic windows; score360s vs decision380s plus identical refractory state | Deterministic trigger/failure timing; no future waiting or later successful trigger substituted for first failure |
| DREV-05 MAJOR: qualitative starvation/ceiling/failure exceptions could rescue negative results | ACCEPTED/RESOLVED, TD§7: quantitative flat-input/shared-failure conventions and explicit arm/chain failure rule; ceiling not escape; same rankings on changed graphs are not themselves degeneracy | Verdict overrides fixed before outcomes; finite-set negative result remains possible and interpretable |
| DREV-06 MINOR: conflicting metric duplicates channel or case? | RESOLVED, TD§4.1: invalidate affected channel both windows, mask0; trace key conflict is shared-case failure | Implementer has one rule and fixture |
| DREV-07 MINOR: R seed failures/time budget | RESOLVED, TD§5.1: zero failed chain, denominator32; budget aggregate32, remaining chains0 after timeout; any failed chain gates relation interpretation | No successful-only control mean or hidden computational advantage |
| DREV-08 MINOR: time-bearing facade versus core allowlist | RESOLVED, TD§12: trusted slicing facade separate from explicit numeric score_core input | No epochs/labels/handle in unprivileged scorer |
| DREV-09 MINOR: zero observed count and unresolved-parent language | RESOLVED, TD§4.1/5: zero observed spans≠zero traffic; unresolved within reference may be boundary-censored, no outside-window lookup | Exact observable meaning; no fabricated coverage decomposition |
| DREV-10 MINOR: support adapter operation key/sampling | RESOLVED, TD§4.2/12: optional literal operationName; sample via sourcehash+rowordinal, trusted deterministic redaction | Packet support implementable without label/content selection |
| DREV-11 MINOR: deletion sensitivity ambiguity | RESOLVED, TD§7: sign preservation>0 is fixed veto; crossingδ reported but not new veto | Avoid two competing support rules |

Remaining NOT VERIFIED are execution facts: reference-window mobility, loader/all-used-log compatibility, baseline immutable execution source/env/fidelity, runtime, C5 outputs, explanation/target validation, true population interval coverage and exact historical raw-version linkage. D assigns owners and bounded claims; none is falsely marked a successful experiment. No open critical/major **specification** objection remains. Human acceptance and E execution authority remain OPEN for Minh.

## 8. Acceptance coverage and validation scope

User acceptance A–X maps to TD sections: **A–D** §§1/4/5 (estimand/matching/control limits); **E–G** §§2/4 (candidates/label/input isolation); **H–I** §§5/10 (semantics/modes); **J–K** §§3/7 (exposure/units); **L–M** §7 (metrics/effect/verdicts); **N** §6 (eligibility/fidelity); **O–Q** §§9/10 (C3–C5); **R** §11 (immutable explanation packet); **S** §§7/8 (failures); **T–U** §13 (manifest/pilot/freeze); **V** this ledger§§1–4 (bounded primary verification); **W** independent review§§11–13 and adjudication above; **X** TD§13.1 + handoff (E contracts/fixtures).

`validate-task-d.py` performs only synthetic mathematical and document/preservation checks; results in `task-d-validation.json`. It does not implement/execute the real RCA pipeline or download raw files. Governance audit output is `task-d-governance-validation.txt`. Complete tracked diffs and untracked deliverables are inspected; machine receipts identify their exact hashes. An initial validator run found its own not-yet-written receipt link; the validator now checks that self-output after serialization. This was a validation-order issue, not a scientific result or silently skipped external link.

Final validation: **76 checks passed**. The repository governance audit returned **PASS with one scope warning**: it counts six changed P files, comprising the five authorized Task-D files and the preserved preexisting README edit. The approved impact map above and user §§6/31/36 cover the Task-D changes; the warning is not an unresolved request for approval or permission to change README. No human decision was promoted.

Formal-report conclusions remain prospective: contribution/control rationale, evidence semantics, exposure and limits may be written now; measured quality, runtime, detection, LLM and FlashTicket results await their actual tasks. **TASK D WORK COMPLETE / DOCUMENT REVIEW_READY; STOP BEFORE E.**
