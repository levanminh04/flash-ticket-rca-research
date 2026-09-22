# Task C — Evidence ledger

- Date: 2026-09-20. Intent: EXECUTE; artifact class: FORMATION; decisions: CANDIDATE/OPEN only.
- Authority: current Task-C request; Task A for literature; closed Task B §12 for reconciled dataset facts; persisted machine results prevail over prose. Task B §§1–11 and pre-close snapshot are historical.
- Provenance inventory: [task-c-input-inventory.json](task-c-input-inventory.json), SHA-256/bytes of input reports, evidence and audit scripts. No input evidence is edited.
- Claim classes below are evidence annotations, not new project decision states: VERIFIED classes map to FACT; reviewer/Task-C inferences map to CANDIDATE; OPEN remains OPEN. User's execution/scope requirements are USER_CONFIRMED, not approval of a direction.

## Source keys

- A = D:/Project/flash-ticket-platform/docs/research-rca/task-a-ban-do-bang-chung-doc-lap.md (DRAFT, source cutoff 2026-09-20); read complete, including C.2–C.12, J–Q.
- B = D:/Project/flash-ticket-rca-research/dataset-audit/TASK-B-RCAEval-audit.md (CLOSED); read complete; §12 authoritative over preserved older statements.
- R directory = D:/Project/flash-ticket-rca-research/audits/rcaeval; all 11 required reviewer reports read: A/B/C/D/E/F/G/H/I/J/resource. Their scope/date limits remain binding.
- Governance read: root AGENTS.md, govern-capstone-work SKILL.md and project-authority-and-gates.md, docs/quy-trinh-lam-viec.md, DT18 mission, roles, R0 and lien-ket-rca. R0/linked prior method proposals are not sources for candidate discovery; only governance/current mission apply.
- Required raw-sample-plan.md, resume state, persisted manifest verification, B2B manifest and machine inventory inspected. Pre-close snapshot is inventoried; B §§1–11 preserve its substantive history.

## Evidence statements

| ID | Claim | Source / section or JSON path | Evidence class | Scope | Limitations |
|---|---|---|---|---|---|
| A-001 | Detection, affected components, RCA rank, causal validation and language explanation are different tasks | A B.1/B.2/D/J | VERIFIED — TASK A | 11 mapped methods | Method name does not establish task coverage |
| A-002 | Graph serves topology, feature context, anomaly object, propagation, conditional reasoning or ranking | A D/E/F | VERIFIED — TASK A | Mapped pipelines | Graph at ranker alone does not prove graph-conditioned detection |
| A-003 | Multimodal graph AD/RCA already exists | A C.7/C.8/C.12/G | VERIFIED — TASK A | Eadro/TORAI/ARMOR; DeepTraLog trace+log | No novelty from three modalities alone |
| A-004 | Missing modalities and random edge removal have prior evaluations | A H; C.8/C.9/C.12 | VERIFIED — TASK A | TORAI/DéjàVu/ARMOR | Does not establish real missingness mechanism or reconstruction |
| A-005 | Graph ablations and finer representations already have precedents | A C.7/C.9/I/L | VERIFIED — TASK A | Specific paper setups | Repeating an ablation is not automatically a gap |
| A-006 | No gap established as STRONG CANDIDATE | A L/Q | VERIFIED — TASK A | Bounded 11-method evidence pack | Absence from survey is not literature-wide absence |
| A-007 | Service-root rank supports MRR/Hit@k; node F1 needs same-unit anomaly labels | A J | VERIFIED — TASK A | Metric definitions | Single-root NDCG is a rank transform, not severity |
| A-008 | Baseline inputs, supervision, output units differ | A C/F | VERIFIED — TASK A | BARO/RCD/CIRCA/Eadro/MicroRank etc. | Adapting an operation ranker to service is an adaptation, not exact reproduction |
| A-009 | MicroRank paper/code detector mismatch remains UNVERIFIED; some calibration/runtime details unknown | A C.3/C.4/C.7/F | VERIFIED — TASK A | Named implementation details | Does not block problem-level questions unless they depend on that exact detail |
| B-001 | Task B closed, capability decision only | B header; §12.20 | VERIFIED — TASK B | Pinned RCAEval | Does not choose a final dataset or method |
| M-001 | 90 RE2-TT cases = 5 root services × 6 faults × 3 repeats; 90 valid published windows, 720/721 timesteps | subagent-i-re2tt-groundtruth.json: re2tt_metadata_facts | VERIFIED — MACHINE EVIDENCE | Full RE2-TT metadata | Injection regime is not independently observed anomaly onset; repetitions need dependence controls |
| M-002 | Metrics/traces 90 each, logs 89; no extra operation/resource/indicator target artifact | subagent-i-re2tt-groundtruth.json: official_repository_tree, ground_truth_availability | VERIFIED — MACHINE EVIDENCE | Full pinned RE2-TT tree/metadata | File presence does not establish whole-population log/metric schema |
| M-003 | 90 traces, 67,345,051 rows, one 11-field schema, 27 literal services, 161 literal service-operation pairs | re2tt-trace-full-subset-audit.json: summary | VERIFIED — MACHINE EVIDENCE | Full RE2-TT trace subset | Per-case/cutoff graph smaller than union; union is audit statistic, not permissible test graph |
| M-004 | 65,748,095 of 66,781,374 parent references resolve (98.45274372%); 7 cases <90%, minimum 38.54287289% | same JSON: summary.parent_resolution, parent_resolution_case_profile | VERIFIED — MACHINE EVIDENCE | Full RE2-TT trace subset | Parent resolution is not complete topology recall; missingness cause not identified |
| M-005 | All 90 target labels occur in their full-case trace candidate sets; sizes 20–27 | re2tt-target-candidate-coverage.json | VERIFIED — MACHINE EVIDENCE | Full-case RE2-TT | Not a guarantee for any shorter prefix or pre-incident-only graph |
| M-006 | 55 observed cross-service relation types; no duplicate within-case trace/span keys; semantic resource/protocol fields absent | re2tt-trace-full-subset-audit.json: summary | VERIFIED — MACHINE EVIDENCE | Full trace subset | No CALLS/USES/messaging/causal labels inferred |
| B-002 | Service root ranking and known-window RCA evaluable; operation/resource/affected-node/path targets absent | B §12.9/12.12/12.17 | VERIFIED — TASK B | Pinned RE2-TT | No service/node anomaly F1 |
| B-003 | Literal service-operation representation supported, semantic operation type and operation GT unsupported | B §12.7 | VERIFIED — TASK B | RE2-TT | Internal representation may still be evaluated against service targets |
| B-004 | Graph from resolved same-trace parent references only; retain low-coverage cases | B §12.7/12.11/12.15 | VERIFIED — TASK B | RE2-TT | No architectural completion or silent repairs |
| R-001 | Wide metrics expose entity suffix tokens, some null/zero series; trace method/status all-null in two original TT samples | R subagent-d-metrics.md; subagent-b-trace-schema.md | VERIFIED — TASK B | Six metric/three trace samples | Do not promote sample null profile to whole RE2-TT; no typed resource inference |
| R-002 | L–M exact service/container-second bins; M–T/L–T service+time only | R E/H; B §12.5/12.13 | VERIFIED — TASK B | Four original log samples plus one B2B TT case | No event/request correlation; unmatched names stay unmatched |
| M-007 | B2B 271,919/271,919 logs have exact L–M bin match; zero log trace/span ID matches | subagent-h-red-team-evidence.json: b2b_re2tt_normal_log_case_evidence | VERIFIED — MACHINE EVIDENCE | re2tt_ts-auth-service_cpu_2 only | “Normal log-bearing case” means ordinary case with logs, NOT a healthy-only control |
| B-005 | Path/case labels forbidden; root/fault evaluation-only; inject_time only external known-window boundary | B §12.10 | VERIFIED — TASK B | All pilot protocols | End-to-end input must not use inject_time or fixed midpoint shortcut |
| B-006 | Resource graph not supported | B §12.8, resource reviewer | VERIFIED — TASK B | Pilot resources | Text prefixes remain raw labels, not typed DB/cache/host nodes |
| M-008 | Source revision afeacb11bcc94dadfd1c8f483ee4377b2b8b614e; original 20 files verified; B2B 3 hashes match official LFS | raw-manifest-verification.json; b2b manifest | VERIFIED — MACHINE EVIDENCE | Persisted Task-B checks | Task C reads records; does not claim a fresh full raw rehash |
| M-009 | B2 processed remote traces with ranges and retained no new trace corpus | full-trace JSON: summary.transfer; B §12.2 | VERIFIED — MACHINE EVIDENCE | 89 remote plus 1 reused local object | A 90-case experiment will need authorized pinned retrieval later; audit JSON is not model-ready telemetry |
| B-007 | Two RE1 published windows invalid; 0/90 RE2-TT metadata out-of-window | B §12.4; metadata-invariants.json; I JSON | VERIFIED — MACHINE EVIDENCE | Metadata; one RE1 raw-confirmed | No silent correction |
| R-003 | Restricting ranking to five injected targets is leaky/trivial Top-5 | R I/H; B §12.13 | VERIFIED — TASK B | Candidate-universe policy | Same telemetry-derived universe for all comparators |
| T-001 | 90 cases, not 67M independent experimental replications | M-001/M-003 plus study design | TASK-C INFERENCE | Proposed statistics | Clustering by scenario/repeat and temporal dependence must be addressed |
| T-002 | All fixed injection offsets create a schedule shortcut for a putative detector | M-001 plus B-005 | TASK-C INFERENCE | RE2-TT detection claims | Window P/R/F1 measures injection-regime agreement only; no production false-alarm claim |
| P-001 | Current title/mission is DT18; public experiments then FlashTicket application/evaluation; log/trace/metrics mapped to graph | docs/evidence/project-direction/2026-09-18-de-tai-va-nhiem-vu.md | PRIMARY-SOURCE FACT | User-confirmed current mission | Not evidence of runtime completion or supervisor approval of a specific method |
| P-002 | Four team members; Minh chiefly owns RCA and shared infrastructure | docs/project/roles.md | PRIMARY-SOURCE FACT | Current assignment | Four people do not imply four full-time RCA researchers |
| P-003 | Five-stage guidance interpreted under current Task-C request §5; examples are not mandatory algorithms/metrics | User Task-C §5; A M | PRIMARY-SOURCE FACT | Current task constraints | Historical email never overrides DT18 title/mission |
| O-001 | Novelty not established; final choice, effect-size relevance, resource budget and validation ambition are undecided | A-006, current request | OPEN | Human decision C Phase 2 / method Task D | No auto-selection or weighted winner |

## Post-discovery source corrections — 2026-09-21

These additions preserve the original A/B sources and reviewer submissions. They govern Task-C interpretation where shorthand was too strong.

| ID | Claim | Source | Evidence class | Scope / implication |
|---|---|---|---|---|
| TV-001 | Eadro already ablates graph aggregation and modalities | targeted-verification TV-01, original §V-G | PRIMARY-SOURCE FACT | Generic graph benefit is not an unstudied question |
| TV-002 | DejaVu studies previously unseen faulty failure units | targeted-verification TV-02, original §5.5 | PRIMARY-SOURCE FACT | Scenario grouping is validity, not novelty by itself |
| TV-003 | BARO varies assumed anomaly boundary; this differs from censoring available data at fixed boundary | targeted-verification TV-03, original §4.8 | PRIMARY-SOURCE FACT for experiment; TASK-C INFERENCE for contrast | C2 is retrospective matched-cutoff inquiry only |
| TV-004 | MicroRank varies trace count and graph weights, reports component costs; five-minute window flushing does not establish a mandatory post-alert wait | targeted-verification TV-04, official PDF SHA recorded | PRIMARY-SOURCE FACT | Supersedes stronger timing shorthand in A/reviewers for Task C, without editing those sources |
| EC-007 | B §12.10 does not authorize training on root labels | evidence-cross-review EC-07, B line371 | VERIFIED — TASK B | No supervised training exception inferred from label availability or separate result table |
| EC-009 | Historical letter names AI explanation, not LLM or named algorithm/metric examples | evidence-cross-review EC-09; original historical letter §1; Task C §5 | PRIMARY-SOURCE FACT | Current request supplies LLM/examples; DT18 remains current mission. Tightens P-003 provenance, not scope. |

## Reconciliation completed before discovery

Lightweight arithmetic check: [task-c-machine-evidence-check.json](task-c-machine-evidence-check.json). PowerShell parsed persisted JSON, summed `cases.parquet.rows` and `cases.parent_resolution.resolved_same_trace/unresolved_same_trace`, counted per-case resolution <0.9, counted true `root_target_present_in_telemetry_candidate_set`, and took min/max candidate counts. All reported totals match. Metadata hash was freshly calculated and matched Task B. This is not a new dataset audit; no raw telemetry was rescanned, no download or installation occurred.

1. Historical D/F blanket inject-time ban narrows under B §12.10: allowed only as declared external known-incident boundary; forbidden detector input.
2. Historical time-only L–M wording contradicted by E/H raw bin checks. Direct is bin-specific only.
3. Sample parent rates are superseded in scope by full B2 rates; low-resolution cases are retained.
4. Literature service counts (e.g. 64 TT) cannot overwrite 27 trace literals or 20–27 per-case candidate sets in this snapshot.
5. Operation/indicator language in papers does not create missing pinned-release labels.
6. No material evidence conflict remains unresolved at Phase 0. Feasibility unknowns such as future baseline runtime are labeled OPEN, not dataset defects.

## Anti-anchoring execution

Main agent necessarily saw the earlier conversation and has read governance documents referencing historical proposals. It cannot claim a clean slate. Candidate generation is therefore delegated to six fresh-context reviewers (fork_turns=none), who receive only authoritative inputs, current constraints, and a distinct lens; no prior chat proposal or another reviewer's candidates. Two waves of three use the four available concurrent slots. Main will not merge before all six submit. Independent interpretation does not mean independent raw data: reviewers share the same A/B evidence.

## Authorized impact map

New authoritative Phase-1 synthesis: D:/Project/flash-ticket-platform/docs/research-rca/task-c-independent-research-shortlist.md, DRAFT for human choice. Supporting original reviewer outputs, ledger, normalization, gates, red-team and resume records live under the user-specified research `task-c/` directory. No durable research choice is promoted; no system requirement is created. A/B, reviewer evidence, raw manifests, telemetry, application code, B16, existing indexes/README/source register remain unchanged. Validation: verify citations and evidence scope, reconcile objections against machine evidence, check coverage of all requested fields, source hashes unchanged, review complete new-file content and run the repository governance audit. This exact deliverable scope was authorized in the current Task-C request; no duplicate approval is needed.
