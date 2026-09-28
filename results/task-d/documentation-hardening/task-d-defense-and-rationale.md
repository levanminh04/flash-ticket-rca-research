# Task D — Defense and Rationale Companion

> **DOCUMENTATION-ONLY COMPANION TO EXECUTED TD-v1.3**  
> **DOES NOT MODIFY METHOD SEMANTICS**  
> **EXECUTED TD SHA256: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`**

Status: `CANDIDATE` documentation for Minh's review. This is not human approval, method freeze, TD-v1.4, final efficacy or authorization for Task F/G/H/I. The canonical executed specification remains `P/docs/research-rca/task-d-method-and-experiment-specification.md`; if this companion differs from it, the canonical TD rules.

## 1. Purpose and evidence boundary

This companion makes the rationale and limitations of the already executed TD-v1.3 easier to defend. It adds no formula, threshold, hyperparameter, candidate, selection right, split, evaluator, graph operator or failure policy. Development30 is complete with `PASS WITH LIMITATIONS`; current-method final60 predictions/labels are unopened and the method remains `CANDIDATE` pending Minh's human decision. The benchmark is not called clean or untouched: TD's exposure ledger records that E1 had already seen TT90 baseline outcomes and post-hoc fusion/strata.

Epistemic boundary:

- `FACT`: exact TD text/hash, completed development identities and saved Phase 1/2 measurements.
- `USER_CONFIRMED`: this session may add documentation-only companion/audit/assurance artifacts while preserving TD bytes.
- `CANDIDATE`: defense interpretations and freeze-readiness recommendation.
- `OPEN`: human method acceptance/freeze, Task F authorization, final60 efficacy and FlashTicket target-system results.

## 2. Ten data-quality and interpretation gates

No external source establishes the exact numeric value of any gate below. They are fixed, pre-outcome `STUDY_SPECIFIC_DESIGN` guards. Their defensibility comes from a named failure mode, precommitment, retained planned denominators and bounded claims—not from pretending the number is universally optimal.

### 2.1 Metric-bin support: `>=5 distinct seconds`

- **Exact role:** a C1 10-second metric bin is available only when at least five distinct seconds contribute after identical duplicates collapse.
- **Failure mode prevented:** a burst or repeated sample at one/few timestamps representing the whole bin.
- **External exact-value source:** none.
- **Direct sensitivity:** no sensitivity changes the half-bin support ratio alone. Registered bin5/10/20 variants use `ceil(0.5 * bin seconds)`, so they preserve the rule while changing resolution.
- **Why defensible:** it is a simple half-bin temporal-coverage convention fixed before outcomes and applied identically to L/O/R.
- **Allowed claim:** the bin has a minimum spread of observed seconds under the registered convention.
- **Prohibited claim:** five seconds is statistically optimal, literature-mandated or proof of uniform sampling.

### 2.2 C1 channel support: `>=24/30` finite bins in both windows

- **Exact role:** a C1 channel enters local evidence only with at least 24 finite bins in each 30-bin reference and query window.
- **Failure mode prevented:** median/IQR and Q90 being driven by heavily incomplete fragments or asymmetric support.
- **External exact-value source:** none.
- **Direct sensitivity:** none for the 80% ratio. Window/bin sensitivities recompute the gate as `ceil(0.8N)` rather than searching the ratio.
- **Why defensible:** the fixed completeness convention conditions whether a channel is usable; unavailable data remain explicit and planned cases are retained.
- **Allowed claim:** included channels meet the registered two-window completeness minimum.
- **Prohibited claim:** 80% proves missingness is ignorable or was selected to maximize MRR.

### 2.3 R mobility thresholds

- **Exact role:** before strong topology-arrangement interpretation, require per case at least 32 distinct final graphs and median retained-edge fraction at most `.8`; require those case-level conditions for at least 80% of planned final cases and at least 50% of each evaluator root stratum.
- **Failure mode prevented:** presenting an unswitchable or barely moving randomization kernel as a meaningful topology control.
- **External exact-value source:** none.
- **Direct sensitivity:** no direct search of gate cutoffs. Registered topology-only `100E/200E/400E` diagnostics assess mobility at bounded proposal budgets without root outcomes.
- **Why defensible:** the gates are minimum movement diagnostics fixed before outcome; failing cases are not removed and the TD explicitly says this is not a mixing proof.
- **Allowed claim:** a passing run showed the registered minimum endpoint diversity/edge turnover across the required cases/strata.
- **Prohibited claim:** passing proves stationary, uniform or independent graph samples, causal topology, or complete nuisance control.

### 2.4 C5 fit support: `>=18/23` lag1 rows

- **Exact role:** a primary lag1 target model requires at least 18 valid own-lag/target fit pairs from the 23 possible rows after the first lag.
- **Failure mode prevented:** fitting a per-target ridge model on a small, missingness-selected fragment.
- **External exact-value source:** none.
- **Direct sensitivity:** none for 18/23 alone. Bin10, prefix240 and lag3 use their separately registered row gates as profile changes, not a threshold search.
- **Why defensible:** about 78% support is close to the study's broader 80% completeness convention; it is input-only, frozen before predictions and common across G/L/ALL and lambda values.
- **Allowed claim:** every modeled primary lag1 target met the registered minimum own-row support.
- **Prohibited claim:** 18 rows guarantee coefficient accuracy, independence or optimal generalization.

### 2.5 C5 calibration support: `>=9/12` rows

- **Exact role:** a target must have at least nine valid held-out calibration input rows, followed by finite residual verification, to emit calibrated residual scores.
- **Failure mode prevented:** residual center/scale being estimated from only a few points or from numerically invalid residuals.
- **External exact-value source:** none.
- **Direct sensitivity:** none for 9/12 alone; registered temporal profiles change support and gates together.
- **Why defensible:** it requires most of the disjoint calibration minute while tolerating limited archival missingness.
- **Allowed claim:** calibrated targets have the registered minimum held-out support.
- **Prohibited claim:** nine correlated residuals make Q95–Q99 precise or probabilistically calibrated.

### 2.6 Threshold selection: `>=100` normal endpoints

- **Exact role:** a fold's weighted normal-score distribution must contain at least 100 finite endpoints before q selection is valid.
- **Failure mode prevented:** choosing an upper-tail operating point from trivial pooled support.
- **External exact-value source:** none.
- **Direct sensitivity:** none for this gate.
- **Why defensible:** it is a pre-outcome minimum-support rule combined with case-coverage and weighted-CDF semantics.
- **Allowed claim:** q selection had at least the registered number of finite normal endpoints.
- **Prohibited claim:** the endpoints are independent, 100 guarantees tail precision, or q is a production false-positive rate.

### 2.7 Threshold selection: `>=80%` training-case contribution

- **Exact role:** at least 80% of fold-training cases must contribute at least one normal score to the threshold distribution.
- **Failure mode prevented:** a few well-instrumented cases defining the shared threshold.
- **External exact-value source:** none.
- **Direct sensitivity:** none for this gate.
- **Why defensible:** it is a pre-outcome representativeness guard used with planned-case denominators; case contribution is visible rather than silently dropped.
- **Allowed claim:** the threshold distribution had broad case participation under the fixed rule.
- **Prohibited claim:** participation is endpoint-balanced, missing-at-random or representative of production traffic.

### 2.8 Signal-starvation gate: `>=80%` planned final incidents

- **Exact role:** relation attribution is `INCONCLUSIVE` when at least 80% of planned final incidents have empty `V` or identical `round(local/max(local),12)` values; all-zero is handled separately as the common all-tie/no-evidence case.
- **Failure mode prevented:** interpreting graph differences when the shared local evidence is absent or non-discriminating in most incidents.
- **External exact-value source:** none.
- **Direct sensitivity:** none for the 80% cutoff.
- **Why defensible:** it is fixed before final outcomes, conditions only strong relation attribution, retains failures/cases and does not automatically veto a valid bounded negative when local signal is informative.
- **Allowed claim:** widespread local-signal starvation makes the graph relation contrast uninterpretable under TD-v1.3.
- **Prohibited claim:** this is a generic “fewer than 80% eligible” rule, passing proves evidence quality in every stratum, or starved cases may be excluded.

### 2.9 Shared preprocessing failure: `>10%` planned final incidents

- **Exact role:** more than 10% shared preprocessing failure makes shared input insufficient and relation attribution `INCONCLUSIVE`.
- **Failure mode prevented:** a common loader/mapping failure being misread as an L/O/R difference or full-study efficacy result.
- **External exact-value source:** none.
- **Direct sensitivity:** none.
- **Why defensible:** it is a conservative, fixed governance stop condition applied before arm comparison; operational utility still scores failures as zero.
- **Allowed claim:** the graph attribution gate is not passed when shared pipeline loss exceeds the registered ceiling.
- **Prohibited claim:** up to 10% failure is ignorable, unbiased or proof that the input pipeline is correct.

### 2.10 C5 lambda objective: `>=80%` development-case eligibility

- **Exact role:** common lambda selection requires eligible fixed input target IDs from at least 80% of development cases; input-insufficient cases add no loss observations but remain planned coverage denominators.
- **Failure mode prevented:** selecting a shared regularizer from a narrow subset of convenient cases.
- **External exact-value source:** none.
- **Direct sensitivity:** none for the 80% gate; the three registered lambda values are the bounded selection set.
- **Why defensible:** eligibility is determined before predictions, identically across G/L/ALL/lambda, and cannot shrink based on numerical prediction success.
- **Allowed claim:** the selected lambda objective had broad case eligibility under the registered rule.
- **Prohibited claim:** 80% prevents channel-level loss dominance, balances target influence or validates the objective's physical scale. Phase 2 specifically shows that it does not.

## 3. Why PPR is used in C1

### A. PageRank/PPR primitive

Personalized PageRank is a stationary probability-mass propagation mechanism with damping and a personalization distribution. It is suitable for the registered C1 estimand because the observed local anomaly evidence can become the starting mass rather than letting structure alone rank hubs. This is a standard primitive, not a claim that PageRank is the universally best graph RCA method.

### B. Prior RCA lineage

MicroRCA's official implementation reverses its anomaly graph and applies PageRank with `alpha=.85`. This supports reverse-propagation lineage and the conventional `.85` reference. It does not validate the exact RE2-TT graph, local score, undirected variant, randomized control or selected `.5`: [MicroRCA code](https://github.com/elastisys/MicroRCA/blob/master/MicroRCA.py).

### C. Exact TD-v1.3 adaptation

TD-v1.3 constructs a binary observed caller `u -> v` relation only when a same-trace parent resolves and both spans lie in the reference window. That edge is an observed execution dependency, **not a causal edge**. The primary operator uses either the reverse-call projection or a declared undirected development alternative.

For positive local mass `l`, TD computes:

```text
m = max(l)
p = (l/m) / sum(l/m)
pi = (1-d)p + d T^T pi
d in {.2,.5,.85}
```

If `sum(l)=0`, the canonical result is a common all-tie/no-evidence outcome. There is **no uniform-PPR fallback**. Uniform-positive personalization is only a label-free diagnostic; it may create a topology ranking and must not be confused with primary zero-mass behavior.

The controlled interpretation is:

```text
same metric+trace local evidence
  -> L: no graph propagation
  -> O: registered observed-graph propagation
  -> R: same propagation on degree/component-preserving perturbations
```

- `O-L` estimates the incremental effect of the registered graph propagation on the same upstream evidence.
- `O-R` examines the arrangement of observed topology relative to finite structural perturbations that preserve the declared coarse properties.
- Neither contrast identifies causal edges, all graph value or all topology nuisance.

`.85` has prior/reference lineage. `.2` and `.5` are a bounded study-specific grid spanning lower and intermediate reliance on graph travel. Development selected undirected `.5`; no theorem or source makes `.5` optimal. The undirected variant is a study-specific direction-agnostic alternative, not a prior-work guarantee and not a causal model.

PPR remains primary because it cleanly tests mass propagation anchored by local evidence. Value diffusion is secondary because it smooths score values rather than redistributing probability mass; it cannot rescue or replace the primary after outcome. A GNN would introduce learned representation, capacity, training and hyperparameter choices, so it would answer a different question rather than the controlled L/O/R estimand.

## 4. Formula distinctions that must not be collapsed

### Input normalization

C1 and C5 input channels use the registered robust input scale:

```text
center = median(finite fit/reference values)
scale  = max(IQR, epsilon_rel * median(abs(values)), 1e-12)
```

`epsilon_rel` is the relative input floor. `1e-12` is the absolute input fallback reached when both IQR and relative magnitude are zero.

### C5 residual normalization

C5 later normalizes held-out absolute forecast errors using a separate formula:

```text
mu_e = median(e)
s_e  = max(IQR(e), epsilon_e)
r    = max(0, (e-mu_e)/s_e)
epsilon_e = .01 primary; {.001,.1} sensitivities
```

The residual floor is absolute and downstream. It does not alter input scalers or the input `1e-12` branch.

### G/L/ALL

All arms use the same targets, input scalers and nominal five-slot tensor under a fixed configuration:

- `L`: own lag; all four context mean/fraction slots forced to zero.
- `G`: own lag plus caller/callee same-channel graph-neighbor means and coverage.
- `ALL`: own lag plus all-other same-channel context, duplicated into the two context blocks as specified.

Their effective capacity differs. G-versus-L is therefore a graph-restricted additional-context comparison, not a pure graph-structure causal effect. ALL is a generic-context diagnostic, not a capacity-matched no-graph control.

### Graph TV

The exact registered secondary operator is:

```text
TV_c = mean over valid undirected edges of (z_u,c - z_v,c)^2
S = max_c TV_c
```

It is adapted from graph total-variation principles; it is not literally an unnormalized `x^T L x` implementation. No comparable edge yields `UNAVAILABLE`, and Graph TV cannot rescue primary C1/forecast failure.

## 5. Phase 1 limitation — C1 mechanism

Development30 produced `L=.744206`, `O=.702405`, `R=.678235`; observed graph/PPR did not exceed local-only on aggregate. HELP/HARM/UNCHANGED was `2/6/22`.

All `17/17` cases where local evidence ranked the root first retained root rank 1 after PPR. Therefore the earlier hypothesis “PPR commonly harms when local evidence is already strong” is **NOT SUPPORTED**. The six HARM cases all began with a non-top1 local root.

Isolate, degree, reachability and `travel × loss` patterns are post-hoc `CANDIDATE` mechanisms from 30 cases/10 cells. They are exploratory, non-causal and do not authorize a runtime graph gate, operator switch or method redesign. The allowed statement is only that PPR behavior varied with topology/cell/binning in development and aggregate O did not improve over L.

## 6. Phase 2 limitation — C5 absolute input fallback

`1e-12` is the absolute **input-scale** fallback. When both `median(abs(finite))=0` and `IQR=0`, changing the relative-floor multiplier leaves the branch unchanged:

```text
epsilon_rel * 0 = 0
max(0, 0, 1e-12) = 1e-12
```

Phase 2 found that affected channels were 4.1947% of selected-lambda eligible targets but contributed 99.9999999846% of the registered lambda objective. Affected channels also set the extreme primary L calibration tail and L-MTL/L-MT thresholds. The existing relative-floor OFAT did not test the absolute fallback because the same 288 scaler identities remained affected.

This is not sufficient to explain primary L collapse. Lag3 kept exactly the same 288 affected scaler identities but raised L-MTL F1 from `.0726` to `.6508` and removed the extreme threshold behavior. Affected channels were system-max sources in a minority of bins, and G/L/ALL all modeled nearly the same affected targets. G and ALL had additional context/effective capacity, so G-versus-L cannot be attributed solely to graph structure or to avoidance of the fallback.

The adjudication remains **REAL BUT NON-DECISIVE LIMITATION**: the fallback is a material numerical/interpretive weakness and must be disclosed, but saved registered evidence neither identifies it as the sole cause nor requires a post-outcome floor amendment. This companion proposes no new floor or experiment.

## 7. FlashTicket target-system role

Public benchmark and FlashTicket supply different evidence:

- **Public benchmark:** ground-truth-evaluable method evidence under controlled, known injected roots/faults and the registered public-data adapters.
- **FlashTicket:** **target-system controlled transfer/validation**—map actual FlashTicket log/trace/metrics, construct its observed dependency graph, integrate the read-only diagnostic mechanism, inject/observe controlled faults under authorized system gates, and measure transfer plus system behavior.

FlashTicket is not merely a demo or visualization surface. It is the target product in which the RCA mechanism must run and be evaluated. Conversely, no FlashTicket efficacy, production alarm quality or transfer success is claimed before those target-system measurements occur. Public results do not substitute for FlashTicket validation, and FlashTicket evidence does not retroactively tune the public final campaign.

## 8. Human freeze boundary

Documentation hardening leaves all negative and unstable development findings visible. It does not convert study-specific conventions into externally validated optima, post-hoc correlations into runtime rules, or development selections into final efficacy. A material pre-freeze method change would require a versioned return to Task D, independent review and an explicit extra-attempt/exposure record; it would increase development selection exposure but would not itself open final60. No current finding requires that amendment path. Minh remains the human owner of any approval/freeze decision. Task F and current-method final60 outcomes remain unopened.
