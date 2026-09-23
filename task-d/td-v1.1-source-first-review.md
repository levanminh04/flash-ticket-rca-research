# TD-v1.1 — Independent source-first review

## FIRST PASS — preserved independent opinion

- Review date: 2026-09-23. Reviewer: `td11_source_first`.
- Intent: `REVIEW`, with an explicitly authorized single review artifact; artifact class `FORMATION`. No method approval, execution authorization, baseline execution, data download, model run, installation, application change, commit or push.
- Input snapshots personally checked: `P= D:/Project/flash-ticket-platform`, HEAD `6bd04e625926e923301cc6bb1433682f01fd87fc`; `W= D:/Project/flash-ticket-rca-research`, HEAD `c7e47fdcc69c53876f7bd3f1a5e71ef89c59ccf6`. P had an existing dirty `README.md`; W was clean. That change is not owned by this review.
- Independence: this pass was written before receiving the main reviewer's proposed fixes. I did not read the user's complete attachment or root's prior conversation. I read the current protocol because that is the object under review; its references to earlier reviews do not establish correctness by consensus. No earlier Task-D reviewer report or main candidate list was used to form these findings.
- Status: review findings are `CANDIDATE` interpretations unless explicitly identified as source observations (`FACT`) or unresolved authority questions (`OPEN`). Nothing here changes RCA-001–017 or makes a technical option `USER_CONFIRMED`/`DECIDED`.

## 1. Sources actually used

Personally read P `AGENTS.md`, `.agents/skills/govern-capstone-work/SKILL.md`, its complete `references/project-authority-and-gates.md`, DT18 title/mission, roles, the original 22/08 advisor letter, RCA-001–017, all of C Phase 2 decision lock, MASTER program, current entire TD-v1.0, D handoff, CURRENT-STATE, Task-B capability digest and Task B CLOSED §12.1–12.20. The system master workflow was read for the project/authority boundary. Supporting Task-A sections inspected on demand: I §§1–10; C.1–C.11 and especially MicroRCA/MicroRank/BARO/TORAI/DeepTraLog/GDN mechanisms; G–K; M source notice and table. Supporting Task-C Phase-1 §§4–5 were read to distinguish the restricted C1 claim from full-program completeness. This is not a new survey, dataset audit, reproduction or verification of external papers.

The additional advisor guidance was supplied verbatim to this reviewer by Minh through the current task. **Original send date and original channel are NOT VERIFIED.** Its content includes: method research first; construct dependency graphs; graph-based anomaly detection mapping log/trace to graph (examples PageRank anomaly/subgraph/GNN); experiments on public datasets including Train Ticket, Sock Shop, LEMMA-RCA; comparisons and P/R/F1/MRR/NDCG; downstream LLM explanations; an explicit request to understand methods more deeply and extend experiments to other public datasets. It also says the product can reuse the old system and only needs to demonstrate incident-related features. The observation that this text was supplied now is a `FACT`; its chronology relative to DT18 and authority to supersede DT18 are `OPEN`. It must not be attributed to the archived 22/08 email: that email's exact text lacks the algorithm examples and this exact metric list.

## 2. Independent verdict

**TD-v1.0 is a careful specification of one narrow, testable C1 experiment, but it is not yet a reconciled specification of the complete method program described by the newly supplied guidance.** The strongest problem is not that C1 is invalid, that a negative result is unacceptable, or that the study must invent a GNN. It is that a defensible within-method graph-ranking contrast is being used as the center of a program whose graph-anomaly capability and broader public validation still have no explicit accepted disposition.

There is no source-based reason here to discard C1 or to change the locked acceptance of empirical/system/reproducibility contributions and valid negative results. The current technical choices are still `CANDIDATE`; D can be revised within that authority to correct gaps, rationale, boundaries and technical contracts. A new advisor-facing scope commitment or a change to the system mission must not be hidden in that revision.

## 3. Strongest aspects to preserve

1. **Honest task and evidence boundaries.** D §§1–4/10, C lock §§3–5 and B §12 distinguish known-window ranking, injection-regime detection, service-root labels, operation evidence and causal claims. They explicitly avoid equating PageRank-style propagation with a graph detector. This is scientifically useful, not needless caution.
2. **C1 controls are stronger than graph ON/OFF.** Shared local evidence/candidate sets, identity/observed/degree-and-component-preserving structural controls, fixed capacity, and explicit unpreserved nuisances make the proposed contrast interpretable. D §5 does not pretend rewiring identifies causal truth or uniform graph randomness.
3. **Leakage and exposure are handled unusually well.** D §§2–3 separates evaluator metadata from model inputs and acknowledges historical TT outcome exposure. The 30/60 split is a prospective new contrast on a studied benchmark, not retroactively pristine holdout data. Root labels remain evaluation-only, as locked.
4. **Negative and missing outcomes remain visible.** D §§7–8 keeps planned denominators, ties, missing targets, graph isolates, failed chains, failure-inclusive operational utility and negative/inconclusive/invalid distinctions. A local ceiling is not automatically an excuse to avoid a negative result.
5. **Full-method comparison is separated from attribution.** D §6 recognizes that O versus BARO with unequal modalities cannot measure pure relation effect. BARO is labeled as an adapted ranking component; original supervised baselines are not quietly trained in violation of C.
6. **LLM and transfer boundaries are sound.** D §§11–12 preserves rank and structured evidence, separates faithfulness from diagnosis correctness, and leaves application integration to H and the system gates. C3/C4 are explicitly discussed rather than silently erased.
7. **The existing survey is not merely a list of method names.** The inspected Task-A mechanism sections describe detector, graph, ranker, supervision, input/label needs and limitations. The newly supplied criticism of a previous report should not be misrepresented as evidence that the current Task-A survey contains no technical depth. What is missing is a clear bridge from that depth to the chosen D mechanism and its testable limitations.

## 4. Findings and ownership

### SF-01 — MAJOR / authority: the product-scope statements are not reconciled

- **FACT sources:** DT18 §2 paragraph 1 directly requires building the distributed ticketing system and measuring throughput, response time, errors, scalability, consistency and transaction stability. P AGENTS, “Đề tài và ranh giới hai bộ tài liệu” item 2 explicitly says not to write that the system only needs to run. The newly supplied text says “sản phẩm hệ thống chỉ cần tập trung demo những tính năng liên quan tới phát hiện sự cố.”
- **OPEN:** whether this is newer advice superseding the confirmed DT18 mission, a comment on prioritization/prototype scope, or advice from an earlier stage. Original chronology is not established. Research-first timing itself is compatible with independent D–G progress and need not be manufactured into a conflict; reducing the system deliverable/evaluation is the material conflict.
- **Impact:** claims about overall thesis scope, reuse, H exit and final report. It does not invalidate the frozen C1 question or justify reopening service architecture.
- **Owner/timing:** Minh, before adopting a new overall product/assessment scope; advisor confirmation if Minh needs it. D may record the exact conflict and retain DT18 duties. Do not resolve it by silently declaring “demo only” or by claiming the new text is the 22/08 email.

### SF-02 — MAJOR / capability: graph-based anomaly detection is absent from the specified detector

- **FACT sources:** D §10 explicitly says metric bins only and “detector không được gọi graph-based”; §5 puts graph only in late ranking. Task A I §§2/4, C.2–3 and C.10–11 distinguish graph-ranked RCA from graph-dependent anomaly scoring. The newly supplied step 2 explicitly asks for graph-based anomaly detection.
- **Finding (`CANDIDATE` interpretation):** current D meets detection→graph RCA as a pipeline, but does not meet a strict reading in which graph contributes to anomaly score/decision or the graph object is scored. Calling the whole pipeline graph-based does not close this capability gap.
- **Crucial boundary:** B §12.12 rules out node/service anomaly F1, not all graph-dependent system-level detection. The same bounded injection-regime labels already used in D §10 do not by themselves forbid graph-dependent detection. Conversely, they cannot validate production onset/FPR or node correctness after adding a graph.
- **Owner/timing:** D/Minh reconciliation before accepting the whole method baseline; exact implementation/evaluation remains E/F/G as authorized. Preserve C1 and C5 mandatory status. The source does not mandate PageRank, a subgraph algorithm and a GNN all together, nor a new algorithm. Whether a separate graph-dependent capability is adopted or the broad interpretation is explicitly accepted must be visible; this reviewer does not select a mechanism.

### SF-03 — MAJOR / experimental program: additional public-dataset validation has no owned path

- **FACT sources:** C Phase 1 §4.10 permits a narrow RE2-TT-only claim; RCA-001 fixes that primary RQ. MASTER §2 and D §§2–3/12–14 specify RE2-TT then FlashTicket. The newly supplied final paragraph explicitly asks to expand experiments to other public datasets.
- **Finding:** another private/target system is not itself another public dataset. The validity of the narrow C1 result and completeness of the advisor-facing public-validation program are different questions. The existing restricted claim does not answer the new expansion request.
- **OPEN:** number, release, target, compatibility and role of additional public datasets; these examples are applications/dataset families rather than automatically compatible releases. Task A K and B §12 support that distinction. Do not assume a Sock Shop release has traces or LEMMA has the same graph/GT fields.
- **Owner/timing:** Minh owns any new scope commitment; D/Master can expose the selection/acceptance gate and evidence needed without selecting a release blindly. Must be resolved before declaring the public research program complete, not necessarily before a bounded RE2-TT first pilot. C1 need not be changed: external validation can be a separate declared phase, with domain/telemetry mismatches reported rather than repaired from labels.

### SF-04 — MAJOR for advisor-facing claims, MODERATE for narrow C1 / scientific rationale

- **FACT sources:** D §§4–6 chooses robust metric/trace-count deviations, a fixed half-weight fusion, symmetric binary reference topology and restart smoothing at alpha .5; only Local-MAX and BARO ranking adaptation run as external-context alternatives. Task A C.2–11 contains substantially richer detector/ranker mechanisms and known limitations. D honestly limits the result to this mechanism.
- **Finding:** the protocol is executable in detail but lacks a compact technical chain showing which concrete limitation of existing RCA methods motivates these particular choices and what observation would teach the reader about that limitation. “Do not add a confound” explains the clean contrast, but does not by itself explain why this local representation and smoothing policy are a scientifically useful probe. An engineering simplicity argument is permissible; it must be labeled as such rather than sold as an untested improvement over prior work.
- **Not a finding of invalidity:** a controlled one-mechanism C1 experiment can stand without SOTA superiority, mandatory deep learning or a new graph algorithm. No source establishes that the current method cannot work. The absence of an external runnable graph method limits contextual comparison; it does not remove the internal structural comparator.
- **Owner/timing:** D before approval should connect mechanisms/limitations/claims and explicitly bound the baseline package. E validates fidelity. Broader baselines or a redesigned mechanism are choices to justify, not an automatic response to a reviewer preference.

### SF-05 — MODERATE / graph interpretation: causal uncertainty does not imply that observed direction is unusable

- **FACT sources:** B §12.7 supports observed parent→child direction but not causal propagation. D §5 says it symmetrizes because parent identity does not establish causal direction.
- **Finding:** symmetrizing is an allowed `CANDIDATE` choice, but the stated rationale skips a distinction. Observed directed relation can be used as observed direction without asserting causal direction. Dropping direction therefore changes the estimand and may discard useful structure; it is not compelled by B.
- **Owner/timing:** D rationale/claim boundary before approval. Record undirected adjacency as deliberate scope/simplicity choice and its directional limitation. This does not require adding a direction sweep or selecting a reverse-flow design; do not choose a variant after seeing performance.

### SF-06 — MODERATE / metric disposition: NDCG is left ambiguous rather than explicitly reconciled

- **FACT sources:** new guidance lists P/R/F1/MRR/NDCG. D §7 chooses MRR plus Hit@k and says NDCG is not primary, but gives no NDCG output contract or explicit omission rationale. D §10 correctly supplies bounded system-bin P/R/F1. Task A J.1 explains valid one-root NDCG and its limited meaning.
- **Finding:** keeping one primary endpoint is correct; an advisor's list does not mean all metrics must become primary or use false node labels. It does require an explicit disposition. Single-root NDCG is computable from the existing ranked output and does not measure severity. If reported, tie/miss/failure/k/gain/normalization must be stated; if omitted, say why and who accepted that interpretation.
- **Owner/timing:** D before freeze. This can be reconciled as a descriptive ranking metric or an explicit rationale without changing C1, training, dataset or primary-hypothesis family. Do not relabel Hit@k as binary anomaly precision.

### SF-07 — MODERATE / capability precision: mapped logs and operation counts are evidence, not demonstrated anomaly-localization capability

- **FACT sources:** D §4.2 maps log counts and randomly selected-by-hash excerpts, and supports top operation count changes. Neither log nor operation evidence enters core rank; §10 is metric-only. §11 calls scores suspicion utility and preserves evidence/limits. DT18-NV2 and new step 2 mention mapping operational data onto the graph for anomaly/diagnostic work.
- **Finding:** current D supplies concrete multimodal mapping and explanation support, which is valuable, but does not specify log-content anomaly scoring, operation localization, learned multimodal fusion, affected-region truth or an explicit affected-region output. Claims must identify which mapping is passive support, which changes scores, and which capability is still OPEN. A graph image plus attached excerpts is not empirical evidence of a multimodal diagnostic gain.
- **Owner/timing:** D capability/claim table now; F packet verification; H/I only for correctly labeled target/explanation capabilities. No requirement to make every modality affect C1 or invent operation/node labels. The meaningful acceptance question is the pipeline's intended capability, not a demand for more features.

### SF-08 — MODERATE / inference and overengineering: decision rules are conventional and highly compound

- **FACT sources:** D §7 uses 20 scenario blocks, 50,000 bootstrap draws, two adjusted intervals, delta .05, 11 deletion sign checks, starvation/input gates and zero tolerance for arm-specific failures. §5.1 adds 32 chains, exact component preservation and mobile-graph gates. D openly calls the bootstrap a conditional sensitivity approximation and the thresholds design conventions.
- **Finding:** precision of constants does not establish scientific calibration or independent-sample inference. Conditional bootstrap bounds may organize finite-benchmark evidence, but “97.5%/simultaneous” language must not be turned into verified population confidence. The compound support rule may yield an inconclusive verdict even when there is useful bounded evidence; that is a declared decision convention, not a universal falsification theorem.
- **Preserve:** paired incidents/scenarios, visible heterogeneity, fixed endpoints, reproducibility, nuisance diagnostics and no score-guided rewiring. These are justified by C1. The bootstrap count and 32 controls are not inherently excessive compute for these graph sizes, but real end-to-end costs remain unmeasured.
- **Owner/timing:** D should explain the purpose of each gate and distinguish operational utility, experimental informativeness and claim strength; E measures cost/topology mobility before G. No basis here to demand fewer controls or approve different thresholds solely for simplicity. Any simplification must preserve the estimand and be reviewed before outcomes.

### SF-09 — MODERATE / feasibility remains execution evidence, not a specification contradiction

- **FACT sources:** D §§3/5.1/8/13 leaves reference-window control mobility, candidate coverage, signal saturation, loader joins, source pins and resources to label-free E/F validation. B full-case traces do not prove the fixed five-minute horizon; sampled joins do not prove all logs.
- **Finding:** these are real pre-campaign risks with correctly assigned checks, not already verified success and not reasons to rerun raw audits now. A rigid component-preserving control can be degenerate on small reference graphs; constant or clipped local scores can leave no useful contrast. The current thresholds may stop G but do not silently authorize changing them after scores.
- **Owner/timing:** E/F before G, with reviewed D revision if necessary. Preserve hard cases and the existing failure-inclusive estimand. No raw download or experimental execution is authorized by this review.

## 5. Claimed versus actually specified capability

| Capability | Actually specified in TD-v1.0 | What cannot yet be claimed |
|---|---|---|
| Dependency graph | Exact trace-parent relations in reference window; undirected binary processing for C1 | Full topology, causal edges, resource graph |
| Local anomaly evidence | Robust per-service metric deviation and trace-occurrence deviation | Calibrated anomaly probabilities or node correctness |
| Graph participation | Late fixed score smoothing and controlled ranking contrast | Graph-dependent detector, all graph methods, causal propagation |
| Detection | Metric-only rolling system score, unlabeled quantile, persistence/refractory replay | Production FPR, true onset, graph-based detection |
| Log/operation support | Counts, availability, source-linked excerpts, operation count differences | Log-content anomaly model, root-operation accuracy, measured fusion benefit |
| RCA output | Suspicion scores/ties for telemetry-derived services | Correctness, until E–G/H evidence exists |
| LLM | Deterministic input/output/rank-preservation boundary; I owns implementation and rubric | Faithfulness/usefulness, until measured |
| Public validation | RE2-TT known-window primary plus bounded detector replay | Multi-public-dataset validation |
| Target integration | Research adapter contract and H gate | FlashTicket runtime integration or changed application requirements |

## 6. What D may safely revise without changing C or human decisions

Safe candidate-specification revisions include: source-faithful current-guidance provenance; an explicit unresolved authority table; a requirement-to-capability/endpoint/owner map; exact distinction between the C1 probe and full-method capability; technical rationale for each simplification; precise metric disposition; clarification of conditional inference; a named gate for broader public-dataset evidence; and implementation acceptance conditions already owned by E/F. These preserve C1, labels-evaluation-only, valid negatives, C3/C4 conditional studies, mandatory C5/LLM, public-first then H and the two system/research interfaces.

Not safe to silently promote: “advisor approved TD,” “system demo replaces DT18 evaluation,” a second public release as selected/available, a supervised learner, a graph-dependent detector choice, a new novelty requirement, dropped C5/LLM/H, or new app/API/schema obligations. A concrete graph-dependent detector or additional public experiment can be proposed within D as `CANDIDATE` without changing C1, but accepting a changed capability/scope obligation requires the appropriate Minh decision. Do not bundle inferred consequences into the verbatim advisor-source statement.

## 7. Review handoff and preservation

- Decisions added/changed: none. C1 and RCA-001–017 remain unchanged. Authority/acceptance questions remain `OPEN`; suggested interpretations remain `CANDIDATE`.
- Assumptions: this is a research-specification review of the pinned TD-v1.0, not approval of a run; currently supplied guidance has no verified original date/channel; no assumed time shortage or preference for GNN, PageRank or a particular baseline.
- File owned by this reviewer: only `W/task-d/td-v1.1-source-first-review.md`. Preserve this FIRST PASS verbatim. Any challenge/adjudication or review of proposed TD-v1.1 belongs in an appended later pass.
- Checks: source reads and exact HEAD/working-tree inspection; no data/model execution. Scientific claims above concern written contracts and their logical implications, not benchmark outcomes.
- Formal-report material: method/GT distinction, exact graph role, method-choice rationale and prior limitations, public-dataset scope, failure-inclusive effect reporting, strict versus broad graph-anomaly wording, graph direction limits, explanation faithfulness versus root correctness, and unresolved advisor/DT18 scope authority.

**First-pass conclusion:** the existing C1 experimental core is defensible with its stated limits. The main reconciliation work is to close or visibly own the gap between that core and the full graph-anomaly/public-validation method program. This can be done without replacing C1 or inventing data capabilities, but it cannot be completed by stronger claims alone.

## Validation receipt after first-pass persistence

- The FIRST PASS above was persisted before discussion of the main reviewer's fixes, initial SHA-256 `62FB942286EA73A91EF3850588A5A55DE0DE0DA541C787993EDBB6515AF74D60`.
- The required P governance audit completed with **PASS, 0 warnings**, process exit 0. Its repository scope does not independently validate the scientific content of this W review.
- Working-tree check after the audit: P still only had the existing `M README.md`; W had only the new review artifact. No decision/source/method file was edited by this reviewer. The complete new-file diff was inspected; it contains this review only.
