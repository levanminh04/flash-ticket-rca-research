# Independent scientific interpretation review — Task E

Reviewer: native agent `/root/final_scientific_review`. Review state: **SCIENTIFIC REVIEW CLOSED — RECOMMEND PASS WITH LIMITATIONS**, 2026-09-28. The separate final RCD numerical/leakage receipts are verified and close the last condition on this scientific recommendation. Recommendation remains CANDIDATE for coordinator adjudication. This is the scientific interpretation role for authorized development preflight, not formal five-independent-agent assurance or human final acceptance. No model execution, new search grid, final60 access, application/legacy edits, commit or push was performed by this reviewer.

## Authority and method

Read P `AGENTS.md`, full governance skill and authority/gates reference, DT18 mission, roles, TD-v1.3 canonical method, U27/U27R development/amendment missions. Class: REVIEW / FORMATION. P is canonical; W is explicitly authorized experimental evidence storage. P HEAD `3d7ec9d824d12c98dc233705ef50908b62adf235`, branch `codex/rca-research-program`; W HEAD `f49859df7664758f1143a1033535da7f6f29d7d6`, branch `main`, observed 2026-09-28. Existing unrelated/other-agent changes are untouched. Only this report is reviewer-owned.

Observations below are FACT about saved development artifacts. Scientific interpretations and verdict recommendations are CANDIDATE, not approved method decisions. Absence of an observed defect in this review is not proof of universal correctness or absence of leakage.

## Verified inputs and bounded observations

Directly inspected primary JSON data, per-case metrics, selected-configuration curves, grouped effects/precision, C5 evaluation/calibration/events, all 30 C5 capacity seals, numerical input/frozen-model/prediction schemas, and the ridge/scaling code path. Did not rely on coordinator outcome interpretation.

| Evidence | SHA256 |
|---|---|
| `e27-033-c1-development-full/c1-results.json` | `eeeb0a09f43281d1df649a1b74e352d484796263bd3fb921aadb1c634e1c1e3d` |
| `e27-033-c1-development-full/selection.json` | `b573102a18763eecd235ca2450438e265c2404c990a0180be6164af9806ea754` |
| `e27-035-c5-development-full/c5-selection.json` | `4e56b27a2e044774f2fc4021f64a7d093f66dfaeb0c9dd019955d53f246f343c` |
| `e27-035-c5-development-full/c5-summary.json` | `bdf98053c313e1ba41f0146113cc61684d6ae3dd051dc1a09159935dc6c460fd` |
| `e27-036-c1-development-sensitivity/c1-sensitivity.json` | `0e955b12ad6977a9b2ce7f7b80db211c6e3c87aebe45250bb673227befd3648b` |
| `e27-023-development-input-summary/actual-use-input-summary.json` | `96c3409bca5b1f486a94d0114909bade04e8b98dd8010b769173ce92a5d1c94d` |
| `e27-022-development-topology/topology-summary.json` | `b188513f46e48c20754fe94df1b9fdaebb1a3395b4b4ca635d9abd73dd5a40db` |

### C1

Selected common local policy is floor .01 / channel Q90 / availablemean. Primary PPR is undirected d=.5; secondary diffusion is undirected .85. Local absolute-MRR margin is .005806; primary PPR margin .001557. Leave-cell local winner is unchanged in 9/10 deletions, PPR in 7/10, diffusion in 9/10. These are small, selection-exposed margins, not robustly identified optimal parameters.

| Arm | MRR | Hit1 | Hit3 | Hit5 | NDCG5 |
|---|---:|---:|---:|---:|---:|
| L | .744206 | .566667 | .900000 | .933333 | .786968 |
| O | .702405 | .566667 | .800000 | .833333 | .726779 |
| mean R | .678235 | .566667 | .742708 | .800000 | .696040 |
| Diffusion | .720162 | .600000 | .833333 | .866667 | .752844 |
| mean R diffusion | .696729 | .585807 | .793750 | .828255 | .722158 |
| BARO adapter | .659120 | .533333 | .733333 | .900000 | .709459 |

Delta O-L=-.041801; O-R=.024171. Conditional 97.5% paired-cell development intervals are [-.126229,.055841] and [-.005774,.079596], both crossing the registered .05. Thus this is **not bounded support**, and these diagnostic intervals also do **not establish the registered bounded-negative criterion**. The observed negative mean is a valid negative development observation; calling it a conclusive negative experiment would overstate it. Historical benchmark exposure, selection on these ten development cells, crossed root/fault dependence and shared campaign limit inference. 30 incidents, 256 perturbations and 50,000 bootstrap resamples are not independent campaigns.

L is informative and strong but not at a global ceiling: 17/30 Hit1, .255794 possible MRR headroom. The failure to improve cannot be excused solely by no room to improve. Root-rank gains/losses are sparse: O-L improves two cases, worsens six and leaves 22 unchanged. Travel/loss is the only positive cell, +.252381; auth/delay=-.225556. Removing auth leaves O-L=-.004890; removing travel leaves -.083799. O-R gain is concentrated in loss; deleting the loss fault makes O-R=-.003609. Aggregate MC SE .000463 is much smaller than .024171, but reducing random-draw noise does not resolve heterogeneity or incident uncertainty.

Development cells do not fully cross roots and fault types: mem/socket only route, cpu/delay only auth/train, disk/loss only order/travel. A descriptive fault effect therefore cannot be separated cleanly from root identity, graph position or campaign condition. The split does not establish unseen-service, unseen-fault-family or independent-system generalization. Degree/component-preserving R controls do not preserve every path, spectrum or centrality statistic; O-R isolates this declared finite-perturbation contrast, not a causal relation effect purified of every topological nuisance.

Input audit has root visible 30/30, no query-only nodes and no reported trace-key conflicts; 24 cases have 27 nodes/55 edges/1 isolate, six have 20 nodes/20 edges/2 isolates. Parent-resolution range includes .8355, so high resolution is not universal or topology recall. R mobility passes the descriptive development gate in every case for both representations at all three budgets; it is not mixing proof or the future final gate. Missing logs in one case do not veto primary M/T. The separate numerical and firewall reviews provide bounded checked correctness for their completed scopes, as recorded below.

Mandatory C1 OFAT saved effects O-L: bin5 -.161283; bin20 +.001243; horizon180 -.046140; horizon420 -.010067; floor .0001 -.023948; floor .001 -.059993; temporal-max -.047648; old-cap20 -.120716; old fixed fusion -.041801. The sign flip at bin20 is tiny and still far below .05; it does not rescue the primary. Absolute L varies materially (e.g. .498343 at 5s vs .752963 at 20s), exposing representation/window dependence. All registered PPR O scores remain below selected L. Secondary diffusion does not rescue the primary or establish a result about all graph families.

### C5 primary development

All eight detector arms have 30/30 scored cases, 7,560/7,560 scored evaluable bins (3,240 normal and 4,320 injected), zero unavailable bins, zero execution failures. Each threshold-training fold has 24/24 normal-scored cases and 2,592 normal endpoints; full calibration has 30 cases / 10 scenarios / 3,240 endpoints. The coverage/calibration gates pass on this saved scope. These are injection-regime proxy labels, not independently certified healthy/anomalous onset or causal-node truth.

| Arm | macro precision | macro recall | macro F1 | q | full-refit threshold |
|---|---:|---:|---:|---:|---:|
| G-MTL | .798049 | .649537 | .669994 | .95 | 5300.844 |
| L-MTL | .170600 | .050231 | .072555 | .95 | 2.216949e14 |
| ALL-MTL | .807611 | .668750 | .690865 | .95 | 4361.702 |
| G-MT | .806515 | .665509 | .688862 | .95 | 4361.702 |
| L-MT | .175208 | .048611 | .072001 | .95 | 1.588908e14 |
| ALL-MT | .806515 | .664583 | .687474 | .95 | 4361.702 |
| TV-MTL | .293692 | .048611 | .078600 | .95 | 2.405175e24 |
| TV-MT | .321157 | .043519 | .074813 | .95 | 1.165049e24 |

The large G-L gap does not identify a graph-specific benefit: ALL-MTL exceeds G-MTL, and MT G/ALL are almost equal. Equal planned/actual target coverage prevents explaining this gap merely by dropping hard cases in one arm, but effective capacity/regularization differ. Across cases at lambda10, mean active columns/model: G-MTL 2.195, L-MTL .946, ALL-MTL 3.219; mean effective ridge df including intercept: 1.194, 1.085, 1.264. G/L/ALL model count is identical per case within modality (176–252 MTL;162–232 MT). ALL duplicated features and G sparse neighborhoods preclude a capacity-matched pure topology claim.

The common lambda10 objective is ~7.051117e9, with margin 145990 (~.0021% of its magnitude); leave-cell reselection chooses lambda1 in six deletions and lambda10 in four. All q selections remain .95 in ten leave-cell cascades. Thus threshold quantile choice is stable inside the finite grid, while lambda is not; high loss magnitude and tiny relative margin need floor/scale attribution, not a claim of a well-established optimum.

Scores/scales require careful interpretation: MTL prefix scale floors average 50.63 channels/case, constants 12.53; G residual floor use 31.5 channels/case versus L 36.13; largest per-case residual scales reach ~2.4e12. Very large finite values are allowed by uncapped TD mathematics, not by themselves a numerical bug. Model availability averages 228.37 of 230.43 applicable MTL channels; system availability does not imply every service/channel is modeled.

**Raw-array scale attribution, independently recomputed without model execution:** load each of the30 saved `frozen-models.npz` and `predictions.npz`; take selected lambda10 MTL arrays; use pre-injection endpoint mask and equal case→bin→finite-channel averaging. This reproduces saved losses to floating precision: G7,021,877,238.464475; L7,010,433,685.533825; ALL7,121,040,364.537610. Channels with frozen prefix scale exactly1e-12 account for respectively .9999999998450, .9999999998447 and .9999999998473 of those weighted losses. Thus the common lambda criterion is overwhelmingly dominated by the absolute-floor channels; the near-tie does not show an empirically stable, broadly representative optimum. The L normalized forecast objective is slightly lower than G/ALL despite its far lower detector F1: the F1 gap must not be rewritten as a general improvement in forecasting accuracy.

For L-MTL,159 normal bins exceed the full-refit descriptive threshold; first-max source channel is LOGCOUNT in156 and TRACECOUNT in3. Across those159 winners, service counts are121 `ts-preserve-other-service`,37 `ts-preserve-service`, one `ts-payment-service`. G/ALL normal-tail sources are mainly latency-90, with a smaller LOGCOUNT component. Across all7560 endpoints, G/L/ALL first-max ties occur31/31/36 times; first-max source counting is descriptive, not unique causal attribution. Sparse fit-count channels can meet the positive-observation eligibility rule yet have median/IQR zero, giving the prescribed1e-12 scaler. This is a **severe observed method/data weakness** in scale-based selection and max-score calibration, not proof of leakage or numerical failure. Existing registered prefix/lag/residual-floor sensitivity must characterize it. It does not authorize post-result clipping, dropping these channels or changing lambda selection to make the graph win.

C5 heterogeneity is material: G-MTL cell F1 ranges .047849 (auth/delay) to .985907 (train/cpu); auth/cpu=.197462, while several disk/train cells are near .98. Do not present only pooled F1=.770244 in place of planned macro=.669994. MT slightly outperforms MTL for G; added logs have no demonstrated universal benefit.

Using OOF thresholds and fixed event policy, G-MTL emits 17 pre-injection triggers in14 cases across4.5 observed/scored normal hours, reaches a post-injection trigger in26/30 cases, conditional median delay60s, range20–665s. ALL-MTL:15 pre-triggers/13 cases,26 post-trigger cases, median40s,range20–360s. L-MTL:6 pre-triggers/5cases,4post-trigger cases; TV-MTL only1post-trigger case and TV-MT none. These are bounded archival event statistics; the conditional median excludes censored cases and must always carry26/30. Raw-bin F1 is not trigger utility or a production false-alarm guarantee.

### Integrated trigger-to-ranking evidence —038 COMPLETE

Directly inspected `e27-038-integrated-development/integrated-results.json`, SHA256 `2bd64082f30f7a356bc5b6e69ecd9f12346946a36e73c33ed3a14a0167181b18`, execution exit0. All30 planned cases remain in each of eight summaries. Arm name identifies the detector; **every arm uses the same selected PPR/MTL diagnosis after triggering**. Thus integrated L-MTL is not a local-only ranking baseline and this is not another C1 relation-effect estimate.

| Detector feeding common diagnosis | Planned MRR | Hit1 | Hit3 | post-trigger valid cases |
|---|---:|---:|---:|---:|
| G-MTL | .470935 | .400000 | .500000 |26/30|
| G-MT | .469988 | .400000 | .500000 |26/30|
| ALL-MTL | .511869 | .433333 | .566667 |26/30|
| ALL-MT | .497766 | .433333 | .533333 |26/30|
| L-MTL | .011483 | .000000 | .000000 |4/30|
| L-MT | .013828 | .000000 | .000000 |5/30|
| TV-MTL | .008333 | .000000 | .000000 |1/30|
| TV-MT | .000000 | .000000 | .000000 |0/30|

G-MTL conditional MRR on the26 valid cases is .543386; it must not replace planned .470935. G-MTL has80 total trigger diagnoses,74 valid and6 INSUFFICIENT_HISTORY. First post-injection cases have adequate history; the four absent post-injection triggers remain0. Five cases later obtain a better RR than the first post-injection diagnosis; the saved first-only rule does not let these rescue composition. All pre-trigger history limitations are retained.

Composition still has strong cell heterogeneity: G-MTL cell MRR1.0 for order/disk and travel/disk, .027222 auth/delay and .037582 route/mem. ALL-MTL improves chiefly order/loss (.530303 versus G-MTL .111500). Useful trigger coverage does not imply accurate diagnosis of every fault. The gap from known-window C1 is not an isolated detector cost: query horizon, window placement, log inclusion and planned missing-trigger penalties also differ. This supports executable bounded composition and limitations, not production readiness or graph-specific superiority.

### C5 registered sensitivity —037 COMPLETE

Directly inspected `e27-037-c5-development-sensitivity/sensitivity-summary.json` SHA256 `3af4aed5b0ad72c3b0f0654b76932239130fb3f47625ad1ab0ee0e20f2b55659`, `c5-summary.json` SHA256 `47e66e73e54835b77279a1c37542d0e054481b0abf7a41835dcfa6ba2de88bfb`, and per-detector grouped evaluation/event files. Exit0; all210 planned case-variant runs complete; zero input-unavailable, prediction-failure or TV-failed case runs. All56 detector/variant summaries are VALID with30 scored cases and zero unavailable evaluable bins. Primary registry remains unchanged; selected lambda/q are held fixed with the declared per-variant calibration, not replaced by the best sensitivity result.

| MTL variant | G macro F1 | L macro F1 | ALL macro F1 | G−L | G−ALL |
|---|---:|---:|---:|---:|---:|
| Primary | .669994 | .072555 | .690865 | .597439 | −.020872 |
| 10s bin / registered fit-calibration gates | .661715 | .652055 | .665116 | .009660 | −.003401 |
| 240s prefix | .740912 | .084072 | .747319 | .656839 | −.006407 |
| Own lag3 | .679172 | .650814 | .656562 | .028358 | .022610 |
| Residual floor .001 | .608138 | .072555 | .618152 | .535583 | −.010014 |
| Residual floor .1 | .684615 | .072555 | .703017 | .612060 | −.018402 |
| Relative floor .0001 | .438039 | .072555 | .437744 | .365484 | .000294 |
| Relative floor .001 | .576171 | .072555 | .609233 | .503617 | −.033062 |

**Material interpretation:** the large primary G−L detector gap nearly disappears under10s bins or a richer local lag history; L full-refit threshold becomes6893.942 or8421.053, versus primary2.216949e14. G−L remains positive on this finite grid, but its magnitude is profoundly sensitive to temporal representation, local capacity and calibration. The primary result does not show graph context is necessary for useful detection. G−ALL changes sign and its small primary MT advantage also reverses in several variants; observed adjacency is not a consistently superior predictor restriction. These results reinforce the scale/capacity explanation above; they do not justify silently replacing the primary.

Grouped evidence shows what moves: at10s, L rises to .9812 order/disk, .9324 train/cpu, .9814 train/delay and .9704 travel/disk, comparable to G; auth/delay remains poor (.0267 L/.0516 G). At lag3 L is .7712 route/mem versus G .6542, but .4185 route/socket versus G .6330. At relative floor .0001 G order/disk falls from .9769 to .1257 and travel/disk from .9815 to .3347, while train/cpu stays .9883. This is structured channel/temporal sensitivity, not a universal loss of available data. Increasing the prefix benefits route/mem and travel/loss but does not establish independent healthy-prefix truth or a transferable threshold.

Event-only diagnostics also remain distinct from bin F1 and parameter selection. With primary G-MTL scores, streak1/3/5 at refractory300 give82/80/76 total triggers,17/17/12 pre-injection triggers and26/30 post-trigger cases throughout. Refractory60/300/600 at streak3 gives271/80/52 total triggers and21/17/14 pre-injection triggers;26/30 post-trigger cases remain, conditional median delay37.5/60/107.5s. L-MTL post-trigger cases fall9→4→0 for streak1→3→5, while TV-MTL falls16→1→0 with30→1→0 pre-triggers. Thus raw exceedance quality is insufficient to claim useful sustained alerts; changing persistence can trade sparse detections against pre-injection alarms. Nonmonotonic conditional delays are possible because pre-injection triggers change refractory state; a longer streak is not an independently monotone onset estimator. No event variant is adopted here.

Severity adjudication: **material method/data weakness and expected claim limitation**, not an identified execution bug. D already requires reporting these sensitivities and permits valid unstable/negative methods to be retained with explicit limits. The finite registry has exposed the weakness without a new operator, missing-case deletion or post-hoc rescue. There is no need to amend D merely to obtain a more favorable detector score. Any later attempt to change count scaling, feature membership, objective, primary bin/lag or event policy must be separately versioned/reviewed before a future freeze; this review does not approve such a change.

### Other independent checks and RCD execution attribution

Read the numerical and leakage reviewers' current reports and their explicit limitations. Their independently reconstructed C1 ranks/control graphs and C5 primary E/scalers/masks/MAE/threshold-support/F1 corroborate the raw figures above; no CRITICAL/MAJOR numerical, leakage or evaluator defect is reported in those completed scopes. The worker boundary is an API/process discipline, not an OS filesystem sandbox. Formal assurance remains OPEN.

Read039 timing plan/result and `timing-stacks.log` directly. Six CONFIG_COMPLETE entries exist: bins5 seeds420/421/422 take68.286/109.179/125.549s; bins3 take75.490/81.738/107.968s. The exact nine-config process then exits3221225477 after604.444s without deadline reach or final transport reply, while bins7 seed420 is running. Three primary configs alone exceed the original300s aggregate request budget. This confirms that the earlier blanket timeout is not evidence of algorithmic zero efficacy or fundamental RCD infeasibility. The later crash is an additional execution defect to retain and diagnose, not a completed nine-config run.040 chunk qualification records3/3 tests, including real-process nine individual chunks versus the qualified batch, without corpus predictions. Recovery still requires immutable per-config provenance, all registered seeds/bins and explicit failure handling; this review does not silently accept missing outputs.

### Final RCD recovery interpretation —041 COMPLETE

Direct evidence: `e27-041-rcd-development-recovery/rcd-development-results.json`, SHA256 `7dcab2e14efa3552bde3d8c00696b9c5b6e17894547f363640e5b9bc0ef45969`. Independently inspected all30 case result records/270 seed-bin statuses and all270 chunk seal metadata, final resume receipt, recovery plan, six-abandoned-attempt preservation receipt, comparator adapter and exact two-line post-split time-drop patch. All270 results are SUCCESS and all270 seals COMPLETE; every bin setting has90 planned/successful seed runs, zero failures, zero unknown metric keys.24 prior completed configurations were reused (18 from034 and6 completed039 log events),246 newly computed. No failed configuration was silently counted as a completed prediction. The final resume records exit0 and reuse of264 completed chunks, followed by the remaining six; abandoned incomplete attempts were preserved byte-identically with no completed artifact moved.

| RCD adapted configuration | MRR | Hit1 | Hit3 | Hit5 | NDCG5 | successful/planned |
|---|---:|---:|---:|---:|---:|---:|
| Primary bins5 | .253367 | .122222 | .247009 | .395123 | .254162 |90/90|
| Diagnostic bins3 | .354273 | .255556 | .359419 | .430152 | .341115 |90/90|
| Diagnostic bins7 | .293702 | .166667 | .300814 | .412589 | .288224 |90/90|

All summaries average the three registered seeds, retaining bins5 as primary. The better bins3 diagnostic is not adopted. Primary fault-group MRR spans .077520 delay to .510516 CPU; root-group MRR spans .131657 route to .340994 auth.53/90 primary seed results place the root within the worst padding tie. This is valid partial-ranking behavior under the declared adapter, not an execution failure or root absence; metric rankings contain1–15 distinct owning services across the full run. The comparator is sensitive to discretization and selective returned rankings. Walltime per completed configuration ranges7.850–554.009s (median95.879s); primary summed method time is11,348.155s, a computational-resource observation, not a directly comparable cold end-to-end runtime benchmark.

Fidelity is bounded to **RCD-RCAEval-adapted-TD12**. The inspected adapter uses raw1s exact-mapped metrics, controller reference-median imputation, gamma5/localizedTrue, all seeds420/421/422, the pinned upstream wrapper, and the exact post-split time-drop patch.264 seals include patch hash `472685d2513a47cefce36640d9de3e21769923f85de48f7cf6feec43e2ae8838` and patched-source hash `036946005d53e5c6a11e2a4b5c099f2194ab104f15df8fd74d74668827278393`; the six reused039 entries explicitly link the completed observer log events and pinned qualification report instead of inventing a missing original transport response. All270 link the same source-manifest and numeric-worker hashes. The separate final leakage receipt now closes the declared source/execution-chain check for these six; this role previously inspected the declared links and actual039 completed events.

RCD and BARO are usable contextual comparators for this development task; final RCD chain/arithmetic verification is closed by the receipts below. Their telemetry, pooling, candidate-metric eligibility and output forms differ from the common M+T L/O/R contrast. O exceeding either adapter cannot isolate observed-relation benefit, establish exact-paper superiority or rescue the negative O−L result. The earlier RCD timeout/failure zeros belong to invalid/incomplete engineering attempts034/039, not the final comparator efficacy estimate.041 shows the registered RCD method can execute on this development scope; no replacement comparator or method amendment is scientifically required by its lower score.

### Final closure evidence — 2026-09-28

Read the two final041 addenda and verified their SHA256 values. This closure did not reopen prior scientific scopes or execute predictions. The numerical receipt is `PASS_CHECKED_SCOPE` with no failures; the leakage receipt is `PASS`. Neither introduces a CRITICAL/MAJOR finding or a scientific blocker.

| Final verification receipt | SHA256 | Bounded closure |
|---|---|---|
| `final-numerical-rcd-verification.json` | `ff12723ff950d062d5fd3d731104bf6d316e0a2e87608943d862c3f172b03430` | All270 expected config identities, raw/seal ranks, owner mapping, padding/tie metrics,90 case/seed means,63 subgroup means and preserved recovery evidence checked; failures empty. |
| `final-leakage-checks-rcd041.json` | `32c0b761c5de8216cc6263fa1c622ad1335a57fa5cae8cbfda871fe425679ade` | All270 chunks,46 source and407 input hashes, complete30×3×3 roster,24 reused configurations, evaluator ordering and preserved interrupted artifacts checked; PASS. |

The receipts retain18 reused034 configurations, six exact completed039 observer events and246 new configurations, and verify the final result hash recorded above. Thus the remaining041 correctness/source/reuse condition is CLOSED within the reviewers' stated scope. These checks do not enlarge the scientific claim, establish an OS sandbox, approve a final freeze or replace human acceptance.

## Sixteen falsification questions — final scientific answers

| # | Question / current conclusion | Classification / implication |
|---:|---|---|
| 1 | Local informative: MRR .744206; selected all-tie/empty/zero counts all0/30. Root ranks:17 at1,9 at2,one each3/4/7/10. | Surviving bounded assumption. |
| 2 | Local strong, not ceiling globally; 13/30 not rank1. | Method claim limit; ceiling cannot dismiss losses. |
| 3 | Structure exists and finite R mobility passes development gates. | Surviving control assumption; no mixing/final guarantee. |
| 4 | O-L negative mean; 22/30 unchanged root RR, few large harms/gains. | Valid negative development observation; separate numerical/firewall checks passed their bounded scope. |
| 5 | O-R small positive, larger than MC SE, unstable across faults. | Arrangement gain not broad or robust support. |
| 6 | Travel/loss dominates positive contrast. | Data/heterogeneity weakness; keep every case. |
| 7 | Root/fault/cell effects vary; C1 sign flips under OFAT, C5 G−ALL flips, G−L magnitude collapses at10s/lag3. | Material limitation covered by TD robustness-review policy, not automatic retune. |
| 8 | Independent numerical reviewer verifies all saved C1 ranks/equations/controls, without failures. | Bounded checked numerical validity; no all-input guarantee. |
| 9 | C5 complete scored coverage and all calibration gates pass. | Surviving bounded input assumption. |
| 10 | G beats L, ALL≈G, equal model counts but different capacity;10s/lag3 largely remove G−L advantage. | Strong evidence against treating the primary gap as graph necessity or stable graph-specific gain. |
| 11 | Extreme scales and lambda instability; >99.999999984% weighted MAE from1e-12 prefix-scale channels; temporal sensitivity materially changes L calibration. | Verified severe method/data weakness; registered sensitivity exposes it, no automatic numerical invalidity. |
| 12 | Events exist but frequent archival pre-triggers and censoring; common diagnosis G-MTL MRR .470935,26/30 valid; persistence/refractory diagnostics materially alter alert count. | Operational/diagnostic limitation; no production claim. |
| 13 | BARO contextual adapter; RCD041 completes270/270 configs, primary MRR .253367, declared source/patch links retained. | Comparator usable within adaptation limits; prior timeouts are engineering failures, not efficacy. Final chain/arithmetic receipts passed and are verified. |
| 14 | Separate independent reconstruction verifies C1 seal/demand and C5 prefix/scaler/calibration-support firewall; final041 linkage also passes. | Bounded assurance across the assigned evidence; OS sandbox absent and formal assurance remains OPEN. |
| 15 | No verified scientific finding requires D amendment under its existing claim-limitation policy; RCD execution recovered without engine/registry change. | No scientific blocker identified. Final numerical/leakage041 condition closed; coordinator development adjudication can proceed. |
| 16 | Supports bounded execution/selection/heterogeneity observations; no final efficacy, novelty, all-graph, production or FlashTicket validation. | Required report claim boundary. |

## Final scientific recommendation and boundaries

**Final scientific recommendation: PASS WITH LIMITATIONS for Task E development preflight.** Every required scientific output scope has been examined here: C1 registered selection/controls, C1 OFAT, C5 primary/OFAT/events, integrated diagnosis and all-seed RCD recovery. The separate final041 numerical/leakage receipts pass, their hashes are verified, and the last correctness/source/reuse condition is closed. No unresolved scientific blocker or finding requiring RETURN TO TASK D is identified. No additional predictions or scientific search are needed to complete this assigned review.

This recommendation has material conditions on the final report: retain inconclusive selection-exposed C1 inference; disclose concentrated loss-fault gains; disclose absolute-floor domination of C5 MAE and the collapse of G−L advantage under10s/lag3; avoid graph-specific superiority from G≈ALL or contextual baseline comparisons; retain all failed/recovered attempts, censoring and planned denominators. Omitting these limits would make the synthesis misleading even though the numeric execution is valid. Performance weakness is not invalid execution, and the fixed TD contract already provides a policy for honest unstable/negative results.

No unresolved method-contract or execution blocker remains in this assigned scientific review. Earlier incomplete RCD attempts remain documented as engineering failures; the complete recovered run supplies the comparator estimate. This closure authorizes neither a new registry/comparator policy nor a reinterpretation of earlier failure penalties as method quality. Human formal acceptance and five-independent-reviewer assurance stay OPEN regardless of development verdict.

Failure taxonomy at final scientific handoff: **method weakness** — sensitivity of graph contrasts, uncapped sparse-scale domination, max-score multiplicity and unequal active capacity; **data weakness** — ten partially crossed development cells, shared/historical exposure, no independent healthy/onset GT, missing logs in one case and incomplete trace-service scope; **implementation/execution defects** — earlier aggregate RCD deadline, later crash/interruption, repaired via preserved per-config recovery; **expected limitations** — finite R mobility without mixing proof, conditional uncertainty, adapters rather than exact reproductions, triggered query composition differing from C1; **unresolved scientific blocker** — none identified. Final041 correctness closure is complete within the verified receipt scope; formal human/five-reviewer gates remain explicitly OPEN.

No decision was promoted, no method/registry was changed and no final configuration was frozen. A development PASS does not authorize F/G/H/I, final60 evaluation or deployment. The next possible work is coordinator review and human authorization of a separately defined next stage. FlashTicket system construction, observability integration and real load/concurrency/diagnosis evaluation under DT18 remain required and are not substituted by these public-benchmark results.

Report-relevant material: separate known-window ranking from detection/composition; retain both O-L/O-R; expose heterogeneity, floor/scale effects, active capacity and censoring; explain historical selection exposure and dataset-to-FlashTicket limits under DT18. No project decision was added or changed by this review.

Reviewer file/validation handoff: only `results/task-e/final-scientific-review.md` was created/edited by this reviewer. Read-only arithmetic, aggregation, schema, metadata and hash checks are described in their corresponding sections; no test or model campaign was rerun. Own-file whitespace diff check passed. Required P governance audit returned PASS with one warning that the shared P diff touches10 files; U27R already authorizes the D/E multi-file impact, and those shared changes are not this reviewer's mutation. Assumption retained: examined case IDs are the registered development30; final60 and all application/legacy scopes remain outside this review.
