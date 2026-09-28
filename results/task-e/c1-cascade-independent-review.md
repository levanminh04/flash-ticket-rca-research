# Independent staged C1 cascade review — 2026-09-27

Reviewer: `c5_campaign_recovery`, independent of the C1 controller/test author. Intent: REVIEW. No C1 implementation or fixture source was edited. No new test, model, real prediction, or outcome job was executed; no actual ranking/selection outcomes or final60 data were opened. This note is a bounded technical review, not human method approval or empirical RCA success.

## Conclusion

No CRITICAL or MAJOR finding in the requested staged-selection, worker-isolation, sealing, denominator, or identity-L tie-normalization scope. The reviewed implementation and the 16/16 fixture receipt are mutually consistent. Proceeding to the already-authorized predetermined smoke is supported, while the coordinator must inspect the smoke's explicit input-failure list instead of treating its status string as a coverage gate. Two bounded hardening observations remain below; neither requires a scientific-method amendment.

## Reviewed identities and qualification evidence

All following live source hashes were recomputed and match the immutable `e27-027-c1-cascade-qualification/run-contract.json` source pins:

| Source | SHA256 |
|---|---|
| `scripts/task_e/c1_development.py` | `c2e97d7840466963ff41cd1c7a47fc492bac90e8d4b40cc9788f833443f71fe2` |
| `tests/task_e/test_c1_campaign.py` | `01cf4d1ad57f7eeb98096fd7ca33af5680f3e91b658f7646411bb991232cfc0c` |
| `scripts/task_e/worker.py` | `483ffc40577e125b8c1d27ebbde1afa5d8ffa8d38990ba657c260a0453bb1e92` |
| `scripts/task_e/boundary.py` | `1796dd0cf2a2fa5293bd59d2449c2996cb11b484aef8c4b5e1f32b9d5f2b1371` |
| `scripts/task_e/ranking.py` | `1b671310d326502ff0be9864c4e1ef8dcf52674a1810342687f896ac4d1b17ed` |
| `scripts/task_e/evaluator.py` | `73b1b4cbd0fcdda157d1d018614633dba72756a96423e445f64a966efcfe7511` |
| `scripts/task_e/calibration.py` | `0d27b9c3474645e54a5a1e22ba684359b854bd66076c9d541404627b5b2c572d` |
| `scripts/task_e/execution.py` | `385e67003355f0fff101942f71f369be2f8a2432aa6fd1a937214f9d67c1c92c` |
| `scripts/task_e/contract.py` | `d157eb28db6154272a166d60b029f0249d130f8a8bac2912fcc81fe782dc27c3` |

Additional current launcher hash: `f46babc398d708e7fb2e6472714ce0199377f4a69e8345a616913a28591ff16d`.

Qualification receipt: **16 tests, 0 failures, 0 errors**, 155.4858824 seconds; execution exit0, 156.3107427 seconds. Its declared scope is synthetic controller/arithmetic qualification, without real data or child model execution. The test source was read rather than accepting its PASS label alone.

| Receipt under `results/task-e/e27-027-c1-cascade-qualification/` | SHA256 |
|---|---|
| `run-contract.json` | `db21779d0b5053b809d583e009d673fc7f7aa3ede6020aef3a8fba08ca911dd5` |
| `c1-controller-fixture-report.json` | `cef11aba024210b2cb8181be97b6a19508b78d020a7a866ccda6b7ef5acdbcda` |
| `execution.json` | `a4066951c9f5f2f4e0fb75db9102bb0384100231c13a9d55d0cc81d95f688a20` |

The receipt pins TD SHA256 `34fd73f6a84dc6b45834bd7fd4cc7b86e19e54f1011de99735631f027ee18971` and dataset revision `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`. Governing checks used TD §§3–6,8–10 and canonical project/skill rules already read in this subtask.

## Findings by requested concern

1. **Selection cascade and finite search — PASS.** `forecast_free_predictions` (C1 lines86–100) invokes only local scoring and identity rankers; the worker dispatch does not compute observed rankings when rank configs are absent. All local predictions are sealed before the first nontrivial evaluation (lines223–231). `local-selection.json` fixes both the primary theta and every whole-cell-deletion theta from absolute L-MRR only (lines232–239). `observed_request_plan` (lines150–160) then creates only the required theta/case union. The plan is saved before any O call (lines242–246), primary theta is first, and each requested theta roster is sealed before its evaluation (lines247–268). O never selects theta. The fixture's analytic counterexample requests 30 primary plus27 conditional cases, rather than an eight-theta Cartesian execution. The full mock checks one theta when all L choices tie. PPR stays primary independently of the diffusion score; R is absent from winner selection.

2. **OOF interpretation and denominators — PASS within declared development design.** Case-prefix scoring has no cross-case fitted model; the registered five held-out cell pairs partition the30 records. Equal incident means equal equal-cell means because all three repeats are retained for each cell, including whole-cell deletions. This is explicitly selection-exposed development scoring, not an unbiased post-selection estimate. Input failures generate eight explicit local zeros, requested observed zeros, all256 failed-draw zeros and comparator zeros (lines78–83,171–177,251–255,281–290). Empty V/root absence stays zero rather than excluding a case. Fixtures separately verify 29/30 and (29/30)*(2/3) summaries and empty-candidate retention. A numeric failure aborts the development attempt for correction; it is not a candidate with an artificially favorable reduced denominator.

3. **Numeric/evaluator separation — PASS.** Workers receive only numeric ref/query arrays, masks via missing values, adjacency, channel-type codes and registered config. Labels, service names, metadata, absolute epochs and file paths remain in the trusted controller. `worker.py` imports numeric detection/ranking only and rejects unknown request fields (lines79–125). The empty-rank local call does receive adjacency as an allowed numeric field, but `local_scores` does not consume it and no O ranking occurs in that branch. The controller can read metadata for routing/failure records without turning it into worker input; no claim of an adversarial OS sandbox is made.

4. **Prediction seals precede relevant evaluation — PASS.** Local files and the whole local-stage seal precede local ranking evaluation; the source uses exclusive creation and SHA256 receipts. O, BARO/Local-MAX and R arrays are sealed before their metrics. For R, all256 draw scores in each representation are saved before draw evaluation (lines303–313), and metrics are averaged per draw, not computed from mean scores. The near-tie, complete-roster, R arithmetic and seal-order fixtures inspect this ordering. This is an auditable staged experiment; it does not claim to keep development labels unknown to the trusted process until the entire cascade has finished, which would contradict supervised development selection.

5. **Identity-L normalization and ties — PASS.** L is evaluated on its identity-PPR mass, using the same max/total normalization scale as O; it is not evaluated on uncapped raw local evidence. Secondary identity diffusion is saved/evaluated separately. With T=I, the registered ranker's equation reduces to the normalized local vector; zero evidence is a complete all-tie result, including an empty vector. `tie_metrics` rounds the finite rank scores at12 decimals and uses the full tie denominator. The synthetic vector `[1e12,1e12+.1,0]` yields both identity L and empty-graph O RR=.75, avoiding a false graph improvement from comparing raw and normalized tie scales. Fixed identity damping .85 is algebraically irrelevant for T=I; this review does not assert bitwise equality at every floating-point rounding boundary across dampings.

6. **Actual-use topology lineage — verified without outcomes.** Independently checked every primary-budget receipt in `e27-022-development-topology`: **60/60** (30cases ×2representations) COMPLETE; all cite `e27-019-development-loader-audit`; all stored original numeric-file hashes match current input bytes; all case-audit hashes match; all `graphs.npz` hashes match their topology receipt. No graph ranking or outcome was computed/read. This establishes the supplied topology/input linkage, not a new mixing/mobility conclusion.

## Bounded observations

- **MINOR C1-RV-01 — smoke PASS is not a data-coverage gate.** Lines214–220 write `status=PASS` even if materialized inputs were skipped, but retain the exact `input_failure_cases`. The qualified success fixture covers the complete ten-case route, not an all-input-failed smoke. Coordinator action: inspect this list and actual executed case count before proceeding; retain failures and assess them under TD, rather than using the string alone. No requested actual smoke has yet been reviewed here.
- **MINOR C1-RV-02 — admission relies on the qualified launch workflow.** `main` checks the development stage fragment and per-input byte pins; it does not independently compare all executing source hashes/current TD or consume topology receipts when reading graph NPZ files. The launcher records and snapshots the full source/input sets before execution. The supplied 027 source match and the 60/60 topology lineage check above close this concern for the identified sources/inputs when the coordinator uses that launcher and holds sources fixed. A bare direct invocation with an arbitrary contract is not qualified by this review. Optional hardening can make the same admission checks explicit in the controller without changing the method.

## Remaining scope and report wording

No scientific decision state changed. No actual graph utility, comparator performance, running cost, sensitivity stability, or final readiness claim follows from16 synthetic tests and static review. Predetermined smoke, actual development30, registered sensitivities, C5/integrated composition, resources and post-run scientific review remain separate requirements. Report this review as evidence that the supervised selection cascade and its controls were qualified before new development outcomes, retaining the benchmark's historical exposure limitations.
