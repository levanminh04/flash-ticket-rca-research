# Task E — development preflight adjudication, 27/09/2026

**RETURN TO TASK D.** Coordinator assessment, not human method approval. Confidence high that C5 cannot yet be implemented uniquely from TD-v1.2; no assessment of empirical RCA accuracy is available from this run.

This is the synthesis for all six attempts `e27-001` through `e27-006`, stored beside the first receipt. It was written after those attempts. Each attempt retains its own pre-execution contract, exact source snapshot, raw log and result JSON. Wave1 sample observations and later reviews are separately identified; they are not inputs or outputs of the first synthetic execution.

## 1. Authority, identity and actual scope

Intent EXECUTE; research work under the current DT18 mission. Minh authorized scoped development before five-agent assurance, retained formal review, prohibited final evaluation/scope changes, and approved `../preflight-plan.md` §§4–5. Canonical U27 and RCA-043–048 record those statements. The approved mission §13 requires stopping when the protocol cannot be implemented unambiguously. This stop is not a new approval requirement invented by a reviewer.

| Source | Identity |
|---|---|
| P | `D:/Project/flash-ticket-platform`, branch `codex/rca-research-program`, HEAD `3d7ec9d824d12c98dc233705ef50908b62adf235` |
| W | `D:/Project/flash-ticket-rca-research`, branch `main`, HEAD `f49859df7664758f1143a1033535da7f6f29d7d6` |
| TD-v1.2 | P `docs/research-rca/task-d-method-and-experiment-specification.md`; SHA256 `985f1c5fc983422272dfbde8b69ed5ff98ee4fdd1631af075d03788c3770ad54`; unchanged |
| RE2-TT | revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`; exact development30 in W `configs/task-e-td12-development.json` |
| Runtime | Existing W Python3.12.10 environment; package versions/hardware in each contract and environment lock; no package installation |
| Exposure | Synthetic execution only; Wave1 inspected two already-local development cases; prior E1 exposure remains disclosed in D exposure ledger |

No development predictions, detector training, smoke campaign, empirical selection/sensitivity, final outcomes, RE3 campaign or FlashTicket integration were run. No new telemetry was downloaded. Twenty small original upstream source files and one patched copy were stored for comparator inspection. There was no commit or push.

## 2. What broke and how it was classified

**D-E27-01 — C5 applicable-neighbor membership (OPEN, high confidence).** TD §7 specifies a “frozen same-type applicable degree” but does not define whether membership requires a scaler computable from the fit prefix, enough rows for the neighbor's own target model, or another predicate. These concepts differ under missingness. In the executable synthetic counterexample, two neighbor channels have 24/12 finite prefix bins but 23/0 valid lag1 pairs. Both can have prefix median/IQR; only the first meets the own-model minimum18. At the next input, the first is unavailable and the second has standardized value10. Scaler-based membership gives mean10, coverage0.5, degree2; own-target-fit membership gives mean0, coverage0, degree1. Same data and graph, different G/ALL predictors. Neither interpretation was adopted. No detector was fitted and no difference in measured F1 or real-data prevalence is claimed.

**D-E27-02 — C5 encountered-conflict scope (OPEN, moderate–high confidence).** TD §7 says streaming conflicts invalidate the encountered bin from the cutoff. It does not specify the affected service/channel mask, graph-fit consequences or persistence into later state. The difference from C1's shared input failure is not itself a contradiction: they are different modes. The `C5-CONFLICT` dictionaries are a static illustration with manually stated mask alternatives, not outputs from two implemented loaders. The two inspected trace samples did not contain conflicting keys. A chronological policy must be specified before claiming C5 replay qualification.

**Implementation corrections, not D amendments:**

- Input loader now rejects nondevelopment paths and mismatched bytes before Parquet access; optional bad log support cannot veto C1 M/T. These were corrected before the initial boundary suite.
- Available-modality mean uses a max-first calculation to avoid overflowing a sum of finite large nonnegative scores. This is a defensive code correction, not an observed empirical failure.
- Independent review identified decimal-rounding overflow: `np.round([1e308,1e307],12)` becomes nonfinite, manufacturing a tie from distinct finite comparator scores. Magnitude-safe Python scalar rounding preserves TD's twelve-decimal tie rule. Huge unequal scores, genuine huge ties and ordinary near-tie boundaries now pass analytic regressions.
- C1 bundle construction no longer lets finite fractional clocks clearly outside its reference/query union veto selected inputs. Inside-window fractional and unplaceable clocks remain explicit failures; log failure remains support-only. This qualifies the tested bundle path, not every physical-schema/archive admission path. C5 remains explicitly unqualified.

**TEST-E27-01 — failed test assertion, preserved.** Attempt004 required more than one distinct final graph from four random chains. TD does not guarantee that: accepted switches can still end at the same graph. The correction injects one known legal diamond switch followed by three shared-endpoint rejections and checks the exact analytic adjacency and counts, in directed and undirected modes. A separate test checks rejection and rollback of a switch that splits a component. Ranking source bytes were unchanged across003/004/005. This correction was independently read-reviewed; the failed004 report/log/source remain intact. It was not a change to TD expected output to force a pass.

Missing84 telemetry files and the unqualified RCD dependency environment are execution dependencies, not proof of data incompatibility. The C5 ambiguities are sufficient for the mission's return rule. They do not prove C1 unusable; the complete campaign is held while the common protocol is clarified.

## 3. What survived: exact execution receipts

Paths below are relative to `W/results/task-e/`. Repeated tests are not counted as additional independent evidence.

| Attempt | Actual result | Scope |
|---|---|---|
| `e27-001-synthetic` | 18/18 PASS | Initial bounded local/PPR/diffusion/R/evaluator/BARO and RCD-stub checks; C5 applicability counterexample |
| `e27-002-boundary` | 9/9 PASS | Synthetic DataFrames and mocked path/hash checks |
| `e27-003-math-fix` | 19/19 PASS | Added large-comparator-score tie regression after evaluator correction |
| `e27-004-math-review` | 21 tests, 1 failure | Overstrong stochastic endpoint-uniqueness assertion; preserved |
| `e27-005-math-closure` | **21/21 PASS** | Current math source; exact accepted switch, rejection/rollback and safe ties |
| `e27-006-boundary-closure` | **13/13 PASS** | Current C1 bundle source; outside/inside-window and unplaceable-clock regressions |

The latest suites support their explicit cases: analytic two-node PPR and diffusion, zero evidence, mass conservation, chain/star/isolate/index permutation, available-modality fusion, ties/Hit/RR/NDCG, planned denominator rejection of missing entries, structural-switch invariants, BARO downshift/spike behavior, and RCD interface exception-versus-empty-output semantics. RCD used stub callables. They do not qualify full256 per-draw metric aggregation, bootstrap/fold selection, randomization mixing on real graphs, complete C5 forecasting/threshold/event fixtures, worker/cache isolation or full actual-used loader behavior.

See each directory's `fixture-report.json` or `leakage-audit.json`, `execution.log`, `run-contract.json` and `source-manifest.json`. `resources.json` consolidates measured suite durations; full30 peak memory and runtime remain unmeasured. No performance claim follows from subsecond unit-suite timings.

## 4. Actual development-data observations, not RCA results

[loader-audit.json](loader-audit.json) preserves Wave1 reviewer observations and five coordinator-verified file hashes. Only `re2tt_ts-auth-service_cpu_1` M/T and `re2tt_ts-auth-service_cpu_2` M/L/T were available: 5/89 expected telemetry objects, 2/30 cases. No attempt to certify the other28 cases was made. Missing28 traces total501,871,707bytes in the existing inventory; sizes of missing metrics/logs were not verified.

Both sample C1 reference graphs have27 nodes and55 directed edges; selected parent resolution was241,395/241,395 and169,196/169,196. Exact mapped metric channels were202/369 and200/367; eligible C1 metric channels were202 and192. Unmatched names were not silently mapped. Cpu2 logs contain271,919 rows,16 null messages and1,052 exact duplicate rows that remain counted;20/27 trace services had first120s log support. Cpu1 log absence is declared by the pinned metadata, not a download failure.

These facts support “the two samples contain graph and telemetry structure.” They do not establish local informativeness, root-ranking accuracy, C5 calibration, graph benefit or corpus-wide missingness bias. The sample audit preceded implementation and is not a full30 actual-use audit of the current loader.

## 5. Mandatory falsification questions

| Question | Evidence | Verdict | Confidence |
|---|---|---|---|
| 1. Local evidence informative or degenerate? | Analytic deviation fixtures only; no actual case scores | OPEN; not measured | High about this limit |
| 2. Enough observed graph structure? | Two actual reference graphs27 nodes/55edges | Structure exists in these samples; sufficiency across30 OPEN | High sample facts; low generalization |
| 3. Does O differ from L? | Synthetic directed two-node/chain/star cases | Operator can change computation; empirical relevance OPEN | High fixture result |
| 4. O versus R stable or Monte Carlo noise? | Bounded switch fixtures, not outcome aggregation | NOT RUN | High about this limit |
| 5. Few cases dominate delta? | No actual deltas | NOT RUN | High about this limit |
| 6. Local-only near ceiling? | No actual rankings | NOT RUN | High about this limit |
| 7. C5 gain from graph or active capacity? | Same missing prefix permits different context definitions | Cannot yet test uniquely; RETURN D | High ambiguity evidence |
| 8. Detector availability sufficient? | Two input-prefix observations, no fitted detectors | NOT RUN; input eligibility is not model availability | High about this limit |
| 9. Prefix/residual scale stable? | No trained residual/calibration series | NOT RUN | High about this limit |
| 10. Missingness systematic bias? | Unequal sample channels/log support; synthetic membership example | Risk visible, bias/prevalence unmeasured | Moderate risk; no effect estimate |
| 11. Leakage signs? | Bounded13 boundary tests and static review; over-broad C1 clock veto corrected | Partial boundary support only; C5/cache/process qualification OPEN | High bounded result |
| 12. Baseline fidelity sufficient? |20pinned sources, exact patch, BARO fixture, RCD stubs | Source alignment supported; real RCD NOT QUALIFIED | High source identity; runtime OPEN |
| 13. D assumption refuted by actual data? | Two samples; no model experiment | No measured falsification of graph/RCA accuracy; code exposes D underspecification | High distinction |
| 14. Must return D before F/freeze? | D-E27-01 and02, independently reviewed | **YES**, narrow clarification | High / moderate–high |

## 6. Required D clarification, not applied

1. Define the prefix-only membership/scaler predicate for each neighbor channel, distinct from own-target fit/calibration eligibility and per-bin availability. State the frozen denominator and identical application to G/ALL and MT/MTL. Any new minimum or policy is explicit, reviewed and chosen before outcomes, not hidden in code or selected by measured benefit.
2. Define chronological handling of a conflicting trace key: which channels/services/bins are masked, effects while forming the prefix graph, handling after it is frozen, persistence/recovery and audit recording. A future conflict must not retroactively alter past decisions. Do not silently invent event arrival truth from archive row order.

Both remain OPEN for Minh and the D method owner/reviewer. The coordinator has not amended TD or approved either interpretation. No new feature/operator, scope reduction, dataset switch or C1 redesign is proposed by this evidence.

## 7. Review and next authorized step

[review.json](review.json) names actual agents and roles. Wave1 involved three identities with multiple roles; two fresh agents reviewed code/snapshots/logs/source pins. They inherited context and the proposed verdict, so this was not blind reproduction. One fresh reviewer later authored the narrow C1 fix and is not independent for that delta; the other reviewed its closure. These reviews do not automatically satisfy historical five-independent D assurance.

Next: obtain a narrow D clarification/amendment under its gate, snapshot the resulting protocol, then resume the already-authorized E stages. Finish complete synthetic C5/aggregation/firewall checks; qualify RCD's pinned custom dependencies; acquire only missing development objects and audit all89 before any real model run; check actual reference-graph mobility before outcome interpretation; perform the predetermined smoke and, if its gates pass, full30 registry plus mandatory OFAT sensitivity. Keep all failed cases/draws. A failure may still be a valid result; no graph-win requirement.

E remains incomplete for scientific PASS. No F/G/H/I or final freeze is opened. DT18 still requires the distributed ticket system and its own performance, consistency and transaction-stability evaluation alongside graph-based monitoring/diagnosis. Report-facing material from this checkpoint is reproducibility, exact failure attribution, scope of synthetic evidence and unresolved C5 definitions—not measured RCA effectiveness.

## 8. Files and handoff

Canonical source/decisions were recorded before execution. The current handoff/state/map are updated only after these evidence files exist. `file-inventory.json` records every task-created/modified file with bytes/hash/purpose, excluding the pre-existing P README change and generated Python caches. Git heads, TD bytes and that README hash are preserved in final validation. Full task changes are local and uncommitted.

W implementation: six modules `contract.py`, `acquire.py`, `loader.py`, `ranking.py`, `evaluator.py`, `comparators.py`; two test files; development config; existing-environment lock; baseline source manifest/patch/snapshots; scoped `.gitignore`; preflight plan and six preserved run receipts. `detection.py` and `run_preflight.py` were deliberately not created after the protocol stop; there is no completed end-to-end campaign runner. No empty predictions/sensitivity files are supplied as apparent results.
