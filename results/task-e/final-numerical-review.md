# Independent numerical/data review — checkpoint 1

State: FACT for checked artifacts; overall Task E review remains OPEN. Intent REVIEW. Canonical authority TD-v1.3 SHA256 `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971`, §§3–5,8–10; development-only authorization U27R §17. No application, final60, legacy, model runs, new grids or existing outputs changed.

## Completed independent verification

The independent calculation used NumPy and explicit formulas, without importing the project evaluator/ranking implementation. It consumed sealed arrays and checked equations; it did not run new predictions. Evidence: `final-numerical-verification.json` (SHA256 `bbca4f7b287deb7f11b62b06a923269024b043f1041bd9bfa4cdf8462da3b756`), `checks`, `max_absolute_differences`, `summary`, `topology`, `sensitivity`, and `evidence_hashes`. All 11 recorded evidence anchors still matched on continuation; completed numerical checks were reused.

- C1 e27-033: exact planned30 retained, 240 local variants, 513 recorded observed variants, 69,120 R per-draw rankings (30×256×9). Tie-aware RR/Hit1/3/5/NDCG5 recomputed; all match exactly at individual-rank level. R metrics are the mean of all256 per-draw metrics, never the metric of mean scores. No failed R draw silently removed. Means and conditional MC SD/SE match within 4.12e−15.
- L is evaluated on the identity-operator normalized vector, with the same probability scale as PPR O/R. All240 PPR and diffusion identity checks pass, excluding a raw-L versus normalized-O rounding confound for these outputs. Maximum PPR equation residual 5.09e−16; diffusion 5.83e−16. All checked scores finite, PPR mass/nonnegativity and diffusion convex bounds pass; no C1 numerical channel failure.
- Loader e27-019: all30 case identities, eight profiles each and all270 materialized numeric-file hashes match. Candidates include the root in30/30; graph sizes20 or27 nodes,20 or55 directed edges. Local signal is not all-tied in any of30. This checkpoint did not independently parse every raw telemetry row or rehash every physical raw object.
- Topology e27-022, corroborating026: all180 jobs (30×two representations×three budgets),46,080 saved graphs checked for exact degrees, exact component vertex partition, no loops, undirected symmetry, seeds, hashes, proposal accounting and retained-edge fraction. All180 satisfy the registered development mobility gates. This verifies finite perturbations, not mixing/uniform sampling or causal truth.
- C1 sensitivity e27-036: allnine completed OFAT variants preserve planned30. All540 L/O case metrics and18 headline means match sealed arrays. No variant adopted into the primary registry by this review.
-447 prediction seals and1,027 pinned-input hashes pass. The original verification records six source-snapshot flags; their closure is below.

## Numerical findings and limitations

No CRITICAL/MAJOR numerical/data error found in the checked C1/topology scope. Development L MRR=0.7442063492063493, O=0.7024052287581699, R=0.6782346218755165; O−L=−0.0418011204481794, O−R=+0.0241706068826534. Diffusion O=0.7201617933723196 and R=0.6967286198275685. BARO=0.6591203703703704 is its declared adaptation, not exact-paper reproduction. These are selection-exposed development estimates, not final results.

The O−L sign changes at20s bins (+0.0012433862433862);5s bins give−0.1612827432794754. This is material sensitivity requiring claim limits under D §8, not a reason to change method after outcomes. Primary local information is present, but MRR0.744 is not perfect ceiling.

MINOR provenance packaging issue: `source-manifest.json` stores universal-newline-decoded `utf8_snapshot`, while its `sha256` describes original bytes. The six failures are the same three files in033 and036: `scripts/task_e/c1_development.py` (369 CRLF among432 LF), `scripts/task_e/integrated_development.py` (1 CRLF among196 LF), and `baselines/task-e-source-manifest.json` (258 CRLF). Original current bytes match all recorded hashes; their decoded text matches every saved snapshot. This is not evidence of scientific/source drift. Exact mixed-newline byte reconstruction from text alone is unavailable. Preserve originals; a future immutable supplemental byte snapshot can strengthen reproducibility without rewriting old receipts. Closure evidence: `final-numerical-closure-addendum.json`, `source_flags`.

## Pending review

C5 primary035 independent loss/threshold/F1/event arithmetic; C5 sensitivity037; integrated038; RCD completed reuse/rerun evidence and runtime fidelity; independent physical raw-source hash audit. RCD timeout zeros are execution outcomes, not evidence of poor method efficacy. A coordinator report of timing diagnosis is not treated here as independently verified evidence. Overall Task E acceptance remains OPEN.

## Handoff

No decision state changed. Assumption: only registered development case identifiers are examined. Files created: this checkpoint report, numerical-verification JSON and closure-addendum JSON. Tests were arithmetic/equation/hash/graph audits above; no method rerun. Formal-report material: exact development results, variation across bin sizes, finite-control validity, selection exposure, topology noncausality and snapshot newline limitation. No final-stage approval is implied.

## Checkpoint 2 — completed C5 primary, sensitivity and integrated review

This section supersedes the corresponding pending items above. It is still not the final Task E acceptance: completed RCD recovery/fidelity/evaluation remains OPEN for review.

C5 primary035: independently checked all89 physically present raw telemetry objects against the loader's expected SHA256 and byte counts (0.656GB), all30 case seals and90 saved artifact hashes. All540 case/config combinations have fit-only applicability, correct fit scalers, fixed input-based model/target masks, finite predictions on those masks, absolute prediction error, one-sided residual scaling and system maxima. All M/T residual components match between MT and MTL. Recomputed all270 case forecast MAEs,9 arm losses and3 lambda objectives exactly; selected lambda10 follows the registered objective. Recomputed all120 fold thresholds and exact normal-support IDs,24 q objectives,8 full thresholds, all macro P/R/F1, and480 OOF/full-refit event sequences with first-post and normal-duration boundaries. There is no numerical failure in this checked scope. Evidence: `final-numerical-c5-primary-verification.json`.

Primary macro F1: G-MTL0.6699937206, L-MTL0.0725547478, ALL-MTL0.6908652803; G-MT0.6888623896, L-MT0.0720006779, ALL-MT0.6874737380. Every detector has30 scored cases. These are held-out-fold threshold scores used in development selection, not production or final evaluation performance. Large finite thresholds remain material: L-MTL2.216949271969e14 and TV-MTL2.405174801409e24. The arithmetic audit does not make those scales operationally calibrated or establish that G's advantage over L is due only to relations.

Additional context audit: all1,620 frozen degree denominators and60 TV channel/edge/system checks pass; TV maximum relative formula discrepancy1.64e−15. An initial reviewer check reported51 flags when using ordinary arithmetic means, vectorized contraction and a cancellation-prone stationarity denominator. Those are preserved in `final-numerical-c5-context-verification.json`, not erased. Adjudication with the actual safe-pooling arithmetic and scalar dot equation finds all180 selected-lambda case/arms exactly equal to stored predictions and intercepts. Proper normwise ridge stationarity maximum3.72e−15 and dot summation backward error4.40e−16 close those flags as reviewer-check artifacts, not method implementation errors. The largest same-products compensated-sum difference divided by residual scale is0.0244140625, in one case for ALL MT and MTL; this does not certify forward coefficient accuracy in an ill-conditioned problem. Evidence: `final-numerical-c5-context-adjudication.json`.

C5 sensitivity037: all210 case/variant seals,630 saved artifact hashes and registered grids pass; all targets finite on fixed masks, same G/L/ALL masks, residual/error/system-max arithmetic consistent. The56 detector variants retain the primary lambda10 and chosen q; no outcome-driven replacement occurred. Recomputed280 fold thresholds,56 full thresholds and their exact support IDs, all21,840 case metric fields and168 macro P/R/F1 checks exactly. Replayed3,360 sensitivity event lists plus2,400 event-only OOF/refit lists across40 registered event settings. No mismatch. Evidence: `final-numerical-c5-sensitivity-verification.json`.

Sensitivity is scientifically material despite arithmetic validity: L-MTL F1 rises from0.07255 at primary5s/lag1 to0.65206 at10s and0.65081 atlag3; G-MTL is0.66172 and0.67917 respectively. The primary large G−L advantage is not stable to these registered changes. G−ALL changes sign atlag3 and the smallest relative floor. These observations require bounded claims; they do not authorize selecting a better-looking variant after development.

Integrated038: independently audited124 unique case/trigger records,352 artifact hashes and past-window metadata. All114 valid predictions have the expected30 reference and6 query bins; tie metrics match exactly, PPR equation residual≤1.88e−16. Ten early triggers retain INSUFFICIENT_HISTORY. All240 detector/case first-post-only compositions retain the exact035 OOF trigger lists; first failure/absence cannot be rescued by later triggers. All eight summaries retain planned30. G-MTL composed MRR0.4709346380 includes four cases with no post-injection trigger. This remains a secondary composition, not primary C1. Evidence: `final-numerical-integrated-verification.json`.

No unresolved CRITICAL/MAJOR numerical error in these completed scopes. MINOR normalized-newline snapshot packaging limitation remains. No raw-row-by-row independent loader replay was performed; physical source hashes, materialized arrays, saved formulas and denominators were audited. RCD034 timeout/native-process receipts must not be interpreted as method efficacy;041 recovery is still pending independent completed-evidence review. No claim of final freeze, final60 execution or overall Task E completion is made.

Checkpoint2 created five additional reviewer-only JSON artifacts listed below; existing run outputs and initial verification findings were preserved. No decision state, application, research implementation or algorithm changed.

| Artifact | SHA256 |
|---|---|
| `final-numerical-c5-primary-verification.json` | `908a1f11a0227f06d1145decd6c0f8dcbd9eacf57f4688ba6b1048f8cbba23b6` |
| `final-numerical-c5-context-verification.json` | `b0228ce52848b9b96410dd1fd8aefab4b51ce839e693ff845a1c81a98b154243` |
| `final-numerical-c5-context-adjudication.json` | `f3589ac0717cef3294c2ccbe94d02103ffb87546a06975e944b4af53f70d7f54` |
| `final-numerical-integrated-verification.json` | `6b968e43a435a9fd2655ab21a6c0c01b36aaa0a596f6d96a28ae5d2c64770ca5` |
| `final-numerical-c5-sensitivity-verification.json` | `28564f5e933cd519b28afd465c9e2c494063b2d486438f30326c64863642dee5` |

## Final numerical review closure — RCD041

This section closes the final pending numerical/data scope. Prior C1, C5, OFAT and integrated arithmetic audits remain closed and were not repeated. State: FACT for the verified results below. Numerical/data reviewer verdict: **PASS WITH LIMITATIONS — CHECKED DEVELOPMENT SCOPE**. This is reviewer evidence for coordinator adjudication, not overall Task E acceptance, human approval, final freeze or authorization to open final60.

RCD041 finished with resume02 exit0. The complete file is `e27-041-rcd-development-recovery/rcd-development-results.json`, SHA256 `7dcab2e14efa3552bde3d8c00696b9c5b6e17894547f363640e5b9bc0ef45969`. Independent verification receipt: `final-numerical-rcd-verification.json`, SHA256 `ff12723ff950d062d5fd3d731104bf6d316e0a2e87608943d862c3f172b03430`.

All270 registered replies/seals are COMPLETE/SUCCESS:30 cases ×3 bin settings ×3 seeds. Independently checked46 source-file raw hashes,407 pinned inputs, all270 numeric-input identities,516 saved raw artifact hashes, and exact raw→seal→evaluation correspondence. All5,028 admitted metric keys map to the literal service owner using the declared suffix rules. Every output preserves first occurrence per service and pads every unranked candidate as one worst tie. All270 tie metrics and root tie intervals match exactly; all90 within-case three-seed means and450 seed-variability metrics match exactly. Allthree aggregates retain30 cases/90 seed runs, with0 failed seed runs; all63 root/fault/cell means match. Headline arithmetic difference≤5.56e−17.

| RCD bins | Role | MRR | Hit@1 | Hit@3 | Hit@5 | NDCG@5 | Root in tied ranks /90 |
|---|---|---:|---:|---:|---:|---:|---:|
| 5 | Fixed primary | 0.2533669715 | 0.1222222222 | 0.2470085470 | 0.3951229953 | 0.2541617034 | 53 |
| 3 | Registered sensitivity | 0.3542734550 | 0.2555555556 | 0.3594188034 | 0.4301516165 | 0.3411154174 | 49 |
| 7 | Registered sensitivity | 0.2937015267 | 0.1666666667 | 0.3008136152 | 0.4125894356 | 0.2882236413 | 54 |

The recovery preserves24 previously successful configurations:18 from two complete034 cases and6 exact CONFIG_COMPLETE records from039. Each reused result equals its original evidence;246 other configurations have complete new raw replies. The162 complete seals listed in resume01 and264 listed in resume02 remain byte-identical (426 checks, including repeated preservation checks across checkpoints). All18 files from six interrupted unsealed attempts remain byte-identical under `attempt-history/interrupted-01`. These were incomplete attempts, not deleted completed predictions. Prior034 timeouts and039 native-process failure remain separate execution history; their zeros are not treated as method efficacy in the completed041 aggregate. The adaptation's predefined bins5 remains primary even though bins3 has higher development MRR.

No new CRITICAL/MAJOR numerical/data defect was found. Remaining limitations are claims and evidence boundaries: contextual adapted RCD rather than exact-paper reproduction; partial ranking/worst-tie prevalence; development selection exposure; finite-control rather than mixing guarantees; C5 scale/conditioning and sensitivity limitations; normalized-newline source snapshots; no independent raw-row-by-row loader replay. None of these is silently promoted to clean final evaluation or production performance.

Reviewer handoff: all assigned completed-artifact numerical/data scopes are now CLOSED. No scientific decision was added/promoted, and no research/application code, old run output, source receipt or failure was edited. This final update creates only the RCD verification JSON and appends this reviewer report. Formal report should retain the denominator, partial-tie rule, bin-sensitivity results, adapted-comparator label and recovery provenance above.
