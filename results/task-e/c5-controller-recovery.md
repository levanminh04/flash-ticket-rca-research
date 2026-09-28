# C5 controller recovery checkpoint — 2026-09-27

State: source/fixture ownership frozen for coordinator qualification. This is a recovery note, not a decision, approval, test PASS, or empirical result. No actual outcomes or final60 were read by this subtask. No tests or models were executed by this subtask; only AST parsing, source review and whitespace checks ran.

Owned implementation files:

- `scripts/task_e/c5_development.py` — SHA256 `618c75ed188f2769952942fc50b350bac3de631dd1e063367aac281ce6b8c054`.
- `tests/task_e/test_c5_campaign.py` — SHA256 `217187b5cebfb964c1f2510da237e93cf99ecb43a51275f8861cacddfc76d292`.

The controller has exact predetermined smoke10 (.01 floor, no selection), development30 G/L/ALL × MT/MTL × lambda3, the qualified hierarchical fixed-input pre-injection MAE objective, weighted normal training CDF and held-out q selection, independent graph-TV failure handling, and seven registered OFAT variants with primary lambda/q fixed. It saves exact numeric inputs, frozen models, predictions including partial failures, case/campaign seals, threshold support IDs, costs, capacity diagnostics, root/fault/cell summaries, both lambda/q deletion diagnostics and cascade reselection, fixed-q lambda F1 diagnostics, and event-only sensitivities.

Specific interrupted-source bugs fixed: C1 `local_config` schema mismatch; assigning independent TV `None` edge counts into an integer array and thereby failing valid forecasting; insufficient MT/MTL component equality checks; q deletion runs ignoring reselected lambda; primary calibration being mislabeled complete when invalid. Detailed lambda support tuples are discarded one arm at a time only after the qualified evaluator returns; exact support remains reconstructible from sealed masks/endpoints. Leave-cell lambda reaggregates those exact per-case losses and rechecks coverage instead of recalculating identical case-prefix models. A failed diagnostic lambda F1 refit stays distinct from the selected primary detector status.

Fifteen analytic/controller fixtures are written but UNEXECUTED. Expectations include the 17/15 unequal-support loss hierarchy, joint equal-arm lambda loss and tie, deletion changing lambda10 to lambda1, 21/27 deletion coverage failure, 24/6 grouped threshold IDs, q=.95 F1=.8 versus q=.975/.99 F1=1, continuous-positive triggers at195/495 with tau195, no future suffix at fit, explicit TV-only failure, retained partial numeric arrays, pinned audit/cache integrity, and primary-vs-diagnostic failure separation. Fixtures use a fake numeric worker; prior worker/detection qualification remains a separate prerequisite.

Next coordinator action: create a new immutable pre-run contract and run the fixture script, preserving any failure. From the research workspace with the already-qualified Python environment:

```text
python -B -m scripts.task_e.launch_development <NEW_RUN_ID> tests/task_e/test_c5_campaign.py --stage development-c5-controller-fixtures
```

Do not reuse an existing run ID. The launcher pins all Task E sources/tests before execution. The fixture emits `c5-controller-fixture-report.json` and returns nonzero for failures.

Controller CLI: `c5_development.py RUN {smoke,full,sensitivity} --audit-root AUDIT [--c1-selection C1_SELECTION] [--primary-run C5_PRIMARY] [--worker-timeout 300]`. Use the launcher to pin the full audit contract/summary/case receipts/NPZ set; full and sensitivity additionally pin C1 selection. Sensitivity additionally pins the primary C5 run contract, selection, campaign seal and every case seal/artifact (launcher `--pin-root` covers JSON/NPZ). Full/sensitivity require C1 JSON containing `local_config` and `ppr_config`.

Integrated diagnosis handoff: `integrated-trigger-hook.json` has `items` with detector, case, opaque handle, all OOF triggers, first post-injection trigger, `threshold_mode=OOF`, and `profile=TD12-INTEGRATED-MTL`. The coordinator-owned integrated implementation must retain insufficient-history/failure/no-trigger zeros and use the first post-injection trigger only for composed metrics. The C5 controller does not run integrated diagnosis itself.

Remaining qualification: run the 15 fixtures; independent code review; actual smoke gate; actual full30, mandatory sensitivity, integrated diagnosis, and scientific review. No empirical C5 quality, runtime, memory, availability, or robustness conclusion follows from this checkpoint. In particular, model maxima, small residual-scale samples, graph/ALL capacity differences, event-time rather than arrival-time replay, conditional scored support and supervised injection-regime calibration retain the TD claim limits. No source-of-truth scientific decision was added or changed.
