# C5 absolute-scale fallback diagnosis on development30

**POST-HOC DEVELOPMENT DIAGNOSTIC**  
**NOT FINAL EFFICACY**  
**NOT PARAMETER SELECTION**  
**NO METHOD CHANGE AUTHORIZED**

## Adjudication

**Classification: C. REAL BUT NON-DECISIVE LIMITATION.**

**Recommendation: OPTION 1 — KEEP TD-v1.3 WITH EXPLICIT LIMITATION.** No method amendment is executed or authorized by this report.

The `1e-12` input-scale fallback is a real and numerically material weakness: only 4.19% of primary selected-lambda eligible target values belong to affected channels, yet they contribute effectively all of the registered lambda-selection forecast loss, and affected channels set the extreme primary L calibration tail and threshold. However, affected channels are the system-maximum source in only a minority of scored bins, and lag3 raises L-MTL F1 from 0.0726 to 0.6508 while retaining exactly the same 288 affected scaler identities. Therefore the fallback is not sufficient, on saved evidence, to explain the primary L-MTL collapse or the G-versus-L gap.

This is not an implementation bug: the source implements the formula registered in TD-v1.3. It is also not strong enough evidence for a pre-freeze method amendment, because no registered run isolates the absolute fallback itself and the strongest within-artifact contrast (lag3) contradicts a single-cause explanation.

## Scope and evidence identity

The analysis is read-only over completed development artifacts. It does not refit, rescore, regenerate predictions, or open final60/F/G/H/I.

- Canonical project: branch `codex/rca-research-program`, HEAD `576be4b6935c9a837e6f2bcc6356a89bfe61c6ac`.
- Research workspace: branch `main`, HEAD `664d7180f0af3fadc8f11d7747b9d75833aeca34`.
- TD-v1.3 SHA256: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`.
- Primary run-contract SHA256: `cbcdff14c799c6be6fe4ef6c509d74365d4426a0b23f73236f87182a1dad0628`.
- Primary prediction-seal SHA256: `b2d01f6de1d584b35d27a5f6ff9ab9ecfbe26eb018e70e4ac717e5b422d634bf`.
- Sensitivity run-contract SHA256: `1933e9f0028d3abe313de92a95ccfa07f9c1800ba8b7f11f377d11e7652c94bc`.
- Sensitivity prediction-seal SHA256: `759bef0a51f040a2c68173fcc1dcaa4ff3e0ce8f8d389f8801bbf53fb2ce43f1`.
- Verified: 30 primary case seals and all 210 sensitivity case seals; all 90 primary and 630 sensitivity frozen-model/prediction/numeric-input artifact hashes matched their seals.
- Verified state: development30 `COMPLETE / PASS WITH LIMITATIONS`; method remains `CANDIDATE`, not human-approved/frozen; Phase 1 is closed and unchanged.

The calculation script decodes saved frozen-model and prediction arrays. It does not import the detector as an execution path and does not call fit, forecast, score, calibration, or selection routines.

## Source audit: what each floor and variant actually changes

### Input scale

`detection.py` constructs each qualifying input channel scaler as:

```text
location       = median(finite fit values)
iqr            = Q75(finite) - Q25(finite)
relative_floor = floor * median(abs(finite))
scale          = max(iqr, relative_floor, 1e-12)
```

The literal `1e-12` is therefore the **absolute input-scale fallback**. It is neither the relative floor nor the residual floor.

If `median(abs(finite)) = 0` and `IQR = 0`, the source evaluates all three registered relative-floor values as follows:

```text
floor in {.0001, .001, .01}
relative_floor = floor * 0 = 0
scale = max(0, 0, 1e-12) = 1e-12
```

Consequently, the relative-floor OFAT cannot vary the suspected zero-median/zero-IQR branch. This is proven both by source semantics and by exact affected-set identity in the saved artifacts.

### Residual scale

Residual normalization occurs later. The source computes calibration forecast errors and uses:

```text
residual_scale = max(IQR(calibration errors), residual_floor)
```

Changing `residual_floor` only changes this downstream error normalization. It does not alter the input scaler, input history, or `1e-12` fallback.

### Registered variants

| Variant | Field or mechanism changed | Kept unchanged for this diagnosis |
|---|---|---|
| primary | Baseline: bin5, lag1, fit/cal 24/12 bins, relative floor `.01`, residual floor `.01` | Registered TD-v1.3 primary |
| relative-floor `.0001` / `.001` | Multiplier on `median(abs(finite))` in input scale | Absolute `1e-12`, bin/profile, lag, residual floor, fit/cal support |
| bin10 | Bin width 5→10 seconds; fit/cal rows 24/12→12/6; gates 18/9→8/5 | Fit/cal duration remains 120/60 seconds; lag1; floor formula and floor values |
| lag3 | Lag 1→3; feature width 5→7; minimum fit rows 18→20 | Primary bin5 profile, fit/cal windows, input-scaler formula and both floor values |
| prefix240 | Fit/cal rows 24/12→32/16; gates 18/9→24/12 | Bin5, lag1, scale formulas and floor values |
| residual-floor `.001` / `.1` | Downstream residual-scale lower bound | Input scaler E, its `1e-12` fallback, bin/profile, lag |

For G, L, and ALL, the saved input tensor E, scaler locations/scales, qualifying target mask, and model mask are common. The arms differ in active predictors: L uses own lag history, G adds graph-neighbor context, and ALL adds all-other-node context. Therefore G-versus-L is confounded by additional context/capacity and is not a pure graph-structure contrast.

## Q1 — Where and how often does `1e-12` occur?

In primary MTL there are **288 affected case×node×channel scalers out of 6,913 qualifying scalers (4.1661%)**, present in **30/30 cases**.

| Channel type | Affected scalers | Share of affected |
|---|---:|---:|
| Metric | 228 | 79.17% |
| Trace-count | 35 | 12.15% |
| Log-count | 25 | 8.68% |
| **Total** | **288** | **100%** |

Of the 228 metric scalers, 227 are the `error` metric and one is `workload`. The affected-count distribution per case is median 8.5, IQR [5.25, 13.75], range [2, 20].

Affected scalers occur on 27 service/node identities. The ten most frequent are:

| Service/node | Affected scalers |
|---|---:|
| `ts-preserve-other-service` | 35 |
| `ts-admin-travel-service` | 29 |
| `ts-preserve-service` | 20 |
| `ts-travel-service` | 17 |
| `ts-food-service` | 16 |
| `ts-order-other-service` | 15 |
| `ts-basic-service` | 15 |
| `ts-ticketinfo-service` | 15 |
| `ts-travel2-service` | 13 |
| `ts-admin-basic-info-service` | 13 |

These account for 188/288 affected scalers; the other 100 are spread across 17 services. The prevalence is therefore broad rather than confined to one node.

All 288 affected scalers have stored center zero and recomputed IQR zero. Support-row count is median 24, IQR [24, 24], range [1, 24]. There are 222 constant and one singleton affected scalers. Among the 60 affected count channels, positive fit observations have median 4, IQR [3, 5], range [1, 5]. Thus this is primarily a zero-baseline/sparse-channel phenomenon, not simply missing support.

The registered primary model mask includes **287/288** affected scalers as targets in every arm; the extreme-scale channel is not generally excluded from G, L, or ALL.

## Q2 — Does it dominate lambda-selection forecast loss?

Yes, numerically and across all three arms.

At selected lambda 10, the exact saved objective is `7,051,117,096.1786375`; the deterministic recomputation matches it within the script's strict tolerance. The evaluator is linearly decomposable using its actual hierarchy: channel mean within bin, bin mean within case, case mean within scenario, scenario mean, then equal-arm mean. Using the same eligible IDs and denominators:

- affected eligible targets: **92,988 / 2,216,814 = 4.1947%**;
- affected contribution to the selected-lambda objective: **99.9999999846%**;
- affected share of raw absolute forecast loss: **99.9999999853%**;
- the 60 affected trace/log count scalers alone contribute **99.8803%** of the objective;
- affected metric scalers contribute about **0.1197%** of the objective.

The dominance is not isolated to a single arm: affected contribution fractions are approximately 99.9999999845% for G, 99.9999999845% for L, and 99.9999999847% for ALL. It also persists across every registered lambda candidate, so it is not an artifact of selecting lambda 10.

Interpretation: the registered forecast-loss objective is overwhelmingly an extreme-scale/sparse-count objective. This does **not** by itself prove that the downstream detector F1 or arm ordering is caused by the same channels.

## Q3 — Does it usually dominate the system maximum residual?

No. It is material and especially concentrated in L, but it is not the maximum source in most bins.

Tie attribution compares the saved system score to every eligible channel residual at that bin. Bins are classified as `AFFECTED_ONLY`, `UNAFFECTED_ONLY`, or `MIXED_TIE`; no mixed affected/unaffected ties occur in these selected primary configurations.

| Primary detector | Affected-only max bins | Scored bins | Share |
|---|---:|---:|---:|
| G-MTL | 398 | 7,560 | 5.2646% |
| L-MTL | 898 | 7,560 | 11.8783% |
| ALL-MTL | 264 | 7,560 | 3.4921% |
| G-MT | 310 | 7,560 | 4.1005% |
| L-MT | 690 | 7,560 | 9.1270% |
| ALL-MT | 203 | 7,560 | 2.6852% |
| **All six** | **2,763** | **45,360** | **6.0913%** |

Across MTL only, affected channels account for 1,560/22,680 = **6.8783%** of maxima. In L-MTL, the 898 affected maxima consist of 88 metric, 222 trace-count, and 588 log-count maxima. The affected maximum rate is therefore elevated in L relative to G/ALL and relative to the affected eligible-ID fraction, but 88.12% of L-MTL bins still have an unaffected maximum source.

## Q4 — Are extreme thresholds directly associated with affected channels?

Yes for the extreme primary L thresholds; not uniformly for G/ALL.

- L-MTL full threshold: **`2.2169492719693778e14`**. Its exact threshold-setting score is tied across eight saved bin occurrences of affected `ts-preserve-service|log-count` in case `re2tt_ts-order-service_loss_1`. The entire weighted upper calibration tail at or above the threshold is `AFFECTED_ONLY`.
- L-MT full threshold: **`1.5889e14`** (rounded). Its exact source is an affected trace-count channel for `ts-preserve-other-service`; the weighted upper tail is also 100% affected.
- G-MTL full threshold: **5,300.8444**. The exact threshold source is unaffected; affected-only bins carry 33.74% of the weighted upper tail.
- ALL-MTL full threshold: **4,361.7021**. The exact threshold source is unaffected; affected-only bins carry 11.70% of the weighted upper tail.

This is strong association between the fallback and primary L threshold inflation. It is not causal identification of the complete L behavior, and the saved TV artifact is not decomposed to node-channel identity, so the same attribution is not claimed for TV.

## Q5 — Does registered relative-floor sensitivity test the pathology?

**No.** Primary `.01`, `.001`, and `.0001` have the exact same set of 288 `scale=1e-12` identities. They also have the same L-MTL affected-max count (898/7,560), the same L-MTL full threshold (`2.2169492719693778e14`), and the same L-MTL F1 (`0.0725547478`).

The variants can change scales for nonzero-baseline channels and can therefore change G/ALL results, but they do not perturb the zero-median/zero-IQR fallback being diagnosed. The existing OFAT should not be cited as evidence that the absolute fallback was stress-tested.

## Q6 — Does bin10 improve L-MTL by reducing the pathology?

Bin10 is **consistent with** a large reduction in sparse-count manifestations, but it is not a causal isolation.

| Quantity | Primary/bin5 | bin10 |
|---|---:|---:|
| `1e-12` scalers | 288/6,913 (4.1661%) | 240/6,912 (3.4722%) |
| Affected metric scalers | 228 | 227 |
| Affected trace/log count scalers | 60 | 13 |
| L-MTL affected max bins | 898/7,560 (11.8783%) | 95/3,780 (2.5132%) |
| L-MTL full threshold | `2.2169e14` | 6,893.94 |
| L-MTL F1 | 0.0726 | 0.6521 |

The bin10 affected set removes 48 primary identities and adds none; Jaccard overlap is 0.8333. The 78.3% drop in affected count-channel scalers, lower max dominance, finite-scale threshold, and higher L-MTL F1 move together.

However, bin10 simultaneously changes the aggregation width, number of fit/calibration rows, row gates, scored-bin count, and the time-series representation. It does not isolate the fallback. The correct conclusion is association, not “bin10 proves that reducing `1e-12` fixes L.”

## Q7 — What does lag3 show?

Lag3 retains **exactly the same 288 affected scaler identities** and the same 4.1661% prevalence as primary. Nevertheless:

- L-MTL F1 rises from **0.0726 to 0.6508**;
- L-MTL affected-max share falls from **11.8783% to 4.6429%** (351/7,560);
- L-MTL full threshold falls from **`2.2169e14` to 8,421.05**;
- affected modeled targets remain 287, while total models change only from 6,851 to 6,808;
- L active predictors increase from mean 0.946 to 2.833 and effective degrees of freedom from 1.085 to 1.219.

The input-scale pathology is unchanged. What changes is history/feature construction and the fit-row gate. Lag3 therefore shows that a model/history change can avoid downstream dominance by the same affected targets without removing their `1e-12` scales.

## Q8 — Is `1e-12` sufficient to explain primary L-MTL collapse?

**No.** It is a plausible contributor to the extreme primary L calibration and a decisive contributor to lambda forecast loss, but unchanged affected-scale prevalence coexists with L-MTL F1 0.6508 under lag3. The fallback is therefore not a sufficient explanation for primary L-MTL F1 0.0726.

Two additional registered observations reinforce the distinction:

- prefix240 retains near-primary prevalence (284/6,927, 4.0999%) and L-MTL remains low at 0.0841;
- residual-floor `.001`, `.01`, and `.1` retain the same affected input identities and the same L-MTL F1, while the L threshold rescales by factors of ten. This is downstream scale/calibration behavior, not a repair of the input-scale branch.

Saved evidence cannot estimate the counterfactual F1 under a different absolute input floor because no registered variant changes it, and this diagnosis deliberately does not create one.

## Q9 — Can G-versus-L be attributed specifically to graph structure?

**No.** All arms receive the same normalized E tensor and model the same extreme-scale targets, but their predictor capacity differs materially:

| Primary MTL arm | Mean active predictors | Mean effective df | Macro F1 |
|---|---:|---:|---:|
| L | 0.946 | 1.085 | 0.0726 |
| G | 2.201 | 1.196 | 0.6700 |
| ALL | 3.213 | 1.271 | 0.6909 |

G adds graph-neighbor context, while ALL adds non-graph all-other-node context; ALL exceeds G in primary. The evidence supports an **additional-context/capacity effect**, not an identified graph-structure effect. G and ALL do not avoid the affected channels; they forecast or calibrate them differently using more context.

## Q10 — Keep TD-v1.3 or propose amendment?

**KEEP TD-v1.3 WITH EXPLICIT LIMITATION.** The exact limitation that should accompany development interpretation is:

> On development30, the absolute `1e-12` input-scale fallback applies to zero-median/zero-IQR channels. About 4.19% of selected-lambda eligible target values from those channels contribute effectively all registered lambda-selection MAE and affected channels set the extreme primary L calibration tail/threshold. The registered relative-floor OFAT does not vary this fallback. However, affected channels are system-max sources in a minority of scored bins, and identical fallback prevalence coexists with high L-MTL performance under lag3. The fallback is therefore a real numerical and interpretive limitation, not a demonstrated sole cause of primary L collapse or graph-specific gain.

This recommendation preserves all TD-v1.3 development results and does not promote a method change. The next evidence check, if separately authorized before freeze, should first ask whether the scientific claim needs causal isolation of the absolute fallback; it should not be framed as a search for a better score or a preferred floor. No such diagnostic is designed or run here.

## Evidence for, evidence against, and uncertainty

### Evidence for material pathology

1. `1e-12` is reached by the registered formula for 288 zero-center/zero-IQR scalers in every development case.
2. Affected values are only 4.1947% of lambda-eligible targets but contribute 99.9999999846% of the selected-lambda objective.
3. Affected sparse count channels alone contribute 99.8803% of that objective.
4. Affected channels directly set the extreme primary L-MTL and L-MT thresholds and occupy 100% of their weighted upper calibration tails.
5. Their system-max incidence is higher in L than in G/ALL.

### Evidence against a decisive or single-cause interpretation

1. Only 6.0913% of all primary scored maxima, and 11.8783% of L-MTL maxima, are affected-only.
2. Lag3 keeps the exact affected set but raises L-MTL F1 from 0.0726 to 0.6508 and removes extreme threshold behavior.
3. G, L, and ALL share the affected inputs and targets; arm behavior differs with contextual feature capacity.
4. ALL exceeds G in primary, preventing a graph-specific attribution.
5. Bin10 co-varies several mechanisms and cannot isolate input scaling.
6. Relative-floor and residual-floor variants do not perturb the absolute fallback branch.

### Uncertainty

- No registered artifact varies only the absolute input fallback, so its causal effect on F1 cannot be identified from saved runs.
- Channel-level forecast-loss decomposition is exact for the registered linear objective, but it does not establish causal responsibility for nonlinear max-score and threshold outcomes.
- Development30 is a small development sample; all correlations and cross-variant comparisons here are **EXPLORATORY / POST-HOC / NOT CAUSAL**.
- TV maxima cannot be assigned to node-channel scalers from the saved TV representation and are not included in channel-level dominance claims.

## Epistemic status and governance

- **FACT:** source formula semantics, artifact hashes/seals, affected counts, exact evaluator recomputation, thresholds, F1 values, and max-source attribution from stored arrays.
- **CANDIDATE:** classification C and the recommendation to retain TD-v1.3 with the stated limitation, pending Minh's decision and any human review required before freeze.
- **OPEN:** whether a separately authorized, pre-registered absolute-floor diagnostic is necessary for the intended thesis claim. This report neither proposes candidates nor authorizes execution.

No durable project decision was promoted. No TD/config/method source was mutated.

## Artifacts created

1. `analysis.py` — deterministic read-only verification and aggregation.
2. `scale-summary.csv` — 1,440 aggregated case/config/arm/modality rows; no million-row channel dump.
3. `report.md` — this adjudication.

No completed run directory was modified. Phase 1 artifacts remain byte-identical.

PHASE 2 COMPLETE — WAITING FOR MINH.  
NO METHOD AMENDMENT EXECUTED.  
FINAL60 UNTOUCHED.
