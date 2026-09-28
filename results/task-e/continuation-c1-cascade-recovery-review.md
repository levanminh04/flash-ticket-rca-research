# C1 cascade recovery review — 2026-09-27

Owner/reviewer: `c1_campaign_recovery_review`. Scope: authorized Task E development controller and synthetic fixtures. Canonical method remains P `docs/research-rca/task-d-method-and-experiment-specification.md` TD-v1.3. No raw telemetry, actual predictions, final60 or new method/operator/registry is authorized by this note.

## Evidence and finding

- FACT: immutable e27-025 completed 15 synthetic tests with zero errors/failures, exit 0, 183.831 seconds. Its fixture report SHA256 is `72ef59f9bd15888851839038aeaf0cfff4a289fe0ed518626c4d55ded8932329`. It did not check the number or ordering of observed-graph configurations executed.
- FACT: reviewed C1 source SHA256 `b77bee764e0fabd5c71b26bad95c9b31cc363011eaf6b1d407b0a12d0960a8a2` invoked all nine observed rank configurations for each of eight local variants in `forecast_free_predictions`, and evaluated all 72 combinations before selecting local theta. The absolute-L then absolute-O selector itself was correct.
- USER_CONFIRMED scope: U27R §15 states “No Cartesian brute force unless amended D explicitly requires it.” Canonical TD §3 selects eight L variants, freezes theta, then compares six PPR and three secondary diffusion configurations; §8 says no Cartesian grid. Leave-cell reselection is mandatory, but does not require evaluating every theta in every case.
- Review classification: **MAJOR pre-outcome execution/exposure deviation**, detected before actual C1 development predictions. This finding does not establish a graph-gain selection error or invalidate a nonexistent real C1 result. Existing e27-025 remains valid evidence for its narrower fixture coverage.

## Applied restoration

The coordinator explicitly authorized this bounded implementation correction. Scientific states, formulas, split, folds, tie priorities, registry and TD are unchanged.

1. Compute the eight local vectors and their identity rankings, retaining channel arrays/masks and numeric inputs. No observed graph ranking is requested in this stage.
2. Seal the entire planned local roster in `local-stage-seal.json`, then evaluate L. Shared input failures retain planned zero outcomes.
3. Choose the primary theta and each leave-cell theta from L alone. Save `local-selection.json` before any observed graph prediction.
4. Build `observed-execution-plan.json` from those recorded decisions. Every requested `(theta, case)` records whether the primary or an identified deletion requires it. Execute the primary theta first; execute other theta values only on the union of cases retained by deletions that selected them. Reuse a shared `(theta, case)` result once.
5. For each demanded theta, run the six PPR plus three secondary configurations, seal every requested case prediction, then evaluate those scores. Primary and deletion ranking selections use their own theta and planned case subset. Local evidence is not recomputed.
6. Smoke uses the predeclared priority theta `LOCAL[0]` and nine rank configurations for feasibility, with no label evaluation or selection. It no longer expands eight theta values into observed configurations.

`selection.json` keeps `local_config`, `ppr_config`, `diffusion_config` and existing selection fields for C5/integrated callers. The per-case `observed` curve collection is now sparse, keyed by requested local index. Observed score files move to separately sealed `*-observed-local<index>.npz` artifacts. Local NPZ files contain no Cartesian observed score cube. The existing selected-theta R diagnostic behavior is unchanged in this correction.

## Qualification scope

Source frozen for e27-027: `scripts/task_e/c1_development.py`, SHA256 `c2e97d7840466963ff41cd1c7a47fc492bac90e8d4b40cc9788f833443f71fe2`.

Fixture source frozen for e27-027: `tests/task_e/test_c1_campaign.py`, SHA256 `01cf4d1ad57f7eeb98096fd7ca33af5680f3e91b658f7646411bb991232cfc0c`.

The 16-fixture suite retains previous arithmetic, empty-V, failure, seal, sensitivity, bootstrap and Monte Carlo checks, and adds execution-budget/order assertions. One analytic roster makes theta0 win overall while theta1 wins only when a specified cell is deleted: the demand must contain exactly 30 primary and 27 conditional cases, not all eight local indices. The full controller fixture requires one observed-theta request per case when all L selections tie at theta0, verifies L decisions exist before O requests, and verifies primary O seals before evaluation. Hash verification is checked once per artifact rather than repeated for every R-draw metric, reducing redundant fixture I/O without weakening the seal boundary assertion.

e27-027 was launched through the pre-run contract launcher with synthetic-only exposure. Read its immutable `c1-controller-fixture-report.json` and `execution.json` for the outcome; this note does not infer PASS from source inspection or launch. Old receipts remain unchanged.

**Closure checked after execution:** e27-027 completed all 16 tests with zero errors/failures in 155.4858824 seconds; `execution.json` records exit 0 and 156.3107427 seconds wall time. The source/test hashes above match the contracted files. The pre-outcome Cartesian-execution finding is **closed for this implementation and synthetic scope**. This is restoration of TD's cascade, not a TD amendment, empirical freeze or claim that actual development will pass.

## Independent C5 controller review after e27-028

Read-only review of `scripts/task_e/c5_development.py`, SHA256 `618c75ed188f2769952942fc50b350bac3de631dd1e063367aac281ce6b8c054`, and `tests/task_e/test_c5_campaign.py`, SHA256 `217187b5cebfb964c1f2510da237e93cf99ecb43a51275f8861cacddfc76d292`. Those hashes are pinned in e27-028. Its fixture report records 15 tests, zero errors/failures, 5.6517521 seconds; execution exit is 0. No C5 raw data or actual models were executed by this reviewer.

Review result: **no outstanding CRITICAL/MAJOR finding in the inspected controller and registered execution scope**. Specific checks:

- The primary 18 numeric configurations are the required three arms, two declared modalities and three lambda values. The common lambda objective reads only MTL G/L/ALL, before residual scaling, with equal arm and scenario/case/bin/channel weighting. The MT lambda outputs support the mandatory modality/lambda diagnostics; they do not vote in primary lambda selection.
- q search occurs after lambda is selected. Other lambda F1 curves hold that selected primary q fixed and label themselves diagnostic; they do not select a lambda by F1 or open a lambda-by-q winner grid. Seven numeric sensitivities are OFAT at the selected lambda; q stays fixed while training CDF thresholds are refitted for the changed score scale. Event sensitivities change streak or refractory independently and do not retune numeric detectors.
- Common target masks, eligibility, scalers, M/T coefficients and residual components are checked across the required arms/lambdas/modalities. Missing observations do not become healthy zeros or shrink masks in response to numeric prediction failures. The trusted evaluator uses only pre-injection fixed eligible bins for forecast loss and fold-training normal score IDs for CDF calibration.
- Lambda deletion diagnostics reaggregate already qualified per-case losses because prefix models are case-local, recheck the 80% support gate, and rerun lambda selection. The subsequent q cascade uses that deletion's lambda and refits its CDF; the new analytic fixtures cover a changed winner and 21/27 insufficient support.
- The worker receives only the fixed warmup and successive numeric bins. All planned case seals are committed and checked before evaluator-only tau/scenario data enters calibration. Partial failures retain artifacts and cannot be overwritten as successful checkpoints.
- TV arithmetic failure remains a TV failure without vetoing valid forecast components. A log-only TV failure can affect MTL TV while MT and common forecast components remain separately checked. Failed/unavailable cases remain in planned coverage/F1 denominators; inadequate calibration support returns a non-complete verdict.
- The fixture suite checks normal-only lambda loss despite huge post-injection errors, unequal-channel weighting, exact q support IDs, deletion cascade, chronological worker input, seals/tampering, partial failures, TV isolation and MT/MTL drift. There is no dedicated full input-unavailable controller fixture; static inspection of that path retains an explicit sealed `INPUT_UNAVAILABLE` record and unavailable score arrays. This limited fixture gap does not establish a code defect, and empirical input failures must still be reviewed if encountered.

This scoped review does not certify actual input coverage, runtime/memory, threshold usability, integrated diagnosis, completed empirical sensitivity, final60 or final scientific assurance. Those remain downstream evidence gates.

## Remaining handoff

- Actual smoke/development30 and mandatory empirical sensitivity remain subsequent coordinator work after fixture/review acceptance.
- Selection manifests and the sparse execution plan belong in the reproducibility appendix; e27-025 and this pre-outcome correction should remain in the implementation audit trail.
- No method claim, final configuration freeze, final benchmark approval, or human scientific approval is created here.
