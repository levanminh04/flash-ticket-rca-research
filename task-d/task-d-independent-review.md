# Task D — Independent methodology review

Date: 2026-09-22. Reviewer: independent methodology reviewer, source-first pass. Owner of any subsequent research decision: Lê Văn Minh.

**Review status: source-first opinion persisted before receiving the main agent's candidate findings, attachment contents, adjudication, or draft Task D protocol.** This file is a reviewer artifact, not a second roadmap and not human approval. All recommendations and technical choices below are `CANDIDATE`; missing execution evidence is `OPEN`. No A/B/C gate is reopened by this review.

## 1. Scope, provenance, and evidence

Intent: `EXECUTE` only for this explicitly authorized review artifact; `REVIEW` for project sources. Class: `FORMATION`. The delegated scope permits Pre-D audit and D specification, forbids E execution, download, installation, baseline runs, and application changes. Only this file is owned by this reviewer.

Bindings: `P = D:/Project/flash-ticket-platform`; `W = D:/Project/flash-ticket-rca-research`. Verified source HEADs before writing: P `e0bc0d9daad732948faaeb7b54fcc4cb02aa0142`; W `ec418ac4f7fd87d4e0ae159aa9559b8549bb909a`. P already had a modified README; it was not touched. W had no tracked working-tree changes at review start. HEAD identifies provenance, not backup or an approval.

Sources actually used:

| Source | Sections / authority used |
|---|---|
| P/AGENTS.md | Complete constitution; DT18 priority, independent RCA ownership, human approval and historical provenance |
| P/.agents/skills/govern-capstone-work/SKILL.md; references/project-authority-and-gates.md | Complete workflow and authority reference |
| P/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md | Complete DT18 title and mission |
| P/docs/project/roles.md | Complete current roles; Minh owns RCA |
| P/docs/quy-trinh-lam-viec.md | Complete workflow; opening RCA-specific rhythm and system/RCA separation are directly applicable |
| P/docs/research-rca/SESSION-BOOTSTRAP.md; CURRENT-STATE.md | Complete recovery pack and current status; authority is subordinate to the current authorized task |
| P/docs/research-rca/task-c-research-decision-lock.md | Complete TC-P2-v1; primary C1, roles, leakage, falsification, §6 handoff |
| P/docs/research-rca/MASTER-RESEARCH-PROGRAM.md | §§1–3, Task A–K contracts, §§5–9; especially D exit and E entry |
| P/docs/research-rca/task-b-dataset-capability-summary.md | Complete transfer summary; sample/full-subset and storage distinctions |
| W/dataset-audit/TASK-B-RCAEval-audit.md | Authoritative CLOSED §12.1–12.20; pre-close history not used to override closure |
| P/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md | Task distinctions I§§1–10 / II§B; comparator descriptions II§C.2–C.12; graph placement §D–F; missingness §H; granularity §I; metrics §J; dataset §K; closest work/gaps §L; historical interpretation §M; prohibited claims §N |

Input SHA-256: C lock `E9ADA986553EA150958D6355A57CCD140A55C80A62B84F5B4665E5D3DC258C98`; B summary `18A71EA34E0D3F5D5E11BBDEAE3439536BD80D6AAA7F22172B4AB0EE0EF3A45B`; master `E40ABFDF4B61E81074F9C522897481CE543575D25658E7B1117DC279014E331A`; authoritative B report `BE40D10E359DC7DE670D537C9C7000819161ED2739DC0A6280F69219A716C38A`. These are document checks only, not a raw-data rehash.

No user attachment or W/program-review report was read. No prior review was used to construct this opinion. Task A statements are read as bounded prior-work synthesis; this review does not freshly verify current external software or paper versions.

## 2. Independent verdict

**CANDIDATE assessment: D can start. No hard external or scientific blocker to writing D is established by the selected sources.** C1 has a locked question, service-root target and permitted first dataset. B CLOSED supplies adequate capability evidence for protocol formation. Current task authorization removes the previously recorded wait-for-D boundary; the old waiting text is a state snapshot, not a new scientific obstacle.

**D must not be called approved or execution-ready merely because a complete-looking specification exists.** Master Task D requires independent critique adjudication and Minh's acceptance of the baseline protocol before E. Missing exact metrics, windows, graph mechanism, controls, split, and implementation choices are normal D work, not reasons to repeat C or require a fresh audit before drafting.

The scientifically central risk is identifiability: an observed-graph method can beat a simple local scorer because it adds smoothing, degree preference, different features, candidate filtering, or a larger search budget. Such a result alone does not answer the locked C1. A modest method with explicit controls and bounded claims can answer C1; algorithmic novelty or a positive result is not required.

## 3. Disposition by stage

| ID | Independent finding / source | Correct place and minimum action |
|---|---|---|
| IR-01 | `FACT`: C Phase 2 §§1/4/6 intentionally leave quantitative protocol choices open. | **Inside D**, not before D: choose implementable definitions and label new selections `CANDIDATE` pending Minh. Preserve RCA-001–017. |
| IR-02 | `FACT`: B §12.2 verifies the trace audit but did not retain the complete 90-case corpus; B §12.5 verifies joins only on inspected samples. | **D defines**, **E/F executes**: explicit input requirements, schema/join acceptance checks and fail behavior. Do not demand a new 90-case download or full multimodal audit to write D. |
| IR-03 | `FACT`: C §1 requires controls beyond graph ON/OFF; A §D–F shows graph can act at different pipeline stages. | **Inside D**: common local evidence and candidate universe; define the primary contrast and structure controls with precisely stated preserved/changed properties. Freeze graph role and direction rather than leave them to implementation convenience. |
| IR-04 | `FACT`: C §4 and master §2 prohibit root/fault fitting/tuning, test contamination and pseudoreplication. | **Inside D before any E pilot**: exact development/calibration/final-evaluation assignment or deterministic rule; exposure ledger; evaluator-only grouping metadata; planned paired statistic at incident/scenario level. **E/F** records actual exposure. |
| IR-05 | `FACT`: B §12.10 grants injection time only as known-window RCA boundary; no independent anomaly-onset labels. | **Inside D**: two distinct input and evaluation modes, detector initialization/calibration without injection oracle, and explicitly bounded injection-regime endpoints. **F/G** checks and measures them. |
| IR-06 | `FACT`: B §12.9 has no operation, affected-node, resource or propagation GT. | **Inside D**: service-root output only for RE2-TT quantitative localization; C3 operation evidence remains literal intermediate evidence. Do not seek absent operation GT as a prerequisite to D. |
| IR-07 | `FACT`: parent resolution differs markedly across cases; one case lacks logs; complete-case target coverage does not imply fixed-window target coverage. | **Inside D**: missingness, isolated/unseen node, empty feature, missing-target, invalid-file and timeout rules with an explicit denominator. **E/F** verifies; **G** reports coverage. |
| IR-08 | `FACT`: A §C.2/C.3 identifies close graph-ranking precedents; §C.4/C.8 provides non-supervised comparators with differing inputs/semantics; §C.7/C.9 require supervised labels. | **D** records comparator rationale and compatibility; targeted official-source/code inspection is appropriate for any selected implementation. **E** pins and reproduces/adapts. Do not require incompatible supervised training or all surveyed methods. |
| IR-09 | `FACT`: C §§2/3 keeps C5 and LLM mandatory intended capabilities, C3/C4 present but exact ablations conditional, C2 optional. | **Inside D**: concrete disposition for every component, downstream contracts and separate evaluation endpoints. Detailed LLM study belongs to I; FlashTicket execution to H. |
| IR-10 | `FACT`: master §2 allows controlled D revision after E exposes incompatibility; §3 requires run manifests and failure preservation. | **D** names revision/freeze/review triggers. **E/F/G** creates actual runtime evidence. Do not claim package locks, results or feasibility that do not yet exist. |

No source correction is independently required **before drafting D**. A material mismatch discovered while selecting an implementation would block the affected choice, not automatically all D work. Canonical handoff/state updates should reflect completed D drafting and its approval boundary without modifying historical A/B/C bodies.

## 4. Specific methodological issues D must make explicit

### 4.1 What is being estimated

`CANDIDATE`: write the primary estimand as a paired difference in a predeclared service-ranking metric for a specified incident population and an explicit graph-versus-control comparison. Separate an equal-input mechanistic contrast from a practical comparator with different feature construction. The latter can test pipeline competitiveness but cannot by itself identify relation utility.

Define the useful effect criterion before final-test outcomes. Failure to reject a zero-effect null is not equivalence; a positive point estimate with broad uncertainty is not a supported practical gain. Do not make a many-metric win or a best-seed result the success rule. Account for the number and hierarchy of confirmatory contrasts. See C §§1/4/5; A §J; master Task G.

### 4.2 Counterfactual controls and orientation

`CANDIDATE`: a control table should say, for each contrast, what is equal: telemetry cutoff, service candidates, local feature scores, propagation amount, capacity, number of parameters, graph density/degrees, weights and seeds. Also state what is not equal. No generic shuffled graph preserves every nuisance.

Direction reversal is a useful sensitivity question if justified, but it is not interchangeable with degree preservation: reversing a directed graph exchanges in/out degrees and changes a ranker's interpretation. A degree-preserving randomization needs a specified directed/weighted construction, realizability handling, seed budget and diagnostics. If a particular control cannot be constructed, preserve its failure and restrict the claim; do not quietly choose an easier null after seeing ranking results.

Unweighted observed relations can avoid making raw traffic count part of the treatment, but local features, observed-node visibility and edge presence can still depend on traffic volume. Conversely, weighted relations require a direct volume-confounding discussion. These are D design questions, not reasons to install a graph framework early. Sources: C §1; B §§12.6/12.7/12.11; A §§D/E/L.

### 4.3 Reference construction, normalization and look-ahead

`CANDIDATE`: specify the exact reference and diagnostic window, endpoint inclusivity, units, alignment, clock rule and graph time support. State whether graph is constructed from reference data, diagnostic data or both, and what the estimand then means. A graph aggregated over the entire audited population is not a per-incident observed graph; the 27 services and 55 relations are audit unions, not an allowed fixed vocabulary/topology.

Normalizers, category vocabularies, log templates, metric ownership maps and caches can leak future/test information even with root labels removed. Each fitted object needs scope and cutoff provenance. Candidate generation must not use the five injected labels. A known-window experiment may use telemetry within its declared available window; that does not license later telemetry in the detector mode. Sources: B summary; B §§12.7/12.9/12.10; C §4; master §§2/3.

Specify zero/near-zero reference variability, sparse operations, unavailable channels and mapping failures. A literal service/operation pair is reproducible identity, not a protocol-semantic operation. A max-over-channels score may favor a service with more metric/operation channels; merely keeping the same function in both arms does not establish fairness against a comparator with a different channel set. This deserves an explicit aggregation/coverage diagnostic rather than silently dropping low-evidence services.

### 4.4 Exposure and small-sample inference

`CANDIDATE`: use separate ledger categories for schema inspection, telemetry/feature inspection, outcome-score inspection and design/tuning use. The audit's knowledge of labels and schemas does not prove that every future model score has been inspected. Equally, a case used to select parameters cannot become untouched by renaming it. Preserve provenance rather than demand a new dataset or blanket-exclude all audited cases. Source: master §2.

There are 90 incidents but only 30 service×fault scenarios with repeated realizations, and all come from one benchmark system/revision. D should explicitly state the intended generalization population, split grouping and paired resampling/testing unit. Seeds, windows and spans are not independent incidents. Holding repeats apart may test within-scenario repeat performance; it is not evidence for unseen scenario/system generalization. A full-corpus descriptive secondary table can be useful if clearly separate from held-out claims and cannot be used to rescue primary H1.

The scorer and LLM should not receive grouping/fault metadata; an isolated evaluator can use those fields for the declared split/stratification. Do not interpret “evaluation only” as permission for supervised parameter search on a development subset's root labels. Source: C §4; B §§12.4/12.10.

### 4.5 Missingness, failure and tied ranks

`CANDIDATE`: define the ordered output, tie rule and metrics on absent root, empty ranking, all-equal scores, incomplete candidates and execution failure. Preserve all planned incidents in the primary denominator. A separate successful-run analysis may diagnose implementation behavior but cannot replace it.

If tied scores are broken lexically by service name, report the convention and avoid making structural absence look like evidence. Prefer a metric policy whose tie behavior is explicit and independently fixture-tested in E; there is no existing C decision fixing the choice. Report raw failure causes as well as the chosen score contribution. A timeout and a correct but tied output are scientifically different events.

Observed low parent resolution is a natural diagnostic stratum, not a randomized treatment. Any association between graph coverage and ranking quality can reflect fault/scenario/traffic differences. Synthetic edge removal, if later selected, tests that perturbation mechanism only, not every real missingness process. Sources: B §§12.11/12.12; A §H; C §§4/5.

### 4.6 Comparator fidelity without scope inflation

`CANDIDATE`: the minimal convincing baseline package includes a common-input local comparator and suitable structural controls; an external literature comparator supplies context. The exact set and priorities belong to D. Do not relabel a generic robust score as reproduced BARO or a service-only PPR variant as exact MicroRCA when mandatory detector/host/correlation steps are absent. Keep separate names for exact reproduction, adaptation, and a newly specified simple comparator.

MicroRank is close in graph-weighted ranking but has operation-level machinery and paper/code detector discrepancies; MicroRCA has host/deployment information not supplied by the RE2-TT graph. Eadro/DéjàVu supervision conflicts with the locked evaluation-only root-label policy unless a new user decision changes that policy. TORAI's lack of a service-call graph does not make it “graph free” in every sense because it learns a causal structure internally. These are compatibility disclosures, not automatic exclusions or a mandate to reproduce every method. Sources: A §§C.2–C.9, D–F; B §12.8; C §4.

### 4.7 End-to-end and explanation claims

`CANDIDATE`: C5 should have a specified automatic trigger and a path from trigger to rank, with no hidden injection-time calibration. A detector miss must remain visible when measuring the composed pipeline. Known-window rank quality and detector-triggered rank quality are separate outputs. Pre-injection intervals in injected cases are limited normal controls, not a production false-alarm study. Source: C §§2/4/5; B §12.12.

The evidence packet should carry versioned service ranks, observed evidence, availability/coverage, score meaning and limitations, while keeping root/fault labels, label-bearing paths, oracle boundaries and benchmark metadata out of model-facing prompts. Explanation faithfulness to a wrong packet is separate from root-ranking correctness. Recommendations should remain diagnostic checks, not autonomous repair. Detailed provider/rubric execution is I's job; D must leave a usable contract. Sources: C §2; master Tasks F/I; DT18-NV2/NV3.

## 5. Remediation that would be excessive or harmful

1. **Reopen Task A because no strong novelty gap was established.** C already accepts empirical/system/reproducibility contribution. Preserve A's historical uncertainty and C's human choice; do a narrow comparator check only where needed.
2. **Rewrite A's old OPEN language as if D's decisions had existed during the blind survey.** Add forward authority pointers only if necessary; never edit history to manufacture anticipation or consensus.
3. **Rerun B or download all modalities before drafting D.** B CLOSED is sufficient to design. Loader checks on actual experiment inputs belong to E/F. Its source §12 wins over pre-close text.
4. **Treat all audited cases as irreparably contaminated or declare all final cases untouched.** Both exceed current evidence. Use an exposure ledger and bounded claims.
5. **Require a large learned model, GNN, resource graph or operation GT to make the thesis strong.** These requirements do not follow from C1/DT18 and some conflict with B capabilities or label policy.
6. **Block D–G on FlashTicket, faculty template, or explanation-provider readiness.** The roadmap separates those dependencies. H and final program completion remain mandatory; they are not prerequisites to protocol specification.
7. **Expand C3/C4 into extra primary RQs or remove them for convenience.** Preserve their design role with a reasoned disposition, as locked.
8. **Select an environment/GPU/framework before comparator requirements are known.** That is E feasibility work and is not authorized now.
9. **Interpret a reviewer severity label as a new human decision.** Only the owner's accepted choice changes the locked scope. This review provides critique, not approval.

## 6. Conditions for later critical review of the D draft

I would challenge a D draft as not ready for owner acceptance if any of the following remains ambiguous:

- the primary effect/contrast, what it can identify, or the final success/negative/inconclusive/invalid rule;
- exact field availability, windows, reference fits, graph construction/direction, feature aggregation or candidate universe;
- structural-control properties, failure behavior, and the mismatch between a treatment and a claimed nuisance control;
- root/fault label access, detector oracle isolation, and exposure/split ownership;
- unit/dependence, tie/miss/failure denominator, primary metric and paired uncertainty/multiplicity policy;
- baseline selection/fidelity/adaptation requirements and a bounded response to E incompatibility;
- C3/C4 disposition, C5 contract and LLM packet/explanation boundary;
- explicit human acceptance and separate E authorization.

The present verdict is therefore **proceed with D specification, review its actual choices, then stop for the required owner acceptance before E**. It is not permission to run E, nor evidence that any selected baseline will work or graph will improve ranking.

## 7. Handoff and preservation

Decisions added/changed: none. A/B/C choices and approvals remain as recorded. Assumptions: current delegated task accurately conveys Minh's permission for Pre-D and D specification only; the pinned document revisions are the source set for this pass. Files changed: only W/task-d/task-d-independent-review.md. Checks: source existence, read-only repository state/HEAD and document hashes; no experiment, raw audit, package install or external write.

Formal-report material eventually needed: task/GT distinctions, observed-relation semantics, estimand/controls, incident/scenario dependence, exposure limits, faithful interpretation of negative/inconclusive results, and separate detector/ranking/explanation evidence. Numerical claims must later point to real E–I manifests and runs.

This source-first section must remain intact. Subsequent challenge/adjudication should be appended with a clearly marked phase and draft version/hash rather than silently replacing the initial opinion.

## 8. Phase 2 — Narrow historical exposure check, after persistence

Trigger: after §1–7 had been written and frozen, the main agent requested an evidence-on-demand check of P/docs/research-rca/E1-kiem-dinh-rcaeval-va-kha-thi-myrca.md §§2–3. This is a new source query about prior exposure, not adoption of an external review finding or reopening E1's method. Only the relevant exposure content was used; the attachment and program-review findings remain unread.

**FACT — material historical outcomes were inspected.** E1 §2.1 reports 11 CSV files / 990 rows, the same 90 case IDs per system across methods, labels and top-five output consistency. §2.2 reports metric selection, 30-cluster bootstrap and paired comparisons; §2.3 explicitly says they were post-hoc and insufficient for held-out confirmatory claims. §3.1 publishes Train Ticket method outcomes; §3.3 compares paired Train Ticket outcomes and motivates fusion from disagreement on 38/90 cases; §3.4 publishes performance by injected service. The historical inspection therefore was not schema-only.

**OPEN — exact raw-revision and incident mapping.** E1 §2.3 records missing dataset hashes, run manifests and patches. These deficiencies do not erase the known outcome exposure, but they prevent this reviewer from declaring that all historical runs used exactly the pinned Task-B raw bytes. A narrow evaluator-side case-ID mapping between the historical CSV inventory and current RE2-TT inventory can establish incident overlap if needed; it requires no baseline run or raw corpus re-download. It must not expose labels/paths to the scorer.

**CANDIDATE correction required inside D before E:** do not describe a newly split RE2-TT evaluation set as historically outcome-unseen or untouched. Record the E1 outcome/stratum/hypothesis exposure explicitly, including the known coverage and the unverified raw-revision link. Distinguish a set held out from *new protocol-specific tuning* from a genuinely unexposed confirmatory test. New paired measurements can still answer a bounded empirical question under a frozen protocol; their historical selection dependence must be disclosed. A split or hash reassignment cannot undo the prior exposure.

This sharpens §4.4; it does not require reopening A/B/C, rewriting E1, abandoning C1, or procuring a new dataset before D. An owner decision would be needed only if the proposed remedy changes the locked RQ/dataset scope. Keep E1's post-hoc results as historical evidence; do not transplant its AC@1 choice, numeric thresholds or fusion suggestion into D as a preapproved design.

Validation after the initial write: P governance audit executed with exit code 0; W `git diff --check` returned no tracked diff errors. The new review file was separately inspected as an untracked addition. These are document checks, not experimental validation.

## 9. Phase 3 — Challenge of candidate findings F01–F12

Date: 2026-09-23 after authorized continuation. Input is the main agent's twelve-item candidate list, received only after the source-first opinion was persisted. The list is a set of claims to assess, not evidence by itself. No attachment or W/program-review report has been opened by this reviewer.

For the one newly relevant attribution question, inspected the historical advisor letter P/docs/evidence/advisor-direction/2026-08-22-dinh-huong-de-tai.md §1 and the narrow correction row in C Phase 1's adjudication table. The letter asks for surveying suitable metrics and AI explanation; it does not name PageRank/GNN or the listed ranking/detection metrics, and it does not specifically require an LLM. Current C lock independently requires the intended LLM capability. This verifies the scope of F06 without reopening historical design.

| Finding | Independent challenge / severity | Owner, minimum fix, timing |
|---|---|---|
| F01 — C1 risks arbitrary A/B comparison | **Substantive, high for D exit.** Accept the risk, but do not declare existing C1 invalid. C explicitly assigns fair controls to D. Same telemetry alone is insufficient; an external comparator with another scorer is context, not an isolated relation test. | D author defines matched primary contrasts and limitations; reviewer checks. No A/B/C reopening. |
| F02 — 90 cases not untouched after audit | **Partly overbroad as originally framed.** Schema/topology inspection alone does not demonstrate outcome-guided tuning; exposure categories matter. Phase 2's E1 check establishes the stronger material outcome/stratum/hypothesis exposure. | D exposure ledger and qualified final-set claim before E. Do not blanket-exclude audited cases, erase exposure, or call a new split untouched. Exact historical raw identity remains bounded by evidence. |
| F03 — Eadro/DéjàVu ineligible | **Correct for their original root-supervised training under current policy.** Overbroad if interpreted as forbidden literature or proof no conceivable separately audited pretrained variant could ever be compared. Such a new variant is not currently validated and need not be added. | D compatibility table distinguishes surveyed prior from runnable current comparator. Do not train with current root labels or weaken C/B policy implicitly. |
| F04 — fixed-schedule shortcut | **High for detector validity; not a known-window RCA defect.** Reference/query windows may intentionally use the external incident boundary in C1. Detector initialization, thresholds and trigger must not exploit fixed offset/case duration or metadata. | D defines separate modes and label-free detector input; E/F test isolation, including shifts/crops where appropriate. No need to forbid incident boundary in C1. |
| F05 — all 89 log joins not verified | **Correct scope limitation, not a new audit failure.** Full trace evidence and sampled log/metric evidence are intentionally different. | D specifies loader acceptance/availability/failure contract; E/F verifies actual used files. No full multimodal audit prerequisite to drafting D. |
| F06 — A §M historical attribution | **Confirmed provenance correction, bounded severity.** It is already recognized in C Phase 1; it does not negate the current user-confirmed C5/LLM requirements. | D uses DT18/current C sources and notes the historical correction where needed. Preserve A's historical body; no mass rewrite, renewed advisor approval requirement, or removal of LLM. |
| F07 — bounded closest-work review | **Appropriate D obligation.** A global novelty/absence claim would be unjustified; a new exhaustive survey or an assumption that the closest work must be exactly reproduced would be excessive. | D opens selected primary/artifact evidence for actual comparator compatibility. Literature contribution remains empirical, not method novelty. |
| F08 — 5×6×3 dependence | **High for inference.** Scenario grouping handles within-cell repeats but not every root/fault/system dependence. Seed/window/span replication never expands incident n. | D states conditional estimand, paired grouping and uncertainty limits; G implements. Avoid describing 30 designed cells as 30 random independent systems. |
| F09 — path/case leakage | **High implementation boundary, already a locked rule.** Literal service names remain legitimate telemetry identities; forbidding every token resembling a label would destroy the task. The forbidden shortcut is answer-bearing metadata/path or memorized injected subset. | D separate evaluator provenance from scorer/LLM, specify sanitized identifiers and label-free telemetry loader; E/F verify. |
| F10 — C5 bounded regime | **Correct, high claim boundary.** Regime detection is not onset truth, node anomaly F1 or production false-alarm reliability. C5 still needs a functioning automatic trigger and composed-pipeline evaluation. | D/F/G public regime endpoint, H controlled target evidence; keep known-window ranking separate. |
| F11 — reviewer did not rerun 67M spans | **Not a defect.** Existing full trace audit remains evidence unless a concrete integrity discrepancy appears. | No remediation beyond accurate evidence provenance; do not rerun B or imply fresh raw verification. |
| F12 — duplicate governance | **Correct efficiency concern.** A reviewer record and per-task handoff are evidence, not new authority. | Put method in D, state in CURRENT, roadmap in master, review details in W. Do not require redundant approval ledgers or repeat all source contracts. |

No listed issue independently blocks the start of D. F01/F04/F08/F09/F10 and the E1-strengthened F02 can block acceptance of an inadequately specified protocol. F05 execution evidence belongs later. F06 is a scoped provenance disclosure. F11 calls for no extra work.

## 10. Phase 3 — Critical challenge of proposed estimand and controls

Reviewed proposal: common local metric/trace deviation scores `l`; local arm L; observed arm O using an undirected binary reference-window adjacency; row-normalized `P`; restart smoothing `q = 0.5 l + 0.5 Pq`; self-loop for isolates. R applies the same smoothing to 32 seeded fixed-budget simple-graph two-edge-switch chains preserving each labelled node's degree and exact component membership. Candidate set uses permitted per-case reference/query trace identities. Primary paired MRR contrasts are O−L and O−mean(R), jointly necessary; practical criterion 0.05 MRR; scenario-block uncertainty and leave-root/fault sensitivity; 10 development and 20 evaluation scenario cells, all three repeats together. C3 scoring deferred but operation evidence retained; C4 graph at ranking; C5/LLM contracts retained.

All conclusions here are `CANDIDATE`. No formula, split, threshold, implementation or execution is human-approved by this review.

### 10.1 Verdict on informativeness

**This is a scientifically useful modest C1 mechanism if its claim is explicitly conditional.** It tests whether the particular arrangement of observed reference-window undirected service relations improves service ranking under fixed restart smoothing and a fixed evidence construction, compared with the specified local and degree/component-preserving perturbation controls. It does not estimate the utility of all trace graph information, directed dependency reasoning, arbitrary graph models or causal relations.

Avoid an overcorrection that insists on GNNs, operation scoring or many extra baselines to make the contrast valid. The simple mechanism has valuable advantages: no root-label fitting, no learned-capacity discrepancy between O/R, a visible graph intervention, and directly auditable inputs. A strong external contextual comparator is still useful for practical interpretation but not the causal identification device for O−R.

### 10.2 Controls do not preserve effective smoothing

The R design preserves per-node degree, component partition, the smoothing coefficient, number of vertices/edges and algorithmic form. It **does not** preserve spectrum, bottlenecks, mixing rate, path lengths, local signal homophily or effective smoothing strength. Those properties change because the arrangement changes. It is defensible to treat them as part of the tested relational structure; it is not defensible to say that all smoothing effects have been removed as an alternative explanation.

Required wording: fixed propagation rule/coefficient and degree/component structure are controlled; higher-order structural and smoothing differences remain part of the contrast. O−L demonstrates a pipeline change; O−R narrows the explanation beyond those preserved properties. Neither proves that an edge's business/causal semantics caused the gain.

Constant-input invariance is a good algebraic sanity check: with row-stochastic P, `l = c1` implies `q = c1`, and an isolate retains its local score. It prevents a ranking generated from a globally constant input solely by centrality. It does **not** remove all degree/position interactions with nonconstant scores. The q values are smoothed evidence scores, not calibrated root probabilities or necessarily a probability-mass PageRank vector. These properties can be fixture-tested without experiments in E.

### 10.3 Define the R estimand and validity before scores

For each incident, compute each perturbed graph's ranking and reciprocal rank, then take the mean **of those reciprocal ranks**. Reciprocal rank of an average score vector answers an ensemble-ranker question and is not the same contrast. State which is intended; the proposed wording suggests the former.

Each chain can start from O with an independent seed, but a fixed finite chain is not a uniform sample over all valid graphs. The resulting reference is the declared perturbation algorithm/distribution. Do not report a permutation/randomization p-value relying on exchangeability between O and R. Report finite-seed variation/Monte Carlo limitations; seeds are not additional incident samples and should not be selected by performance. A 32-seed average is a reference expectation estimate, not 32 new independent successes.

Component preservation must mean the resulting connected-component vertex sets are exactly equal, not merely that an edge switch stays within each original component; an internal switch can disconnect a component. Specify rejected proposals, repeated graphs, no-switch graphs, graph serialization and the fixed budget. Unique degree sequences such as a labelled star, cliques and isolates can make every allowed graph equal to O. Such cases are still in the denominator, but cannot identify a residual arrangement effect.

Preset **label-free** diagnostics: accepted switches, unique edge sets, edge overlap, number of mobile edges/nodes and proportion of cases with a nontrivial control. Do not automatically invalidate every study because a few components are frozen. Conversely, if almost all controls equal O, the primary residual-structure claim is not identified. The final draft must state the criterion for that verdict before E/G; it may honestly use a declared feasibility review based only on graph diagnostics rather than pretend a universal numeric threshold is known.

### 10.4 Graph time support, symmetrization and volume

Reference-only graph construction is a legitimate choice that prevents incident-induced topology updates from silently joining the treatment. Explain the tradeoff: a reference graph can be stale/incomplete and query-only services may be isolates. Use the same permitted candidate universe in every arm and retain missing roots. The full-case audit union must never repair the graph.

Symmetrization intentionally discards parent→child direction. This is a bounded adjacency-utility test, not evidence about upstream propagation. It can fail when direction matters even if directed graph reasoning would work. Do not add a direction arm merely to rescue a negative result; a later change needs a protocol version/review.

Binary edges avoid **explicit edge-frequency weighting**, not all volume confounding. Edge visibility, degree, service sampling, feature precision and missingness can still depend on traffic. R preserves the node degrees associated with those features, which helps, but does not remove every signal–traffic–topology association. Record local score/coverage/volume diagnostics without root-guided filters or post-hoc removal.

### 10.5 Local evidence can make the test vacuous

The supplied scorer description is not yet implementable: per-channel construction, reference normalization, variance floor, missing reference, aggregation over time/channels/modalities, scaling, clipping and no-evidence scores remain necessary. A single scalar per service is acceptable; it must not silently prefer services with more channels or blend incomparable scales.

Same l in all three arms establishes a matched treatment input but does not establish that l is useful for diagnosis. If it is constant, saturated or nearly all missing, O/R can only answer a degenerate question. D/E should check scorer mechanics and label-free variation/coverage without tuning on root outcomes. A negative result must be stated as conditional on the chosen evidence model, not proof that relations contain no useful information.

For logs: excluding log scores from the primary matched contrast is possible, but D must explicitly retain actual log-to-service/time/graph-evidence mapping and availability handling in the intended F pipeline to respect DT18 and the C lock. Logging a future placeholder is not implementation. Do not claim a three-modality scoring experiment when only metric/trace scores enter rank. Optional log ablation should not inflate the core test.

### 10.6 Split, uncertainty and decision rule

A 10-development/20-evaluation scenario split with all three repeats together is preferable to scattering repeats across partitions for the intended new-combination assessment. The split is **not exactly balanced across all six faults**, because ten is not divisible by six; say near-balanced and show the deterministic assignment. Each root/fault can occur on both sides, so this is held-out combinations within familiar identities, not unseen-root/fault/system transfer. Root/fault metadata for grouping is evaluator-only and must not enter features.

The E1 exposure makes the correct claim a prospectively locked comparison on a previously studied benchmark, with an evaluation subset excluded from new D/E/F tuning. Never call it untouched or historically outcome-unseen. If the development partition includes raw/schema-inspected cases, record that rather than changing assignments to fabricate independence.

Scenario-block bootstrap handles the repeats within each included service×fault cell; it does not make the 20 designed cells independently sampled from a population or eliminate crossed root/fault dependence. Report intervals as conditional uncertainty/stability under that resampling scheme. Leave-one-root/fault-out sensitivity is useful, but with only five/six groups it is not independent validation or proof of calibrated population coverage. Preserve three-repeat aggregation and failure contributions in every draw.

Two jointly required improvements avoid selecting the easier comparator after results. State the complete success rule: whether the 0.05 threshold applies to point estimates or interval lower limits, which uncertainty condition is also required, and how equality, broad intervals and conflicting contrasts are classified. Do not call 0.05 an empirically validated operational utility threshold; it is a prespecified study criterion unless independently justified. A conjunction is different from claiming significance if either contrast wins; do not reflexively multiply corrections without naming the claim family.

### 10.7 C3/C4 and outcomes that must remain visible

Keeping literal operation evidence in the packet while deferring scored operation representation is consistent with C3 if its reason is stated: it isolates the service-level relation contrast and avoids conflating feature-granularity changes. Do not claim an operation representation ablation was run.

For C4, L/O/R test the use and structure of graph **at one fixed placement after local scoring**. This is a graph-use/structure ablation and a C4 placement disposition; it is **not a comparison of graph placements**. Say that direct graph-conditioned local scoring is deferred with a reason, not experimentally ruled inferior.

If O improves over L but matches R, report evidence compatible with useful generic degree/component/smoothing effects, while the additional observed-arrangement claim is unsupported. If O fails against L, the mechanism has no demonstrated practical gain in this setup. If R is effectively unchanged, the residual-arrangement result is uninformative. Those are distinct outcomes; do not collapse them into a universal “graph has no value.”

### 10.8 Required fixes before final draft acceptance

1. Exact scorer/window/candidate/failure/tie contract and correct score semantics.
2. Qualified nuisance-control table; R mean-of-metric estimand; precise rewire and control-mobility validity rule.
3. Explicitly near-balanced scenario assignment, historical exposure, conditional uncertainty and complete joint decision rule.
4. Concrete log mapping and C5/LLM downstream contracts without increasing core scoring scope implicitly.
5. Accurate C3/C4 disposition and contextual comparator fidelity/acceptance criteria.

With these details, the proposal is informative enough to specify and submit to Minh. None requires running a baseline now. Full-draft review remains pending; this is not protocol acceptance.

## 11. Phase 4 — Full TD-v1.0 adversarial review

Date: 2026-09-23. Read the entire P/docs/research-rca/task-d-method-and-experiment-specification.md, including the previously truncated middle retrieved separately. Reviewed SHA-256: `CA7004757CC463304B32B4A4F42C1989A9F1E4947B40C82ED46BECA40B385038`. Findings refer to that exact version; line numbers are navigation aids, section references control. The source-first opinion remains unchanged. No protocol edits, real-data reads, baseline execution, installs or downloads were performed by this reviewer.

**Review verdict: REVISE BEFORE OWNER ACCEPTANCE / E.** No CRITICAL defect or reason to reopen C1/A/B/C was found. Five MAJOR specification issues below can materially change outputs or conclusions; they are local to D and can be corrected without adding a new research method. Several MINOR ambiguities should be made deterministic before implementation. All findings and suggested remedies are `CANDIDATE` pending main-agent adjudication; they do not approve or replace the protocol.

### 11.1 MAJOR findings

#### DREV-01 — Provenance-changing canary contradicts the control seed rule

**Severity: MAJOR. Locations: §2 lines 46–48; §5.1 line 124; §13.1.** §2 requires changing case ID/path metadata with telemetry unchanged to preserve ranks. Yet case_handle is a hash of caseID and every R seed hashes case_handle. Changing caseID therefore changes the control graphs and potentially R ranks with no telemetry change. This is an exact contract contradiction, not merely a potential implementation bug.

There is a second stochastic equivariance issue: sorting edges by opaque node keys and replaying the same random integers after arbitrary reindexing need not select the correspondingly permuted edges. L/O are permutation-equivariant algebraically, but a finite sample of 32 newly generated R graphs is not guaranteed to be bitwise equivariant under that procedure, even if its distribution is equivariant.

**Required correction:** choose and document one consistent randomness contract before E. For example, freeze a seed stream unrelated to mutable answer-bearing provenance, record its identity only in the manifest, and hold that stream fixed for metadata canaries. For service-index permutations, require exact deterministic-core equivalence using correspondingly permuted control adjacencies/coupled proposals, and separately test that the generator preserves its graph invariants. Do not promise exact finite-sample R equivalence under an independently regenerated chain unless its ordering/coupling guarantees it. Keep actual seed and mapping provenance visible; do not weaken label isolation to hide this contradiction.

#### DREV-02 — C5 has ground-truth bin labels but no defined predicted bin labels

**Severity: MAJOR. Location: §10 lines 209–215.** The protocol defines a score threshold, three-bin persistence and refractory alert events, then requests per-bin P/R/F1. It never states whether a bin's prediction is (a) raw threshold exceedance, (b) a persistence-qualified state, (c) only the trigger impulse, or (d) an active alert during the refractory period. These produce radically different recall/F1 for an identical sustained signal. Event counts cannot silently become anomaly-state labels.

Also undefined: a system bin with no valid channels; whether its placeholder zero enters calibration; handling an incident with no evaluable positive/negative bins; and zero-denominator precision/F1 when no alert is produced. `≥100 valid system bins` does not define a valid system bin or these metric cases.

**Required correction:** specify a deterministic `predicted_regime(t)` separately from `trigger_event(t)` and name which feeds bin metrics. Define valid-system-score construction from available channels, unavailable/reset behavior, denominator/undefined rules and macro aggregation. Preserve alert suppression and trigger counts as separate endpoints. Add a short synthetic sequence fixture with sustained exceedance, a gap and a refractory period; expected bin labels and trigger times must be explicit. No new dataset or detector family is required.

#### DREV-03 — The clipped C5 score can make the trigger mathematically unreachable

**Severity: MAJOR. Locations: §4.1 and §10 lines 209–211.** C5 reuses the channel score bounded in [0,1], then calibrates its 99th percentile and requires a **strict** exceedance. If the 99th percentile is 1, no possible future valid score can trigger. This is not ordinary conservatism: it is structural inability to trigger. For example, 100 calibration scores containing 98 zeros and two ones give type-7 q99=1. The present calibration check only requires a count of 100 and would accept this unusable operating point. No claim is made here about the actual dataset's saturation prevalence.

**Required correction:** before E, either define an unclipped C5 score (separate from the frozen C1 rank score), or add an explicit calibration-adequacy failure when the strict-threshold support is empty, with a predeclared D-revision route before G. Also log threshold ties/saturation and a synthetic capped-score fixture. Do not switch `>` to `>=`, change the percentile, or tune persistence after looking at regime labels. A structurally impossible detector must not be accepted as a functioning automatic-trigger capability merely because it produces a zero score table.

#### DREV-04 — Insufficient-history diagnosis and detector restart have no executable state machine

**Severity: MAJOR. Location: §10 lines 211–217.** Detector triggering starts after 360 seconds, but diagnosis at trigger t requires history back to t−660. For t<660 relative to the observed origin, waiting cannot recover the missing past for that original trigger. “Pending diagnosis until the first trigger with enough context” does not specify whether the old trigger is discarded, queued, moved to a later anchor, retried without a new trigger, or suppressed by the 300-second refractory timer. These choices change composed RCA coverage and the first eligible post-injection diagnosis.

The crop/restart check also promises comparison after identical 360-second history while a three-score streak depends on two earlier endpoints: identical latest feature history alone need not imply identical previous streak state. Refractory state is recognized in the draft, but persistence state also needs a defined carry/replay rule.

**Required correction:** define observed replay origin/bin anchoring, the alert/persistence/refractory state transitions and diagnosis disposition. A simple option is: a trigger lacking history records `INSUFFICIENT_HISTORY` with no queued rank; refractory still applies; a later independently emitted trigger may qualify. Alternatively specify a different complete policy, but do not shift the original t silently. State exactly which state/history is held equal in restart fixtures, or require enough additional elapsed bins to rebuild persistence before comparing events. Composed endpoint must consume this same state machine.

#### DREV-05 — Undefined signal/ceiling/failure overrides can rescue a negative result after outcomes

**Severity: MAJOR. Locations: §4.1 line 89; §7 verdict table lines 174–180.** Control mobility has an explicit pre-G criterion, but “signal starvation/ceiling,” “effective perturbation does not discriminate,” and “results mainly depend on unexplained failures” do not. Since these override VALID NEGATIVE, an analyst can inspect a graph loss and retrospectively label the experiment inconclusive. The draft forbids endpoint changes but currently leaves this discretion inside the locked endpoint.

In particular, if L already ranks every root first, an inability to improve by 0.05 is a valid bounded finding about utility over L under the declared setup; ceiling alone does not make the estimand undefined. Similarly, O/R can yield the same output on genuinely different admissible graphs for informative nonconstant l; that can be a zero arrangement effect rather than failed control construction.

**Required correction:** enumerate mechanically testable information-validity overrides with exact scope, timing and thresholds, preferably label-free before outputs. Define whether “all tie” means every incident or a stated fraction, distinguish no-input failure from a legitimate tied output, and distinguish structurally unchanged controls from equal rankings produced by changed controls. Remove ceiling as an automatic inconclusive escape, or specify its limited interpretation before outputs without overriding the finite-set effect claim. Define the crash/seed-failure asymmetry criterion rather than deciding what “mainly” means after results. Keep descriptive failure analysis and all planned denominators regardless of verdict.

### 11.2 MINOR issues that need precise implementation conventions

| ID / severity | Exact location and issue | Minimal correction |
|---|---|---|
| DREV-06 — MINOR | §4.1 line 82 says conflicting metric duplicates invalidate “channel/case evidence.” Channel invalidation with zero+mask and shared incident failure with all-arm zero produce different rankings and denominators. §8 does not select which applies. | Pick one deterministic disposition for conflicting duplicates and distinguish it from corrupt-file/trace failure. Add the matching fixture. |
| DREV-07 — MINOR | §5.1/§8: R is a mean of 32 runs, but “failure0 for that arm” does not identify whether one chain timeout zeros that chain, the full R family, or the whole incident. Timeout scope likewise does not say whether R budget is per chain or aggregate. | Define planned seed denominator, per-chain/aggregate timeout and numerical-failure behavior. Never average only successful chains. Report partial failures and apply the fixed verdict rule from DREV-05. |
| DREV-08 — MINOR | §2, §4 and §12: the scorer is said to receive only normalized arrays without epochs, but `rank(bundle,window,config)` exposes time-bearing observations and intervals unless this is explicitly a trusted facade around a separate core. | Name the trusted adapter/controller boundary and the exact unprivileged core input schema; the facade may slice but the core must follow §2. |
| DREV-09 — MINOR | §4.1: zero trace count is a count of observed spans when parsing succeeds; it does not establish zero actual traffic under incomplete/sampled telemetry. §5 says report boundary-censored/unresolved parents although selected-window-only reads may not distinguish a parent outside the window from an uncollected parent. | Use “zero observed span count” and “unresolved within selected reference, potentially boundary-censored”; only report a separately known boundary-censor count if supported without forbidden out-of-window telemetry. |
| DREV-10 — MINOR | §11 permits logs/operation evidence but `ObservationBundle.spans` in §12 omits operationName; error redaction and log sampling hashes are required but their stable key is not specified. | Include the optional literal operation key in the adapter or name a separate support bundle. Specify stable sampling identity and sanitization responsibility so records are not selected by GT or response content. |
| DREV-11 — MINOR | §7 root/fault deletion condition says “if conclusion changes” before the precise support table requires only all deletion point effects >0. An effect can remain >0 but fall below δ, creating two interpretations. | State that the locked sensitivity rule is sign preservation (if that is intended); crossing δ is reported heterogeneity but not an additional unstated veto. |

### 11.3 NOT VERIFIED — honest limitations, not defects to repair now

- **NOT VERIFIED:** actual reference-window graph mobility, ≥80%/stratum adequacy, score saturation, target visibility and useful nonconstant local evidence. The existing full-case audit cannot establish these. The pre-G topology/label-free checks are the right location; no audit rerun or baseline execution is required during D.
- **NOT VERIFIED:** runnable source pins/licenses, all-file schema/joins, comparator runtime and fidelity. The protocol correctly makes these E/F receipts. A paper-equation BARO component adaptation is a legitimate declared contextual comparator; exact end-to-end BARO is not being claimed.
- **NOT VERIFIED:** independent-population interval coverage. The draft explicitly narrows the bootstrap to a conditional exchangeable-scenario approximation and discloses root/fault/campaign dependence. This is an honest inferential limit, not grounds to invent a multi-dataset campaign now.
- **NOT VERIFIED:** actual C5 performance, log evidence usefulness, LLM faithfulness and FlashTicket transfer. They are later measurements, not present D results.

### 11.4 Coverage of the requested adversarial attacks

The following twenty lenses cover the supplied attack categories without forcing an issue under every heading. “Addressed” means the draft's contract is adequate at specification level, not that execution has passed.

| # | Lens | Assessment |
|---:|---|---|
| 1 | Construct: graph utility versus all graph information | Addressed by narrow undirected-reference-arrangement estimand, §§1/5. |
| 2 | Task and target/GT fit | Addressed: known-window service rank; no operation/node/causal GT claim. |
| 3 | Input/oracle/path leakage | Generally addressed; exact canary contradiction DREV-01 and facade clarification DREV-08 remain. |
| 4 | Candidate universe and query-only/missing targets | Addressed: same trace-derived per-window V, missing root zero, no injected-label candidate list. |
| 5 | Feature/reference construction and starvation | Detailed enough for core design; duplicate policy DREV-06 and verdict escape DREV-05 remain. Empirical usefulness is NOT VERIFIED. |
| 6 | Capacity/scoring fairness | Addressed for O/R; L/O change propagation intentionally. No learned-parameter mismatch hidden. |
| 7 | Degree/volume/smoothing alternatives | Addressed with declared preserved quantities and spectrum/visibility limitations. No complete nuisance-removal claim. |
| 8 | Structural randomization/null validity | Good fixed finite algorithm and no uniform/permutation-p claim; DREV-01/07 require reproducible randomness/failure scope. |
| 9 | Baseline strawman and comparison scope | Adequate bounded package: Local-MAX plus declared BARO component; no SOTA superiority claim. No mandatory demand for every paper implementation. |
| 10 | Comparator fidelity/supervision eligibility | Adequate labeling and E acceptance fixtures. Original root-supervised Eadro/DéjàVu not run under forbidden training. |
| 11 | Historical exposure/held-out semantics | Strong: E1 exposure explicit; no untouched-test claim; scenario split is new-tuning holdout only. |
| 12 | Incident/repeat/seed pseudoreplication | Addressed: incident outcomes, scenario aggregation, fixed 32-seed metric mean; seeds/spans not extra n. |
| 13 | Multiplicity and uncertainty | Conservative two-contrast intervals and conjunctive rule defined; dependence limits explicit. No statistical-significance proof claimed. |
| 14 | Missingness/errors/denominators | Planned denominator preserved; remaining exact dispositions DREV-06/07 and DREV-05 overrides need correction. |
| 15 | Graph semantics and time support | Adequate observed relation/symmetrization disclosure; wording precision DREV-09. |
| 16 | Detector versus ranking and chronology | Major unresolved C5 prediction, reachability and state-machine definitions DREV-02/03/04. |
| 17 | C3/C4 role and deferred scope | Addressed: operation support retained, no claimed operation accuracy; one placement disposition, no cross-placement experiment claim. |
| 18 | LLM/evidence integrity | Adequate immutable-rank/untrusted-evidence boundary; support adapter omission DREV-10. I evaluation remains separate. |
| 19 | Reproducibility/freeze/implementation readiness | Substantial manifest and fixture contract; DREV-01/04/06/07/08/10 need precise contracts. No premature run/fidelity claim. |
| 20 | Negative/inconclusive/invalid verdicts | Numerical joint thresholds are clear; qualitative overrides DREV-05 and sensitivity ambiguity DREV-11 must be closed. |

### 11.5 Required main-agent adjudication and next step

Main agent should accept, reject with source/reason, or resolve each DREV-01–05 in the protocol and record the exact delta. Close minor implementation choices in the same revision where straightforward. No reviewer vote is needed and no new human scientific choice is inferred from this report.

After correction, verify the final protocol hash and the changed sections against these findings. Minh still owns protocol acceptance and the separate E execution authorization. The review file remains the only artifact changed by this reviewer; original source-first sections and earlier opinions are preserved.

## 12. Phase 4 — Verification of the first correction pass

Verified revised TD-v1.0 SHA-256 `85E6DA0556466A2F4E9F21D4000A5C127778497997F542D7FBCD5C013741B75A` on 2026-09-23. This is a new draft snapshot, not an overwrite of the §11 review input.

| Finding | Verification result |
|---|---|
| DREV-01 | **Resolved at specification level.** Metadata canaries retain pinned execution handle/seeds; service permutations carry realized controls. This tests the deterministic core with coupled random inputs rather than claiming exact independently regenerated Monte Carlo equivalence. |
| DREV-02 | **Resolved at specification level.** Predicted bin label is threshold exceedance before persistence/refractory; no-valid-channel bins are unavailable; undefined metric denominators use zero with counts. Alert-event and composed ranking endpoints are separate. |
| DREV-03 | **Resolved at specification level.** C5 uses an explicitly separate unbounded absolute-deviation score; the C1 capped scorer is unchanged. Calibration performance remains unverified, but the hard support-ceiling contradiction is removed. |
| DREV-04 | **Partly resolved.** Consecutive diagnostic windows require 600 seconds; insufficient-history trigger fails immediately without queued future diagnosis. First post-injection trigger remains the composed endpoint even on failure. Persistence/refractory and crop-state details below still need closure. |
| DREV-05 | **Resolved at specification level.** ≥80% flat/empty local vectors, >10% shared-input failures, or any core-arm-specific failure are predeclared inconclusive conventions. Local ceiling is explicitly not an escape. Thresholds are disclosed design conventions, not empirically validated universal criteria. |
| DREV-06–11 | Still present in this intermediate snapshot; awaiting main-agent disposition or wording corrections. |

Remaining part of DREV-04: “three consecutive bins” plus refractory does not specify whether streak updates/resets during refractory, whether trigger condition is `streak>=3` or exactly `==3`, and how sustained exceedance can retrigger. The restart fixture still allows score/streak comparison after identical 360-second history, although streak depends on two previous score endpoints. Minimal deterministic correction: define streak update on every valid endpoint, reset on unavailable/non-exceedance, specify the trigger predicate and whether streak resets on emission. Compare raw score after identical 360-second history; compare persistence after enough additional endpoints to reconstruct it (20 seconds for this design) or with explicitly carried state; compare emitted alerts only with the same refractory state. This is a state-definition fix, not a request to change the detector method.

## 13. Phase 4 — Final correction verification and closure

Verified TD-v1.0 SHA-256 **`9822A92081FB5D958FDE35B68D274906BD36EE66288017645A7EC6840A2C1C4D`** on 2026-09-23. Read all changed sections identified by DREV-01–11 and the added acceptance fixture; the entire initial draft was read in §11. Earlier findings remain as evidence of the review sequence.

| Finding | Final disposition and evidence |
|---|---|
| DREV-01 | **RESOLVED — §2.** Pinned random execution inputs stay fixed under metadata canaries; service permutation carries realized controls. |
| DREV-02 | **RESOLVED — §10/§13.1.** Score exceedance supplies bin predictions; trigger events are separate. Unavailable bins and zero/undefined per-case metrics have explicit handling and planned denominator. |
| DREV-03 | **RESOLVED — §10.** Separate uncapped C5 score eliminates the impossible strict-exceedance-of-1 configuration. |
| DREV-04 | **RESOLVED — §10/§13.1.** State initial values, every-bin streak update, `streak>=3`, refractory expiry, insufficient-history failure and no pending retry are explicit. Score comparison needs 360 seconds; event comparison needs 380 seconds plus matching refractory state. The proposed threshold-2 synthetic sequence correctly implies triggers at 380 and 680 with the stated gap; this was checked from the stated transition rule, not a claimed executed detector run. |
| DREV-05 | **RESOLVED — §7.** Information/failure conventions are numerical and prespecified; ceiling is not an inconclusive escape; changed graphs with equal scores are no longer automatically treated as invalid controls. |
| DREV-06 | **RESOLVED — §4.1.** Conflicting metric duplicates invalidate that entire channel over the incident's selected reference/query, preserve other channels and use the specified mask/placeholder. Trace-key conflicting payload is a separate shared-case failure. |
| DREV-07 | **RESOLVED — §5.1/§8.** Every failed R chain contributes zero in denominator 32; resource limit covers all 32; uncompleted chains remain failures; any failed chain invokes the declared relation-attribution inconclusive rule. |
| DREV-08 | **RESOLVED — §12.** `rank` is explicitly the trusted facade; separate `score_core` receives numeric arrays/masks/service indices/adjacency/config, without bundle, windows, epochs, handle or GT. |
| DREV-09 | **RESOLVED — §§4.1/5.** Counts are explicitly observed spans; unresolved parents are only known unresolved within reference, with possible boundary censoring and no extra out-of-window repair. |
| DREV-10 | **RESOLVED — §§4.2/12.** Optional operationName and opaque log record identity are present; deterministic source-hash/row-ordinal sampling precedes trusted versioned redaction. |
| DREV-11 | **RESOLVED — §7.** Deletion sensitivity veto is exactly positive point-effect sign preservation; crossing δ is descriptive heterogeneity rather than a second hidden gate. |

**Final independent methodology assessment: no unresolved CRITICAL or MAJOR finding in the reviewed specification.** The draft is ready to be presented for Minh's protocol acceptance under the existing D→E gate. This is reviewer closure of identified document defects, **not human approval, scientific result validation, or authorization to run E**. The technical selections remain `CANDIDATE`; root decision policy and task scope are unchanged.

Material limitations remain explicit and appropriate: finite previously studied RE2-TT population; no graph-wide/causal or population-generalization claim; fixed simple scorer and undirected reference adjacency; no supervised-root fitting; conditional bootstrap assumptions; loader/mobility/feature adequacy and executable baseline fidelity still unverified; C5/LLM/FlashTicket results belong to later tasks. The strong negative/inconclusive rules and conservative information conventions may reduce the chance of a supported result, but are disclosed before new outcomes rather than selected to rescue H1. An E incompatibility must follow the recorded D revision path before G.

Only W/task-d/task-d-independent-review.md was edited by this reviewer. Validation: direct source/section checks, corrected-state transition reasoning, complete review addition inspection and whitespace check. No numerical effect, benchmark run, full raw audit, package setup or outside-system mutation occurred. Preserve the source-first §§1–7 and all subsequent versioned passes when packaging the handoff.
