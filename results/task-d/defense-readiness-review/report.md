# Task D — Defense Readiness & Rationale Review

> **POST-HOC DEFENSE-READINESS REVIEW — CANDIDATE**  
> **NOT FINAL EFFICACY · NOT PARAMETER SELECTION · NO METHOD CHANGE AUTHORIZED**

Review date: 2026-09-28  
Canonical method: TD-v1.3, SHA256 `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`  
Scope: read-only review of rationale, provenance, development limitations and defense language. No prediction, detector or randomized-graph run was executed.

## 1. Executive adjudication

### Verdict: **B. READY TO FREEZE AFTER DOCUMENTATION HARDENING**

TD-v1.3 has no scientific blocker identified by this review. Its primary estimands, comparison arms, selection firewall, negative-result policy and inference boundaries are defensible. The method also distinguishes prior-work primitives from study-specific parameterization and has bounded development sensitivities for the choices most likely to affect outcome.

It is not yet defense-ready as a standalone canonical document. Ten choices are `DOCUMENTATION_GAP`: their exact numeric thresholds are operationally reasonable and pre-outcome, but the rationale is scattered or not stated beside the clause. In addition, the TD status/prose still reflects an earlier amendment-review moment, while `CURRENT-STATE.md` now records completed development and Phase 1/2 limitations. These are documentation hardening needs, not authority to alter a formula, registry or completed artifact.

Audit totals across 64 major choices:

| Status | Count |
|---|---:|
| `DEFENSIBLE` | 18 |
| `DEFENSIBLE_WITH_LIMITATION` | 36 |
| `DOCUMENTATION_GAP` | 10 |
| `SCIENTIFIC_GAP` | 0 |

Provenance classifications:

| Classification | Count |
|---|---:|
| `DIRECTLY_ADOPTED` | 2 |
| `ADAPTED_FROM_PRIOR_WORK` | 10 |
| `STANDARD_STATISTICAL_METHOD` | 8 |
| `STUDY_SPECIFIC_DESIGN` | 44 |

No finding requires TD-v1.4, rerunning development or changing a registered method. Recommended gate: harden rationale/provenance prose, have Minh review the exact language, then freeze TD-v1.3 without changing method semantics.

## 2. PPR rationale

### 2.1 What comes from prior work and what belongs to TD-v1.3

PageRank/PPR is not invented by this project. PageRank supplies a stationary mass propagation mechanism with damping and a personalization vector. NetworkX documents that PageRank is driven by incoming-link structure and allows a user-specified personalization distribution. MicroRCA applies PageRank to a reversed anomaly graph in its official implementation. These sources support the primitive and the reverse-propagation lineage: [NetworkX PageRank](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html), [MicroRCA paper](https://doi.org/10.1109/NOMS47738.2020.9110353), [MicroRCA official code](https://github.com/elastisys/MicroRCA/blob/master/MicroRCA.py).

They do **not** validate the exact TD graph, score construction, undirected alternative or damping `.5`. Those are registered adaptations. The defensible statement is therefore:

> Prior work supports personalized/reversed PageRank as an RCA propagation primitive; TD-v1.3 tests a transparent, dataset-specific adaptation and does not inherit a causal or optimality guarantee.

### 2.2 Why PPR answers the C1 question

C1 asks whether dependency-aware propagation improves a fixed local anomaly ranking. The design keeps the upstream evidence identical:

`metric + trace local evidence → personalization p → observed dependency operator → O ranking`

`L` stops before propagation; `O` applies the observed graph; `R` applies topology-randomized controls while preserving coarse graph properties. This makes `O-L` the incremental effect of the registered observed-graph operator and `O-R` a topology-specific contrast. Degree or ordinary centrality would not answer this estimand because they can rank structural hubs without conditioning on incident evidence.

### 2.3 Direction, damping and alternatives

- The raw trace edge caller → callee is adopted from parent-child trace semantics. It is an observed execution dependency, not a causal edge.
- Reverse-call PPR embodies the hypothesis that a downstream symptom can transfer diagnostic mass toward an upstream caller. It has MicroRCA lineage but remains a heuristic.
- Undirected PPR tests whether adjacency remains useful when diagnostic direction is incomplete. It is an association operator, not a causal relaxation.
- `.85` is the conventional PageRank/MicroRCA reference point. `.2` and `.5` create a small registered range from local-evidence-dominant to graph-dominant propagation. Development selected undirected `.5`; no theorem says `.5` is optimal.
- Isolate self-loops make the transition well-defined and preserve local mass. They do not imply self-causation.

### 2.4 Why PPR remains primary despite development `O < L`

The method was registered to test graph value, not to guarantee graph victory. Development30 produced `L≈.744206`, `O≈.702405`, `R≈.678235`; HELP/HARM/UNCHANGED was `2/6/22`. A negative development result is therefore evidence about the registered estimand, not a method-selection failure that authorizes redesign.

Phase 1 also prevents an attractive but unsupported rescue narrative: all 17 cases where L placed the root at rank 1 remained rank 1 after PPR, so the hypothesis “PPR usually harms when local evidence is already strong” was `NOT SUPPORTED`. Isolate, degree and `travel × loss` patterns remain post-hoc/candidate mechanisms and cannot authorize graph gating.

### 2.5 PPR versus value diffusion and GNN

PPR redistributes normalized probability mass and preserves a clear personalization interpretation. Value diffusion smooths numeric scores and has a different mathematical meaning; it remains secondary so its outcome cannot replace the primary. A GNN would introduce learned representation, capacity, training and hyperparameter choices, defeating the controlled `L/O/R` estimand. This is a scope, fairness and reproducibility rationale—not evidence that GNN is inferior.

**PPR adjudication:** `DEFENSIBLE_WITH_LIMITATION`. It has real lineage and a strong experimental rationale. Its exact graph/damping parameterization is study-specific, development-selected with a small margin and limited leave-cell stability, and development efficacy is negative.

## 3. Formula and parameter provenance

The complete 64-row audit is in `parameter-defense-matrix.csv`. The classification rule used here is:

- `DIRECTLY_ADOPTED`: data semantics or a source rule transferred without changing its meaning.
- `ADAPTED_FROM_PRIOR_WORK`: prior work supports the primitive, but TD owns the adapter, inputs or exact values.
- `STANDARD_STATISTICAL_METHOD`: standard estimator, metric or inference device; study configuration is still bounded by TD.
- `STUDY_SPECIFIC_DESIGN`: registered operator, threshold, guard or experimental convention chosen for this study.

### 3.1 Verified source support

| Component | What the source supports | What it does not support |
|---|---|---|
| PPR / reverse graph | PageRank personalization and reverse-graph RCA lineage ([NetworkX](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html), [MicroRCA](https://doi.org/10.1109/NOMS47738.2020.9110353)) | TD observed graph, undirected choice or damping `.5` optimality |
| Robust median/IQR | Robust deviation under outliers/limited data in [BARO](https://arxiv.org/abs/2405.09330); median/IQR error normalization in [GDN](https://arxiv.org/abs/2106.06947) | TD windows, Q90, relative floor or `1e-12` safety semantics |
| Forecast-residual graph context | Graph-structured prediction/residual anomaly principle in [GDN](https://arxiv.org/abs/2106.06947) | TD ridge model, G/L/ALL masks, fit/cal split or thresholds |
| Conditional RCA comparator | Localized/conditional causal discovery family in [RCD](https://arxiv.org/abs/2203.14883) and its fixed official adapter lineage | Causality of TD trace graph or equivalence of adapters |
| Graph total variation | Canonical variation functional `x^T L x` in graph-signal literature | Gaussian guarantees or exact thresholds on TD binary observed graphs |
| Grouped validation | Blocking dependent samples is preferable to naive random folds ([Roberts et al.](https://doi.org/10.1111/ecog.02881)) | Exact five-fold/two-cell design optimality |
| Block bootstrap | Resampling must respect dependence; naive resampling can mislead ([Owen](https://arxiv.org/abs/0712.1111)) | Exact validity for every crossed benchmark dependency |
| Selection uncertainty | Model-selection reuse can create optimism ([Cawley & Talbot](https://www.jmlr.org/papers/v11/cawley10a.html)); overlapping CV estimates are correlated ([Bengio & Grandvalet](https://www.jmlr.org/papers/v5/grandvalet04a.html)) | A proof that TD's development selection has zero bias |
| SESOI | Practical effect thresholds should be prespecified and justified ([Lakens](https://pubmed.ncbi.nlm.nih.gov/28736600/)) | Universal meaning of MRR delta `.05` |

Every adapted row in the matrix says `PRIOR SUPPORTS PRINCIPLE, NOT EXACT PARAMETERIZATION` where transfer could otherwise be overstated.

### 3.2 Why study-specific numbers can still be defensible

The majority of rows are study-specific because the benchmark cadence, data availability, leakage boundary and compute budget must be operationalized. A number is defensible without a paper asserting the same number when it:

1. targets an explicit failure mode;
2. was fixed or bounded before outcome;
3. has a small, registered alternative set where outcome sensitivity matters;
4. has a claim boundary matching the evidence; and
5. is not described as an external optimum.

TD-v1.3 meets this standard for the main windows, temporal aggregators, PPR grid, lag, lambda/q grids, event policy, R budget and inferential thresholds. The ten documentation gaps fail prose centralization, not scientific validity.

## 4. Strongest rationale

1. **The L/O/R estimand and shared-evidence constraint.** The comparison changes the graph operator while holding local evidence and case support fixed. This is the clearest defense against confounding upstream score quality with graph value.
2. **Leakage and selection firewall.** Fit, calibration, injection and final confirmation are separated; root/fault repeats stay grouped; predictions/selections are sealed. Negative development results are preserved rather than tuned away.
3. **PPR as a transparent prior-work-informed primitive.** Personalization connects the operator directly to C1, while reverse and undirected alternatives are bounded and explicitly non-causal.
4. **Robust score construction with explicit missingness.** Median/IQR and Q90 have an intelligible robustness purpose; absent data are not silently interpolated; root absence is conservatively scored as failure.
5. **Inference and claim controls.** MRR is predeclared primary, tie handling is fixed, two primary contrasts receive multiplicity control, and delta `.05` is presented as a study-specific SESOI rather than an SLA.

## 5. Weakest rationale

The five choices most likely to draw difficult questions are:

1. **Absolute fallback `1e-12`.** It is numerically necessary but not physically meaningful; Phase 2 found severe scale effects and lambda-loss dominance. It remains defensible only with explicit disclosure that it is a real but non-decisive limitation.
2. **Undirected PPR with damping `.5`.** It was selected on only 30 development cases, with a small selection margin and leave-cell instability. It must be called a registered development choice, never an optimum.
3. **Primary timing: C1 `300 s`/`10 s` and C5 `5 s`/lag1.** Registered sensitivities show material temporal sensitivity, especially bin10 and lag3 for L-MTL. These choices define the estimand; they are not universal.
4. **Coverage gates (`24/30`, five distinct seconds, `18/23`, `9/12`, 80% and 10%).** They solve clear support/representativeness failure modes, but exact cutoffs lack direct sensitivity and their rationale is insufficiently centralized.
5. **R mobility and compute thresholds (`256`, `200E`, overlap/unique/stratum gates).** They are sensible prespecified quality controls, yet passing them demonstrates observed movement, not Markov-chain convergence.

## 6. Documentation gaps

Ten matrix rows are `DOCUMENTATION_GAP`. They can be resolved with prose only, without changing a parameter:

1. Explain `>=5 distinct seconds` as a half-bin temporal-coverage guard.
2. Explain `>=24/30 finite bins` as the C1 80% support convention and state that no direct cutoff sensitivity exists.
3. State that the R mobility thresholds are operational minimum-quality gates, not a mixing theorem.
4. Explain `>=18/23` C5 fit rows as approximately 80% usable lagged support.
5. Explain `>=9/12` calibration rows as minimum viability, while acknowledging tail-quantile uncertainty.
6. Explain `>=100` normal endpoints as minimum pooled support, not 100 independent observations.
7. Explain `>=80%` training-case contribution as a case-coverage guard, not balanced influence.
8. State the exact signal-starvation rule: relation attribution becomes inconclusive when at least 80% of planned final incidents have empty `V` or identical rounded normalized local values; all-zero is handled separately as all-tie. It is not a generic “fewer than 80% eligible” rule.
9. Explain shared-preprocessing failure `>10%` as a governance stop condition, not an ignorable-failure guarantee.
10. Explain C5 lambda eligibility `>=80%` as broad case participation that does not prevent numeric loss dominance.

Cross-cutting prose hardening is also required:

- Update the TD status/context narrative so it no longer reads as though no development predictions exist; do not modify formulas or registry entries.
- Add a concise “source supports principle, not exact parameterization” boundary beside PPR, robust scaling, forecasting, RCD and graph-TV lineage.
- Add the Phase 1 negative mechanism result and Phase 2 `1e-12` limitation to the defense/limitation section without turning either into a rule or amendment.
- State explicitly that G/L/ALL differ in context/capacity, so G-versus-L is not a pure graph-structure effect.

These edits require Minh's approval as documentation hardening of the canonical Task D source. This review does not perform them.

## 7. Scientific gaps

**None identified (`0`).**

The review found no code-versus-TD mismatch, unregistered outcome-dependent primary choice, undefined primary estimand or evidence-chain break that would materially invalidate inference. Strong sensitivity and selection uncertainty remain limitations, not blockers, because they are visible, bounded, and paired with restricted claims.

A future finding would become a `SCIENTIFIC_GAP` only if it showed, for example, that a primary computation differs from TD, final labels entered selection, a comparison arm lacks common evidence in a way that invalidates the contrast, or the saved artifact cannot support the declared endpoint. None of those conditions was found here.

## 8. Phase 1/2 implications

### Phase 1 — C1 mechanism analysis

- Recomputed development: `L≈.744206`, `O≈.702405`, `R≈.678235`.
- HELP/HARM/UNCHANGED: `2/6/22`.
- All `17/17` local-rank1 cases retained rank1 under PPR.
- The hypothesis that PPR usually harms already-strong local evidence was `NOT SUPPORTED`.
- Degree, isolate and `travel × loss` patterns are post-hoc, exploratory and non-causal.

Defense implication: do not say PPR generally dilutes strong evidence; do say the registered graph operator did not improve aggregate development C1 and that limited case mechanisms remain hypotheses only.

### Phase 2 — C5 scale diagnosis

- `1e-12` is an absolute input-scale fallback, not the relative floor or residual floor.
- When median magnitude and IQR are zero, relative-floor variants cannot change that branch.
- Affected channels can dominate lambda-selection forecast loss numerically.
- That dominance is insufficient to explain primary L-MTL collapse: lag3 recovered L-MTL strongly while affected scaler identities stayed unchanged.
- G-versus-L remains confounded by context/feature capacity.
- Final classification was `REAL BUT NON-DECISIVE LIMITATION`; recommendation was to keep TD-v1.3 with explicit limitation.

Defense implication: acknowledge the pathology, avoid single-cause attribution, preserve the sealed method, and do not claim graph “fixes” the scale issue.

## 9. Freeze recommendation

### Recommendation: **HARDEN DOCS THEN FREEZE**

The exact next step is a bounded documentation pass, subject to Minh's approval, that:

1. adds the ten gate rationales listed above beside or in a single authoritative rationale section;
2. centralizes PPR lineage and the boundary between prior primitive and TD adaptation;
3. incorporates Phase 1/2 limitations using their existing post-hoc status;
4. updates stale development-state prose without changing any formula, parameter, registry, hash-protected completed artifact or claim gate; and
5. has Minh verify that the 43 spoken answers in `defense-qa.md` match the intended defense position before marking TD human-approved/frozen.

No method decision is required. If Minh wants to change any number or operator rather than document it, that would be a separate amendment decision with selection-exposure analysis; this review does not recommend or authorize it.

## Audit boundary and confirmations

- Development30 state and Phase 1/2 reports were read; Phase 1/2 were not reopened.
- Final60 and Task F/G/H/I were not opened.
- Zero model/prediction/detector/RCD/randomized-graph reruns.
- Zero TD/config/registry mutation.
- Zero commit/push.
- Exactly three new review artifacts were created in this directory.
