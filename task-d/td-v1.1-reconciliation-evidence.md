# TD-v1.1 — Independent reconciliation evidence

- Date: 2026-09-23. Owner: Minh; main adjudicator: Codex. Class: FORMATION / evidence supporting the canonical protocol in P.
- Authority: current request “Independent Reconciliation + TD-v1.1 Revision” §§0–39; later explicit Minh clarification preserved in advisor evidence §3/RCA-018–021. Technical selections remain CANDIDATE.
- P = `D:/Project/flash-ticket-platform`; W = `D:/Project/flash-ticket-rca-research`. Before review: P branch `codex/rca-research-program`, HEAD `6bd04e625926e923301cc6bb1433682f01fd87fc`; W `main`, HEAD `c7e47fdcc69c53876f7bd3f1a5e71ef89c59ccf6`. Only pre-existing tracked change was P/README.md; preserved SHA-256 `3646cb1b6e8da832e8b9513fd8318d749f7f5f6788b5d3223eda7f5a9a662274`. No newer D revision was present.
- Current revision is local, not committed/pushed. Earlier commits above preserve TD-v1.0; do not describe this revision as already on GitHub.
- Scope: source reconciliation/specification, independent reviews, small deterministic document/math checks. No E/F/G/H/I implementation, baseline/data run, training, install, full corpus download or app changes.

## 1. Evidence and independent discovery

Required sources read: P AGENTS/skill/authority reference, DT18/roles, old22/08 letter, RCA decisions/C Phase2/Master/state/map, full current protocol and handoff, Task A prior mechanisms/metrics/datasets/§M, C shortlist, B digest; W B CLOSED§12 and metadata/log reports, C ledger/red-team/literature positioning, D-v1.0 evidence/exposure/independent review. Deeper inspection only to settle SS/LEMMA compatibility and historical/current attribution; no restart of A/B/C raw audit.

A separate source-first reviewer received authoritative artifacts plus new verbatim guidance **before** seeing candidate fixes/full request. Its [FIRST PASS](td-v1.1-source-first-review.md) is preserved; final file hash is recorded in the machine receipt. After persistence the same reviewer challenged the concrete proposal. A different fresh reviewer owns [delta review](td-v1.1-delta-review.md). Independence is interpretive, not independent datasets or a vote.

**Strengths retained:** C1 matched evidence/control estimand, explicit leakage/exposure, root-label firewall, ties/failure denominators, valid negative results, bounded dataset semantics, and downstream LLM rank invariance. Source-first found real gaps in graph detection, program ownership and method rationale; it rejected any inference that C1 must be discarded or Task A has no technical depth.

## 2. Conflict matrix and adjudication

“Resolved” below means specification/ownership/provenance correction, not measured method success. Severity is main adjudication using the user's four finding levels; source-first MODERATE wording is preserved in its original artifact and mapped here to MINOR or execution risk as appropriate.

| Source / requirement | Current TD-v1.0 behavior | Conflict? | Severity / owner | Evidence | Resolution in TD-v1.1 |
|---|---|---|---|---|---|
| Advisor Step1 dependency graph | Reference observed service relations; undirected processing | No task gap; semantics bounded | OBSERVATION D/F | D§5; B§12.6–7 | Keep graph; explicit direction choice/limits |
| Advisor Step2 graph AD | Metric-only detector, graph after trigger | Yes: local capability gap, more than naming | MAJOR D | OldD§10 vs new source Step2; A§D.3 | §10 graph-conditioned score before threshold with matched local control |
| Advisor log/trace graph mapping | Counts/excerpts support; trace evidence scores C1 | Partial | MINOR D/F | OldD§4.1–2/10 | Separate structure/evidence; logs contribute C5 node score, no edge join |
| DT18 M/T/L mapping | Two scored modalities + passive logs | Partial, not proof of noncompliance | MINOR D/F/H | DT18-NV2; oldD§4/11 | Node counts/scoring/packet roles explicit; quality not yet measured |
| C1 primary role | Narrow known-window relation-utility contrast | No | OBSERVATION D | C lock§1; RCA001–004 | All C1 numeric/input/control/statistical rules retained |
| C3 mandatory topic | Operation support; scored study deferred | No; not operation accuracy | OBSERVATION D/F | C lock§2; RCA006/007; D§9 | Preserve, counts not anomaly GT |
| C4 mandatory topic | Late graph ranking; cross-placement deferred | No | OBSERVATION D | RCA008; D§9 | C5 pre-alert graph is capability mechanism; no automatic C4 placement campaign |
| C5 mandatory capability | Metric detection→graph RCA | Role right, strict graph detector absent | MAJOR D | RCA009 + advisor Step2 | Concrete C5 graph/input/threshold/state/evaluation contract |
| Task-B detection limits | System-bin injection-regime only | No | OBSERVATION F/G/H | B§12.9–12 | Keep labels/claims bounded; no production onset/FPR |
| Task-B graph-AD limits | Read as not node-evaluable | Overstated if read “all graph AD forbidden” | MINOR D | B§12.12; C5 regime labels | Graph-conditioned system score evaluable PARTIAL; node truth remains NO |
| Existing metric-only C5 | All mapped metric entities; no graph | Yes for stricter source guidance | MAJOR D | OldD§10 | New trace-derived V restriction disclosed; no silent comparator equivalence |
| Logs current role | Packet-only | Partial capability choice, not invalid C1 | MINOR D | OldD§4.2 | C1 unchanged; LOGCOUNT-v1 for C5/integrated profile |
| TRACE_STRUCTURE | Implicit within graph builder | Naming ambiguity | MINOR D | OldD§4–5 | Explicit relation fields/reference-only graph in §10.1 |
| TRACE_EVIDENCE | Span occurrence, not duration/status | Already valid; roles conflated by “trace” label | MINOR D | OldD§4.1 | Keep occurrence; state topology use in every caption/arm definition |
| Integrated MTL proposal | Not fully defined/scored | Candidate justified as bounded capability, not novelty | MINOR D/F | Newrequest§11 vs oldD§10–11 | Count evidence→graph AD→triggered MTL rank→packet; cannot claim gain yet |
| Current modality ablation | Different M detector and MT ranking tasks | No matched M/ML/MT/MTL study | MINOR D | OldD§4.1/6/10; A§C.7/G is prior work | Four C5 configs: nested3 + local1; no factorial claim |
| Multi-public expectation | RE2-TT then FlashTicket | Yes: no owned expansion path | MAJOR D/Minh/E/J | Advisor final paragraph; MRP-v1; C§4.10 | §15/MRP PUBLIC-EXTENSION gate, bounded SS/LEMMA audit; selection/results OPEN |
| Metric mapping | MRR/Hit; regime P/R/F1; NDCG only “not primary” | Missing explicit NDCG disposition | MINOR D | OldD§7/10; A§J.1 | Secondary expected-tie NDCG@5, no extra primary test |
| LLM role | Immutable rank packet, no GT/tools | No | OBSERVATION F/I | RCA010/011; D§11 | Packetv1.1 carries separate detector/profile; I still evaluates |
| FlashTicket later | H separate, D–G independent | No | OBSERVATION H/system | RCA013–015; DT18 | Keep real integration/system duties; no app/architecture edits |
| Advisor “demo-only” vs DT18 | Competing scope readings | Material if used literally; now resolved by Minh | MAJOR Minh | Newsource§1/3; DT18; RCA018–021 | User confirmed historical context and retained method value; no system reduction |
| Method-choice rationale | Detailed math, weak bridge from prior limitations | Yes, explanation/claim gap | MAJOR D for full-method claims | SF04; A§C/D/G/L | New§1.1 links mechanism/limitation/test; no claim improved prior method |
| Undirected justification | Causal uncertainty treated as reason to discard direction | Overstated | MINOR D | SF05; B supports observed direction | §5 deliberate simplification, explicitly loses direction |
| Compound inference gates | Precisely fixed but conventional | Risk of reading conventions as calibrated science | MINOR D/G | SF08; D§7 | §1.1 distinguishes informativeness/failure/claim strength; constants unchanged |
| Passive operation/log “capability” | Mapped evidence might sound like localization | Overclaim risk, not missing GT to invent | MINOR D/F/I | SF07; BGT | Exact scored vs support outputs and prohibited metrics |
| New graph smoothing | May be mistaken for amplification/structural AD | New design risk | MINOR D | q fixed point + row-stochastic P | §10 says max(q)≤max(a), possible true-spike suppression |
| Per-arm calibration | New four configs can have different numeric thresholds | Confound if called fixed-threshold effect | MINOR D/G | §10 math | Same policy/budget/endpoints, explicit total operating-policy comparison |
| Integrated diagnosis in modality arms | M detector still feeds MTL diagnosis | Misleading “M-only end-to-end” risk | MINOR D/G | §10.5 | Arm labels apply only detector node evidence; common diagnosis function |
| Missing-log case | No-log raw MT/MTL equality | Does not guarantee equal alerts with different thresholds | MINOR D/G | §10.4/6 | Preserve case/masks/denominator and report availability, no equivalence claim |

## 3. Audit of existing canonical modality ablations

Baseline audited = TD-v1.0 at P commit `6bd04e6`, before revision. C1 profiles and C5 detector from different tasks are **not** a matched study.

| Requested block | Frozen project-specific ablation already present? | Exact existing source / meaning |
|---|---|---|
| M | **PARTIAL** | D-v1.0§10 metric-only detector; §6 Local-MAX/BARO use metrics. No matched modality-ablation family |
| M+L | **NO** | D-v1.0§4.2 explicitly keeps logs out of score; no ML arm |
| M+T | **PARTIAL** | D-v1.0§4.1 l=(m+t)/2 in C1 L/O/R. They vary graph arrangement, not modality |
| M+T+L | **NO** | Logs only support packet at D-v1.0§4.2/11, no MTL scorer |

Task A§C.7/G/H describes **Eadro's** ablations and prior multimodal work, not a frozen FlashTicket study. C Phase1§4.3 treats logs as conditional supplementary block; reviewer suggestions do not create canonical experiments. Search was scoped to A/C/D/Master and W C/D ledgers; exact formula/arm definitions, not keyword matches, decided this table.

**Chosen candidate set:** C5-G-M → C5-G-MT → C5-G-MTL plus C5-L-MTL. All four: same trace-derived V, rolling300s/60s windows, same masks, no learnt parameters, same fit budget; G has observed reference topology, L identity but retains trace-derived candidate/evidence source. Numeric coefficients1/3 fixed for each enabled block, removed blocks0. Each config calibrates q99 once on same unlabeled dev endpoints. Logs missing0+mask, never case exclusion. Solver q=.5a+.5Pq; score maxq. Exact formulas/validity/failure rules at canonical D§10.2–6.

| Config | Modalities / graph / candidates | Missingness | Calibration/capacity | Question |
|---|---|---|---|---|
| C5-G-M | Metric node evidence + trace-derived P/V | Shared required metric/trace validity; no L/T node block | Same q99 policy, zero learned params, same solver | Base with trace structure, never “trace-free” |
| C5-G-MT | M+trace occurrence + same P/V | T unavailable0; no renormalization | Same | Conditional T contribution after M |
| C5-G-MTL | M+T+log volume + same P/V | Log missing/malformed/unmapped0+mask; keep case | Same | Conditional L contribution after M+T; candidate default |
| C5-L-MTL | Same MTL/V; identity operator | Exactly same MTL evidence/masks | Same policy, own threshold, same solver | Graph participation under matched calibration policy |

Rejected expansions: M+L is meaningful in principle but answers log contribution without trace evidence, outside minimal nested question; T-only/L-only/full factorial would add contrasts without a current primary objective. No log-confirmatory claim while full-input joins/usefulness unverified. No C5 structural controls/placement sweep: useful only under separately justified question. Negative supporting results remain reportable; do not choose the best config after seeing eval as if preregistered.

## 4. Revised pipeline and rejected alternatives

```text
Metrics --------> robust metric evidence ------------------------┐
Traces ---------> TRACE_EVIDENCE: span occurrence ----------------+--> service node evidence
Logs -----------> LOGCOUNT-v1: log1p row counts ------------------┘
Traces ---------> TRACE_STRUCTURE: reference parent links --> observed service graph
                                      node evidence + graph
                                               |
                                 graph-conditioned anomaly score
                                               |
                                 threshold + persistence --> alert
                                               |
                           same triggered MTL graph RCA profile
                                               |
                           operation counts + redacted log support
                                               |
                                  immutable EvidencePacket
                                               |
                            LLM explanation + suggested checks
```

This is the **intended integrated capability**, not an implemented system. Primary C1 remains separate known-window M+T L/O/R without detector/log scoring. C5 modality configs vary detector evidence; triggered diagnosis MTL is common. Operation evidence never supplies fabricated operation labels.

Log alternatives evaluated: raw row counts selected as least assumption-heavy numeric representation; severity counts require reliable severity schema/semantics not verified; template frequency/Drain/Drain3 can detect content changes but introduce vocabulary/config/order/version/fit-time choices and unknown usefulness; no-log-scoring leaves Step2 multimodal scoring less directly represented. Count scoring detects volume changes only, may miss constant-volume content anomalies and favor traffic changes. Tool choice is not needed: LOGCOUNT-v1 is a deterministic interface, no template identity to learn. A future template extension needs reference/dev-only vocabulary, frozen IDs/config/source hashes, no future/test fitting and a reviewed D revision. LLM parser is not accepted.

Simple graph smoothing is chosen to minimize assumptions/fit capacity while directly testing graph dependence before decision. It is not a new algorithm, cannot increase the maximum over local evidence, and may worsen detection. No evidence justifies a GNN or guarantees a stronger score. External graph-method superiority remains outside this package.

## 5. Component roles, states and evaluations

| Component | Role / changed? | Implementation scope | Public evaluation | FlashTicket evaluation | State |
|---|---|---|---|---|---|
| C1 | PRIMARY unchanged | M+T known-window L/O/R; controls/δ/inference unchanged | Root-service MRR, Hit and secondary NDCG; same60 cases | H transfer same declared contrast with target mapping | Role USER_CONFIRMED; method CANDIDATE; results OPEN |
| C2 | OPTIONAL unchanged | No horizon sweep opened | No new study | Only if separately scoped | Role USER_CONFIRMED; inactive |
| C3 | Mandatory topic unchanged | Literal operation evidence in packet; scored representation deferred | Mapping/count evidence, no operation accuracy | May evaluate localization only with matching intervention GT/scope | Role USER_CONFIRMED; disposition CANDIDATE; utility OPEN |
| C4 | Mandatory topic unchanged | C1 late mixing; no cross-placement study | L/O/R mechanism, not all placement options | H records actual mechanism | Role USER_CONFIRMED; implementation CANDIDATE |
| C5 | Mandatory capability; mechanism revised | Graph-conditioned detector plus same MTL diagnosis; four supporting configs | Regime P/R/F1/coverage/censored delay/composed ranking | H independent healthy/fault workloads, actual timing, labels | Role USER_CONFIRMED; revised method CANDIDATE; performance OPEN |
| LLM | Mandatory downstream unchanged | Packetv1.1 and no-rerank/no-GT/no-auto-repair contract | I evidence faithfulness/unsupported claims/usefulness | Same plus target packets | Role USER_CONFIRMED; provider/rubric execution OPEN |

## 6. Task / GT / metric matrix

| Task | GT available | Allowed metric | Forbidden interpretation |
|---|---|---|---|
| Known-window RCA | One published service root/case | MRR primary; Hit1/3/5; NDCG5 secondary with expected ties; failure0 | Detector quality, causal truth, multi-root/graded severity |
| Graph relation utility C1 | Same roots, paired L/O/R outputs after G | Paired ΔMRR under fixed controls; conditional scenario sensitivity | All graphs/algorithms, intrinsic information, causal path validity |
| System-level anomaly detection | Injection boundary only, not independently labeled onset | Bin regime Precision/Recall/F1, coverage, trigger count/rate, censored first-trigger delay | Production false-positive rate or actual onset latency |
| Graph-aware AD C5 | Same bounded system-bin labels | Same P/R/F1; matched graph/local operating-policy comparison | Node/affected-service F1 or structural anomaly correctness |
| Operation evidence | Literal operation identity/counts; no root-operation GT | Mapping/availability/packet faithfulness | Operation localization accuracy |
| Node anomaly detection | No per-service abnormality/affected-node truth | **None** for node P/R/F1 | Root service treated as the only anomalous node |
| LLM explanation | Structured evidence; root label only separate ranking evaluator | Faithfulness, unsupported statement rate, rank invariance, human usefulness under I rubric | Fluency as correctness; LLM-created ground truth |
| FlashTicket target validation | Future controlled interventions and measured telemetry | Only metrics matching actual target labels; system throughput/latency/errors/scaling/consistency/stability separately | Reusing public GT, claiming present runtime success, reducing DT18 to demo |

NDCG mathematical check: one strict root rank r≤5 gives1/log2(r+1), else0; ties average over **entire** group. Per-case strict order within top5 matches RR, aggregate does not necessarily: A ranks(1,6) MRR7/12, B(2,3) MRR5/12; NDCG5 A=.5 < B≈.5655. These are synthetic arithmetic values, not benchmark results. NDCG adds a discount view, not new label information or a second confirmatory victory condition.

## 7. Dataset verification details

Read-only RE2-SS metadata query by independent capability reviewer against existing `W/datasets/rcaeval/metadata/cases.parquet`; pinned SHA `c49a288920dbba2e8e724679a14636d5c7eb2b45426bba14007ef79a6c0ab1bb` matched.90rows,5roots×6faults×3repeat; metrics/logs90,traces0,root-cause-file0; injection inside window90/90; metadata720normal+721faulty timesteps percase. These are metadata facts, not certification of every raw schema. Broader SockShop metadata includes RE1-SS125/RE2-SS90/RE3-SS30, not interchangeable collections.

Existing W audit `audits/rcaeval/subagent-e-logs-multimodal.md` establishes sample `re2ss_orders_loss_2`:87,652rows, timestamp/container_name/message,10entities, exact entity-second joins. Text32hex/16hex patterns in2,850messages are merely candidate context; no verified parent/span graph. No raw reopened here.

[LEMMA v4](https://arxiv.org/html/2406.05375v4) §§3.1–3.2/AppJ and [official repository](https://github.com/KnowledgeDiscovery/rca_baselines) support IT metric/log node/pod data and controlled root labels/timestamps, not a pinned compatible service trace graph. Exact subdataset/revision/cases, entity-to-service map, root cardinality, independent onset/healthy controls and released span schema remain OPEN. Do not select a release from a paper count or use repo mention “trace” as schema evidence.

Canonical D§15/MRP gate resolves missing **ownership/path**, not missing external validation. Minh must accept the chosen supporting/replication scope before a second campaign; no new dataset mandatory for C1, no silent waiver of advisor expansion, no use of FlashTicket as a second public dataset.

## 8. Additional issues discovered beyond the prompt

Not every lens yielded a defect. Beyond the prompt's proposed repairs, the independent source-first reviewer identified:

1. **Observed direction vs causal direction (SF05, MINOR D):** v1.0 rationale implied absent causal truth justified removing observed direction. Corrected rationale in§5 without changing graph math; report lost directional signal as limitation.
2. **Method rationale vs implementation precision (SF04, MAJOR D):** detailed equations were not a compact explanation of which prior limitation motivated this probe. §1.1 now connects prior mechanisms/label constraints, choices, falsifiable observations and claims; no invented novelty.
3. **Compound thresholds as conventions (SF08, MINOR D/G):** carefully fixed constants cannot establish population inference or a universal informativeness criterion. Clarified purpose without changing C1 rules; real cost/mobility remain E/F.
4. **Affected-region display versus ground truth (SF07, MINOR F/H/J):** attached counts/graph are evidence views, not verified affected-region accuracy. No new affected-node requirement/labels manufactured; future display must state “observed suspicious evidence,” with actual target capability checked in H.
5. **Revision-created risks:** smoothing can suppress true isolated faults; per-arm calibration changes the estimand; missing-log raw equivalence does not imply equal triggers; detector modality labels do not describe common MTL diagnosis. All disclosed and contracted in§10, with deterministic checks for the mathematical claims.

No evidence here establishes benchmark performance, actual root coverage within windows, all-log quality, source/license executability, normal-history validity or deployment feasibility. These are NOT VERIFIED execution items, not solved by prose.

## 9. Independent review disposition

| FIRST PASS finding | Main classification | Revision / evidence | Disposition |
|---|---|---|---|
| SF01 product scope | MAJOR Minh | User clarification source§3, RCA018–021, D§0/15 | RESOLVED authority; exact old send date remains NOT VERIFIED |
| SF02 missing graph detector | MAJOR D | D§10.1–4 actual graph-dependent score before threshold + local control | Spec fixed; numerical fixture/fresh review validate, performance OPEN |
| SF03 public path absent | MAJOR D/Minh/E/J | D§15 and MRP named gate with compatibility/failure/owner/scope | Ownership gap resolved; second dataset selection and evidence OPEN, not a complete multi-public result |
| SF04 rationale | MAJOR D for advisor-facing claims | D§1.1 mechanism/limitation/test table | Spec rationale corrected, no SOTA claim |
| SF05 direction | MINOR D | D§5 reason only, math unchanged | Corrected |
| SF06 NDCG | MINOR D | D§7 exact binary gain/IDCG/tie/miss/cutoff | Corrected; supporting only |
| SF07 capability wording | MINOR D/F/H | D§4.2/10/11/15 and matrix§6 | Corrected scored/support boundaries; actual capability OPEN |
| SF08 inference conventions | MINOR D/G | D§1.1/7 | Clarified; C1 values unchanged |
| SF09 feasibility | NOT VERIFIED E/F | Existing loader/mobility/resources gates retained and C5 fixtures added | Correctly deferred, not claimed fixed by D |

CRITICAL first pass: none. Fresh delta reviewer independently checked the actual revision across20 attacks and compared five C1 blocks against TD-v1.0: no CRITICAL/MAJOR established. Three MINOR findings were corrected and reviewer-verified closed:

| Delta finding | Evidence / correction | Verification / final disposition |
|---|---|---|
| DR11-01 — endpoint bin ambiguity | D§10.6 now explicitly scores the last10s bin[t−10,t), not query60s | Fresh reviewer read corrected section; CLOSED |
| DR11-02 — full-file-hash log sampling not prefix invariant | Reviewer synthetic counterexample; D§10.6 limits future invariance to numeric/decision/rank outputs, with explicit retrospective packet/explanation limitation | Full hash/IDs/text never enter score; separate packet rank immutability retained; CLOSED |
| DR11-03 — unbounded streak counter after crop | D§10.6 compares decisions after380s with common refractory state, not numerical equality of accumulated streak | Three endpoints reconstitute predicate streak≥3; reviewer checked; CLOSED |

Additional independently discovered issue beyond supplied concerns: hash-based log sample selection can change past explanations when source-file suffix changes. It is bounded and disclosed, not silently repaired into an unverified streaming explanation implementation. No D-owned CRITICAL/MAJOR/MINOR remains. NOT VERIFIED items remain those in§7/11 and the reviewer report; no invented benchmark result. OBSERVATIONS include max-pooling/multiplicity, missingness/trace coverage, external graph-baseline absence and dataset-selection limits.

## 10. Exact file inventory and authority

Current task authority: request§26/27/30 allows source/protocol/minimal propagation/W evidence. Later clarification requires atomic human records under AGENTS; no technical proposal promoted.

| Kind | Exact path | Why / change / authority |
|---|---|---|
| CREATED | D:/Project/flash-ticket-platform/docs/evidence/advisor-direction/2026-09-23-huong-dan-do-minh-cung-cap.md | Verbatim separate advisor quote, unknown exact provenance, verbatim current user clarification; request§4/5 + U23 |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/task-d-method-and-experiment-specification.md | TD-v1.1 changelog/rationale/C5/MTL/metrics/packet/acceptance/coverage; request§26–30 |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/task-d-handoff.md | Current review outcome/opens/next action, preserve historical receipts by link |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/CURRENT-STATE.md | Single current revision/gate state |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/ARTIFACT-MAP.md | New source/reviews/validation and revised versions |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/MASTER-RESEARCH-PROGRAM.md | MRP-v1.1 C5 participation/public-extension ownership, no new RQ/task authorization |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md | One added§M provenance notice only; retain prior survey and old correction |
| MODIFIED | D:/Project/flash-ticket-platform/docs/research-rca/RESEARCH-DECISIONS.md | Append atomic RCA018–021 from actual user clarification, unchanged001–017 |
| MODIFIED | D:/Project/flash-ticket-platform/docs/project/decision-register.md | Register new RCAIDs/source/scope without duplicate decision authority |
| CREATED | D:/Project/flash-ticket-rca-research/task-d/td-v1.1-source-first-review.md | Independent opinion persisted before candidate proposals; request§8 |
| CREATED | D:/Project/flash-ticket-rca-research/task-d/td-v1.1-reconciliation-evidence.md | This required conflict/modality/roles/GT/finding/inventory record; request§31–38 |
| CREATED | D:/Project/flash-ticket-rca-research/task-d/td-v1.1-delta-review.md | Different fresh reviewer, actual revision attacks and later closure; request§28 |
| CREATED | D:/Project/flash-ticket-rca-research/task-d/validate_td_v1_1.py | Stdlib-only deterministic document/math checks; no method implementation/run; request§30 |
| CREATED | D:/Project/flash-ticket-rca-research/task-d/td-v1.1-validation.json | Actual results/hashes/limits from new validator; never overwrite v1.0 receipt |
| CREATED | D:/Project/flash-ticket-rca-research/task-d/td-v1.1-governance-validation.txt | Current repo governance audit output; skill audit requirement |

Intentionally unchanged (exact paths, not a claim every file in both repos was inspected):

| Path | Reason / authority |
|---|---|
| D:/Project/flash-ticket-platform/README.md | Pre-existing unowned user edit; preserve exact hash |
| D:/Project/flash-ticket-platform/AGENTS.md | Constitution remains current, not edited to accommodate design |
| D:/Project/flash-ticket-platform/docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md | User reaffirmed title/mission; no scope reduction |
| D:/Project/flash-ticket-platform/docs/evidence/advisor-direction/2026-08-22-dinh-huong-de-tai.md | Historical verbatim source; new wording must not overwrite it |
| D:/Project/flash-ticket-platform/docs/research-rca/task-c-research-decision-lock.md | C1/human role/label policy unchanged |
| D:/Project/flash-ticket-platform/docs/research-rca/task-c-independent-research-shortlist.md | Historical Phase1, current notice routes to state; not rewritten |
| D:/Project/flash-ticket-platform/docs/research-rca/task-b-dataset-capability-summary.md | TaskB facts not changed to fit design |
| D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md | CLOSED authority unchanged, no raw audit rerun |
| D:/Project/flash-ticket-rca-research/task-d/task-d-evidence-ledger.md | TD-v1.0 history preserved |
| D:/Project/flash-ticket-rca-research/task-d/task-d-exposure-ledger.md | Historical exposure/split retained; this revision adds no new outcome exposure |
| D:/Project/flash-ticket-rca-research/task-d/task-d-independent-review.md | v1.0 reviewer closure remains true of its snapshot, not rewritten |
| D:/Project/flash-ticket-rca-research/task-d/task-d-validation.json | v1.0 synthetic/document receipt preserved |
| D:/Project/flash-ticket-rca-research/task-d/task-d-governance-validation.txt | v1.0 audit preserved |
| D:/Project/flash-ticket-rca-research/task-d/validate-task-d.py | Old synthetic/document validator preserved unchanged; new version has a separate script/receipt |

All app/source/schema/API/architecture/legacy repositories, raw data and prior C/B reviewer/audit artifacts remain outside mutation scope. No commit/push/reset/stash/checkout/deletion. No C1 performance value generated in this task.

## 11. Handoff constraints

The technical artifact can be human-review-ready only after fresh delta review's D-owned CRITICAL/MAJOR issues are closed. That is distinct from **human approval**, public-extension scope selection and empirical validation. Task E is **NO / NOT AUTHORIZED** until Minh separately accepts the revised protocol and authorizes scope.

Formal-report material: graph participation before/after alert; exact common-input relation contrast; detector vs ranking/GT distinction; source chronology/DT18 clarification; M/T/L roles/missingness; nested conditional comparisons; smoothing limits; prior-work rationale; historical outcome exposure; single-root NDCG; separate public/target/explanation evidence; candid negative/failure results after actual runs.

## 12. Final gate and validation

Actual deterministic check run: **97/97 PASS**, covering document/authority/history preservation and small synthetic arithmetic only. Initial validation caught an output-receipt self-link timing issue and one trailing whitespace; both corrected before final run. No scientific result was generated.

Governance audit: **PASS, 1 warning** because P diff includes10 files (9 task-owned plus pre-existing README). The multi-file impact map was stated before edits; request§26/30 authorized the revision targets, and later explicit Minh clarification supplies the authority for the two decision-register updates. The warning is disclosed, not an unresolved scientific failure. Full tracked diff and newly created source/evidence/reviews were inspected; exact scope/HEAD preservation checked in the receipt.

| # | Required final question | Answer |
|---:|---|---|
| 1 | Is the current Task-D package now scientifically ready for Minh's human review? | **YES**, specification level REVIEW_READY; technical choices remain CANDIDATE, not human APPROVED. |
| 2 | Is C1 unchanged? | **YES**, primary inputs/windows/controls/baselines/split/inference/verdict retained; only descriptive secondary NDCG added. |
| 3 | Does the revised pipeline genuinely include graph-aware anomaly detection? | **YES by design and deterministic mathematical check**: graph changes score before threshold; real benefit NOT VERIFIED. |
| 4 | Does the revised design account for metrics, traces and logs while respecting RE2-TT limits? | **YES**: M/T occurrence/L volume, structure/evidence separated, masks/no edge join; all-used-file verification remains E/F. |
| 5 | Is the modality-ablation design scientifically interpretable? | **YES**, nested detector-evidence effects plus matched local/graph operating-policy comparison; not factorial or ranker-only effects. |
| 6 | Does it align with the quoted advisor guidance? | **YES at bounded method-specification/ownership level under RCA018–021**; no claim additional-public experiments, LLM or target work already completed. Second-public scope/release/evidence OPEN. |
| 7 | Does it align with DT18? | **YES**, full distributed-system construction/evaluation retained alongside RCA; no demo-only reduction. |
| 8 | Any unresolved CRITICAL or MAJOR issues? | **NO D-owned CRITICAL/MAJOR remains** in fresh reviewed specification. Execution evidence and scope acceptance explicitly OPEN, not silently passed. |
| 9 | What remains OPEN for E/F/G/H/I? | E: pins/licenses/env/calibration/resources/adapters; F: actual pipeline/all-used-log joins/invariance; G: frozen empirical effects; H: controlled target/arrival/healthy-workload validation and system coordination; I: model/prompt/rubric/faithfulness/usefulness. Minh: protocol acceptance/E authorization and second-public addendum/scope. |
| 10 | Is Task E authorized? | **NO.** |

Final protocol SHA-256: `9a70e64db570916b9f02fcc81fab3f4bf7cef0313f5c2de213a9eb0a8d690f3c`; independently recorded in delta-review§2.3. Final per-artifact hashes live in `td-v1.1-validation.json`. No commit or push of this revision; no Task E execution.
