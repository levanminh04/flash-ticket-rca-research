# TD-v1.3 C5 clarification rationale

Status: CANDIDATE technical specification for U27R-authorized development. Not human approval of an algorithm, formal five-agent assurance, final freeze, or empirical success. Coordinator selected the policies after three independent native reviews and **before any actual development prediction, F1 or MRR outcome**. Outcomes did not select these policies.

Authority: P/docs/evidence/project-direction/2026-09-27-rca-c5-amendment-and-e-resume.md. P means flash-ticket-platform; W means flash-ticket-rca-research. Canonical executable rules are P/docs/research-rca/task-d-method-and-experiment-specification.md §7.0a–b. Old TD-v1.2 bytes are preserved in W/task-d/td-v1.2-before-c5-amendment.md (SHA256 985f1c5fc983422272dfbde8b69ed5ff98ee4fdd1631af075d03788c3770ad54). The pre-change inventory preserves earlier receipts and unrelated working-tree state.

## Evidence and independence

A c5_semantics_a reviewed semantics/dataflow; B c5_statistics_b reviewed statistical effects; C c5_adversary_c reviewed adversarial counterexamples. Initial reviews were read-only and independent, with no development outcomes and no access to each other's recommendations before responding. They considered competing interpretations; agreement alone did not select a rule. The coordinator subsequently assigned separate implementation modules. Their implementation work is not fresh independent qualification; a new reviewer must inspect the amendment and expected fixtures before resume.

Task B §12.6 audited all 90 pinned trace files, 67,345,051 rows, and found zero duplicate composite (traceID,spanID) keys. This previously recorded aggregate is evidence about the pinned corpus, not new access to final raw data. It means conflict handling is defensive and cannot be presented as empirically prevalent. B's joins support exact service/time association, not request identity from log text, causal graph truth, or certified arrival order. Prior E receipts establish numeric and bounded loader properties, not a C5 policy or actual RCA performance.

## D-E27-01: membership versus own-model availability

Problem: TD-v1.2 did not uniquely define frozen applicable neighbors. A scaler-only neighbor and an own-model-eligible neighbor can produce different context and coverage from identical observations.

| Candidate | Advantages | Costs / reason rejected or selected |
|---|---|---|
| M1: fit-prefix exact mapping plus scaler support, independent of own forecast model | Freezes context from observed channel support; separates signal availability from whether a target can be forecast; avoids lag/config-dependent graph degree | SELECTED. Singleton/constant or sporadic channels can have weak scales. Must disclose support and floor diagnostics; no invented support threshold. |
| M2: require own-model fit eligibility | Removes sparse poorly supported neighbors; deterministic if input-only | Rejected for this registry: changing own lag or row gate changes neighbors and the estimand, confounding registered lag sensitivity with graph pruning. It excludes usable observed neighbor signals merely because their own targets cannot be forecast. |
| M3: require calibration/residual/model success | May remove noisy or numerically troublesome signals | Rejected: calibration and solver results would alter training context; arm/λ-dependent support changes masks and can reward numerical failure. |

M1 predicate E is exact §7.0a: literal fit-prefix node, exact channel mapping, at least one finite unmasked fit bin, and positive fit count for count channels. Median/type-7 IQR/floor are fitted to finite fit observations. Own model still needs the registered fit/cal input row gates. Nonfinite predictions are failures, not permission to shrink eligibility. Per-bin availability intersects a frozen set; it changes the numerator and mean, never the denominator. Empty set and empty available subset both yield 0/0 feature sentinels but different audit states.

### Related warmup identity defect

TD-v1.2 used a 180-second vocabulary with a 120-second fit segment. Viable alternative V180 would retrospectively use all warmup identities for training: it is causal at the first emitted score but makes the held-out calibration identity select fit context. Example: B has metrics throughout fit but first trace at 150s; appending B changes ALL's training mean. B explicitly demonstrated this; A/C accepted it as a meaningful abstraction issue.

SELECTED: Vfit at F=120 controls every scaler/context/model. V at H=180 may append cal-only services as isolates with all models/channels absent. Alternatives of keeping V180 would require weakening held-out claims to values conditional on warmup identity. Chosen rule preserves held-out dataflow without adding a parameter. F/H track only the already registered sensitivities. Names are literal observations, including later-discredited keys, not physical truth. No trace after H expands V.

Effects: G uses exact-channel caller/callee sets; L context is zero; ALL uses all other E services twice. Missing-neighbor indicators can themselves change residuals. ALL duplicates columns and therefore changes effective ridge capacity; it is generic-context comparison, not perfect capacity matching. Fixed-parameter MT and MTL M/T components are identical; MTL adds log targets and may change system max and fitted threshold. TV uses E, not own model gates. Calibration may disable a target output without changing another target's context.

Assumptions/risks: exact same suffix is a pragmatic comparability rule, not proof that services have comparable healthy scales. One/small finite support, constants, missingness patterns and correlated short calibration errors can inflate residuals. Preserve flags/support/coverage; do not silently add a threshold or tune it using outcomes. Backward compatibility: split, C1, λ/q and all registered numeric gates remain; C5 formerly ambiguous inputs become uniquely defined. Cal-only identities intentionally cease to influence fit context.

## D-E27-02: encountered trace contradictions

| Candidate | Advantages | Costs / reason rejected or selected |
|---|---|---|
| Local trace-only current-bin mask of observed owner union, persistent key tombstone | Localizes evidence corruption to actually contradictory identity; explicit recovery; preserves independent M/L | SELECTED. Older committed counts and frozen graph may later be discredited, which remains visible in audits. |
| Mask all trace services in every conflicting bin | Conservative and deterministic | Rejected when owners are known: discards unrelated service observations and induces correlated missingness without evidence. Used only when owner is unknown, so localization is impossible. |
| Permanently invalidate service/case/all modalities | Simple invalidation | Rejected: key contradiction is not evidence of permanent service absence or corrupted independent M/L. Missingness changes the experiment disproportionately. |
| Clean entire archive/rebuild prefix from future variants | Produces globally consistent retrospective tables | Rejected: future observations retract previous bins, graph or decisions; cache cutoff invariance fails. |

Replay event timestamps, not file row order or invented arrival times; equal-time batches prevent tie-order winners. Full 11-field payload equality has one null sentinel. Identical duplicates count once; a distinct payload for the same composite key quarantines it. Only current trace bins for the union of claimed literal owners become unavailable. Third owner expands the union now/later, never earlier. Missing key with valid owner masks that owner's trace bin; unknown owner masks all trace channels in the bin. Null/unresolved parent is not contradiction. Metric/log channels stay independent. Unplaceable required metric-origin/trace clocks are input-admission failure, not repaired chronology; malformed optional log clocks explicitly disable logs alone.

### Disagreement: provisional fit cleansing

B proposed a viable alternative: before first score, clean counts in the provisional fit prefix when a later fit contradiction is known. A/C favored all closed bins immutable. Coordinator rejects B's count-cleansing alternative to maintain one deterministic cutoff/cache rule across fit, calibration and runtime. Earlier accepted fit counts remain committed, even if later discredited; do not call those counts ground truth. At F the graph is nevertheless an integrity-checked snapshot: only still-clean parent and child witnesses known by F support an edge; another clean support preserves the binary edge. This count/graph asymmetry is explicit rather than hidden. After F no graph, scaler, membership or coefficient repair. Late contradiction gets a post_freeze_discredited_support receipt.

Service recovery is next clean bin, key tombstone is permanent, no TTL. Own lag can delay a residual by one/three further bins. Partial-channel missingness cannot reset the system event streak when another channel still supplies a valid positive score. Source clock/schema admission is distinct from causal identity replay; prefix guarantees are conditional on placeable clocks, not an assertion that corrupt future timestamps can be processed.

Effects on G/L/ALL: same observed bins/masks, same E and frozen support; no arm-specific cleaning. G may keep late-discredited topology as a declared frozen observation. ALL's context can change only through current availability. MT/MTL share M/T effects and leave logs unchanged. TV sees the same graph and current masks. Backward compatibility: no C1 conflict-policy change; C5 gets a new deterministic event-time policy, no new operator or tuning parameter. Main failure mode is retained questionable historical evidence, plus unknown-owner all-trace missingness and permanent key quarantine; each has an audit counter and cannot be silently excluded.

## Analytic expectations fixed before implementation execution

Numbers below are standardized channel values; trace counts below are accepted raw counts before log1p.

| Fixture category | Expected result from TD-v1.3 |
|---|---|
| Both neighbors scaler + own models, b=4,c=10 | mean7, coverage1, denominator2 |
| c scaler exists but own fit pairs insufficient | same mean7/1/2; c own model absent |
| b current missing with valid own model | mean10, coverage.5, denominator2 |
| c wholly fit-absent but future c=100 | mean4, coverage1, denominator1; future cannot join |
| Applicable pool empty | mean0, coverage0, denominator0 |
| Applicable b,c both currently absent | mean0, coverage0, denominator2 |
| G/L/ALL | same own value; L four zero slots; ALL duplicates 7,7,1,1; isolate G equals L features |
| MT/MTL | M/T E, raw component predictions/errors identical at fixed λ; system maxima may differ |
| Recovery/denominator freeze | missing then available never changes frozen denominator |
| Joint permutation | inverse-permuted arrays, graph and outputs equal |
| Cal-only B first trace150, prior metrics | V includes B; Vfit excludes B; B isolated/model-absent and absent from ALL |
| First trace at181 | cannot expand V |
| Clean parent A at10, child B at11 | A→B, child accepted once |
| Identical child duplicate | count once, no masks, edge retained |
| Same-time distinct payload at11 | B bin[10,15) masked; no edge witness; permutation invariant |
| Child conflict claiming C at119.999 | B/C bin[115,120) masked, older bins unchanged, edge unsupported at F |
| Independent second clean support | binary A→B survives a poisoned first support |
| Conflict exactly120 | graph already frozen with A→B; only [120,125) masked |
| Conflict at200 | frozen graph and all prior bins/outputs unchanged; [200,205) mask plus late-discredit audit |
| Repeated tainted key at201,207 | both current bins masked; no new accepted count |
| Third owner | expands current/future owner union only |
| Clean bin[205,210) after conflict | service count available; lag1 residual may still be absent until endpoint215 |
| Conflict in trace with usable metric/log | M/L unchanged bytewise |
| Missing key / unknown owner / null parent | local trace mask / all-trace mask / no conflict respectively |
| Chunk/cache replay and cutoff extension | same closed values, masks, graph and audits at same cutoff; future cannot retract prefix |
| Event t=τ | pre-injection because producing bin ends at τ; first post trigger strictly greater |

Fixture files and actual reports must identify the tested expectation. Targeted review must reject tests that simply mirror source logic. Separate future dataflow, numeric, event, calibration, resource and real comparator qualification remains required; this rationale itself is not executable PASS.
