# Task D — Executed-Identity and Documentation Consistency Audit

> **DOCUMENTATION-ONLY AUDIT OF EXECUTED TD-v1.3**  
> **DOES NOT MODIFY METHOD SEMANTICS**

Canonical source: `D:/Project/flash-ticket-platform/docs/research-rca/task-d-method-and-experiment-specification.md`  
Required SHA256 before documentation writes: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`  
Required SHA256 after documentation writes: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`

Status: `CANDIDATE` audit for independent assurance and Minh's decision. Canonical TD wins every conflict.

## 1. Scope and method

The audit cross-checked the 64-row defense matrix, 43-answer defense Q&A and defense-readiness report against the canonical TD, `CURRENT-STATE.md`, completed-development handoff/preflight, and Phase 1/2 reports. Checks covered PPR direction and zero-mass behavior, isolate semantics, damping, selected-development wording, temporal pooling, all floor types, G/L/ALL, lag/lambda/q rights, MRR/ties/failures, R budgets, final60 firewall and FlashTicket scope.

No executable source, TD byte, config, completed run or post-hoc result was changed.

## 2. Issues found and documentation-only corrections

| # | Source statement | Conflicting statement | Canonical ruling | Documentation-only fix | Method semantics changed? |
|---:|---|---|---|---|---|
| 1 | TD §5: `sum(l)=0 -> common all-tie/no-evidence, never silent uniform PageRank` | Matrix: `fallback uniform if mass is zero` | Zero local mass produces the common no-evidence tie; uniform-positive personalization is diagnostic only | Rewrote the matrix row to state the exact positive-mass formula and no-uniform zero-mass behavior; companion repeats the boundary | **NO** |
| 2 | TD §7: `mu_e=median(e)`, `s_e=max(IQR(e), epsilon_e)`, `epsilon_e=.01`, `r=max(0,(e-mu_e)/s_e)` | Matrix applied an input-style relative/absolute formula to residual scale | Residual floor is an absolute downstream floor, separate from input `epsilon_rel` and input `1e-12` | Replaced the matrix formula and defense text with the exact TD residual formula | **NO** |
| 3 | TD §9: signal starvation when `>=80%` planned final incidents have empty `V` or identical rounded normalized local values; all-zero separate | Matrix/report described it as fewer than 80% cases being eligible | It is a local-signal informativeness gate, not generic case eligibility | Corrected matrix and report; companion gives exact role/claims | **NO** |
| 4 | TD §7.2: `TV_c=MEAN` over valid squared edge differences and `S=max_c TV_c` | Matrix named unnormalized `x^T L x` as the exact detector | Laplacian TV is lineage; the executed operator uses mean edge variation and a channel maximum | Corrected the matrix exact choice and transfer limitation | **NO** |
| 5 | TD §§7/7.0a: L has own lag with context slots zero; G has own lag plus graph context; ALL has own lag plus all-other context; capacities differ | Q&A shorthand could be read as G lacking own history and ALL merely adding it | Own lag is common; context sets/effective capacities differ | Rewrote Q&A answers 24–25 with exact feature semantics and attribution limit | **NO** |
| 6 | DT18 and TD §12: FlashTicket is the target system for application, integration and later validation; public data does not replace it | Q&A called FlashTicket a place to run the mechanism and “minh họa tích hợp” | FlashTicket is target-system controlled transfer/validation, not demo-only; efficacy is still unmeasured | Rewrote Q&A answer 41 and added the target-system role to the companion | **NO** |
| 7 | TD §2 exposure ledger: E1 already saw TT90 baseline outcomes and post-hoc fusion/strata; claim only prospectively frozen new contrasts on a previously studied benchmark | Matrix called final60 a larger “untouched” final set | Current-method final60 predictions/labels are unopened, but the benchmark is not clean or untouched | Corrected matrix and Q&A final60 wording; companion now carries the exposure boundary | **NO** |
| 8 | TD §§2–3: lambda uses pre-injection numeric loss inside a declared study-specific supervised regime | Matrix called lambda selection `label-free` without qualification | It avoids incident outcome labels but is not wholly label-free development | Corrected matrix purpose/claim/defense wording | **NO** |
| 9 | TD §§8/13: a material pre-freeze change may return to D for versioning/review/exposure logging before G | Matrix/Q&A implied any post-development change consumes the final60 firewall | A reviewed amendment increases development exposure but does not itself open final60; silent outcome retuning remains prohibited | Corrected matrix governance row, Q&A answers 11/38 and companion boundary | **NO** |

**Issue count: 9 documentation inconsistencies; 0 method-semantic changes; 0 scientific blocker found by the author audit.** Issues 7–9 were identified by independent assurance and corrected by the author before follow-up assurance. The final blocker judgment is reserved for independent assurance and Minh.

## 3. Required consistency checks with no conflict

| Check | Canonical result | Audit result |
|---|---|---|
| PPR raw/processing direction | Raw caller `u->v`; primary reverse-call or registered undirected variant | Consistent after correction |
| Isolate semantics | Row-stochastic isolate self-loop; numerical/topological completion only | Consistent |
| Damping | `{.2,.5,.85}`; `.85` prior reference, `.2/.5` study grid; development selected undirected `.5` | Consistent; no optimality claim |
| Q90/max | Temporal Q90 primary; metric-channel max/Q90 registry; selected Q90; max diagnostics/sensitivity | Consistent |
| Windows/bins | C1 300/300 s with bin10 primary; C5 bin5/180 s primary; bounded registered sensitivities | Consistent; no universal-optimum claim |
| Input/relative/absolute/residual floors | Input uses IQR, relative floor and `1e-12`; residual uses `max(IQR(e), epsilon_e)` | Consistent after correction |
| G/L/ALL | Own lag is common; L zeros context, G uses graph context, ALL uses all-other context; effective capacities differ | Consistent after correction |
| Lag | lag1 primary, lag3 sensitivity; sensitivity does not replace primary | Consistent |
| Lambda/q rights | lambda selected from registered grid using pre-injection loss; q from registered grid using training normal scores and held-out development macro F1 | Consistent |
| MRR/ties | Planned-denominator tie-aware MRR; expected RR across tie interval | Consistent |
| Root absent/failure/all-tie | Root absent or method failure scores zero; valid all-tie is not method failure | Consistent |
| R | 256 chains; `200*max(1,E)` proposals primary; topology-only 100/200/400E sensitivity | Consistent |
| Final firewall/exposure | Current-method final labels open only after sealed predictions and no final tuning; historical TT90 outcome exposure remains disclosed | Consistent after correction; never described as clean/untouched |
| FlashTicket | Target-system controlled transfer/validation remains future authorized work; no efficacy claim yet | Consistent after correction |
| Phase 1 | O below L; 17/17 local-rank1 retained; strong-local-harm hypothesis not supported; no graph gate | Consistent |
| Phase 2 | `1e-12` real but non-decisive; relative-floor OFAT does not test it; lag3 counterevidence; G/L capacity confounding | Consistent |

## 4. Identity and evidence-chain ruling

- Executed TD identity before documentation write: `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`.
- Executed TD identity required after every documentation/assurance write: the same hash.
- Canonical TD was not edited by the authoring step.
- Completed Task E, Phase 1 and Phase 2 artifacts were not edited.
- Corrections were limited to derived defense documentation and the two new companion/audit artifacts.

## 5. Remaining authority

This audit does not approve/freeze the method or authorize Task F/final60. Independent assurance must rule on semantics, overclaim, provenance, negative-result disclosure, firewall and readiness. Minh alone decides human approval/freeze.
